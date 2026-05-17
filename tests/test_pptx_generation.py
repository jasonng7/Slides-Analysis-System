from __future__ import annotations

import json
from pathlib import Path

import pytest

from pptx_generation.notes_builder import build_slide_notes
from pptx_generation.editable_reference_deck_generator import (
    generate_editable_reference_deck_from_recommendation,
)
from pptx_generation.placeholder_deck_generator import (
    generate_placeholder_deck_from_recommendation,
    normalize_recommendation_to_slide_plans,
)
from pptx_generation.pptx_repository import default_output_path, save_generation_metadata
from pptx_generation.reference_deck_generator import generate_reference_deck_from_recommendation
from pptx_generation.slide_layout_builder import select_layout_family


def _sample_recommendation() -> dict:
    return {
        "recommendation_type": "deck",
        "brief_interpretation": "Build a board-ready market entry deck.",
        "content_diagnosis": "Source content discusses market entry options and missing evidence.",
        "recommended_output_mode": "deck",
        "recommended_audience_type": "board_of_directors",
        "recommended_slide_or_deck_title": "OSK EWA Market Entry",
        "recommended_storyline": "Assess market attractiveness, options, risks, and recommendation.",
        "recommended_slide_structure": {
            "recommended_slide_type": "board_decision_paper",
            "recommended_chart_type": "mixed_layout",
            "recommended_storyline_type": "options_evaluation_recommendation",
            "suggested_action_title": "OSK should test EWA entry through build-buy-partner options",
            "layout_instruction": "Use a decision paper layout.",
            "content_blocks": ["Decision required", "Options", "Recommendation"],
            "data_required": ["Market size"],
            "analysis_required": ["Options scoring"],
            "missing_data_or_research_gaps": ["Competitor traction"],
            "powerpoint_template_instruction": "Use a board decision structure.",
            "quality_checklist": ["Insight-led title"],
        },
        "recommended_deck_structure": {
            "suggested_deck_title": "OSK Market Entry Recommendation: EWA",
            "sections": [
                {
                    "section_name": "Executive decision",
                    "section_purpose": "Frame the board decision.",
                    "recommended_slides": [
                        {
                            "slide_title": "OSK should assess EWA entry through a build-buy-partner lens",
                            "slide_type": "executive_summary",
                            "chart_type": "mixed_layout",
                            "storyline_type": "situation_complication_resolution",
                            "content_to_use_from_source": "Market is early; options are build, buy, or partner.",
                            "additional_data_needed": "Market size and competitor traction.",
                            "template_instruction": "Use three message boxes and a decision ask.",
                        },
                        {
                            "slide_title": "Entry options should be evaluated across speed, control, economics, and risk",
                            "slide_type": "options_analysis",
                            "chart_type": "matrix",
                            "storyline_type": "options_evaluation_recommendation",
                            "content_to_use_from_source": "Core decision is build, buy, or partner.",
                            "additional_data_needed": "Cost and timing by option.",
                            "template_instruction": "Use three option columns.",
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
                "slide_number": 12,
                "slide_title": "Executive summary pattern",
                "slide_type": "executive_summary",
                "chart_type": "mixed_layout",
                "layout_pattern": "Key messages with decision bar",
                "reusable_template_instruction": "Use as a board summary structure.",
                "similarity_score": 0.88,
                "matching_method": "vector_search",
            },
            {
                "deck_name": "Corporate Template Library OSK Style_v1",
                "slide_number": 31,
                "slide_title": "Options comparison pattern",
                "slide_type": "options_analysis",
                "chart_type": "matrix",
                "layout_pattern": "Three options with criteria row",
                "reusable_template_instruction": "Use for build-buy-partner comparison.",
                "similarity_score": 0.82,
                "matching_method": "vector_search",
            },
        ],
        "matching_method": "vector_search",
    }


def test_recommendation_json_normalizes_into_slide_plans() -> None:
    plans = normalize_recommendation_to_slide_plans(_sample_recommendation())

    assert len(plans) == 2
    assert plans[0]["slide_type"] == "executive_summary"
    assert plans[0]["matched_template"]["deck_name"] == "OSK Strategy Template Library"
    assert plans[1]["matched_template"]["slide_number"] == 31


def test_missing_optional_fields_do_not_crash_normalizer() -> None:
    recommendation = {
        "recommended_output_mode": "slide",
        "recommended_slide_or_deck_title": "Single slide",
        "recommended_slide_structure": {
            "suggested_action_title": "Use a practical placeholder slide",
        },
    }

    plans = normalize_recommendation_to_slide_plans(recommendation)

    assert len(plans) == 1
    assert plans[0]["slide_title"] == "Use a practical placeholder slide"
    assert plans[0]["slide_type"] == "other"


def test_default_file_names_are_generated() -> None:
    path = default_output_path("Create a board-ready market entry deck", "20260515_120000")

    assert path.name == "create_a_board_ready_market_entry_deck_20260515_120000.pptx"


def test_speaker_notes_builder_returns_useful_content() -> None:
    plan = normalize_recommendation_to_slide_plans(_sample_recommendation())[0]
    notes = build_slide_notes(plan)

    assert "Slide objective:" in notes
    assert "Matched OSK template reference:" in notes
    assert "Reusable template instruction:" in notes


@pytest.mark.parametrize(
    ("slide_type", "chart_type", "expected"),
    [
        ("executive_summary", "mixed_layout", "executive_summary"),
        ("competitor_benchmark", "table", "competitor_benchmark"),
        ("market_sizing", "waterfall_chart", "market_sizing"),
        ("options_analysis", "matrix", "strategic_options"),
        ("risk_assessment", "table", "risk"),
    ],
)
def test_layout_selection_for_key_slide_types(slide_type: str, chart_type: str, expected: str) -> None:
    assert select_layout_family({"slide_type": slide_type, "chart_type": chart_type}) == expected


def test_generated_deck_metadata_is_saved(tmp_path, monkeypatch) -> None:
    metadata_dir = tmp_path / "metadata"
    monkeypatch.setitem(
        __import__("pptx_generation.pptx_repository", fromlist=["OUTPUT_DIRECTORIES"]).OUTPUT_DIRECTORIES,
        "generated_deck_metadata",
        metadata_dir,
    )

    metadata_path = save_generation_metadata({"status": "ok"}, tmp_path / "deck.pptx")

    assert metadata_path.exists()
    assert json.loads(metadata_path.read_text(encoding="utf-8"))["status"] == "ok"


def test_generator_handles_empty_recommendation_gracefully(tmp_path) -> None:
    empty_path = tmp_path / "empty.json"
    empty_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError):
        generate_placeholder_deck_from_recommendation(empty_path, tmp_path / "empty.pptx")


def test_generated_deck_from_recommendation_file(tmp_path) -> None:
    pytest.importorskip("pptx")
    recommendation_path = tmp_path / "recommendation.json"
    recommendation_path.write_text(json.dumps(_sample_recommendation()), encoding="utf-8")
    output_path = tmp_path / "stage7_test_deck.pptx"

    metadata = generate_placeholder_deck_from_recommendation(recommendation_path, output_path)

    assert Path(metadata["output_path"]).exists()
    assert metadata["number_of_content_slides"] == 2
    assert metadata["number_of_slides"] == 5
    assert Path(metadata["speaker_notes_path"]).exists()


def test_reference_deck_uses_reference_backgrounds(tmp_path, monkeypatch) -> None:
    pytest.importorskip("pptx")
    Image = pytest.importorskip("PIL.Image")
    recommendation_path = tmp_path / "recommendation.json"
    recommendation_path.write_text(json.dumps(_sample_recommendation()), encoding="utf-8")
    image_path = tmp_path / "reference.png"
    Image.new("RGB", (1600, 900), color=(240, 244, 248)).save(image_path)

    def fake_resolver(matched_template):
        return {
            "found": True,
            "deck_name": matched_template.get("deck_name"),
            "slide_number": matched_template.get("slide_number"),
            "slide_title": matched_template.get("slide_title"),
            "slide_image_path": str(image_path),
        }

    monkeypatch.setattr(
        "pptx_generation.reference_deck_generator.resolve_reference_slide_image",
        fake_resolver,
    )
    output_path = tmp_path / "stage8a_reference_deck.pptx"

    metadata = generate_reference_deck_from_recommendation(recommendation_path, output_path)

    assert Path(metadata["output_path"]).exists()
    assert metadata["generator_version"] == "stage8a_reference_image_background_v1"
    assert metadata["content_slides_with_reference_background"] == 2
    assert metadata["reference_background_mode"] == "slide_image_background_with_editable_overlays"


def test_editable_reference_deck_reports_cloned_slides(tmp_path, monkeypatch) -> None:
    pytest.importorskip("pptx")
    recommendation_path = tmp_path / "recommendation.json"
    recommendation_path.write_text(json.dumps(_sample_recommendation()), encoding="utf-8")

    def fake_clone(prs, slide_plan, presentation_cache=None):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.shapes.add_textbox(0, 0, 1000, 1000).text = slide_plan["slide_title"]
        return slide, {
            "deck_name": slide_plan["matched_template"].get("deck_name"),
            "slide_number": slide_plan["matched_template"].get("slide_number"),
            "slide_title": slide_plan["matched_template"].get("slide_title"),
            "source_file": "source.pptx",
        }

    monkeypatch.setattr(
        "pptx_generation.editable_reference_deck_generator.clone_reference_slide_into",
        fake_clone,
    )
    output_path = tmp_path / "stage8b_editable_deck.pptx"

    metadata = generate_editable_reference_deck_from_recommendation(recommendation_path, output_path)

    assert Path(metadata["output_path"]).exists()
    assert metadata["generator_version"] == "stage8b_editable_reference_slide_clone_v1"
    assert metadata["content_slides_cloned_from_source_pptx"] == 2
    assert metadata["content_slides_with_image_fallback"] == 0
