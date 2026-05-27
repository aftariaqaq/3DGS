from pathlib import Path

from app.services import colmap_runner, ffmpeg_runner, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(storage, "SCENES_DIR", tmp_path / "scenes")
    monkeypatch.setattr(ffmpeg_runner.storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(colmap_runner.storage, "JOBS_DIR", tmp_path / "jobs")


def test_extract_frames_runs_ffmpeg_and_limits_frames(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_input_dir("job_001") / "input.mp4").write_text("video", encoding="utf-8")

    calls = []

    def fake_run_command(args, log_path, cwd=None):
        calls.append((args, log_path, cwd))
        for index in range(5):
            (storage.job_images_dir("job_001") / f"frame_{index + 1:06d}.jpg").write_text(
                "frame", encoding="utf-8"
            )

    monkeypatch.setattr(ffmpeg_runner, "run_command", fake_run_command)

    frame_count = ffmpeg_runner.extract_frames("job_001", fps=1, max_frames=3)

    assert frame_count == 3
    assert len(list(storage.job_images_dir("job_001").glob("*.jpg"))) == 3
    assert calls[0][0][0] == "ffmpeg"
    assert "-vf" in calls[0][0]
    assert "fps=1" in calls[0][0]


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
