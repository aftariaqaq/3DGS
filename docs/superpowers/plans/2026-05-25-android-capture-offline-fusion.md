# Android Capture Offline Fusion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working slice of Android-native raw capture plus host-side capture-bundle validation, timestamp-aware frame selection, and export into the existing CUDA 3DGS job layout.

**Architecture:** The Android app records a platform-neutral capture bundle and does not compute authoritative poses. The host Python packages validate the bundle, normalize metadata, score frames, attach sensor windows, and create selected-frame job inputs for COLMAP CUDA and Splatfacto/OpenSplat. The first milestone is deterministic and inspectable; VIO and hard pose fusion remain later extensions.

**Tech Stack:** Kotlin, Gradle Android project, Camera2/CameraX interop, Android SensorManager, Python 3.12, Pydantic or dataclasses, pytest, FFmpeg/OpenCV-compatible image analysis, existing FastAPI/CUDA pipeline.

---

## File Structure

- `apps/capture-android/`: Android-native capture app project.
- `apps/capture-android/app/src/main/java/.../`: Kotlin source.
- `apps/capture-android/app/src/test/java/.../`: JVM unit tests for serializers and manifest builders.
- `packages/capture_schema/`: Python schema models, JSONL readers, checksum validation, bundle import.
- `packages/sensor_fusion/`: timestamp alignment, sensor windowing, motion statistics, conflict report primitives.
- `packages/frame_select/`: frame quality scoring and deterministic keyframe selection.
- `packages/pipeline/`: capture-to-job command glue for existing `data/jobs/<job_id>` layout.
- `tests/capture_schema/`: host-side schema and import tests.
- `tests/sensor_fusion/`: host-side alignment/windowing tests.
- `tests/frame_select/`: host-side scoring and selection tests.
- `tests/pipeline/`: capture-to-job export tests.
- `scripts/ops/import_capture.ps1`: PowerShell wrapper for host import/select command.
- `README-CUDA.md`: add capture workflow section after CLI path exists.

## Task 1: Host Package Skeleton

**Files:**
- Create: `packages/capture_schema/__init__.py`
- Create: `packages/capture_schema/models.py`
- Create: `packages/capture_schema/jsonl.py`
- Create: `packages/capture_schema/checksums.py`
- Create: `packages/capture_schema/validator.py`
- Create: `tests/capture_schema/test_models.py`
- Create: `tests/capture_schema/test_checksums.py`

- [ ] **Step 1: Write failing model tests**

Create tests that build a minimal valid `metadata.json`, `frame_timestamps` record, camera sample, IMU sample, event, and checksum manifest.

Run:

```powershell
$env:PYTHONPATH="$PWD"
python -m pytest tests/capture_schema/test_models.py -v
```

Expected: fail because `packages.capture_schema.models` does not exist.

- [ ] **Step 2: Implement schema models**

Implement typed models for:

- `CaptureMetadata`
- `FrameTimestamp`
- `CameraSample`
- `ImuSample`
- `CaptureEvent`
- `ChecksumManifest`

Required metadata fields must match the spec. Optional camera geometry fields must include `zoom_ratio`, `scaler_crop_region`, AE/AF/AWB lock flags, calibration profile, camera-to-IMU transform, and time offset.

- [ ] **Step 3: Implement JSONL helpers**

Add `read_jsonl(path)` and `write_jsonl(path, records)` with UTF-8 encoding, one JSON object per line, and useful validation errors containing path and line number.

- [ ] **Step 4: Implement checksum validation**

Add:

```python
def sha256_file(path: Path) -> str: ...
def validate_checksums(bundle_root: Path, manifest: ChecksumManifest) -> list[str]: ...
```

Return a list of human-readable errors instead of throwing on the first mismatch.

- [ ] **Step 5: Run tests**

Run:

```powershell
$env:PYTHONPATH="$PWD"
python -m pytest tests/capture_schema -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add packages/capture_schema tests/capture_schema
git commit -m "feat: add capture bundle schema validation"
```

## Task 2: Bundle Import And Report

**Files:**
- Create: `packages/capture_schema/importer.py`
- Create: `packages/capture_schema/report.py`
- Create: `tests/capture_schema/test_importer.py`

- [ ] **Step 1: Write failing importer tests**

Use a temporary bundle directory with `video.mp4`, JSON files, JSONL files, and checksums. Assert importer copies to `data/captures/<capture_id>/raw`, writes normalized metadata to `normalized/metadata.json`, and writes `reports/import_report.json`.

- [ ] **Step 2: Implement import directory support**

Implement:

```python
def import_capture_bundle(source: Path, captures_root: Path, capture_id: str | None = None) -> ImportReport: ...
```

Support directory sources first. Zip support can be a second pass in the same function if simple.

