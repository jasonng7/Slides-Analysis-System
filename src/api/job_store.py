from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import OUTPUT_DIR

JOBS_DIR = OUTPUT_DIR / "api_jobs"
UPLOADS_DIR = JOBS_DIR / "uploads"
JOB_RECORDS_DIR = JOBS_DIR / "records"

_LOCK = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_job_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    JOB_RECORDS_DIR.mkdir(parents=True, exist_ok=True)


def create_job(*, input_type: str, goal: str | None, mode: str, source_name: str | None = None) -> dict[str, Any]:
    ensure_job_dirs()
    job = {
        "job_id": uuid.uuid4().hex,
        "status": "queued",
        "input_type": input_type,
        "source_name": source_name or input_type,
        "goal": goal or "",
        "mode": mode,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "result": None,
        "error": None,
    }
    save_job(job)
    return job


def job_path(job_id: str) -> Path:
    return JOB_RECORDS_DIR / f"{job_id}.json"


def load_job(job_id: str) -> dict[str, Any] | None:
    ensure_job_dirs()
    path = job_path(job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_job(job: dict[str, Any]) -> None:
    ensure_job_dirs()
    job["updated_at"] = now_iso()
    path = job_path(str(job["job_id"]))
    with _LOCK:
        path.write_text(json.dumps(job, indent=2), encoding="utf-8")


def update_job(job_id: str, **updates: Any) -> dict[str, Any]:
    job = load_job(job_id)
    if job is None:
        raise KeyError(f"Job not found: {job_id}")
    job.update(updates)
    save_job(job)
    return job


def public_job(job: dict[str, Any], api_prefix: str = "/api") -> dict[str, Any]:
    output_path = (job.get("result") or {}).get("output_path") if isinstance(job.get("result"), dict) else None
    response = dict(job)
    if output_path and Path(output_path).exists() and job.get("status") == "succeeded":
        response["download_url"] = f"{api_prefix}/jobs/{job['job_id']}/download"
    else:
        response["download_url"] = None
    return response
