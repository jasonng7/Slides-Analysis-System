from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DEFAULT_RENDER_DPI, OUTPUT_DIRECTORIES, SUPPORTED_DECK_EXTENSIONS
from database.repository import register_ingested_deck
from ingestion.convert_pdf_to_images import convert_pdf_to_images
from ingestion.convert_pptx_to_images import convert_pptx_to_images
from ingestion.extract_text_from_pdf import extract_text_from_pdf
from ingestion.extract_text_from_pptx import extract_text_from_pptx
from utils.file_utils import ensure_project_directories, relative_to_project, slugify
from utils.json_utils import write_json


@dataclass(frozen=True)
class IngestionSummary:
    deck_name: str
    deck_slug: str
    source_file: str
    source_type: str
    slide_count: int
    image_count: int
    text_count: int
    metadata_count: int
    render_method: str


def _slide_title(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:180]
    return ""


def _metadata_payload(
    *,
    deck_name: str,
    deck_slug: str,
    source_file: Path,
    source_type: str,
    slide_number: int,
    slide_image_path: Path | None,
    extracted_text_path: Path | None,
    extracted_text: str,
    render_method: str,
) -> dict[str, Any]:
    return {
        "deck_name": deck_name,
        "deck_slug": deck_slug,
        "slide_number": slide_number,
        "slide_title": _slide_title(extracted_text),
        "source_file": str(source_file),
        "source_type": source_type,
        "slide_image_path": str(slide_image_path) if slide_image_path else None,
        "extracted_text_path": str(extracted_text_path) if extracted_text_path else None,
        "extracted_text_char_count": len(extracted_text),
        "extracted_text_preview": extracted_text[:500],
        "render_method": render_method,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage": "ingestion",
    }


def ingest_deck(file_path: Path, dpi: int = DEFAULT_RENDER_DPI) -> IngestionSummary:
    ensure_project_directories()

    if not file_path.exists():
        raise FileNotFoundError(f"Input deck not found: {file_path}")

    source_type = file_path.suffix.lower().lstrip(".")
    if file_path.suffix.lower() not in SUPPORTED_DECK_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_DECK_EXTENSIONS))
        raise ValueError(f"Unsupported file type '{file_path.suffix}'. Supported: {supported}")

    deck_name = file_path.stem
    deck_slug = slugify(f"{deck_name}_{source_type}")
    text_dir = OUTPUT_DIRECTORIES["extracted_text"]
    image_dir = OUTPUT_DIRECTORIES["slide_images"]
    metadata_dir = OUTPUT_DIRECTORIES["parsed_objects"]
    render_method = "pymupdf_pdf_render"

    if source_type == "pdf":
        text_paths = extract_text_from_pdf(file_path, text_dir, deck_slug)
        image_paths = convert_pdf_to_images(file_path, image_dir, deck_slug, dpi=dpi)
    else:
        text_paths = extract_text_from_pptx(file_path, text_dir, deck_slug)
        image_paths, render_method = convert_pptx_to_images(
            file_path,
            image_dir,
            deck_slug,
            text_paths,
            dpi=dpi,
        )

    slide_count = max(len(text_paths), len(image_paths))
    metadata_count = 0
    slide_records: list[dict[str, Any]] = []

    for index in range(slide_count):
        slide_number = index + 1
        text_path = text_paths[index] if index < len(text_paths) else None
        image_path = image_paths[index] if index < len(image_paths) else None
        extracted_text = text_path.read_text(encoding="utf-8").strip() if text_path else ""
        metadata_path = metadata_dir / f"{deck_slug}_slide_{slide_number:03d}.json"
        payload = _metadata_payload(
            deck_name=deck_name,
            deck_slug=deck_slug,
            source_file=file_path,
            source_type=source_type,
            slide_number=slide_number,
            slide_image_path=image_path,
            extracted_text_path=text_path,
            extracted_text=extracted_text,
            render_method=render_method,
        )
        write_json(metadata_path, payload)
        slide_records.append({**payload, "slide_text": extracted_text})
        metadata_count += 1

    register_ingested_deck(
        deck_name=deck_name,
        source_file=str(file_path),
        source_type=source_type,
        slide_records=slide_records,
    )

    return IngestionSummary(
        deck_name=deck_name,
        deck_slug=deck_slug,
        source_file=relative_to_project(file_path),
        source_type=source_type,
        slide_count=slide_count,
        image_count=len(image_paths),
        text_count=len(text_paths),
        metadata_count=metadata_count,
        render_method=render_method,
    )
