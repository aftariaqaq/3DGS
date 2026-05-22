from pathlib import Path

from app.models import JobStatus
from app.services import job_runner, job_store, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(storage, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(job_store.storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(job_store.storage, "SCENES_DIR", tmp_path / "scenes")


def test_run_job_orchestrates_pipeline_and_marks_ready(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    job_store.create_job("job_001", fps=1, max_frames=30, iterations=50)
    calls = []

    monkeypatch.setattr(job_runner.ffmpeg_runner, "extract_frames", lambda job_id, fps, max_frames: calls.append("frames") or 30)
    monkeypatch.setattr(job_runner.colmap_runner, "run_feature_extractor", lambda job_id: calls.append("features"))
    monkeypatch.setattr(job_runner.colmap_runner, "run_sequential_matcher", lambda job_id: calls.append("matching"))
    monkeypatch.setattr(job_runner.colmap_runner, "run_mapper", lambda job_id: calls.append("mapping"))
    monkeypatch.setattr(job_runner.opensplat_runner, "run_opensplat", lambda job_id, iterations: calls.append("opensplat") or Path("splat.ply"))
    monkeypatch.setattr(
        job_runner.model_exporter,
        "export_scene",
        lambda job_id, frame_count=None: calls.append(("export", frame_count))
        or {"id": "scene_001", "model_url": "/static/scenes/scene_001/scene.ply"},
    )

    job_runner.run_job("job_001")

    assert calls == [
        "frames",
        "features",
        "matching",
        "mapping",
        "opensplat",
        ("export", 30),
    ]
    job = job_store.read_job("job_001")
    assert job["status"] == JobStatus.READY
    assert job["scene_id"] == "scene_001"
    assert job["result_model"] == "/static/scenes/scene_001/scene.ply"


def test_run_job_marks_failed_on_exception(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    job_store.create_job("job_001", fps=1, max_frames=30, iterations=50)

    def fail_features(job_id):
        raise RuntimeError("feature extraction failed")

    monkeypatch.setattr(job_runner.ffmpeg_runner, "extract_frames", lambda job_id, fps, max_frames: 30)
    monkeypatch.setattr(job_runner.colmap_runner, "run_feature_extractor", fail_features)

    job_runner.run_job("job_001")

    job = job_store.read_job("job_001")
    assert job["status"] == JobStatus.FAILED
    assert job["error_stage"] == JobStatus.COLMAP_FEATURES
    assert "feature extraction failed" in job["error_message"]

