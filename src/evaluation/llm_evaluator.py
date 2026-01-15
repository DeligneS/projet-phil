"""LLM-based student work evaluator using OpenAI."""

import asyncio
import json
from dataclasses import dataclass
from openai import OpenAI, AsyncOpenAI


@dataclass
class CriterionEvaluation:
    """Evaluation of a single criterion."""

    nom: str
    note: int
    note_max: int
    commentaire: str


@dataclass
class EvaluationResult:
    """Complete evaluation result for a student."""

    student_name: str
    feedback_general: str
    criteres: list[CriterionEvaluation]
    note_finale: float
    note_max: float


EVALUATION_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "evaluation_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "feedback_general": {
                    "type": "string",
                    "description": "General feedback about the student's work",
                },
                "criteres": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "nom": {
                                "type": "string",
                                "description": "Name of the evaluation criterion",
                            },
                            "note": {
                                "type": "integer",
                                "description": "Score for this criterion",
                            },
                            "note_max": {
                                "type": "integer",
                                "description": "Maximum possible score for this criterion",
                            },
                            "commentaire": {
                                "type": "string",
                                "description": "Comment explaining the score",
                            },
                        },
                        "required": ["nom", "note", "note_max", "commentaire"],
                        "additionalProperties": False,
                    },
                    "description": "List of criterion evaluations",
                },
                "note_finale": {
                    "type": "number",
                    "description": "Final grade",
                },
                "note_max": {
                    "type": "number",
                    "description": "Maximum possible grade",
                },
            },
            "required": ["feedback_general", "criteres", "note_finale", "note_max"],
            "additionalProperties": False,
        },
    },
}


def build_evaluation_prompt(
    student_work: str,
    evaluation_grid: str,
    knowledge_base: str,
    custom_instructions: str,
) -> str:
    """Build the user prompt for evaluation.

    Args:
        student_work: The student's submitted work content.
        evaluation_grid: The evaluation criteria/rubric.
        knowledge_base: Reference materials for evaluation.
        custom_instructions: Additional instructions from the professor.

    Returns:
        Formatted prompt string.
    """
    prompt_parts = []

    prompt_parts.append("## Grille d'évaluation\n")
    prompt_parts.append(evaluation_grid)

    if knowledge_base:
        prompt_parts.append("\n\n## Base de connaissances / Documents de référence\n")
        prompt_parts.append(knowledge_base)

    if custom_instructions:
        prompt_parts.append("\n\n## Instructions supplémentaires du professeur\n")
        prompt_parts.append(custom_instructions)

    prompt_parts.append("\n\n## Travail de l'étudiant à évaluer\n")
    prompt_parts.append(student_work)

    return "\n".join(prompt_parts)


def evaluate_student_work(
    client: OpenAI,
    student_name: str,
    student_work: str,
    evaluation_grid: str,
    knowledge_base: str,
    system_prompt: str,
    custom_instructions: str = "",
    model: str = "gpt-4o",
) -> EvaluationResult:
    """Evaluate a student's work using an LLM.

    Args:
        client: OpenAI client instance.
        student_name: Name of the student being evaluated.
        student_work: The student's submitted work content.
        evaluation_grid: The evaluation criteria/rubric.
        knowledge_base: Reference materials for evaluation.
        system_prompt: System prompt for the LLM.
        custom_instructions: Additional instructions from the professor.
        model: OpenAI model to use.

    Returns:
        EvaluationResult containing feedback and grades.
    """
    user_prompt = build_evaluation_prompt(
        student_work=student_work,
        evaluation_grid=evaluation_grid,
        knowledge_base=knowledge_base,
        custom_instructions=custom_instructions,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=EVALUATION_JSON_SCHEMA,
        temperature=0.3,  # Lower temperature for more consistent evaluations
    )

    result_json = json.loads(response.choices[0].message.content)

    criteres = [
        CriterionEvaluation(
            nom=c["nom"],
            note=c["note"],
            note_max=c["note_max"],
            commentaire=c["commentaire"],
        )
        for c in result_json["criteres"]
    ]

    return EvaluationResult(
        student_name=student_name,
        feedback_general=result_json["feedback_general"],
        criteres=criteres,
        note_finale=result_json["note_finale"],
        note_max=result_json["note_max"],
    )


