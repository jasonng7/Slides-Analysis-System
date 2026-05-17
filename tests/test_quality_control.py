from __future__ import annotations

import json
from pathlib import Path

import pytest

from quality_control.deck_qa_models import (
    find_duplicate_titles,
    find_near_duplicate_titles,
    rating_for_score,
)
from quality_control.generated_deck_qa import review_generated_deck
from quality_control.qa_report_builder import build_markdown_qa_report
from quality_control.qa_repository import find_latest_generated_deck, save_qa_json, save_qa_markdown
from quality_control.recommendation_qa import review_recommendation


def _sample_recommendation() -> dict:
    return {
        "recommendation_type": "deck",
        "brief_interpretation": "Board-ready deck.",
        "content_diagnosis": "Decision requires market, competitor, and option assessment.",
        "recommended_output_mode": "deck",
        "recommended_audience_type": "board_of_directors",
        "recommended_slide_or_deck_title": "OSK market entry recommendation",
        "recommended_storyline": "Assess attractiveness, options, risks, and decision ask.",
        "recommended_slide_structure": {
            "recommended_slide_type": "board_decision_paper",
            "recommended_chart_type": "mixed_layout",
            "recommended_storyline_type": "options_evaluation_recommendation",
            "suggested_action_title": "OSK should evaluate entry after validating demand and economics",
            "layout_instruction": "Decision paper.",
            "content_blocks": ["Decision", "Options", "Recommendation"],
            "data_required": ["Market size"],
            "analysis_required": ["Options score"],
            "missing_data_or_research_gaps": ["Competitor traction"],
            "powerpoint_template_instruction": "Use board summary.",
            "quality_checklist": ["Insight-led title"],
        },
        "recommended_deck_structure": {
            "suggested_deck_title": "OSK market entry recommendation",
            "sections": [
                {
                    "section_name": "Decision",
                    "section_purpose": "Frame board decision.",
                    "recommended_slides": [
                        {
                            "slide_title": "OSK should evaluate market entry after validating demand and economics",
                            "slide_type": "executive_summary",
                            "chart_type": "mixed_layout",
                            "storyline_type": "insight_evidence_implication",
                            "content_to_use_from_source": "Early market with emerging competitors.",
                            "additional_data_needed": "Market data.",
                            "template_instruction": "Use summary blocks.",
                        },
                        {
                            "slide_title": "OSK should evaluate market entry after validating demand and economics",
                            "slide_type": "executive_summary",
                            "chart_type": "mixed_layout",
                            "storyline_type": "insight_evidence_implication",
                            "content_to_use_from_source": "Early market with emerging competitors.",
                            "additional_data_needed": "Market data.",
                            "template_instruction": "Use summary blocks.",
                        },
                    ],
                }
            ],
        },
        "similar_slide_patterns_used": [],
        "alternative_structures": [],
        "next_steps_for_user": [],
        "similar_slide_patterns_found": [
            {
                "deck_name": "OSK Strategy Template Library",
                "slide_number": 53,
                "slide_title": "Opportunity challenge pattern",
                "slide_type": "opportunity_challenge_analysis",
                "chart_type": "text_only",
                "similarity_score": 0.52,
                "matching_method": "vector_search",
            }
        ],
        "matching_method": "vector_search",
    }


def test_recommendation_qa_handles_sample_recommendation(tmp_path) -> None:
    path = tmp_path / "recommendation.json"
    path.write_text(json.dumps(_sample_recommendation()), encoding="utf-8")

    result = review_recommendation(path)

    assert result["qa_type"] == "recommendation"
    assert result["summary"]["recommended_slide_count"] == 2
    assert result["overall_score"] <= 100
    assert any(issue["category"] == "slide_quality" for issue in result["issues"])


def test_generated_deck_qa_handles_missing_pptx_gracefully(tmp_path) -> None:
    result = review_generated_deck(tmp_path / "missing.pptx")

    assert result["overall_score"] == 0
    assert result["issues"][0]["severity"] == "critical"


