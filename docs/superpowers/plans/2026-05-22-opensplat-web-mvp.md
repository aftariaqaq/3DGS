# OpenSplat Web MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a no-NVIDIA-GPU first-stage MVP where a user uploads a phone video, the system runs FFmpeg + COLMAP + OpenSplat CPU, then opens the generated 3DGS result directly in a Web viewer.

**Architecture:** Use a local single-machine pipeline with explicit job directories and JSON metadata. The backend wraps external command-line tools, records stage logs, exposes job/scene APIs, and serves generated model files; the frontend uploads videos, polls job status, shows logs, and embeds a Gaussian Splat viewer for the final scene.

**Tech Stack:** PowerShell, FFmpeg, COLMAP, OpenSplat, FastAPI, Python subprocess, JSON file storage, React, Vite, Three.js, GaussianSplats3D.

---

## Scope

This plan covers Phase 1 only:

- Upload one MP4 video from a Web page.
- Extract frames with FFmpeg.
- Estimate camera poses with COLMAP.
- Train with OpenSplat in CPU-compatible mode.
- Export a Web-loadable model artifact.
- Browse the result in the same Web app.
- Show logs and failure stage when a task fails.

This plan intentionally excludes:

- User accounts and permissions.
- Multi-GPU scheduling.
- Distributed workers.
- Asset/机柜 semantic annotation.
- Measurement tools.
- Incremental reconstruction.
- Production object storage.
- Nerfstudio/Splatfacto execution.

## Critical Acceptance Criteria

The Phase 1 MVP is complete only when:

- A user can open the Web upload page.
- A user can upload an MP4 video.
- The backend creates a job and runs all pipeline stages.
- The frontend displays job status and logs.
- OpenSplat produces a model artifact.
- The backend creates a scene record.
- The frontend opens `/scenes/:sceneId`.
- The scene page loads the generated model.
- The user can rotate, pan, and zoom the 3DGS result in the Web page.
- A failed job shows the failed stage and useful log output.

The existence of `data/jobs/{job_id}/opensplat/splat.ply` alone is not sufficient.

## File Structure

Create these files:

```text
D:\.codex_workplace\3DGS\
  backend\
    app\
      __init__.py
      main.py
      config.py
      models.py
      routes\
        __init__.py
        uploads.py
        jobs.py
        scenes.py
      services\
        __init__.py
        storage.py
        process_runner.py
        ffmpeg_runner.py
        colmap_runner.py
        opensplat_runner.py
        model_exporter.py
        job_store.py
        scene_store.py
        job_runner.py
        log_reader.py
    requirements.txt

  frontend\
    index.html
    package.json
    tsconfig.json
    vite.config.ts
    src\
      main.tsx
      App.tsx
      api\
        client.ts
        jobs.ts
        scenes.ts
        uploads.ts
      pages\
        UploadPage.tsx
        JobPage.tsx
        ScenePage.tsx
      components\
        UploadPanel.tsx
        JobStatusPanel.tsx
        LogPanel.tsx
        GaussianViewer.tsx
        SceneToolbar.tsx
      styles.css

  scripts\
    check_environment.ps1
    run_pipeline_test.ps1

  data\
    jobs\
    scenes\
```

Responsibilities:

- `scripts/check_environment.ps1`: Verify local tool availability.
- `scripts/run_pipeline_test.ps1`: Run the pipeline without backend/frontend.
- `backend/app/config.py`: Central paths and command names.
- `backend/app/models.py`: Pydantic models and status constants.
- `storage.py`: Build and create job/scene paths.
- `process_runner.py`: Execute external commands, stream logs, return exit status.
- `ffmpeg_runner.py`: Extract frames from uploaded video.
- `colmap_runner.py`: Run feature extraction, matching, and mapping.
- `opensplat_runner.py`: Run OpenSplat with bounded iterations.
- `model_exporter.py`: Copy or convert model output into `data/scenes/{scene_id}`.
- `job_store.py`: Read/write `job.json`.
- `scene_store.py`: Read/write scene `metadata.json`.
- `job_runner.py`: Orchestrate the end-to-end pipeline.
- `log_reader.py`: Return combined or stage-specific logs.
- `uploads.py`: Accept MP4 upload and start job.
- `jobs.py`: Return job status and logs.
- `scenes.py`: Return scene metadata.
- `GaussianViewer.tsx`: Embed the Web Gaussian Splat viewer.

