from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import metrics_reader, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(metrics_reader.storage, "JOBS_DIR", tmp_path / "jobs")


def test_metrics_endpoint_returns_parsed_loss_points(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_logs_dir("job_001") / "opensplat.log").write_text(
        "Step 10: 0.5 (5%)\nStep 20: 0.25 (10%)\n",
        encoding="utf-8",
    )

    response = TestClient(app).get("/api/jobs/job_001/metrics")

    assert response.status_code == 200
    assert response.json()["latest_loss"] == 0.25
    assert response.json()["points"][-1] == {"step": 20, "loss": 0.25, "progress": 10}


def test_metrics_view_serves_html():
    response = TestClient(app).get("/jobs/job_001/metrics-view")

    assert response.status_code == 200
    assert "Training Loss" in response.text
    assert "/api/jobs/job_001/metrics" in response.text

