from pathlib import Path

from PIL import Image

from packages.capture_schema.jsonl import read_jsonl, write_jsonl
from packages.capture_schema.models import CameraSample, CaptureEvent, FrameTimestamp, ImuSample
from packages.pipeline.__main__ import main
from packages.pipeline.prepare_capture import (
    prepare_and_create_job,
    prepare_capture_for_selection,
    process_video_to_job,
)


def _write_image(path: Path, pixels: list[list[int]]) -> None:
    image = Image.new("L", (len(pixels[0]), len(pixels)))
    image.putdata([value for row in pixels for value in row])
    image.save(path)


def test_prepare_capture_extracts_frames_scores_and_attaches_sensor_windows(tmp_path):
    capture_root = tmp_path / "captures" / "capture_001"
    raw_dir = capture_root / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "video.mp4").write_bytes(b"fake video")
    write_jsonl(
        raw_dir / "frame_timestamps.jsonl",
        [
            FrameTimestamp(frame_index=0, pts_us=0, sensor_timestamp_ns=1_000),
            FrameTimestamp(frame_index=1, pts_us=33_333, sensor_timestamp_ns=34_333_000),
            FrameTimestamp(frame_index=2, pts_us=200_000, sensor_timestamp_ns=200_000_000),
        ],
    )
    write_jsonl(
        raw_dir / "camera_samples.jsonl",
        [
            CameraSample(sensor_timestamp_ns=1_000, exposure_time_ns=8_000_000, iso=400),
            CameraSample(sensor_timestamp_ns=34_333_000, exposure_time_ns=8_000_000, iso=400),
        ],
    )
    write_jsonl(
        raw_dir / "imu_samples.jsonl",
        [
            ImuSample(type="gyro", timestamp_ns=1_000, x=0.0, y=0.0, z=0.1),
            ImuSample(type="accelerometer", timestamp_ns=1_000, x=0.0, y=0.0, z=9.8),
            ImuSample(type="rotation_vector", timestamp_ns=1_000, x=0.0, y=0.0, z=0.0, w=1.0),
            ImuSample(type="gyro", timestamp_ns=200_000_000, x=6.0, y=0.0, z=0.0),
        ],
    )
    write_jsonl(raw_dir / "events.jsonl", [CaptureEvent(timestamp_ns=200_000_000, type="focus_jump")])

    def fake_extractor(video_path: Path, frames_dir: Path, frame_count: int) -> list[Path]:
        assert video_path == raw_dir / "video.mp4"
        frames_dir.mkdir(parents=True, exist_ok=True)
        paths = [frames_dir / f"frame_{index:06d}.jpg" for index in range(frame_count)]
        _write_image(paths[0], [[0, 255, 0], [255, 128, 255], [0, 255, 0]])
        _write_image(paths[1], [[128, 128, 128], [128, 128, 128], [128, 128, 128]])
        _write_image(paths[2], [[0, 255, 0], [255, 128, 255], [0, 255, 0]])
        return paths

    prepare_capture_for_selection(capture_root, max_frames=2, frame_extractor=fake_extractor)

    assert (capture_root / "normalized" / "frames" / "frame_000000.jpg").exists()
    sensor_windows = read_jsonl(capture_root / "normalized" / "sensor_windows.jsonl")
    decisions = read_jsonl(capture_root / "normalized" / "frame_decisions.jsonl")
    assert len(sensor_windows) == 3
    assert sensor_windows[2]["flags"] == ["fast_rotation", "focus_jump_nearby", "metadata_missing"]
    assert [decision["frame_index"] for decision in decisions] == [0, 1, 2]
    assert decisions[0]["selected"] is True
    assert "blur" in decisions[1]["reasons"]
    assert "fast_rotation" in decisions[2]["reasons"]


def test_prepare_capture_trims_estimated_timestamps_to_extracted_frames(tmp_path):
    capture_root = tmp_path / "captures" / "capture_001"
    raw_dir = capture_root / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "video.mp4").write_bytes(b"fake video")
    write_jsonl(
        raw_dir / "frame_timestamps.jsonl",
        [
            FrameTimestamp(frame_index=0, pts_us=0, sensor_timestamp_ns=1_000),
            FrameTimestamp(frame_index=1, pts_us=33_333, sensor_timestamp_ns=34_333_000),
            FrameTimestamp(frame_index=2, pts_us=66_666, sensor_timestamp_ns=67_666_000),
        ],
    )
    write_jsonl(raw_dir / "camera_samples.jsonl", [CameraSample(sensor_timestamp_ns=1_000)])
    write_jsonl(raw_dir / "imu_samples.jsonl", [ImuSample(type="gyro", timestamp_ns=1_000, x=0.0, y=0.0, z=0.1)])
    write_jsonl(raw_dir / "events.jsonl", [])

    def short_extractor(video_path: Path, frames_dir: Path, frame_count: int) -> list[Path]:
        frames_dir.mkdir(parents=True, exist_ok=True)
        paths = [frames_dir / "frame_000000.jpg", frames_dir / "frame_000001.jpg"]
        _write_image(paths[0], [[0, 255, 0], [255, 128, 255], [0, 255, 0]])
        _write_image(paths[1], [[0, 255, 0], [255, 128, 255], [0, 255, 0]])
        return paths

    prepare_capture_for_selection(capture_root, max_frames=2, frame_extractor=short_extractor)

    decisions = read_jsonl(capture_root / "normalized" / "frame_decisions.jsonl")
    windows = read_jsonl(capture_root / "normalized" / "sensor_windows.jsonl")
    assert [decision["frame_index"] for decision in decisions] == [0, 1]
    assert [window["frame_index"] for window in windows] == [0, 1]


