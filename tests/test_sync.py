"""Tests for sync orchestrator — pure logic parts."""

from datetime import datetime, timezone

from md_drop.note import Note
from md_drop.sync import _content_hash


def _make_note(title="Test", body="Body"):
    return Note(
        timestamp=datetime(2026, 3, 25, tzinfo=timezone.utc),
        title=title,
        body=body,
        source="web",
    )


def test_content_hash_deterministic():
    note = _make_note()
    assert _content_hash(note) == _content_hash(note)


def test_content_hash_differs_by_title():
    a = _make_note(title="A")
    b = _make_note(title="B")
    assert _content_hash(a) != _content_hash(b)


def test_content_hash_differs_by_body():
    a = _make_note(body="one")
    b = _make_note(body="two")
    assert _content_hash(a) != _content_hash(b)


def test_content_hash_ignores_metadata():
    a = _make_note()
    b = _make_note()
    b.source = "email"
    b.source_id = "abc123"
    # Same title+body = same hash regardless of source
    assert _content_hash(a) == _content_hash(b)


def test_content_hash_length():
    note = _make_note()
    assert len(_content_hash(note)) == 16
