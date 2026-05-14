CONTENT_ANALYSIS_PROMPT = """
You are a senior corporate strategy consultant and presentation structuring expert.

Analyze the provided source content. The content may come from a PDF report, Word document, PowerPoint deck, CSV table, pasted text, or other business material.

Your job is not to create slides yet. Your job is to understand what the content contains and prepare it for slide or deck recommendation.

Separate clearly:
1. What the content says
2. How the content could be presented

Return valid JSON only.

User goal, if provided:
{{USER_GOAL}}

Source type:
{{SOURCE_TYPE}}

Source content:
{{SOURCE_CONTENT}}

Analyze the content and return this JSON:

{
  "content_summary": "",
  "document_type": "",
  "business_context": "",
  "primary_analysis_type": "",
  "secondary_analysis_types": [],
  "likely_audience": "",
  "recommended_output_mode": "",
  "key_topics": [],
  "key_entities": [],
  "metrics_detected": [],
  "time_periods_detected": [],
  "geographies_detected": [],
  "strategic_questions_answered": [],
  "strategic_questions_unanswered": [],
  "content_tags": [],
  "suitable_slide_types": [],
  "suitable_deck_sections": [],
  "missing_data_or_research_gaps": [],
  "data_quality_assessment": "",
  "presentation_implications": ""
}

Allowed document_type values:
- slide_deck
- report
- financial_statement
- article
- brochure
- spreadsheet
- raw_notes
- meeting_notes
- research_extract
- unknown

Allowed primary_analysis_type values:
- executive_summary
- market_research
- industry_research
- competitor_analysis
- valuation_analysis
- m_and_a_analysis
- joint_venture_analysis
- corporate_exercise
- business_case
- financial_analysis
- operating_model
- implementation_planning
- risk_analysis
- strategic_options
- recommendation
- unknown

Allowed likely_audience values:
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

Allowed recommended_output_mode values:
- slide
- deck
- audit
- classify
- auto

Rules:
- If the user specifies an audience or goal, use it.
- If not, infer likely_audience from the content.
- If the content is broad and has multiple sections, recommend "deck".
- If the content is narrow and focused on one message, recommend "slide".
- If the content is an existing deck and the user mode is audit, recommend "audit".
- If the content is an existing template or slide library and the user mode is classify, recommend "classify".
- Identify missing data needed to create a board-ready slide or deck.
- Identify entities such as companies, markets, products, customers, competitors, geographies, and financial metrics.
- suitable_slide_types should map to the existing slide taxonomy where possible.
- suitable_deck_sections should describe logical deck sections if the output should be a deck.
- Do not invent facts not found in the source content.
- If information is not provided, state that it is missing.
""".strip()


CHUNK_SUMMARY_PROMPT = """
You are summarizing one chunk of source material for later strategy slide/deck recommendation.
Return concise bullet-style notes as plain text.

User goal:
{{USER_GOAL}}

Source type:
{{SOURCE_TYPE}}

Chunk:
{{SOURCE_CONTENT}}
""".strip()


CONTENT_ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "content_summary",
        "document_type",
        "business_context",
        "primary_analysis_type",
        "secondary_analysis_types",
        "likely_audience",
        "recommended_output_mode",
        "key_topics",
        "key_entities",
        "metrics_detected",
        "time_periods_detected",
        "geographies_detected",
        "strategic_questions_answered",
        "strategic_questions_unanswered",
        "content_tags",
        "suitable_slide_types",
        "suitable_deck_sections",
        "missing_data_or_research_gaps",
        "data_quality_assessment",
        "presentation_implications",
    ],
    "properties": {
        "content_summary": {"type": "string"},
        "document_type": {
            "type": "string",
            "enum": [
                "slide_deck",
                "report",
                "financial_statement",
                "article",
                "brochure",
                "spreadsheet",
                "raw_notes",
                "meeting_notes",
                "research_extract",
                "unknown",
            ],
        },
        "business_context": {"type": "string"},
        "primary_analysis_type": {
            "type": "string",
            "enum": [
                "executive_summary",
                "market_research",
                "industry_research",
                "competitor_analysis",
                "valuation_analysis",
                "m_and_a_analysis",
                "joint_venture_analysis",
                "corporate_exercise",
                "business_case",
                "financial_analysis",
                "operating_model",
                "implementation_planning",
                "risk_analysis",
                "strategic_options",
                "recommendation",
                "unknown",
            ],
        },
        "secondary_analysis_types": {"type": "array", "items": {"type": "string"}},
        "likely_audience": {
            "type": "string",
            "enum": [
                "board_of_directors",
                "ceo",
                "executive_committee",
                "head_of_department",
                "corporate_strategy_team",
                "investment_committee",
                "project_steering_committee",
                "internal_management",
                "external_client",
                "general_business_audience",
                "unknown",
            ],
        },
        "recommended_output_mode": {
            "type": "string",
            "enum": ["slide", "deck", "audit", "classify", "auto"],
        },
        "key_topics": {"type": "array", "items": {"type": "string"}},
        "key_entities": {"type": "array", "items": {"type": "string"}},
        "metrics_detected": {"type": "array", "items": {"type": "string"}},
        "time_periods_detected": {"type": "array", "items": {"type": "string"}},
        "geographies_detected": {"type": "array", "items": {"type": "string"}},
        "strategic_questions_answered": {"type": "array", "items": {"type": "string"}},
        "strategic_questions_unanswered": {"type": "array", "items": {"type": "string"}},
        "content_tags": {"type": "array", "items": {"type": "string"}},
        "suitable_slide_types": {"type": "array", "items": {"type": "string"}},
        "suitable_deck_sections": {"type": "array", "items": {"type": "string"}},
        "missing_data_or_research_gaps": {"type": "array", "items": {"type": "string"}},
        "data_quality_assessment": {"type": "string"},
        "presentation_implications": {"type": "string"},
    },
}
