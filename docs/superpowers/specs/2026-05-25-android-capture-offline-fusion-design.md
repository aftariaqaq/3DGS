# Android Capture And Offline Fusion Design

## Decision

Build an Android-native capture app plus a host-side Python fusion pipeline.

The Android app records raw observations, not authoritative pose. The host pipeline validates the capture package, aligns timelines, extracts and scores frames, uses sensors as weak priors and diagnostics, and prepares data for COLMAP CUDA and Nerfstudio Splatfacto.

The first implementation targets Android only, but the exported capture format is platform-neutral so iOS, 360 cameras, or other capture clients can be added later.

## Goals

- Capture video and sensor data with reliable timestamps.
- Avoid ARCore as a dependency.
- Avoid treating phone realtime pose as ground truth.
- Preserve enough raw data for host-side fusion and debugging.
- Improve frame selection before COLMAP so mapper time and failure rate go down.
- Produce outputs that can enter the existing CUDA pipeline.

## Non-Goals

- No iOS app in the first pass.
- No realtime SLAM/VIO requirement on device.
- No hard pose injection into COLMAP in the first pass.
- No mobile-side 3DGS training.
- No cloud synchronization requirement.

## Architecture

```text
Android capture app
  -> capture bundle zip or directory
  -> host bundle validator
  -> timestamp alignment
  -> frame extraction
  -> quality scoring
  -> IMU and camera metadata windowing
  -> keyframe selection
  -> COLMAP CUDA input
  -> Splatfacto/OpenSplat training input
```

The Android app is intentionally simple: capture, monitor, export. It does not decide final frame selection and does not claim final camera poses.

The host pipeline owns all interpretation. It compares image-derived geometry, sensor timelines, and COLMAP diagnostics. If COLMAP and sensor signals conflict, COLMAP remains the geometry authority when reprojection quality is good; sensor data becomes a weak prior and failure detector.

## Capture Bundle Format

Each capture exports a directory or zip:

```text
capture_<capture_id>/
  video.mp4
  metadata.json
  frame_timestamps.jsonl
  camera_samples.jsonl
  imu_samples.jsonl
  events.jsonl
  checksums.json
```

### `metadata.json`

Required fields:

- `schema_version`
- `capture_id`
- `app_version`
- `platform`
- `device_manufacturer`
- `device_model`
- `android_api_level`
- `camera_id`
- `lens_facing`
- `sensor_orientation_degrees`
- `video_width`
- `video_height`
- `target_fps`
- `actual_video_duration_us`
- `video_codec`
- `bitrate_bps`
- `started_monotonic_ns`
- `stopped_monotonic_ns`

Optional fields:

- `lens_intrinsics`
- `lens_distortion`
- `physical_sensor_size`
- `focal_lengths`
- `stabilization_mode`
- `exposure_mode`
- `focus_mode`
- `white_balance_mode`

### `frame_timestamps.jsonl`

One record per encoded or observed frame when possible:

```json
{"frame_index":0,"pts_us":0,"sensor_timestamp_ns":123456789,"monotonic_ns":123456900}
```

Fields:

- `frame_index`: zero-based frame index.
- `pts_us`: video presentation timestamp.
- `sensor_timestamp_ns`: closest camera sensor timestamp if available.
- `monotonic_ns`: app-side monotonic timestamp.

### `camera_samples.jsonl`

One record per Camera2 capture result when available:

```json
{"sensor_timestamp_ns":123456789,"exposure_time_ns":8333333,"iso":400,"focal_length_mm":5.43,"focus_distance_diopters":0.0,"aperture":1.8}
```

Target fields:

- exposure time
- ISO
- focal length
- focus distance
- aperture
- optical stabilization mode
- video stabilization mode
- lens intrinsics
- lens distortion
- rolling shutter skew if available
- auto exposure state
- autofocus state
- white balance state

### `imu_samples.jsonl`

One record per sensor sample:

```json
{"type":"gyro","timestamp_ns":123456789,"x":0.01,"y":-0.02,"z":0.03,"accuracy":3}
```

Supported sensor types:

- `gyro`
- `accelerometer`
- `magnetometer`
- `rotation_vector`
- `game_rotation_vector`

Rotation vectors are stored as weak orientation observations, not as trusted camera poses.

### `events.jsonl`

Events record capture context and anomalies:

```json
{"timestamp_ns":123456789,"type":"capture_started","message":"recording started"}
```

Event types:

- `capture_started`
- `capture_stopped`
- `dropped_frame`
- `exposure_jump`
- `focus_jump`
- `thermal_warning`
- `app_pause`
- `app_resume`
- `export_started`
- `export_completed`

### `checksums.json`

Maps file paths to SHA-256 hashes so host import can reject damaged packages.

## Android App Design

### Technology

- Kotlin.
- Android Camera2 or CameraX with Camera2 interop.
- MediaRecorder or MediaCodec based recording, selected during implementation after checking timestamp access trade-offs.
- Android SensorManager for IMU streams.
- Local file export to app storage, then share/save zip.

