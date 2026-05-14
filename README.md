# Slide Intelligence System

Stage 1/2 prototype for ingesting PDF and PPTX decks.

## What works now

- Creates the planned project folders.
- Converts PDF pages into PNG slide images.
- Converts PPTX slides into PNG slide images through LibreOffice.
- Extracts text from PDF pages and PPTX slides.
- Writes one metadata JSON file per slide.

Later stages will add SQLite storage, classification, embeddings, recommendations,
and placeholder PowerPoint generation.

## Install

```bash
python3 -m pip install -r requirements.txt
```

PPTX rendering requires LibreOffice (`soffice`) to be available on `PATH`.

## Ingest a deck

```bash
python src/main.py ingest --file input_decks/pdf/sample.pdf
python src/main.py ingest --file input_decks/pptx/sample.pptx
python src/main.py ingest --folder input_decks
```

Ingestion also registers decks and slides in `data/slide_library.sqlite`.

## Database

```bash
python src/main.py db-init
python src/main.py db-summary
```

## Classification

Create a local `.env` file:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.5
```

Then classify ingested slides:

```bash
python src/main.py classify --limit 5
python src/main.py classify --deck sample
python src/main.py classify --all
python src/main.py classification-summary
```

## Content Analysis and Recommendation

Analyze pasted text or a source file:

```bash
python src/main.py analyze-content --text "Paste content here" --goal "Create a market opportunity slide" --mode slide
python src/main.py analyze-content --file input_content/sample_report.pdf --goal "Create a board-ready strategy update" --mode auto
```

Recommend a slide/deck structure from the analyzed content:

```bash
python src/main.py recommend --text "Paste content here" --goal "Create a competitor landscape slide" --mode slide --prompt
python src/main.py recommend --file input_content/sample_report.pdf --goal "Create a board-ready market entry deck" --mode deck
python src/main.py content-summary
```

Supported Stage 5 content inputs: `.pdf`, `.pptx`, `.docx`, `.txt`, `.md`, and basic `.csv`.
`.xlsx` is intentionally left as a later-stage placeholder.

## Embeddings and Search

Create text embeddings for classified slides:

```bash
python src/main.py embed-slides --limit 10
python src/main.py embed-slides
python src/main.py embedding-summary
```

Search the slide library semantically:

```bash
python src/main.py search-slides --query "competitor benchmarking table for market entry analysis" --top-k 5
```

## Placeholder PowerPoint Generation

Generate an editable placeholder PPTX from an existing recommendation JSON:

```bash
python src/main.py generate-pptx --recommendation output/recommendations/latest_recommendation.json --output output/generated_decks/market_entry_recommendation.pptx
```

Or run the recommendation pipeline and PPTX generator directly from source content:

```bash
python src/main.py generate-pptx-from-text --text "Paste content here" --goal "Create a board-ready market entry deck" --mode deck --output output/generated_decks/market_entry_deck.pptx
python src/main.py generate-pptx-from-file --file input_content/sample_report.pdf --goal "Create a board-ready market entry deck" --mode deck --output output/generated_decks/market_entry_deck.pptx
python src/main.py generated-deck-summary
```

Stage 7 generates placeholder skeleton decks only. It does not recreate OSK design
styling or generate final polished slides.

Outputs are written to:

- `output/slide_images/`
- `output/extracted_text/`
- `output/parsed_objects/`
- `output/classified_slides/`
- `output/content_analysis/`
- `output/recommendations/`
- `output/embeddings/`
- `output/generated_decks/`
