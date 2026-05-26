from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from packages.capture_schema.jsonl import read_jsonl, write_jsonl
from packages.capture_schema.models import CameraSample, CaptureEvent, FrameTimestamp, ImuSample
from packages.frame_select.image_io import load_grayscale_image
from packages.frame_select.scoring import blur_score, duplicate_score, exposure_score, texture_score
from packages.frame_select.selection import FrameCandidate, select_keyframes
from packages.pipeline.capture_to_job import create_job_from_capture
from packages.sensor_fusion.windows import SensorWindow, build_sensor_windows

FrameExtractor = Callable[[Path, Path, int], list[Path]]


def _frame_name(frame_index: int) -> str:
    return f"frame_{frame_index:06d}.jpg"


def _coerce_frame(record: dict[str, Any]) -> FrameTimestamp:
    return FrameTimestamp(
        frame_index=int(record["frame_index"]),
        pts_us=int(record["pts_us"]),
        sensor_timestamp_ns=record.get("sensor_timestamp_ns"),
        monotonic_ns=record.get("monotonic_ns"),
    )


def _coerce_camera_sample(record: dict[str, Any]) -> CameraSample:
    return CameraSample(**record)


def _coerce_imu_sample(record: dict[str, Any]) -> ImuSample:
    return ImuSample(**record)


def _coerce_event(record: dict[str, Any]) -> CaptureEvent:
    return CaptureEvent(**record)


def _default_ffmpeg_extractor(video_path: Path, frames_dir: Path, frame_count: int) -> list[Path]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to extract frames from video.mp4")
    frames_dir.mkdir(parents=True, exist_ok=True)
    pattern = frames_dir / "frame_%06d.jpg"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-frames:v",
            str(frame_count),
            "-start_number",
            "0",
            "-q:v",
            "2",
            str(pattern),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return [path for path in (frames_dir / _frame_name(index) for index in range(frame_count)) if path.exists()]


def _frames_with_extracted_images(frames: list[FrameTimestamp], extracted: list[Path]) -> list[FrameTimestamp]:
    available_indexes = {int(path.stem.rsplit("_", 1)[-1]) for path in extracted if path.exists()}
    return [frame for frame in frames if frame.frame_index in available_indexes]


def _sensor_flags_by_frame(windows: list[SensorWindow]) -> dict[int, list[str]]:
    return {window.frame_index: window.flags for window in windows}


def _build_candidates(frames: list[FrameTimestamp], frames_dir: Path, windows: list[SensorWindow]) -> list[FrameCandidate]:
    candidates: list[FrameCandidate] = []
    previous_image = None
    flags_by_frame = _sensor_flags_by_frame(windows)
    for frame in frames:
        image = load_grayscale_image(frames_dir / _frame_name(frame.frame_index))
        candidates.append(
            FrameCandidate(
                frame_index=frame.frame_index,
                timestamp_ns=frame.sensor_timestamp_ns or frame.monotonic_ns or frame.pts_us * 1_000,
                blur=blur_score(image),
                exposure=exposure_score(image),
                texture=texture_score(image),
                duplicate=None if previous_image is None else duplicate_score(image, previous_image),
                sensor_flags=flags_by_frame.get(frame.frame_index, []),
            )
        )
        previous_image = image
    return candidates


def prepare_capture_for_selection(
    capture_root: Path,
    *,
    max_frames: int,
    min_time_distance_ns: int = 100_000_000,
    frame_extractor: FrameExtractor | None = None,
) -> Path:
    capture_root = Path(capture_root)
    raw_dir = capture_root / "raw"
    normalized_dir = capture_root / "normalized"
    frames_dir = normalized_dir / "frames"
    frames = [_coerce_frame(record) for record in read_jsonl(raw_dir / "frame_timestamps.jsonl")]
    camera_samples = [_coerce_camera_sample(record) for record in read_jsonl(raw_dir / "camera_samples.jsonl")]
    imu_samples = [_coerce_imu_sample(record) for record in read_jsonl(raw_dir / "imu_samples.jsonl")]
    events = [_coerce_event(record) for record in read_jsonl(raw_dir / "events.jsonl")]

    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    extractor = frame_extractor or _default_ffmpeg_extractor
    extracted = extractor(raw_dir / "video.mp4", frames_dir, len(frames))
    frames = _frames_with_extracted_images(frames, extracted)
    if not frames:
        raise ValueError("frame extractor did not create any usable frames")

    windows = build_sensor_windows(frames, imu_samples, camera_samples, events)
    candidates = _build_candidates(frames, frames_dir, windows)
    decisions = select_keyframes(candidates, max_frames=max_frames, min_time_distance_ns=min_time_distance_ns)

    write_jsonl(normalized_dir / "sensor_windows.jsonl", [asdict(window) for window in windows])
    write_jsonl(normalized_dir / "frame_decisions.jsonl", decisions)
    return normalized_dir


def prepare_and_create_job(
    capture_root: Path,
    jobs_root: Path,
    *,
    job_id: str,
    max_frames: int,
    min_time_distance_ns: int = 100_000_000,
    frame_extractor: FrameExtractor | None = None,
) -> Path:
    prepare_capture_for_selection(
        capture_root,
        max_frames=max_frames,
        min_time_distance_ns=min_time_distance_ns,
        frame_extractor=frame_extractor,
    )
    return create_job_from_capture(capture_root, jobs_root, job_id=job_id, max_frames=max_frames)
