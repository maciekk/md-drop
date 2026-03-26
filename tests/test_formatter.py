"""Tests for HTML-to-Markdown conversion."""

from md_drop.formatter import html_to_markdown


def test_simple_paragraph():
    assert html_to_markdown("<p>Hello world</p>") == "Hello world"


def test_heading():
    result = html_to_markdown("<h1>Title</h1><p>Body</p>")
    assert "# Title" in result
    assert "Body" in result


def test_bold_and_italic():
    result = html_to_markdown("<p><strong>bold</strong> and <em>italic</em></p>")
    assert "**bold**" in result
    assert "*italic*" in result


def test_link():
    result = html_to_markdown('<p><a href="https://example.com">click</a></p>')
    assert "[click](https://example.com)" in result


def test_unordered_list():
    html = "<ul><li>one</li><li>two</li><li>three</li></ul>"
    result = html_to_markdown(html)
    assert "one" in result
    assert "two" in result
    assert "three" in result


def test_strips_images():
    result = html_to_markdown('<p>text<img src="x.png">more</p>')
    assert "x.png" not in result
    assert "text" in result
    assert "more" in result


def test_strips_scripts():
    result = html_to_markdown("<p>safe</p><script>alert(1)</script>")
    assert "safe" in result
    assert "alert" not in result


def test_collapses_excessive_newlines():
    html = "<p>a</p><br><br><br><br><br><p>b</p>"
    result = html_to_markdown(html)
    # Should not have more than 2 consecutive blank lines
    assert "\n\n\n\n" not in result


def test_empty_input():
    assert html_to_markdown("") == ""


def test_plain_text_passthrough():
    result = html_to_markdown("just plain text")
    assert "just plain text" in result
