from __future__ import annotations

import json
import shutil
from pathlib import Path

from packages.capture_schema.jsonl import read_jsonl, write_jsonl


def _frame_name(frame_index: int) -> str:
    return f"frame_{frame_index:06d}.jpg"


def _copy_import_report(capture_root: Path, capture_dir: Path) -> None:
    source = capture_root / "reports" / "import_report.json"
    destination = capture_dir / "import_report.json"
    if source.exists():
        shutil.copy2(source, destination)
    else:
        destination.write_text(json.dumps({"warnings": ["import report missing"], "errors": []}), encoding="utf-8")


def create_job_from_capture(capture_root: Path, jobs_root: Path, job_id: str, max_frames: int) -> Path:
    capture_root = Path(capture_root)
    jobs_root = Path(jobs_root)
    job_root = jobs_root / job_id
    images_dir = job_root / "images"
    capture_dir = job_root / "capture"
    frames_dir = capture_root / "normalized" / "frames"
    decisions_path = capture_root / "normalized" / "frame_decisions.jsonl"

    if not frames_dir.exists():
        raise ValueError(f"normalized frames directory not found: {frames_dir}")
    if not decisions_path.exists():
        raise ValueError(f"frame decisions file not found: {decisions_path}")

    for refresh_dir in (images_dir, capture_dir):
        if refresh_dir.exists():
            shutil.rmtree(refresh_dir)
    images_dir.mkdir(parents=True)
    capture_dir.mkdir(parents=True)

    decisions = read_jsonl(decisions_path)
    selected_decisions = [decision for decision in decisions if decision.get("selected") is True][:max_frames]

    selected_records = []
    for decision in selected_decisions:
        frame_index = int(decision["frame_index"])
        frame_name = _frame_name(frame_index)
        source = frames_dir / frame_name
        if not source.exists():
            raise ValueError(f"selected frame missing: {source}")
        shutil.copy2(source, images_dir / frame_name)
        selected_records.append(
            {
                "frame_index": frame_index,
                "timestamp_ns": decision.get("timestamp_ns"),
                "image": f"images/{frame_name}",
                "score": decision.get("score"),
                "reasons": decision.get("reasons", []),
            }
        )

    write_jsonl(capture_dir / "selected_frames.jsonl", selected_records)
    write_jsonl(capture_dir / "frame_scores.jsonl", decisions)
    sensor_windows_path = capture_root / "normalized" / "sensor_windows.jsonl"
    if sensor_windows_path.exists():
        shutil.copy2(sensor_windows_path, capture_dir / "sensor_windows.jsonl")
    else:
        write_jsonl(capture_dir / "sensor_windows.jsonl", [])
    _copy_import_report(capture_root, capture_dir)

    return job_root