## Data Layout

Each job uses:

```text
data/jobs/{job_id}/
  input/
    input.mp4
  images/
    frame_000001.jpg
  colmap/
    database.db
    sparse/
      0/
        cameras.bin
        images.bin
        points3D.bin
  opensplat/
    splat.ply
    cameras.json
  web/
  logs/
    extract_frames.log
    colmap_features.log
    colmap_matching.log
    colmap_mapping.log
    opensplat.log
    model_export.log
  job.json
```

Each scene uses:

```text
data/scenes/{scene_id}/
  scene.ply
  metadata.json
```

If GaussianSplats3D cannot load OpenSplat PLY directly, `model_exporter.py` must instead create `scene.splat` or `scene.ksplat` and set `model_type` accordingly.

## Job Statuses

Use these statuses:

```text
CREATED
UPLOADED
EXTRACTING_FRAMES
COLMAP_FEATURES
COLMAP_MATCHING
COLMAP_MAPPING
TRAINING_OPEN_SPLAT
EXPORTING_MODEL
READY
FAILED
```

`job.json` shape:

```json
{
  "id": "job_001",
  "status": "TRAINING_OPEN_SPLAT",
  "stage": "OpenSplat CPU training",
  "created_at": "2026-05-22T16:00:00+08:00",
  "updated_at": "2026-05-22T16:05:00+08:00",
  "fps": 1,
  "max_frames": 80,
  "iterations": 500,
  "input_video": "data/jobs/job_001/input/input.mp4",
  "frame_count": 80,
  "scene_id": null,
  "result_model": null,
  "error_stage": null,
  "error_message": null
}
```

`metadata.json` shape:

```json
{
  "id": "scene_001",
  "job_id": "job_001",
  "name": "scene_001",
  "model_type": "ply",
  "model_url": "/static/scenes/scene_001/scene.ply",
  "created_at": "2026-05-22T16:20:00+08:00",
  "stats": {
    "frame_count": 80,
    "model_size_bytes": 12345678
  }
}
```

## API Contract

### Upload Video

```http
POST /api/uploads/video
Content-Type: multipart/form-data
```

Fields:

- `file`: MP4 video.
- `fps`: number, default `1`.
- `max_frames`: number, default `80`.
- `iterations`: number, default `500`.

Response:

```json
{
  "job_id": "job_001",
  "status": "UPLOADED"
}
```

### Get Job

```http
GET /api/jobs/{job_id}
```

Response:

```json
{
  "id": "job_001",
  "status": "READY",
  "stage": "Ready",
  "scene_id": "scene_001",
  "error_stage": null,
  "error_message": null
}
```

### Get Logs

```http
GET /api/jobs/{job_id}/logs
GET /api/jobs/{job_id}/logs?stage=opensplat
```

Response:

```json
{
  "job_id": "job_001",
  "stage": "opensplat",
  "text": "..."
}
```

### Get Scene

```http
GET /api/scenes/{scene_id}
```

Response:

```json
{
  "id": "scene_001",
  "job_id": "job_001",
  "model_type": "ply",
  "model_url": "/static/scenes/scene_001/scene.ply"
}
```

### Static Files

```http
GET /static/scenes/{scene_id}/scene.ply
GET /static/scenes/{scene_id}/metadata.json
```

## Task 1: Create Environment Check Script

**Files:**

- Create: `D:\.codex_workplace\3DGS\scripts\check_environment.ps1`

- [ ] **Step 1: Write the script**

The script must check these commands:

```powershell
ffmpeg -version
colmap -h
opensplat.exe --help
```

It must print `[OK]` or `[FAIL]` for each command and exit non-zero if any command is unavailable.

- [ ] **Step 2: Run the script**

Run:

```powershell
.\scripts\check_environment.ps1
```

Expected:

```text
[OK] ffmpeg
[OK] colmap
[OK] opensplat
```

or a clear failure that identifies missing tools.

- [ ] **Step 3: Commit**

If this is later placed in a git repository:

