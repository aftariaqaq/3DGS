from __future__ import annotations

from typing import Protocol, TypeVar

from packages.capture_schema.models import FrameTimestamp


class Timestamped(Protocol):
    timestamp_ns: int


T = TypeVar("T", bound=Timestamped)


def frame_time_ns(frame: FrameTimestamp) -> int:
    if frame.sensor_timestamp_ns is not None:
        return frame.sensor_timestamp_ns
    if frame.monotonic_ns is not None:
        return frame.monotonic_ns
    return frame.pts_us * 1000


def nearest_sample(samples: list[T], timestamp_ns: int) -> T:
    if not samples:
        raise ValueError("samples must not be empty")
    return min(samples, key=lambda sample: abs(sample.timestamp_ns - timestamp_ns))


def samples_between(samples: list[T], start_ns: int, end_ns: int) -> list[T]:
    return [sample for sample in samples if start_ns <= sample.timestamp_ns <= end_ns]

