#!/usr/bin/env bash
set -euo pipefail

docker run --rm \
  --gpus '"device=4,5,6,7"' \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
  -e PYTHONPATH=/workspace/apps/api \
  -v /data/3dgs/repo:/workspace \
  -w /workspace \
  3dgs-runtime:rtx5090 \
  python - <<'PY'
from pathlib import Path
import shutil
from app.services import storage, job_store

job_id = "test1"
video = Path("/workspace/test_video/test1.mp4")

storage.ensure_job_dirs(job_id)
shutil.copy2(video, storage.job_input_dir(job_id) / "input.mp4")
job_store.create_job(job_id, fps=2, max_frames=700, iterations=5000)

print("created:", storage.job_dir(job_id))
PY
