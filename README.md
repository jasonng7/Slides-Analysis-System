# Slide Intelligence System

End-to-end slide intelligence MVP for ingesting slide libraries, classifying
reusable consulting slide patterns, recommending deck structures from source
content, generating editable reference-slide PowerPoint drafts, and reviewing
generated decks with QA checks.

## What works now

- PDF/PPTX ingestion into slide images, extracted text, and metadata.
- SQLite registration for slide and content libraries.
- LLM-powered slide classification.
- Content extraction and analysis from PDF, PPTX, DOCX, TXT, MD, CSV, or pasted text.
- Semantic slide-pattern search with text embeddings.
- Slide/deck recommendation using local OSK template patterns.
- Generic, reference-image, and editable reference-slide PPTX generation.
- QA review for recommendation JSON and generated PPTX decks.
- Vercel-ready web demo dashboard in `web/`.

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

## Reference-Style Placeholder PowerPoint Generation

Generate a stronger visual draft by using matched reference slide PNGs as
non-editable backgrounds, then overlaying editable content and build-note boxes:

```bash
python src/main.py generate-reference-pptx --recommendation output/recommendations/latest_recommendation.json --output output/generated_decks/market_entry_reference_style.pptx
python src/main.py generate-reference-pptx-from-text --text "Paste content here" --goal "Create a board-ready market entry deck" --mode deck --output output/generated_decks/market_entry_reference_style.pptx
python src/main.py generate-reference-pptx-from-file --file input_content/sample_report.pdf --goal "Create a board-ready market entry deck" --mode deck --output output/generated_decks/market_entry_reference_style.pptx
```

Stage 8A uses reference slide images as backgrounds. The overlaid text boxes are
editable, but the reference background itself is not yet editable. True slide
duplication and shape-level content replacement are left for a later stage.

## Editable Reference-Slide PowerPoint Generation

Generate a more editable reference-style draft by cloning matched source PPTX
slides where possible, replacing the title, and adding editable content/build
note panels. Slides that cannot be cloned fall back to the Stage 8A image
background approach:

```bash
python src/main.py generate-editable-reference-pptx --recommendation output/recommendations/latest_recommendation.json --output output/generated_decks/market_entry_editable_reference.pptx
python src/main.py generate-editable-reference-pptx-from-text --text "Paste content here" --goal "Create a board-ready market entry deck" --mode deck --output output/generated_decks/market_entry_editable_reference.pptx
python src/main.py generate-editable-reference-pptx-from-file --file input_content/sample_report.pdf --goal "Create a board-ready market entry deck" --mode deck --output output/generated_decks/market_entry_editable_reference.pptx
```

Stage 8B is an MVP. It works best for normal text boxes, shapes, and images.
Complex grouped objects, charts, embedded workbooks, and master-layout behavior
still require manual QA.

## Generated Deck QA

Review recommendation JSON and generated PPTX files before using them:

```bash
python src/main.py review-recommendation --recommendation output/recommendations/latest_recommendation.json
python src/main.py review-generated-deck --pptx output/generated_decks/market_entry_editable_reference.pptx
python src/main.py review-latest-generated-deck
python src/main.py qa-summary
```

QA reports are saved as JSON and Markdown in `output/qa_reports/`.

## Vercel Demo Dashboard

The `web/` folder contains a Next.js dashboard for manager demos. It visualizes
the project flow and can call the EC2 FastAPI backend when
`NEXT_PUBLIC_API_BASE_URL` is configured in Vercel.

```bash
cd web
npm install
npm run dev
```

For Vercel deployment, import the GitHub repo. The root `vercel.json` builds the
Next.js app from `web/`.

Set this Vercel environment variable to enable real EC2 generation:

```bash
NEXT_PUBLIC_API_BASE_URL=http://13.214.251.94
```

Use HTTPS and a domain later for production. Supabase or Vercel Blob should be
added later only when browser uploads, persistent cloud jobs, and shared
generated files are needed.

## EC2 API Backend

The FastAPI backend exposes the local Python engine over HTTP:

```bash
.venv/bin/uvicorn --app-dir src api.app:app --host 127.0.0.1 --port 8000
```

Useful endpoints:

- `GET /api/health`
- `POST /api/jobs/text`
- `POST /api/jobs/file`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/download`

For the current MVP, generated files are stored temporarily on EC2 and cleaned
after 15 minutes by the `slide-analysis-cleanup.timer` systemd timer.

Example text job:

```bash
curl -X POST http://127.0.0.1:8000/api/jobs/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We are evaluating whether OSK should enter the earned wage access market in Malaysia.",
    "goal": "Create a board-ready market entry recommendation deck",
    "mode": "deck"
  }'
```

Outputs are written to:

- `output/slide_images/`
- `output/extracted_text/`
- `output/parsed_objects/`
- `output/classified_slides/`
- `output/content_analysis/`
- `output/recommendations/`
- `output/embeddings/`
- `output/generated_decks/`
- `output/qa_reports/`
