from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from config import OUTPUT_DIRECTORIES
from embeddings.embed_text import DEFAULT_EMBEDDING_MODEL, embed_text
from embeddings.embedding_repository import (
    get_classified_slide_count,
    get_classified_slides_for_embedding,
    load_embedding_index,
    save_embedding_index,
    save_embedding_metadata,
)


LOGGER = logging.getLogger(__name__)


def build_slide_text_for_embedding(slide_record: dict, tags: list[str]) -> str:
    lines = [
        f"Deck: {slide_record.get('deck_name', '')}",
        f"Slide: {slide_record.get('slide_number', '')}",
        f"Title: {slide_record.get('slide_title', '')}",
        f"Slide type: {slide_record.get('slide_type', '')}",
        f"Chart type: {slide_record.get('chart_type', '')}",
        f"Storyline: {slide_record.get('storyline_type', '')}",
        f"Audience: {slide_record.get('audience_type', '')}",
        f"Business context: {slide_record.get('business_context', '')}",
        f"Layout: {slide_record.get('layout_pattern', '')}",
        f"Tags: {', '.join(tags)}",
        f"Reusable instruction: {slide_record.get('reusable_template_instruction', '')}",
        f"Slide text: {slide_record.get('slide_text', '')}",
    ]
    return "\n".join(lines).strip()


def embed_classified_slides(force: bool = False, limit: int | None = None) -> dict[str, Any]:
    load_dotenv()
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL
    total_classified = get_classified_slide_count()
    slides = get_classified_slides_for_embedding(force=force, limit=limit)

    existing_index = load_embedding_index()
    index_by_slide_id = {
        int(item["slide_id"]): item
        for item in existing_index
        if item.get("slide_id") is not None and not force
    }

    summary = {
        "total_classified_slides": total_classified,
        "selected_slides": len(slides),
        "embedded_slides": 0,
        "skipped_slides": max(0, total_classified - len(slides)) if not force else 0,
        "failed_slides": 0,
        "failures": [],
        "embedding_model": embedding_model,
    }

    for slide in slides:
        slide_id = int(slide["slide_id"])
        tags = slide.get("tags", [])
        embedding_input = build_slide_text_for_embedding(slide, tags)
        created_at = datetime.now(timezone.utc).isoformat()
        vector_path = _vector_path(slide_id)

        try:
            vector = embed_text(embedding_input, model=embedding_model)
            payload = {
                "slide_id": slide_id,
                "embedding_type": "text",
                "embedding_model": embedding_model,
                "embedding_input": embedding_input,
                "vector": vector,
                "created_at": created_at,
            }
            vector_path.parent.mkdir(parents=True, exist_ok=True)
            vector_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            save_embedding_metadata(
                slide_id=slide_id,
                embedding_type="text",
                vector_path=str(vector_path),
                created_at=created_at,
            )
            index_by_slide_id[slide_id] = {
                "slide_id": slide_id,
                "embedding_type": "text",
                "embedding_model": embedding_model,
                "vector_path": str(vector_path),
                "vector": vector,
            }
            summary["embedded_slides"] += 1
            LOGGER.info("Embedded slide %s", slide_id)
        except Exception as exc:
            summary["failed_slides"] += 1
            summary["failures"].append(
                {
                    "slide_id": slide_id,
                    "deck_name": slide.get("deck_name"),
                    "slide_number": slide.get("slide_number"),
                    "error": str(exc),
                }
            )
            LOGGER.exception("Failed embedding slide %s", slide_id)

    save_embedding_index(
        sorted(index_by_slide_id.values(), key=lambda item: int(item["slide_id"]))
    )
    return summary


def _vector_path(slide_id: int) -> Path:
    return OUTPUT_DIRECTORIES["text_embeddings"] / f"slide_{slide_id:06d}_text_embedding.json"
