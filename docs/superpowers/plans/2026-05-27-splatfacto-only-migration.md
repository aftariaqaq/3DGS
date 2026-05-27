# Splatfacto-Only Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current OpenSplat CUDA training path with a Nerfstudio + Splatfacto-only CUDA workflow, with no supported OpenSplat CUDA runner, Docker image, API path, docs, or packaging entrypoint remaining.

**Architecture:** Keep the existing capture, frame selection, COLMAP, metrics view, and web viewer surfaces, but change the training backend boundary from OpenSplat to Splatfacto. The job layout becomes `data/jobs/<job_id>/nerfstudio/{data,outputs,exports}`; exported viewer assets come from `ns-export gaussian-splat`, not `opensplat/splat.ply`.

**Tech Stack:** Python 3.12, FastAPI, pytest, PowerShell, Docker CUDA, Nerfstudio CLI (`ns-train`, `ns-export`), Splatfacto, COLMAP, GaussianSplats3D-compatible `.ply` export.

---

## Current State Summary

The project currently still has an active OpenSplat path:

- `apps/api/app/services/opensplat_runner.py` runs Docker image `opensplat-cuda:local`.
- `apps/api/app/services/job_runner.py` imports `opensplat_runner` and calls `run_opensplat`.
- `apps/api/app/services/storage.py` creates `job_opensplat_dir`.
- `apps/api/app/services/model_exporter.py` copies `data/jobs/<job_id>/opensplat/splat.ply` into `data/scenes/<scene_id>/scene.ply`.
- `apps/api/app/services/metrics_reader.py` parses `logs/opensplat.log`.
- `scripts/ops/build_opensplat_cuda_docker.ps1` and `scripts/ops/run_opensplat_cuda_only.ps1` are supported CUDA ops.
- `docker/opensplat-cuda.Dockerfile` is a supported Dockerfile.
- `README-CUDA.md`, `docs/cuda-migration.md`, `docker/README.md`, `packages/splatfacto/README.md`, and tests still mention OpenSplat.

The target state is Splatfacto-only:

- Training runs through `ns-train splatfacto --data <nerfstudio-data-dir>`.
- Export runs through `ns-export gaussian-splat --load-config <config.yml> --output-dir <export-dir>`.
- API and scripts expose Splatfacto names only.
- OpenSplat CUDA build/run scripts and Dockerfile are removed.
- The CUDA migration package contains no supported OpenSplat CUDA files.

Official Nerfstudio references used while writing this plan:

- Splatfacto runs with `ns-train splatfacto --data <data>` and exports via `ns-export gaussian-splat --load-config <config> --output-dir exports/splat`.
- Nerfstudio notes that Splatfacto works better when initialized from COLMAP/SfM points.
- `ns-train` custom dataparser args go after the method name; default Nerfstudio data can be passed with `--data`.

---

## File Structure

### Create

- `apps/api/app/services/splatfacto_runner.py`
  - Owns Nerfstudio data staging, `ns-train splatfacto`, export config discovery, and `ns-export gaussian-splat`.
- `apps/api/tests/test_splatfacto_runner.py`
  - Unit tests for command construction, output discovery, and failure behavior.
- `scripts/ops/run_splatfacto_cuda.ps1`
  - Manual GPU-host script for rerunning Splatfacto against an existing job.
- `docker/nerfstudio-splatfacto.Dockerfile`
  - Optional CUDA Docker image for reproducible Nerfstudio/Splatfacto execution.

### Modify

- `apps/api/app/config.py`
  - Remove `OPENSPLAT_CUDA_DOCKER_IMAGE`.
  - Add `NERFSTUDIO_DOCKER_IMAGE = "nerfstudio-splatfacto:local"`.
  - Add `NERFSTUDIO_EXPORT_CMD = "ns-export"`.
- `apps/api/app/services/storage.py`
  - Replace `job_opensplat_dir(job_id)` with `job_nerfstudio_dir(job_id)`, `job_nerfstudio_data_dir(job_id)`, `job_nerfstudio_outputs_dir(job_id)`, and `job_splatfacto_export_dir(job_id)`.
- `apps/api/app/services/job_runner.py`
  - Replace `opensplat_runner.run_opensplat(...)` with `splatfacto_runner.run_splatfacto(...)`.
  - Rename training stage text from `"CUDA splat training"` to `"Splatfacto training"`.