### Capture Mode

The first capture mode prioritizes repeatability:

- Target 4K or 1080p depending device capability.
- Target 30 fps by default.
- Fixed or logged exposure behavior.
- Fixed or logged focus behavior.
- Disable or log video stabilization if the device exposes the setting.
- Keep screen awake during capture.

### UI

First version screens:

- Capture screen with preview, record button, elapsed time, frame rate, sensor status.
- Quality strip showing warnings only: too dark, too bright, motion too fast, sensor unavailable, dropped frames.
- Export screen listing completed captures and export status.

No training, COLMAP, or 3D viewer inside the app.

## Host Fusion Pipeline

### Package Boundaries

- `packages/capture_schema`: schema definitions, validation, checksums, import.
- `packages/sensor_fusion`: timestamp alignment, sensor windowing, conflict diagnostics.
- `packages/frame_select`: image scoring and keyframe selection.
- `packages/pipeline`: connects capture imports to the existing CUDA job layout.

### Import Output

After import, host storage should contain:

```text
data/captures/<capture_id>/
  raw/
  normalized/
  reports/
```

The existing training jobs can then consume selected frames:

```text
data/jobs/<job_id>/
  images/
  capture/
    selected_frames.jsonl
    frame_scores.jsonl
    sensor_windows.jsonl
    import_report.json
```

### Frame Scoring

Each candidate frame gets:

- blur score
- exposure score
- entropy or texture score
- temporal distance from previous selected frame
- gyro magnitude window
- acceleration magnitude window
- exposure/focus stability flags
- duplicate or near-duplicate flag

### Selection Strategy

First version uses deterministic rules:

- Reject badly blurred frames.
- Reject extreme exposure frames.
- Reject frames near large exposure or focus jumps.
- Prefer frames separated by enough time and motion.
- Avoid long static runs.
- Avoid high angular velocity frames unless coverage is otherwise poor.
- Cap total selected frames by job target.

The output includes the reason each frame was kept or rejected.

## COLMAP Conflict Handling

Sensor data is used before and after COLMAP, not as hard truth inside COLMAP.

Before COLMAP:

- Use gyro and duplicate scoring to reduce redundant frames.
- Use motion segmentation to avoid feeding long unstable bursts.
- Optionally split captures into reconstruction segments.

After COLMAP:

- Compare COLMAP relative rotations with rotation-vector or gyro trend after time alignment.
- Compare COLMAP pose jumps against blur, exposure, and gyro windows.
- Mark suspicious frames and segments.
- Recommend resampling or segmenting when conflicts are large.

Conflict policy:

- If COLMAP has low reprojection error and consistent track coverage, trust COLMAP for geometry.
- If COLMAP has local jumps or poor track coverage, use sensor and image-quality signals to identify candidate bad frames.
- If sensor and COLMAP disagree globally, first suspect timestamp alignment, coordinate transform, stabilization, rolling shutter, or changing intrinsics.

## Interfaces

### CLI

Proposed host commands:

```powershell
python -m capture_schema validate D:\captures\capture_001.zip
python -m pipeline import-capture D:\captures\capture_001.zip --capture-id capture_001
python -m frame_select select data\captures\capture_001 --max-frames 700 --job-id job_capture_001
```

### API

The FastAPI app should eventually expose:

- `POST /api/captures/import`
- `GET /api/captures/{capture_id}`
- `GET /api/captures/{capture_id}/report`
- `POST /api/jobs/from-capture`

These endpoints can come after the CLI path works.

## Testing

Host-side tests:

- Validate good and bad bundle schemas.
- Reject checksum mismatches.
- Align synthetic video and IMU timestamps.
- Score synthetic sharp, blurred, dark, and duplicate frames.
- Select deterministic frame subsets with expected keep/reject reasons.

Android tests:

- Unit test bundle manifest generation.
- Unit test JSONL serializers.
- Instrumented smoke test for sensor availability where possible.

Manual acceptance:

- Record a 30 to 60 second Android capture.
- Export bundle.
- Validate bundle on host.
- Extract and select frames.
- Confirm selected frames include timestamps, quality scores, sensor windows, and keep/reject reasons.
- Feed selected frames to CUDA COLMAP and 3DGS training.

## Risks

- Android devices expose inconsistent Camera2 metadata.
- Encoded frame timestamps may not map perfectly to sensor timestamps.
- Video stabilization may crop or warp frames in ways that hurt geometry.
- Some devices throttle during long 4K capture.
- IMU coordinate frames and camera frames require careful transform handling.

Risk mitigation:

- Preserve raw metadata and clearly report missing fields.
- Prefer diagnostics over hidden corrections.
- Start with deterministic filtering before adding probabilistic fusion.
- Keep bundle format versioned.

## First Milestone

The first milestone is not a polished app. It is a measurement instrument:

- Android app records video plus metadata.
- Host validates and imports the capture.
- Host selects frames with explicit scoring.
- Existing CUDA pipeline can train from those selected frames.

