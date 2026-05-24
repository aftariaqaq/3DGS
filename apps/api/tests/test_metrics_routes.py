from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import metrics_reader, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(storage, "SCENES_DIR", tmp_path / "scenes")
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


def test_metrics_view_includes_axis_labels():
    response = TestClient(app).get("/jobs/job_001/metrics-view")

    assert response.status_code == 200
    assert "Step" in response.text
    assert "Loss" in response.text
    assert "xTicks" in response.text
    assert "yTicks" in response.text


def test_scene_viewer_serves_webgl_html(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.SCENES_DIR.mkdir(parents=True)
    scene_dir = storage.SCENES_DIR / "scene_001"
    scene_dir.mkdir()
    (scene_dir / "metadata.json").write_text(
        '{"id":"scene_001","model_url":"/static/scenes/scene_001/scene.ply","model_type":"ply"}',
        encoding="utf-8",
    )

    response = TestClient(app).get("/scenes/scene_001/viewer")

    assert response.status_code == 200
    assert "3DGS Viewer" in response.text
    assert "/static/scenes/scene_001/scene.ply" in response.text
    assert "@mkkellogg/gaussian-splats-3d@0.4.7" in response.text
    assert "GaussianSplats3D.Viewer" in response.text
    assert 'id="viewer-root"' in response.text
