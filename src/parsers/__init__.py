from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .excel_parser import parse_excel
from .html_parser import parse_html
from .zip_handler import extract_student_submissions, parse_document, get_supported_extensions
from .url_fetcher import fetch_url_content, parse_urls_from_text, fetch_multiple_urls

__all__ = [
    "parse_pdf",
    "parse_docx",
    "parse_excel",
    "parse_html",
    "extract_student_submissions",
    "parse_document",
    "get_supported_extensions",
    "fetch_url_content",
    "parse_urls_from_text",
    "fetch_multiple_urls",
]