- `apps/api/app/services/model_exporter.py`
  - Read exported Splatfacto `.ply` from `data/jobs/<job_id>/nerfstudio/exports/splat.ply` or `splatfacto.ply`.
  - Error message must mention Splatfacto, not OpenSplat.
- `apps/api/app/services/metrics_reader.py`
  - Parse `logs/splatfacto.log`.
  - Support common Nerfstudio log patterns and a sidecar JSONL metrics format if emitted by our runner.
- `apps/api/tests/test_job_runner.py`
  - Update orchestration expectations from `opensplat_cuda` to `splatfacto`.
- `apps/api/tests/test_model_exporter.py`
  - Update source output path and assertions.
- `apps/api/tests/test_metrics_reader.py`
  - Replace OpenSplat sample logs with Splatfacto/Nerfstudio sample logs.
- `apps/api/tests/test_pipeline_runners.py`
  - Remove OpenSplat runner tests or replace with Splatfacto runner tests.
- `scripts/ops/check_environment.ps1`
  - Remove OpenSplat checks.
  - Add checks for `ns-train`, `ns-export`, CUDA, and optional Docker image.
- `scripts/ops/package_cuda_release.ps1`
  - Ensure removed OpenSplat CUDA files are not packaged.
- `README-CUDA.md`
  - Rewrite sections around Nerfstudio + Splatfacto-only training.
- `docs/cuda-migration.md`
  - Rewrite migration instructions and remove OpenSplat CUDA references.
- `docker/README.md`
  - Point to Nerfstudio/Splatfacto Dockerfile only.
- `packages/splatfacto/README.md`
  - Update from placeholder/fallback wording to primary backend contract.
- `packages/colmap_cuda/README.md`
  - Remove OpenSplat fallback wording.

### Delete

- `apps/api/app/services/opensplat_runner.py`
- `scripts/ops/build_opensplat_cuda_docker.ps1`
- `scripts/ops/run_opensplat_cuda_only.ps1`
- `docker/opensplat-cuda.Dockerfile`

### Leave Historical Only

- `scripts/legacy/*`
- `docker/legacy/opensplat-cpu.Dockerfile`
- `docs/phase-1-verification.md`
- old `docs/superpowers/plans/*opensplat*`

These may mention OpenSplat as history, but they must not be referenced by active docs, packaging instructions, API code, or supported ops scripts.

---

## Task 1: Define Splatfacto Job Storage Boundary

**Files:**
- Modify: `apps/api/app/services/storage.py`
- Modify: `apps/api/tests/test_file_stores.py`

- [ ] **Step 1: Write failing storage tests**

Add tests:

```python
def test_ensure_job_dirs_creates_nerfstudio_dirs(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)

    storage.ensure_job_dirs("job_001")

    assert storage.job_nerfstudio_dir("job_001").is_dir()
    assert storage.job_nerfstudio_data_dir("job_001").is_dir()
    assert storage.job_nerfstudio_outputs_dir("job_001").is_dir()
    assert storage.job_splatfacto_export_dir("job_001").is_dir()
    assert not (storage.job_dir("job_001") / "opensplat").exists()
```

- [ ] **Step 2: Run failing test**

```powershell
$env:PYTHONPATH='D:\.codex_workplace\3DGS\apps\api'
python -m pytest apps/api/tests/test_file_stores.py -q
```

Expected: fail because new storage helpers do not exist.

- [ ] **Step 3: Implement storage helpers**

In `apps/api/app/services/storage.py`, replace:

```python
def job_opensplat_dir(job_id: str) -> Path:
    return job_dir(job_id) / "opensplat"
```

with:

```python
def job_nerfstudio_dir(job_id: str) -> Path:
    return job_dir(job_id) / "nerfstudio"


def job_nerfstudio_data_dir(job_id: str) -> Path:
    return job_nerfstudio_dir(job_id) / "data"


def job_nerfstudio_outputs_dir(job_id: str) -> Path:
    return job_nerfstudio_dir(job_id) / "outputs"


def job_splatfacto_export_dir(job_id: str) -> Path:
    return job_nerfstudio_dir(job_id) / "exports"
```

Update `ensure_job_dirs` to create these directories and no OpenSplat directory.