- [ ] **Step 3: Validate geometry controls**

Report warnings when:

- `zoom_ratio` is missing or not `1.0`
- `scaler_crop_region` changes across samples
- stabilization mode is enabled or unknown
- lens intrinsics/distortion are missing
- AE/AF/AWB lock flags are false or unknown

- [ ] **Step 4: Run tests**

```powershell
$env:PYTHONPATH="$PWD"
python -m pytest tests/capture_schema -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add packages/capture_schema tests/capture_schema
git commit -m "feat: import capture bundles with reports"
```

## Task 3: Sensor Timeline And Windowing

**Files:**
- Create: `packages/sensor_fusion/__init__.py`
- Create: `packages/sensor_fusion/timeline.py`
- Create: `packages/sensor_fusion/windows.py`
- Create: `packages/sensor_fusion/diagnostics.py`
- Create: `tests/sensor_fusion/test_timeline.py`
- Create: `tests/sensor_fusion/test_windows.py`

- [ ] **Step 1: Write failing alignment tests**

Create synthetic frame timestamps and IMU samples. Assert nearest-neighbor and interval queries return expected samples.

- [ ] **Step 2: Implement timeline alignment**

Implement:

```python
def nearest_sample(samples, timestamp_ns): ...
def samples_between(samples, start_ns, end_ns): ...
def frame_time_ns(frame): ...
```

Use `sensor_timestamp_ns` when present, otherwise convert `pts_us` to ns relative to capture start.

- [ ] **Step 3: Implement sensor windows**

For each frame, compute:

- gyro sample count
- gyro magnitude mean/max
- acceleration magnitude mean/max
- rotation-vector availability
- metadata window completeness

- [ ] **Step 4: Implement diagnostic flags**

Flag:

- `fast_rotation`
- `high_acceleration`
- `metadata_missing`
- `exposure_jump_nearby`
- `focus_jump_nearby`
- `zoom_or_crop_change_nearby`
- `stabilization_change_nearby`

- [ ] **Step 5: Run tests**

```powershell
$env:PYTHONPATH="$PWD"
python -m pytest tests/sensor_fusion -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add packages/sensor_fusion tests/sensor_fusion
git commit -m "feat: add capture sensor timeline windowing"
```

## Task 4: Deterministic Frame Scoring

**Files:**
- Create: `packages/frame_select/scoring.py`
- Create: `packages/frame_select/selection.py`
- Create: `packages/frame_select/outputs.py`
- Create: `tests/frame_select/test_scoring.py`
- Create: `tests/frame_select/test_selection.py`

- [ ] **Step 1: Write failing scoring tests**

Use tiny generated images or simple arrays to test sharp, blurred, dark, bright, and duplicate frames. Do not require real test videos.

- [ ] **Step 2: Implement image quality scores**

Implement deterministic scores:

- blur score using Laplacian variance or equivalent
- exposure score from luminance histogram
- texture score from gradient/entropy approximation
- duplicate score using downscaled grayscale difference

- [ ] **Step 3: Implement keep/reject reasons**

Each candidate frame must produce:

```json
{
  "frame_index": 12,
  "selected": true,
  "score": 0.82,
  "reasons": ["sharp", "motion_diverse"]
}
```

Reject reasons include blur, exposure, duplicate, too close temporally, fast rotation, metadata jump, and max-frame cap.

- [ ] **Step 4: Run tests**

```powershell
$env:PYTHONPATH="$PWD"
python -m pytest tests/frame_select -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add packages/frame_select tests/frame_select
git commit -m "feat: add deterministic capture frame scoring"
```

## Task 5: Capture-To-Job CLI

**Files:**
- Create: `packages/pipeline/__init__.py`
- Create: `packages/pipeline/capture_to_job.py`
- Create: `packages/pipeline/__main__.py`
- Create: `tests/pipeline/test_capture_to_job.py`
- Create: `scripts/ops/import_capture.ps1`

- [ ] **Step 1: Write failing pipeline test**

Create a synthetic imported capture and assert `create_job_from_capture(...)` writes:

```text
data/jobs/<job_id>/images/
data/jobs/<job_id>/capture/selected_frames.jsonl
data/jobs/<job_id>/capture/frame_scores.jsonl
data/jobs/<job_id>/capture/sensor_windows.jsonl
data/jobs/<job_id>/capture/import_report.json
```

- [ ] **Step 2: Implement pipeline function**

Implement:

```python
def create_job_from_capture(capture_root: Path, jobs_root: Path, job_id: str, max_frames: int) -> Path: ...
```

Copy or extract selected frame images into the existing `images/` directory expected by COLMAP.

- [ ] **Step 3: Implement CLI**

Support:

```powershell
python -m packages.pipeline import-capture D:\captures\capture_001 --job-id job_capture_001 --max-frames 700
```

