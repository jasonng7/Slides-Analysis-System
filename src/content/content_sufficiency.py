from __future__ import annotations

from typing import Any


def score_content_sufficiency(content_analysis: dict[str, Any], raw_text: str | None = None) -> dict[str, Any]:
    """Score whether the source can support a board-ready deck without invention.

    This is deliberately heuristic. The LLM still plans the storyline, but this
    guardrail tells it when to make a shorter deck or expose research gaps.
    """
    text = raw_text or ""
    word_count = len(text.split())
    metrics = _as_list(content_analysis.get("metrics_detected"))
    entities = _as_list(content_analysis.get("key_entities"))
    topics = _as_list(content_analysis.get("key_topics"))
    gaps = _as_list(content_analysis.get("missing_data_or_research_gaps"))
    answered = _as_list(content_analysis.get("strategic_questions_answered"))

    score = 20
    if word_count >= 150:
        score += 10
    if word_count >= 600:
        score += 10
    if word_count >= 1500:
        score += 10
    if len(topics) >= 3:
        score += 10
    if len(entities) >= 2:
        score += 10
    if len(metrics) >= 2:
        score += 10
    if len(answered) >= 2:
        score += 10
    if len(gaps) > 4:
        score -= 10
    if len(gaps) > 8:
        score -= 10

    score = max(0, min(100, score))
    if score >= 75:
        level = "strong"
        recommendation = "Source can support a board-ready deck; still mark any gaps explicitly."
    elif score >= 50:
        level = "usable"
        recommendation = "Source can support a concise deck or strong mini-deck; avoid unsupported sections."
    elif score >= 30:
        level = "thin"
        recommendation = "Source is thin; prefer a short deck with research-gap slides."
    else:
        level = "insufficient"
        recommendation = "Source is insufficient for a full deck; generate a diagnostic outline and missing-data checklist."

    return {
        "score": score,
        "level": level,
        "word_count": word_count,
        "metrics_count": len(metrics),
        "entity_count": len(entities),
        "topic_count": len(topics),
        "gap_count": len(gaps),
        "recommendation": recommendation,
    }


def _as_list(value: object) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        return [value]
    return []
