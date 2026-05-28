from pathlib import Path

from app.services import colmap_metrics_reader, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(colmap_metrics_reader.storage, "JOBS_DIR", tmp_path / "jobs")


def test_read_colmap_metrics_reports_stage_progress(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    for index in range(5):
        (storage.job_images_dir("job_001") / f"frame_{index:04d}.jpg").write_text("image", encoding="utf-8")
    (storage.job_logs_dir("job_001") / "colmap_features.log").write_text(
        "Processed file [1/5]\nProcessed file [3/5]\n",
        encoding="utf-8",
    )
    (storage.job_logs_dir("job_001") / "colmap_matching.log").write_text(
        "Matching block [1/4]\nMatching block [2/4]\n",
        encoding="utf-8",
    )
    (storage.job_logs_dir("job_001") / "colmap_mapping.log").write_text(
        "Registering image #1 (1)\nRegistering image #2 (2)\n=> Registered images: 2\n=> Points: 1234\n",
        encoding="utf-8",
    )
    sparse_zero = storage.job_colmap_dir("job_001") / "sparse" / "0"
    sparse_zero.mkdir(parents=True)
    (sparse_zero / "cameras.bin").write_bytes(b"camera")
    (sparse_zero / "images.bin").write_bytes(b"images")
    (sparse_zero / "points3D.bin").write_bytes(b"points")

    metrics = colmap_metrics_reader.read_colmap_metrics("job_001")

    assert metrics["job_id"] == "job_001"
    assert metrics["stage"] == "completed"
    assert metrics["images_total"] == 5
    assert metrics["feature_progress"] == {"current": 3, "total": 5, "percent": 60}
    assert metrics["matching_progress"] == {"current": 2, "total": 4, "percent": 50}
    assert metrics["registered_images"] == 2
    assert metrics["sparse_points"] == 1234
    assert metrics["sparse_model_exists"] is True
    assert "Registered images" in metrics["recent_log"]


def test_read_colmap_metrics_handles_missing_logs(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")

    metrics = colmap_metrics_reader.read_colmap_metrics("job_001")

    assert metrics["stage"] == "waiting"
    assert metrics["images_total"] == 0
    assert metrics["feature_progress"] == {"current": 0, "total": 0, "percent": 0}
    assert metrics["matching_progress"] == {"current": 0, "total": 0, "percent": 0}
    assert metrics["recent_log"] == ""
