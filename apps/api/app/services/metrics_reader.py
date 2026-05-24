import re
from typing import Any

from app.services import storage

STEP_RE = re.compile(r"^Step\s+(\d+):\s+([0-9.eE+-]+)\s+\((\d+)%\)")


def read_training_metrics(job_id: str) -> dict[str, Any]:
    log_path = storage.job_logs_dir(job_id) / "opensplat.log"
    points: list[dict[str, int | float]] = []

    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = STEP_RE.match(line.strip())
            if not match:
                continue
            points.append(
                {
                    "step": int(match.group(1)),
                    "loss": float(match.group(2)),
                    "progress": int(match.group(3)),
                }
            )

    latest = points[-1] if points else None
    return {
        "job_id": job_id,
        "latest_step": latest["step"] if latest else None,
        "latest_loss": latest["loss"] if latest else None,
        "progress": latest["progress"] if latest else 0,
        "points": points,
    }

