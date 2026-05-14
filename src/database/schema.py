from pathlib import Path

from database.db import get_connection


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS decks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  deck_name TEXT,
  source_file TEXT,
  source_type TEXT,
  business_domain TEXT,
  created_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_decks_source_file
ON decks(source_file);

CREATE TABLE IF NOT EXISTS slides (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  deck_id INTEGER,
  slide_number INTEGER,
  slide_title TEXT,
  slide_text TEXT,
  slide_image_path TEXT,
  extracted_text_path TEXT,
  slide_type TEXT,
  chart_type TEXT,
  storyline_type TEXT,
  audience_type TEXT,
  business_context TEXT,
  layout_pattern TEXT,
  reusable_template_instruction TEXT,
  quality_score REAL,
  created_at TEXT,
  FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_slides_deck_id
ON slides(deck_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_slides_deck_number
ON slides(deck_id, slide_number);

CREATE TABLE IF NOT EXISTS slide_tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slide_id INTEGER,
  tag TEXT,
  FOREIGN KEY(slide_id) REFERENCES slides(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_slide_tags_slide_id
ON slide_tags(slide_id);

CREATE TABLE IF NOT EXISTS embeddings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slide_id INTEGER,
  embedding_type TEXT,
  vector_path TEXT,
  created_at TEXT,
  FOREIGN KEY(slide_id) REFERENCES slides(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_embeddings_slide_id
ON embeddings(slide_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_embeddings_slide_type
ON embeddings(slide_id, embedding_type);

CREATE TABLE IF NOT EXISTS content_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_name TEXT,
  source_file TEXT,
  source_type TEXT,
  user_goal TEXT,
  raw_text_path TEXT,
  analysis_json_path TEXT,
  content_summary TEXT,
  document_type TEXT,
  business_context TEXT,
  primary_analysis_type TEXT,
  recommended_output_mode TEXT,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_content_sources_source_type
ON content_sources(source_type);

CREATE TABLE IF NOT EXISTS content_tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content_source_id INTEGER,
  tag TEXT,
  FOREIGN KEY(content_source_id) REFERENCES content_sources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_tags_content_source_id
ON content_tags(content_source_id);

CREATE TABLE IF NOT EXISTS content_entities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content_source_id INTEGER,
  entity TEXT,
  entity_type TEXT,
  FOREIGN KEY(content_source_id) REFERENCES content_sources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_entities_content_source_id
ON content_entities(content_source_id);

CREATE TABLE IF NOT EXISTS content_recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content_source_id INTEGER,
  recommendation_json_path TEXT,
  recommendation_txt_path TEXT,
  output_mode TEXT,
  recommended_slide_type TEXT,
  recommended_deck_sections TEXT,
  created_at TEXT,
  FOREIGN KEY(content_source_id) REFERENCES content_sources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_recommendations_content_source_id
ON content_recommendations(content_source_id);
"""


def initialize_database(db_path: Path | None = None) -> None:
    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
