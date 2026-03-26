"""Main sync orchestrator — CLI entry point."""

import hashlib
import logging
import sys
import time
from pathlib import Path

import click
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from md_drop.config import Config, load_config
from md_drop.note import Note
from md_drop.sources import gmail, sheet
from md_drop.writer import write_note

log = logging.getLogger("md_drop")

ALL_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _get_credentials(config: Config) -> Credentials:
    """Load or create OAuth2 credentials."""
    creds = None
    token_path = config.google.token_file
    creds_path = config.google.credentials_file

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), ALL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                click.echo(
                    f"Error: credentials file not found at {creds_path}\n"
                    "Download OAuth credentials from Google Cloud Console.\n"
                    "See README.md for setup instructions.",
                    err=True,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), ALL_SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
        log.info("Saved credentials to %s", token_path)

    return creds


def _content_hash(note: Note) -> str:
    """Generate a hash for deduplication."""
    content = f"{note.title}|{note.body}".encode("utf-8")
    return hashlib.sha256(content).hexdigest()[:16]


def _run_sync(config: Config, dry_run: bool) -> int:
    """Run one sync cycle. Returns number of notes synced."""
    creds = _get_credentials(config)
    all_notes: list[Note] = []

    # Fetch from Google Sheet
    if config.google.sheet_id:
        try:
            sheet_notes = sheet.fetch_pending(creds, config.google.sheet_id)
            all_notes.extend(sheet_notes)
        except Exception:
            log.exception("Error fetching from Google Sheet")

    # Fetch from Gmail
    if config.gmail.enabled:
        try:
            gmail_notes = gmail.fetch_pending(
                creds, config.gmail.label, config.gmail.synced_label
            )
            all_notes.extend(gmail_notes)
        except Exception:
            log.exception("Error fetching from Gmail")

    if not all_notes:
        log.info("No pending notes found")
        return 0

    # Deduplicate by content hash
    seen_hashes: set[str] = set()
    unique_notes: list[Note] = []
    for note in all_notes:
        h = _content_hash(note)
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_notes.append(note)
        else:
            log.info("Skipping duplicate: %s", note.title or note.body[:40])

    log.info("Syncing %d notes (%d duplicates removed)",
             len(unique_notes), len(all_notes) - len(unique_notes))

    if dry_run:
        for note in unique_notes:
            click.echo(
                f"[DRY RUN] Would write: {note.source} | "
                f"{note.title or note.body[:40]}"
            )
        return len(unique_notes)

    # Write notes to vault
    sheet_rows_to_mark: list[int] = []
    gmail_ids_to_mark: list[str] = []

    for note in unique_notes:
        try:
            write_note(note, config)
            if note.source == "web":
                sheet_rows_to_mark.append(int(note.source_id))
            elif note.source == "email":
                gmail_ids_to_mark.append(note.source_id)
        except Exception:
            log.exception("Error writing note: %s", note.title or note.body[:40])

    # Mark sources as synced
    if sheet_rows_to_mark and config.google.sheet_id:
        try:
            sheet.mark_synced(creds, config.google.sheet_id, sheet_rows_to_mark)
        except Exception:
            log.exception("Error marking sheet rows as synced")

    if gmail_ids_to_mark:
        try:
            gmail.mark_synced(creds, config.gmail.synced_label, gmail_ids_to_mark)
        except Exception:
            log.exception("Error marking Gmail messages as synced")

    return len(unique_notes)


@click.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to config file (default: ~/.config/md-drop/config.toml)",
)
@click.option(
    "--vault",
    type=click.Path(path_type=Path),
    default=None,
    help="Override vault path from config",
)
@click.option("--dry-run", is_flag=True, help="Show what would be synced without writing")
@click.option("--once", is_flag=True, help="Run once and exit (default: loop)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def main(config_path, vault, dry_run, once, verbose):
    """Sync captured Markdown content into your Obsidian vault."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config(config_path or Path("~/.config/md-drop/config.toml").expanduser())
    if vault:
        cfg.vault.path = vault

    if not cfg.vault.path.exists():
        click.echo(f"Error: vault path does not exist: {cfg.vault.path}", err=True)
        sys.exit(1)

    if once:
        count = _run_sync(cfg, dry_run)
        click.echo(f"Synced {count} notes." if count else "Nothing to sync.")
    else:
        click.echo(
            f"Starting sync loop (every {cfg.sync.interval_seconds}s). Ctrl+C to stop."
        )
        while True:
            try:
                _run_sync(cfg, dry_run)
            except KeyboardInterrupt:
                break
            except Exception:
                log.exception("Error in sync loop")
            time.sleep(cfg.sync.interval_seconds)


if __name__ == "__main__":
    main()