```powershell
git add scripts/check_environment.ps1
git commit -m "chore: add environment check script"
```

## Task 2: Create Command-Line Pipeline Script

**Files:**

- Create: `D:\.codex_workplace\3DGS\scripts\run_pipeline_test.ps1`

- [ ] **Step 1: Write script parameters**

The script must accept:

```powershell
param(
  [Parameter(Mandatory=$true)][string]$InputVideo,
  [string]$JobId = "job_test_001",
  [int]$Fps = 1,
  [int]$MaxFrames = 80,
  [int]$Iterations = 500
)
```

- [ ] **Step 2: Create job directories**

The script must create:

```text
data/jobs/{JobId}/input
data/jobs/{JobId}/images
data/jobs/{JobId}/colmap
data/jobs/{JobId}/colmap/sparse
data/jobs/{JobId}/opensplat
data/jobs/{JobId}/logs
```

- [ ] **Step 3: Copy video**

Copy input video to:

```text
data/jobs/{JobId}/input/input.mp4
```

- [ ] **Step 4: Extract frames**

Run:

```powershell
ffmpeg -y -i data/jobs/{JobId}/input/input.mp4 -vf fps={Fps} data/jobs/{JobId}/images/frame_%06d.jpg
```

Write output to:

```text
data/jobs/{JobId}/logs/extract_frames.log
```

- [ ] **Step 5: Limit frames**

If frame count exceeds `MaxFrames`, keep a deterministic subset. Prefer evenly spaced frames. If that is too much for the first pass, keep the first `MaxFrames` and document this limitation.

- [ ] **Step 6: Run COLMAP feature extraction**

Run:

```powershell
colmap feature_extractor `
  --database_path data/jobs/{JobId}/colmap/database.db `
  --image_path data/jobs/{JobId}/images
```

Write output to:

```text
data/jobs/{JobId}/logs/colmap_features.log
```

- [ ] **Step 7: Run COLMAP sequential matcher**

Run:

```powershell
colmap sequential_matcher `
  --database_path data/jobs/{JobId}/colmap/database.db
```

Write output to:

```text
data/jobs/{JobId}/logs/colmap_matching.log
```

- [ ] **Step 8: Run COLMAP mapper**

Run:

```powershell
colmap mapper `
  --database_path data/jobs/{JobId}/colmap/database.db `
  --image_path data/jobs/{JobId}/images `
  --output_path data/jobs/{JobId}/colmap/sparse
```

Write output to:

```text
data/jobs/{JobId}/logs/colmap_mapping.log
```

- [ ] **Step 9: Run OpenSplat**

First try:

```powershell
opensplat.exe data/jobs/{JobId} -n {Iterations}
```

If this does not detect the COLMAP project, try:

```powershell
opensplat.exe data/jobs/{JobId}/colmap -n {Iterations}
```

Write output to:

```text
data/jobs/{JobId}/logs/opensplat.log
```

- [ ] **Step 10: Verify output**

The script must check for `splat.ply` in the expected OpenSplat output location. If OpenSplat writes to the working directory, move the result into:

```text
data/jobs/{JobId}/opensplat/splat.ply
```

- [ ] **Step 11: Run on a small test video**

Run:

```powershell
.\scripts\run_pipeline_test.ps1 -InputVideo "D:\path\to\short-room-video.mp4" -JobId "job_test_001" -Fps 1 -MaxFrames 50 -Iterations 300
```

Expected:

```text
data/jobs/job_test_001/opensplat/splat.ply
```

- [ ] **Step 12: Commit**

```powershell
git add scripts/run_pipeline_test.ps1
git commit -m "chore: add local opensplat pipeline script"
```

## Task 3: Validate Web Viewer Compatibility

**Files:**

- Create: `D:\.codex_workplace\3DGS\frontend\package.json`
- Create: `D:\.codex_workplace\3DGS\frontend\src\components\GaussianViewer.tsx`
- Create: `D:\.codex_workplace\3DGS\frontend\src\pages\ScenePage.tsx`

- [ ] **Step 1: Create a temporary static model path**

Copy a known `splat.ply` from Task 2 to:

```text
data/scenes/scene_test_001/scene.ply
```

- [ ] **Step 2: Install frontend dependencies**

Run inside `frontend`:

