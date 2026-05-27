#!/usr/bin/env bash
set -euo pipefail

mkdir -p /data/3dgs/logs

docker run --rm \
  --name 3dgs-train-test1 \
  --gpus '"device=4,5,6,7"' \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
  -e PYTHONPATH=/workspace/apps/api \
  -v /data/3dgs/repo:/workspace \
  -v /data/3dgs/logs:/logs \
  -w /workspace \
  3dgs-runtime:rtx5090 \
  bash -lc 'python - <<PY 2>&1 | tee /logs/test1-run.log
from app.services.job_runner import run_job
run_job("test1")
PY'
