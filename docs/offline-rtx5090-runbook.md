# Offline RTX 5090 Server Runbook

Target server:

- Host: `10.143.2.128`
- Work root: `/data/3dgs`
- Runtime image: `3dgs-runtime:rtx5090`
- Runtime archive: `/data/3dgs/3dgs-runtime-rtx5090.tar`
- Physical GPUs: `4,5,6,7`
- Container-visible GPUs: `0,1,2,3`

## 1. Expected Layout

```text
/data/3dgs/
  3dgs-runtime-rtx5090.tar
  logs/
  repo/
    apps/
    docker/
    docs/
    packages/
    scripts/
    tests/
    test_video/test1.mp4
```

## 2. Load Image

```bash
docker load -i /data/3dgs/3dgs-runtime-rtx5090.tar
```

## 3. Validate Runtime

```bash
cd /data/3dgs/repo
bash scripts/server/validate_runtime.sh
```

The validation must report exactly four CUDA devices inside the container.

## 4. Create Or Refresh `test1`

```bash
cd /data/3dgs/repo
bash scripts/server/create_test1_job.sh
```

This creates:

```text
/data/3dgs/repo/data/jobs/test1/input/input.mp4
/data/3dgs/repo/data/jobs/test1/job.json
```

## 5. Start API Monitoring

```bash
cd /data/3dgs/repo
bash scripts/server/run_api.sh
```

Metrics page:

```text
http://10.143.2.128:8000/jobs/test1/metrics-view
```

## 6. Start Training

In another terminal:

```bash
cd /data/3dgs/repo
bash scripts/server/run_train_test1.sh
```

## 7. Monitor GPU Usage

On the host:

```bash
watch -n 2 'nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv | sed -n "1p;6,9p"'
```

The workload must use physical GPUs `4,5,6,7` only.

## 8. Logs

```text
/data/3dgs/repo/data/jobs/test1/logs/extract_frames.log
/data/3dgs/repo/data/jobs/test1/logs/colmap_features.log
/data/3dgs/repo/data/jobs/test1/logs/colmap_matching.log
/data/3dgs/repo/data/jobs/test1/logs/colmap_mapping.log
/data/3dgs/repo/data/jobs/test1/logs/nerfstudio-process-data.log
/data/3dgs/repo/data/jobs/test1/logs/splatfacto.log
/data/3dgs/repo/data/jobs/test1/logs/splatfacto-export.log
/data/3dgs/logs/test1-run.log
```

## 9. Viewer

After export:

```text
http://10.143.2.128:8000/scenes/scene_test1/viewer
```

## 10. Acceptance Checklist

- `docker load` succeeds.
- `scripts/server/validate_runtime.sh` sees exactly four CUDA devices.
- `data/jobs/test1/colmap/sparse/0` exists.
- `data/jobs/test1/nerfstudio/outputs/**/config.yml` exists.
- `data/jobs/test1/nerfstudio/exports/*.ply` exists.
- Metrics page is reachable during training.
- Viewer page is reachable after export.
