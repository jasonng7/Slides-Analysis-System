from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DECKS_DIR = PROJECT_ROOT / "input_decks"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = PROJECT_ROOT / "data"

OUTPUT_DIRECTORIES = {
    "slide_images": OUTPUT_DIR / "slide_images",
    "extracted_text": OUTPUT_DIR / "extracted_text",
    "parsed_objects": OUTPUT_DIR / "parsed_objects",
    "classified_slides": OUTPUT_DIR / "classified_slides",
    "content_analysis": OUTPUT_DIR / "content_analysis",
    "content_raw_text": OUTPUT_DIR / "content_analysis" / "raw_text",
    "content_analysis_json": OUTPUT_DIR / "content_analysis" / "analysis",
    "content_chunks": OUTPUT_DIR / "content_analysis" / "chunks",
    "content_errors": OUTPUT_DIR / "content_analysis" / "errors",
    "embeddings": OUTPUT_DIR / "embeddings",
    "text_embeddings": OUTPUT_DIR / "embeddings" / "text",
    "generated_decks": OUTPUT_DIR / "generated_decks",
    "generated_deck_logs": OUTPUT_DIR / "generated_decks" / "logs",
    "generated_deck_metadata": OUTPUT_DIR / "generated_decks" / "metadata",
    "slide_plans": OUTPUT_DIR / "slide_plans",
    "slide_plan_errors": OUTPUT_DIR / "slide_plans" / "errors",
    "generated_templates": OUTPUT_DIR / "generated_templates",
    "qa_reports": OUTPUT_DIR / "qa_reports",
    "qa_reports_json": OUTPUT_DIR / "qa_reports" / "json",
    "qa_reports_markdown": OUTPUT_DIR / "qa_reports" / "markdown",
    "recommendations": OUTPUT_DIR / "recommendations",
    "recommendation_errors": OUTPUT_DIR / "recommendations" / "errors",
}

INPUT_DIRECTORIES = {
    "pdf": INPUT_DECKS_DIR / "pdf",
    "pptx": INPUT_DECKS_DIR / "pptx",
}

INPUT_CONTENT_DIR = PROJECT_ROOT / "input_content"
INPUT_DIRECTORIES["content"] = INPUT_CONTENT_DIR

SUPPORTED_DECK_EXTENSIONS = {".pdf", ".pptx"}
SUPPORTED_CONTENT_EXTENSIONS = {".pdf", ".pptx", ".docx", ".txt", ".md", ".csv", ".xlsx"}
DEFAULT_RENDER_DPI = 200
