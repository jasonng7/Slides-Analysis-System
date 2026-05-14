import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from embeddings.search_similar_slides import search_similar_slides_by_text
from recommendation.match_slide_patterns import (
    build_recommendation_search_query,
    find_relevant_slide_patterns,
)


def sample_analysis():
    return {
        "content_summary": "Malaysia EWA competitors and employer adoption.",
        "business_context": "EWA market entry",
        "primary_analysis_type": "competitor_analysis",
        "secondary_analysis_types": ["market_research"],
        "key_topics": ["earned wage access", "employer adoption"],
        "content_tags": ["ewa", "market_entry", "competitor_landscape"],
        "suitable_slide_types": ["competitor_landscape", "competitor_benchmark"],
        "likely_audience": "executive_committee",
    }


class VectorSearchTests(unittest.TestCase):
    def test_search_handles_empty_index_gracefully(self):
        with patch("embeddings.search_similar_slides.load_embedding_index", return_value=[]), patch(
            "embeddings.search_similar_slides.rebuild_index_from_embedding_files", return_value=[]
        ):
            self.assertEqual(search_similar_slides_by_text("market entry", top_k=5), [])

    def test_recommendation_falls_back_to_metadata_matching_without_embeddings(self):
        patterns = [
            {
                "deck_name": "OSK",
                "slide_number": 1,
                "slide_title": "Competitor landscape",
                "slide_text": "EWA market entry competitor analysis",
                "slide_type": "competitor_landscape",
                "chart_type": "table",
                "storyline_type": "market_trend_opportunity",
                "audience_type": "executive_committee",
                "business_context": "EWA market entry",
                "layout_pattern": "table plus implication box",
                "tags": ["ewa", "competitor_landscape"],
                "reusable_template_instruction": "Use for competitor landscape.",
            }
        ]
        with patch("recommendation.match_slide_patterns.load_embedding_index", return_value=[]), patch(
            "recommendation.match_slide_patterns.get_classified_slide_patterns", return_value=patterns
        ):
            matches = find_relevant_slide_patterns(sample_analysis(), "market entry")

        self.assertEqual(matches[0]["matching_method"], "metadata_match")
        self.assertGreater(matches[0]["match_score"], 0)

    def test_recommendation_uses_vector_search_when_embeddings_exist(self):
        vector_result = [
            {
                "slide_id": 1,
                "deck_name": "OSK",
                "slide_number": 2,
                "slide_title": "Vector result",
                "slide_type": "competitor_benchmark",
                "chart_type": "table",
                "matching_method": "vector_search",
                "similarity_score": 0.91,
            }
        ]
        with patch("recommendation.match_slide_patterns.load_embedding_index", return_value=[{"slide_id": 1}]), patch(
            "recommendation.match_slide_patterns.search_similar_slides_by_text", return_value=vector_result
        ):
            matches = find_relevant_slide_patterns(sample_analysis(), "market entry")

        self.assertEqual(matches, vector_result)

    def test_query_construction_works_from_sample_content_analysis(self):
        query = build_recommendation_search_query(
            sample_analysis(),
            "Create a board-ready market entry recommendation deck",
        )

        self.assertIn("board-ready market entry", query)
        self.assertIn("Malaysia EWA competitors", query)
        self.assertIn("competitor_landscape", query)
        self.assertIn("executive_committee", query)


if __name__ == "__main__":
    unittest.main()
