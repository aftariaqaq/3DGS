from pathlib import Path

from app.models import JobStatus
from app.services import job_store, scene_store, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(storage, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(job_store.storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(job_store.storage, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(scene_store.storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(scene_store.storage, "SCENES_DIR", tmp_path / "scenes")


def test_ensure_job_dirs_creates_expected_layout(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)

    storage.ensure_job_dirs("job_001")

    for relative_path in [
        "input",
        "images",
        "colmap",
        "colmap/sparse",
        "nerfstudio",
        "nerfstudio/data",
        "nerfstudio/outputs",
        "nerfstudio/exports",
        "web",
        "logs",
    ]:
        assert (tmp_path / "jobs" / "job_001" / relative_path).is_dir()
    assert not (tmp_path / "jobs" / "job_001" / "opensplat").exists()


def test_job_store_lifecycle(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")

    created = job_store.create_job("job_001", fps=1, max_frames=50, iterations=300)

    assert created["id"] == "job_001"
    assert created["status"] == JobStatus.CREATED
    assert created["fps"] == 1
    assert created["max_frames"] == 50
    assert created["iterations"] == 300

    updated = job_store.update_status("job_001", JobStatus.EXTRACTING_FRAMES, stage="Extracting frames")

    assert updated["status"] == JobStatus.EXTRACTING_FRAMES
    assert updated["stage"] == "Extracting frames"
    assert job_store.read_job("job_001")["status"] == JobStatus.EXTRACTING_FRAMES

    failed = job_store.mark_failed("job_001", "COLMAP_FEATURES", "feature extraction failed")

    assert failed["status"] == JobStatus.FAILED
    assert failed["error_stage"] == "COLMAP_FEATURES"
    assert failed["error_message"] == "feature extraction failed"

    ready = job_store.mark_ready("job_001", "scene_001", "/static/scenes/scene_001/scene.ply")

    assert ready["status"] == JobStatus.READY
    assert ready["scene_id"] == "scene_001"
    assert ready["result_model"] == "/static/scenes/scene_001/scene.ply"


def test_scene_store_creates_reads_and_lists_metadata(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)

    first = scene_store.create_scene(
        scene_id="scene_001",
        job_id="job_001",
        model_type="ply",
        model_url="/static/scenes/scene_001/scene.ply",
        stats={"frame_count": 30, "model_size_bytes": 1234},
    )
    scene_store.create_scene(
        scene_id="scene_002",
        job_id="job_002",
        model_type="splat",
        model_url="/static/scenes/scene_002/scene.splat",
        stats={"frame_count": 10},
    )

    assert first["id"] == "scene_001"
    assert first["job_id"] == "job_001"
    assert first["model_type"] == "ply"
    assert scene_store.read_scene("scene_001")["model_url"] == "/static/scenes/scene_001/scene.ply"
    assert [scene["id"] for scene in scene_store.list_scenes()] == ["scene_001", "scene_002"]
