import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from embeddings.build_vector_index import build_slide_text_for_embedding
from embeddings.search_similar_slides import cosine_similarity


class EmbeddingTests(unittest.TestCase):
    def test_cosine_similarity_works(self):
        self.assertAlmostEqual(cosine_similarity([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(cosine_similarity([1, 0], [0, 1]), 0.0)
        self.assertEqual(cosine_similarity([1, 0], [1]), 0.0)

    def test_build_slide_text_for_embedding_includes_key_fields(self):
        slide = {
            "deck_name": "Corporate Template Library OSK Style_v1",
            "slide_number": 31,
            "slide_title": "Competitor Benchmarking Table",
            "slide_type": "competitor_benchmark",
            "chart_type": "table",
            "storyline_type": "options_evaluation_recommendation",
            "audience_type": "executive_committee",
            "business_context": "comparing companies across key metrics",
            "layout_pattern": "benchmarking table with implication box",
            "reusable_template_instruction": "Use for comparing peers.",
            "slide_text": "Competitor A | Competitor B",
        }

        text = build_slide_text_for_embedding(slide, ["competitor analysis", "benchmarking"])

        self.assertIn("Deck: Corporate Template Library OSK Style_v1", text)
        self.assertIn("Slide type: competitor_benchmark", text)
        self.assertIn("Chart type: table", text)
        self.assertIn("Tags: competitor analysis, benchmarking", text)
        self.assertIn("Slide text: Competitor A | Competitor B", text)


if __name__ == "__main__":
    unittest.main()
