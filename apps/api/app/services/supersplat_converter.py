import os
import shlex
from pathlib import Path

from app.services import process_runner

DEFAULT_SPLAT_TRANSFORM_COMMAND = "npx --yes @playcanvas/splat-transform@2.4.0"
NERFSTUDIO_TO_SUPERSPLAT_ROTATION = "180,0,0"


def _command_prefix() -> list[str]:
    return shlex.split(os.environ.get("SPLAT_TRANSFORM_COMMAND", DEFAULT_SPLAT_TRANSFORM_COMMAND))


def convert_to_supersplat(source_ply: Path, target_dir: Path, log_path: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "scene.sog"
    base_args = [
        *_command_prefix(),
        "-w",
        str(source_ply),
        "--filter-nan",
        "-r",
        NERFSTUDIO_TO_SUPERSPLAT_ROTATION,
    ]
    process_runner.run_command([*base_args, str(target_path)], log_path)

    viewer_path = target_dir / "supersplat.html"
    process_runner.run_command([*base_args, str(viewer_path)], log_path)

    if not target_path.exists():
        raise RuntimeError(f"SuperSplat conversion did not create output: {target_path}")
    if not viewer_path.exists():
        raise RuntimeError(f"SuperSplat conversion did not create viewer: {viewer_path}")
    return target_path
