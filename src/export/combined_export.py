"""Combined export functions that create ZIP files with main format + markdown txt files."""

import io
import zipfile

from src.evaluation.llm_evaluator import EvaluationResult
from .excel_export import create_excel_report_with_summary
from .word_export import create_word_document, create_free_format_word_document
from .markdown_export import create_markdown_evaluation, create_markdown_free_format, sanitize_filename


def create_combined_export_excel(evaluations: list[EvaluationResult]) -> io.BytesIO:
    """Create a ZIP containing the Excel report and markdown txt files.

    Args:
        evaluations: List of evaluation results.

    Returns:
        BytesIO containing the ZIP file.
    """
    zip_buffer = io.BytesIO()

    # Use ZIP_STORED for better macOS compatibility
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_STORED) as zf:
        # Add Excel report
        excel_buffer = create_excel_report_with_summary(evaluations)
        zf.writestr("evaluations_etudiants.xlsx", excel_buffer.getvalue())

        # Add markdown txt files in a subfolder
        for evaluation in evaluations:
            safe_name = sanitize_filename(evaluation.student_name)
            markdown_content = create_markdown_evaluation(evaluation)
            zf.writestr(f"markdown/{safe_name}.txt", markdown_content.encode("utf-8"))

    zip_buffer.seek(0)
    return zip_buffer


def create_combined_export_word(evaluations: list[EvaluationResult]) -> io.BytesIO:
    """Create a ZIP containing Word documents and markdown txt files.

    Args:
        evaluations: List of evaluation results.

    Returns:
        BytesIO containing the ZIP file.
    """
    zip_buffer = io.BytesIO()

    # Use ZIP_STORED for better macOS compatibility
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_STORED) as zf:
        for evaluation in evaluations:
            safe_name = sanitize_filename(evaluation.student_name)

            # Add Word document
            word_buffer = create_word_document(evaluation)
            zf.writestr(f"word/{safe_name}.docx", word_buffer.getvalue())

            # Add markdown txt file
            markdown_content = create_markdown_evaluation(evaluation)
            zf.writestr(f"markdown/{safe_name}.txt", markdown_content.encode("utf-8"))

    zip_buffer.seek(0)
    return zip_buffer


def create_combined_export_free_format(
    evaluations: list[tuple[str, str]],
) -> io.BytesIO:
    """Create a ZIP containing free-format Word documents and markdown txt files.

    Args:
        evaluations: List of (student_name, content) tuples.

    Returns:
        BytesIO containing the ZIP file.
    """
    zip_buffer = io.BytesIO()

    # Use ZIP_STORED for better macOS compatibility
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_STORED) as zf:
        for student_name, content in evaluations:
            safe_name = sanitize_filename(student_name)

            # Add Word document
            word_buffer = create_free_format_word_document(student_name, content)
            zf.writestr(f"word/{safe_name}.docx", word_buffer.getvalue())

            # Add markdown txt file
            markdown_content = create_markdown_free_format(student_name, content)
            zf.writestr(f"markdown/{safe_name}.txt", markdown_content.encode("utf-8"))

    zip_buffer.seek(0)
    return zip_buffer
