"""Student evaluation application using Streamlit and OpenAI."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from openai import AsyncOpenAI

# Load environment variables from .env file
load_dotenv()

from src.parsers import extract_student_submissions, parse_document, fetch_multiple_urls, parse_urls_from_text
from src.evaluation import (
    evaluate_all_students_async,
    evaluate_all_students_free_format_async,
    EvaluationResult,
)
from src.export import (
    create_combined_export_excel,
    create_combined_export_word,
    create_combined_export_free_format,
)

# Page configuration
st.set_page_config(
    page_title="Évaluation des travaux étudiants",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Évaluation des travaux étudiants")
st.markdown("---")


def load_default_system_prompt() -> str:
    """Load the default system prompt from file."""
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""


def parse_uploaded_files(files: list) -> str:
    """Parse and concatenate content from multiple uploaded files."""
    if not files:
        return ""

    contents = []
    for file in files:
        content = file.read()
        file.seek(0)  # Reset file pointer for potential re-read

        parsed = parse_document(file.name, content)
        if parsed:
            contents.append(f"=== {file.name} ===\n{parsed}")

    return "\n\n".join(contents)


# Initialize async OpenAI client
@st.cache_resource
def get_async_openai_client():
    """Get or create async OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return AsyncOpenAI(api_key=api_key)


async_client = get_async_openai_client()

if not async_client:
    st.error(
        "⚠️ Clé API OpenAI non configurée. "
        "Veuillez définir la variable d'environnement `OPENAI_API_KEY`."
    )
    st.stop()

# Three column layout for inputs
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📋 Grille d'évaluation")

    eval_grid_files = st.file_uploader(
        label="Fichiers (PDF, Word, Excel, TXT, HTML)",
        type=["pdf", "docx", "xlsx", "txt", "html", "htm"],
        accept_multiple_files=True,
        help="Uploadez un ou plusieurs fichiers contenant la grille d'évaluation",
        key="eval_grid",
    )

    eval_grid_text = st.text_area(
        label="Ou saisissez directement la grille",
        placeholder="Collez ici votre grille d'évaluation, critères, barème...",
        height=150,
        key="eval_grid_text",
        help="Vous pouvez combiner fichiers et texte",
    )

with col2:
    st.subheader("📁 Travaux étudiants")
    student_zip = st.file_uploader(
        label="Fichier ZIP des travaux",
        type=["zip"],
        accept_multiple_files=False,
        help="ZIP contenant un dossier par étudiant (nom du dossier = nom de l'étudiant)",
        key="student_zip",
    )

with col3:
    st.subheader("📖 Base de connaissances")

    knowledge_files = st.file_uploader(
        label="Fichiers (PDF, Word, Excel, TXT, HTML)",
        type=["pdf", "docx", "xlsx", "txt", "html", "htm"],
        accept_multiple_files=True,
        help="Documents servant de référence pour l'évaluation",
        key="knowledge",
    )

    knowledge_urls = st.text_area(
        label="URLs (une par ligne)",
        placeholder="https://exemple.com/cours\nhttps://autre-site.com/reference",
        height=80,
        key="knowledge_urls",
        help="Le contenu des pages web sera extrait automatiquement",
    )

    knowledge_text = st.text_area(
        label="Ou saisissez directement du contenu",
        placeholder="Collez ici des informations de référence, extraits de cours, définitions...",
        height=150,
        key="knowledge_text",
        help="Vous pouvez combiner fichiers, URLs et texte",
    )

st.markdown("---")

# Output format section
st.subheader("📤 Format de sortie")

OUTPUT_FORMATS = {
    "excel": "Excel (un fichier, une sheet par étudiant)",
    "word_structured": "Word structuré (un document par étudiant, sections par critère)",
    "word_free": "Word libre (format personnalisé)",
}

output_format = st.radio(
    label="Choisissez le format de sortie",
    options=list(OUTPUT_FORMATS.keys()),
    format_func=lambda x: OUTPUT_FORMATS[x],
    horizontal=True,
)

# Show output format instructions for free format
output_format_instructions = ""
if output_format == "word_free":
    output_format_instructions = st.text_area(
        label="Instructions pour le format de sortie",
        placeholder="Décrivez comment vous souhaitez que l'évaluation soit formatée...\n\nExemple:\n- Commencer par un résumé en 2-3 phrases\n- Lister les points forts\n- Lister les axes d'amélioration\n- Terminer par une note globale",
        height=150,
        help="Ces instructions définissent la structure du document de sortie",
    )

st.markdown("---")

# Custom instructions section
st.subheader("💬 Instructions personnalisées")
default_prompt = load_default_system_prompt()

