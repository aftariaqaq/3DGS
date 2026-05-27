import shutil
import uuid
from pathlib import Path

from app.services import scene_store, storage


def _new_scene_id() -> str:
    return f"scene_{uuid.uuid4().hex[:12]}"


def convert_if_needed(source_ply: Path, target_dir: Path) -> tuple[str, Path]:
    target_path = target_dir / "scene.ply"
    shutil.copy2(source_ply, target_path)
    return "ply", target_path


def export_scene(
    job_id: str,
    scene_id: str | None = None,
    frame_count: int | None = None,
) -> dict:
    scene_id = scene_id or _new_scene_id()
    source_ply = storage.job_splatfacto_export_dir(job_id) / "splat.ply"
    if not source_ply.exists():
        candidates = sorted(storage.job_splatfacto_export_dir(job_id).glob("*.ply"))
        source_ply = candidates[0] if candidates else source_ply
    if not source_ply.exists():
        raise RuntimeError(f"Splatfacto output not found: {source_ply}")

    storage.ensure_scene_dir(scene_id)
    model_type, model_path = convert_if_needed(source_ply, storage.scene_dir(scene_id))
    model_url = f"/static/scenes/{scene_id}/{model_path.name}"
    stats = {
        "model_size_bytes": model_path.stat().st_size,
    }
    if frame_count is not None:
        stats["frame_count"] = frame_count

    return scene_store.create_scene(
        scene_id=scene_id,
        job_id=job_id,
        model_type=model_type,
        model_url=model_url,
        stats=stats,
    )
