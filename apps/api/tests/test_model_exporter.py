from pathlib import Path

import pytest

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


def test_export_scene_converts_to_supersplat_and_writes_metadata(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    source = storage.job_splatfacto_export_dir("job_001") / "splat.ply"
    source.write_text("ply data", encoding="utf-8")

    def fake_convert(source_ply, target_dir, log_path):
        assert source_ply == target_dir / "source.ply"
        assert log_path == storage.job_logs_dir("job_001") / "supersplat-convert.log"
        target = target_dir / "scene.sog"
        target.write_text("sog data", encoding="utf-8")
        (target_dir / "supersplat.html").write_text("<html></html>", encoding="utf-8")
        return target

    monkeypatch.setattr(model_exporter.supersplat_converter, "convert_to_supersplat", fake_convert)

    metadata = model_exporter.export_scene("job_001", scene_id="scene_001", frame_count=30)

    target = storage.scene_dir("scene_001") / "scene.sog"
    source_copy = storage.scene_dir("scene_001") / "source.ply"
    assert target.read_text(encoding="utf-8") == "sog data"
    assert source_copy.read_text(encoding="utf-8") == "ply data"
    assert metadata["id"] == "scene_001"
    assert metadata["job_id"] == "job_001"
    assert metadata["model_type"] == "sog"
    assert metadata["model_url"] == "/static/scenes/scene_001/scene.sog"
    assert metadata["source_model_url"] == "/static/scenes/scene_001/source.ply"
    assert metadata["viewer_url"] == "/scenes/scene_001/supersplat"
    assert metadata["fallback_viewer_url"] == "/scenes/scene_001/viewer"
    assert metadata["supersplat_viewer_url"] == "/static/scenes/scene_001/supersplat.html"
    assert metadata["stats"]["frame_count"] == 30
    assert metadata["stats"]["model_size_bytes"] == len("sog data")
    assert metadata["stats"]["source_model_size_bytes"] == len("ply data")
    assert scene_store.read_scene("scene_001")["id"] == "scene_001"


def test_export_scene_generates_scene_id_when_not_provided(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_splatfacto_export_dir("job_001") / "splat.ply").write_text("ply data", encoding="utf-8")

    def fake_convert(source_ply, target_dir, log_path):
        target = target_dir / "scene.sog"
        target.write_text("sog data", encoding="utf-8")
        (target_dir / "supersplat.html").write_text("<html></html>", encoding="utf-8")
        return target

    monkeypatch.setattr(model_exporter.supersplat_converter, "convert_to_supersplat", fake_convert)

    metadata = model_exporter.export_scene("job_001")

    assert metadata["id"].startswith("scene_")
    assert (storage.scene_dir(metadata["id"]) / "scene.sog").is_file()


def test_export_scene_errors_when_splatfacto_output_missing(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")

    with pytest.raises(RuntimeError, match="Splatfacto output not found"):
        model_exporter.export_scene("job_001")
