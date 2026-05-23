# CUDA Migration Package

This project can run the local web viewer on any machine, while OpenSplat training can be moved to a Linux or WSL2 environment with an NVIDIA GPU.

## Host Requirements

- NVIDIA driver with `nvidia-smi` working on the host.
- Docker with NVIDIA Container Toolkit enabled.
- FFmpeg and COLMAP available if you want to run the full video-to-COLMAP pipeline on the GPU host.
- Python 3.12 or compatible Python for the FastAPI backend.

OpenSplat's upstream CUDA build requires CUDA and a CUDA-matched LibTorch package. The Dockerfile in this package follows the upstream CUDA Docker build pattern with CUDA `12.1.1`, LibTorch `2.2.1`, and configurable CUDA architectures.

## Build OpenSplat CUDA Image

```powershell
.\scripts\build_opensplat_cuda_docker.ps1 `
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

## Run Full Pipeline With CUDA OpenSplat

After building the image, run the existing pipeline with the CUDA image and GPU switch:

```powershell
.\scripts\run_pipeline_test.ps1 `
  -InputVideo 'D:\path\to\video.mp4' `
  -JobId job_cuda_001 `
  -Fps 15 `
  -MaxFrames 700 `
  -Iterations 2500 `
  -OpenSplatDownscaleFactor 2 `
  -OpenSplatNumDownscales 2 `
  -OpenSplatDockerImage opensplat-cuda:local `
  -OpenSplatUseGpu
```

The script extracts candidate frames, evenly samples them down to `MaxFrames`, runs COLMAP, and then starts OpenSplat with Docker `--gpus all`.

## Reuse Existing COLMAP and Re-run CUDA OpenSplat

If a job already has `data/jobs/<job_id>/images` and `data/jobs/<job_id>/colmap`, skip FFmpeg and COLMAP:

```powershell
.\scripts\run_opensplat_cuda_only.ps1 `
  -JobId job_quality_006 `
  -Iterations 2500 `
  -OpenSplatDownscaleFactor 2 `
  -OpenSplatNumDownscales 2 `
  -ImageName opensplat-cuda:local
```

## Start Web Backend

```powershell
$env:PYTHONPATH='D:\path\to\3DGS\backend'
pip install -r backend\requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Useful URLs:

```text
http://127.0.0.1:8000/jobs/<job_id>/metrics-view
http://127.0.0.1:8000/scenes/<scene_id>/viewer
```

## Create a Portable Zip

```powershell
.\scripts\package_cuda_release.ps1
```

The package includes source, backend, Dockerfiles, scripts, and docs. It intentionally excludes `data/jobs`, test videos, local Docker layers, and Git metadata.
