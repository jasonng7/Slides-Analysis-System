import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from database.repository import get_database_summary, register_ingested_deck
from database.schema import initialize_database


class DatabaseTests(unittest.TestCase):
    def test_initialize_database_creates_required_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "slide_library.sqlite"

            initialize_database(db_path)

            with sqlite3.connect(db_path) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }

            self.assertIn("decks", tables)
            self.assertIn("slides", tables)
            self.assertIn("slide_tags", tables)
            self.assertIn("embeddings", tables)

    def test_register_ingested_deck_is_idempotent_by_source_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "slide_library.sqlite"
            source_file = str(Path(temp_dir) / "sample.pdf")

            first_records = [
                {
                    "slide_number": 1,
                    "slide_title": "First title",
                    "slide_text": "First title\nBody",
                    "slide_image_path": "/tmp/slide_001.png",
                    "extracted_text_path": "/tmp/slide_001.txt",
                    "created_at": "2026-05-14T00:00:00+00:00",
                },
                {
                    "slide_number": 2,
                    "slide_title": "Second title",
                    "slide_text": "Second title\nBody",
                    "slide_image_path": "/tmp/slide_002.png",
                    "extracted_text_path": "/tmp/slide_002.txt",
                    "created_at": "2026-05-14T00:00:00+00:00",
                },
            ]
            second_records = [first_records[0]]

            first_deck_id = register_ingested_deck(
                deck_name="sample",
                source_file=source_file,
                source_type="pdf",
                slide_records=first_records,
                db_path=db_path,
            )
            second_deck_id = register_ingested_deck(
                deck_name="sample",
                source_file=source_file,
                source_type="pdf",
                slide_records=second_records,
                db_path=db_path,
            )

            summary = get_database_summary(db_path)

            self.assertEqual(first_deck_id, second_deck_id)
            self.assertEqual(summary.deck_count, 1)
            self.assertEqual(summary.slide_count, 1)
            self.assertEqual(summary.slides_by_source_type, [("pdf", 1)])


if __name__ == "__main__":
    unittest.main()
