/**
 * md-drop — Google Apps Script web app.
 *
 * Serves a simple Markdown capture form and appends submissions to a Google Sheet.
 * Deploy as a web app: Execute as "Me", access "Anyone".
 *
 * Script Properties (set via Project Settings > Script Properties):
 *   - SHEET_ID:  ID of the Google Sheet to write to
 *   - AUTH_TOKEN: shared secret for form validation
 *   - PIN: (optional) short memorable PIN; visiting ?pin=<PIN> redirects to ?t=<AUTH_TOKEN>
 */

var VERSION = "2026-03-26 19:07";

function doGet(e) {
  var params = (e && e.parameter) || {};

  // PIN access: ?pin=<PIN> → render form directly with AUTH_TOKEN
  if (params.pin) {
    var props = PropertiesService.getScriptProperties();
    var expectedPin = props.getProperty("PIN");
    if (expectedPin && params.pin === expectedPin) {
      var token = props.getProperty("AUTH_TOKEN");
      var template = HtmlService.createTemplateFromFile("Form");
      template.token = token;
      template.version = VERSION;
      return template
        .evaluate()
        .setTitle("md-drop")
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
    }
    return HtmlService.createHtmlOutput("<p>Invalid PIN.</p>").setTitle("md-drop");
  }

  var token = params.t || "";
  var template = HtmlService.createTemplateFromFile("Form");
  template.token = token;
  template.version = VERSION;
  return template
    .evaluate()
    .setTitle("md-drop")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function submitNote(token, title, body) {
  var props = PropertiesService.getScriptProperties();
  var expectedToken = props.getProperty("AUTH_TOKEN");

  if (!expectedToken || token !== expectedToken) {
    return { success: false, error: "Invalid token" };
  }

  var sheetId = props.getProperty("SHEET_ID");
  if (!sheetId) {
    return { success: false, error: "SHEET_ID not configured" };
  }

  var ss = SpreadsheetApp.openById(sheetId);
  var sheet = ss.getSheetByName("inbox");
  if (!sheet) {
    sheet = ss.getSheets()[0];
  }

  var timestamp = new Date().toISOString();
  sheet.appendRow([timestamp, title || "", body || "", "web", "pending", ""]);

  return { success: true };
}
