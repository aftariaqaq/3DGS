# 3DGS CUDA Migration Quick Start

This package is for moving the current OpenSplat + web viewer workflow to a machine with an NVIDIA GPU.

## 1. Required Host Software

Install these on the target machine before running the pipeline:

- NVIDIA driver. `nvidia-smi` must work in a terminal.
- Docker Desktop or Docker Engine.
- NVIDIA Container Toolkit. Docker must support `docker run --gpus all ...`.
- FFmpeg.
- COLMAP.
- Python 3.12 or a compatible Python 3 version.

Quick checks:

```powershell
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
ffmpeg -version
colmap -h
python --version
```

## 2. Build CUDA OpenSplat Image

From the project root:

```powershell
.\scripts\build_opensplat_cuda_docker.ps1 `
  -ImageName opensplat-cuda:local `
  -CudaVersion 12.1.1 `
  -TorchVersion 2.2.1 `
  -CudaArchitectures "75;80;86;89"
```

CUDA architecture hints:

```text
RTX 20xx / Turing: 75
RTX 30xx / Ampere: 86
A100 / Ampere datacenter: 80
RTX 40xx / Ada: 89
H100 / Hopper: 90
```

Use a semicolon-separated list if you want the image to support multiple GPU families.

## 3. Run Full Video-to-3DGS Pipeline

Example for the current long test video style:

```powershell
.\scripts\run_pipeline_test.ps1 `
  -InputVideo 'D:\path\to\test2.mp4' `
  -JobId job_cuda_001 `
  -Fps 15 `
  -MaxFrames 1000 `
  -Iterations 4000 `
  -OpenSplatDownscaleFactor 2 `
  -OpenSplatNumDownscales 2 `
  -OpenSplatDockerImage opensplat-cuda:local `
  -OpenSplatUseGpu
```

For smaller GPUs, start safer:

```powershell
.\scripts\run_pipeline_test.ps1 `
  -InputVideo 'D:\path\to\test2.mp4' `
  -JobId job_cuda_safe_001 `
  -Fps 10 `
  -MaxFrames 700 `
  -Iterations 3000 `
  -OpenSplatDownscaleFactor 4 `
  -OpenSplatNumDownscales 2 `
  -OpenSplatDockerImage opensplat-cuda:local `
  -OpenSplatUseGpu
```

## 4. Re-run Only OpenSplat With Existing COLMAP

Use this when `data\jobs\<job_id>\images` and `data\jobs\<job_id>\colmap` already exist:

```powershell
.\scripts\run_opensplat_cuda_only.ps1 `
  -JobId job_cuda_001 `
  -Iterations 4000 `
  -OpenSplatDownscaleFactor 2 `
  -OpenSplatNumDownscales 2 `
  -ImageName opensplat-cuda:local
```

## 5. Start Web Backend

Install Python dependencies:

```powershell
pip install -r backend\requirements.txt
```

Start the API and viewer:

```powershell
$env:PYTHONPATH="$PWD\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/jobs/<job_id>/metrics-view
http://127.0.0.1:8000/scenes/<scene_id>/viewer
```

If you trained from the command line and need to export a scene manually:

```powershell
$env:PYTHONPATH="$PWD\backend"
@'
from app.services import model_exporter
scene = model_exporter.export_scene("job_cuda_001", scene_id="scene_job_cuda_001", frame_count=1000)
print(scene)
'@ | python -
```

Then open:

```text
http://127.0.0.1:8000/scenes/scene_job_cuda_001/viewer
```

## 6. Important Notes

- CPU runs already failed with exit `137` for high frame counts at `downscale=2`; use CUDA for those settings.
- `run_pipeline_test.ps1` now samples frames evenly across the whole video when `MaxFrames` is lower than extracted candidates.
- The package does not include `data\jobs`, videos, Docker layers, or Git metadata.
- Detailed migration notes live in `docs\cuda-migration.md`.