def test_pipeline_cli_exposes_prepare_capture_command(capsys, monkeypatch, tmp_path):
    capture_root = tmp_path / "capture_001"

    def fake_prepare_capture_for_selection(*, capture_root_arg, max_frames_arg):
        assert capture_root_arg == capture_root
        assert max_frames_arg == 700
        return capture_root / "normalized"

    monkeypatch.setattr(
        "packages.pipeline.__main__.prepare_capture_for_selection",
        lambda capture_root, max_frames: fake_prepare_capture_for_selection(
            capture_root_arg=capture_root,
            max_frames_arg=max_frames,
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["python -m packages.pipeline", "prepare-capture", str(capture_root), "--max-frames", "700"],
    )

    main()

    assert f"prepared capture: {capture_root / 'normalized'}" in capsys.readouterr().out


def test_prepare_and_create_job_runs_full_host_selection_pipeline(tmp_path):
    capture_root = tmp_path / "captures" / "capture_001"
    raw_dir = capture_root / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "video.mp4").write_bytes(b"fake video")
    write_jsonl(
        raw_dir / "frame_timestamps.jsonl",
        [
            FrameTimestamp(frame_index=0, pts_us=0, sensor_timestamp_ns=1_000),
            FrameTimestamp(frame_index=1, pts_us=200_000, sensor_timestamp_ns=200_000_000),
        ],
    )
    write_jsonl(raw_dir / "camera_samples.jsonl", [CameraSample(sensor_timestamp_ns=1_000)])
    write_jsonl(raw_dir / "imu_samples.jsonl", [ImuSample(type="gyro", timestamp_ns=1_000, x=0.0, y=0.0, z=0.1)])
    write_jsonl(raw_dir / "events.jsonl", [])

    def fake_extractor(video_path: Path, frames_dir: Path, frame_count: int) -> list[Path]:
        frames_dir.mkdir(parents=True, exist_ok=True)
        paths = [frames_dir / f"frame_{index:06d}.jpg" for index in range(frame_count)]
        _write_image(paths[0], [[0, 255, 0], [255, 128, 255], [0, 255, 0]])
        _write_image(paths[1], [[128, 128, 128], [128, 128, 128], [128, 128, 128]])
        return paths

    job_root = prepare_and_create_job(
        capture_root,
        tmp_path / "jobs",
        job_id="job_capture_001",
        max_frames=1,
        frame_extractor=fake_extractor,
    )

    assert (job_root / "images" / "frame_000000.jpg").exists()
    assert (job_root / "capture" / "selected_frames.jsonl").exists()
    assert read_jsonl(job_root / "capture" / "selected_frames.jsonl")[0]["frame_index"] == 0


def test_process_video_to_job_creates_no_sensor_capture_and_selected_job(tmp_path):
    source_video = tmp_path / "input.mp4"
    source_video.write_bytes(b"fake video")

    def fake_probe(video_path: Path, fps: int):
        assert video_path == source_video
        assert fps == 2
        return {
            "width": 1920,
            "height": 1080,
            "target_fps": 2,
            "duration_us": 1_000_000,
            "codec": "h264",
            "bitrate_bps": 4_000_000,
            "frames": [
                FrameTimestamp(frame_index=0, pts_us=0, monotonic_ns=0),
                FrameTimestamp(frame_index=1, pts_us=500_000, monotonic_ns=500_000_000),
                FrameTimestamp(frame_index=2, pts_us=1_000_000, monotonic_ns=1_000_000_000),
            ],
        }

    def fake_extractor(video_path: Path, frames_dir: Path, frame_count: int, fps: int | None = None) -> list[Path]:
        assert video_path.name == "video.mp4"
        assert frame_count == 3
        assert fps == 2
        frames_dir.mkdir(parents=True, exist_ok=True)
        paths = [frames_dir / f"frame_{index:06d}.jpg" for index in range(frame_count)]
        _write_image(paths[0], [[0, 255, 0], [255, 128, 255], [0, 255, 0]])
        _write_image(paths[1], [[255, 0, 255], [0, 128, 0], [255, 0, 255]])
        _write_image(paths[2], [[0, 0, 255], [255, 128, 0], [0, 255, 0]])
        return paths

    job_root = process_video_to_job(
        source_video,
        tmp_path / "captures",
        tmp_path / "jobs",
        job_id="job_video_001",
        fps=2,
        max_frames=2,
        probe_video=fake_probe,
        frame_extractor=fake_extractor,
    )

    capture_root = tmp_path / "captures" / "video_job_video_001"
    assert (capture_root / "raw" / "video.mp4").read_bytes() == b"fake video"
    assert read_jsonl(capture_root / "raw" / "imu_samples.jsonl") == []
    assert read_jsonl(capture_root / "raw" / "camera_samples.jsonl") == []
    assert read_jsonl(capture_root / "raw" / "frame_timestamps.jsonl")[1]["pts_us"] == 500_000
    assert (job_root / "capture" / "selected_frames.jsonl").exists()
    assert len(list((job_root / "images").glob("*.jpg"))) == 2
    assert read_jsonl(capture_root / "normalized" / "frame_decisions.jsonl")[0]["reasons"] == ["selected"]
