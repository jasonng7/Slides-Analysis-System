from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from database.db import get_connection
from database.schema import initialize_database


@dataclass(frozen=True)
class DatabaseSummary:
    deck_count: int
    slide_count: int
    slides_by_source_type: list[tuple[str, int]]
    latest_decks: list[dict[str, Any]]


@dataclass(frozen=True)
class ClassificationSummary:
    total_slides: int
    classified_slides: int
    unclassified_slides: int
    slides_by_slide_type: list[tuple[str, int]]
    slides_by_chart_type: list[tuple[str, int]]
    average_quality_score: float | None


@dataclass(frozen=True)
class ContentSummary:
    total_content_sources: int
    sources_by_type: list[tuple[str, int]]
    sources_by_primary_analysis_type: list[tuple[str, int]]
    latest_sources: list[dict[str, Any]]
    latest_recommendations: list[dict[str, Any]]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_ingested_deck(
    *,
    deck_name: str,
    source_file: str,
    source_type: str,
    slide_records: list[dict[str, Any]],
    business_domain: str | None = None,
    db_path: Path | None = None,
) -> int:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        existing = connection.execute(
            "SELECT id FROM decks WHERE source_file = ?",
            (source_file,),
        ).fetchone()

        if existing:
            deck_id = int(existing["id"])
            connection.execute(
                """
                UPDATE decks
                SET deck_name = ?,
                    source_type = ?,
                    business_domain = COALESCE(?, business_domain),
                    created_at = ?
                WHERE id = ?
                """,
                (deck_name, source_type, business_domain, _now(), deck_id),
            )
        else:
            cursor = connection.execute(
                """
                INSERT INTO decks (
                  deck_name,
                  source_file,
                  source_type,
                  business_domain,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (deck_name, source_file, source_type, business_domain, _now()),
            )
            deck_id = int(cursor.lastrowid)

        # Idempotency policy: keep one deck row per source file, then replace
        # that deck's slide rows on each ingest. This is simpler and safer than
        # trying to diff slide-level render/text changes from regenerated files.
        connection.execute("DELETE FROM slides WHERE deck_id = ?", (deck_id,))

        for record in slide_records:
            connection.execute(
                """
                INSERT INTO slides (
                  deck_id,
                  slide_number,
                  slide_title,
                  slide_text,
                  slide_image_path,
                  extracted_text_path,
                  slide_type,
                  chart_type,
                  storyline_type,
                  audience_type,
                  business_context,
                  layout_pattern,
                  reusable_template_instruction,
                  quality_score,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    deck_id,
                    record.get("slide_number"),
                    record.get("slide_title"),
                    record.get("slide_text", ""),
                    record.get("slide_image_path"),
                    record.get("extracted_text_path"),
                    record.get("slide_type"),
                    record.get("chart_type"),
                    record.get("storyline_type"),
                    record.get("audience_type"),
                    record.get("business_context"),
                    record.get("layout_pattern"),
                    record.get("reusable_template_instruction"),
                    record.get("quality_score"),
                    record.get("created_at") or _now(),
                ),
            )

        return deck_id


def get_database_summary(db_path: Path | None = None) -> DatabaseSummary:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        deck_count = int(connection.execute("SELECT COUNT(*) AS count FROM decks").fetchone()["count"])
        slide_count = int(connection.execute("SELECT COUNT(*) AS count FROM slides").fetchone()["count"])

        by_source_rows = connection.execute(
            """
            SELECT d.source_type, COUNT(s.id) AS slide_count
            FROM decks d
            LEFT JOIN slides s ON s.deck_id = d.id
            GROUP BY d.source_type
            ORDER BY d.source_type
            """
        ).fetchall()
        slides_by_source_type = [
            (row["source_type"] or "unknown", int(row["slide_count"]))
            for row in by_source_rows
        ]

        latest_rows = connection.execute(
            """
            SELECT
              d.id,
              d.deck_name,
              d.source_file,
              d.source_type,
              d.created_at,
              COUNT(s.id) AS slide_count
            FROM decks d
            LEFT JOIN slides s ON s.deck_id = d.id
            GROUP BY d.id
            ORDER BY d.created_at DESC, d.id DESC
            LIMIT 5
            """
        ).fetchall()
        latest_decks = [dict(row) for row in latest_rows]

    return DatabaseSummary(
        deck_count=deck_count,
        slide_count=slide_count,
        slides_by_source_type=slides_by_source_type,
        latest_decks=latest_decks,
    )


