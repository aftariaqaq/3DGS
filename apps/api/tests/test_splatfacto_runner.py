from pathlib import Path

import pytest

from app.services import colmap_model_selector, splatfacto_runner, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(splatfacto_runner.storage, "JOBS_DIR", tmp_path / "jobs")


def test_run_splatfacto_uses_ns_train_and_ns_export(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_images_dir("job_001") / "frame_000001.jpg").write_text("image", encoding="utf-8")
    (storage.job_colmap_dir("job_001") / "sparse" / "0").mkdir(parents=True)
    calls = []

    def fake_run_command(command, log_path, cwd=None, env=None):
        calls.append((command, log_path.name, cwd, env))
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
    assert calls[1][0][calls[1][0].index("--vis") + 1] == "viewer+tensorboard"
    assert calls[1][1] == "splatfacto.log"
    assert calls[2][0][:2] == ["ns-export", "gaussian-splat"]
    assert "--load-config" in calls[2][0]
    assert calls[2][1] == "splatfacto-export.log"
    assert calls[2][3] == {"TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD": "1"}


def test_run_splatfacto_stages_largest_colmap_reconstruction(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_images_dir("job_001") / "frame_000001.jpg").write_text("image", encoding="utf-8")
    sparse_root = storage.job_colmap_dir("job_001") / "sparse"
    for model_id, images, points in [("0", 65, 20454), ("1", 742, 315233), ("2", 12, 900)]:
        model_dir = sparse_root / model_id
        model_dir.mkdir(parents=True)
        (model_dir / "cameras.bin").write_bytes((1).to_bytes(8, "little"))
        (model_dir / "images.bin").write_bytes(images.to_bytes(8, "little"))
        (model_dir / "points3D.bin").write_bytes(points.to_bytes(8, "little"))
    calls = []

    def fake_run_command(command, log_path, cwd=None, env=None):
        calls.append(command)
        if command[0] == "ns-train":
            config = storage.job_nerfstudio_outputs_dir("job_001") / "job_001" / "splatfacto" / "config.yml"
            config.parent.mkdir(parents=True)
            config.write_text("config", encoding="utf-8")
        if command[0] == "ns-export":
            (storage.job_splatfacto_export_dir("job_001") / "splat.ply").write_text("ply", encoding="utf-8")

    monkeypatch.setattr(splatfacto_runner, "run_command", fake_run_command)

    splatfacto_runner.run_splatfacto("job_001", max_num_iterations=2500)

    selected = colmap_model_selector.select_best_sparse_model("job_001")
    assert selected.model_id == "1"
    staged = storage.job_nerfstudio_data_dir("job_001") / "colmap" / "sparse" / "0"
    assert (staged / "images.bin").read_bytes()[:8] == (742).to_bytes(8, "little")
    assert calls[0][calls[0].index("--colmap-model-path") + 1] == str(staged)


def test_run_splatfacto_errors_when_export_missing(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_images_dir("job_001") / "frame_000001.jpg").write_text("image", encoding="utf-8")
    (storage.job_colmap_dir("job_001") / "sparse" / "0").mkdir(parents=True)

    def fake_run_command(command, log_path, cwd=None, env=None):
        if command[0] == "ns-process-data":
            (storage.job_nerfstudio_data_dir("job_001") / "transforms.json").write_text("{}", encoding="utf-8")
        if command[0] == "ns-train":
            config = storage.job_nerfstudio_outputs_dir("job_001") / "job_001" / "splatfacto" / "config.yml"
            config.parent.mkdir(parents=True)
            config.write_text("config", encoding="utf-8")

    monkeypatch.setattr(splatfacto_runner, "run_command", fake_run_command)

    with pytest.raises(RuntimeError, match="Splatfacto export not found"):
        splatfacto_runner.run_splatfacto("job_001", max_num_iterations=2500)