```powershell
npm install
npm install three @mkkellogg/gaussian-splats-3d
```

If the package name differs, check the GaussianSplats3D project documentation and record the actual package name in this plan.

- [ ] **Step 3: Implement a minimal `GaussianViewer`**

The first pass only needs:

- A full-window canvas/container.
- Load model URL.
- Orbit-style navigation.
- Loading state.
- Error state.
- Cleanup on unmount.

- [ ] **Step 4: Run Vite**

Run:

```powershell
npm run dev
```

Expected:

```text
Local: http://localhost:5173/
```

- [ ] **Step 5: Open scene page**

Open:

```text
http://localhost:5173/scenes/scene_test_001
```

Expected:

- The generated model loads.
- User can rotate.
- User can zoom.
- User can pan.

- [ ] **Step 6: Decide conversion requirement**

If `scene.ply` loads successfully, record:

```text
model_type = ply
conversion = not required for Phase 1
```

If it does not load, add a conversion step to Task 9 and record:

```text
model_type = splat or ksplat
conversion = required
```

- [ ] **Step 7: Commit**

```powershell
git add frontend
git commit -m "test: validate gaussian splat web viewer"
```

## Task 4: Build Backend Skeleton

**Files:**

- Create: `D:\.codex_workplace\3DGS\backend\requirements.txt`
- Create: `D:\.codex_workplace\3DGS\backend\app\__init__.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\main.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\config.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\models.py`

- [ ] **Step 1: Create requirements**

Use:

```text
fastapi
uvicorn[standard]
python-multipart
pydantic
```

- [ ] **Step 2: Define config**

`config.py` must define:

```python
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR.parent / "data"
JOBS_DIR = DATA_DIR / "jobs"
SCENES_DIR = DATA_DIR / "scenes"
FFMPEG_CMD = "ffmpeg"
COLMAP_CMD = "colmap"
OPENSPLAT_CMD = "opensplat.exe"
```

Adjust `ROOT_DIR` if needed after verifying actual path resolution.

- [ ] **Step 3: Define models**

Include job status constants and Pydantic response models for upload, job, logs, and scene.

- [ ] **Step 4: Create FastAPI app**

`main.py` must:

- Create the app.
- Include routers later.
- Mount `/static/jobs` and `/static/scenes`.
- Provide `GET /health`.

- [ ] **Step 5: Run backend**

Run:

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Expected:

```http
GET http://localhost:8000/health
```

returns:

```json
{"status":"ok"}
```

- [ ] **Step 6: Commit**

```powershell
git add backend
git commit -m "feat: add backend skeleton"
```

## Task 5: Implement Job and Scene Storage

**Files:**

- Create: `D:\.codex_workplace\3DGS\backend\app\services\__init__.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\services\storage.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\services\job_store.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\services\scene_store.py`

- [ ] **Step 1: Write storage helpers**

`storage.py` must provide:

```python
def job_dir(job_id: str) -> Path: ...
def job_input_dir(job_id: str) -> Path: ...
def job_images_dir(job_id: str) -> Path: ...
def job_colmap_dir(job_id: str) -> Path: ...
def job_opensplat_dir(job_id: str) -> Path: ...
def job_logs_dir(job_id: str) -> Path: ...
def scene_dir(scene_id: str) -> Path: ...
def ensure_job_dirs(job_id: str) -> None: ...
def ensure_scene_dir(scene_id: str) -> None: ...
```

- [ ] **Step 2: Write job store**

`job_store.py` must:

- Create `job.json`.
- Read `job.json`.
- Update status.
- Mark failure with `error_stage` and `error_message`.
- Mark ready with `scene_id`.

- [ ] **Step 3: Write scene store**

`scene_store.py` must:

- Create scene metadata.
- Read scene metadata.
- List scene metadata.

- [ ] **Step 4: Add unit-level smoke test**

Manually run a short Python snippet from `backend`:

```powershell
python - <<'PY'
from app.services.storage import ensure_job_dirs
from app.services.job_store import create_job, read_job
ensure_job_dirs("job_smoke")
create_job("job_smoke", fps=1, max_frames=50, iterations=300)
print(read_job("job_smoke")["id"])
PY
```

Expected:

