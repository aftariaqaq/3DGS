import json
import re
from typing import Any

from app.services import storage

TEXT_STEP_RES = [
    re.compile(r"step=(\d+).*loss=([0-9.eE+-]+)", re.IGNORECASE),
    re.compile(r"Step\s+(\d+).*loss[:=]\s*([0-9.eE+-]+)", re.IGNORECASE),
]


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
    points = _read_jsonl_metrics(job_id) or _read_text_metrics(job_id)

    latest = points[-1] if points else None
    return {
        "job_id": job_id,
        "latest_step": latest["step"] if latest else None,
        "latest_loss": latest["loss"] if latest else None,
        "progress": latest["progress"] if latest else 0,
        "points": points,
    }
