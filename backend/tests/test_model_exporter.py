from pathlib import Path

from app.services import job_store, model_exporter, scene_store, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(storage, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(job_store.storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(job_store.storage, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(scene_store.storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(scene_store.storage, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(model_exporter.storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(model_exporter.storage, "SCENES_DIR", tmp_path / "scenes")


def test_export_scene_copies_ply_and_writes_metadata(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    source = storage.job_opensplat_dir("job_001") / "splat.ply"
    source.write_text("ply data", encoding="utf-8")

    metadata = model_exporter.export_scene("job_001", scene_id="scene_001", frame_count=30)

    target = storage.scene_dir("scene_001") / "scene.ply"
    assert target.read_text(encoding="utf-8") == "ply data"
    assert metadata["id"] == "scene_001"
    assert metadata["job_id"] == "job_001"
    assert metadata["model_type"] == "ply"
    assert metadata["model_url"] == "/static/scenes/scene_001/scene.ply"
    assert metadata["stats"]["frame_count"] == 30
    assert metadata["stats"]["model_size_bytes"] == len("ply data")
    assert scene_store.read_scene("scene_001")["id"] == "scene_001"


def test_export_scene_generates_scene_id_when_not_provided(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_opensplat_dir("job_001") / "splat.ply").write_text("ply data", encoding="utf-8")

    metadata = model_exporter.export_scene("job_001")

    assert metadata["id"].startswith("scene_")
    assert (storage.scene_dir(metadata["id"]) / "scene.ply").is_file()