def evaluate_student_work_free_format(
    client: OpenAI,
    student_name: str,
    student_work: str,
    evaluation_grid: str,
    knowledge_base: str,
    system_prompt: str,
    output_format_instructions: str,
    custom_instructions: str = "",
    model: str = "gpt-4o",
) -> str:
    """Evaluate a student's work with free-format output.

    Args:
        client: OpenAI client instance.
        student_name: Name of the student being evaluated.
        student_work: The student's submitted work content.
        evaluation_grid: The evaluation criteria/rubric.
        knowledge_base: Reference materials for evaluation.
        system_prompt: System prompt for the LLM.
        output_format_instructions: Instructions for how to format the output.
        custom_instructions: Additional instructions from the professor.
        model: OpenAI model to use.

    Returns:
        Free-form text evaluation.
    """
    prompt_parts = []

    if evaluation_grid:
        prompt_parts.append("## Grille d'évaluation\n")
        prompt_parts.append(evaluation_grid)

    if knowledge_base:
        prompt_parts.append("\n\n## Base de connaissances / Documents de référence\n")
        prompt_parts.append(knowledge_base)

    if custom_instructions:
        prompt_parts.append("\n\n## Instructions supplémentaires du professeur\n")
        prompt_parts.append(custom_instructions)

    prompt_parts.append("\n\n## Format de sortie attendu\n")
    prompt_parts.append(output_format_instructions)

    prompt_parts.append(f"\n\n## Travail de l'étudiant ({student_name}) à évaluer\n")
    prompt_parts.append(student_work)

    user_prompt = "\n".join(prompt_parts)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


# =============================================================================
# Async versions for parallel processing
# =============================================================================


async def evaluate_student_work_async(
    client: AsyncOpenAI,
    student_name: str,
    student_work: str,
    evaluation_grid: str,
    knowledge_base: str,
    system_prompt: str,
    custom_instructions: str = "",
    model: str = "gpt-4o",
) -> EvaluationResult:
    """Async version: Evaluate a student's work using an LLM.

    Args:
        client: AsyncOpenAI client instance.
        student_name: Name of the student being evaluated.
        student_work: The student's submitted work content.
        evaluation_grid: The evaluation criteria/rubric.
        knowledge_base: Reference materials for evaluation.
        system_prompt: System prompt for the LLM.
        custom_instructions: Additional instructions from the professor.
        model: OpenAI model to use.

    Returns:
        EvaluationResult containing feedback and grades.
    """
    user_prompt = build_evaluation_prompt(
        student_work=student_work,
        evaluation_grid=evaluation_grid,
        knowledge_base=knowledge_base,
        custom_instructions=custom_instructions,
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=EVALUATION_JSON_SCHEMA,
        temperature=0.3,
    )

    result_json = json.loads(response.choices[0].message.content)

    criteres = [
        CriterionEvaluation(
            nom=c["nom"],
            note=c["note"],
            note_max=c["note_max"],
            commentaire=c["commentaire"],
        )
        for c in result_json["criteres"]
    ]

    return EvaluationResult(
        student_name=student_name,
        feedback_general=result_json["feedback_general"],
        criteres=criteres,
        note_finale=result_json["note_finale"],
        note_max=result_json["note_max"],
    )


async def evaluate_student_work_free_format_async(
    client: AsyncOpenAI,
    student_name: str,
    student_work: str,
    evaluation_grid: str,
    knowledge_base: str,
    system_prompt: str,
    output_format_instructions: str,
    custom_instructions: str = "",
    model: str = "gpt-4o",
) -> str:
    """Async version: Evaluate a student's work with free-format output.

    Args:
        client: AsyncOpenAI client instance.
        student_name: Name of the student being evaluated.
        student_work: The student's submitted work content.
        evaluation_grid: The evaluation criteria/rubric.
        knowledge_base: Reference materials for evaluation.
        system_prompt: System prompt for the LLM.
        output_format_instructions: Instructions for how to format the output.
        custom_instructions: Additional instructions from the professor.
        model: OpenAI model to use.

    Returns:
        Free-form text evaluation.
    """
    prompt_parts = []

    if evaluation_grid:
        prompt_parts.append("## Grille d'évaluation\n")
        prompt_parts.append(evaluation_grid)

    if knowledge_base:
        prompt_parts.append("\n\n## Base de connaissances / Documents de référence\n")
        prompt_parts.append(knowledge_base)

    if custom_instructions:
        prompt_parts.append("\n\n## Instructions supplémentaires du professeur\n")
        prompt_parts.append(custom_instructions)

    prompt_parts.append("\n\n## Format de sortie attendu\n")
    prompt_parts.append(output_format_instructions)

    prompt_parts.append(f"\n\n## Travail de l'étudiant ({student_name}) à évaluer\n")
    prompt_parts.append(student_work)

    user_prompt = "\n".join(prompt_parts)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


