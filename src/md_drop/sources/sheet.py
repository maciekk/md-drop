"""Google Sheets source — reads pending rows and marks them synced."""

import logging
from datetime import datetime, timezone

from googleapiclient.discovery import build

from md_drop.note import Note

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_service(creds):
    return build("sheets", "v4", credentials=creds)


def fetch_pending(creds, sheet_id: str) -> list[Note]:
    """Read all rows where status column is 'pending'."""
    service = _get_service(creds)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range="A:F")
        .execute()
    )
    rows = result.get("values", [])
    if not rows:
        return []

    # First row is header: timestamp | title | body | source | status | synced_at
    notes = []
    for i, row in enumerate(rows[1:], start=2):  # 1-indexed, skip header
        if len(row) < 5:
            continue
        timestamp_str, title, body, source, status = row[0], row[1], row[2], row[3], row[4]
        if status.strip().lower() != "pending":
            continue
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            timestamp = datetime.now(timezone.utc)
        notes.append(
            Note(
                timestamp=timestamp,
                title=title.strip(),
                body=body.strip(),
                source=source.strip() or "web",
                source_id=str(i),  # Row number in sheet
            )
        )

    log.info("Found %d pending notes in Google Sheet", len(notes))
    return notes


def mark_synced(creds, sheet_id: str, row_numbers: list[int]) -> None:
    """Update status to 'synced' and set synced_at timestamp for given rows."""
    if not row_numbers:
        return
    service = _get_service(creds)
    now = datetime.now(timezone.utc).isoformat()
    data = []
    for row_num in row_numbers:
        data.append(
            {
                "range": f"E{row_num}:F{row_num}",
                "values": [["synced", now]],
            }
        )
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "RAW", "data": data},
    ).execute()
    log.info("Marked %d rows as synced in Google Sheet", len(row_numbers))
