from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
SCENES_DIR = DATA_DIR / "scenes"

FFMPEG_CMD = "ffmpeg"
COLMAP_CMD = "colmap"
NERFSTUDIO_PROCESS_CMD = "ns-process-data"
NERFSTUDIO_CMD = "ns-train"
NERFSTUDIO_EXPORT_CMD = "ns-export"
SPLATFACTO_METHOD = "splatfacto"
NERFSTUDIO_DOCKER_IMAGE = "nerfstudio-splatfacto:local"
