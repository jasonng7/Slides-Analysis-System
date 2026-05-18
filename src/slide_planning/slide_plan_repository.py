from __future__ import annotations

from pathlib import Path
from typing import Any

from config import OUTPUT_DIRECTORIES
from utils.file_utils import slugify
from utils.json_utils import write_json


def ensure_slide_plan_dirs() -> None:
    OUTPUT_DIRECTORIES["slide_plans"].mkdir(parents=True, exist_ok=True)
    OUTPUT_DIRECTORIES["slide_plan_errors"].mkdir(parents=True, exist_ok=True)


def save_slide_plan(plan: dict[str, Any], source_name: str, timestamp: str) -> Path:
    ensure_slide_plan_dirs()
    path = OUTPUT_DIRECTORIES["slide_plans"] / f"slide_plan_{slugify(source_name)}_{timestamp}.json"
    write_json(path, plan)
    return path


def save_raw_plan_error(raw_response: str, source_name: str, timestamp: str) -> Path:
    ensure_slide_plan_dirs()
    path = OUTPUT_DIRECTORIES["slide_plan_errors"] / f"slide_plan_{slugify(source_name)}_{timestamp}_raw.txt"
    path.write_text(raw_response, encoding="utf-8")
    return path
