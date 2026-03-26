"""Tests for the vault writer."""

from datetime import datetime, timezone
from pathlib import Path

from md_drop.note import Note
from md_drop.writer import (
    _generate_filename,
    _make_unique_path,
    _slugify,
    write_daily,
    write_inbox,
)


# --- _slugify ---


def test_slugify_basic():
    assert _slugify("Hello World") == "hello-world"


def test_slugify_special_chars():
    assert _slugify("What's up? (test)") == "whats-up-test"


def test_slugify_unicode():
    assert _slugify("café résumé") == "cafe-resume"


def test_slugify_max_length():
    result = _slugify("a very long title that exceeds the limit", max_length=10)
    assert len(result) <= 10


def test_slugify_empty():
    assert _slugify("") == ""


def test_slugify_only_special_chars():
    assert _slugify("!!!???") == ""


# --- _generate_filename ---


def _make_note(title="Test Note", body="Some body", ts=None):
    return Note(
        timestamp=ts or datetime(2026, 3, 25, 14, 30, tzinfo=timezone.utc),
        title=title,
        body=body,
        source="web",
    )


def test_generate_filename_with_title():
    note = _make_note(title="My Great Idea")
    filename = _generate_filename(note)
    assert filename == "2026-03-25-my-great-idea.md"


def test_generate_filename_no_title():
    note = _make_note(title="", body="Some quick thought about things")
    filename = _generate_filename(note)
    assert filename.startswith("2026-03-25-")
    assert filename.endswith(".md")
    assert "some-quick-thought" in filename


def test_generate_filename_no_title_no_body():
    note = _make_note(title="", body="")
    filename = _generate_filename(note)
    assert filename == "2026-03-25-untitled.md"


# --- _make_unique_path ---


def test_make_unique_path_no_conflict(tmp_path):
    path = tmp_path / "note.md"
    assert _make_unique_path(path) == path


def test_make_unique_path_with_conflict(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("existing")
    result = _make_unique_path(path)
    assert result == tmp_path / "note-2.md"


def test_make_unique_path_multiple_conflicts(tmp_path):
    for name in ["note.md", "note-2.md", "note-3.md"]:
        (tmp_path / name).write_text("existing")
    result = _make_unique_path(tmp_path / "note.md")
    assert result == tmp_path / "note-4.md"


# --- write_inbox ---


def test_write_inbox_creates_file(tmp_path):
    note = _make_note()
    path = write_inbox(note, tmp_path, "Inbox")
    assert path.exists()
    assert path.parent.name == "Inbox"
    content = path.read_text()
    assert "Some body" in content
    assert "source: web" in content
    assert "tags:" in content


def test_write_inbox_creates_directory(tmp_path):
    note = _make_note()
    write_inbox(note, tmp_path, "Deep/Nested/Inbox")
    assert (tmp_path / "Deep" / "Nested" / "Inbox").is_dir()


def test_write_inbox_includes_title_in_frontmatter(tmp_path):
    note = _make_note(title="Important")
    path = write_inbox(note, tmp_path, "Inbox")
    content = path.read_text()
    assert "title: Important" in content


def test_write_inbox_no_duplicate_filenames(tmp_path):
    note1 = _make_note(title="Same Title")
    note2 = _make_note(title="Same Title")
    path1 = write_inbox(note1, tmp_path, "Inbox")
    path2 = write_inbox(note2, tmp_path, "Inbox")
    assert path1 != path2
    assert path1.exists()
    assert path2.exists()


# --- write_daily ---


def test_write_daily_creates_new_file(tmp_path):
    note = _make_note()
    path = write_daily(note, tmp_path, "Daily", "## Captures")
    assert path.exists()
    assert path.name == "2026-03-25.md"
    content = path.read_text()
    assert "## Captures" in content
    assert "Some body" in content
    assert "(web)" in content


def test_write_daily_appends_to_existing(tmp_path):
    daily_dir = tmp_path / "Daily"
    daily_dir.mkdir()
    existing = daily_dir / "2026-03-25.md"
    existing.write_text("# 2026-03-25\n\n## Captures\n\n### 10:00 (web)\nOld note\n")

    note = _make_note(body="New note")
    write_daily(note, tmp_path, "Daily", "## Captures")

    content = existing.read_text()
    assert "Old note" in content
    assert "New note" in content


def test_write_daily_adds_heading_if_missing(tmp_path):
    daily_dir = tmp_path / "Daily"
    daily_dir.mkdir()
    existing = daily_dir / "2026-03-25.md"
    existing.write_text("# 2026-03-25\n\nSome other content\n")

    note = _make_note()
    write_daily(note, tmp_path, "Daily", "## Captures")

    content = existing.read_text()
    assert "## Captures" in content
    assert "Some body" in content
