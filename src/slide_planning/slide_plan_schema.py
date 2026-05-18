from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from classification.taxonomy import normalize_taxonomy_value
from content.content_schema import normalize_string_list


class ContentBlock(BaseModel):
    heading: str = ""
    body: str = ""
    evidence: str = ""


class SourceGroundingItem(BaseModel):
    slide_number: int = 0
    source_basis: str = ""
    unsupported_items: list[str] = Field(default_factory=list)

    @field_validator("unsupported_items", mode="before")
    @classmethod
    def _unsupported_items(cls, value: object) -> list[str]:
        return normalize_string_list(value)


class PlannedSlide(BaseModel):
    slide_number: int = 1
    slide_title: str = ""
    slide_type: str = "other"
    chart_type: str = "unknown"
    storyline_type: str = "other"
    slide_objective: str = ""
    key_message: str = ""
    source_evidence: list[str] = Field(default_factory=list)
    content_blocks: list[ContentBlock] = Field(default_factory=list)
    data_points: list[str] = Field(default_factory=list)
    visual_approach: str = ""
    layout_preference: str = ""
    template_match_query: str = ""
    use_template_if_relevant: bool = True
    missing_data_or_assumptions: list[str] = Field(default_factory=list)
    speaker_notes: str = ""
    quality_checks: list[str] = Field(default_factory=list)

    @field_validator("slide_type", mode="before")
    @classmethod
    def _slide_type(cls, value: object) -> str:
        return normalize_taxonomy_value("slide_type", value)

    @field_validator(
        "source_evidence",
        "data_points",
        "missing_data_or_assumptions",
        "quality_checks",
        mode="before",
    )
    @classmethod
    def _string_lists(cls, value: object) -> list[str]:
        return normalize_string_list(value)


class ContentFirstSlidePlan(BaseModel):
    deck_title: str = "Content-first board-ready deck"
    audience: str = "general_business_audience"
    output_mode: str = "deck"
    strategy_summary: str = ""
    source_grounding_policy: str = "Strict source grounding; missing information is marked explicitly."
    content_sufficiency_score: int = 0
    content_sufficiency_level: str = "unknown"
    recommended_slide_count: int = 0
    template_strategy: str = "Use OSK templates only when relevant; otherwise create a clean corporate layout."
    slides: list[PlannedSlide] = Field(default_factory=list)
    source_grounding_report: list[SourceGroundingItem] = Field(default_factory=list)
    global_missing_data: list[str] = Field(default_factory=list)
    generation_warnings: list[str] = Field(default_factory=list)

    @field_validator("global_missing_data", "generation_warnings", mode="before")
    @classmethod
    def _lists(cls, value: object) -> list[str]:
        return normalize_string_list(value)

    @field_validator("content_sufficiency_score", mode="before")
    @classmethod
    def _score(cls, value: object) -> int:
        try:
            score = int(float(value))
        except (TypeError, ValueError):
            score = 0
        return max(0, min(100, score))


SLIDE_PLAN_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "deck_title",
        "audience",
        "output_mode",
        "strategy_summary",
        "source_grounding_policy",
        "content_sufficiency_score",
        "content_sufficiency_level",
        "recommended_slide_count",
        "template_strategy",
        "slides",
        "source_grounding_report",
        "global_missing_data",
        "generation_warnings",
    ],
    "properties": {
        "deck_title": {"type": "string"},
        "audience": {"type": "string"},
        "output_mode": {"type": "string"},
        "strategy_summary": {"type": "string"},
        "source_grounding_policy": {"type": "string"},
        "content_sufficiency_score": {"type": "number"},
        "content_sufficiency_level": {"type": "string"},
        "recommended_slide_count": {"type": "number"},
        "template_strategy": {"type": "string"},
        "slides": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "slide_number",
                    "slide_title",
                    "slide_type",
                    "chart_type",
                    "storyline_type",
                    "slide_objective",
                    "key_message",
                    "source_evidence",
                    "content_blocks",
                    "data_points",
                    "visual_approach",
                    "layout_preference",
                    "template_match_query",
                    "use_template_if_relevant",
                    "missing_data_or_assumptions",
                    "speaker_notes",
                    "quality_checks",
                ],
                "properties": {
                    "slide_number": {"type": "number"},
                    "slide_title": {"type": "string"},
                    "slide_type": {"type": "string"},
                    "chart_type": {"type": "string"},
                    "storyline_type": {"type": "string"},
                    "slide_objective": {"type": "string"},
                    "key_message": {"type": "string"},
                    "source_evidence": {"type": "array", "items": {"type": "string"}},
                    "content_blocks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["heading", "body", "evidence"],
                            "properties": {
                                "heading": {"type": "string"},
                                "body": {"type": "string"},
                                "evidence": {"type": "string"},
                            },
                        },
                    },
                    "data_points": {"type": "array", "items": {"type": "string"}},
                    "visual_approach": {"type": "string"},
                    "layout_preference": {"type": "string"},
                    "template_match_query": {"type": "string"},
                    "use_template_if_relevant": {"type": "boolean"},
                    "missing_data_or_assumptions": {"type": "array", "items": {"type": "string"}},
                    "speaker_notes": {"type": "string"},
                    "quality_checks": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "source_grounding_report": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["slide_number", "source_basis", "unsupported_items"],
                "properties": {
                    "slide_number": {"type": "number"},
                    "source_basis": {"type": "string"},
                    "unsupported_items": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "global_missing_data": {"type": "array", "items": {"type": "string"}},
        "generation_warnings": {"type": "array", "items": {"type": "string"}},
    },
}


def validate_slide_plan(payload: dict[str, Any]) -> dict[str, Any]:
    plan = ContentFirstSlidePlan.model_validate(payload).model_dump()
    for index, slide in enumerate(plan["slides"], start=1):
        slide["slide_number"] = slide.get("slide_number") or index
    plan["recommended_slide_count"] = plan.get("recommended_slide_count") or len(plan["slides"])
    return plan