def test_generated_deck_qa_inspects_simple_pptx(tmp_path) -> None:
    pptx = pytest.importorskip("pptx")
    prs = pptx.Presentation()
    for title in ["Cover", "Agenda", "Insight-led content slide", "Appendix: references"]:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.shapes.add_textbox(100000, 100000, 5000000, 500000).text = title
        slide.shapes.add_textbox(100000, 800000, 5000000, 500000).text = "Enough supporting content for QA inspection."
    deck_path = tmp_path / "simple.pptx"
    prs.save(deck_path)
    metadata_path = tmp_path / "simple.json"
    metadata_path.write_text(
        json.dumps(
            {
                "number_of_slides": 4,
                "number_of_content_slides": 1,
                "matching_method": "vector_search",
                "content_slides_cloned_from_source_pptx": 1,
                "content_slides_with_image_fallback": 0,
                "referenced_template_slides": [{"deck_name": "OSK", "slide_number": 1}],
            }
        ),
        encoding="utf-8",
    )
    notes_path = tmp_path / "simple_speaker_notes.md"
    notes_path.write_text("# Notes\n\nUseful notes.", encoding="utf-8")

    result = review_generated_deck(deck_path, metadata_path, notes_path)

    assert result["summary"]["total_slides"] == 4
    assert result["summary"]["cover_found"] is True
    assert result["summary"]["agenda_found"] is True
    assert result["summary"]["appendix_found"] is True


def test_duplicate_and_near_duplicate_title_detection() -> None:
    duplicates = find_duplicate_titles(["Market entry option", "Market entry option"])
    near_duplicates = find_near_duplicate_titles(
        ["OSK should enter after demand validation", "OSK should enter after demand validation and economics"]
    )

    assert duplicates
    assert near_duplicates


def test_scoring_rating_bands() -> None:
    assert rating_for_score(90) == "Strong"
    assert rating_for_score(75) == "Usable with minor review"
    assert rating_for_score(60) == "Needs consultant refinement"
    assert rating_for_score(40) == "Needs regeneration or major manual fixing"


def test_markdown_report_builder_includes_issues_and_recommendations() -> None:
    result = {
        "qa_type": "generated_deck",
        "reviewed_path": "deck.pptx",
        "generated_at": "2026-05-15T00:00:00+00:00",
        "overall_score": 78,
        "rating": "Usable with minor review",
        "summary": {"total_slides": 10},
        "issues": [{"severity": "medium", "category": "structure", "message": "Too long", "recommendation": "Condense"}],
        "recommendations": ["Condense the deck."],
        "slide_level_findings": [{"slide_number": 1, "title": "Title", "word_count": 1}],
    }

    markdown = build_markdown_qa_report(result)

    assert "QA Report" in markdown
    assert "Too long" in markdown
    assert "Condense the deck" in markdown


def test_repository_saves_qa_json_and_markdown(tmp_path, monkeypatch) -> None:
    import quality_control.qa_repository as repo

    monkeypatch.setitem(repo.OUTPUT_DIRECTORIES, "qa_reports_json", tmp_path / "json")
    monkeypatch.setitem(repo.OUTPUT_DIRECTORIES, "qa_reports_markdown", tmp_path / "markdown")
    monkeypatch.setitem(repo.OUTPUT_DIRECTORIES, "qa_reports", tmp_path)
    result = {
        "qa_type": "generated_deck",
        "reviewed_path": "deck.pptx",
        "generated_at": "2026-05-15T00:00:00+00:00",
        "overall_score": 80,
    }

    json_path = save_qa_json(result)
    markdown_path = save_qa_markdown("# QA\n", qa_result=result)

    assert json_path.exists()
    assert markdown_path.exists()


def test_latest_generated_deck_finder_handles_empty_folder(tmp_path, monkeypatch) -> None:
    import quality_control.qa_repository as repo

    monkeypatch.setitem(repo.OUTPUT_DIRECTORIES, "generated_decks", tmp_path)

    assert find_latest_generated_deck() is None
