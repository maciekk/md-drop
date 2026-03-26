"""Gmail source — reads labeled messages and marks them with a synced label."""

import base64
import logging
from datetime import datetime, timezone

from googleapiclient.discovery import build

from md_drop.formatter import html_to_markdown
from md_drop.note import Note

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _get_service(creds):
    return build("gmail", "v1", credentials=creds)


def _ensure_label(service, label_name: str) -> str:
    """Get or create a Gmail label, return its ID."""
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"] == label_name:
            return label["id"]
    # Create the label
    created = (
        service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
    log.info("Created Gmail label: %s", label_name)
    return created["id"]


def _get_label_id(service, label_name: str) -> str | None:
    """Get a Gmail label ID by name, or None if it doesn't exist."""
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"] == label_name:
            return label["id"]
    return None


def _extract_body(payload: dict) -> tuple[str, bool]:
    """Extract message body. Returns (text, is_html)."""
    # Simple single-part message
    if payload.get("body", {}).get("data"):
        mime = payload.get("mimeType", "")
        data = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        return data, "html" in mime

    # Multipart — prefer text/plain, fall back to text/html
    parts = payload.get("parts", [])
    plain_text = None
    html_text = None

    for part in parts:
        mime = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")
        if not body_data:
            # Nested multipart
            nested_text, nested_is_html = _extract_body(part)
            if nested_text:
                if nested_is_html:
                    html_text = html_text or nested_text
                else:
                    plain_text = plain_text or nested_text
            continue
        decoded = base64.urlsafe_b64decode(body_data).decode("utf-8")
        if mime == "text/plain":
            plain_text = plain_text or decoded
        elif "html" in mime:
            html_text = html_text or decoded

    if plain_text:
        return plain_text, False
    if html_text:
        return html_text, True
    return "", False


def fetch_pending(
    creds, label_name: str, synced_label_name: str
) -> list[Note]:
    """Read messages with the source label but without the synced label."""
    service = _get_service(creds)

    source_label_id = _get_label_id(service, label_name)
    if not source_label_id:
        log.warning("Gmail label '%s' not found — skipping Gmail source", label_name)
        return []

    synced_label_id = _get_label_id(service, synced_label_name)

    # Search for messages with source label
    query = f"label:{label_name}"
    if synced_label_id:
        query += f" -label:{synced_label_name}"

    results = (
        service.users().messages().list(userId="me", q=query, maxResults=50).execute()
    )
    message_ids = [m["id"] for m in results.get("messages", [])]

    if not message_ids:
        log.info("No pending Gmail messages found")
        return []

    notes = []
    for msg_id in message_ids:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        subject = headers.get("Subject", "").strip()
        date_str = headers.get("Date", "")

        try:
            # Parse email date header
            from email.utils import parsedate_to_datetime

            timestamp = parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            timestamp = datetime.now(timezone.utc)

        body_text, is_html = _extract_body(msg["payload"])
        if is_html:
            body_text = html_to_markdown(body_text)

        notes.append(
            Note(
                timestamp=timestamp,
                title=subject,
                body=body_text.strip(),
                source="email",
                source_id=msg_id,
            )
        )

    log.info("Found %d pending Gmail messages", len(notes))
    return notes


def mark_synced(creds, synced_label_name: str, message_ids: list[str]) -> None:
    """Add the synced label to processed messages."""
    if not message_ids:
        return
    service = _get_service(creds)
    synced_label_id = _ensure_label(service, synced_label_name)

    for msg_id in message_ids:
        service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"addLabelIds": [synced_label_id]},
        ).execute()

    log.info("Marked %d Gmail messages as synced", len(message_ids))