```text
job_smoke
```

- [ ] **Step 5: Commit**

```powershell
git add backend/app/services
git commit -m "feat: add file based job and scene storage"
```

## Task 6: Implement Process Runner

**Files:**

- Create: `D:\.codex_workplace\3DGS\backend\app\services\process_runner.py`

- [ ] **Step 1: Implement command execution**

`process_runner.py` must expose:

```python
def run_command(args: list[str], log_path: Path, cwd: Path | None = None) -> None:
    ...
```

Requirements:

- Write command line to the log first.
- Stream stdout and stderr into the log.
- Raise a typed exception or `RuntimeError` on non-zero exit.
- Include exit code in error message.

- [ ] **Step 2: Smoke test success**

Run:

```powershell
python - <<'PY'
from pathlib import Path
from app.services.process_runner import run_command
run_command(["powershell", "-NoProfile", "-Command", "Write-Output hello"], Path("test-success.log"))
PY
```

Expected:

```text
test-success.log contains hello
```

- [ ] **Step 3: Smoke test failure**

Run:

```powershell
python - <<'PY'
from pathlib import Path
from app.services.process_runner import run_command
try:
    run_command(["powershell", "-NoProfile", "-Command", "exit 7"], Path("test-fail.log"))
except RuntimeError as exc:
    print(exc)
PY
```

Expected:

```text
exit code 7
```

- [ ] **Step 4: Commit**

```powershell
git add backend/app/services/process_runner.py
git commit -m "feat: add logged process runner"
```

## Task 7: Implement Pipeline Runners

**Files:**

- Create: `D:\.codex_workplace\3DGS\backend\app\services\ffmpeg_runner.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\services\colmap_runner.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\services\opensplat_runner.py`

- [ ] **Step 1: Implement FFmpeg runner**

Expose:

```python
def extract_frames(job_id: str, fps: int, max_frames: int) -> int:
    ...
```

It must:

- Run FFmpeg.
- Count extracted frames.
- Enforce `max_frames`.
- Return final frame count.

- [ ] **Step 2: Implement COLMAP runner**

Expose:

```python
def run_feature_extractor(job_id: str) -> None: ...
def run_sequential_matcher(job_id: str) -> None: ...
def run_mapper(job_id: str) -> None: ...
```

It must write logs to the expected log files.

- [ ] **Step 3: Implement OpenSplat runner**

Expose:

```python
def run_opensplat(job_id: str, iterations: int) -> Path:
    ...
```

It must:

- Run OpenSplat.
- Locate `splat.ply`.
- Move/copy it to `data/jobs/{job_id}/opensplat/splat.ply`.
- Return the final path.

- [ ] **Step 4: Smoke test with an existing job**

Use a small job prepared by Task 2. Run each function manually from Python.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/services/ffmpeg_runner.py backend/app/services/colmap_runner.py backend/app/services/opensplat_runner.py
git commit -m "feat: add ffmpeg colmap and opensplat runners"
```

## Task 8: Implement Model Exporter

**Files:**

- Create: `D:\.codex_workplace\3DGS\backend\app\services\model_exporter.py`

- [ ] **Step 1: Implement scene creation from job output**

Expose:

```python
def export_scene(job_id: str) -> dict:
    ...
```

It must:

- Create a new `scene_id`.
- Copy `data/jobs/{job_id}/opensplat/splat.ply` to `data/scenes/{scene_id}/scene.ply` if PLY is compatible.
- Write `metadata.json`.
- Return scene metadata.

- [ ] **Step 2: Leave conversion hook**

Add a small internal function:

```python
def convert_if_needed(source_ply: Path, target_dir: Path) -> tuple[str, Path]:
    ...
```

For Phase 1, it may simply copy PLY and return `("ply", target_path)`.

- [ ] **Step 3: Smoke test export**

Run against a job with `opensplat/splat.ply`.

- [ ] **Step 4: Commit**

```powershell
git add backend/app/services/model_exporter.py
git commit -m "feat: export opensplat output as web scene"
```

## Task 9: Implement Job Runner

**Files:**

- Create: `D:\.codex_workplace\3DGS\backend\app\services\job_runner.py`

- [ ] **Step 1: Implement orchestration**

Expose:

```python
def run_job(job_id: str) -> None:
    ...
