"""Convert HTML content to clean Markdown."""

import re

from markdownify import markdownify


def html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown, cleaning up excessive whitespace."""
    # Remove script and style elements entirely before conversion
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    md = markdownify(html, heading_style="ATX", strip=["img"])
    # Collapse runs of 3+ newlines into 2
    lines = md.split("\n")
    result = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                result.append("")
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result).strip()
