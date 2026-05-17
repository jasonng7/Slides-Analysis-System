from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import OUTPUT_DIRECTORIES
from utils.file_utils import slugify


def ensure_qa_dirs() -> None:
    for key in ["qa_reports", "qa_reports_json", "qa_reports_markdown"]:
        OUTPUT_DIRECTORIES[key].mkdir(parents=True, exist_ok=True)


def save_qa_json(qa_result: dict[str, Any], output_path: str | Path | None = None) -> Path:
    ensure_qa_dirs()
    path = Path(output_path) if output_path else _default_report_path(qa_result, "json")
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(qa_result, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def save_qa_markdown(markdown: str, output_path: str | Path | None = None, qa_result: dict[str, Any] | None = None) -> Path:
    ensure_qa_dirs()
    path = Path(output_path) if output_path else _default_report_path(qa_result or {}, "md")
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path


def list_qa_reports(limit: int = 10) -> list[dict[str, Any]]:
    ensure_qa_dirs()
    paths = sorted(
        OUTPUT_DIRECTORIES["qa_reports_json"].glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    reports: list[dict[str, Any]] = []
    for path in paths[:limit]:
        payload: dict[str, Any] = {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"error": "Could not parse QA report JSON."}
        reports.append(
            {
                "path": str(path),
                "file_name": path.name,
                "modified_at": path.stat().st_mtime,
                "qa_type": payload.get("qa_type"),
                "reviewed_path": payload.get("reviewed_path"),
                "overall_score": payload.get("overall_score"),
                "rating": payload.get("rating"),
            }
        )
    return reports


def find_latest_generated_deck() -> Path | None:
    output_dir = OUTPUT_DIRECTORIES["generated_decks"]
    if not output_dir.exists():
        return None
    decks = [
        path
        for path in output_dir.glob("*.pptx")
        if not path.name.startswith("_") and not path.name.startswith("~$")
    ]
    if not decks:
        return None
    return max(decks, key=lambda path: path.stat().st_mtime)


def find_matching_metadata_for_deck(pptx_path: str | Path) -> Path | None:
    deck_path = Path(pptx_path)
    candidates = [
        OUTPUT_DIRECTORIES["generated_deck_metadata"] / f"{deck_path.stem}.json",
        deck_path.with_suffix(".json"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    metadata_dir = OUTPUT_DIRECTORIES["generated_deck_metadata"]
    if not metadata_dir.exists():
        return None
    matches = sorted(metadata_dir.glob(f"*{deck_path.stem}*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def find_matching_notes_for_deck(pptx_path: str | Path) -> Path | None:
    deck_path = Path(pptx_path)
    candidates = [
        OUTPUT_DIRECTORIES["generated_deck_metadata"] / f"{deck_path.stem}_speaker_notes.md",
        deck_path.with_name(f"{deck_path.stem}_speaker_notes.md"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    notes_dir = OUTPUT_DIRECTORIES["generated_deck_metadata"]
    if not notes_dir.exists():
        return None
    matches = sorted(notes_dir.glob(f"*{deck_path.stem}*notes*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def _default_report_path(qa_result: dict[str, Any], suffix: str) -> Path:
    reviewed = Path(str(qa_result.get("reviewed_path") or "qa_report")).stem
    qa_type = slugify(str(qa_result.get("qa_type") or "qa"))
    timestamp = str(qa_result.get("generated_at") or "").replace(":", "").replace("-", "").split(".")[0]
    timestamp = slugify(timestamp) or "latest"
    directory = OUTPUT_DIRECTORIES["qa_reports_json"] if suffix == "json" else OUTPUT_DIRECTORIES["qa_reports_markdown"]
    return directory / f"{qa_type}_{slugify(reviewed)}_{timestamp}.{suffix}"
