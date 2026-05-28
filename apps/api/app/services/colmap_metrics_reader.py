import re
from pathlib import Path
from typing import Any

from app.services import storage

PROGRESS_RES = [
    re.compile(r"Processed file \[(\d+)/(\d+)\]", re.IGNORECASE),
    re.compile(r"Matching block \[(\d+)/(\d+)\]", re.IGNORECASE),
]
REGISTERED_RES = [
    re.compile(r"Registered images:\s*(\d+)", re.IGNORECASE),
    re.compile(r"Registering image #\d+\s*\((\d+)\)", re.IGNORECASE),
]
POINTS_RES = [
    re.compile(r"Points:\s*(\d+)", re.IGNORECASE),
    re.compile(r"points3D:\s*(\d+)", re.IGNORECASE),
]


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _count_images(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for candidate in path.iterdir() if candidate.suffix.lower() in {".jpg", ".jpeg", ".png"})


def _progress_from_log(text: str) -> dict[str, int]:
    current = 0
    total = 0
    for pattern in PROGRESS_RES:
        for match in pattern.finditer(text):
            current = int(match.group(1))
            total = int(match.group(2))
    percent = int(round((current / total) * 100)) if total else 0
    return {"current": current, "total": total, "percent": percent}


def _last_int_match(text: str, patterns: list[re.Pattern[str]]) -> int:
    value = 0
    for pattern in patterns:
        for match in pattern.finditer(text):
            value = int(match.group(1))
    return value


def _recent_log(*texts: str, max_lines: int = 80) -> str:
    lines: list[str] = []
    for text in texts:
        lines.extend(line for line in text.splitlines() if line.strip())
    return "\n".join(lines[-max_lines:])


def _sparse_model_exists(job_id: str) -> bool:
    sparse_zero = storage.job_colmap_dir(job_id) / "sparse" / "0"
    return all((sparse_zero / name).exists() for name in ["cameras.bin", "images.bin", "points3D.bin"])


def _stage(features_log: str, matching_log: str, mapping_log: str, sparse_model_exists: bool) -> str:
    if sparse_model_exists:
        return "completed"
    if mapping_log:
        return "mapping"
    if matching_log:
        return "matching"
    if features_log:
        return "feature_extraction"
    return "waiting"


def read_colmap_metrics(job_id: str) -> dict[str, Any]:
    logs_dir = storage.job_logs_dir(job_id)
    features_log = _read_text(logs_dir / "colmap_features.log")
    matching_log = _read_text(logs_dir / "colmap_matching.log")
    mapping_log = _read_text(logs_dir / "colmap_mapping.log")
    sparse_model_exists = _sparse_model_exists(job_id)

    return {
        "job_id": job_id,
        "stage": _stage(features_log, matching_log, mapping_log, sparse_model_exists),
        "images_total": _count_images(storage.job_images_dir(job_id)),
        "feature_progress": _progress_from_log(features_log),
        "matching_progress": _progress_from_log(matching_log),
        "registered_images": _last_int_match(mapping_log, REGISTERED_RES),
        "sparse_points": _last_int_match(mapping_log, POINTS_RES),
        "sparse_model_exists": sparse_model_exists,
        "recent_log": _recent_log(features_log, matching_log, mapping_log),
    }