def get_slides_for_classification(
    *,
    limit: int | None = None,
    deck_name: str | None = None,
    force: bool = False,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    initialize_database(db_path)

    where_clauses: list[str] = []
    params: list[Any] = []

    if deck_name:
        where_clauses.append("d.deck_name = ?")
        params.append(deck_name)

    if not force:
        where_clauses.append("(s.slide_type IS NULL OR TRIM(s.slide_type) = '')")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    limit_sql = "LIMIT ?" if limit is not None else ""
    if limit is not None:
        params.append(limit)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            f"""
            SELECT
              s.id AS slide_id,
              s.deck_id,
              s.slide_number,
              s.slide_title,
              s.slide_text,
              s.slide_image_path,
              s.extracted_text_path,
              d.deck_name,
              d.source_file,
              d.source_type
            FROM slides s
            JOIN decks d ON d.id = s.deck_id
            {where_sql}
            ORDER BY d.created_at DESC, d.id DESC, s.slide_number ASC
            {limit_sql}
            """,
            params,
        ).fetchall()

    return [dict(row) for row in rows]


def update_slide_classification(
    *,
    slide_id: int,
    classification: dict[str, Any],
    db_path: Path | None = None,
) -> None:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE slides
            SET slide_title = ?,
                slide_type = ?,
                chart_type = ?,
                storyline_type = ?,
                audience_type = ?,
                business_context = ?,
                layout_pattern = ?,
                reusable_template_instruction = ?,
                quality_score = ?
            WHERE id = ?
            """,
            (
                classification.get("slide_title"),
                classification.get("slide_type"),
                classification.get("chart_type"),
                classification.get("storyline_type"),
                classification.get("audience_type"),
                classification.get("business_context"),
                classification.get("layout_pattern"),
                classification.get("reusable_template_instruction"),
                classification.get("quality_score"),
                slide_id,
            ),
        )
        connection.execute("DELETE FROM slide_tags WHERE slide_id = ?", (slide_id,))
        for tag in classification.get("tags", []):
            connection.execute(
                "INSERT INTO slide_tags (slide_id, tag) VALUES (?, ?)",
                (slide_id, tag),
            )


def get_classification_summary(db_path: Path | None = None) -> ClassificationSummary:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        total_slides = int(connection.execute("SELECT COUNT(*) AS count FROM slides").fetchone()["count"])
        classified_slides = int(
            connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM slides
                WHERE slide_type IS NOT NULL AND TRIM(slide_type) != ''
                """
            ).fetchone()["count"]
        )
        unclassified_slides = total_slides - classified_slides

        slide_type_rows = connection.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(slide_type), ''), 'unclassified') AS slide_type,
                   COUNT(*) AS count
            FROM slides
            GROUP BY COALESCE(NULLIF(TRIM(slide_type), ''), 'unclassified')
            ORDER BY count DESC, slide_type ASC
            """
        ).fetchall()
        chart_type_rows = connection.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(chart_type), ''), 'unclassified') AS chart_type,
                   COUNT(*) AS count
            FROM slides
            GROUP BY COALESCE(NULLIF(TRIM(chart_type), ''), 'unclassified')
            ORDER BY count DESC, chart_type ASC
            """
        ).fetchall()
        average_quality = connection.execute(
            """
            SELECT AVG(quality_score) AS average_quality_score
            FROM slides
            WHERE quality_score IS NOT NULL
            """
        ).fetchone()["average_quality_score"]

    return ClassificationSummary(
        total_slides=total_slides,
        classified_slides=classified_slides,
        unclassified_slides=unclassified_slides,
        slides_by_slide_type=[
            (row["slide_type"], int(row["count"])) for row in slide_type_rows
        ],
        slides_by_chart_type=[
            (row["chart_type"], int(row["count"])) for row in chart_type_rows
        ],
        average_quality_score=float(average_quality) if average_quality is not None else None,
    )


