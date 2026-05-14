import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from content.content_schema import validate_recommendation
from recommendation.generate_slide_prompt import generate_prompt_from_recommendation
from recommendation.match_slide_patterns import find_relevant_slide_patterns


def content_analysis():
    return {
        "content_summary": "EWA market has emerging providers and employer concerns.",
        "business_context": "Malaysia EWA market entry",
        "likely_audience": "executive_committee",
        "content_tags": ["ewa", "market_entry", "competitor_landscape"],
        "suitable_slide_types": ["competitor_landscape"],
    }


def valid_recommendation(mode="slide"):
    return {
        "recommendation_type": "single_slide",
        "brief_interpretation": "Create a competitor landscape slide.",
        "content_diagnosis": "Content is directional and needs competitor evidence.",
        "recommended_output_mode": mode,
        "recommended_audience_type": "executive_committee",
        "recommended_slide_or_deck_title": "Malaysia EWA competitor landscape",
        "recommended_storyline": "Market remains early and fragmented.",
        "recommended_slide_structure": {
            "recommended_slide_type": "competitor_landscape",
            "recommended_chart_type": "table",
            "recommended_storyline_type": "market_trend_opportunity",
            "suggested_action_title": "Malaysia's EWA market remains fragmented, creating space for a trusted entrant",
            "layout_instruction": "Use an action title, competitor table, and implication box.",
            "content_blocks": ["competitor list", "employer concerns", "implication"],
            "data_required": ["competitor names", "pricing", "customer segments"],
            "analysis_required": ["compare competitor positioning"],
            "missing_data_or_research_gaps": ["market share"],
            "powerpoint_template_instruction": "Benchmark table with right-side implication box.",
            "quality_checklist": ["clear action title", "source all claims"],
        },
        "recommended_deck_structure": {
            "suggested_deck_title": "EWA market entry assessment",
            "sections": [
                {
                    "section_name": "Market context",
                    "section_purpose": "Frame opportunity",
                    "recommended_slides": [
                        {
                            "slide_title": "Market overview",
                            "slide_type": "industry_overview",
                            "chart_type": "mixed_layout",
                            "storyline_type": "market_trend_opportunity",
                            "content_to_use_from_source": "emerging providers",
                            "additional_data_needed": "market size",
                            "template_instruction": "overview with implication box",
                        }
                    ],
                }
            ],
        },
        "similar_slide_patterns_used": [],
        "alternative_structures": ["market attractiveness"],
        "next_steps_for_user": ["collect competitor pricing"],
    }


class RecommendFromContentTests(unittest.TestCase):
    def test_recommendation_json_required_fields_exist(self):
        result = validate_recommendation(valid_recommendation())

        self.assertIn("recommended_slide_structure", result)
        self.assertIn("recommended_deck_structure", result)

    def test_system_works_when_no_classified_slides_are_available(self):
        with patch("recommendation.match_slide_patterns.load_embedding_index", return_value=[]), patch(
            "recommendation.match_slide_patterns.get_classified_slide_patterns", return_value=[]
        ):
            self.assertEqual(find_relevant_slide_patterns(content_analysis(), None), [])

    def test_system_works_when_classified_slide_patterns_exist(self):
        patterns = [
            {
                "deck_name": "sample",
                "slide_number": 1,
                "slide_title": "Competitor landscape",
                "slide_text": "EWA competitors and market entry",
                "slide_type": "competitor_landscape",
                "chart_type": "table",
                "storyline_type": "market_trend_opportunity",
                "audience_type": "executive_committee",
                "business_context": "Malaysia EWA market entry",
                "layout_pattern": "Table plus implication box",
                "tags": ["ewa", "competitor_landscape"],
                "reusable_template_instruction": "Reuse as a competitor table.",
            }
        ]

        with patch("recommendation.match_slide_patterns.load_embedding_index", return_value=[]), patch(
            "recommendation.match_slide_patterns.get_classified_slide_patterns", return_value=patterns
        ):
            matches = find_relevant_slide_patterns(content_analysis(), "EWA market entry")

        self.assertEqual(len(matches), 1)
        self.assertGreater(matches[0]["match_score"], 0)

    def test_prompt_generation_works_for_slide_mode(self):
        prompt = generate_prompt_from_recommendation(valid_recommendation("slide"))

        self.assertIn("Recommended slide type", prompt)
        self.assertIn("Content blocks", prompt)

    def test_prompt_generation_works_for_deck_mode(self):
        prompt = generate_prompt_from_recommendation(valid_recommendation("deck"))

        self.assertIn("Deck outline", prompt)
        self.assertIn("Market context", prompt)


if __name__ == "__main__":
    unittest.main()
