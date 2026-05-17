from __future__ import annotations

import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from api.job_store import UPLOADS_DIR, create_job, load_job, public_job, save_job, update_job
from config import OUTPUT_DIRECTORIES, SUPPORTED_CONTENT_EXTENSIONS
from database.repository import get_classification_summary, get_database_summary
from embeddings.embedding_repository import get_embedding_summary
from pptx_generation.editable_reference_deck_generator import (
    generate_editable_reference_deck_from_file,
    generate_editable_reference_deck_from_text,
)
from quality_control.generated_deck_qa import review_generated_deck
from quality_control.qa_repository import find_matching_metadata_for_deck, find_matching_notes_for_deck
from utils.file_utils import slugify

load_dotenv()

app = FastAPI(
    title="Slide Analysis System API",
    version="0.1.0",
    description="Temporary EC2 API for generating editable reference-slide PowerPoint drafts.",
)

_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGIN", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_executor = ThreadPoolExecutor(max_workers=int(os.getenv("SLIDE_API_WORKERS", "1")))


class TextGenerationRequest(BaseModel):
    text: str = Field(min_length=20)
    goal: str | None = None
    mode: Literal["slide", "deck", "audit", "classify", "auto"] = "deck"


def _summary_payload() -> dict:
    db = get_database_summary()
    classification = get_classification_summary()
    embeddings = get_embedding_summary()
    return {
        "status": "ok",
        "deck_count": db.deck_count,
        "slide_count": db.slide_count,
        "classified_slides": classification.classified_slides,
        "unclassified_slides": classification.unclassified_slides,
        "slides_with_text_embeddings": embeddings.slides_with_text_embeddings,
        "slides_without_text_embeddings": embeddings.slides_without_text_embeddings,
        "embedding_model": embeddings.embedding_model or "n/a",
        "temporary_storage": "ec2_local_files",
        "cleanup_policy": "generated artifacts older than 15 minutes are deleted by systemd timer",
    }


@app.get("/api/health")
def health() -> dict:
    return _summary_payload()


@app.post("/api/jobs/text")
def create_text_job(request: TextGenerationRequest) -> dict:
    job = create_job(input_type="text", goal=request.goal, mode=request.mode, source_name="pasted_text")
    _executor.submit(_run_text_job, job["job_id"], request.text, request.goal, request.mode)
    return public_job(job)


@app.post("/api/jobs/file")
def create_file_job(
    file: UploadFile = File(...),
    goal: str | None = Form(default=None),
    mode: Literal["slide", "deck", "audit", "classify", "auto"] = Form(default="deck"),
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_CONTENT_EXTENSIONS - {".xlsx"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Use PDF, PPTX, DOCX, TXT, MD, or CSV for this MVP.",
        )

    job = create_job(input_type="file", goal=goal, mode=mode, source_name=file.filename or "uploaded_file")
    safe_name = f"{job['job_id']}_{slugify(Path(file.filename or 'uploaded_file').stem)}{suffix}"
    upload_path = UPLOADS_DIR / safe_name
    with upload_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    job["uploaded_file_path"] = str(upload_path)
    save_job(job)

    _executor.submit(_run_file_job, job["job_id"], str(upload_path), goal, mode)
    return public_job(job)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = load_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return public_job(job)


@app.get("/api/jobs/{job_id}/download")
def download_job_output(job_id: str) -> FileResponse:
    job = load_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "succeeded":
        raise HTTPException(status_code=409, detail="Job has not completed successfully")

    output_path = Path((job.get("result") or {}).get("output_path", ""))
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Generated deck expired or is missing")

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=output_path.name,
    )


def _run_text_job(job_id: str, text: str, goal: str | None, mode: str) -> None:
    output_path = OUTPUT_DIRECTORIES["generated_decks"] / f"{job_id}_editable_reference.pptx"
    _run_generation_job(
        job_id,
        lambda: generate_editable_reference_deck_from_text(
            text=text,
            goal=goal,
            mode=mode,
            output_path=output_path,
        ),
    )


def _run_file_job(job_id: str, file_path: str, goal: str | None, mode: str) -> None:
    output_path = OUTPUT_DIRECTORIES["generated_decks"] / f"{job_id}_editable_reference.pptx"
    _run_generation_job(
        job_id,
        lambda: generate_editable_reference_deck_from_file(
            file_path=file_path,
            goal=goal,
            mode=mode,
            output_path=output_path,
        ),
    )


def _run_generation_job(job_id: str, generator) -> None:
    try:
        update_job(job_id, status="running", error=None)
        metadata = generator()
        output_path = Path(metadata["output_path"])
        qa = review_generated_deck(
            output_path,
            metadata_path=find_matching_metadata_for_deck(output_path),
            notes_path=find_matching_notes_for_deck(output_path),
        )
        update_job(
            job_id,
            status="succeeded",
            result={
                "output_path": str(output_path),
                "metadata_path": metadata.get("metadata_path"),
                "speaker_notes_path": metadata.get("speaker_notes_path"),
                "matching_method": metadata.get("matching_method"),
                "number_of_slides": metadata.get("number_of_slides"),
                "number_of_content_slides": metadata.get("number_of_content_slides"),
                "cloned_slide_count": metadata.get("content_slides_cloned_from_source_pptx"),
                "image_fallback_count": metadata.get("content_slides_with_image_fallback"),
                "qa_score": qa.get("overall_score"),
                "qa_rating": qa.get("rating"),
                "qa_summary": qa.get("summary", {}),
                "qa_top_issues": qa.get("issues", [])[:8],
            },
        )
    except Exception as exc:
        update_job(job_id, status="failed", error=str(exc))
