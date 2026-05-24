from pathlib import Path

from app.services import metrics_reader, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(metrics_reader.storage, "JOBS_DIR", tmp_path / "jobs")


def test_read_training_metrics_parses_opensplat_steps(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_logs_dir("job_001") / "opensplat.log").write_text(
        "\n".join(
            [
                "Using CUDA",
                "Step 1: 0.281546 (0%)",
                "Step 2: 0.304394 (0%)",
                "Step 1000: 0.134722 (100%)",
                "Wrote /work/opensplat/splat.ply",
            ]
        ),
        encoding="utf-8",
    )

    metrics = metrics_reader.read_training_metrics("job_001")

    assert metrics["job_id"] == "job_001"
    assert metrics["latest_step"] == 1000
    assert metrics["latest_loss"] == 0.134722
    assert metrics["progress"] == 100
    assert metrics["points"] == [
        {"step": 1, "loss": 0.281546, "progress": 0},
        {"step": 2, "loss": 0.304394, "progress": 0},
        {"step": 1000, "loss": 0.134722, "progress": 100},
    ]


def test_read_training_metrics_handles_missing_log(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")

    metrics = metrics_reader.read_training_metrics("job_001")

    assert metrics["job_id"] == "job_001"
    assert metrics["latest_step"] is None
    assert metrics["latest_loss"] is None
    assert metrics["progress"] == 0
    assert metrics["points"] == []
