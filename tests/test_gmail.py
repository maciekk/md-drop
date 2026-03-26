"""Tests for Gmail source — focuses on _extract_body (pure logic)."""

import base64

from md_drop.sources.gmail import _extract_body


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


def test_extract_plain_text_single_part():
    payload = {
        "mimeType": "text/plain",
        "body": {"data": _b64("Hello world")},
    }
    text, is_html = _extract_body(payload)
    assert text == "Hello world"
    assert is_html is False


def test_extract_html_single_part():
    payload = {
        "mimeType": "text/html",
        "body": {"data": _b64("<p>Hello</p>")},
    }
    text, is_html = _extract_body(payload)
    assert text == "<p>Hello</p>"
    assert is_html is True


def test_extract_multipart_prefers_plain():
    payload = {
        "mimeType": "multipart/alternative",
        "body": {},
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {"data": _b64("Plain version")},
            },
            {
                "mimeType": "text/html",
                "body": {"data": _b64("<p>HTML version</p>")},
            },
        ],
    }
    text, is_html = _extract_body(payload)
    assert text == "Plain version"
    assert is_html is False


def test_extract_multipart_falls_back_to_html():
    payload = {
        "mimeType": "multipart/alternative",
        "body": {},
        "parts": [
            {
                "mimeType": "text/html",
                "body": {"data": _b64("<p>HTML only</p>")},
            },
        ],
    }
    text, is_html = _extract_body(payload)
    assert text == "<p>HTML only</p>"
    assert is_html is True


def test_extract_nested_multipart():
    payload = {
        "mimeType": "multipart/mixed",
        "body": {},
        "parts": [
            {
                "mimeType": "multipart/alternative",
                "body": {},
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": _b64("Nested plain")},
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": _b64("<p>Nested HTML</p>")},
                    },
                ],
            },
            {
                "mimeType": "application/pdf",
                "body": {},
            },
        ],
    }
    text, is_html = _extract_body(payload)
    assert text == "Nested plain"
    assert is_html is False


def test_extract_empty_payload():
    payload = {"mimeType": "multipart/mixed", "body": {}, "parts": []}
    text, is_html = _extract_body(payload)
    assert text == ""
    assert is_html is False


def test_extract_no_body_data():
    payload = {"mimeType": "text/plain", "body": {}}
    text, is_html = _extract_body(payload)
    assert text == ""
    assert is_html is False
