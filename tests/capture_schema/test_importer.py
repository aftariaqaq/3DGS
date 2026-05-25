import json
from dataclasses import asdict

from packages.capture_schema.checksums import sha256_file
from packages.capture_schema.importer import import_capture_bundle
from packages.capture_schema.jsonl import write_jsonl
from packages.capture_schema.models import (
    CameraSample,
    CaptureEvent,
    CaptureMetadata,
    ChecksumManifest,
    FrameTimestamp,
    ImuSample,
)


def _write_sample_bundle(bundle_root):
    metadata = CaptureMetadata(
        schema_version="1.0",
        capture_id="capture_001",
        app_version="0.1.0",
        platform="android",
        device_manufacturer="Google",
        device_model="Pixel",
        android_api_level=35,
        camera_id="0",
        lens_facing="back",
        sensor_orientation_degrees=90,
        video_width=3840,
        video_height=2160,
        target_fps=30,
        actual_video_duration_us=2_000_000,
        video_codec="video/avc",
        bitrate_bps=80_000_000,
        started_monotonic_ns=1_000,
        stopped_monotonic_ns=2_001_000_000,
        zoom_ratio=1.2,
        scaler_crop_region=[0, 0, 3840, 2160],
        ae_lock_enabled=False,
        af_lock_enabled=True,
        awb_lock_enabled=None,
        stabilization_mode="on",
    )
    (bundle_root / "metadata.json").write_text(json.dumps(asdict(metadata)), encoding="utf-8")
    (bundle_root / "video.mp4").write_bytes(b"video")
    write_jsonl(
        bundle_root / "frame_timestamps.jsonl",
        [FrameTimestamp(frame_index=0, pts_us=0, sensor_timestamp_ns=1_000, monotonic_ns=1_000)],
    )
    write_jsonl(
        bundle_root / "camera_samples.jsonl",
        [
            CameraSample(
                sensor_timestamp_ns=1_000,
                zoom_ratio=1.2,
                scaler_crop_region=[0, 0, 3840, 2160],
                video_stabilization_mode="on",
            )
        ],
    )
    write_jsonl(
        bundle_root / "imu_samples.jsonl",
        [ImuSample(type="gyro", timestamp_ns=1_000, x=0.0, y=0.0, z=0.0)],
    )
    write_jsonl(
        bundle_root / "events.jsonl",
        [CaptureEvent(timestamp_ns=1_000, type="capture_started", message="recording started")],
    )
    manifest = ChecksumManifest(
        files={
            "video.mp4": sha256_file(bundle_root / "video.mp4"),
            "metadata.json": sha256_file(bundle_root / "metadata.json"),
            "frame_timestamps.jsonl": sha256_file(bundle_root / "frame_timestamps.jsonl"),
            "camera_samples.jsonl": sha256_file(bundle_root / "camera_samples.jsonl"),
            "imu_samples.jsonl": sha256_file(bundle_root / "imu_samples.jsonl"),
            "events.jsonl": sha256_file(bundle_root / "events.jsonl"),
        }
    )
    (bundle_root / "checksums.json").write_text(json.dumps(asdict(manifest)), encoding="utf-8")


def test_import_capture_bundle_copies_raw_files_and_writes_report(tmp_path):
    source = tmp_path / "capture_source"
    source.mkdir()
    _write_sample_bundle(source)
    captures_root = tmp_path / "captures"

    report = import_capture_bundle(source, captures_root)

    capture_root = captures_root / "capture_001"
    assert report.capture_id == "capture_001"
    assert (capture_root / "raw" / "video.mp4").read_bytes() == b"video"
    assert (capture_root / "normalized" / "metadata.json").exists()
    assert (capture_root / "reports" / "import_report.json").exists()

    report_json = json.loads((capture_root / "reports" / "import_report.json").read_text(encoding="utf-8"))
    assert report_json["capture_id"] == "capture_001"
    assert report_json["errors"] == []
    assert "zoom_ratio is not 1.0" in report_json["warnings"]
    assert "stabilization mode is enabled or unknown" in report_json["warnings"]
    assert "AE lock is disabled or unknown" in report_json["warnings"]


def test_import_capture_bundle_reports_checksum_errors(tmp_path):
    source = tmp_path / "capture_source"
    source.mkdir()
    _write_sample_bundle(source)
    (source / "video.mp4").write_bytes(b"damaged")

    report = import_capture_bundle(source, tmp_path / "captures")

    assert any("checksum mismatch: video.mp4" in error for error in report.errors)
