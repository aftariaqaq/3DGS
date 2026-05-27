#!/usr/bin/env bash
set -euo pipefail

docker run --rm \
  --name 3dgs-api \
  --gpus '"device=4,5,6,7"' \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
  -e PYTHONPATH=/workspace/apps/api \
  -p 8000:8000 \
  -v /data/3dgs/repo:/workspace \
  -w /workspace \
  3dgs-runtime:rtx5090 \
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
