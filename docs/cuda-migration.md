# CUDA Migration Package

This project is now organized as a CUDA-only workspace. Use an NVIDIA GPU host for COLMAP feature extraction, matching, and splat training.

## Host Requirements

- NVIDIA driver with `nvidia-smi` working on the host.
- Docker with NVIDIA Container Toolkit enabled.
- FFmpeg and COLMAP available if you want to run the full video-to-COLMAP pipeline on the GPU host.
- Python 3.12 or compatible Python for the FastAPI backend.

OpenSplat's upstream CUDA build requires CUDA and a CUDA-matched LibTorch package. The Dockerfile in this package follows the upstream CUDA Docker build pattern with CUDA `12.1.1`, LibTorch `2.2.1`, and configurable CUDA architectures.

## Build OpenSplat CUDA Image

```powershell
.\scripts\ops\build_opensplat_cuda_docker.ps1 `
  -ImageName opensplat-cuda:local `
  -CudaVersion 12.1.1 `
  -TorchVersion 2.2.1 `
  -CudaArchitectures "75;80;86;89"
```

Choose CUDA architectures for your NVIDIA GPU:

```text
Turing RTX 20xx: 75
Ampere RTX 30xx / A-series: 80;86
Ada RTX 40xx / L4: 89
Hopper H100: 90
Blackwell RTX 50xx: 120
```

If you are unsure, keep the default `"75;80;86;89"` for a broad modern build. It takes longer to compile but is portable across common RTX hosts.

## Active Workspace Layout

- `apps/api`: FastAPI API, job orchestration, metrics view, and 3DGS viewer.
- `packages/frame_select`: frame extraction and selection boundary.
- `packages/colmap_cuda`: CUDA COLMAP boundary.
- `packages/splatfacto`: Nerfstudio Splatfacto boundary.
- `packages/pipeline`: end-to-end job orchestration boundary.
- `packages/viewer`: browser viewer boundary.
- `scripts/ops`: supported CUDA operations.
- `scripts/legacy` and `docker/legacy`: historical CPU prototype assets.

## Reuse Existing COLMAP and Re-run CUDA OpenSplat

If a job already has `data/jobs/<job_id>/images` and `data/jobs/<job_id>/colmap`, skip FFmpeg and COLMAP:

```powershell
.\scripts\ops\run_opensplat_cuda_only.ps1 `
  -JobId job_quality_006 `
  -Iterations 2500 `
  -OpenSplatDownscaleFactor 2 `
  -OpenSplatNumDownscales 2 `
  -ImageName opensplat-cuda:local
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

## Create a Portable Zip

```powershell
.\scripts\ops\package_cuda_release.ps1
```

The package includes source, apps, package boundaries, Dockerfiles, scripts, and docs. It intentionally excludes `data/jobs`, test videos, local Docker layers, and Git metadata.
