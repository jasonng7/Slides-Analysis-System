# BUILD_PLAN.md — Consulting & Corporate Strategy Slide Intelligence System

## 1. Project Objective

Build a slide intelligence system that helps users structure future presentation slides by learning from reference decks and extracting reusable slide patterns.

The system should support both:

1. Consulting-style slides  
   - Strategy recommendations
   - Executive summaries
   - Market sizing
   - Competitor benchmarking
   - Operating model
   - Roadmaps
   - Transformation plans
   - Root-cause diagnostics

2. Corporate strategy slides  
   - M&A / corporate exercise analysis
   - Joint venture evaluation
   - Industry research
   - Competitor and market valuation analysis
   - Emerging trends
   - Key opportunities and challenges
   - Board / ExCo / CEO-level strategy updates

The system should not copy slide designs or proprietary content. It should extract generic, reusable structure, layout, storyline, and communication patterns.

---

## 2. End-to-End Target Workflow

```text
1. Slide Library Collection
   ↓
2. PDF/PPTX to slide images + text
   ↓
3. Slide parser
   - Extract title
   - Extract text blocks
   - Detect charts/tables/shapes
   - Identify layout zones
   ↓
4. Slide classifier
   - Slide type
   - Chart type
   - Storyline type
   - Audience type
   ↓
5. Vector database
   - Store image embeddings
   - Store text embeddings
   - Store tags and metadata
   ↓
6. Slide recommendation engine
   ↓
7. Prompt generator / PowerPoint template generator
```

---

## 3. MVP Scope

Build the first version as an LLM-powered slide classifier and recommender, not a custom ML model.

### MVP Input

- PDF consulting decks
- PPTX decks
- Corporate strategy decks
- Industry research decks
- Valuation / M&A / JV related decks

### MVP Output

For every slide, generate a structured JSON record:

```json
{
  "deck_name": "",
  "slide_number": 1,
  "slide_title": "",
  "action_title_quality": "",
  "slide_type": "",
  "chart_type": "",
  "storyline_type": "",
  "audience_type": "",
  "business_context": "",
  "layout_pattern": "",
  "content_blocks": [],
  "detected_objects": [],
  "tags": [],
  "reusable_template_instruction": "",
  "recommended_use_cases": [],
  "source_file": "",
  "slide_image_path": "",
  "extracted_text_path": ""
}
```

---

## 4. Recommended Tech Stack

### Core Language

Python

### Suggested Libraries

| Function | Recommended Tool |
|---|---|
| PDF slide rendering | PyMuPDF |
| PPTX parsing | python-pptx |
| Image processing | Pillow, OpenCV |
| OCR fallback | Tesseract or cloud vision API |
| Table detection | OpenCV + LLM verification |
| Chart detection | LLM vision + heuristic rules |
| Text embeddings | OpenAI embeddings or local sentence-transformers |
| Image embeddings | CLIP or multimodal embedding API |
| Metadata storage | SQLite for MVP |
| Vector database | ChromaDB or FAISS for MVP; Supabase / pgvector later |
| PowerPoint generation | python-pptx |
| CLI app | Typer or argparse |
| Config | YAML or JSON |

---

## 5. Recommended Project Structure

```text
slide-intelligence-system/
  README.md
  BUILD_PLAN.md
  requirements.txt
  .env.example

  input_decks/
    pdf/
    pptx/

  output/
    slide_images/
    extracted_text/
    parsed_objects/
    classified_slides/
    embeddings/
    generated_templates/
    recommendations/

  data/
    slide_library.sqlite
    taxonomy.yaml
    prompt_templates.yaml

  src/
    main.py
    config.py

    ingestion/
      collect_library.py
      convert_pdf_to_images.py
      convert_pptx_to_images.py
      extract_pptx_objects.py
      extract_text_from_pdf.py
      extract_text_from_pptx.py

    parsing/
      parse_slide_layout.py
      detect_layout_zones.py
      detect_tables.py
      detect_charts.py
      normalize_slide_record.py

    classification/
      classify_slide.py
      classify_slide_batch.py
      taxonomy.py
      prompts.py

    embeddings/
      embed_text.py
      embed_image.py
      build_vector_index.py
      search_similar_slides.py

    recommendation/
      recommend_slide_structure.py
      generate_slide_prompt.py
      generate_storyline.py

    pptx_generation/
      generate_placeholder_pptx.py
      layout_templates.py
      style_guide.py

    quality_check/
      score_slide_quality.py
      check_action_title.py
      check_consulting_style.py

    utils/
      file_utils.py
      json_utils.py
      logging_utils.py

  tests/
    test_ingestion.py
    test_classification.py
    test_recommendation.py
```