```

Order:

1. Set `EXTRACTING_FRAMES`.
2. Run FFmpeg.
3. Set `COLMAP_FEATURES`.
4. Run COLMAP features.
5. Set `COLMAP_MATCHING`.
6. Run COLMAP matching.
7. Set `COLMAP_MAPPING`.
8. Run COLMAP mapper.
9. Set `TRAINING_OPEN_SPLAT`.
10. Run OpenSplat.
11. Set `EXPORTING_MODEL`.
12. Export scene.
13. Set `READY`.

- [ ] **Step 2: Implement failure handling**

Any exception must:

- Mark job as `FAILED`.
- Save `error_stage`.
- Save `error_message`.
- Preserve logs.

- [ ] **Step 3: Smoke test with copied video**

Call `run_job("job_smoke")` for a job that has `input/input.mp4`.

- [ ] **Step 4: Commit**

```powershell
git add backend/app/services/job_runner.py
git commit -m "feat: orchestrate opensplat reconstruction jobs"
```

## Task 10: Implement Backend Routes

**Files:**

- Create: `D:\.codex_workplace\3DGS\backend\app\routes\__init__.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\routes\uploads.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\routes\jobs.py`
- Create: `D:\.codex_workplace\3DGS\backend\app\routes\scenes.py`
- Modify: `D:\.codex_workplace\3DGS\backend\app\main.py`

- [ ] **Step 1: Implement upload route**

`POST /api/uploads/video` must:

- Accept multipart upload.
- Validate `.mp4` extension or content type.
- Create a job id.
- Save video to job input path.
- Create `job.json`.
- Start background job execution.
- Return job id.

- [ ] **Step 2: Implement job routes**

Routes:

```http
GET /api/jobs
GET /api/jobs/{job_id}
GET /api/jobs/{job_id}/logs
```

- [ ] **Step 3: Implement scene routes**

Routes:

```http
GET /api/scenes
GET /api/scenes/{scene_id}
```

- [ ] **Step 4: Wire routers and static paths**

`main.py` must include all routers and serve:

```text
/static/jobs
/static/scenes
```

- [ ] **Step 5: Manual API test**

Run:

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Then upload with:

```powershell
curl.exe -F "file=@D:\path\to\short-room-video.mp4" -F "fps=1" -F "max_frames=50" -F "iterations=300" http://localhost:8000/api/uploads/video
```

Expected:

```json
{"job_id":"...","status":"UPLOADED"}
```

- [ ] **Step 6: Commit**

```powershell
git add backend/app/routes backend/app/main.py
git commit -m "feat: add upload job and scene APIs"
```

## Task 11: Build Frontend Skeleton

**Files:**

- Create: `D:\.codex_workplace\3DGS\frontend\index.html`
- Create: `D:\.codex_workplace\3DGS\frontend\package.json`
- Create: `D:\.codex_workplace\3DGS\frontend\tsconfig.json`
- Create: `D:\.codex_workplace\3DGS\frontend\vite.config.ts`
- Create: `D:\.codex_workplace\3DGS\frontend\src\main.tsx`
- Create: `D:\.codex_workplace\3DGS\frontend\src\App.tsx`
- Create: `D:\.codex_workplace\3DGS\frontend\src\styles.css`

- [ ] **Step 1: Create Vite React TypeScript app files**

Use minimal routes for:

```text
/upload
/jobs/:jobId
/scenes/:sceneId
```

- [ ] **Step 2: Install dependencies**

Run:

```powershell
cd frontend
npm install
```

- [ ] **Step 3: Run dev server**

Run:

```powershell
npm run dev
```

Expected:

```text
http://localhost:5173/
```

- [ ] **Step 4: Commit**

```powershell
git add frontend
git commit -m "feat: add frontend skeleton"
```

## Task 12: Implement Frontend API Client

**Files:**

- Create: `D:\.codex_workplace\3DGS\frontend\src\api\client.ts`
- Create: `D:\.codex_workplace\3DGS\frontend\src\api\uploads.ts`
- Create: `D:\.codex_workplace\3DGS\frontend\src\api\jobs.ts`
- Create: `D:\.codex_workplace\3DGS\frontend\src\api\scenes.ts`

- [ ] **Step 1: Define API base URL**

Use:

```ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
```

- [ ] **Step 2: Implement upload call**

Expose:

```ts
export async function uploadVideo(file: File, options: { fps: number; maxFrames: number; iterations: number }): Promise<{ job_id: string; status: string }>
```

- [ ] **Step 3: Implement job calls**

Expose:

```ts
export async function getJob(jobId: string): Promise<Job>
export async function getJobLogs(jobId: string, stage?: string): Promise<string>
```

- [ ] **Step 4: Implement scene call**

Expose:

```ts
export async function getScene(sceneId: string): Promise<Scene>
```

- [ ] **Step 5: Commit**

```powershell
git add frontend/src/api
git commit -m "feat: add frontend API client"
```

## Task 13: Implement Upload Page

**Files:**

- Create: `D:\.codex_workplace\3DGS\frontend\src\pages\UploadPage.tsx`
- Create: `D:\.codex_workplace\3DGS\frontend\src\components\UploadPanel.tsx`
- Modify: `D:\.codex_workplace\3DGS\frontend\src\App.tsx`

- [ ] **Step 1: Build upload form**

Fields:

- MP4 file input.
- FPS numeric input, default `1`.
- Max frames numeric input, default `50`.
- Iterations numeric input, default `300`.

- [ ] **Step 2: Submit upload**

On submit:

- Disable submit button.
- Call upload API.
- Navigate to `/jobs/{job_id}`.

- [ ] **Step 3: Show validation**

Show clear messages for:

- No file selected.
- Non-MP4 file.
- Upload failure.

- [ ] **Step 4: Manual test**

Upload a small MP4 and confirm navigation to job page.

- [ ] **Step 5: Commit**

```powershell
git add frontend/src/pages/UploadPage.tsx frontend/src/components/UploadPanel.tsx frontend/src/App.tsx
git commit -m "feat: add video upload page"
```

## Task 14: Implement Job Page

**Files:**

- Create: `D:\.codex_workplace\3DGS\frontend\src\pages\JobPage.tsx`
- Create: `D:\.codex_workplace\3DGS\frontend\src\components\JobStatusPanel.tsx`
- Create: `D:\.codex_workplace\3DGS\frontend\src\components\LogPanel.tsx`
- Modify: `D:\.codex_workplace\3DGS\frontend\src\App.tsx`

- [ ] **Step 1: Poll job status**

Every 2 seconds call:

```text
GET /api/jobs/{job_id}
```

Stop polling when status is:

```text
READY
FAILED
```

- [ ] **Step 2: Poll logs**

Every 3 seconds call:

```text
GET /api/jobs/{job_id}/logs
```

- [ ] **Step 3: Show ready action**

When `status === "READY"` and `scene_id` is present, show:

```text
Open Scene
```

Click navigates to:

```text
/scenes/{scene_id}
```

- [ ] **Step 4: Show failure**

If failed, show:

- `error_stage`
- `error_message`
- logs

- [ ] **Step 5: Commit**

```powershell
git add frontend/src/pages/JobPage.tsx frontend/src/components/JobStatusPanel.tsx frontend/src/components/LogPanel.tsx frontend/src/App.tsx
git commit -m "feat: add job status and logs page"
```

## Task 15: Implement Scene Viewer Page

**Files:**

- Create: `D:\.codex_workplace\3DGS\frontend\src\pages\ScenePage.tsx`
- Create: `D:\.codex_workplace\3DGS\frontend\src\components\GaussianViewer.tsx`
- Create: `D:\.codex_workplace\3DGS\frontend\src\components\SceneToolbar.tsx`
- Modify: `D:\.codex_workplace\3DGS\frontend\src\App.tsx`
- Modify: `D:\.codex_workplace\3DGS\frontend\src\styles.css`

- [ ] **Step 1: Fetch scene metadata**

On page load:

```text
GET /api/scenes/{scene_id}
```

- [ ] **Step 2: Initialize viewer**

`GaussianViewer` must:

- Fill available viewport.
- Load `scene.model_url`.
- Support rotate, pan, and zoom.
- Show loading state.
- Show load errors.
- Dispose viewer resources on unmount.

- [ ] **Step 3: Add toolbar**

Toolbar actions:

- Back to job if `job_id` is present.
- Reset view.
- Show model type.

- [ ] **Step 4: Manual viewer test**

Open:

```text
http://localhost:5173/scenes/{scene_id}
```

Expected:

- Model appears.
- Mouse drag rotates.
- Wheel zooms.
- Pan works.
- Resize works.

- [ ] **Step 5: Commit**

```powershell
git add frontend/src/pages/ScenePage.tsx frontend/src/components/GaussianViewer.tsx frontend/src/components/SceneToolbar.tsx frontend/src/App.tsx frontend/src/styles.css
git commit -m "feat: add web gaussian splat scene viewer"
```

## Task 16: End-to-End Verification

**Files:**

- Modify as needed based on bugs found.
- Create: `D:\.codex_workplace\3DGS\docs\phase-1-verification.md`

- [ ] **Step 1: Start backend**

Run:

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Start frontend**

Run:

```powershell
cd frontend
npm run dev
```

- [ ] **Step 3: Upload a small phone video**

Use:

```text
fps = 1
max_frames = 50
iterations = 300
```

- [ ] **Step 4: Watch job complete**

Expected statuses:

```text
UPLOADED
EXTRACTING_FRAMES
COLMAP_FEATURES
COLMAP_MATCHING
COLMAP_MAPPING
TRAINING_OPEN_SPLAT
EXPORTING_MODEL
READY
```

- [ ] **Step 5: Open scene**

Click `Open Scene`.

Expected:

- `/scenes/{scene_id}` opens.
- Model loads.
- Rotate works.
- Zoom works.
- Pan works.

- [ ] **Step 6: Record verification**

Write:

```text
docs/phase-1-verification.md
```

Include:

- Test video duration.
- FPS.
- Max frames.
- Iterations.
- Total runtime.
- COLMAP success/failure notes.
- OpenSplat output path.
- Scene URL.
- Viewer result.
- Known issues.

- [ ] **Step 7: Commit**

```powershell
git add docs/phase-1-verification.md
git commit -m "docs: record phase 1 verification"
```

## Risk Register

### Risk: OpenSplat PLY is not directly compatible with GaussianSplats3D

Mitigation:

- Validate in Task 3 before backend work.
- If incompatible, add conversion to `model_exporter.py`.
- Keep `model_type` flexible: `ply`, `splat`, or `ksplat`.

### Risk: COLMAP fails on机房 video

Mitigation:

- Use short, slow, well-lit test video.
- Start with a single rack area, not the whole room.
- Use `sequential_matcher`.
- Keep intermediate COLMAP logs.

### Risk: CPU training is too slow

Mitigation:

- Default `fps=1`.
- Default `max_frames=50`.
- Default `iterations=300`.
- Treat quality as secondary in Phase 1.

### Risk: Long-running job blocks API server

Mitigation:

- Use FastAPI background task or a dedicated thread for Phase 1.
- Keep only one active job at a time if necessary.
- Move to Celery/RQ in Phase 2.

### Risk: Large model causes browser memory pressure

Mitigation:

- Use small test videos.
- Record model size in scene metadata.
- Add conversion/compression in Phase 2 if needed.

## Phase 1 Completion Checklist

- [ ] `check_environment.ps1` passes.
- [ ] `run_pipeline_test.ps1` creates `splat.ply`.
- [ ] Web viewer compatibility is confirmed or conversion is implemented.
- [ ] Backend upload API works.
- [ ] Job status API works.
- [ ] Logs API works.
- [ ] Scene API works.
- [ ] Frontend upload page works.
- [ ] Frontend job page shows status and logs.
- [ ] Frontend scene page loads generated model.
- [ ] User can rotate, zoom, and pan in the Web viewer.
- [ ] End-to-end verification is documented.

## Execution Handoff

Plan complete when this document is reviewed. Recommended execution order:

1. Task 1-3 first, because they validate the two main uncertainties: local toolchain and Web model compatibility.
2. Task 4-10 next, to wrap the working command-line pipeline in a backend.
3. Task 11-15 next, to build the Web upload/status/viewer experience.
4. Task 16 last, to verify the complete user-facing loop.

