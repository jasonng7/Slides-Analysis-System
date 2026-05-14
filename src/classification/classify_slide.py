from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from classification.prompts import CLASSIFICATION_JSON_SCHEMA, CLASSIFICATION_PROMPT
from classification.taxonomy import clamp_quality_score, normalize_taxonomy_value


REQUIRED_FIELDS = [
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
]


class MissingOpenAIAPIKeyError(RuntimeError):
    pass


class InvalidClassificationResponse(ValueError):
    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


class SlideClassification(BaseModel):
    slide_title: str = ""
    action_title_quality: str = "unclear_title"
    slide_type: str = "other"
    chart_type: str = "unknown"
    storyline_type: str = "other"
    audience_type: str = "unknown"
    business_context: str = ""
    layout_pattern: str = ""
    content_blocks: list[str] = Field(default_factory=list)
    detected_objects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    reusable_template_instruction: str = ""
    recommended_use_cases: list[str] = Field(default_factory=list)
    quality_score: float = 0.0

    @field_validator(
        "action_title_quality",
        "slide_type",
        "chart_type",
        "storyline_type",
        "audience_type",
        mode="before",
    )
    @classmethod
    def _normalize_taxonomy(cls, value: object, info) -> str:
        return normalize_taxonomy_value(info.field_name, value)

    @field_validator("quality_score", mode="before")
    @classmethod
    def _clamp_score(cls, value: object) -> float:
        return clamp_quality_score(value)

    @field_validator("content_blocks", "detected_objects", "tags", "recommended_use_cases", mode="before")
    @classmethod
    def _normalize_string_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]


def validate_classification(payload: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Missing classification fields: {', '.join(missing)}")
    return SlideClassification.model_validate(payload).model_dump()


def classify_slide(slide_image_path: str, extracted_text_path: str) -> dict[str, Any]:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIAPIKeyError(
            "OPENAI_API_KEY is missing. Add it to .env before running classification."
        )

    image_path = Path(slide_image_path)
    text_path = Path(extracted_text_path)
    extracted_text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
    image_data_url = _image_data_url(image_path)
    model = os.getenv("OPENAI_MODEL") or "gpt-5.5"

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": CLASSIFICATION_PROMPT},
                    {
                        "type": "input_text",
                        "text": f"Extracted slide text:\n{extracted_text}",
                    },
                    {
                        "type": "input_image",
                        "image_url": image_data_url,
                        "detail": "high",
                    },
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "slide_classification",
                "schema": CLASSIFICATION_JSON_SCHEMA,
                "strict": True,
            }
        },
    )

    raw_output = _response_text(response)
    try:
        payload = json.loads(raw_output)
        return validate_classification(payload)
    except Exception as exc:
        raise InvalidClassificationResponse(str(exc), raw_output) from exc


def _image_data_url(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Slide image not found: {path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    return "\n".join(chunks).strip()