---

## 6. Slide Taxonomy

The system should classify slides into the following categories.

### 6.1 Consulting Slide Types

```yaml
consulting_slide_types:
  - executive_summary
  - situation_complication_resolution
  - issue_tree
  - hypothesis_tree
  - market_sizing
  - competitor_benchmark
  - 2x2_matrix
  - value_chain
  - process_flow
  - operating_model
  - roadmap
  - gantt_timeline
  - waterfall
  - heatmap
  - dashboard
  - financial_summary
  - recommendation_slide
  - options_analysis
  - prioritization_matrix
  - risk_assessment
  - stakeholder_map
  - transformation_journey
  - implementation_plan
```

### 6.2 Corporate Strategy Slide Types

```yaml
corporate_strategy_slide_types:
  - corporate_exercise_overview
  - merger_acquisition_rationale
  - merger_acquisition_deal_structure
  - joint_venture_rationale
  - joint_venture_operating_model
  - strategic_partnership_analysis
  - industry_overview
  - industry_trend_analysis
  - market_attractiveness
  - market_entry_strategy
  - competitor_landscape
  - competitor_deep_dive
  - valuation_comparison
  - precedent_transaction_analysis
  - trading_comparable_analysis
  - synergy_assessment
  - strategic_fit_assessment
  - investment_thesis
  - opportunity_challenge_analysis
  - growth_options_analysis
  - business_case_summary
  - board_decision_paper
```

### 6.3 Chart Types

```yaml
chart_types:
  - bar_chart
  - stacked_bar_chart
  - line_chart
  - area_chart
  - pie_chart
  - donut_chart
  - waterfall_chart
  - bubble_chart
  - scatter_plot
  - heatmap
  - table
  - matrix
  - flow_diagram
  - timeline
  - gantt_chart
  - value_chain_diagram
  - map
  - dashboard_cards
  - icon_grid
  - text_only
  - mixed_layout
```

### 6.4 Storyline Types

```yaml
storyline_types:
  - problem_solution
  - situation_complication_resolution
  - insight_evidence_implication
  - options_evaluation_recommendation
  - current_state_future_state_gap
  - market_trend_opportunity
  - diagnosis_root_cause_action
  - hypothesis_evidence_conclusion
  - investment_thesis_supporting_evidence
  - risk_mitigation
  - strategy_execution_impact
  - before_after_bridge
```

### 6.5 Audience Types

```yaml
audience_types:
  - board_of_directors
  - ceo
  - executive_committee
  - head_of_department
  - corporate_strategy_team
  - investment_committee
  - project_steering_committee
  - internal_management
  - external_client
  - general_business_audience
```

---

## 7. Data Model

Use SQLite for MVP. Suggested tables:

### 7.1 decks

```sql
CREATE TABLE decks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  deck_name TEXT,
  source_file TEXT,
  source_type TEXT,
  business_domain TEXT,
  created_at TEXT
);
```

### 7.2 slides

```sql
CREATE TABLE slides (
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
  FOREIGN KEY(deck_id) REFERENCES decks(id)
);
```

### 7.3 slide_tags

```sql
CREATE TABLE slide_tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slide_id INTEGER,
  tag TEXT,
  FOREIGN KEY(slide_id) REFERENCES slides(id)
);
```

### 7.4 embeddings

```sql
CREATE TABLE embeddings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slide_id INTEGER,
  embedding_type TEXT,
  vector_path TEXT,
  created_at TEXT,
  FOREIGN KEY(slide_id) REFERENCES slides(id)
);
```

---

## 8. Main Pipeline

### 8.1 Ingest Deck

Command:

```bash
python src/main.py ingest --file input_decks/pdf/sample.pdf
```

Expected actions:

1. Register deck metadata
2. Convert each page / slide into PNG
3. Extract text
4. Save image and text files
5. Create preliminary slide records

---

### 8.2 Parse Slide

Command:

```bash
python src/main.py parse --deck sample
```

Expected actions:

1. Identify title region
2. Extract text blocks
3. Detect major visual zones
4. Detect tables, charts, icons, callouts, footnotes
5. Output structured parse JSON per slide

---

### 8.3 Classify Slide

