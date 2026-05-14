from classification.taxonomy import (
    ACTION_TITLE_QUALITY_VALUES,
    AUDIENCE_TYPE_VALUES,
    CHART_TYPE_VALUES,
    SLIDE_TYPE_VALUES,
    STORYLINE_TYPE_VALUES,
)


CLASSIFICATION_PROMPT = """
You are a senior strategy consultant and presentation design expert.

Analyze the provided slide image and extracted text. Your job is to classify the slide into reusable consulting and corporate strategy patterns.

Do not copy the slide. Do not reproduce proprietary wording. Extract only generic structure, storyline, communication logic, and layout patterns.

Return valid JSON only.

Classify the slide using the following fields:

{
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
  "quality_score": 0
}

Rules:
- Use only allowed taxonomy values where applicable.
- quality_score must be a number from 0 to 100.
- content_blocks must describe the major slide sections.
- detected_objects should include visible objects such as title, subtitle, chart, table, icons, callout box, legend, source note, footnote, logo, section divider.
- tags should contain 5 to 10 searchable tags.
- reusable_template_instruction should explain how this slide structure can be reused for another business topic.
- If unsure, choose "other" or "unknown" rather than inventing new categories.
""".strip()


CLASSIFICATION_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "slide_title",
        "action_title_quality",
        "slide_type",
        "chart_type",
        "storyline_type",
        "audience_type",
        "business_context",
        "layout_pattern",
        "content_blocks",
        "detected_objects",
        "tags",
        "reusable_template_instruction",
        "recommended_use_cases",
        "quality_score",
    ],
    "properties": {
        "slide_title": {"type": "string"},
        "action_title_quality": {"type": "string", "enum": ACTION_TITLE_QUALITY_VALUES},
        "slide_type": {"type": "string", "enum": SLIDE_TYPE_VALUES},
        "chart_type": {"type": "string", "enum": CHART_TYPE_VALUES},
        "storyline_type": {"type": "string", "enum": STORYLINE_TYPE_VALUES},
        "audience_type": {"type": "string", "enum": AUDIENCE_TYPE_VALUES},
        "business_context": {"type": "string"},
        "layout_pattern": {"type": "string"},
        "content_blocks": {"type": "array", "items": {"type": "string"}},
        "detected_objects": {"type": "array", "items": {"type": "string"}},
        "tags": {
            "type": "array",
            "minItems": 5,
            "maxItems": 10,
            "items": {"type": "string"},
        },
        "reusable_template_instruction": {"type": "string"},
        "recommended_use_cases": {"type": "array", "items": {"type": "string"}},
        "quality_score": {"type": "number", "minimum": 0, "maximum": 100},
    },
}
