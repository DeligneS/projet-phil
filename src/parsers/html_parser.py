"""HTML document parser using BeautifulSoup."""

from bs4 import BeautifulSoup


def parse_html(content: bytes) -> str:
    """Extract text content from an HTML file.

    Args:
        content: Raw bytes of the HTML file.

    Returns:
        Extracted text content.
    """
    # Try to decode with different encodings
    html_text = None
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            html_text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if html_text is None:
        html_text = content.decode("utf-8", errors="replace")

    soup = BeautifulSoup(html_text, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style"]):
        element.decompose()

    # Get text content
    text = soup.get_text(separator="\n")

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    text = "\n".join(line for line in lines if line)

    return text
