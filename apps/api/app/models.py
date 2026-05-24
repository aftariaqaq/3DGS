from enum import StrEnum

from pydantic import BaseModel


class JobStatus(StrEnum):
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    EXTRACTING_FRAMES = "EXTRACTING_FRAMES"
    COLMAP_FEATURES = "COLMAP_FEATURES"
    COLMAP_MATCHING = "COLMAP_MATCHING"
    COLMAP_MAPPING = "COLMAP_MAPPING"
    TRAINING_SPLAT = "TRAINING_SPLAT"
    EXPORTING_MODEL = "EXPORTING_MODEL"
    READY = "READY"
    FAILED = "FAILED"


class UploadResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    stage: str | None = None
    scene_id: str | None = None
    error_stage: str | None = None
    error_message: str | None = None


class LogsResponse(BaseModel):
    job_id: str
    stage: str | None = None
    text: str


class SceneResponse(BaseModel):
    id: str
    job_id: str
    model_type: str
    model_url: str