Command:

```bash
python src/main.py classify --deck sample
```

Expected actions:

1. Send slide image + extracted text to LLM
2. Classify:
   - slide type
   - chart type
   - storyline type
   - audience type
   - business context
   - layout pattern
3. Generate reusable template instruction
4. Save classification JSON
5. Update SQLite database

---

### 8.4 Build Embeddings

Command:

```bash
python src/main.py embed --deck sample
```

Expected actions:

1. Generate text embedding from extracted text and classification
2. Generate image embedding from slide image if available
3. Store vectors locally
4. Update vector index

---

### 8.5 Recommend Slide Structure

Command:

```bash
python src/main.py recommend --brief "Compare EWA competitors in Malaysia and identify market opportunity for OSK"
```

Expected output:

```json
{
  "recommended_slide_type": "competitor_landscape",
  "recommended_layout": "benchmark table with right-side implication box",
  "recommended_storyline": "market_trend_opportunity",
  "suggested_title": "Malaysia's EWA landscape remains early-stage, creating space for a trusted financial services-led entrant",
  "content_blocks": [
    "Competitor comparison table",
    "Fee model / pricing comparison",
    "Target customer segment",
    "Key opportunity white space",
    "Strategic implication"
  ],
  "similar_reference_slides": [],
  "powerpoint_template_instruction": ""
}
```

---

### 8.6 Generate Placeholder PowerPoint

Command:

```bash
python src/main.py generate-pptx --brief "Create a board-ready slide on M&A rationale for acquiring a fintech platform"
```

Expected actions:

1. Recommend slide structure
2. Generate PowerPoint layout with placeholders
3. Use generic corporate / consulting style
4. Export `.pptx`

Expected output:

```text
output/generated_templates/ma_rationale_template.pptx
```

---

## 9. LLM Classification Prompt

Use this as the core prompt for slide classification.

```text
You are a senior strategy consultant and presentation design expert.

Analyze the provided slide image and extracted text. Your job is to classify the slide into reusable consulting and corporate strategy patterns.

Do not copy the slide. Do not reproduce proprietary wording. Extract only generic structure, storyline, communication logic, and layout patterns.

Return valid JSON only.

Classify the slide using the following fields:

1. slide_title
2. action_title_quality
   - strong_insight_title
   - descriptive_topic_title
   - unclear_title
   - missing_title

3. slide_type
Choose from:
- executive_summary
- situation_complication_resolution
- issue_tree
- hypothesis_tree
- market_sizing
- competitor_benchmark
- 2x2_matrix
- value_chain
- process_flow
- operating_model
- roadmap
- gantt_timeline
- waterfall
- heatmap
- dashboard
- financial_summary
- recommendation_slide
- options_analysis
- prioritization_matrix
- risk_assessment
- stakeholder_map
- transformation_journey
- implementation_plan
- corporate_exercise_overview
- merger_acquisition_rationale
- merger_acquisition_deal_structure
- joint_venture_rationale
- joint_venture_operating_model
- strategic_partnership_analysis
- industry_overview
- industry_trend_analysis
- market_attractiveness
- market_entry_strategy
- competitor_landscape
- competitor_deep_dive
- valuation_comparison
- precedent_transaction_analysis
- trading_comparable_analysis
- synergy_assessment
- strategic_fit_assessment
- investment_thesis
- opportunity_challenge_analysis
- growth_options_analysis
- business_case_summary
- board_decision_paper
- other

4. chart_type
Choose from:
- bar_chart
- stacked_bar_chart
- line_chart
- area_chart
- pie_chart
- donut_chart
- waterfall_chart
- bubble_chart
- scatter_plot
- heatmap
- table
- matrix
- flow_diagram
- timeline
- gantt_chart
- value_chain_diagram
- map
- dashboard_cards
- icon_grid
- text_only
- mixed_layout
- unknown

5. storyline_type
Choose from:
- problem_solution
- situation_complication_resolution
- insight_evidence_implication
- options_evaluation_recommendation
- current_state_future_state_gap
- market_trend_opportunity
- diagnosis_root_cause_action
- hypothesis_evidence_conclusion
- investment_thesis_supporting_evidence
- risk_mitigation
- strategy_execution_impact
- before_after_bridge
- other

6. audience_type
Choose from:
- board_of_directors
- ceo
- executive_committee
- head_of_department
- corporate_strategy_team
- investment_committee
- project_steering_committee
- internal_management
- external_client
- general_business_audience
- unknown

7. business_context
Describe the likely business context in one short phrase.

8. layout_pattern
Describe the slide layout generically. Example:
"Action title at top, three-column comparison table in body, key implication box on right, source note at bottom."

9. content_blocks
List the major content blocks on the slide.

10. detected_objects
List visible objects such as:
- title
- subtitle
- chart
- table
- icons
- callout box
- legend
- source note
- footnote
- logo
- section divider

11. tags
Generate 5 to 10 searchable tags.

12. reusable_template_instruction
Explain how to reuse this slide structure for a different business topic.

13. recommended_use_cases
List situations where this slide structure would be useful.

14. quality_score
Score from 0 to 100 based on:
- message clarity
- layout clarity
- chart appropriateness
- executive readability
- reusability

Return JSON only.
```

