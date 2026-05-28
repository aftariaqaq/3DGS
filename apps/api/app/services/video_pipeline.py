from app.services import storage
from packages.capture_schema.jsonl import read_jsonl
from packages.pipeline.prepare_capture import process_video_to_job


def process_job_video(job_id: str, fps: int, max_frames: int) -> int:
    input_video = storage.job_input_dir(job_id) / "input.mp4"
    captures_root = storage.job_dir(job_id).parent.parent / "captures"
    process_video_to_job(
        input_video,
        captures_root,
        storage.job_dir(job_id).parent,
        job_id=job_id,
        fps=fps,
        max_frames=max_frames,
        extract_log_path=storage.job_logs_dir(job_id) / "extract_frames.log",
    )
    selected = read_jsonl(storage.job_dir(job_id) / "capture" / "selected_frames.jsonl")
    frame_count = len(selected)
    if frame_count < 2:
        raise RuntimeError(f"Need at least 2 selected frames for COLMAP, got {frame_count}")
    return frame_count
