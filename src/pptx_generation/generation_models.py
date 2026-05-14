from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GeneratedSlidePlan:
    slide_number: int
    slide_title: str
    slide_type: str = "other"
    storyline: str = ""
    slide_objective: str = ""
    layout_pattern: str = ""
    chart_type: str = "unknown"
    business_context: str = ""
    suggested_content: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    matched_template: dict[str, Any] = field(default_factory=dict)
    matching_method: str = "metadata_match"

    def as_dict(self) -> dict[str, Any]:
        return {
            "slide_number": self.slide_number,
            "slide_title": self.slide_title,
            "slide_type": self.slide_type,
            "storyline": self.storyline,
            "slide_objective": self.slide_objective,
            "layout_pattern": self.layout_pattern,
            "chart_type": self.chart_type,
            "business_context": self.business_context,
            "suggested_content": self.suggested_content,
            "tags": self.tags,
            "matched_template": self.matched_template,
            "matching_method": self.matching_method,
        }


@dataclass
class GeneratedDeckInput:
    title: str
    user_goal: str = ""
    mode: str = "deck"
    source_recommendation_path: str | None = None
    matching_method: str = "metadata_match"
    slide_patterns: list[dict[str, Any]] = field(default_factory=list)
    recommendation: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "user_goal": self.user_goal,
            "mode": self.mode,
            "source_recommendation_path": self.source_recommendation_path,
            "matching_method": self.matching_method,
            "slide_patterns": self.slide_patterns,
            "recommendation": self.recommendation,
        }


@dataclass
class GeneratedDeckMetadata:
    generated_at: str
    output_path: str
    source_recommendation_path: str | None
    user_goal: str
    mode: str
    number_of_slides: int
    number_of_content_slides: int
    matching_method: str
    referenced_template_slides: list[dict[str, Any]]
    warnings: list[str]
    generator_version: str = "stage7_placeholder_v1"

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "output_path": self.output_path,
            "source_recommendation_path": self.source_recommendation_path,
            "user_goal": self.user_goal,
            "mode": self.mode,
            "number_of_slides": self.number_of_slides,
            "number_of_content_slides": self.number_of_content_slides,
            "matching_method": self.matching_method,
            "referenced_template_slides": self.referenced_template_slides,
            "warnings": self.warnings,
            "generator_version": self.generator_version,
        }
