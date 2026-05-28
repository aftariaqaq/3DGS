from app.models import JobStatus
from app.services import (
    colmap_runner,
    job_store,
    model_exporter,
    splatfacto_runner,
    video_pipeline,
)


def _run_stage(job_id: str, status: JobStatus, stage: str, action):
    job_store.update_status(job_id, status, stage=stage)
    try:
        return action()
    except Exception as exc:
        job_store.mark_failed(job_id, status, str(exc))
        raise


def run_job(job_id: str) -> None:
    job = job_store.read_job(job_id)
    frame_count = 0

    try:
        frame_count = _run_stage(
            job_id,
            JobStatus.EXTRACTING_FRAMES,
            "Processing video and selecting keyframes",
            lambda: video_pipeline.process_job_video(job_id, job["fps"], job["max_frames"]),
        )
        _run_stage(
            job_id,
            JobStatus.COLMAP_FEATURES,
            "COLMAP feature extraction",
            lambda: colmap_runner.run_feature_extractor(job_id),
        )
        _run_stage(
            job_id,
            JobStatus.COLMAP_MATCHING,
            "COLMAP sequential matching",
            lambda: colmap_runner.run_sequential_matcher(job_id),
        )
        _run_stage(
            job_id,
            JobStatus.COLMAP_MAPPING,
            "COLMAP mapping",
            lambda: colmap_runner.run_mapper(job_id),
        )
        _run_stage(
            job_id,
            JobStatus.TRAINING_SPLAT,
            "Splatfacto training",
            lambda: splatfacto_runner.run_splatfacto(job_id, job["iterations"]),
        )
        scene = _run_stage(
            job_id,
            JobStatus.EXPORTING_MODEL,
            "Exporting model",
            lambda: model_exporter.export_scene(job_id, scene_id=f"scene_{job_id}", frame_count=frame_count),
        )
        job_store.mark_ready(job_id, scene["id"], scene["model_url"])
    except Exception:
        return
