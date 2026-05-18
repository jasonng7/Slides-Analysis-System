from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from classification.classify_slide import MissingOpenAIAPIKeyError
from content.analyze_content import _response_text
from content.content_sufficiency import score_content_sufficiency
from skills.skill_loader import load_skill_text
from slide_planning.prompts import CONTENT_FIRST_SLIDE_PLAN_PROMPT
from slide_planning.slide_plan_repository import save_raw_plan_error, save_slide_plan
from slide_planning.slide_plan_schema import SLIDE_PLAN_JSON_SCHEMA, validate_slide_plan


class InvalidSlidePlanResponse(ValueError):
    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


def generate_slide_plan(
    *,
    content_analysis: dict[str, Any],
    user_goal: str | None,
    mode: str = "deck",
    source_text: str | None = None,
) -> dict[str, Any]:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIAPIKeyError(
            "OPENAI_API_KEY is missing. Add it to .env before running content-first slide planning."
        )

    raw_text = source_text if source_text is not None else _read_source_text(content_analysis)
    sufficiency = score_content_sufficiency(content_analysis, raw_text)
    client = OpenAI(api_key=api_key)
    raw_response = _run_slide_plan(
        client=client,
        content_analysis=content_analysis,
        user_goal=user_goal,
        mode=mode,
        source_text=raw_text,
        sufficiency=sufficiency,
    )

    try:
        plan = validate_slide_plan(json.loads(raw_response))
    except Exception as exc:
        error_path = save_raw_plan_error(
            raw_response,
            str(content_analysis.get("source_name") or "source"),
            str(content_analysis.get("timestamp") or "unknown"),
        )
        raise InvalidSlidePlanResponse(f"{exc}. Raw response saved to {error_path}", raw_response) from exc

    plan["user_goal"] = user_goal or ""
    plan["requested_mode"] = mode
    plan["content_source_id"] = content_analysis.get("content_source_id")
    plan["content_analysis_json_path"] = content_analysis.get("analysis_json_path")
    plan["raw_text_path"] = content_analysis.get("raw_text_path")
    plan["content_sufficiency"] = sufficiency
    plan_path = save_slide_plan(
        plan,
        str(content_analysis.get("source_name") or "source"),
        str(content_analysis.get("timestamp") or "unknown"),
    )
    plan["slide_plan_json_path"] = str(plan_path)
    save_slide_plan(
        plan,
        str(content_analysis.get("source_name") or "source"),
        str(content_analysis.get("timestamp") or "unknown"),
    )
    return plan


def _run_slide_plan(
    *,
    client: OpenAI,
    content_analysis: dict[str, Any],
    user_goal: str | None,
    mode: str,
    source_text: str,
    sufficiency: dict[str, Any],
) -> str:
    prompt = (
        CONTENT_FIRST_SLIDE_PLAN_PROMPT.replace("{{SKILL_TEXT}}", load_skill_text())
        .replace("{{USER_GOAL}}", user_goal or "Not provided")
        .replace("{{REQUESTED_MODE}}", mode)
        .replace("{{CONTENT_SUFFICIENCY_JSON}}", json.dumps(sufficiency, indent=2))
        .replace("{{CONTENT_ANALYSIS_JSON}}", json.dumps(content_analysis, indent=2))
        .replace("{{SOURCE_CONTENT}}", source_text[:60000])
    )
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL") or "gpt-5.5",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "content_first_slide_plan",
                "schema": SLIDE_PLAN_JSON_SCHEMA,
                "strict": True,
            }
        },
    )
    return _response_text(response)


def _read_source_text(content_analysis: dict[str, Any]) -> str:
    raw_path = content_analysis.get("raw_text_path")
    if raw_path:
        path = Path(str(raw_path))
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
    return str(content_analysis.get("content_summary") or "")