- [ ] **Step 4: Run storage tests**

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/services/storage.py apps/api/tests/test_file_stores.py
git commit -m "refactor: use nerfstudio job directories"
```

---

## Task 2: Add Splatfacto Runner

**Files:**
- Create: `apps/api/app/services/splatfacto_runner.py`
- Create: `apps/api/tests/test_splatfacto_runner.py`
- Modify: `apps/api/app/config.py`

- [ ] **Step 1: Write failing command construction test**

Create `apps/api/tests/test_splatfacto_runner.py`:

```python
from pathlib import Path

from app.services import splatfacto_runner, storage


def configure_tmp_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(splatfacto_runner.storage, "JOBS_DIR", tmp_path / "jobs")


def test_run_splatfacto_uses_ns_train_and_ns_export(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_images_dir("job_001") / "frame_000001.jpg").write_text("image", encoding="utf-8")
    (storage.job_colmap_dir("job_001") / "sparse" / "0").mkdir(parents=True)
    calls = []

    def fake_run_command(command, log_path):
        calls.append((command, log_path.name))
        if command[0] == "ns-train":
            config = storage.job_nerfstudio_outputs_dir("job_001") / "job_001" / "splatfacto" / "config.yml"
            config.parent.mkdir(parents=True)
            config.write_text("config", encoding="utf-8")
        if command[0] == "ns-export":
            storage.job_splatfacto_export_dir("job_001").mkdir(parents=True, exist_ok=True)
            (storage.job_splatfacto_export_dir("job_001") / "splat.ply").write_text("ply", encoding="utf-8")

    monkeypatch.setattr(splatfacto_runner, "run_command", fake_run_command)

    output = splatfacto_runner.run_splatfacto("job_001", max_num_iterations=2500)

    assert output == storage.job_splatfacto_export_dir("job_001") / "splat.ply"
    assert calls[0][0][:2] == ["ns-train", "splatfacto"]
    assert "--data" in calls[0][0]
    assert "--max-num-iterations" in calls[0][0]
    assert calls[1][0][:2] == ["ns-export", "gaussian-splat"]
    assert "--load-config" in calls[1][0]
```

- [ ] **Step 2: Run failing test**

```powershell
$env:PYTHONPATH='D:\.codex_workplace\3DGS\apps\api'
python -m pytest apps/api/tests/test_splatfacto_runner.py -q
```

Expected: fail because `splatfacto_runner` does not exist.

- [ ] **Step 3: Implement `splatfacto_runner.py`**

Implement:

```python
import shutil
from pathlib import Path

from app import config
from app.services import process_runner, storage

run_command = process_runner.run_command


def _stage_nerfstudio_data(job_id: str) -> Path:
    data_dir = storage.job_nerfstudio_data_dir(job_id)
    images_target = data_dir / "images"
    sparse_target = data_dir / "colmap" / "sparse"
    if images_target.exists():
        shutil.rmtree(images_target)
    if sparse_target.exists():
        shutil.rmtree(sparse_target)
    shutil.copytree(storage.job_images_dir(job_id), images_target)
    shutil.copytree(storage.job_colmap_dir(job_id) / "sparse", sparse_target)
    return data_dir


