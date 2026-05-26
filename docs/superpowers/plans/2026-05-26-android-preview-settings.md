# Android Preview And Capture Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real camera preview and a settings surface to the Android capture app so capture quality, focus, frame rate, resolution, bitrate, and stabilization behavior are visible and controllable before recording.

**Architecture:** Split the current single-screen button app into small Android-native units: a settings model, a settings panel, a preview/recording controller, and export wiring. Camera2 remains the capture backend because it can expose `CaptureResult.SENSOR_TIMESTAMP` and camera metadata needed for host-side IMU alignment.

**Tech Stack:** Kotlin, Android Camera2, `TextureView` or `SurfaceView`, `MediaRecorder`, Android `SensorManager`, JVM unit tests, ADB smoke tests, host Python capture importer.

---

## File Structure

- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt`
  - Owns screen composition, permission flow, button handlers, and high-level recording state.
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraVideoRecorder.kt`
  - Add preview surface support, settings application, capture callbacks, and metadata recording hooks.
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CaptureSettings.kt`
  - Immutable settings model for resolution, fps, bitrate, focus mode, stabilization, warmup, and timestamp strategy.
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraMetadataRecorder.kt`
  - Records per-frame `CaptureResult` data into frame timestamp and camera sample records.
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/ui/SettingsPanel.kt`
  - Builds a compact Chinese settings panel using native Android widgets.
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/export/CaptureBundleExporter.kt`
  - Export real frame timestamps and camera samples when available.
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/UiText.kt`
  - Add Chinese labels for preview/settings/status.
- Tests:
  - `apps/capture-android/app/src/test/java/com/local3dgs/capture/CaptureSettingsTest.kt`
  - `apps/capture-android/app/src/test/java/com/local3dgs/capture/CameraMetadataRecorderTest.kt`
  - `apps/capture-android/app/src/test/java/com/local3dgs/capture/CaptureBundleExporterTest.kt`
  - `apps/capture-android/app/src/test/java/com/local3dgs/capture/UiTextTest.kt`

## Task 1: Capture Settings Model

**Files:**
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CaptureSettings.kt`
- Create: `apps/capture-android/app/src/test/java/com/local3dgs/capture/CaptureSettingsTest.kt`

- [ ] **Step 1: Write failing tests**

Test default settings:

```kotlin
val settings = CaptureSettings.defaults()
assertEquals(1920, settings.width)
assertEquals(1080, settings.height)
assertEquals(30, settings.fps)
assertEquals(20_000_000, settings.bitrateBps)
assertEquals(FocusMode.CONTINUOUS, settings.focusMode)
assertEquals(StabilizationMode.OFF, settings.stabilizationMode)
```

Run:

```powershell
& "$env:USERPROFILE\.gradle\wrapper\dists\gradle-8.14.3-bin\cv11ve7ro1n3o1j4so8xd9n66\gradle-8.14.3\bin\gradle.bat" -p apps\capture-android testDebugUnitTest --tests com.local3dgs.capture.CaptureSettingsTest
```

Expected: fail because `CaptureSettings` does not exist.

- [ ] **Step 2: Implement settings model**

Add:

```kotlin
enum class FocusMode { CONTINUOUS, LOCK_CENTER_AFTER_WARMUP }
enum class StabilizationMode { OFF, ON_IF_NEEDED }

data class CaptureSettings(
    val width: Int,
    val height: Int,
    val fps: Int,
    val bitrateBps: Int,
    val focusMode: FocusMode,
    val stabilizationMode: StabilizationMode,
    val warmupMs: Long
) {
    companion object {
        fun defaults() = CaptureSettings(
            width = 1920,
            height = 1080,
            fps = 30,
            bitrateBps = 20_000_000,
            focusMode = FocusMode.CONTINUOUS,
            stabilizationMode = StabilizationMode.OFF,
            warmupMs = 1500
        )
    }
}
```

- [ ] **Step 3: Run tests**

Expected: pass.

- [ ] **Step 4: Commit**

```powershell
git add apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CaptureSettings.kt apps/capture-android/app/src/test/java/com/local3dgs/capture/CaptureSettingsTest.kt
git commit -m "feat: add android capture settings model"
```

## Task 2: Settings UI