The command should print the created job directory and report path.

- [ ] **Step 4: Add PowerShell wrapper**

Create `scripts/ops/import_capture.ps1` with parameters:

- `CapturePath`
- `JobId`
- `MaxFrames`
- `CapturesRoot`
- `JobsRoot`

- [ ] **Step 5: Run tests**

```powershell
$env:PYTHONPATH="$PWD"
python -m pytest tests/capture_schema tests/sensor_fusion tests/frame_select tests/pipeline -v
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add packages/pipeline tests/pipeline scripts/ops/import_capture.ps1
git commit -m "feat: create cuda jobs from capture bundles"
```

## Task 6: Android Project Skeleton

**Files:**
- Create: `apps/capture-android/settings.gradle.kts`
- Create: `apps/capture-android/build.gradle.kts`
- Create: `apps/capture-android/app/build.gradle.kts`
- Create: `apps/capture-android/app/src/main/AndroidManifest.xml`
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt`
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/model/CaptureModels.kt`
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/export/JsonlWriter.kt`
- Create: `apps/capture-android/app/src/test/java/com/local3dgs/capture/CaptureModelsTest.kt`

- [ ] **Step 1: Create minimal Gradle Android project**

Use Kotlin and Android application plugin versions available on the target dev machine. Keep the app simple and avoid product polish.

- [ ] **Step 2: Add permissions**

Manifest permissions:

- `CAMERA`
- `RECORD_AUDIO` only if audio is kept; omit if no audio
- `BODY_SENSORS` only if needed by selected sensors
- foreground service permissions if recording uses a service

- [ ] **Step 3: Add data models and JSONL serializer tests**

Test that metadata, camera samples, IMU samples, events, and frame timestamps serialize with the same field names as the host schema.

- [ ] **Step 4: Run Android unit tests**

```powershell
cd apps\capture-android
.\gradlew testDebugUnitTest
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add apps/capture-android
git commit -m "feat: add android capture app skeleton"
```

## Task 7: Android Recording Prototype

**Files:**
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt`
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraController.kt`
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/sensors/SensorRecorder.kt`
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/export/CaptureExporter.kt`

- [ ] **Step 1: Implement preview and record button**

Use Camera2 or CameraX with Camera2 interop. Prefer the path that exposes camera metadata and timestamps reliably.

- [ ] **Step 2: Lock geometry defaults**

During capture:

- fixed `camera_id`
- fixed resolution and frame rate
- `zoom_ratio = 1.0` when supported
- no user zoom
- AE/AF/AWB warmup, then lock when supported
- stabilization disabled or logged

- [ ] **Step 3: Record IMU streams**

Record gyro and accelerometer by default. Record magnetometer, rotation vector, and game rotation vector when available.

- [ ] **Step 4: Export bundle directory**

Write `video.mp4`, `metadata.json`, JSONL files, and `checksums.json`.

- [ ] **Step 5: Manual smoke test**

Install on one Android device, record 30 seconds, export bundle, and validate it on host:

```powershell
$env:PYTHONPATH="$PWD"
python -m packages.capture_schema validate D:\captures\capture_test
```

Expected: validation passes with zero errors; warnings are acceptable for unsupported metadata.

- [ ] **Step 6: Commit**

```powershell
git add apps/capture-android
git commit -m "feat: record android capture bundles"
```

## Task 8: Documentation And End-To-End Smoke

**Files:**
- Modify: `README-CUDA.md`
- Create: `docs/capture-workflow.md`
- Modify: `packages/frame_select/README.md`
- Modify: `packages/pipeline/README.md`

- [ ] **Step 1: Document capture workflow**

Document:

- Android capture settings
- export bundle contents
- host validation
- frame selection
- job creation
- feeding existing CUDA COLMAP/training

- [ ] **Step 2: Run full host test suite**

```powershell
$env:PYTHONPATH="$PWD"
python -m pytest apps/api/tests tests -v
```

Expected: pass.

- [ ] **Step 3: Run package smoke command**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ops\package_cuda_release.ps1 -PackageName capture-fusion-smoke.zip
```

Expected: creates `artifacts/capture-fusion-smoke.zip` without cache files.

- [ ] **Step 4: Commit**

```powershell
git add README-CUDA.md docs/capture-workflow.md packages/frame_select/README.md packages/pipeline/README.md
git commit -m "docs: add capture fusion workflow"
```

## Review And Execution Notes

- Use `superpowers:test-driven-development` for host Python features.
- Use `superpowers:verification-before-completion` before claiming each task complete.
- Do not introduce ARCore.
- Do not treat Android rotation vectors as ground-truth pose.
- Do not inject hard poses into COLMAP in this milestone.
- Keep Android and host schema field names aligned.
- Keep generated captures, videos, and jobs out of git.

