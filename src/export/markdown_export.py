"""Markdown text export for evaluation results."""

from src.evaluation.llm_evaluator import EvaluationResult


def create_markdown_evaluation(evaluation: EvaluationResult) -> str:
    """Create a Markdown formatted evaluation for a student.

    Args:
        evaluation: Evaluation result for a student.

    Returns:
        Markdown formatted string.
    """
    lines = []

    # Title
    lines.append(f"# Évaluation - {evaluation.student_name}")
    lines.append("")

    # Final grade
    lines.append("## Note finale")
    lines.append("")
    lines.append(f"**{evaluation.note_finale} / {evaluation.note_max}**")
    lines.append("")

    # Criteria section
    lines.append("## Évaluation par critère")
    lines.append("")

    for criterion in evaluation.criteres:
        lines.append(f"### {criterion.nom}")
        lines.append("")
        lines.append(f"**Note :** {criterion.note} / {criterion.note_max}")
        lines.append("")
        lines.append(f"**Commentaire :** {criterion.commentaire}")
        lines.append("")

    # General feedback
    lines.append("## Feedback général")
    lines.append("")
    lines.append(evaluation.feedback_general)
    lines.append("")

    return "\n".join(lines)


def create_markdown_free_format(student_name: str, content: str) -> str:
    """Create a Markdown file from free-format content.

    Args:
        student_name: Name of the student.
        content: The evaluation content.

    Returns:
        Markdown formatted string with title.
    """
    lines = []
    lines.append(f"# Évaluation - {student_name}")
    lines.append("")
    lines.append(content)
    lines.append("")

    return "\n".join(lines)


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename.

    Args:
        name: The desired filename.

    Returns:
        Sanitized filename.
    """
    return "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_"
        for c in name
    )
