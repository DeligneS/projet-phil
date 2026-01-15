"""ZIP file handler for extracting student submissions."""

import re
import zipfile
import io
from pathlib import PurePosixPath


def extract_student_name_from_moodle_folder(folder_name: str) -> str | None:
    """Extract student name from Moodle submission folder format.

    Moodle format: "Student Name_ID_assignsubmission_type"
    Example: "Abdoul Karim Coulibaly_1236059_assignsubmission_onlinetext"

    Args:
        folder_name: The folder name from Moodle export.

    Returns:
        Extracted student name, or None if not a Moodle format.
    """
    # Moodle pattern: Name_Numbers_assignsubmission_type
    match = re.match(r"^(.+?)_\d+_assignsubmission_", folder_name)
    if match:
        return match.group(1).strip()
    return None


def extract_student_submissions(zip_content: bytes) -> dict[str, list[tuple[str, bytes]]]:
    """Extract student submissions from a ZIP file.

    Supports two formats:
    1. Simple: Each folder at root level = one student
    2. Moodle: Assignment folder > Student_ID_assignsubmission_type > files

    Args:
        zip_content: Raw bytes of the ZIP file.

    Returns:
        Dictionary mapping student names to list of (filename, content) tuples.
    """
    students: dict[str, list[tuple[str, bytes]]] = {}

    with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zf:
        for file_info in zf.infolist():
            # Skip directories and Mac metadata
            if file_info.is_dir() or "__MACOSX" in file_info.filename:
                continue

            # Parse the path
            path = PurePosixPath(file_info.filename)
            parts = path.parts
            filename = path.name

            # Skip hidden files
            if filename.startswith("."):
                continue

            # Skip files at root level
            if len(parts) < 2:
                continue

            # Try to detect Moodle structure (nested folders with student submissions)
            student_name = None

            # Check each folder level for Moodle pattern
            for i, part in enumerate(parts[:-1]):  # Exclude filename
                moodle_name = extract_student_name_from_moodle_folder(part)
                if moodle_name:
                    student_name = moodle_name
                    break

            # Fallback to first folder if not Moodle format
            if student_name is None:
                student_name = parts[0]

            # Read file content
            content = zf.read(file_info.filename)

            if student_name not in students:
                students[student_name] = []

            students[student_name].append((filename, content))

    return students


def get_supported_extensions() -> set[str]:
    """Return the set of supported file extensions."""
    return {".pdf", ".docx", ".xlsx", ".xls", ".txt", ".md", ".html", ".htm"}


def parse_document(filename: str, content: bytes) -> str | None:
    """Parse a document based on its extension.

    Args:
        filename: Name of the file (used to determine type).
        content: Raw bytes of the file.

    Returns:
        Extracted text content, or None if format not supported.
    """
    from .pdf_parser import parse_pdf
    from .docx_parser import parse_docx
    from .excel_parser import parse_excel
    from .html_parser import parse_html

    ext = PurePosixPath(filename).suffix.lower()

    if ext == ".pdf":
        return parse_pdf(content)
    elif ext == ".docx":
        return parse_docx(content)
    elif ext in (".xlsx", ".xls"):
        return parse_excel(content)
    elif ext in (".html", ".htm"):
        return parse_html(content)
    elif ext in (".txt", ".md"):
        return content.decode("utf-8", errors="replace")

    return None
