from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = ROOT_DIR
DATA_DIR = PROJECT_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
SCENES_DIR = DATA_DIR / "scenes"

FFMPEG_CMD = "ffmpeg"
COLMAP_CMD = "colmap"
OPENSPLAT_CMD = "opensplat.exe"
OPENSPLAT_DOCKER_IMAGE = "opensplat-cpu:local"
