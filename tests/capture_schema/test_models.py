import pytest

from packages.capture_schema.models import (
    CameraSample,
    CaptureEvent,
    CaptureMetadata,
    ChecksumManifest,
    FrameTimestamp,
    ImuSample,
)


def test_capture_metadata_accepts_required_and_camera_geometry_fields():
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
        actual_video_duration_us=61_000_000,
        video_codec="video/avc",
        bitrate_bps=80_000_000,
        started_monotonic_ns=1_000,
        stopped_monotonic_ns=61_001_000_000,
        zoom_ratio=1.0,
        scaler_crop_region=[0, 0, 3840, 2160],
        ae_lock_enabled=True,
        af_lock_enabled=True,
        awb_lock_enabled=True,
        camera_to_imu_transform=[
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        camera_imu_time_offset_ns=0,
        calibration_profile_id="pixel-0-4k-1x",
    )

    assert metadata.capture_id == "capture_001"
    assert metadata.zoom_ratio == 1.0
    assert metadata.scaler_crop_region == [0, 0, 3840, 2160]
    assert metadata.ae_lock_enabled is True


def test_capture_metadata_rejects_invalid_dimensions_and_timestamps():
    with pytest.raises(ValueError, match="video_width"):
        CaptureMetadata(
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
            video_width=0,
            video_height=2160,
            target_fps=30,
            actual_video_duration_us=61_000_000,
            video_codec="video/avc",
            bitrate_bps=80_000_000,
            started_monotonic_ns=1_000,
            stopped_monotonic_ns=61_001_000_000,
        )


def test_sample_models_preserve_timestamps_and_payloads():
    frame = FrameTimestamp(
        frame_index=7,
        pts_us=233_333,
        sensor_timestamp_ns=123_456_789,
        monotonic_ns=123_456_900,
    )
    camera = CameraSample(
        sensor_timestamp_ns=123_456_789,
        exposure_time_ns=8_333_333,
        iso=400,
        focal_length_mm=5.43,
        focus_distance_diopters=0.0,
        aperture=1.8,
        zoom_ratio=1.0,
        scaler_crop_region=[0, 0, 3840, 2160],
    )
    imu = ImuSample(type="gyro", timestamp_ns=123_456_789, x=0.01, y=-0.02, z=0.03, accuracy=3)
    event = CaptureEvent(timestamp_ns=123_456_789, type="capture_started", message="recording started")
    checksums = ChecksumManifest(files={"video.mp4": "a" * 64, "metadata.json": "b" * 64})

    assert frame.frame_index == 7
    assert camera.focal_length_mm == 5.43
    assert imu.type == "gyro"
    assert event.type == "capture_started"
    assert checksums.files["video.mp4"] == "a" * 64