async def evaluate_all_students_async(
    client: AsyncOpenAI,
    student_submissions: dict[str, str],
    evaluation_grid: str,
    knowledge_base: str,
    system_prompt: str,
    custom_instructions: str = "",
    model: str = "gpt-4o",
    max_concurrent: int = 5,
    progress_callback: callable = None,
) -> list[EvaluationResult | Exception]:
    """Evaluate all students in parallel with concurrency control.

    Args:
        client: AsyncOpenAI client instance.
        student_submissions: Dict mapping student_name to their work content.
        evaluation_grid: The evaluation criteria/rubric.
        knowledge_base: Reference materials for evaluation.
        system_prompt: System prompt for the LLM.
        custom_instructions: Additional instructions from the professor.
        model: OpenAI model to use.
        max_concurrent: Maximum number of concurrent API calls.
        progress_callback: Optional callback(completed, total) for progress updates.

    Returns:
        List of EvaluationResult or Exception for each student.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    completed = 0
    total = len(student_submissions)

    async def evaluate_with_semaphore(student_name: str, student_work: str):
        nonlocal completed
        async with semaphore:
            try:
                result = await evaluate_student_work_async(
                    client=client,
                    student_name=student_name,
                    student_work=student_work,
                    evaluation_grid=evaluation_grid,
                    knowledge_base=knowledge_base,
                    system_prompt=system_prompt,
                    custom_instructions=custom_instructions,
                    model=model,
                )
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, student_name)
                return result
            except Exception as e:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, student_name)
                return e

    tasks = [
        evaluate_with_semaphore(name, work)
        for name, work in student_submissions.items()
    ]

    return await asyncio.gather(*tasks)


async def evaluate_all_students_free_format_async(
    client: AsyncOpenAI,
    student_submissions: dict[str, str],
    evaluation_grid: str,
    knowledge_base: str,
    system_prompt: str,
    output_format_instructions: str,
    custom_instructions: str = "",
    model: str = "gpt-4o",
    max_concurrent: int = 5,
    progress_callback: callable = None,
) -> list[tuple[str, str | Exception]]:
    """Evaluate all students in parallel with free-format output.

    Args:
        client: AsyncOpenAI client instance.
        student_submissions: Dict mapping student_name to their work content.
        evaluation_grid: The evaluation criteria/rubric.
        knowledge_base: Reference materials for evaluation.
        system_prompt: System prompt for the LLM.
        output_format_instructions: Instructions for output format.
        custom_instructions: Additional instructions from the professor.
        model: OpenAI model to use.
        max_concurrent: Maximum number of concurrent API calls.
        progress_callback: Optional callback(completed, total) for progress updates.

    Returns:
        List of (student_name, content or Exception) tuples.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    completed = 0
    total = len(student_submissions)

    async def evaluate_with_semaphore(student_name: str, student_work: str):
        nonlocal completed
        async with semaphore:
            try:
                result = await evaluate_student_work_free_format_async(
                    client=client,
                    student_name=student_name,
                    student_work=student_work,
                    evaluation_grid=evaluation_grid,
                    knowledge_base=knowledge_base,
                    system_prompt=system_prompt,
                    output_format_instructions=output_format_instructions,
                    custom_instructions=custom_instructions,
                    model=model,
                )
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, student_name)
                return (student_name, result)
            except Exception as e:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, student_name)
                return (student_name, e)

    tasks = [
        evaluate_with_semaphore(name, work)
        for name, work in student_submissions.items()
    ]

    return await asyncio.gather(*tasks)
