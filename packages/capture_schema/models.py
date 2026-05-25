from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


def _require_positive(name: str, value: int | float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _require_non_negative(name: str, value: int | float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _require_timestamp_order(started: int, stopped: int) -> None:
    if stopped < started:
        raise ValueError("stopped_monotonic_ns must be greater than or equal to started_monotonic_ns")


def _validate_matrix4(name: str, value: list[list[float]] | None) -> None:
    if value is None:
        return
    if len(value) != 4 or any(len(row) != 4 for row in value):
        raise ValueError(f"{name} must be a 4x4 matrix")


@dataclass(slots=True)
class CaptureMetadata:
    schema_version: str
    capture_id: str
    app_version: str
    platform: str
    device_manufacturer: str
    device_model: str
    android_api_level: int
    camera_id: str
    lens_facing: str
    sensor_orientation_degrees: int
    video_width: int
    video_height: int
    target_fps: int
    actual_video_duration_us: int
    video_codec: str
    bitrate_bps: int
    started_monotonic_ns: int
    stopped_monotonic_ns: int
    lens_intrinsics: list[float] | None = None
    lens_distortion: list[float] | None = None
    physical_sensor_size: list[float] | None = None
    focal_lengths: list[float] | None = None
    stabilization_mode: str | None = None
    exposure_mode: str | None = None
    focus_mode: str | None = None
    white_balance_mode: str | None = None
    zoom_ratio: float | None = None
    scaler_crop_region: list[int] | None = None
    ae_lock_enabled: bool | None = None
    af_lock_enabled: bool | None = None
    awb_lock_enabled: bool | None = None
    camera_to_imu_transform: list[list[float]] | None = None
    camera_imu_time_offset_ns: int | None = None
    calibration_profile_id: str | None = None

    def __post_init__(self) -> None:
        _require_positive("video_width", self.video_width)
        _require_positive("video_height", self.video_height)
        _require_positive("target_fps", self.target_fps)
        _require_positive("actual_video_duration_us", self.actual_video_duration_us)
        _require_positive("bitrate_bps", self.bitrate_bps)
        _require_non_negative("started_monotonic_ns", self.started_monotonic_ns)
        _require_non_negative("stopped_monotonic_ns", self.stopped_monotonic_ns)
        _require_timestamp_order(self.started_monotonic_ns, self.stopped_monotonic_ns)
        if self.zoom_ratio is not None:
            _require_positive("zoom_ratio", self.zoom_ratio)
        if self.scaler_crop_region is not None and len(self.scaler_crop_region) != 4:
            raise ValueError("scaler_crop_region must contain four integers")
        _validate_matrix4("camera_to_imu_transform", self.camera_to_imu_transform)


@dataclass(slots=True)
class FrameTimestamp:
    frame_index: int
    pts_us: int
    sensor_timestamp_ns: int | None = None
    monotonic_ns: int | None = None

    def __post_init__(self) -> None:
        _require_non_negative("frame_index", self.frame_index)
        _require_non_negative("pts_us", self.pts_us)
        if self.sensor_timestamp_ns is not None:
            _require_non_negative("sensor_timestamp_ns", self.sensor_timestamp_ns)
        if self.monotonic_ns is not None:
            _require_non_negative("monotonic_ns", self.monotonic_ns)


@dataclass(slots=True)
class CameraSample:
    sensor_timestamp_ns: int
    exposure_time_ns: int | None = None
    iso: int | None = None
    focal_length_mm: float | None = None
    focus_distance_diopters: float | None = None
    aperture: float | None = None
    zoom_ratio: float | None = None
    scaler_crop_region: list[int] | None = None
    optical_stabilization_mode: str | None = None
    video_stabilization_mode: str | None = None
    lens_intrinsics: list[float] | None = None
    lens_distortion: list[float] | None = None
    rolling_shutter_skew_ns: int | None = None
    ae_state: str | None = None
    af_state: str | None = None
    awb_state: str | None = None

    def __post_init__(self) -> None:
        _require_non_negative("sensor_timestamp_ns", self.sensor_timestamp_ns)
        if self.exposure_time_ns is not None:
            _require_positive("exposure_time_ns", self.exposure_time_ns)
        if self.iso is not None:
            _require_positive("iso", self.iso)
        if self.zoom_ratio is not None:
            _require_positive("zoom_ratio", self.zoom_ratio)
        if self.scaler_crop_region is not None and len(self.scaler_crop_region) != 4:
            raise ValueError("scaler_crop_region must contain four integers")


@dataclass(slots=True)
class ImuSample:
    type: Literal["gyro", "accelerometer", "magnetometer", "rotation_vector", "game_rotation_vector"]
    timestamp_ns: int
    x: float
    y: float
    z: float
    accuracy: int | None = None
    w: float | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_negative("timestamp_ns", self.timestamp_ns)


@dataclass(slots=True)
class CaptureEvent:
    timestamp_ns: int
    type: str
    message: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_negative("timestamp_ns", self.timestamp_ns)


@dataclass(slots=True)
class ChecksumManifest:
    files: dict[str, str]

    def __post_init__(self) -> None:
        for path, digest in self.files.items():
            if not path or path.startswith("/") or "\\" in path:
                raise ValueError(f"invalid checksum path: {path}")
            if len(digest) != 64:
                raise ValueError(f"invalid sha256 digest for {path}")
            int(digest, 16)

