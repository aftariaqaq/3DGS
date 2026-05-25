from __future__ import annotations

import math
from dataclasses import dataclass, field

from packages.capture_schema.models import CameraSample, CaptureEvent, FrameTimestamp, ImuSample
from packages.sensor_fusion.diagnostics import flags_for_event_types
from packages.sensor_fusion.timeline import frame_time_ns, samples_between


@dataclass(slots=True)
class SensorWindow:
    frame_index: int
    timestamp_ns: int
    gyro_sample_count: int
    gyro_magnitude_mean: float | None
    gyro_magnitude_max: float | None
    acceleration_sample_count: int
    acceleration_magnitude_mean: float | None
    acceleration_magnitude_max: float | None
    rotation_vector_available: bool
    metadata_sample_count: int
    flags: list[str] = field(default_factory=list)


def _magnitude(sample: ImuSample) -> float:
    return math.sqrt(sample.x * sample.x + sample.y * sample.y + sample.z * sample.z)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _max(values: list[float]) -> float | None:
    if not values:
        return None
    return max(values)


def build_sensor_windows(
    frames: list[FrameTimestamp],
    imu_samples: list[ImuSample],
    camera_samples: list[CameraSample],
    events: list[CaptureEvent],
    *,
    half_window_ns: int = 50_000_000,
    fast_rotation_threshold: float = 4.0,
    high_acceleration_threshold: float = 15.0,
) -> list[SensorWindow]:
    windows: list[SensorWindow] = []
    for frame in frames:
        timestamp = frame_time_ns(frame)
        start = timestamp - half_window_ns
        end = timestamp + half_window_ns
        imu_window = samples_between(imu_samples, start, end)
        camera_window = [sample for sample in camera_samples if start <= sample.sensor_timestamp_ns <= end]
        event_window = samples_between(events, start, end)

        gyro_magnitudes = [_magnitude(sample) for sample in imu_window if sample.type == "gyro"]
        acceleration_magnitudes = [_magnitude(sample) for sample in imu_window if sample.type == "accelerometer"]
        rotation_vector_available = any(
            sample.type in {"rotation_vector", "game_rotation_vector"} for sample in imu_window
        )

        flags = flags_for_event_types({event.type for event in event_window})
        gyro_max = _max(gyro_magnitudes)
        acceleration_max = _max(acceleration_magnitudes)
        if gyro_max is not None and gyro_max >= fast_rotation_threshold:
            flags.append("fast_rotation")
        if acceleration_max is not None and acceleration_max >= high_acceleration_threshold:
            flags.append("high_acceleration")
        if not camera_window:
            flags.append("metadata_missing")

        windows.append(
            SensorWindow(
                frame_index=frame.frame_index,
                timestamp_ns=timestamp,
                gyro_sample_count=len(gyro_magnitudes),
                gyro_magnitude_mean=_mean(gyro_magnitudes),
                gyro_magnitude_max=gyro_max,
                acceleration_sample_count=len(acceleration_magnitudes),
                acceleration_magnitude_mean=_mean(acceleration_magnitudes),
                acceleration_magnitude_max=acceleration_max,
                rotation_vector_available=rotation_vector_available,
                metadata_sample_count=len(camera_window),
                flags=sorted(set(flags)),
            )
        )
    return windows

