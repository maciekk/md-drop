/**
 * md-drop — Google Apps Script web app.
 *
 * Serves a simple Markdown capture form and appends submissions to a Google Sheet.
 * Deploy as a web app: Execute as "Me", access "Anyone".
 *
 * Script Properties (set via Project Settings > Script Properties):
 *   - SHEET_ID:  ID of the Google Sheet to write to
 *   - AUTH_TOKEN: shared secret for form validation
 */

var VERSION = "2026-03-26 00:02";

function doGet(e) {
  var token = (e && e.parameter && e.parameter.t) || "";
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
