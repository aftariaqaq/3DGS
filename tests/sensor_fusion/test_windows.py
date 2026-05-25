from packages.capture_schema.models import CameraSample, CaptureEvent, FrameTimestamp, ImuSample
from packages.sensor_fusion.windows import build_sensor_windows


def test_build_sensor_windows_computes_motion_stats_and_flags_events():
    frames = [FrameTimestamp(frame_index=0, pts_us=0, sensor_timestamp_ns=1_000)]
    imu_samples = [
        ImuSample(type="gyro", timestamp_ns=900, x=0.0, y=0.0, z=0.0),
        ImuSample(type="gyro", timestamp_ns=1_000, x=3.0, y=4.0, z=0.0),
        ImuSample(type="accelerometer", timestamp_ns=1_050, x=0.0, y=0.0, z=12.0),
        ImuSample(type="rotation_vector", timestamp_ns=1_060, x=0.0, y=0.0, z=0.0, w=1.0),
    ]
    camera_samples = [
        CameraSample(sensor_timestamp_ns=980, exposure_time_ns=8_000_000, iso=400),
    ]
    events = [
        CaptureEvent(timestamp_ns=990, type="exposure_jump"),
        CaptureEvent(timestamp_ns=1_010, type="zoom_changed"),
    ]

    windows = build_sensor_windows(
        frames,
        imu_samples,
        camera_samples,
        events,
        half_window_ns=100,
        fast_rotation_threshold=4.0,
        high_acceleration_threshold=11.0,
    )

    window = windows[0]
    assert window.frame_index == 0
    assert window.gyro_sample_count == 2
    assert window.gyro_magnitude_max == 5.0
    assert window.acceleration_magnitude_max == 12.0
    assert window.rotation_vector_available is True
    assert window.metadata_sample_count == 1
    assert "fast_rotation" in window.flags
    assert "high_acceleration" in window.flags
    assert "exposure_jump_nearby" in window.flags
    assert "zoom_or_crop_change_nearby" in window.flags
