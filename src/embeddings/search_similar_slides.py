from __future__ import annotations

import logging
import math
from typing import Any

from embeddings.embed_text import embed_text
from embeddings.embedding_repository import (
    get_slide_records_by_ids,
    load_embedding_index,
    rebuild_index_from_embedding_files,
)


LOGGER = logging.getLogger(__name__)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def search_similar_slides_by_text(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    index_items = load_embedding_index()
    if not index_items:
        index_items = rebuild_index_from_embedding_files()
    if not index_items:
        return []

    query_vector = embed_text(query)
    scored: list[tuple[float, dict[str, Any]]] = []

    for item in index_items:
        vector = item.get("vector")
        if not isinstance(vector, list):
            continue
        if len(vector) != len(query_vector):
            LOGGER.warning(
                "Skipping slide %s due to embedding dimension mismatch",
                item.get("slide_id"),
            )
            continue
        score = cosine_similarity(query_vector, [float(value) for value in vector])
        scored.append((score, item))

    scored.sort(key=lambda row: row[0], reverse=True)
    top_items = scored[:top_k]
    slide_ids = [int(item["slide_id"]) for _, item in top_items if item.get("slide_id")]
    slide_records = get_slide_records_by_ids(slide_ids)

    results: list[dict[str, Any]] = []
    for score, item in top_items:
        slide_id = int(item["slide_id"])
        record = slide_records.get(slide_id)
        if not record:
            continue
        results.append(
            {
                "slide_id": slide_id,
                "deck_name": record.get("deck_name"),
                "slide_number": record.get("slide_number"),
                "slide_title": record.get("slide_title"),
                "slide_type": record.get("slide_type"),
                "chart_type": record.get("chart_type"),
                "storyline_type": record.get("storyline_type"),
                "audience_type": record.get("audience_type"),
                "business_context": record.get("business_context"),
                "layout_pattern": record.get("layout_pattern"),
                "reusable_template_instruction": record.get("reusable_template_instruction"),
                "tags": record.get("tags", []),
                "similarity_score": round(score, 6),
                "matching_method": "vector_search",
            }
        )

    return results
