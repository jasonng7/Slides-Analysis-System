from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from classification.classify_slide import MissingOpenAIAPIKeyError
from config import OUTPUT_DIRECTORIES
from content.analyze_content import analyze_content
from content.content_repository import save_content_recommendation_record
from content.content_schema import validate_recommendation
from recommendation.generate_slide_prompt import generate_prompt_from_recommendation
from recommendation.match_slide_patterns import find_relevant_slide_patterns
from recommendation.prompts import RECOMMENDATION_JSON_SCHEMA, RECOMMEND_FROM_CONTENT_PROMPT
from utils.file_utils import ensure_project_directories, slugify
from utils.json_utils import write_json


class InvalidRecommendationResponse(ValueError):
    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


def recommend_from_content(
    file_path: str | None = None,
    text: str | None = None,
    user_goal: str | None = None,
    mode: str = "auto",
    prompt_output: bool = False,
) -> dict[str, Any]:
    ensure_project_directories()
    content_analysis = analyze_content(
        file_path=file_path,
        text=text,
        user_goal=user_goal,
        mode=mode,
    )
    patterns = find_relevant_slide_patterns(content_analysis, user_goal)

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIAPIKeyError(
            "OPENAI_API_KEY is missing. Add it to .env before running recommendation."
        )

    client = OpenAI(api_key=api_key)
    raw_response = _run_recommendation(
        client=client,
        content_analysis=content_analysis,
        slide_patterns=patterns,
        user_goal=user_goal,
        mode=mode,
    )

    try:
        recommendation = validate_recommendation(json.loads(raw_response))
    except Exception as exc:
        error_path = _save_error(content_analysis["source_name"], content_analysis["timestamp"], raw_response)
        raise InvalidRecommendationResponse(
            f"{exc}. Raw response saved to {error_path}",
            raw_response,
        ) from exc

    recommendation["content_source_id"] = content_analysis["content_source_id"]
    recommendation["content_analysis_json_path"] = content_analysis["analysis_json_path"]
    recommendation["user_goal"] = user_goal or ""
    recommendation["requested_mode"] = mode
    recommendation["similar_slide_patterns_found"] = patterns
    recommendation["matching_method"] = (
        patterns[0].get("matching_method", "metadata_match") if patterns else "metadata_match"
    )

    json_path = _recommendation_path(content_analysis["source_name"], content_analysis["timestamp"])
    recommendation["recommendation_json_path"] = str(json_path)
    write_json(json_path, recommendation)

    txt_path = None
    if prompt_output:
        prompt_text = generate_prompt_from_recommendation(recommendation)
        txt_path = json_path.with_suffix(".txt")
        txt_path.write_text(prompt_text + "\n", encoding="utf-8")
        recommendation["prompt_txt_path"] = str(txt_path)
        write_json(json_path, recommendation)

    save_content_recommendation_record(
        content_source_id=content_analysis["content_source_id"],
        recommendation_json_path=str(json_path),
        recommendation_txt_path=str(txt_path) if txt_path else None,
        output_mode=recommendation.get("recommended_output_mode", mode),
        recommended_slide_type=recommendation.get("recommended_slide_structure", {}).get(
            "recommended_slide_type"
        ),
        recommended_deck_sections=_deck_sections_text(recommendation),
    )

    return recommendation


def _run_recommendation(
    *,
    client: OpenAI,
    content_analysis: dict[str, Any],
    slide_patterns: list[dict[str, Any]],
    user_goal: str | None,
    mode: str,
) -> str:
    prompt = (
        RECOMMEND_FROM_CONTENT_PROMPT.replace("{{USER_GOAL}}", user_goal or "Not provided")
        .replace("{{REQUESTED_MODE}}", mode)
        .replace("{{CONTENT_ANALYSIS_JSON}}", json.dumps(content_analysis, indent=2))
        .replace("{{RELEVANT_SLIDE_PATTERNS}}", json.dumps(slide_patterns, indent=2))
    )
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL") or "gpt-5.5",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "content_recommendation",
                "schema": RECOMMENDATION_JSON_SCHEMA,
                "strict": True,
            }
        },
    )
    return _response_text(response)


def _recommendation_path(source_name: str, timestamp: str) -> Path:
    output_dir = OUTPUT_DIRECTORIES["recommendations"]
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"recommendation_{slugify(source_name)}_{timestamp}.json"


def _save_error(source_name: str, timestamp: str, raw_response: str) -> Path:
    error_dir = OUTPUT_DIRECTORIES["recommendation_errors"]
    error_dir.mkdir(parents=True, exist_ok=True)
    path = error_dir / f"recommendation_{slugify(source_name)}_{timestamp}_raw.txt"
    path.write_text(raw_response, encoding="utf-8")
    return path


def _deck_sections_text(recommendation: dict[str, Any]) -> str:
    sections = recommendation.get("recommended_deck_structure", {}).get("sections", [])
    if not isinstance(sections, list):
        return ""
    return "; ".join(str(section.get("section_name", "")) for section in sections if section)


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
