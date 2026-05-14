from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import OUTPUT_DIRECTORIES
from classification.classify_slide import (
    InvalidClassificationResponse,
    MissingOpenAIAPIKeyError,
    classify_slide,
    validate_classification,
)
from database.repository import get_slides_for_classification, update_slide_classification
from utils.file_utils import slugify
from utils.json_utils import write_json


LOGGER = logging.getLogger(__name__)


def classify_unclassified_slides(
    limit: int | None = None,
    deck_name: str | None = None,
    force: bool = False,
) -> list[dict[str, Any]]:
    slides = get_slides_for_classification(
        limit=limit,
        deck_name=deck_name,
        force=force,
    )
    results: list[dict[str, Any]] = []

    for slide in slides:
        slide_id = int(slide["slide_id"])
        output_path = _classification_output_path(slide)

        try:
            if output_path.exists() and not force:
                classification = validate_classification(_read_json(output_path))
                status = "reused_existing_json"
            else:
                classification = classify_slide(
                    slide["slide_image_path"],
                    slide["extracted_text_path"],
                )
                write_json(output_path, _classification_payload(slide, classification))
                status = "classified"

            update_slide_classification(
                slide_id=slide_id,
                classification=classification,
            )
            LOGGER.info(
                "Classified slide %s slide %s as %s",
                slide["deck_name"],
                slide["slide_number"],
                classification["slide_type"],
            )
            results.append(
                {
                    "slide_id": slide_id,
                    "deck_name": slide["deck_name"],
                    "slide_number": slide["slide_number"],
                    "status": status,
                    "classification_path": str(output_path),
                    "slide_type": classification["slide_type"],
                    "chart_type": classification["chart_type"],
                }
            )
        except InvalidClassificationResponse as exc:
            error_path = _save_raw_error(slide, exc.raw_response)
            LOGGER.exception(
                "Invalid model response for %s slide %s",
                slide["deck_name"],
                slide["slide_number"],
            )
            results.append(
                {
                    "slide_id": slide_id,
                    "deck_name": slide["deck_name"],
                    "slide_number": slide["slide_number"],
                    "status": "failed",
                    "error": str(exc),
                    "raw_response_path": str(error_path),
                }
            )
        except MissingOpenAIAPIKeyError as exc:
            LOGGER.error(str(exc))
            results.append(
                {
                    "slide_id": slide_id,
                    "deck_name": slide["deck_name"],
                    "slide_number": slide["slide_number"],
                    "status": "failed",
                    "error": str(exc),
                }
            )
        except Exception as exc:
            LOGGER.exception(
                "Classification failed for %s slide %s",
                slide["deck_name"],
                slide["slide_number"],
            )
            results.append(
                {
                    "slide_id": slide_id,
                    "deck_name": slide["deck_name"],
                    "slide_number": slide["slide_number"],
                    "status": "failed",
                    "error": str(exc),
                }
            )

    return results


def _classification_output_path(slide: dict[str, Any]) -> Path:
    deck_slug = slugify(f"{slide['deck_name']}_{slide['source_type']}")
    return (
        OUTPUT_DIRECTORIES["classified_slides"]
        / f"{deck_slug}_slide_{int(slide['slide_number']):03d}.json"
    )


def _classification_payload(
    slide: dict[str, Any],
    classification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "deck_name": slide["deck_name"],
        "source_file": slide["source_file"],
        "source_type": slide["source_type"],
        "slide_id": slide["slide_id"],
        "slide_number": slide["slide_number"],
        "slide_image_path": slide["slide_image_path"],
        "extracted_text_path": slide["extracted_text_path"],
        "classified_at": datetime.now(timezone.utc).isoformat(),
        **classification,
    }


def _read_json(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _save_raw_error(slide: dict[str, Any], raw_response: str) -> Path:
    error_dir = OUTPUT_DIRECTORIES["classified_slides"] / "errors"
    error_dir.mkdir(parents=True, exist_ok=True)
    deck_slug = slugify(f"{slide['deck_name']}_{slide['source_type']}")
    error_path = error_dir / f"{deck_slug}_slide_{int(slide['slide_number']):03d}_raw.txt"
    error_path.write_text(raw_response, encoding="utf-8")
    return error_path
