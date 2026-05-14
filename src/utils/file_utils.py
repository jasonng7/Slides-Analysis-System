import re
from pathlib import Path

from config import DATA_DIR, INPUT_DIRECTORIES, OUTPUT_DIRECTORIES


def ensure_project_directories() -> None:
    for path in [DATA_DIR, *INPUT_DIRECTORIES.values(), *OUTPUT_DIRECTORIES.values()]:
        path.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "deck"


def resolve_input_file(file_path: str) -> Path:
    path = Path(file_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def relative_to_project(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())
