from __future__ import annotations

import logging
import re
from typing import Any

from database.repository import get_classified_slide_patterns
from embeddings.embedding_repository import load_embedding_index
from embeddings.search_similar_slides import search_similar_slides_by_text


LOGGER = logging.getLogger(__name__)


def find_relevant_slide_patterns(
    content_analysis: dict,
    user_goal: str | None,
    limit: int = 5,
) -> list[dict]:
    if load_embedding_index():
        query = build_recommendation_search_query(content_analysis, user_goal)
        try:
            results = search_similar_slides_by_text(query, top_k=limit)
            if results:
                return results
        except Exception as exc:
            LOGGER.warning("Vector search failed; falling back to metadata matching: %s", exc)

    patterns = get_classified_slide_patterns()
    if not patterns:
        return []

    query_terms = _analysis_terms(content_analysis, user_goal)
    suitable_slide_types = set(content_analysis.get("suitable_slide_types", []))
    tags = set(_normalize_list(content_analysis.get("content_tags", [])))
    business_context_terms = _tokens(content_analysis.get("business_context", ""))
    audience = content_analysis.get("likely_audience")

    scored: list[tuple[float, dict[str, Any]]] = []
    for pattern in patterns:
        score = 0.0
        if pattern.get("slide_type") in suitable_slide_types:
            score += 8.0
        if audience and pattern.get("audience_type") == audience:
            score += 4.0

        pattern_tags = set(_normalize_list(pattern.get("tags", [])))
        score += len(tags & pattern_tags) * 3.0

        pattern_context_terms = _tokens(pattern.get("business_context", ""))
        score += len(business_context_terms & pattern_context_terms) * 2.0

        haystack = " ".join(
            str(pattern.get(field) or "")
            for field in [
                "slide_title",
                "slide_text",
                "slide_type",
                "chart_type",
                "storyline_type",
                "audience_type",
                "business_context",
                "layout_pattern",
            ]
        )
        score += len(query_terms & _tokens(haystack)) * 0.5

        if score > 0:
            scored.append((score, pattern))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [_public_pattern(pattern, score) for score, pattern in scored[:limit]]


def build_recommendation_search_query(content_analysis: dict, user_goal: str | None) -> str:
    pieces = [
        user_goal or "",
        content_analysis.get("content_summary", ""),
        content_analysis.get("business_context", ""),
        content_analysis.get("primary_analysis_type", ""),
        " ".join(_normalize_list(content_analysis.get("secondary_analysis_types", []))),
        " ".join(_normalize_list(content_analysis.get("key_topics", []))),
        " ".join(_normalize_list(content_analysis.get("content_tags", []))),
        " ".join(_normalize_list(content_analysis.get("suitable_slide_types", []))),
        content_analysis.get("likely_audience", ""),
    ]
    return " ".join(piece for piece in pieces if piece).strip()


def _analysis_terms(content_analysis: dict, user_goal: str | None) -> set[str]:
    pieces = [
        user_goal or "",
        content_analysis.get("content_summary", ""),
        content_analysis.get("business_context", ""),
        content_analysis.get("primary_analysis_type", ""),
        " ".join(_normalize_list(content_analysis.get("key_topics", []))),
        " ".join(_normalize_list(content_analysis.get("content_tags", []))),
        " ".join(_normalize_list(content_analysis.get("suitable_slide_types", []))),
    ]
    return _tokens(" ".join(pieces))


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", str(value).lower())
        if len(token) >= 3
    }


def _normalize_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _public_pattern(pattern: dict[str, Any], score: float) -> dict[str, Any]:
    return {
        "match_score": round(score, 2),
        "matching_method": "metadata_match",
        "deck_name": pattern.get("deck_name"),
        "slide_number": pattern.get("slide_number"),
        "slide_title": pattern.get("slide_title"),
        "slide_type": pattern.get("slide_type"),
        "chart_type": pattern.get("chart_type"),
        "storyline_type": pattern.get("storyline_type"),
        "audience_type": pattern.get("audience_type"),
        "business_context": pattern.get("business_context"),
        "layout_pattern": pattern.get("layout_pattern"),
        "tags": pattern.get("tags", []),
        "reusable_template_instruction": pattern.get("reusable_template_instruction"),
    }
