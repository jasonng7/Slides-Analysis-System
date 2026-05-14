from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import OUTPUT_DIRECTORIES
from database.db import get_connection
from database.schema import initialize_database


TEXT_INDEX_PATH = OUTPUT_DIRECTORIES["embeddings"] / "text_index.json"


@dataclass(frozen=True)
class EmbeddingSummary:
    total_classified_slides: int
    slides_with_text_embeddings: int
    slides_without_text_embeddings: int
    embedding_model: str | None
    index_file_path: str
    latest_embedded_slides: list[dict[str, Any]]


def get_classified_slides_for_embedding(
    *,
    force: bool = False,
    limit: int | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    initialize_database(db_path)
    where_clauses = ["s.slide_type IS NOT NULL", "TRIM(s.slide_type) != ''"]
    params: list[Any] = []

    if not force:
        where_clauses.append(
            """
            NOT EXISTS (
              SELECT 1
              FROM embeddings e
              WHERE e.slide_id = s.id AND e.embedding_type = 'text'
            )
            """
        )

    limit_sql = "LIMIT ?" if limit is not None else ""
    if limit is not None:
        params.append(limit)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            f"""
            SELECT
              s.id AS slide_id,
              d.deck_name,
              d.source_file,
              d.source_type,
              s.slide_number,
              s.slide_title,
              s.slide_text,
              s.slide_image_path,
              s.slide_type,
              s.chart_type,
              s.storyline_type,
              s.audience_type,
              s.business_context,
              s.layout_pattern,
              s.reusable_template_instruction,
              s.quality_score,
              GROUP_CONCAT(t.tag, ',') AS tags
            FROM slides s
            JOIN decks d ON d.id = s.deck_id
            LEFT JOIN slide_tags t ON t.slide_id = s.id
            WHERE {" AND ".join(where_clauses)}
            GROUP BY s.id
            ORDER BY d.deck_name ASC, s.slide_number ASC
            {limit_sql}
            """,
            params,
        ).fetchall()

    return [_row_with_tags(row) for row in rows]


def get_classified_slide_count(db_path: Path | None = None) -> int:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        return int(
            connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM slides
                WHERE slide_type IS NOT NULL AND TRIM(slide_type) != ''
                """
            ).fetchone()["count"]
        )


def get_existing_embedding(
    slide_id: int,
    embedding_type: str = "text",
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, slide_id, embedding_type, vector_path, created_at
            FROM embeddings
            WHERE slide_id = ? AND embedding_type = ?
            """,
            (slide_id, embedding_type),
        ).fetchone()
    return dict(row) if row else None


def save_embedding_metadata(
    *,
    slide_id: int,
    embedding_type: str,
    vector_path: str,
    created_at: str,
    db_path: Path | None = None,
) -> None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO embeddings (slide_id, embedding_type, vector_path, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(slide_id, embedding_type)
            DO UPDATE SET vector_path = excluded.vector_path,
                          created_at = excluded.created_at
            """,
            (slide_id, embedding_type, vector_path, created_at),
        )


def get_slide_records_by_ids(
    slide_ids: list[int],
    db_path: Path | None = None,
) -> dict[int, dict[str, Any]]:
    if not slide_ids:
        return {}
    initialize_database(db_path)
    placeholders = ",".join("?" for _ in slide_ids)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            f"""
            SELECT
              s.id AS slide_id,
              d.deck_name,
              d.source_file,
              d.source_type,
              s.slide_number,
              s.slide_title,
              s.slide_text,
              s.slide_image_path,
              s.slide_type,
              s.chart_type,
              s.storyline_type,
              s.audience_type,
              s.business_context,
              s.layout_pattern,
              s.reusable_template_instruction,
              s.quality_score,
              GROUP_CONCAT(t.tag, ',') AS tags
            FROM slides s
            JOIN decks d ON d.id = s.deck_id
            LEFT JOIN slide_tags t ON t.slide_id = s.id
            WHERE s.id IN ({placeholders})
            GROUP BY s.id
            """,
            slide_ids,
        ).fetchall()
    return {int(row["slide_id"]): _row_with_tags(row) for row in rows}


def load_embedding_index(index_path: Path | None = None) -> list[dict[str, Any]]:
    path = index_path or TEXT_INDEX_PATH
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return list(payload.get("items", []))
    if isinstance(payload, list):
        return payload
    return []


def save_embedding_index(items: list[dict[str, Any]], index_path: Path | None = None) -> None:
    path = index_path or TEXT_INDEX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "index_type": "slide_text_embeddings",
        "item_count": len(items),
        "items": items,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def rebuild_index_from_embedding_files(index_path: Path | None = None) -> list[dict[str, Any]]:
    embedding_dir = OUTPUT_DIRECTORIES["text_embeddings"]
    items: list[dict[str, Any]] = []
    if embedding_dir.exists():
        for path in sorted(embedding_dir.glob("slide_*_text_embedding.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            vector = payload.get("vector")
            if not isinstance(vector, list):
                continue
            items.append(
                {
                    "slide_id": payload.get("slide_id"),
                    "embedding_type": payload.get("embedding_type", "text"),
                    "embedding_model": payload.get("embedding_model"),
                    "vector_path": str(path),
                    "vector": vector,
                }
            )
    save_embedding_index(items, index_path=index_path)
    return items


def get_embedding_summary(db_path: Path | None = None) -> EmbeddingSummary:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        total_classified = int(
            connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM slides
                WHERE slide_type IS NOT NULL AND TRIM(slide_type) != ''
                """
            ).fetchone()["count"]
        )
        with_embeddings = int(
            connection.execute(
                """
                SELECT COUNT(DISTINCT slide_id) AS count
                FROM embeddings
                WHERE embedding_type = 'text'
                """
            ).fetchone()["count"]
        )
        model_row = connection.execute(
            """
            SELECT vector_path
            FROM embeddings
            WHERE embedding_type = 'text'
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        latest_rows = connection.execute(
            """
            SELECT e.slide_id, d.deck_name, s.slide_number, s.slide_title,
                   s.slide_type, e.vector_path, e.created_at
            FROM embeddings e
            JOIN slides s ON s.id = e.slide_id
            JOIN decks d ON d.id = s.deck_id
            WHERE e.embedding_type = 'text'
            ORDER BY e.created_at DESC, e.id DESC
            LIMIT 5
            """
        ).fetchall()

    embedding_model = None
    if model_row:
        try:
            payload = json.loads(Path(model_row["vector_path"]).read_text(encoding="utf-8"))
            embedding_model = payload.get("embedding_model")
        except (OSError, json.JSONDecodeError):
            embedding_model = None

    return EmbeddingSummary(
        total_classified_slides=total_classified,
        slides_with_text_embeddings=with_embeddings,
        slides_without_text_embeddings=max(0, total_classified - with_embeddings),
        embedding_model=embedding_model,
        index_file_path=str(TEXT_INDEX_PATH),
        latest_embedded_slides=[dict(row) for row in latest_rows],
    )


def _row_with_tags(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["tags"] = [
        tag.strip() for tag in (item.get("tags") or "").split(",") if tag.strip()
    ]
    return item
