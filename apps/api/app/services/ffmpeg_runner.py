from pathlib import Path

from app.config import FFMPEG_CMD
from app.services import storage
from app.services.process_runner import run_command


def _limit_frames(images_dir: Path, max_frames: int) -> int:
    frames = sorted(images_dir.glob("*.jpg"))
    if len(frames) <= max_frames:
        return len(frames)

    for frame in frames[max_frames:]:
        frame.unlink()
    return max_frames


def extract_frames(job_id: str, fps: int, max_frames: int) -> int:
    input_video = storage.job_input_dir(job_id) / "input.mp4"
    images_dir = storage.job_images_dir(job_id)
    images_dir.mkdir(parents=True, exist_ok=True)

    run_command(
        [
            FFMPEG_CMD,
            "-y",
            "-i",
            str(input_video),
            "-vf",
            f"fps={fps}",
            str(images_dir / "frame_%06d.jpg"),
        ],
        storage.job_logs_dir(job_id) / "extract_frames.log",
    )

    frame_count = _limit_frames(images_dir, max_frames)
    if frame_count < 2:
        raise RuntimeError(f"Need at least 2 frames for COLMAP, got {frame_count}")
    return frame_count

