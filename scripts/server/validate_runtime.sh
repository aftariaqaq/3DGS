#!/usr/bin/env bash
set -euo pipefail

docker run --rm \
  --gpus '"device=4,5,6,7"' \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
  3dgs-runtime:rtx5090 \
  bash -lc '
python --version
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())"
ffmpeg -version | head -1
ffprobe -version | head -1
colmap -h >/tmp/colmap-help.txt && echo "colmap ok"
ns-process-data images --help >/tmp/ns-process-data-help.txt && echo "ns-process-data ok"
ns-train splatfacto --help >/tmp/ns-train-help.txt && echo "ns-train splatfacto ok"
ns-export gaussian-splat --help >/tmp/ns-export-help.txt && echo "ns-export gaussian-splat ok"
python -c "import fastapi, uvicorn, httpx, multipart; print(\"api deps ok\")"
'