**Files:**
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/ui/SettingsPanel.kt`
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt`
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/UiText.kt`
- Test: `apps/capture-android/app/src/test/java/com/local3dgs/capture/UiTextTest.kt`

- [ ] **Step 1: Write failing UI text tests**

Assert Chinese labels exist:

```kotlin
assertEquals("分辨率", UiText.SETTING_RESOLUTION)
assertEquals("帧率", UiText.SETTING_FPS)
assertEquals("码率", UiText.SETTING_BITRATE)
assertEquals("对焦", UiText.SETTING_FOCUS)
assertEquals("防抖", UiText.SETTING_STABILIZATION)
```

- [ ] **Step 2: Implement `SettingsPanel`**

Use native widgets:

- `Spinner` for resolution: `1920x1080`, later `3840x2160`
- `Spinner` for fps: `30`, later `60`
- `SeekBar` or `Spinner` for bitrate: `20 Mbps`, `40 Mbps`, `80 Mbps`
- `Spinner` for focus: continuous, center lock after warmup
- `Switch` for stabilization preference

Expose:

```kotlin
class SettingsPanel(context: Context) : LinearLayout(context) {
    fun currentSettings(): CaptureSettings
}
```

- [ ] **Step 3: Wire into MainActivity**

Layout order:

```text
Title
Preview Surface
Status text
Settings panel
Start / Stop / Export buttons
```

Keep it utilitarian; no marketing copy.

- [ ] **Step 4: Run Android unit tests**

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add apps/capture-android/app/src/main/java/com/local3dgs/capture/ui apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt apps/capture-android/app/src/main/java/com/local3dgs/capture/UiText.kt apps/capture-android/app/src/test/java/com/local3dgs/capture/UiTextTest.kt
git commit -m "feat: add android capture settings panel"
```

## Task 3: Camera Preview Pipeline

**Files:**
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraVideoRecorder.kt`
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt`

- [ ] **Step 1: Add preview surface API**

Add methods:

```kotlin
fun bindPreview(surface: Surface)
fun unbindPreview()
```

or use a `TextureView` callback in `MainActivity` and pass `Surface(texture)`.

- [ ] **Step 2: Configure Camera2 session with preview + recorder**

Before recording:

```text
CameraDevice
-> CaptureSession(previewSurface)
-> repeating preview request
```

When recording:

```text
CaptureSession(previewSurface, recorderSurface)
-> repeating record request targeting both surfaces
```

- [ ] **Step 3: Add preview status**

Status should show:

```text
预览中 / 准备对焦 / 录制中 / 已停止 / 导出完成
```

- [ ] **Step 4: Device smoke test**

Run:

```powershell
gradle -p apps\capture-android assembleDebug
adb install -r apps\capture-android\app\build\outputs\apk\debug\app-debug.apk
```

Expected:

- App opens with live preview.
- Preview is not black.
- Buttons remain visible.

- [ ] **Step 5: Commit**

```powershell
git add apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraVideoRecorder.kt apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt
git commit -m "feat: add android camera preview"
```

## Task 4: Focus, Warmup, And Capture Settings Application

**Files:**
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraVideoRecorder.kt`
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt`

- [ ] **Step 1: Apply settings to MediaRecorder**

Use:

```kotlin
settings.width
settings.height
settings.fps
settings.bitrateBps
```

- [ ] **Step 2: Apply settings to CaptureRequest**

Set:

```kotlin
CONTROL_AE_TARGET_FPS_RANGE = Range(settings.fps, settings.fps)
CONTROL_AF_MODE = CONTINUOUS_VIDEO or AUTO
CONTROL_VIDEO_STABILIZATION_MODE = OFF
LENS_OPTICAL_STABILIZATION_MODE = OFF when supported
```

- [ ] **Step 3: Add warmup before recording**

Flow:

```text
Start clicked
-> preview is active
-> run warmup request for settings.warmupMs
-> start MediaRecorder
-> start IMU
```

- [ ] **Step 4: Add center lock focus option**

If `LOCK_CENTER_AFTER_WARMUP`:

- Trigger AF.
- Wait for `CONTROL_AF_STATE_FOCUSED_LOCKED` or timeout.
- Then start recording.

- [ ] **Step 5: Device smoke test**

Expected:

- Video is visibly sharper than current no-preview recording.
- Recorded metadata marks chosen resolution, fps, bitrate, stabilization preference.

- [ ] **Step 6: Commit**

```powershell
git add apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraVideoRecorder.kt apps/capture-android/app/src/main/java/com/local3dgs/capture/MainActivity.kt
git commit -m "feat: apply android capture focus and quality settings"
```

## Task 5: Per-Frame Camera Metadata

**Files:**
- Create: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraMetadataRecorder.kt`
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/camera/CameraVideoRecorder.kt`
- Modify: `apps/capture-android/app/src/main/java/com/local3dgs/capture/export/CaptureBundleExporter.kt`
- Test: `apps/capture-android/app/src/test/java/com/local3dgs/capture/CameraMetadataRecorderTest.kt`
- Test: `apps/capture-android/app/src/test/java/com/local3dgs/capture/CaptureBundleExporterTest.kt`

