from classification.taxonomy import (
    AUDIENCE_TYPE_VALUES,
    CHART_TYPE_VALUES,
    SLIDE_TYPE_VALUES,
    STORYLINE_TYPE_VALUES,
)


RECOMMEND_FROM_CONTENT_PROMPT = """
You are a senior corporate strategy consultant helping the user convert source content into a clear slide or deck structure.

The user may have uploaded a report, Word document, PowerPoint, PDF, CSV, notes, or pasted text. They may not know how to structure it into slides.

Use the content analysis, user goal, and relevant classified slide patterns from the local slide library to recommend the best presentation structure.

Separate clearly:
1. What the content says
2. How to present it
3. What is missing

User goal:
{{USER_GOAL}}

Requested output mode:
{{REQUESTED_MODE}}

Content analysis:
{{CONTENT_ANALYSIS_JSON}}

Relevant classified slide patterns from local slide library:
{{RELEVANT_SLIDE_PATTERNS}}

Return valid JSON only.

Return this JSON:

{
  "recommendation_type": "",
  "brief_interpretation": "",
  "content_diagnosis": "",
  "recommended_output_mode": "",
  "recommended_audience_type": "",
  "recommended_slide_or_deck_title": "",
  "recommended_storyline": "",
  "recommended_slide_structure": {
    "recommended_slide_type": "",
    "recommended_chart_type": "",
    "recommended_storyline_type": "",
    "suggested_action_title": "",
    "layout_instruction": "",
    "content_blocks": [],
    "data_required": [],
    "analysis_required": [],
    "missing_data_or_research_gaps": [],
    "powerpoint_template_instruction": "",
    "quality_checklist": []
  },
  "recommended_deck_structure": {
    "suggested_deck_title": "",
    "sections": [
      {
        "section_name": "",
        "section_purpose": "",
        "recommended_slides": [
          {
            "slide_title": "",
            "slide_type": "",
            "chart_type": "",
            "storyline_type": "",
            "content_to_use_from_source": "",
            "additional_data_needed": "",
            "template_instruction": ""
          }
        ]
      }
    ]
  },
  "similar_slide_patterns_used": [],
  "alternative_structures": [],
  "next_steps_for_user": []
}

Rules:
- If requested_output_mode is "slide", prioritize recommended_slide_structure.
- If requested_output_mode is "deck", prioritize recommended_deck_structure.
- If requested_output_mode is "auto", decide whether slide or deck is more suitable based on content breadth.
- If requested_output_mode is "audit", focus on how the existing deck/content should be improved.
- If requested_output_mode is "classify", suggest how it should be added to the slide library.
- For corporate strategy topics, prioritize:
  - executive_summary
  - board_decision_paper
  - industry_overview
  - industry_trend_analysis
  - competitor_landscape
  - competitor_benchmark
  - valuation_comparison
  - merger_acquisition_rationale
  - joint_venture_rationale
  - investment_thesis
  - strategic_fit_assessment
  - opportunity_challenge_analysis
  - business_case_summary
  - decision_matrix
  - roadmap
  - implementation_plan
  - risk_assessment
- The suggested action title must be insight-led, not a topic title.
- Recommend practical content blocks, not vague advice.
- If the source content does not contain enough evidence, state what is missing.
- Do not invent numbers, companies, sources, or facts.
- Use relevant classified slide patterns as inspiration for structure only, not as copied content.
""".strip()


RECOMMENDATION_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "recommendation_type",
        "brief_interpretation",
        "content_diagnosis",
        "recommended_output_mode",
        "recommended_audience_type",
        "recommended_slide_or_deck_title",
        "recommended_storyline",
        "recommended_slide_structure",
        "recommended_deck_structure",
        "similar_slide_patterns_used",
        "alternative_structures",
        "next_steps_for_user",
    ],
    "properties": {
        "recommendation_type": {"type": "string"},
        "brief_interpretation": {"type": "string"},
        "content_diagnosis": {"type": "string"},
        "recommended_output_mode": {
            "type": "string",
            "enum": ["slide", "deck", "audit", "classify", "auto"],
        },
        "recommended_audience_type": {"type": "string", "enum": AUDIENCE_TYPE_VALUES},
        "recommended_slide_or_deck_title": {"type": "string"},
        "recommended_storyline": {"type": "string"},
        "recommended_slide_structure": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "recommended_slide_type",
                "recommended_chart_type",
                "recommended_storyline_type",
                "suggested_action_title",
                "layout_instruction",
                "content_blocks",
                "data_required",
                "analysis_required",
                "missing_data_or_research_gaps",
                "powerpoint_template_instruction",
                "quality_checklist",
            ],
            "properties": {
                "recommended_slide_type": {"type": "string", "enum": SLIDE_TYPE_VALUES},
                "recommended_chart_type": {"type": "string", "enum": CHART_TYPE_VALUES},
                "recommended_storyline_type": {"type": "string", "enum": STORYLINE_TYPE_VALUES},
                "suggested_action_title": {"type": "string"},
                "layout_instruction": {"type": "string"},
                "content_blocks": {"type": "array", "items": {"type": "string"}},
                "data_required": {"type": "array", "items": {"type": "string"}},
                "analysis_required": {"type": "array", "items": {"type": "string"}},
                "missing_data_or_research_gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "powerpoint_template_instruction": {"type": "string"},
                "quality_checklist": {"type": "array", "items": {"type": "string"}},
            },
        },
        "recommended_deck_structure": {
            "type": "object",
            "additionalProperties": False,
            "required": ["suggested_deck_title", "sections"],
            "properties": {
                "suggested_deck_title": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "section_name",
                            "section_purpose",
                            "recommended_slides",
                        ],
                        "properties": {
                            "section_name": {"type": "string"},
                            "section_purpose": {"type": "string"},
                            "recommended_slides": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": [
                                        "slide_title",
                                        "slide_type",
                                        "chart_type",
                                        "storyline_type",
                                        "content_to_use_from_source",
                                        "additional_data_needed",
                                        "template_instruction",
                                    ],
                                    "properties": {
                                        "slide_title": {"type": "string"},
                                        "slide_type": {"type": "string", "enum": SLIDE_TYPE_VALUES},
                                        "chart_type": {"type": "string", "enum": CHART_TYPE_VALUES},
                                        "storyline_type": {"type": "string", "enum": STORYLINE_TYPE_VALUES},
                                        "content_to_use_from_source": {"type": "string"},
                                        "additional_data_needed": {"type": "string"},
                                        "template_instruction": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "similar_slide_patterns_used": {"type": "array", "items": {"type": "string"}},
        "alternative_structures": {"type": "array", "items": {"type": "string"}},
        "next_steps_for_user": {"type": "array", "items": {"type": "string"}},
    },
}
