import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from content.content_schema import validate_content_analysis


def valid_analysis():
    return {
        "content_summary": "The content describes an emerging market opportunity.",
        "document_type": "raw_notes",
        "business_context": "EWA market entry",
        "primary_analysis_type": "competitor_analysis",
        "secondary_analysis_types": ["market_research"],
        "likely_audience": "executive_committee",
        "recommended_output_mode": "slide",
        "key_topics": ["EWA", "competitors"],
        "key_entities": ["OSK", "EWA providers"],
        "metrics_detected": ["implementation cost"],
        "time_periods_detected": [],
        "geographies_detected": ["Malaysia"],
        "strategic_questions_answered": ["Which factors matter to employers?"],
        "strategic_questions_unanswered": ["Which competitors have strongest traction?"],
        "content_tags": ["ewa", "market_entry", "competitor_landscape"],
        "suitable_slide_types": ["competitor_landscape"],
        "suitable_deck_sections": ["Market context"],
        "missing_data_or_research_gaps": ["Competitor market share"],
        "data_quality_assessment": "Directional notes only.",
        "presentation_implications": "Use a competitor landscape structure.",
    }


class ContentAnalysisSchemaTests(unittest.TestCase):
    def test_required_fields_exist(self):
        result = validate_content_analysis(valid_analysis())

        self.assertIn("content_summary", result)
        self.assertIn("recommended_output_mode", result)

    def test_missing_required_field_raises(self):
        payload = valid_analysis()
        del payload["content_summary"]

        with self.assertRaises(ValueError):
            validate_content_analysis(payload)

    def test_invalid_values_fall_back(self):
        payload = valid_analysis()
        payload["document_type"] = "memo"
        payload["primary_analysis_type"] = "great_analysis"
        payload["likely_audience"] = "everyone"
        payload["recommended_output_mode"] = "poster"
        payload["suitable_slide_types"] = ["bespoke"]

        result = validate_content_analysis(payload)

        self.assertEqual(result["document_type"], "unknown")
        self.assertEqual(result["primary_analysis_type"], "unknown")
        self.assertEqual(result["likely_audience"], "unknown")
        self.assertEqual(result["recommended_output_mode"], "auto")
        self.assertEqual(result["suitable_slide_types"], ["other"])


if __name__ == "__main__":
    unittest.main()
