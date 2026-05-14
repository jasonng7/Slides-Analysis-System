from __future__ import annotations

from typing import Any


def build_slide_notes(slide_plan: dict[str, Any]) -> str:
    matched = slide_plan.get("matched_template") or {}
    suggested_content = _lines(slide_plan.get("suggested_content"))
    missing = _lines(slide_plan.get("missing_data_or_research_gaps"))
    data_required = _lines(slide_plan.get("data_required"))
    analysis_required = _lines(slide_plan.get("analysis_required"))

    parts = [
        f"Slide objective: {slide_plan.get('slide_objective') or 'Clarify the core message and evidence required for this slide.'}",
        f"Recommended storyline: {slide_plan.get('storyline') or 'Use the recommendation storyline as the governing logic.'}",
        f"Recommended slide type: {slide_plan.get('slide_type') or 'other'}",
        f"Suggested chart/table/diagram: {slide_plan.get('chart_type') or 'unknown'}",
        f"Layout pattern: {slide_plan.get('layout_pattern') or 'Use the placeholder layout shown on the slide.'}",
    ]
    if suggested_content:
        parts.append(f"Suggested content to include:\n{suggested_content}")
    if data_required:
        parts.append(f"Data required:\n{data_required}")
    if analysis_required:
        parts.append(f"Analysis required:\n{analysis_required}")
    if missing:
        parts.append(f"Missing data / assumptions:\n{missing}")

    reference = _matched_reference(matched)
    if reference:
        parts.append(f"Matched OSK template reference: {reference}")
    reusable = matched.get("reusable_template_instruction")
    if reusable:
        parts.append(f"Reusable template instruction: {reusable}")

    return "\n\n".join(parts)


def _lines(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        values = [value] if value.strip() else []
    elif isinstance(value, list):
        values = [str(item).strip() for item in value if str(item).strip()]
    else:
        values = [str(value).strip()] if str(value).strip() else []
    return "\n".join(f"- {item}" for item in values)


def _matched_reference(matched: dict[str, Any]) -> str:
    if not matched:
        return ""
    deck_name = matched.get("deck_name") or "Unknown deck"
    slide_number = matched.get("slide_number") or "?"
    title = matched.get("slide_title") or "Untitled template slide"
    score = matched.get("similarity_score") or matched.get("match_score")
    suffix = f", score {score}" if score is not None else ""
    return f"{deck_name} slide {slide_number}: {title}{suffix}"
