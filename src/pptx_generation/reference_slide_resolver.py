from __future__ import annotations

from pathlib import Path
from typing import Any

from config import OUTPUT_DIRECTORIES, PROJECT_ROOT
from database.db import get_connection
from database.schema import initialize_database
from utils.file_utils import slugify


def resolve_reference_slide_image(matched_template: dict[str, Any]) -> dict[str, Any]:
    deck_name = str(matched_template.get("deck_name") or "").strip()
    slide_number = _safe_int(matched_template.get("slide_number"))
    if not deck_name or slide_number is None:
        return {
            "found": False,
            "slide_image_path": None,
            "warning": "Matched template is missing deck_name or slide_number.",
        }

    db_match = _find_slide_image_in_database(deck_name, slide_number)
    if db_match:
        return {"found": True, **db_match}

    file_match = _find_slide_image_by_filename(deck_name, slide_number)
    if file_match:
        return {
            "found": True,
            "deck_name": deck_name,
            "slide_number": slide_number,
            "slide_image_path": str(file_match),
            "source": "filename_fallback",
        }

    return {
        "found": False,
        "deck_name": deck_name,
        "slide_number": slide_number,
        "slide_image_path": None,
        "warning": f"Could not find rendered reference image for {deck_name} slide {slide_number}.",
    }


def _find_slide_image_in_database(deck_name: str, slide_number: int) -> dict[str, Any] | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
              d.deck_name,
              d.source_file,
              s.slide_number,
              s.slide_title,
              s.slide_image_path,
              s.slide_type,
              s.chart_type,
              s.layout_pattern,
              s.reusable_template_instruction
            FROM slides s
            JOIN decks d ON d.id = s.deck_id
            WHERE LOWER(d.deck_name) = LOWER(?) AND s.slide_number = ?
            LIMIT 1
            """,
            (deck_name, slide_number),
        ).fetchone()
    if not row:
        return None
    item = dict(row)
    image_path = _resolve_path(item.get("slide_image_path"))
    if not image_path or not image_path.exists():
        return None
    item["slide_image_path"] = str(image_path)
    item["source"] = "database"
    return item


def _find_slide_image_by_filename(deck_name: str, slide_number: int) -> Path | None:
    image_dir = OUTPUT_DIRECTORIES["slide_images"]
    if not image_dir.exists():
        return None
    suffix = f"slide_{slide_number:03d}.png"
    slug = slugify(deck_name)
    candidates = [
        image_dir / f"{slug}_pptx_{suffix}",
        image_dir / f"{slug}_pdf_{suffix}",
        image_dir / f"{slug}_{suffix}",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    matches = sorted(image_dir.glob(f"*{suffix}"))
    for match in matches:
        if slug in match.stem:
            return match.resolve()
    return None


def _resolve_path(value: object) -> Path | None:
    if not value:
        return None
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _safe_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
