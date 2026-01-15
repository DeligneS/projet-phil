"""PDF document parser using PyMuPDF."""

import pymupdf


def parse_pdf(content: bytes) -> str:
    """Extract text content from a PDF file.

    Args:
        content: Raw bytes of the PDF file.

    Returns:
        Extracted text from all pages of the PDF.
    """
    text_parts = []

    with pymupdf.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())

    return "\n\n".join(text_parts)
