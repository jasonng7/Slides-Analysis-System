from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import OUTPUT_DIRECTORIES
from utils.file_utils import slugify


def ensure_generated_deck_dirs() -> None:
    for key in ["generated_decks", "generated_deck_logs", "generated_deck_metadata"]:
        OUTPUT_DIRECTORIES[key].mkdir(parents=True, exist_ok=True)


def save_generation_metadata(metadata: dict[str, Any], output_path: str | Path) -> Path:
    ensure_generated_deck_dirs()
    deck_path = Path(output_path)
    metadata_path = OUTPUT_DIRECTORIES["generated_deck_metadata"] / f"{deck_path.stem}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return metadata_path


def save_speaker_notes_markdown(
    slide_notes: list[dict[str, str]],
    output_path: str | Path,
) -> Path:
    ensure_generated_deck_dirs()
    deck_path = Path(output_path)
    notes_path = OUTPUT_DIRECTORIES["generated_deck_metadata"] / f"{deck_path.stem}_speaker_notes.md"
    lines = [f"# Speaker Notes: {deck_path.stem}", ""]
    for item in slide_notes:
        lines.append(f"## Slide {item['slide_number']}: {item['slide_title']}")
        lines.append("")
        lines.append(item["notes"].strip())
        lines.append("")
    notes_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return notes_path


def list_generated_decks(limit: int = 10) -> list[dict[str, Any]]:
    ensure_generated_deck_dirs()
    decks = sorted(
        OUTPUT_DIRECTORIES["generated_decks"].glob("*.pptx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    results: list[dict[str, Any]] = []
    for deck_path in decks[:limit]:
        metadata_path = OUTPUT_DIRECTORIES["generated_deck_metadata"] / f"{deck_path.stem}.json"
        metadata: dict[str, Any] = {}
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                metadata = {"warnings": ["Metadata JSON could not be parsed."]}
        results.append(
            {
                "output_path": str(deck_path),
                "file_name": deck_path.name,
                "modified_at": deck_path.stat().st_mtime,
                "metadata_path": str(metadata_path) if metadata_path.exists() else None,
                "metadata": metadata,
            }
        )
    return results


def get_latest_recommendation_path() -> Path | None:
    recommendation_dir = OUTPUT_DIRECTORIES["recommendations"]
    if not recommendation_dir.exists():
        return None
    paths = sorted(
        recommendation_dir.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return paths[0] if paths else None


def default_output_path(goal_or_title: str | None, timestamp: str) -> Path:
    ensure_generated_deck_dirs()
    slug = slugify(goal_or_title or "generated_placeholder_deck")
    return OUTPUT_DIRECTORIES["generated_decks"] / f"{slug}_{timestamp}.pptx"


def python_pptx_available() -> bool:
    try:
        import pptx  # noqa: F401
    except ImportError:
        return False
    return True
