import json
from datetime import datetime, timezone
from typing import Any

from app.services import storage


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_scene(
    scene_id: str,
    job_id: str,
    model_type: str,
    model_url: str,
    stats: dict[str, Any] | None = None,
    source_model_url: str | None = None,
    viewer_url: str | None = None,
    fallback_viewer_url: str | None = None,
    supersplat_viewer_url: str | None = None,
) -> dict[str, Any]:
    storage.ensure_scene_dir(scene_id)
    scene = {
        "id": scene_id,
        "job_id": job_id,
        "name": scene_id,
        "model_type": model_type,
        "model_url": model_url,
        "created_at": _now(),
        "stats": stats or {},
    }
    if source_model_url is not None:
        scene["source_model_url"] = source_model_url
    if viewer_url is not None:
        scene["viewer_url"] = viewer_url
    if fallback_viewer_url is not None:
        scene["fallback_viewer_url"] = fallback_viewer_url
    if supersplat_viewer_url is not None:
        scene["supersplat_viewer_url"] = supersplat_viewer_url
    storage.scene_metadata_path(scene_id).write_text(json.dumps(scene, indent=2), encoding="utf-8")
    return scene


def read_scene(scene_id: str) -> dict[str, Any]:
    return json.loads(storage.scene_metadata_path(scene_id).read_text(encoding="utf-8"))


def list_scenes() -> list[dict[str, Any]]:
    if not storage.SCENES_DIR.exists():
        return []

    scenes = []
    for metadata_path in sorted(storage.SCENES_DIR.glob("*/metadata.json")):
        scenes.append(json.loads(metadata_path.read_text(encoding="utf-8")))
    return scenes
