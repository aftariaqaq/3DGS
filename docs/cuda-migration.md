# CUDA Migration Package

This project is organized as a CUDA-only Nerfstudio + Splatfacto workspace. Use an NVIDIA GPU host for COLMAP feature extraction, matching, sparse mapping, and Splatfacto training.

## Host Requirements

- NVIDIA driver with `nvidia-smi` working.
- Python environment with CUDA-enabled PyTorch.
- Nerfstudio command line tools: `ns-train` and `ns-export`.
- FFmpeg and COLMAP.
- Optional Docker with NVIDIA Container Toolkit.

For RTX 5090 / Blackwell, validate PyTorch CUDA support before starting a long run:

```powershell
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
ns-train splatfacto --help
ns-export gaussian-splat --help
```

## Active Workspace Layout

- `apps/api`: FastAPI API, job orchestration, metrics view, and 3DGS viewer.
- `apps/capture-android`: Android capture app for video, IMU, and metadata collection.
- `packages/frame_select`: frame extraction and selection boundary.
- `packages/colmap_cuda`: CUDA COLMAP boundary.
- `packages/splatfacto`: Nerfstudio Splatfacto boundary.
- `packages/pipeline`: capture import and selected-frame job preparation.
- `packages/viewer`: browser viewer boundary.
- `scripts/ops`: supported CUDA operations.
- `scripts/legacy` and `docker/legacy`: historical prototype assets only.

## Optional Docker Image

```powershell
docker build `
  -f docker\nerfstudio-splatfacto.Dockerfile `
  -t nerfstudio-splatfacto:local `
  .
```

## Reuse Existing COLMAP And Train Splatfacto

If a job already has `data/jobs/<job_id>/images` and `data/jobs/<job_id>/colmap/sparse/0`, skip FFmpeg and COLMAP:

```powershell
.\scripts\ops\run_splatfacto_cuda.ps1 `
  -JobId job_quality_006 `
  -Iterations 25000
```

Docker mode:

```powershell
.\scripts\ops\run_splatfacto_cuda.ps1 `
  -JobId job_quality_006 `
  -Iterations 25000 `
  -UseDocker
```

Expected training outputs:

```text
data/jobs/<job_id>/nerfstudio/outputs/**/config.yml
data/jobs/<job_id>/nerfstudio/exports/*.ply
data/jobs/<job_id>/logs/splatfacto.log
data/jobs/<job_id>/logs/splatfacto-export.log
```

## Start Web Backend

```powershell
$env:PYTHONPATH='D:\path\to\3DGS\apps\api'
pip install -r apps\api\requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Useful URLs:

```text
http://127.0.0.1:8000/jobs/<job_id>/metrics-view
http://127.0.0.1:8000/scenes/<scene_id>/viewer
```

## Create A Portable Zip

```powershell
.\scripts\ops\package_cuda_release.ps1
```

The package includes source, apps, package boundaries, Dockerfiles, scripts, tests, and docs. It intentionally excludes `data/jobs`, test videos, local Docker layers, Git metadata, build outputs, and caches.
