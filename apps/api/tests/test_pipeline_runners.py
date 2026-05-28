from pathlib import Path

from app.services import colmap_runner, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(storage, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(colmap_runner.storage, "JOBS_DIR", tmp_path / "jobs")


def test_colmap_runner_uses_cuda_feature_and_matching(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    calls = []

    def fake_run_command(args, log_path, cwd=None):
        calls.append(args)

    monkeypatch.setattr(colmap_runner, "run_command", fake_run_command)

    colmap_runner.run_feature_extractor("job_001")
    colmap_runner.run_sequential_matcher("job_001")
    colmap_runner.run_mapper("job_001")

    assert calls[0][1] == "feature_extractor"
    assert "--SiftExtraction.use_gpu" in calls[0]
    assert "1" in calls[0]
    assert "--SiftExtraction.max_image_size" in calls[0]
    assert "2400" in calls[0]
    assert calls[1][1] == "sequential_matcher"
    assert "--SiftMatching.use_gpu" in calls[1]
    assert "--SequentialMatching.overlap" in calls[1]
    assert calls[2][1] == "mapper"
    assert "--Mapper.ba_global_max_num_iterations" in calls[2]
