from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from classification.taxonomy import (
    AUDIENCE_TYPE_VALUES,
    CHART_TYPE_VALUES,
    SLIDE_TYPE_VALUES,
    STORYLINE_TYPE_VALUES,
    normalize_taxonomy_value,
)


DOCUMENT_TYPE_VALUES = [
    "slide_deck",
    "report",
    "financial_statement",
    "article",
    "brochure",
    "spreadsheet",
    "raw_notes",
    "meeting_notes",
    "research_extract",
    "unknown",
]

PRIMARY_ANALYSIS_TYPE_VALUES = [
    "executive_summary",
    "market_research",
    "industry_research",
    "competitor_analysis",
    "valuation_analysis",
    "m_and_a_analysis",
    "joint_venture_analysis",
    "corporate_exercise",
    "business_case",
    "financial_analysis",
    "operating_model",
    "implementation_planning",
    "risk_analysis",
    "strategic_options",
    "recommendation",
    "unknown",
]

OUTPUT_MODE_VALUES = ["slide", "deck", "audit", "classify", "auto"]


CONTENT_ANALYSIS_REQUIRED_FIELDS = [
    "content_summary",
    "document_type",
    "business_context",
    "primary_analysis_type",
    "secondary_analysis_types",
    "likely_audience",
    "recommended_output_mode",
    "key_topics",
    "key_entities",
    "metrics_detected",
    "time_periods_detected",
    "geographies_detected",
    "strategic_questions_answered",
    "strategic_questions_unanswered",
    "content_tags",
    "suitable_slide_types",
    "suitable_deck_sections",
    "missing_data_or_research_gaps",
    "data_quality_assessment",
    "presentation_implications",
]

RECOMMENDATION_REQUIRED_FIELDS = [
    "recommendation_type",
    "brief_interpretation",
    "content_diagnosis",
    "recommended_output_mode",
    "recommended_audience_type",
    "recommended_slide_or_deck_title",
    "recommended_storyline",
    "recommended_slide_structure",
    "recommended_deck_structure",
    "similar_slide_patterns_used",
    "alternative_structures",
    "next_steps_for_user",
]


