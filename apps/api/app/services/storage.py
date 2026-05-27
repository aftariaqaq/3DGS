from pathlib import Path

from app.config import JOBS_DIR, SCENES_DIR


def job_dir(job_id: str) -> Path:
    return JOBS_DIR / job_id


def job_input_dir(job_id: str) -> Path:
    return job_dir(job_id) / "input"


def job_images_dir(job_id: str) -> Path:
    return job_dir(job_id) / "images"


def job_colmap_dir(job_id: str) -> Path:
    return job_dir(job_id) / "colmap"


def job_nerfstudio_dir(job_id: str) -> Path:
    return job_dir(job_id) / "nerfstudio"


def job_nerfstudio_data_dir(job_id: str) -> Path:
    return job_nerfstudio_dir(job_id) / "data"


def job_nerfstudio_outputs_dir(job_id: str) -> Path:
    return job_nerfstudio_dir(job_id) / "outputs"


def job_splatfacto_export_dir(job_id: str) -> Path:
    return job_nerfstudio_dir(job_id) / "exports"


def job_web_dir(job_id: str) -> Path:
    return job_dir(job_id) / "web"


def job_logs_dir(job_id: str) -> Path:
    return job_dir(job_id) / "logs"


def job_json_path(job_id: str) -> Path:
    return job_dir(job_id) / "job.json"


def scene_dir(scene_id: str) -> Path:
    return SCENES_DIR / scene_id


def scene_metadata_path(scene_id: str) -> Path:
    return scene_dir(scene_id) / "metadata.json"


def ensure_job_dirs(job_id: str) -> None:
    for path in [
        job_input_dir(job_id),
        job_images_dir(job_id),
        job_colmap_dir(job_id),
        job_colmap_dir(job_id) / "sparse",
        job_nerfstudio_dir(job_id),
        job_nerfstudio_data_dir(job_id),
        job_nerfstudio_outputs_dir(job_id),
        job_splatfacto_export_dir(job_id),
        job_web_dir(job_id),
        job_logs_dir(job_id),
    ]:
        path.mkdir(parents=True, exist_ok=True)


def ensure_scene_dir(scene_id: str) -> None:
    scene_dir(scene_id).mkdir(parents=True, exist_ok=True)