- [ ] **Step 1: Write failing metadata tests**

Test that a synthetic metadata record produces:

- `FrameTimestamp(frameIndex=0, sensorTimestampNs=...)`
- `CameraSample(sensorTimestampNs=..., exposureTimeNs=..., iso=..., focusDistanceDiopters=...)`

- [ ] **Step 2: Add CaptureCallback**

In `setRepeatingRequest`, attach:

```kotlin
object : CameraCaptureSession.CaptureCallback() {
    override fun onCaptureCompleted(
        session: CameraCaptureSession,
        request: CaptureRequest,
        result: TotalCaptureResult
    ) {
        metadataRecorder.record(result)
    }
}
```

Record:

- `CaptureResult.SENSOR_TIMESTAMP`
- `SENSOR_EXPOSURE_TIME`
- `SENSOR_SENSITIVITY`
- `LENS_FOCUS_DISTANCE`
- `LENS_FOCAL_LENGTH`
- `CONTROL_AF_STATE`
- `CONTROL_AE_STATE`
- `CONTROL_AWB_STATE`

- [ ] **Step 3: Export real metadata**

`CaptureBundleExporter.exportRecordedSessionBundle(...)` should use recorded metadata first.

Fallback only if metadata is empty:

```text
estimated fps timestamps
```

- [ ] **Step 4: Host validation**

Pull a device capture and check:

```powershell
python -m packages.capture_schema import ...
python -m packages.pipeline process-capture ...
```

Expected:

- `frame_timestamps.jsonl` count is close to decoded frame count.
- timestamps come from camera sensor, not estimated fps.

- [ ] **Step 5: Commit**

```powershell
git add apps/capture-android/app/src/main/java/com/local3dgs/capture/camera apps/capture-android/app/src/main/java/com/local3dgs/capture/export/CaptureBundleExporter.kt apps/capture-android/app/src/test/java/com/local3dgs/capture
git commit -m "feat: record android per-frame camera metadata"
```

## Task 6: End-To-End Device Acceptance

**Files:**
- Modify: `docs/capture-workflow.md` if it exists, otherwise create it.
- Modify: `README-CUDA.md`

- [ ] **Step 1: Build and install**

```powershell
& "$env:USERPROFILE\.gradle\wrapper\dists\gradle-8.14.3-bin\cv11ve7ro1n3o1j4so8xd9n66\gradle-8.14.3\bin\gradle.bat" -p apps\capture-android testDebugUnitTest assembleDebug
adb install -r apps\capture-android\app\build\outputs\apk\debug\app-debug.apk
```

- [ ] **Step 2: Manual capture**

Record 20-30 seconds with:

- live preview visible
- 1080p
- 30 fps
- 20-40 Mbps
- stabilization off
- continuous focus or center lock focus

- [ ] **Step 3: Pull and validate capture**

```powershell
adb shell run-as com.local3dgs.capture ls -lt cache/exports
adb shell run-as com.local3dgs.capture toybox base64 cache/exports/<capture>.zip > artifacts\device-captures\<capture>.zip.b64
certutil -decode artifacts\device-captures\<capture>.zip.b64 artifacts\device-captures\<capture>.zip
```

- [ ] **Step 4: Host process**

```powershell
$env:PYTHONPATH="$PWD"
python -m packages.capture_schema import <capture-dir>
python -m packages.pipeline process-capture <imported-capture> --job-id job_preview_smoke --max-frames 100
```

Expected:

- `video.mp4` is visually sharp.
- `frame_timestamps.jsonl` contains real camera timestamps.
- `camera_samples.jsonl` contains per-frame camera metadata.
- `selected_frames.jsonl` is non-empty.
- `data/jobs/<job_id>/images` has selected frames.

- [ ] **Step 5: Document known limitations**

Include:

- no iOS yet
- no hard pose injection yet
- Camera2 timestamp quality depends on device implementation
- 4K support depends on device and thermal behavior

- [ ] **Step 6: Commit**

```powershell
git add README-CUDA.md docs/capture-workflow.md
git commit -m "docs: document android preview capture workflow"
```

## Notes

- Do not introduce ARCore as a dependency.
- Do not make real-time pose a hard requirement.
- Prefer Camera2 over system camera so timestamps, metadata, and settings are controlled.
- Keep generated captures, APKs, videos, and jobs out of git.
- If preview/recording session state becomes unstable, split `CameraVideoRecorder` into `CameraPreviewController` and `VideoRecorderController` before continuing.
