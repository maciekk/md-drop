"""Write notes to the Obsidian vault."""

import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

from md_drop.note import Note

log = logging.getLogger(__name__)


def _slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a filesystem-safe slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text[:max_length].rstrip("-")


def _generate_filename(note: Note) -> str:
    """Generate a filename for a note."""
    date_prefix = note.timestamp.strftime("%Y-%m-%d")
    if note.title:
        slug = _slugify(note.title)
    else:
        slug = _slugify(note.body[:60])
    if not slug:
        slug = "untitled"
    return f"{date_prefix}-{slug}.md"


def _make_unique_path(path: Path) -> Path:
    """If path exists, append a numeric suffix."""
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def write_inbox(note: Note, vault_path: Path, inbox_folder: str) -> Path:
    """Write a note as an individual file in the Inbox folder."""
    inbox_dir = vault_path / inbox_folder
    inbox_dir.mkdir(parents=True, exist_ok=True)

    filename = _generate_filename(note)
    file_path = _make_unique_path(inbox_dir / filename)

    post = frontmatter.Post(
        note.body.strip(),
        date=note.timestamp.isoformat(),
        source=note.source,
        tags=["inbox"],
    )
    if note.title:
        post.metadata["title"] = note.title

    file_path.write_text(frontmatter.dumps(post).replace("\n---\n\n", "\n---\n", 1), encoding="utf-8")
    log.info("Wrote %s", file_path)
    return file_path


def write_daily(
    note: Note,
    vault_path: Path,
    daily_folder: str,
    captures_heading: str,
) -> Path:
    """Append a note under the Captures heading in today's Daily Note."""
    daily_dir = vault_path / daily_folder
    daily_dir.mkdir(parents=True, exist_ok=True)

    date_str = note.timestamp.strftime("%Y-%m-%d")
    file_path = daily_dir / f"{date_str}.md"

    # Build the capture entry
    time_str = note.timestamp.strftime("%H:%M")
    title_part = f"**{note.title}**\n" if note.title else ""
    entry = f"\n### {time_str} ({note.source})\n{title_part}{note.body.strip()}\n"

    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")
        if captures_heading in content:
            # Append after the heading
            idx = content.index(captures_heading) + len(captures_heading)
            content = content[:idx] + entry + content[idx:]
        else:
            content += f"\n{captures_heading}\n{entry}"
        file_path.write_text(content, encoding="utf-8")
    else:
        content = f"# {date_str}\n\n{captures_heading}\n{entry}"
        file_path.write_text(content, encoding="utf-8")

    log.info("Appended to %s", file_path)
    return file_path


def write_note(note: Note, config) -> Path:
    """Write a note using the configured strategy."""
    if config.vault.strategy == "daily":
        return write_daily(
            note,
            config.vault.path,
            config.vault.daily_folder,
            config.vault.daily_captures_heading,
        )
    return write_inbox(note, config.vault.path, config.vault.inbox_folder)
