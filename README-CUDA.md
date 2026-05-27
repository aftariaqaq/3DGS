# 3DGS Splatfacto CUDA Quick Start

This workspace targets NVIDIA GPU hosts and uses Nerfstudio + Splatfacto as the only supported 3DGS training backend.

## 1. Pipeline

```text
Android capture or video import
-> frame extraction and quality selection
-> COLMAP CUDA sparse reconstruction
-> ns-train splatfacto
-> ns-export gaussian-splat
-> web metrics and 3DGS viewer
```

## 2. Required Host Software

Install these on the target machine:

- NVIDIA driver. `nvidia-smi` must work.
- Python 3.10-3.12 environment compatible with Nerfstudio.
- PyTorch with CUDA support for the target GPU.
- Nerfstudio with `ns-train` and `ns-export`.
- FFmpeg.
- COLMAP with CUDA support.
- Optional: Docker with NVIDIA Container Toolkit.

Quick checks:

```powershell
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
ffmpeg -version
colmap -h
ns-train splatfacto --help
ns-export gaussian-splat --help
```

For RTX 5090 / Blackwell, prefer a recent NVIDIA driver and a PyTorch CUDA build that explicitly supports the installed driver/runtime combination.

## 3. Check The Host

```powershell
.\scripts\ops\check_environment.ps1
```

## 4. Optional Docker Image

From the project root:

```powershell
docker build `
  -f docker\nerfstudio-splatfacto.Dockerfile `
  -t 3dgs-runtime:rtx5090 `
  .
```

Native Python environments are preferred while validating RTX 5090 compatibility because PyTorch/CUDA support can move faster than project Docker defaults.

## 5. Re-run Splatfacto With Existing COLMAP

Use this when `data\jobs\<job_id>\images` and `data\jobs\<job_id>\colmap\sparse\0` already exist:

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
  -UseDocker `
  -GpuDevices "4,5,6,7"
```

Expected outputs:

```text
data/jobs/<job_id>/nerfstudio/outputs/**/config.yml
data/jobs/<job_id>/nerfstudio/exports/*.ply
data/jobs/<job_id>/logs/splatfacto.log
data/jobs/<job_id>/logs/splatfacto-export.log
```

## 6. Start Web API And Viewer

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
scene = model_exporter.export_scene("job_quality_006", scene_id="scene_job_quality_006", frame_count=700)
print(scene)
'@ | python -
```

Then open:

```text
http://127.0.0.1:8000/scenes/scene_job_quality_006/viewer
```

## 7. Package For A GPU Host

```powershell
.\scripts\ops\package_cuda_release.ps1
```

Build the offline runtime image archive on a machine that can access the selected base image and Python wheels:

```powershell
.\scripts\ops\build_runtime_image.ps1 `
  -ImageName 3dgs-runtime:rtx5090 `
  -TarPath artifacts\3dgs-runtime-rtx5090.tar
```

Create a repo archive for `/data/3dgs/repo`:

```powershell
.\scripts\ops\package_offline_repo.ps1 -IncludeTest1Video
```

The package does not include `data\jobs`, videos, Docker layers, Git metadata, or local caches.

## 8. Notes

- CPU training is not an active path.
- Training quality still depends on capture sharpness, frame selection, and COLMAP pose quality.
- Splatfacto should be initialized from COLMAP/SfM points for this workflow.
- Detailed migration notes live in `docs\cuda-migration.md`.
