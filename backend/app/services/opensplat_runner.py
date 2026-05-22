from pathlib import Path

from app.config import OPENSPLAT_DOCKER_IMAGE
from app.services import storage
from app.services.process_runner import run_command


def _docker_mount_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def run_opensplat(job_id: str, iterations: int) -> Path:
    output_path = storage.job_opensplat_dir(job_id) / "splat.ply"
    storage.job_opensplat_dir(job_id).mkdir(parents=True, exist_ok=True)

    run_command(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{_docker_mount_path(storage.job_dir(job_id))}:/work",
            OPENSPLAT_DOCKER_IMAGE,
            "--cpu",
            "-n",
            str(iterations),
            "-o",
            "/work/opensplat/splat.ply",
            "--colmap-image-path",
            "/work/images",
            "/work/colmap",
        ],
        storage.job_logs_dir(job_id) / "opensplat.log",
    )

    if not output_path.exists():
        raise RuntimeError(f"OpenSplat output not found: {output_path}")
    return output_path

