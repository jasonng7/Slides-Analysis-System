from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from classification.classify_slide import MissingOpenAIAPIKeyError
from config import OUTPUT_DIRECTORIES
from content.chunk_content import chunk_text
from content.content_repository import register_content_analysis
from content.content_schema import validate_content_analysis
from content.extract_content import extract_content
from content.prompts import (
    CHUNK_SUMMARY_PROMPT,
    CONTENT_ANALYSIS_JSON_SCHEMA,
    CONTENT_ANALYSIS_PROMPT,
)
from utils.file_utils import ensure_project_directories, slugify
from utils.json_utils import write_json


class InvalidContentAnalysisResponse(ValueError):
    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


def analyze_content(
    file_path: str | None = None,
    text: str | None = None,
    user_goal: str | None = None,
    mode: str = "auto",
) -> dict[str, Any]:
    ensure_project_directories()
    source_info = extract_content(file_path=file_path, text=text)
    source_text = source_info["raw_text"]

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIAPIKeyError(
            "OPENAI_API_KEY is missing. Add it to .env before running content analysis."
        )

    client = OpenAI(api_key=api_key)
    chunks = chunk_text(source_text)
    _save_chunks(source_info["source_name"], source_info["timestamp"], chunks)

    if len(chunks) > 1:
        summarized_chunks = _summarize_chunks(
            client=client,
            chunks=chunks,
            source_type=source_info["source_type"],
            user_goal=user_goal,
            source_name=source_info["source_name"],
            timestamp=source_info["timestamp"],
        )
        analysis_source_text = "\n\n".join(summarized_chunks) or source_text[:12000]
    else:
        analysis_source_text = chunks[0] if chunks else ""

    raw_response = _run_content_analysis(
        client=client,
        source_content=analysis_source_text,
        source_type=source_info["source_type"],
        user_goal=user_goal,
        mode=mode,
    )

    try:
        analysis = validate_content_analysis(json.loads(raw_response))
    except Exception as exc:
        error_path = _save_error(source_info["source_name"], source_info["timestamp"], raw_response)
        raise InvalidContentAnalysisResponse(
            f"{exc}. Raw response saved to {error_path}",
            raw_response,
        ) from exc

    analysis_path = _analysis_path(source_info["source_name"], source_info["timestamp"])
    write_json(analysis_path, analysis)
    content_source_id = register_content_analysis(
        source_info=source_info,
        analysis=analysis,
        analysis_json_path=str(analysis_path),
        user_goal=user_goal,
    )
    result = {
        **analysis,
        "content_source_id": content_source_id,
        "source_name": source_info["source_name"],
        "source_type": source_info["source_type"],
        "source_file": source_info["source_file"],
        "raw_text_path": source_info["raw_text_path"],
        "analysis_json_path": str(analysis_path),
        "timestamp": source_info["timestamp"],
        "requested_mode": mode,
        "user_goal": user_goal,
    }
    write_json(analysis_path, result)
    return result


def _run_content_analysis(
    *,
    client: OpenAI,
    source_content: str,
    source_type: str,
    user_goal: str | None,
    mode: str,
) -> str:
    prompt = (
        CONTENT_ANALYSIS_PROMPT.replace("{{USER_GOAL}}", user_goal or "Not provided")
        .replace("{{SOURCE_TYPE}}", source_type)
        .replace(
            "{{SOURCE_CONTENT}}",
            f"Requested mode: {mode}\n\n{source_content[:40000]}",
        )
    )
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL") or "gpt-5.5",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "content_analysis",
                "schema": CONTENT_ANALYSIS_JSON_SCHEMA,
                "strict": True,
            }
        },
    )
    return _response_text(response)


def _summarize_chunks(
    *,
    client: OpenAI,
    chunks: list[str],
    source_type: str,
    user_goal: str | None,
    source_name: str,
    timestamp: str,
) -> list[str]:
    summaries: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        prompt = (
            CHUNK_SUMMARY_PROMPT.replace("{{USER_GOAL}}", user_goal or "Not provided")
            .replace("{{SOURCE_TYPE}}", source_type)
            .replace("{{SOURCE_CONTENT}}", chunk)
        )
        try:
            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL") or "gpt-5.5",
                input=prompt,
                max_output_tokens=1800,
            )
            summary = _response_text(response).strip()
            if summary:
                summaries.append(f"Chunk {index} summary:\n{summary}")
        except Exception as exc:
            error_path = _chunk_error_path(source_name, timestamp, index)
            error_path.write_text(str(exc), encoding="utf-8")
    return summaries


def _save_chunks(source_name: str, timestamp: str, chunks: list[str]) -> None:
    chunk_dir = OUTPUT_DIRECTORIES["content_chunks"]
    chunk_dir.mkdir(parents=True, exist_ok=True)
    source_slug = slugify(source_name)
    for index, chunk in enumerate(chunks, start=1):
        (chunk_dir / f"{source_slug}_{timestamp}_chunk_{index:03d}.txt").write_text(
            chunk,
            encoding="utf-8",
        )


def _analysis_path(source_name: str, timestamp: str) -> Path:
    output_dir = OUTPUT_DIRECTORIES["content_analysis_json"]
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{slugify(source_name)}_{timestamp}.json"


def _save_error(source_name: str, timestamp: str, raw_response: str) -> Path:
    error_dir = OUTPUT_DIRECTORIES["content_errors"]
    error_dir.mkdir(parents=True, exist_ok=True)
    error_path = error_dir / f"{slugify(source_name)}_{timestamp}_raw.txt"
    error_path.write_text(raw_response, encoding="utf-8")
    return error_path


def _chunk_error_path(source_name: str, timestamp: str, chunk_index: int) -> Path:
    error_dir = OUTPUT_DIRECTORIES["content_errors"]
    error_dir.mkdir(parents=True, exist_ok=True)
    return error_dir / f"{slugify(source_name)}_{timestamp}_chunk_{chunk_index:03d}.txt"


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
