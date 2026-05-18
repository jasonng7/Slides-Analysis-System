CONTENT_FIRST_SLIDE_PLAN_PROMPT = """
You are building a client-ready, board-ready presentation plan.

Use the Slide Strategy Consultant Skill exactly as the operating standard.

SLIDE STRATEGY CONSULTANT SKILL:
{{SKILL_TEXT}}

USER GOAL:
{{USER_GOAL}}

REQUESTED MODE:
{{REQUESTED_MODE}}

CONTENT SUFFICIENCY:
{{CONTENT_SUFFICIENCY_JSON}}

CONTENT ANALYSIS:
{{CONTENT_ANALYSIS_JSON}}

SOURCE CONTENT:
{{SOURCE_CONTENT}}

Create a source-grounded slide plan. Do not generate a generic long deck. The plan should be as short as the source allows while still answering the user's goal.

Return valid JSON only using this structure:

{
  "deck_title": "",
  "audience": "",
  "output_mode": "",
  "strategy_summary": "",
  "source_grounding_policy": "",
  "content_sufficiency_score": 0,
  "content_sufficiency_level": "",
  "recommended_slide_count": 0,
  "template_strategy": "",
  "slides": [
    {
      "slide_number": 1,
      "slide_title": "",
      "slide_type": "",
      "chart_type": "",
      "storyline_type": "",
      "slide_objective": "",
      "key_message": "",
      "source_evidence": [],
      "content_blocks": [
        {
          "heading": "",
          "body": "",
          "evidence": ""
        }
      ],
      "data_points": [],
      "visual_approach": "",
      "layout_preference": "",
      "template_match_query": "",
      "use_template_if_relevant": true,
      "missing_data_or_assumptions": [],
      "speaker_notes": "",
      "quality_checks": []
    }
  ],
  "source_grounding_report": [
    {
      "slide_number": 1,
      "source_basis": "",
      "unsupported_items": []
    }
  ],
  "global_missing_data": [],
  "generation_warnings": []
}

Rules:
- Stay strictly grounded in source content.
- If source evidence is thin, generate fewer slides.
- For board-ready decks, target 8 to 12 content slides only when source content supports it.
- If the source is narrow, use 3 to 6 content slides.
- Never invent numbers, companies, competitor names, segment sizes, or financials.
- Each slide must include source_evidence or a clearly stated missing_data_or_assumptions item.
- action titles should be insight-led, but only when source evidence supports the claim.
- Use taxonomy-like slide_type/chart_type values where practical.
- template_match_query must be specific to that slide, not the whole deck.
""".strip()
