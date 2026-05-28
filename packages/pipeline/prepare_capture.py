from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from packages.capture_schema.jsonl import read_jsonl, write_jsonl
from packages.capture_schema.models import CameraSample, CaptureEvent, CaptureMetadata, FrameTimestamp, ImuSample
from packages.frame_select.image_io import load_grayscale_image
from packages.frame_select.scoring import blur_score, duplicate_score, exposure_score, texture_score
from packages.frame_select.selection import FrameCandidate, select_keyframes
from packages.pipeline.capture_to_job import create_job_from_capture
from packages.sensor_fusion.windows import SensorWindow, build_sensor_windows

FrameExtractor = Callable[..., list[Path]]
VideoProbe = Callable[[Path, int], dict[str, Any]]


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


def _default_ffmpeg_extractor(
    video_path: Path,
    frames_dir: Path,
    frame_count: int,
    fps: int | None = None,
    log_path: Path | None = None,
) -> list[Path]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to extract frames from video.mp4")
    frames_dir.mkdir(parents=True, exist_ok=True)
    pattern = frames_dir / "frame_%06d.jpg"
    args = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
    ]
    if fps is not None:
        args.extend(["-vf", f"fps={fps}"])
    args.extend(
        [
            "-frames:v",
            str(frame_count),
            "-start_number",
            "0",
            "-q:v",
            "2",
            str(pattern),
        ]
    )
    if log_path is None:
        subprocess.run(
            args,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    else:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8", newline="\n") as log:
            subprocess.run(args, check=True, stdout=log, stderr=subprocess.STDOUT, text=True)
    return [path for path in (frames_dir / _frame_name(index) for index in range(frame_count)) if path.exists()]


def _extract_frames(
    extractor: FrameExtractor,
    video_path: Path,
    frames_dir: Path,
    frame_count: int,
    *,
    fps: int | None,
    log_path: Path | None,
) -> list[Path]:
    if fps is None:
        return extractor(video_path, frames_dir, frame_count)
    if log_path is None:
        return extractor(video_path, frames_dir, frame_count, fps=fps)
    return extractor(video_path, frames_dir, frame_count, fps=fps, log_path=log_path)


def _parse_ratio(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        denominator_value = float(denominator)
        return 0.0 if denominator_value == 0 else float(numerator) / denominator_value
    return float(value)


def _frame_pts_us(frame: dict[str, Any]) -> int | None:
    for key in ("best_effort_timestamp_time", "pts_time", "pkt_pts_time"):
        value = frame.get(key)
        if value not in (None, "N/A"):
            return int(round(float(value) * 1_000_000))
    return None


def _sample_frame_timestamps(pts_values_us: list[int], fps: int, duration_us: int) -> list[FrameTimestamp]:
    interval_us = max(1, int(round(1_000_000 / fps)))
    source_pts = sorted(set(value for value in pts_values_us if value >= 0))
    if not source_pts:
        source_pts = list(range(0, max(duration_us, interval_us), interval_us))

    sampled: list[int] = []
    next_target = source_pts[0]
    for pts_us in source_pts:
        if pts_us + 1 >= next_target:
            sampled.append(pts_us)
            next_target += interval_us
            while pts_us >= next_target:
                next_target += interval_us

    return [
        FrameTimestamp(frame_index=index, pts_us=pts_us, monotonic_ns=pts_us * 1_000)
        for index, pts_us in enumerate(sampled)
    ]


def probe_video_for_capture(video_path: Path, fps: int) -> dict[str, Any]:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe is required to read frame timestamps from video.mp4")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,codec_name,bit_rate,duration,avg_frame_rate,r_frame_rate:frame=best_effort_timestamp_time,pts_time,pkt_pts_time",
            "-of",
            "json",
            str(video_path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    payload = json.loads(result.stdout)
    streams = payload.get("streams") or []
    if not streams:
        raise ValueError(f"no video stream found: {video_path}")
    stream = streams[0]
    frame_pts = [
        pts_us
        for frame in payload.get("frames", [])
        for pts_us in [_frame_pts_us(frame)]
        if pts_us is not None
    ]
    duration_us = int(round(float(stream.get("duration") or 0) * 1_000_000))
    if duration_us <= 0 and frame_pts:
        duration_us = max(frame_pts) + max(1, int(round(1_000_000 / fps)))
    if duration_us <= 0:
        raise ValueError(f"could not determine video duration: {video_path}")
    source_fps = _parse_ratio(stream.get("avg_frame_rate")) or _parse_ratio(stream.get("r_frame_rate")) or fps
    return {
        "width": int(stream.get("width") or 1),
        "height": int(stream.get("height") or 1),
        "target_fps": int(round(source_fps)) if source_fps > 0 else fps,
        "duration_us": duration_us,
        "codec": stream.get("codec_name") or "unknown",
        "bitrate_bps": max(1, int(stream.get("bit_rate") or 1)),
        "frames": _sample_frame_timestamps(frame_pts, fps, duration_us),
    }


def _frames_with_extracted_images(frames: list[FrameTimestamp], extracted: list[Path]) -> list[FrameTimestamp]:
    available_indexes = {int(path.stem.rsplit("_", 1)[-1]) for path in extracted if path.exists()}
    return [frame for frame in frames if frame.frame_index in available_indexes]


def _sensor_flags_by_frame(windows: list[SensorWindow]) -> dict[int, list[str]]:
    return {window.frame_index: window.flags for window in windows}


def _without_missing_metadata_flags(windows: list[SensorWindow]) -> list[SensorWindow]:
    for window in windows:
        window.flags = [flag for flag in window.flags if flag != "metadata_missing"]
    return windows


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
    extraction_fps: int | None = None,
    extract_log_path: Path | None = None,
    suppress_missing_metadata: bool = False,
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
    extracted = _extract_frames(
        extractor,
        raw_dir / "video.mp4",
        frames_dir,
        len(frames),
        fps=extraction_fps,
        log_path=extract_log_path,
    )
    frames = _frames_with_extracted_images(frames, extracted)
    if not frames:
        raise ValueError("frame extractor did not create any usable frames")

    windows = build_sensor_windows(frames, imu_samples, camera_samples, events)
    if suppress_missing_metadata:
        windows = _without_missing_metadata_flags(windows)
    candidates = _build_candidates(frames, frames_dir, windows)
    decisions = select_keyframes(candidates, max_frames=max_frames, min_time_distance_ns=min_time_distance_ns)

    write_jsonl(normalized_dir / "sensor_windows.jsonl", [asdict(window) for window in windows])
    write_jsonl(normalized_dir / "frame_decisions.jsonl", decisions)
    return normalized_dir


def _write_no_sensor_capture(video_path: Path, capture_root: Path, job_id: str, fps: int, probe_video: VideoProbe) -> Path:
    raw_dir = capture_root / "raw"
    reports_dir = capture_root / "reports"
    if capture_root.exists():
        shutil.rmtree(capture_root)
    raw_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    shutil.copy2(video_path, raw_dir / "video.mp4")

    probe = probe_video(video_path, fps)
    frames = probe["frames"]
    if len(frames) < 2:
        raise ValueError(f"Need at least 2 sampled frames for COLMAP, got {len(frames)}")

    metadata = CaptureMetadata(
        schema_version="1.0",
        capture_id=capture_root.name,
        app_version="process-video",
        platform="video",
        device_manufacturer="unknown",
        device_model="unknown",
        android_api_level=0,
        camera_id="unknown",
        lens_facing="unknown",
        sensor_orientation_degrees=0,
        video_width=int(probe["width"]),
        video_height=int(probe["height"]),
        target_fps=int(probe["target_fps"]),
        actual_video_duration_us=int(probe["duration_us"]),
        video_codec=str(probe["codec"]),
        bitrate_bps=int(probe["bitrate_bps"]),
        started_monotonic_ns=0,
        stopped_monotonic_ns=int(probe["duration_us"]) * 1_000,
    )
    (raw_dir / "metadata.json").write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")
    write_jsonl(raw_dir / "frame_timestamps.jsonl", frames)
    write_jsonl(raw_dir / "camera_samples.jsonl", [])
    write_jsonl(raw_dir / "imu_samples.jsonl", [])
    write_jsonl(
        raw_dir / "events.jsonl",
        [
            CaptureEvent(
                timestamp_ns=0,
                type="video_imported_without_sensors",
                message=f"process-video imported {video_path.name} for job {job_id}",
            )
        ],
    )
    (reports_dir / "import_report.json").write_text(
        json.dumps(
            {
                "capture_id": capture_root.name,
                "warnings": ["sensor streams unavailable; frame selection used image quality and timing only"],
                "errors": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return capture_root


def process_video_to_job(
    video_path: Path,
    captures_root: Path,
    jobs_root: Path,
    *,
    job_id: str,
    fps: int,
    max_frames: int,
    min_time_distance_ns: int = 100_000_000,
    probe_video: VideoProbe = probe_video_for_capture,
    frame_extractor: FrameExtractor | None = None,
    extract_log_path: Path | None = None,
) -> Path:
    capture_root = Path(captures_root) / f"video_{job_id}"
    _write_no_sensor_capture(Path(video_path), capture_root, job_id, fps, probe_video)
    prepare_capture_for_selection(
        capture_root,
        max_frames=max_frames,
        min_time_distance_ns=min_time_distance_ns,
        frame_extractor=frame_extractor,
        extraction_fps=fps,
        extract_log_path=extract_log_path,
        suppress_missing_metadata=True,
    )
    return create_job_from_capture(capture_root, jobs_root, job_id=job_id, max_frames=max_frames)


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