def register_content_analysis(
    *,
    source_info: dict[str, Any],
    analysis: dict[str, Any],
    analysis_json_path: str,
    user_goal: str | None = None,
    db_path: Path | None = None,
) -> int:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO content_sources (
              source_name,
              source_file,
              source_type,
              user_goal,
              raw_text_path,
              analysis_json_path,
              content_summary,
              document_type,
              business_context,
              primary_analysis_type,
              recommended_output_mode,
              created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_info.get("source_name"),
                source_info.get("source_file"),
                source_info.get("source_type"),
                user_goal,
                source_info.get("raw_text_path"),
                analysis_json_path,
                analysis.get("content_summary"),
                analysis.get("document_type"),
                analysis.get("business_context"),
                analysis.get("primary_analysis_type"),
                analysis.get("recommended_output_mode"),
                _now(),
            ),
        )
        content_source_id = int(cursor.lastrowid)

        for tag in analysis.get("content_tags", []):
            connection.execute(
                "INSERT INTO content_tags (content_source_id, tag) VALUES (?, ?)",
                (content_source_id, str(tag)),
            )

        for entity in _normalize_content_entities(analysis.get("key_entities", [])):
            connection.execute(
                """
                INSERT INTO content_entities (content_source_id, entity, entity_type)
                VALUES (?, ?, ?)
                """,
                (content_source_id, entity["entity"], entity["entity_type"]),
            )

        return content_source_id


def save_content_recommendation_record(
    *,
    content_source_id: int,
    recommendation_json_path: str,
    recommendation_txt_path: str | None,
    output_mode: str,
    recommended_slide_type: str | None,
    recommended_deck_sections: str | None,
    db_path: Path | None = None,
) -> int:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO content_recommendations (
              content_source_id,
              recommendation_json_path,
              recommendation_txt_path,
              output_mode,
              recommended_slide_type,
              recommended_deck_sections,
              created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_source_id,
                recommendation_json_path,
                recommendation_txt_path,
                output_mode,
                recommended_slide_type,
                recommended_deck_sections,
                _now(),
            ),
        )
        return int(cursor.lastrowid)


def get_content_summary(db_path: Path | None = None) -> ContentSummary:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        total_sources = int(
            connection.execute(
                "SELECT COUNT(*) AS count FROM content_sources"
            ).fetchone()["count"]
        )
        by_type_rows = connection.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(source_type), ''), 'unknown') AS source_type,
                   COUNT(*) AS count
            FROM content_sources
            GROUP BY COALESCE(NULLIF(TRIM(source_type), ''), 'unknown')
            ORDER BY count DESC, source_type ASC
            """
        ).fetchall()
        by_analysis_rows = connection.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(primary_analysis_type), ''), 'unknown') AS primary_analysis_type,
                   COUNT(*) AS count
            FROM content_sources
            GROUP BY COALESCE(NULLIF(TRIM(primary_analysis_type), ''), 'unknown')
            ORDER BY count DESC, primary_analysis_type ASC
            """
        ).fetchall()
        latest_sources = connection.execute(
            """
            SELECT id, source_name, source_type, primary_analysis_type,
                   recommended_output_mode, created_at
            FROM content_sources
            ORDER BY created_at DESC, id DESC
            LIMIT 5
            """
        ).fetchall()
        latest_recommendations = connection.execute(
            """
            SELECT r.id, c.source_name, r.output_mode, r.recommended_slide_type,
                   r.recommended_deck_sections, r.created_at
            FROM content_recommendations r
            JOIN content_sources c ON c.id = r.content_source_id
            ORDER BY r.created_at DESC, r.id DESC
            LIMIT 5
            """
        ).fetchall()

    return ContentSummary(
        total_content_sources=total_sources,
        sources_by_type=[
            (row["source_type"], int(row["count"])) for row in by_type_rows
        ],
        sources_by_primary_analysis_type=[
            (row["primary_analysis_type"], int(row["count"])) for row in by_analysis_rows
        ],
        latest_sources=[dict(row) for row in latest_sources],
        latest_recommendations=[dict(row) for row in latest_recommendations],
    )


def get_classified_slide_patterns(db_path: Path | None = None) -> list[dict[str, Any]]:
    initialize_database(db_path)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
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
            WHERE s.slide_type IS NOT NULL AND TRIM(s.slide_type) != ''
            GROUP BY s.id
            ORDER BY s.quality_score DESC, s.id DESC
            """
        ).fetchall()

    patterns = []
    for row in rows:
        item = dict(row)
        item["tags"] = [
            tag.strip() for tag in (item.get("tags") or "").split(",") if tag.strip()
        ]
        patterns.append(item)
    return patterns


def _normalize_content_entities(raw_entities: Any) -> list[dict[str, str]]:
    if not isinstance(raw_entities, list):
        return []

    entities: list[dict[str, str]] = []
    for item in raw_entities:
        if isinstance(item, dict):
            entity = str(item.get("entity") or item.get("name") or "").strip()
            entity_type = str(item.get("entity_type") or item.get("type") or "unknown").strip()
        else:
            entity = str(item).strip()
            entity_type = "unknown"
        if entity:
            entities.append({"entity": entity, "entity_type": entity_type or "unknown"})
    return entities