custom_instructions = st.text_area(
    label="Instructions supplémentaires pour l'évaluation",
    placeholder="Ajoutez ici des instructions spécifiques pour guider l'évaluation...",
    height=100,
    help="Ces instructions seront ajoutées au prompt envoyé au LLM",
)

# Advanced settings in expander
with st.expander("⚙️ Paramètres avancés"):
    model = st.selectbox(
        "Modèle OpenAI",
        options=["gpt-5.2", "gpt-4.1", "gpt-4o"],
        index=0,
        help="Modèle à utiliser pour l'évaluation",
    )

    max_concurrent = st.slider(
        "Évaluations parallèles",
        min_value=1,
        max_value=1000,
        value=5,
        help="Nombre d'évaluations simultanées (plus = plus rapide, mais attention aux limites de l'API)",
    )

    if st.checkbox("Modifier le prompt système", value=False):
        system_prompt = st.text_area(
            label="Prompt système",
            value=default_prompt,
            height=200,
        )
    else:
        system_prompt = default_prompt

st.markdown("---")

# Evaluation button and results
if st.button("🚀 Lancer l'évaluation", type="primary", use_container_width=True):
    # Validation
    has_eval_grid = eval_grid_files or eval_grid_text.strip()

    # For structured formats, we need an evaluation grid
    if output_format in ("excel", "word_structured") and not has_eval_grid:
        st.error("❌ Veuillez fournir une grille d'évaluation (fichier ou texte).")
        st.stop()

    # For free format, we need output instructions
    if output_format == "word_free" and not output_format_instructions.strip():
        st.error("❌ Veuillez fournir des instructions pour le format de sortie.")
        st.stop()

    if not student_zip:
        st.error("❌ Veuillez uploader le fichier ZIP des travaux étudiants.")
        st.stop()

    # Parse evaluation grid (combine files + text)
    with st.spinner("Lecture de la grille d'évaluation..."):
        eval_grid_parts = []

        # Parse uploaded files
        if eval_grid_files:
            files_content = parse_uploaded_files(eval_grid_files)
            if files_content:
                eval_grid_parts.append(files_content)

        # Add text input
        if eval_grid_text.strip():
            eval_grid_parts.append(f"=== Texte saisi ===\n{eval_grid_text.strip()}")

        eval_grid_content = "\n\n".join(eval_grid_parts)

    if not eval_grid_content:
        st.error("❌ Impossible de lire la grille d'évaluation.")
        st.stop()

    # Parse knowledge base (combine files + URLs + text)
    with st.spinner("Lecture de la base de connaissances..."):
        knowledge_parts = []

        # Parse uploaded files
        if knowledge_files:
            files_content = parse_uploaded_files(knowledge_files)
            if files_content:
                knowledge_parts.append(files_content)

        # Fetch URL content
        if knowledge_urls.strip():
            urls = parse_urls_from_text(knowledge_urls)
            if urls:
                st.info(f"🌐 Récupération du contenu de {len(urls)} URL(s)...")
                url_contents = fetch_multiple_urls(urls)
                for url, content in url_contents:
                    knowledge_parts.append(f"=== {url} ===\n{content}")
                if len(url_contents) < len(urls):
                    st.warning(f"⚠️ {len(urls) - len(url_contents)} URL(s) n'ont pas pu être récupérées.")

        # Add text input
        if knowledge_text.strip():
            knowledge_parts.append(f"=== Texte saisi ===\n{knowledge_text.strip()}")

        knowledge_content = "\n\n".join(knowledge_parts)

    # Extract student submissions
    with st.spinner("Extraction des travaux étudiants..."):
        zip_content = student_zip.read()
        student_submissions = extract_student_submissions(zip_content)

    if not student_submissions:
        st.error("❌ Aucun travail d'étudiant trouvé dans le ZIP.")
        st.stop()

    st.success(f"✅ {len(student_submissions)} étudiants trouvés")

    # Parse all student works first (fast, synchronous)
    with st.spinner("Analyse des fichiers étudiants..."):
        parsed_submissions: dict[str, str] = {}
        for student_name, files in student_submissions.items():
            student_work_parts = []
            for filename, content in files:
                parsed = parse_document(filename, content)
                if parsed:
                    student_work_parts.append(f"=== {filename} ===\n{parsed}")

            if student_work_parts:
                parsed_submissions[student_name] = "\n\n".join(student_work_parts)
            else:
                st.warning(f"⚠️ Aucun fichier lisible pour {student_name}")

    if not parsed_submissions:
        st.error("❌ Aucun travail lisible trouvé.")
        st.stop()

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text(f"Évaluation en cours (0/{len(parsed_submissions)})...")

    # Define progress callback for async evaluation
    def update_progress(completed: int, total: int, student_name: str):
        progress_bar.progress(completed / total)
        status_text.text(f"Évaluation en cours ({completed}/{total}) - Terminé: {student_name}")

    if output_format == "word_free":
        # Free format evaluation - async parallel processing
        results = asyncio.run(
            evaluate_all_students_free_format_async(
                client=async_client,
                student_submissions=parsed_submissions,
                evaluation_grid=eval_grid_content,
                knowledge_base=knowledge_content,
                system_prompt=system_prompt,
                output_format_instructions=output_format_instructions,
                custom_instructions=custom_instructions,
                model=model,
                max_concurrent=max_concurrent,
                progress_callback=update_progress,
            )
        )

        progress_bar.progress(1.0)
        status_text.text("Évaluation terminée!")

        # Process results
        free_evaluations: list[tuple[str, str]] = []
        for student_name, result in results:
            if isinstance(result, Exception):
                st.error(f"❌ Erreur pour {student_name}: {result}")
            else:
                free_evaluations.append((student_name, result))

        if free_evaluations:
            st.success(f"✅ {len(free_evaluations)} étudiants évalués avec succès!")

            # Generate combined ZIP (Word + Markdown txt)
            with st.spinner("Génération des documents..."):
                zip_buffer = create_combined_export_free_format(free_evaluations)

            # Download button
            st.download_button(
                label="📥 Télécharger (ZIP: Word + Markdown)",
                data=zip_buffer,
                file_name="evaluations_etudiants.zip",
                mime="application/zip",
                type="primary",
            )

            # Show preview
            st.markdown("### 📝 Aperçu des évaluations")
            for student_name, content in free_evaluations:
                with st.expander(student_name):
                    st.markdown(content)
        else:
            st.error("❌ Aucune évaluation n'a pu être effectuée.")

    else:
        # Structured evaluation (Excel or Word structured) - async parallel processing
        results = asyncio.run(
            evaluate_all_students_async(
                client=async_client,
                student_submissions=parsed_submissions,
                evaluation_grid=eval_grid_content,
                knowledge_base=knowledge_content,
                system_prompt=system_prompt,
                custom_instructions=custom_instructions,
                model=model,
                max_concurrent=max_concurrent,
                progress_callback=update_progress,
            )
        )

        progress_bar.progress(1.0)
        status_text.text("Évaluation terminée!")

        # Process results
        evaluations: list[EvaluationResult] = []
        for result in results:
            if isinstance(result, Exception):
                st.error(f"❌ Erreur: {result}")
            else:
                evaluations.append(result)

        if evaluations:
            st.success(f"✅ {len(evaluations)} étudiants évalués avec succès!")

            # Generate combined report based on output format (main format + markdown txt)
            if output_format == "excel":
                with st.spinner("Génération des documents..."):
                    zip_buffer = create_combined_export_excel(evaluations)

                st.download_button(
                    label="📥 Télécharger (ZIP: Excel + Markdown)",
                    data=zip_buffer,
                    file_name="evaluations_etudiants.zip",
                    mime="application/zip",
                    type="primary",
                )

            elif output_format == "word_structured":
                with st.spinner("Génération des documents..."):
                    zip_buffer = create_combined_export_word(evaluations)

                st.download_button(
                    label="📥 Télécharger (ZIP: Word + Markdown)",
                    data=zip_buffer,
                    file_name="evaluations_etudiants.zip",
                    mime="application/zip",
                    type="primary",
                )

            # Show summary
            st.markdown("### 📊 Résumé des évaluations")
            summary_data = [
                {
                    "Étudiant": e.student_name,
                    "Note": f"{e.note_finale} / {e.note_max}",
                }
                for e in evaluations
            ]
            st.dataframe(summary_data)

            # Expandable details for each student
            st.markdown("### 📝 Détails par étudiant")
            for evaluation in evaluations:
                with st.expander(f"{evaluation.student_name} - {evaluation.note_finale}/{evaluation.note_max}"):
                    st.markdown("**Feedback général:**")
                    st.write(evaluation.feedback_general)

                    st.markdown("**Critères:**")
                    criteria_data = [
                        {
                            "Critère": c.nom,
                            "Note": f"{c.note}/{c.note_max}",
                            "Commentaire": c.commentaire,
                        }
                        for c in evaluation.criteres
                    ]
                    st.dataframe(criteria_data)
        else:
            st.error("❌ Aucune évaluation n'a pu être effectuée.")
