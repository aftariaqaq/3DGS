import shutil
import uuid
from pathlib import Path

from app.services import scene_store, storage, supersplat_converter


def _new_scene_id() -> str:
    return f"scene_{uuid.uuid4().hex[:12]}"


def convert_if_needed(source_ply: Path, target_dir: Path, log_path: Path) -> tuple[str, Path, Path]:
    source_copy = target_dir / "source.ply"
    shutil.copy2(source_ply, source_copy)
    target_path = supersplat_converter.convert_to_supersplat(source_copy, target_dir, log_path)
    return "sog", target_path, source_copy


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
    model_type, model_path, source_copy = convert_if_needed(
        source_ply,
        storage.scene_dir(scene_id),
        storage.job_logs_dir(job_id) / "supersplat-convert.log",
    )
    model_url = f"/static/scenes/{scene_id}/{model_path.name}"
    source_model_url = f"/static/scenes/{scene_id}/{source_copy.name}"
    stats = {
        "model_size_bytes": model_path.stat().st_size,
        "source_model_size_bytes": source_copy.stat().st_size,
    }
    if frame_count is not None:
        stats["frame_count"] = frame_count

    return scene_store.create_scene(
        scene_id=scene_id,
        job_id=job_id,
        model_type=model_type,
        model_url=model_url,
        source_model_url=source_model_url,
        viewer_url=f"/scenes/{scene_id}/supersplat",
        fallback_viewer_url=f"/scenes/{scene_id}/viewer",
        supersplat_viewer_url=f"/static/scenes/{scene_id}/supersplat.html",
        stats=stats,
    )
