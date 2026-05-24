import json
from datetime import datetime, timezone
from typing import Any

from app.models import JobStatus
from app.services import storage


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_job(job: dict[str, Any]) -> dict[str, Any]:
    path = storage.job_json_path(job["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, indent=2), encoding="utf-8")
    return job


def create_job(job_id: str, fps: int, max_frames: int, iterations: int) -> dict[str, Any]:
    now = _now()
    job = {
        "id": job_id,
        "status": JobStatus.CREATED,
        "stage": "Created",
        "created_at": now,
        "updated_at": now,
        "fps": fps,
        "max_frames": max_frames,
        "iterations": iterations,
        "input_video": None,
        "frame_count": None,
        "scene_id": None,
        "result_model": None,
        "error_stage": None,
        "error_message": None,
    }
    return _write_job(job)


def read_job(job_id: str) -> dict[str, Any]:
    path = storage.job_json_path(job_id)
    return json.loads(path.read_text(encoding="utf-8"))


def update_job(job_id: str, **updates: Any) -> dict[str, Any]:
    job = read_job(job_id)
    job.update(updates)
    job["updated_at"] = _now()
    return _write_job(job)


def update_status(job_id: str, status: JobStatus, stage: str | None = None) -> dict[str, Any]:
    updates: dict[str, Any] = {"status": status}
    if stage is not None:
        updates["stage"] = stage
    return update_job(job_id, **updates)


def mark_failed(job_id: str, error_stage: str, error_message: str) -> dict[str, Any]:
    return update_job(
        job_id,
        status=JobStatus.FAILED,
        stage="Failed",
        error_stage=error_stage,
        error_message=error_message,
    )


def mark_ready(job_id: str, scene_id: str, result_model: str) -> dict[str, Any]:
    return update_job(
        job_id,
        status=JobStatus.READY,
        stage="Ready",
        scene_id=scene_id,
        result_model=result_model,
        error_stage=None,
        error_message=None,
    )

