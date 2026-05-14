import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from classification.classify_slide import REQUIRED_FIELDS, validate_classification


def valid_payload():
    return {
        "slide_title": "Market opportunity is concentrated in one segment",
        "action_title_quality": "strong_insight_title",
        "slide_type": "market_attractiveness",
        "chart_type": "bar_chart",
        "storyline_type": "market_trend_opportunity",
        "audience_type": "executive_committee",
        "business_context": "market growth analysis",
        "layout_pattern": "Title at top, chart on left, implication box on right.",
        "content_blocks": ["action title", "chart", "implication"],
        "detected_objects": ["title", "chart", "legend"],
        "tags": ["market", "growth", "strategy", "chart", "opportunity"],
        "reusable_template_instruction": "Reuse for comparing segment mix across periods.",
        "recommended_use_cases": ["market sizing", "portfolio review"],
        "quality_score": 88,
    }


class ClassificationSchemaTests(unittest.TestCase):
    def test_required_fields_exist(self):
        classification = validate_classification(valid_payload())

        for field in REQUIRED_FIELDS:
            self.assertIn(field, classification)

    def test_missing_required_field_raises(self):
        payload = valid_payload()
        del payload["slide_type"]

        with self.assertRaises(ValueError):
            validate_classification(payload)

    def test_invalid_taxonomy_values_fall_back(self):
        payload = valid_payload()
        payload["action_title_quality"] = "great"
        payload["slide_type"] = "made_up_slide"
        payload["chart_type"] = "made_up_chart"
        payload["storyline_type"] = "made_up_story"
        payload["audience_type"] = "made_up_audience"

        classification = validate_classification(payload)

        self.assertEqual(classification["action_title_quality"], "unclear_title")
        self.assertEqual(classification["slide_type"], "other")
        self.assertEqual(classification["chart_type"], "unknown")
        self.assertEqual(classification["storyline_type"], "other")
        self.assertEqual(classification["audience_type"], "unknown")

    def test_quality_score_is_clamped_between_zero_and_one_hundred(self):
        payload = valid_payload()
        payload["quality_score"] = 200
        self.assertEqual(validate_classification(payload)["quality_score"], 100.0)

        payload["quality_score"] = -10
        self.assertEqual(validate_classification(payload)["quality_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
