import json

from packages.capture_schema.jsonl import write_jsonl
from packages.frame_select.selection import FrameDecision
from packages.pipeline.capture_to_job import create_job_from_capture


def test_create_job_from_capture_writes_selected_images_and_reports(tmp_path):
    capture_root = tmp_path / "captures" / "capture_001"
    frames_dir = capture_root / "normalized" / "frames"
    frames_dir.mkdir(parents=True)
    (frames_dir / "frame_000000.jpg").write_bytes(b"frame0")
    (frames_dir / "frame_000001.jpg").write_bytes(b"frame1")
    (frames_dir / "frame_000002.jpg").write_bytes(b"frame2")
    write_jsonl(
        capture_root / "normalized" / "frame_decisions.jsonl",
        [
            FrameDecision(frame_index=0, timestamp_ns=0, selected=True, score=0.9, reasons=["selected"]),
            FrameDecision(frame_index=1, timestamp_ns=33, selected=False, score=0.1, reasons=["blur"]),
            FrameDecision(frame_index=2, timestamp_ns=66, selected=True, score=0.8, reasons=["selected"]),
        ],
    )
    (capture_root / "reports").mkdir()
    (capture_root / "reports" / "import_report.json").write_text(
        json.dumps({"capture_id": "capture_001", "warnings": [], "errors": []}),
        encoding="utf-8",
    )
    jobs_root = tmp_path / "jobs"

    job_root = create_job_from_capture(capture_root, jobs_root, job_id="job_capture_001", max_frames=2)

    assert (job_root / "images" / "frame_000000.jpg").read_bytes() == b"frame0"
    assert (job_root / "images" / "frame_000002.jpg").read_bytes() == b"frame2"
    assert not (job_root / "images" / "frame_000001.jpg").exists()
    assert (job_root / "capture" / "selected_frames.jsonl").exists()
    assert (job_root / "capture" / "frame_scores.jsonl").exists()
    assert (job_root / "capture" / "sensor_windows.jsonl").exists()
    assert (job_root / "capture" / "import_report.json").exists()


def test_create_job_from_capture_preserves_existing_job_metadata_and_input(tmp_path):
    capture_root = tmp_path / "captures" / "capture_001"
    frames_dir = capture_root / "normalized" / "frames"
    frames_dir.mkdir(parents=True)
    (frames_dir / "frame_000000.jpg").write_text("frame", encoding="utf-8")
    write_jsonl(
        capture_root / "normalized" / "frame_decisions.jsonl",
        [FrameDecision(frame_index=0, timestamp_ns=0, selected=True, score=0.9, reasons=["selected"])],
    )

    job_root = tmp_path / "jobs" / "job_capture_001"
    (job_root / "input").mkdir(parents=True)
    (job_root / "input" / "input.mp4").write_text("video", encoding="utf-8")
    (job_root / "job.json").write_text('{"id":"job_capture_001"}', encoding="utf-8")

    create_job_from_capture(capture_root, tmp_path / "jobs", job_id="job_capture_001", max_frames=1)

    assert (job_root / "job.json").read_text(encoding="utf-8") == '{"id":"job_capture_001"}'
    assert (job_root / "input" / "input.mp4").read_text(encoding="utf-8") == "video"
    assert (job_root / "images" / "frame_000000.jpg").exists()
