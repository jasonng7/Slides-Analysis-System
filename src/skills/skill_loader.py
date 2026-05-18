from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from config import PROJECT_ROOT


DEFAULT_SLIDE_CONSULTANT_SKILL = PROJECT_ROOT / "skills" / "slide_strategy_consultant" / "SKILL.md"


@lru_cache(maxsize=8)
def load_skill_text(skill_path: str | Path = DEFAULT_SLIDE_CONSULTANT_SKILL) -> str:
    path = Path(skill_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"Skill file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
