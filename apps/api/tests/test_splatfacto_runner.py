from pathlib import Path

import pytest

from app.services import splatfacto_runner, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(splatfacto_runner.storage, "JOBS_DIR", tmp_path / "jobs")


def test_run_splatfacto_uses_ns_train_and_ns_export(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_images_dir("job_001") / "frame_000001.jpg").write_text("image", encoding="utf-8")
    (storage.job_colmap_dir("job_001") / "sparse" / "0").mkdir(parents=True)
    calls = []

    def fake_run_command(command, log_path, cwd=None):
        calls.append((command, log_path.name, cwd))
        if command[0] == "ns-process-data":
            (storage.job_nerfstudio_data_dir("job_001") / "transforms.json").write_text("{}", encoding="utf-8")
        if command[0] == "ns-train":
            config = storage.job_nerfstudio_outputs_dir("job_001") / "job_001" / "splatfacto" / "config.yml"
            config.parent.mkdir(parents=True)
            config.write_text("config", encoding="utf-8")
        if command[0] == "ns-export":
            storage.job_splatfacto_export_dir("job_001").mkdir(parents=True, exist_ok=True)
            (storage.job_splatfacto_export_dir("job_001") / "splat.ply").write_text("ply", encoding="utf-8")

    monkeypatch.setattr(splatfacto_runner, "run_command", fake_run_command)

    output = splatfacto_runner.run_splatfacto("job_001", max_num_iterations=2500)

    assert output == storage.job_splatfacto_export_dir("job_001") / "splat.ply"
    assert calls[0][0][:2] == ["ns-process-data", "images"]
    assert "--skip-colmap" in calls[0][0]
    assert "--colmap-model-path" in calls[0][0]
    assert calls[0][1] == "nerfstudio-process-data.log"
    assert calls[1][0][:2] == ["ns-train", "splatfacto"]
    assert "--data" in calls[1][0]
    assert "--max-num-iterations" in calls[1][0]
    assert calls[1][1] == "splatfacto.log"
    assert calls[2][0][:2] == ["ns-export", "gaussian-splat"]
    assert "--load-config" in calls[2][0]
    assert calls[2][1] == "splatfacto-export.log"


def test_run_splatfacto_errors_when_export_missing(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_images_dir("job_001") / "frame_000001.jpg").write_text("image", encoding="utf-8")
    (storage.job_colmap_dir("job_001") / "sparse" / "0").mkdir(parents=True)

    def fake_run_command(command, log_path, cwd=None):
        if command[0] == "ns-process-data":
            (storage.job_nerfstudio_data_dir("job_001") / "transforms.json").write_text("{}", encoding="utf-8")
        if command[0] == "ns-train":
            config = storage.job_nerfstudio_outputs_dir("job_001") / "job_001" / "splatfacto" / "config.yml"
            config.parent.mkdir(parents=True)
            config.write_text("config", encoding="utf-8")

    monkeypatch.setattr(splatfacto_runner, "run_command", fake_run_command)

    with pytest.raises(RuntimeError, match="Splatfacto export not found"):
        splatfacto_runner.run_splatfacto("job_001", max_num_iterations=2500)
