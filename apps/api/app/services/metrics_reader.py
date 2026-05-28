import json
import re
from typing import Any

from app.services import storage

try:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
except ImportError:
    EventAccumulator = None

TEXT_STEP_RES = [
    re.compile(r"step=(\d+).*loss=([0-9.eE+-]+)", re.IGNORECASE),
    re.compile(r"Step\s+(\d+).*loss[:=]\s*([0-9.eE+-]+)", re.IGNORECASE),
]

TENSORBOARD_LOSS_TAGS = ["Train Loss", "Train Loss Dict/main_loss"]


def _read_jsonl_metrics(job_id: str) -> list[dict[str, int | float]]:
    log_path = storage.job_logs_dir(job_id) / "splatfacto-metrics.jsonl"
    if not log_path.exists():
        return []
    points: list[dict[str, int | float]] = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        points.append(
            {
                "step": int(record["step"]),
                "loss": float(record["loss"]),
                "progress": int(record.get("progress", 0)),
            }
        )
    return points


def _read_tensorboard_metrics(job_id: str) -> list[dict[str, int | float]]:
    if EventAccumulator is None:
        return []

    event_paths = sorted(storage.job_nerfstudio_outputs_dir(job_id).glob(f"{job_id}/splatfacto/*/events.out.tfevents.*"))
    points: list[dict[str, int | float]] = []
    for event_path in event_paths:
        accumulator = EventAccumulator(str(event_path))
        try:
            accumulator.Reload()
            scalar_tags = accumulator.Tags().get("scalars", [])
        except Exception:
            continue

        loss_tag = next((tag for tag in TENSORBOARD_LOSS_TAGS if tag in scalar_tags), None)
        if loss_tag is None:
            continue

        try:
            for event in accumulator.Scalars(loss_tag):
                points.append({"step": int(event.step), "loss": float(event.value), "progress": 0})
        except Exception:
            continue

    deduped: dict[int, dict[str, int | float]] = {}
    for point in points:
        deduped[int(point["step"])] = point
    return [deduped[step] for step in sorted(deduped)]


def _read_text_metrics(job_id: str) -> list[dict[str, int | float]]:
    log_path = storage.job_logs_dir(job_id) / "splatfacto.log"
    if not log_path.exists():
        return []
    points: list[dict[str, int | float]] = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        for pattern in TEXT_STEP_RES:
            match = pattern.search(line.strip())
            if match:
                points.append({"step": int(match.group(1)), "loss": float(match.group(2)), "progress": 0})
                break
    return points


def read_training_metrics(job_id: str) -> dict[str, Any]:
    source = "none"
    points = _read_tensorboard_metrics(job_id)
    if points:
        source = "tensorboard"
    else:
        points = _read_jsonl_metrics(job_id)
        if points:
            source = "jsonl"
        else:
            points = _read_text_metrics(job_id)
            if points:
                source = "text"

    latest = points[-1] if points else None
    return {
        "job_id": job_id,
        "source": source,
        "latest_step": latest["step"] if latest else None,
        "latest_loss": latest["loss"] if latest else None,
        "progress": latest["progress"] if latest else 0,
        "points": points,
    }
