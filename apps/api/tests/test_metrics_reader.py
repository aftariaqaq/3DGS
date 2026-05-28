from pathlib import Path

from app.services import metrics_reader, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(metrics_reader.storage, "JOBS_DIR", tmp_path / "jobs")


def test_read_training_metrics_parses_splatfacto_jsonl(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_logs_dir("job_001") / "splatfacto-metrics.jsonl").write_text(
        "\n".join(
            [
                '{"step": 1, "loss": 0.45, "progress": 0}',
                '{"step": 1000, "loss": 0.21, "progress": 40}',
                '{"step": 2500, "loss": 0.12, "progress": 100}',
            ]
        ),
        encoding="utf-8",
    )

    metrics = metrics_reader.read_training_metrics("job_001")

    assert metrics["job_id"] == "job_001"
    assert metrics["latest_step"] == 2500
    assert metrics["latest_loss"] == 0.12
    assert metrics["progress"] == 100
    assert metrics["points"] == [
        {"step": 1, "loss": 0.45, "progress": 0},
        {"step": 1000, "loss": 0.21, "progress": 40},
        {"step": 2500, "loss": 0.12, "progress": 100},
    ]


def test_read_training_metrics_parses_splatfacto_text_log(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_logs_dir("job_001") / "splatfacto.log").write_text(
        "step=10 loss=0.333\nstep=20 loss=0.222\n",
        encoding="utf-8",
    )

    metrics = metrics_reader.read_training_metrics("job_001")

    assert metrics["latest_step"] == 20
    assert metrics["latest_loss"] == 0.222


def test_read_training_metrics_prefers_tensorboard_events(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    events_dir = storage.job_nerfstudio_outputs_dir("job_001") / "job_001" / "splatfacto" / "2026-05-27_123513"
    events_dir.mkdir(parents=True)
    events_path = events_dir / "events.out.tfevents.fake"
    events_path.write_text("event placeholder", encoding="utf-8")
    (storage.job_logs_dir("job_001") / "splatfacto.log").write_text(
        "training started but no loss text here\n",
        encoding="utf-8",
    )

    class FakeEvent:
        def __init__(self, step: int, value: float):
            self.step = step
            self.value = value

    class FakeAccumulator:
        def __init__(self, path: str):
            assert path == str(events_path)

        def Reload(self):
            return self

        def Tags(self):
            return {"scalars": ["Train Loss", "Train Loss Dict/main_loss"]}

        def Scalars(self, tag: str):
            assert tag == "Train Loss"
            return [FakeEvent(0, 0.9), FakeEvent(10, 0.25), FakeEvent(20, 0.125)]

    monkeypatch.setattr(metrics_reader, "EventAccumulator", FakeAccumulator)

    metrics = metrics_reader.read_training_metrics("job_001")

    assert metrics["source"] == "tensorboard"
    assert metrics["latest_step"] == 20
    assert metrics["latest_loss"] == 0.125
    assert metrics["progress"] == 0
    assert metrics["points"][-1] == {"step": 20, "loss": 0.125, "progress": 0}


def test_read_training_metrics_handles_missing_log(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")

    metrics = metrics_reader.read_training_metrics("job_001")

    assert metrics["job_id"] == "job_001"
    assert metrics["latest_step"] is None
    assert metrics["latest_loss"] is None
    assert metrics["progress"] == 0
    assert metrics["points"] == []
