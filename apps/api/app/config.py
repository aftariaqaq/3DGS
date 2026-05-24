from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
SCENES_DIR = DATA_DIR / "scenes"

FFMPEG_CMD = "ffmpeg"
COLMAP_CMD = "colmap"
NERFSTUDIO_CMD = "ns-train"
SPLATFACTO_METHOD = "splatfacto"
OPENSPLAT_CUDA_DOCKER_IMAGE = "opensplat-cuda:local"