def _latest_config(outputs_dir: Path) -> Path:
    configs = sorted(outputs_dir.rglob("config.yml"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not configs:
        raise RuntimeError(f"Splatfacto config not found under {outputs_dir}")
    return configs[0]


def _exported_ply(export_dir: Path) -> Path:
    candidates = [export_dir / "splat.ply", export_dir / "splatfacto.ply"]
    candidates.extend(sorted(export_dir.glob("*.ply")))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(f"Splatfacto export not found under {export_dir}")


def run_splatfacto(job_id: str, max_num_iterations: int) -> Path:
    data_dir = _stage_nerfstudio_data(job_id)
    outputs_dir = storage.job_nerfstudio_outputs_dir(job_id)
    export_dir = storage.job_splatfacto_export_dir(job_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    train_command = [
        config.NERFSTUDIO_CMD,
        config.SPLATFACTO_METHOD,
        "--data",
        str(data_dir),
        "--output-dir",
        str(outputs_dir),
        "--experiment-name",
        job_id,
        "--max-num-iterations",
        str(max_num_iterations),
        "--vis",
        "viewer",
    ]
    run_command(train_command, storage.job_logs_dir(job_id) / "splatfacto.log")

    config_path = _latest_config(outputs_dir)
    export_command = [
        config.NERFSTUDIO_EXPORT_CMD,
        "gaussian-splat",
        "--load-config",
        str(config_path),
        "--output-dir",
        str(export_dir),
    ]
    run_command(export_command, storage.job_logs_dir(job_id) / "splatfacto-export.log")
    return _exported_ply(export_dir)
```

Notes:

- Keep Docker support out of the API runner initially; the GPU host can install Nerfstudio natively or use the script in Task 8.
- If Nerfstudio rejects `--max-num-iterations` on the deployed version, run `ns-train splatfacto --help` on the GPU host and adapt the flag in the runner and test together.

- [ ] **Step 4: Add config**

In `apps/api/app/config.py`:

```python
NERFSTUDIO_CMD = "ns-train"
NERFSTUDIO_EXPORT_CMD = "ns-export"
SPLATFACTO_METHOD = "splatfacto"
NERFSTUDIO_DOCKER_IMAGE = "nerfstudio-splatfacto:local"
```

Remove `OPENSPLAT_CUDA_DOCKER_IMAGE`.

- [ ] **Step 5: Run runner tests**

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add apps/api/app/config.py apps/api/app/services/splatfacto_runner.py apps/api/tests/test_splatfacto_runner.py
git commit -m "feat: add splatfacto training runner"
```

---

## Task 3: Replace API Orchestration

**Files:**
- Modify: `apps/api/app/services/job_runner.py`
- Modify: `apps/api/tests/test_job_runner.py`

- [ ] **Step 1: Update failing orchestration test**

Change `test_run_job_orchestrates_pipeline_and_marks_ready`:

```python
monkeypatch.setattr(
    job_runner.splatfacto_runner,
    "run_splatfacto",
    lambda job_id, max_num_iterations: calls.append("splatfacto") or Path("splat.ply"),
)
```

Expected calls:

```python
assert calls == [
    "frames",
    "features",
    "matching",
    "mapping",
    "splatfacto",
    ("export", 30),
]
```

- [ ] **Step 2: Run failing test**

Expected: fail because `job_runner` still imports `opensplat_runner`.

- [ ] **Step 3: Replace import and stage call**

In `job_runner.py`, replace:

```python
opensplat_runner,
```

with:

```python
splatfacto_runner,
```

Replace:

```python
lambda: opensplat_runner.run_opensplat(job_id, job["iterations"]),
```

with:

```python
lambda: splatfacto_runner.run_splatfacto(job_id, job["iterations"]),
```

Change stage text to `"Splatfacto training"`.

- [ ] **Step 4: Run job runner tests**

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/services/job_runner.py apps/api/tests/test_job_runner.py
git commit -m "refactor: orchestrate splatfacto training"
```

---

## Task 4: Export Splatfacto Output To Web Scene

**Files:**
- Modify: `apps/api/app/services/model_exporter.py`
- Modify: `apps/api/tests/test_model_exporter.py`

- [ ] **Step 1: Update failing exporter tests**

Create source under:

```python
source = storage.job_splatfacto_export_dir("job_001") / "splat.ply"
```

Keep expected web output:

```python
target = storage.scene_dir("scene_001") / "scene.ply"
assert metadata["model_type"] == "ply"
assert metadata["model_url"] == "/static/scenes/scene_001/scene.ply"
```

Add failure test:

```python
def test_export_scene_errors_when_splatfacto_output_missing(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")

    with pytest.raises(RuntimeError, match="Splatfacto output not found"):
        model_exporter.export_scene("job_001")
```

- [ ] **Step 2: Run failing tests**

Expected: fail because exporter still reads OpenSplat directory.

- [ ] **Step 3: Update exporter**

Replace:

```python
source_ply = storage.job_opensplat_dir(job_id) / "splat.ply"
```

with:

```python
source_ply = storage.job_splatfacto_export_dir(job_id) / "splat.ply"
if not source_ply.exists():
    candidates = sorted(storage.job_splatfacto_export_dir(job_id).glob("*.ply"))
    source_ply = candidates[0] if candidates else source_ply
if not source_ply.exists():
    raise RuntimeError(f"Splatfacto output not found: {source_ply}")
```

- [ ] **Step 4: Run exporter tests**

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/services/model_exporter.py apps/api/tests/test_model_exporter.py
git commit -m "refactor: export splatfacto scenes"
```

---

## Task 5: Replace Metrics Reader

**Files:**
- Modify: `apps/api/app/services/metrics_reader.py`
- Modify: `apps/api/tests/test_metrics_reader.py`

- [ ] **Step 1: Write Splatfacto metrics tests**

Replace OpenSplat log sample with a Nerfstudio-compatible sample:

```python
def test_read_training_metrics_parses_splatfacto_jsonl(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_logs_dir("job_001") / "splatfacto-metrics.jsonl").write_text(
        "\n".join(
            [
                '{"step": 1, "loss": 0.45, "progress": 0}',
                '{"step": 1000, "loss": 0.21, "progress": 40}',
                '{"step": 2500, "loss": 0.12, "progress": 100}',
            ]
        ),
        encoding="utf-8",
    )

    metrics = metrics_reader.read_training_metrics("job_001")

    assert metrics["latest_step"] == 2500
    assert metrics["latest_loss"] == 0.12
    assert metrics["progress"] == 100
```

Add a text-log fallback test:

```python
def test_read_training_metrics_parses_splatfacto_text_log(monkeypatch, tmp_path):
    configure_tmp_storage(monkeypatch, tmp_path)
    storage.ensure_job_dirs("job_001")
    (storage.job_logs_dir("job_001") / "splatfacto.log").write_text(
        "step=10 loss=0.333\nstep=20 loss=0.222\n",
        encoding="utf-8",
    )

    metrics = metrics_reader.read_training_metrics("job_001")

    assert metrics["latest_step"] == 20
    assert metrics["latest_loss"] == 0.222
```

- [ ] **Step 2: Run failing metrics tests**

Expected: fail because reader still parses `opensplat.log`.

- [ ] **Step 3: Implement parser**

Implementation rules:

- Prefer `logs/splatfacto-metrics.jsonl` if present.
- Fallback to `logs/splatfacto.log`.
- Accept regex patterns:
  - `step=(\d+).*loss=([0-9.eE+-]+)`
  - `Step\s+(\d+).*loss[:=]\s*([0-9.eE+-]+)`
- Compute progress as `min(100, int(step / latest_configured_iterations * 100))` only if max iteration is available; otherwise leave progress `0` except explicit JSONL progress.

- [ ] **Step 4: Run metrics tests**

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/services/metrics_reader.py apps/api/tests/test_metrics_reader.py
git commit -m "refactor: read splatfacto training metrics"
```

---

## Task 6: Remove OpenSplat API Code And Tests

**Files:**
- Delete: `apps/api/app/services/opensplat_runner.py`
- Modify/Delete: `apps/api/tests/test_pipeline_runners.py`
- Modify: any remaining `apps/api/tests/*`

- [ ] **Step 1: Search active OpenSplat references**

```powershell
rg "opensplat|OpenSplat|OPENSPLAT" apps/api packages scripts/ops docker README-CUDA.md docs/cuda-migration.md docker/README.md packages/splatfacto/README.md packages/colmap_cuda/README.md
```

Expected before this task: active references remain.

- [ ] **Step 2: Delete OpenSplat runner**

```powershell
Remove-Item apps\api\app\services\opensplat_runner.py
```

- [ ] **Step 3: Update `test_pipeline_runners.py`**

Remove OpenSplat tests or move Splatfacto runner assertions to `test_splatfacto_runner.py`.

Keep FFmpeg and COLMAP runner tests.

- [ ] **Step 4: Run API tests**

```powershell
$env:PYTHONPATH='D:\.codex_workplace\3DGS\apps\api'
python -m pytest apps/api/tests -q
```

Expected: pass.

- [ ] **Step 5: Search again**

Allowed remaining references only in:

- `scripts/legacy/*`
- `docker/legacy/*`
- old historical docs under `docs/phase-1-verification.md`
- old historical plans under `docs/superpowers/plans/*opensplat*`

No active API/package/ops/Docker/README migration path may mention OpenSplat.

- [ ] **Step 6: Commit**

```powershell
git add -A apps/api
git commit -m "chore: remove opensplat api backend"
```

---

## Task 7: Replace CUDA Ops Scripts And Docker

**Files:**
- Delete: `scripts/ops/build_opensplat_cuda_docker.ps1`
- Delete: `scripts/ops/run_opensplat_cuda_only.ps1`
- Delete: `docker/opensplat-cuda.Dockerfile`
- Create: `scripts/ops/run_splatfacto_cuda.ps1`
- Create: `docker/nerfstudio-splatfacto.Dockerfile`
- Modify: `scripts/ops/check_environment.ps1`
- Modify: `scripts/ops/package_cuda_release.ps1`
- Modify: `docker/README.md`

- [ ] **Step 1: Write script behavior notes**

`run_splatfacto_cuda.ps1` must support:

```powershell
.\scripts\ops\run_splatfacto_cuda.ps1 `
  -JobId job_quality_006 `
  -Iterations 25000 `
  -UseDocker
```

Native mode:

```powershell
.\scripts\ops\run_splatfacto_cuda.ps1 `
  -JobId job_quality_006 `
  -Iterations 25000
```

- [ ] **Step 2: Implement script**

Script responsibilities:

- Validate `data/jobs/<job_id>/images` exists.
- Validate `data/jobs/<job_id>/colmap/sparse/0` exists.
- Create `data/jobs/<job_id>/nerfstudio/data/images`.
- Copy or junction selected images into Nerfstudio data.
- Copy COLMAP sparse output into `data/jobs/<job_id>/nerfstudio/data/colmap/sparse`.
- Run native:

```powershell
ns-train splatfacto `
  --data "$nerfstudioData" `
  --output-dir "$nerfstudioOutputs" `
  --experiment-name "$JobId" `
  --max-num-iterations "$Iterations" `
  --vis viewer
```

- Run export:

```powershell
ns-export gaussian-splat `
  --load-config "$configPath" `
  --output-dir "$exportDir"
```

- Docker mode mounts repo root and runs equivalent commands inside `nerfstudio-splatfacto:local`.

- [ ] **Step 3: Add Dockerfile**

`docker/nerfstudio-splatfacto.Dockerfile` should:

- Start from an NVIDIA CUDA runtime/devel image compatible with target PyTorch.
- Install Python, git, ffmpeg, COLMAP runtime deps.
- Install PyTorch CUDA and Nerfstudio.
- Run `ns-train splatfacto --help` during build if feasible.

Keep Dockerfile minimal; do not include OpenSplat, LibTorch, or OpenSplat source.

- [ ] **Step 4: Update environment check**

Remove OpenSplat checks. Add:

```powershell
ns-train --help
ns-export --help
python -c "import torch; print(torch.cuda.is_available())"
```

Optional Docker image check:

```powershell
docker image inspect nerfstudio-splatfacto:local
```

- [ ] **Step 5: Update packaging**

Ensure `package_cuda_release.ps1` packages:

- `docker/nerfstudio-splatfacto.Dockerfile`
- `scripts/ops/run_splatfacto_cuda.ps1`

and does not package:

- `docker/opensplat-cuda.Dockerfile`
- `scripts/ops/*opensplat*`

- [ ] **Step 6: Run static validation**

```powershell
rg "opensplat|OpenSplat|OPENSPLAT" scripts/ops docker README-CUDA.md docs/cuda-migration.md docker/README.md
```

Expected: no active references.

- [ ] **Step 7: Commit**

```powershell
git add -A scripts/ops docker
git commit -m "chore: replace opensplat ops with splatfacto"
```

---

## Task 8: Rewrite Documentation

**Files:**
- Modify: `README-CUDA.md`
- Modify: `docs/cuda-migration.md`
- Modify: `docker/README.md`
- Modify: `packages/splatfacto/README.md`
- Modify: `packages/colmap_cuda/README.md`
- Optional Create: `docs/splatfacto-gpu-runbook.md`

- [ ] **Step 1: Rewrite README CUDA flow**

New top-level flow:

```text
Android capture / video import
-> frame selection
-> COLMAP CUDA
-> Nerfstudio Splatfacto
-> ns-export gaussian-splat
-> web viewer
```

Remove OpenSplat CUDA build/run sections.

- [ ] **Step 2: Add 5090 notes**

Document:

- Install a recent NVIDIA driver.
- Use CUDA/PyTorch/Nerfstudio versions compatible with Blackwell/RTX 5090.
- Verify:

```powershell
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
ns-train splatfacto --help
ns-export gaussian-splat --help
```

- [ ] **Step 3: Add Splatfacto run commands**

```powershell
.\scripts\ops\run_splatfacto_cuda.ps1 `
  -JobId job_quality_006 `
  -Iterations 25000
```

Viewer URLs remain:

```text
http://127.0.0.1:8000/jobs/<job_id>/metrics-view
http://127.0.0.1:8000/scenes/<scene_id>/viewer
```

- [ ] **Step 4: Update package docs**

`packages/splatfacto/README.md` should describe it as the only supported training backend.

`packages/colmap_cuda/README.md` should say it exports artifacts for Nerfstudio/Splatfacto only.

- [ ] **Step 5: Run docs search**

```powershell
rg "OpenSplat CUDA|opensplat-cuda|run_opensplat_cuda_only|build_opensplat_cuda" README-CUDA.md docs/cuda-migration.md docker/README.md packages
```

Expected: no matches.

- [ ] **Step 6: Commit**

```powershell
git add README-CUDA.md docs/cuda-migration.md docker/README.md packages/splatfacto/README.md packages/colmap_cuda/README.md
git commit -m "docs: document splatfacto-only cuda workflow"
```

---

## Task 9: End-To-End Splatfacto Acceptance On GPU Host

**Files:**
- No code changes unless bugs are found.

- [ ] **Step 1: Prepare GPU host**

On the 5090 machine:

```powershell
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
ns-train splatfacto --help
ns-export gaussian-splat --help
```

Expected:

- CUDA visible.
- `ns-train` exposes `splatfacto`.
- `ns-export` exposes `gaussian-splat`.

- [ ] **Step 2: Run package tests**

```powershell
$env:PYTHONPATH="$PWD"
python -m pytest tests -q
$env:PYTHONPATH="$PWD\apps\api"
python -m pytest apps/api/tests -q
```

Expected: pass.

- [ ] **Step 3: Run a small Splatfacto job**

Use an existing COLMAP-ready job:

```powershell
.\scripts\ops\run_splatfacto_cuda.ps1 `
  -JobId job_quality_006 `
  -Iterations 2500
```

Expected outputs:

```text
data/jobs/job_quality_006/nerfstudio/outputs/**/config.yml
data/jobs/job_quality_006/nerfstudio/exports/*.ply
data/jobs/job_quality_006/logs/splatfacto.log
data/jobs/job_quality_006/logs/splatfacto-export.log
```

- [ ] **Step 4: Run API export/viewer path**

If using the API:

```powershell
.\scripts\ops\run_api.ps1
```

Then verify:

```text
http://127.0.0.1:8000/jobs/<job_id>/metrics-view
http://127.0.0.1:8000/scenes/<scene_id>/viewer
```

Acceptance requires the exported Splatfacto `.ply` to load in the web viewer. File existence alone is not sufficient.

- [ ] **Step 5: Run active OpenSplat absence check**

```powershell
rg "opensplat|OpenSplat|OPENSPLAT" apps packages scripts/ops docker README-CUDA.md docs/cuda-migration.md docker/README.md
```

Expected:

- No active code, active ops script, active Dockerfile, or active migration doc references.
- Historical references may exist only under `scripts/legacy`, `docker/legacy`, and old historical docs/plans.

- [ ] **Step 6: Commit GPU-host fixes if needed**

If GPU-host testing reveals CLI flag differences or export filename differences:

```powershell
git add <fixed-files>
git commit -m "fix: align splatfacto runner with gpu host"
```

---

## Acceptance Criteria

The migration is complete only when all of these are true:

- API job orchestration calls Splatfacto, not OpenSplat.
- `apps/api/app/services/opensplat_runner.py` is deleted.
- `docker/opensplat-cuda.Dockerfile` is deleted.
- `scripts/ops/build_opensplat_cuda_docker.ps1` is deleted.
- `scripts/ops/run_opensplat_cuda_only.ps1` is deleted.
- `README-CUDA.md` and `docs/cuda-migration.md` describe Nerfstudio + Splatfacto only.
- A GPU-host Splatfacto run produces an exported `.ply`.
- The exported `.ply` is browsable in the current web viewer.
- Metrics view reads Splatfacto progress/loss.
- `python -m pytest tests -q` passes.
- `python -m pytest apps/api/tests -q` passes.
- Active search for OpenSplat references returns no supported code/docs/scripts.

## Known Risks

- Nerfstudio CLI flags can vary by version. Verify `ns-train splatfacto --help` on the 5090 host before finalizing runner flags.
- Splatfacto quality depends heavily on COLMAP quality and image sharpness; migration alone will not fix bad camera poses.
- Exported `.ply` schema may differ slightly from OpenSplat PLY; the web viewer must be tested visually.
- Blackwell/RTX 5090 may require newer PyTorch/CUDA than older Nerfstudio install snippets. Prefer validating torch CUDA availability before training.