---

## 10. Slide Recommendation Prompt

```text
You are a senior strategy consultant helping the user choose the best slide structure for a business message.

The user will provide a slide brief. Your job is to recommend the most suitable consulting or corporate strategy slide structure.

Consider:
- Intended audience
- Business objective
- Type of analysis
- Suitable slide archetype
- Best chart or visual
- Recommended storyline
- Required content blocks
- Possible title
- Recommended PowerPoint layout

Return valid JSON only.

User slide brief:
{{SLIDE_BRIEF}}

Return this structure:

{
  "brief_interpretation": "",
  "recommended_slide_type": "",
  "recommended_chart_type": "",
  "recommended_storyline_type": "",
  "recommended_audience_type": "",
  "suggested_action_title": "",
  "layout_instruction": "",
  "content_blocks": [],
  "data_required": [],
  "analysis_required": [],
  "similar_slide_search_queries": [],
  "powerpoint_template_instruction": "",
  "quality_checklist": []
}
```

---

## 11. Prompt Generator Output

The system should generate prompts that help the user create slide content.

Example:

```text
Create a board-ready consulting-style slide on [topic].

Audience:
[Board / CEO / ExCo / HOD]

Objective:
[Decision / update / recommendation / alignment]

Recommended slide type:
[Competitor benchmark / market attractiveness / M&A rationale]

Slide structure:
- Top: action-oriented title
- Left: key context
- Middle: core analysis
- Right: implications / recommendation
- Bottom: sources and assumptions

Content requirements:
1. [Block 1]
2. [Block 2]
3. [Block 3]

Design requirements:
- Use clear hierarchy
- Use concise labels
- Use consulting-style layout
- Avoid decorative visuals
- Include source note
```

---

## 12. Placeholder PowerPoint Template Requirements

The PowerPoint generator should create generic reusable templates with placeholders, not finished slides.

### Template Format

Use placeholders such as:

```text
[Insert action title]
[Insert key takeaway]
[Insert competitor names]
[Insert metric]
[Insert source]
[Insert implication]
```

### Design Style

- Professional consulting style
- Clean layout
- Strong grid alignment
- Clear hierarchy
- Minimal colors
- Board-ready
- No copyrighted firm branding
- Default font: Aptos
- 16:9 widescreen

### Core Templates to Generate

```yaml
pptx_templates:
  - executive_summary
  - market_attractiveness
  - competitor_benchmark
  - competitor_landscape
  - industry_trend_analysis
  - opportunity_challenge_analysis
  - m_and_a_rationale
  - joint_venture_rationale
  - valuation_comparison
  - strategic_fit_assessment
  - options_evaluation
  - roadmap
  - implementation_plan
  - risk_assessment
  - recommendation_slide
```

---

## 13. Quality Scoring Criteria

Each slide should be scored from 0 to 100.

```yaml
quality_criteria:
  message_clarity:
    weight: 25
    description: "Does the slide communicate a clear insight?"
  layout_clarity:
    weight: 20
    description: "Is the visual hierarchy easy to follow?"
  chart_appropriateness:
    weight: 15
    description: "Is the selected chart suitable for the message?"
  executive_readability:
    weight: 20
    description: "Can a board or executive audience understand it quickly?"
  reusability:
    weight: 20
    description: "Can this structure be reused for other business topics?"
```

---

## 14. Coding Instructions for Codex

Build the MVP in stages. Do not attempt all features at once.

### Stage 1 — Project Setup

1. Create the project folder structure.
2. Add `requirements.txt`.
3. Add `.env.example`.
4. Add a CLI entry point at `src/main.py`.
5. Add logging utilities.

