from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from packages.capture_schema.checksums import validate_checksums
from packages.capture_schema.jsonl import read_jsonl
from packages.capture_schema.models import CaptureMetadata, ChecksumManifest
from packages.capture_schema.report import ImportReport

REQUIRED_BUNDLE_FILES = [
    "video.mp4",
    "metadata.json",
    "frame_timestamps.jsonl",
    "camera_samples.jsonl",
    "imu_samples.jsonl",
    "events.jsonl",
    "checksums.json",
]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _load_metadata(source: Path) -> CaptureMetadata:
    return CaptureMetadata(**_load_json(source / "metadata.json"))


def _load_manifest(source: Path) -> ChecksumManifest:
    return ChecksumManifest(**_load_json(source / "checksums.json"))


def _copy_raw_files(source: Path, raw_dir: Path) -> int:
    raw_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in source.iterdir():
        if path.is_file():
            shutil.copy2(path, raw_dir / path.name)
            count += 1
    return count


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")


def _geometry_warnings(metadata: CaptureMetadata, source: Path) -> list[str]:
    warnings: list[str] = []
    if metadata.zoom_ratio is None or metadata.zoom_ratio != 1.0:
        warnings.append("zoom_ratio is not 1.0")
    if metadata.stabilization_mode is None or metadata.stabilization_mode.lower() not in {"off", "none", "disabled"}:
        warnings.append("stabilization mode is enabled or unknown")
    if metadata.lens_intrinsics is None:
        warnings.append("lens intrinsics are missing")
    if metadata.lens_distortion is None:
        warnings.append("lens distortion is missing")
    if metadata.ae_lock_enabled is not True:
        warnings.append("AE lock is disabled or unknown")
    if metadata.af_lock_enabled is not True:
        warnings.append("AF lock is disabled or unknown")
    if metadata.awb_lock_enabled is not True:
        warnings.append("AWB lock is disabled or unknown")

    camera_samples_path = source / "camera_samples.jsonl"
    if camera_samples_path.exists():
        crop_regions = {
            tuple(sample.get("scaler_crop_region") or [])
            for sample in read_jsonl(camera_samples_path)
            if sample.get("scaler_crop_region") is not None
        }
        if len(crop_regions) > 1:
            warnings.append("scaler crop region changes across camera samples")
    return warnings


def _missing_file_errors(source: Path) -> list[str]:
    return [f"missing required file: {name}" for name in REQUIRED_BUNDLE_FILES if not (source / name).exists()]


def import_capture_bundle(source: Path, captures_root: Path, capture_id: str | None = None) -> ImportReport:
    source = Path(source)
    captures_root = Path(captures_root)
    if not source.is_dir():
        raise ValueError(f"capture bundle source must be a directory: {source}")

    errors = _missing_file_errors(source)
    metadata = _load_metadata(source)
    manifest = _load_manifest(source)
    errors.extend(validate_checksums(source, manifest))

    resolved_capture_id = capture_id or metadata.capture_id
    capture_root = captures_root / resolved_capture_id
    raw_dir = capture_root / "raw"
    normalized_dir = capture_root / "normalized"
    reports_dir = capture_root / "reports"

    if capture_root.exists():
        shutil.rmtree(capture_root)

    raw_file_count = _copy_raw_files(source, raw_dir)
    _write_json(normalized_dir / "metadata.json", asdict(metadata))

    warnings = _geometry_warnings(metadata, source)
    report = ImportReport(
        capture_id=resolved_capture_id,
        source_path=str(source),
        capture_root=str(capture_root),
        raw_file_count=raw_file_count,
        warnings=warnings,
        errors=errors,
    )
    _write_json(reports_dir / "import_report.json", report.to_dict())
    return report

