from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from content.content_sufficiency import score_content_sufficiency
from pptx_generation.content_first_deck_generator import generate_content_first_deck_from_plan
from recommendation.match_slide_patterns import build_planned_slide_search_query
from skills.skill_loader import load_skill_text
from slide_planning.slide_plan_schema import validate_slide_plan


def _sample_slide_plan() -> dict:
    return {
        "deck_title": "Self-storage Market Entry Recommendation",
        "audience": "board_of_directors",
        "output_mode": "deck",
        "strategy_summary": "Assess whether the source evidence supports a market entry decision.",
        "source_grounding_policy": "Use only source-backed claims.",
        "content_sufficiency_score": 65,
        "content_sufficiency_level": "usable",
        "recommended_slide_count": 2,
        "template_strategy": "Use OSK templates only when relevant.",
        "slides": [
            {
                "slide_number": 1,
                "slide_title": "Demand indicators support further validation before entry",
                "slide_type": "market_attractiveness",
                "chart_type": "mixed_layout",
                "storyline_type": "insight_evidence_implication",
                "slide_objective": "Summarize the source-backed market signal.",
                "key_message": "The source points to demand signals, but not enough quantified evidence for an investment decision.",
                "source_evidence": ["Source mentions demand indicators and catchment attractiveness."],
                "content_blocks": [
                    {
                        "heading": "Demand signal",
                        "body": "Use the source's observed catchment and customer need evidence.",
                        "evidence": "Source-backed.",
                    },
                    {
                        "heading": "Evidence gap",
                        "body": "Market size and competitor economics are missing.",
                        "evidence": "Missing from source.",
                    },
                ],
                "data_points": [],
                "visual_approach": "Evidence cards plus validation gap.",
                "layout_preference": "Clean executive evidence layout.",
                "template_match_query": "market attractiveness evidence cards validation gap",
                "use_template_if_relevant": False,
                "missing_data_or_assumptions": ["Market size not provided."],
                "speaker_notes": "Keep the conclusion conditional.",
                "quality_checks": ["No invented figures."],
            },
            {
                "slide_number": 2,
                "slide_title": "Entry decision requires competitor and economics validation",
                "slide_type": "risk_assessment",
                "chart_type": "table",
                "storyline_type": "risk_mitigation",
                "slide_objective": "Identify research gaps before decision.",
                "key_message": "The decision should not proceed without competitor, pricing, and economics validation.",
                "source_evidence": ["Source lacks competitor traction and economics detail."],
                "content_blocks": [
                    {
                        "heading": "Competitor evidence",
                        "body": "Benchmark nearby competitors and pricing.",
                        "evidence": "Not provided in source.",
                    },
                    {
                        "heading": "Financial evidence",
                        "body": "Validate capex, utilization, and breakeven.",
                        "evidence": "Not provided in source.",
                    },
                ],
                "data_points": [],
                "visual_approach": "Risk and mitigation table.",
                "layout_preference": "Three-column risk table.",
                "template_match_query": "risk mitigation table competitor economics validation",
                "use_template_if_relevant": False,
                "missing_data_or_assumptions": ["Competitor economics missing."],
                "speaker_notes": "Use as a decision-gate slide.",
                "quality_checks": ["Research gaps clearly marked."],
            },
        ],
        "source_grounding_report": [],
        "global_missing_data": ["Market size", "Competitor economics"],
        "generation_warnings": [],
    }


def test_slide_consultant_skill_loads() -> None:
    skill = load_skill_text()

    assert "Stay strictly grounded" in skill
    assert "Template Execution Rules" in skill


def test_content_sufficiency_scores_thin_and_usable_content() -> None:
    thin = score_content_sufficiency({"key_topics": [], "metrics_detected": []}, "short note")
    usable = score_content_sufficiency(
        {
            "key_topics": ["market", "competitors", "customers"],
            "metrics_detected": ["occupancy", "pricing"],
            "key_entities": ["OSK", "Damansara"],
            "strategic_questions_answered": ["where to play", "how to win"],
        },
        "word " * 700,
    )

    assert thin["level"] in {"insufficient", "thin"}
    assert usable["score"] > thin["score"]


def test_slide_plan_schema_normalizes_and_clamps() -> None:
    payload = _sample_slide_plan()
    payload["content_sufficiency_score"] = 120
    payload["slides"][0]["slide_type"] = "not_real"

    plan = validate_slide_plan(payload)

    assert plan["content_sufficiency_score"] == 100
    assert plan["slides"][0]["slide_type"] == "other"
    assert plan["recommended_slide_count"] == 2


def test_planned_slide_query_is_slide_specific() -> None:
    slide = _sample_slide_plan()["slides"][1]
    query = build_planned_slide_search_query(slide, {"content_tags": ["market entry"]}, "Create a board deck")

    assert "risk" in query
    assert "competitor economics validation" in query
    assert "Create a board deck" in query


def test_content_first_deck_generation_from_plan(tmp_path, monkeypatch) -> None:
    pytest.importorskip("pptx")

    monkeypatch.setattr(
        "pptx_generation.content_first_deck_generator.find_relevant_patterns_for_planned_slide",
        lambda *args, **kwargs: [],
    )
    output_path = tmp_path / "content_first_test.pptx"

    metadata = generate_content_first_deck_from_plan(
        slide_plan=_sample_slide_plan(),
        content_analysis={"content_tags": ["market entry"]},
        output_path=output_path,
    )

    assert Path(metadata["output_path"]).exists()
    assert metadata["generator_version"] == "stage9_content_first_consultant_v1"
    assert metadata["custom_layout_count"] == 2
    assert metadata["template_shell_count"] == 0
    assert Path(metadata["source_grounding_report_path"]).exists()