### Stage 2 — Deck Ingestion

1. Implement PDF-to-image conversion.
2. Implement PPTX-to-image conversion.
3. Implement PDF text extraction.
4. Implement PPTX text extraction.
5. Save output per slide.

### Stage 3 — Database Setup

1. Create SQLite database.
2. Create tables for decks, slides, tags, and embeddings.
3. Insert basic slide records after ingestion.

### Stage 4 — Slide Classification

1. Implement LLM classification function.
2. Use the classification prompt in this file.
3. Save JSON classification result per slide.
4. Update database records.

### Stage 5 — Search and Recommendation

1. Implement text embedding.
2. Build a local vector search index.
3. Implement similar slide search.
4. Implement recommendation prompt.
5. Return structured recommendation JSON.

### Stage 6 — PowerPoint Template Generation

1. Generate placeholder slides using python-pptx.
2. Support at least 5 template types first:
   - executive_summary
   - competitor_benchmark
   - market_attractiveness
   - opportunity_challenge_analysis
   - roadmap
3. Add more templates after MVP works.

### Stage 7 — Testing

1. Add unit tests for each module.
2. Test with 3 PDF decks and 3 PPTX decks.
3. Validate output JSON.
4. Validate generated PPTX opens correctly.

---

## 15. MVP Acceptance Criteria

The MVP is complete when:

1. User can place a PDF/PPTX deck into `input_decks/`.
2. User can run one command to ingest the deck.
3. Each slide is exported as an image.
4. Each slide has extracted text.
5. Each slide is classified into slide type, chart type, storyline type, and audience type.
6. Metadata is saved in SQLite.
7. User can enter a new slide brief.
8. System recommends a slide structure.
9. System can generate at least one placeholder PPTX slide.
10. The output is reusable for consulting and corporate strategy slides.

---

## 16. Example User Briefs for Testing

Use these as test cases:

```text
Compare EWA competitors in Malaysia and identify market opportunity for OSK.
```

```text
Create a board-ready slide explaining the strategic rationale for acquiring a fintech platform.
```

```text
Summarize key trends, opportunities, and challenges in the Malaysian data centre industry.
```

```text
Evaluate whether a joint venture with a regional logistics player is strategically attractive.
```

```text
Create an executive summary for a corporate strategy workshop on new growth opportunities.
```

```text
Compare market valuation multiples across listed peers and identify valuation gaps.
```

---

## 17. Important Design Principles

1. Do not copy copyrighted slide designs.
2. Extract reusable structure, not proprietary content.
3. Prioritize storyline and decision usefulness over aesthetics.
4. Generate placeholder templates first, not fully designed slides.
5. Keep the system modular.
6. Build with small test decks before scaling.
7. Store every slide as image + text + classification JSON.
8. Use LLM classification before attempting custom ML.
9. Add ML model training only after collecting enough labeled examples.
10. Design outputs for board, CEO, ExCo, HOD, and corporate strategy users.

---

## 18. Future Enhancements

After the MVP works, add:

1. Web app interface
2. Slide screenshot search
3. Drag-and-drop deck upload
4. Visual similarity search
5. Slide quality scoring dashboard
6. Automatic action-title improvement
7. Corporate strategy storyline generator
8. Chart recommendation engine
9. PowerPoint add-in
10. Fine-tuned classifier after 1,000+ labeled slides
11. Supabase / pgvector backend
12. User feedback loop for improving recommendations

---

## 19. First Command Codex Should Implement

Start with this command:

```bash
python src/main.py ingest --file input_decks/pdf/sample.pdf
```

It should:

1. Create output folders if missing.
2. Convert the PDF into slide images.
3. Extract text from each slide.
4. Save one JSON metadata file per slide.
5. Register the deck and slides in SQLite.
6. Print a summary of processed slides.

---

## 20. Definition of Done for First Working Prototype

The first working prototype is done when this flow works:

```bash
python src/main.py ingest --file input_decks/pdf/sample.pdf
python src/main.py classify --deck sample
python src/main.py recommend --brief "Create a competitor benchmarking slide for Malaysia EWA companies"
python src/main.py generate-pptx --brief "Create a market opportunity slide for EWA in Malaysia"
```

Expected outputs:

```text
output/slide_images/
output/extracted_text/
output/classified_slides/
output/recommendations/
output/generated_templates/
data/slide_library.sqlite
```
