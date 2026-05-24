# 3DGS CUDA-Only Quick Start

This workspace is now organized for NVIDIA GPU hosts only. The active runtime is under `apps/api`, CUDA operations live in `scripts/ops`, and historical CPU prototype assets are kept under `scripts/legacy` and `docker/legacy`.

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

## 2. Check The Host

```powershell
.\scripts\ops\check_environment.ps1
```

## 3. Build CUDA OpenSplat Image

From the project root:

```powershell
.\scripts\ops\build_opensplat_cuda_docker.ps1 `
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

## 4. Re-run Only OpenSplat CUDA With Existing COLMAP

Use this when `data\jobs\<job_id>\images` and `data\jobs\<job_id>\colmap` already exist:

```powershell
.\scripts\ops\run_opensplat_cuda_only.ps1 `
  -JobId job_cuda_001 `
  -Iterations 4000 `
  -OpenSplatDownscaleFactor 2 `
  -OpenSplatNumDownscales 2 `
  -ImageName opensplat-cuda:local
```

## 5. Start Web API And Viewer

Install Python dependencies:

```powershell
pip install -r apps\api\requirements.txt
```

Start the API and viewer:

```powershell
.\scripts\ops\run_api.ps1
```

Open:

```text
http://127.0.0.1:8000/jobs/<job_id>/metrics-view
http://127.0.0.1:8000/scenes/<scene_id>/viewer
```

If you trained from the command line and need to export a scene manually:

```powershell
$env:PYTHONPATH="$PWD\apps\api"
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

## 6. Package For A GPU Host

```powershell
.\scripts\ops\package_cuda_release.ps1
```

## 7. Important Notes

- CPU execution is no longer an active path in this workspace.
- The API still exposes the current web upload, metrics, and viewer surfaces while the training backend is being moved toward Nerfstudio Splatfacto.
- The package does not include `data\jobs`, videos, Docker layers, or Git metadata.
- Detailed migration notes live in `docs\cuda-migration.md`.
