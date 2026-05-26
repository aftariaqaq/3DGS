package com.local3dgs.capture.camera

import android.annotation.SuppressLint
import android.content.Context
import android.hardware.camera2.CameraCaptureSession
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraDevice
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureRequest
import android.media.MediaRecorder
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.util.Range
import android.view.Surface
import com.local3dgs.capture.capture.RecordedVideo
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class CameraVideoRecorder(
    private val context: Context
) {
    private val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
    private val cameraThread = HandlerThread("capture-camera")
    private val cameraHandler: Handler by lazy {
        cameraThread.start()
        Handler(cameraThread.looper)
    }
    private var cameraDevice: CameraDevice? = null
    private var captureSession: CameraCaptureSession? = null
    private var mediaRecorder: MediaRecorder? = null
    private var activeVideo: RecordedVideo? = null
    private var previewSurface: Surface? = null

    fun bindPreview(surface: Surface) {
        previewSurface = surface
        runCatching { startPreview() }
    }

    fun unbindPreview() {
        stopCameraSession()
        previewSurface = null
    }

    fun start(outputDir: File, settings: CaptureSettings = CaptureSettings.defaults()): RecordedVideo {
        stopCameraSession()
        outputDir.mkdirs()
        val cameraId = selectBackCameraId()
        val characteristics = cameraManager.getCameraCharacteristics(cameraId)
        val sensorOrientation = characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION) ?: 90
        val videoFile = File(outputDir, "recording_${System.currentTimeMillis()}.mp4")
        val recorder = createMediaRecorder(videoFile, settings)
        val device = openCameraBlocking(cameraId)
        val surface = recorder.surface
        val targets = listOfNotNull(previewSurface, surface)
        val session = createSessionBlocking(device, targets)
        val request = device.createCaptureRequest(CameraDevice.TEMPLATE_RECORD).apply {
            targets.forEach { target -> addTarget(target) }
            set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, Range(settings.fps, settings.fps))
            if (settings.stabilizationMode == StabilizationMode.OFF) {
                set(CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE, CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE_OFF)
                set(CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE, CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE_OFF)
            }
        }.build()
        session.setRepeatingRequest(request, null, cameraHandler)
        recorder.start()
        val recording = RecordedVideo(
            file = videoFile,
            width = settings.width,
            height = settings.height,
            fps = settings.fps,
            bitrateBps = settings.bitrateBps,
            codec = "video/avc",
            cameraId = cameraId,
            lensFacing = "back",
            sensorOrientationDegrees = sensorOrientation,
            stabilizationMode = settings.stabilizationMode.name.lowercase(),
            focusMode = settings.focusMode.name.lowercase()
        )
        mediaRecorder = recorder
        cameraDevice = device
        captureSession = session
        activeVideo = recording
        return recording
    }

    fun stop(): RecordedVideo? {
        val recording = activeVideo
        captureSession?.runCatching { stopRepeating() }
        captureSession?.runCatching { abortCaptures() }
        mediaRecorder?.runCatching { stop() }
        mediaRecorder?.reset()
        mediaRecorder?.release()
        stopCameraSession()
        mediaRecorder = null
        activeVideo = null
        runCatching { startPreview() }
        return recording
    }

    fun isRecording(): Boolean = activeVideo != null

    fun release() {
        if (isRecording()) {
            stop()
        }
        if (cameraThread.isAlive) {
            cameraThread.quitSafely()
        }
    }

    private fun createMediaRecorder(videoFile: File, settings: CaptureSettings): MediaRecorder {
        val recorder = if (Build.VERSION.SDK_INT >= 31) MediaRecorder(context) else MediaRecorder()
        recorder.setVideoSource(MediaRecorder.VideoSource.SURFACE)
        recorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
        recorder.setOutputFile(videoFile.absolutePath)
        recorder.setVideoEncodingBitRate(settings.bitrateBps)
        recorder.setVideoFrameRate(settings.fps)
        recorder.setVideoSize(settings.width, settings.height)
        recorder.setVideoEncoder(MediaRecorder.VideoEncoder.H264)
        recorder.prepare()
        return recorder
    }

    private fun startPreview() {
        val surface = previewSurface ?: return
        if (activeVideo != null || captureSession != null || cameraDevice != null) {
            return
        }
        val cameraId = selectBackCameraId()
        val device = openCameraBlocking(cameraId)
        val session = createSessionBlocking(device, listOf(surface))
        val request = device.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW).apply {
            addTarget(surface)
            set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_VIDEO)
        }.build()
        session.setRepeatingRequest(request, null, cameraHandler)
        cameraDevice = device
        captureSession = session
    }

    private fun stopCameraSession() {
        captureSession?.runCatching { stopRepeating() }
        captureSession?.runCatching { abortCaptures() }
        captureSession?.close()
        cameraDevice?.close()
        captureSession = null
        cameraDevice = null
    }

    private fun selectBackCameraId(): String {
        return cameraManager.cameraIdList.firstOrNull { cameraId ->
            val characteristics = cameraManager.getCameraCharacteristics(cameraId)
            characteristics.get(CameraCharacteristics.LENS_FACING) == CameraCharacteristics.LENS_FACING_BACK
        } ?: cameraManager.cameraIdList.first()
    }

    @SuppressLint("MissingPermission")
    private fun openCameraBlocking(cameraId: String): CameraDevice {
        val latch = CountDownLatch(1)
        var device: CameraDevice? = null
        var error: RuntimeException? = null
        cameraManager.openCamera(
            cameraId,
            object : CameraDevice.StateCallback() {
                override fun onOpened(camera: CameraDevice) {
                    device = camera
                    latch.countDown()
                }

                override fun onDisconnected(camera: CameraDevice) {
                    camera.close()
                    error = RuntimeException("camera disconnected")
                    latch.countDown()
                }

                override fun onError(camera: CameraDevice, code: Int) {
                    camera.close()
                    error = RuntimeException("camera open failed: $code")
                    latch.countDown()
                }
            },
            cameraHandler
        )
        if (!latch.await(5, TimeUnit.SECONDS)) {
            throw RuntimeException("camera open timed out")
        }
        error?.let { throw it }
        return requireNotNull(device) { "camera did not open" }
    }

    private fun createSessionBlocking(camera: CameraDevice, surfaces: List<Surface>): CameraCaptureSession {
        val latch = CountDownLatch(1)
        var session: CameraCaptureSession? = null
        var error: RuntimeException? = null
        camera.createCaptureSession(
            surfaces,
            object : CameraCaptureSession.StateCallback() {
                override fun onConfigured(configuredSession: CameraCaptureSession) {
                    session = configuredSession
                    latch.countDown()
                }

                override fun onConfigureFailed(failedSession: CameraCaptureSession) {
                    error = RuntimeException("camera session configure failed")
                    latch.countDown()
                }
            },
            cameraHandler
        )
        if (!latch.await(5, TimeUnit.SECONDS)) {
            throw RuntimeException("camera session configure timed out")
        }
        error?.let { throw it }
        return requireNotNull(session) { "camera session was not configured" }
    }
}