class ContentAnalysis(BaseModel):
    content_summary: str = ""
    document_type: str = "unknown"
    business_context: str = ""
    primary_analysis_type: str = "unknown"
    secondary_analysis_types: list[str] = Field(default_factory=list)
    likely_audience: str = "unknown"
    recommended_output_mode: str = "auto"
    key_topics: list[str] = Field(default_factory=list)
    key_entities: list[Any] = Field(default_factory=list)
    metrics_detected: list[str] = Field(default_factory=list)
    time_periods_detected: list[str] = Field(default_factory=list)
    geographies_detected: list[str] = Field(default_factory=list)
    strategic_questions_answered: list[str] = Field(default_factory=list)
    strategic_questions_unanswered: list[str] = Field(default_factory=list)
    content_tags: list[str] = Field(default_factory=list)
    suitable_slide_types: list[str] = Field(default_factory=list)
    suitable_deck_sections: list[str] = Field(default_factory=list)
    missing_data_or_research_gaps: list[str] = Field(default_factory=list)
    data_quality_assessment: str = ""
    presentation_implications: str = ""

    @field_validator("document_type", mode="before")
    @classmethod
    def _document_type(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in DOCUMENT_TYPE_VALUES else "unknown"

    @field_validator("primary_analysis_type", mode="before")
    @classmethod
    def _primary_analysis_type(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in PRIMARY_ANALYSIS_TYPE_VALUES else "unknown"

    @field_validator("likely_audience", mode="before")
    @classmethod
    def _audience(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in AUDIENCE_TYPE_VALUES else "unknown"

    @field_validator("recommended_output_mode", mode="before")
    @classmethod
    def _mode(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in OUTPUT_MODE_VALUES else "auto"

    @field_validator(
        "secondary_analysis_types",
        "key_topics",
        "metrics_detected",
        "time_periods_detected",
        "geographies_detected",
        "strategic_questions_answered",
        "strategic_questions_unanswered",
        "content_tags",
        "suitable_deck_sections",
        "missing_data_or_research_gaps",
        mode="before",
    )
    @classmethod
    def _string_list(cls, value: object) -> list[str]:
        return normalize_string_list(value)

    @field_validator("suitable_slide_types", mode="before")
    @classmethod
    def _slide_types(cls, value: object) -> list[str]:
        values = normalize_string_list(value)
        normalized = []
        for item in values:
            normalized.append(item if item in SLIDE_TYPE_VALUES else "other")
        return list(dict.fromkeys(normalized))


class RecommendedSlideStructure(BaseModel):
    recommended_slide_type: str = "other"
    recommended_chart_type: str = "unknown"
    recommended_storyline_type: str = "other"
    suggested_action_title: str = ""
    layout_instruction: str = ""
    content_blocks: list[str] = Field(default_factory=list)
    data_required: list[str] = Field(default_factory=list)
    analysis_required: list[str] = Field(default_factory=list)
    missing_data_or_research_gaps: list[str] = Field(default_factory=list)
    powerpoint_template_instruction: str = ""
    quality_checklist: list[str] = Field(default_factory=list)

    @field_validator("recommended_slide_type", mode="before")
    @classmethod
    def _slide_type(cls, value: object) -> str:
        return normalize_taxonomy_value("slide_type", value)

    @field_validator("recommended_chart_type", mode="before")
    @classmethod
    def _chart_type(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in CHART_TYPE_VALUES else "unknown"

    @field_validator("recommended_storyline_type", mode="before")
    @classmethod
    def _storyline_type(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in STORYLINE_TYPE_VALUES else "other"

    @field_validator(
        "content_blocks",
        "data_required",
        "analysis_required",
        "missing_data_or_research_gaps",
        "quality_checklist",
        mode="before",
    )
    @classmethod
    def _lists(cls, value: object) -> list[str]:
        return normalize_string_list(value)


class RecommendedDeckSlide(BaseModel):
    slide_title: str = ""
    slide_type: str = "other"
    chart_type: str = "unknown"
    storyline_type: str = "other"
    content_to_use_from_source: str = ""
    additional_data_needed: str = ""
    template_instruction: str = ""

    @field_validator("slide_type", mode="before")
    @classmethod
    def _slide_type(cls, value: object) -> str:
        return normalize_taxonomy_value("slide_type", value)

    @field_validator("chart_type", mode="before")
    @classmethod
    def _chart_type(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in CHART_TYPE_VALUES else "unknown"

    @field_validator("storyline_type", mode="before")
    @classmethod
    def _storyline_type(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in STORYLINE_TYPE_VALUES else "other"


class RecommendedDeckSection(BaseModel):
    section_name: str = ""
    section_purpose: str = ""
    recommended_slides: list[RecommendedDeckSlide] = Field(default_factory=list)


class RecommendedDeckStructure(BaseModel):
    suggested_deck_title: str = ""
    sections: list[RecommendedDeckSection] = Field(default_factory=list)


class ContentRecommendation(BaseModel):
    recommendation_type: str = ""
    brief_interpretation: str = ""
    content_diagnosis: str = ""
    recommended_output_mode: str = "auto"
    recommended_audience_type: str = "unknown"
    recommended_slide_or_deck_title: str = ""
    recommended_storyline: str = ""
    recommended_slide_structure: RecommendedSlideStructure = Field(
        default_factory=RecommendedSlideStructure
    )
    recommended_deck_structure: RecommendedDeckStructure = Field(
        default_factory=RecommendedDeckStructure
    )
    similar_slide_patterns_used: list[Any] = Field(default_factory=list)
    alternative_structures: list[str] = Field(default_factory=list)
    next_steps_for_user: list[str] = Field(default_factory=list)

    @field_validator("recommended_output_mode", mode="before")
    @classmethod
    def _mode(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in OUTPUT_MODE_VALUES else "auto"

    @field_validator("recommended_audience_type", mode="before")
    @classmethod
    def _audience(cls, value: object) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized in AUDIENCE_TYPE_VALUES else "unknown"

    @field_validator("alternative_structures", "next_steps_for_user", mode="before")
    @classmethod
    def _string_lists(cls, value: object) -> list[str]:
        return normalize_string_list(value)


def validate_content_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in CONTENT_ANALYSIS_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Missing content analysis fields: {', '.join(missing)}")
    return ContentAnalysis.model_validate(payload).model_dump()


def validate_recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in RECOMMENDATION_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Missing recommendation fields: {', '.join(missing)}")
    return ContentRecommendation.model_validate(payload).model_dump()


def normalize_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
