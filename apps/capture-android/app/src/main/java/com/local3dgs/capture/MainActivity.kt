package com.local3dgs.capture

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.graphics.SurfaceTexture
import android.view.Surface
import android.view.TextureView
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.local3dgs.capture.camera.CameraVideoRecorder
import com.local3dgs.capture.camera.CaptureSettings
import com.local3dgs.capture.camera.CaptureSettingsStore
import com.local3dgs.capture.capture.ImuCaptureSession
import com.local3dgs.capture.capture.ImuSensorRecorder
import com.local3dgs.capture.capture.RecordedVideo
import com.local3dgs.capture.export.CaptureBundleExporter
import com.local3dgs.capture.ui.AspectTextureView
import java.io.File

class MainActivity : Activity() {
    private val imuSession = ImuCaptureSession()
    private lateinit var imuRecorder: ImuSensorRecorder
    private lateinit var videoRecorder: CameraVideoRecorder
    private lateinit var settingsStore: CaptureSettingsStore
    private lateinit var statusText: TextView
    private lateinit var previewView: AspectTextureView
    private var previewSurface: Surface? = null
    private var recordedVideo: RecordedVideo? = null
    private var currentSettings: CaptureSettings = CaptureSettings.defaults()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        imuRecorder = ImuSensorRecorder(this, imuSession)
        videoRecorder = CameraVideoRecorder(this)
        settingsStore = CaptureSettingsStore(this)
        currentSettings = settingsStore.load()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }
        val label = TextView(this).apply {
            text = UiText.APP_TITLE
            textSize = 20f
        }
        statusText = TextView(this).apply {
            text = UiText.STATUS_READY
        }
        previewView = AspectTextureView(this).apply {
            setAspectRatio(currentSettings.width, currentSettings.height)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
            surfaceTextureListener = object : TextureView.SurfaceTextureListener {
                override fun onSurfaceTextureAvailable(surfaceTexture: SurfaceTexture, width: Int, height: Int) {
                    surfaceTexture.setDefaultBufferSize(currentSettings.width, currentSettings.height)
                    previewSurface = Surface(surfaceTexture).also { surface -> videoRecorder.bindPreview(surface) }
                    statusText.text = UiText.STATUS_PREVIEW
                }

                override fun onSurfaceTextureSizeChanged(surfaceTexture: SurfaceTexture, width: Int, height: Int) = Unit

                override fun onSurfaceTextureDestroyed(surfaceTexture: SurfaceTexture): Boolean {
                    videoRecorder.unbindPreview()
                    previewSurface?.release()
                    previewSurface = null
                    return true
                }

                override fun onSurfaceTextureUpdated(surfaceTexture: SurfaceTexture) = Unit
            }
        }
        val settingsButton = Button(this).apply {
            text = UiText.OPEN_SETTINGS
            setOnClickListener { startActivity(Intent(this@MainActivity, SettingsActivity::class.java)) }
        }
        val startButton = Button(this).apply {
            text = UiText.START_CAPTURE
            setOnClickListener { startCapture() }
        }
        val stopButton = Button(this).apply {
            text = UiText.STOP_CAPTURE
            setOnClickListener { stopCapture() }
        }
        val exportButton = Button(this).apply {
            text = UiText.EXPORT_CAPTURE_BUNDLE
            setOnClickListener { exportCaptureBundle() }
        }
        root.addView(label)
        root.addView(previewView)
        root.addView(statusText)
        root.addView(settingsButton)
        root.addView(startButton)
        root.addView(stopButton)
        root.addView(exportButton)
        setContentView(root)
    }

    override fun onResume() {
        super.onResume()
        currentSettings = settingsStore.load()
        if (::previewView.isInitialized) {
            previewView.setAspectRatio(currentSettings.width, currentSettings.height)
            previewView.surfaceTexture?.setDefaultBufferSize(currentSettings.width, currentSettings.height)
        }
    }

    override fun onStop() {
        if (imuSession.isRecording() || videoRecorder.isRecording()) {
            stopCapture()
        }
        super.onStop()
    }

    override fun onDestroy() {
        previewSurface?.release()
        previewSurface = null
        videoRecorder.release()
        super.onDestroy()
    }

    private fun startCapture() {
        if (!hasCameraPermission()) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), CAMERA_PERMISSION_REQUEST)
            Toast.makeText(this, UiText.CAMERA_PERMISSION_REQUIRED, Toast.LENGTH_SHORT).show()
            return
        }
        val recordingsDir = File(cacheDir, "recordings")
        currentSettings = settingsStore.load()
        recordedVideo = videoRecorder.start(recordingsDir, currentSettings)
        imuRecorder.start()
        statusText.text = UiText.STATUS_RECORDING
        Toast.makeText(this, UiText.CAPTURE_STARTED, Toast.LENGTH_SHORT).show()
    }

    private fun stopCapture() {
        val stoppedVideo = if (videoRecorder.isRecording()) {
            videoRecorder.stop()
        } else {
            recordedVideo
        }
        if (imuSession.isRecording()) {
            imuRecorder.stop()
        }
        recordedVideo = stoppedVideo
        statusText.text = UiText.STATUS_READY
        Toast.makeText(this, UiText.CAPTURE_STOPPED, Toast.LENGTH_SHORT).show()
    }

    private fun exportCaptureBundle() {
        try {
            val outputDir = File(cacheDir, "exports")
            val snapshot = imuSession.snapshot()
            val video = recordedVideo
            val zip = if (video != null && video.file.exists() && video.file.length() > 0) {
                CaptureBundleExporter().exportRecordedSessionBundle(outputDir, snapshot, video)
            } else {
                CaptureBundleExporter().exportSessionBundle(outputDir, snapshot)
            }
            shareFile(zip)
        } catch (error: Exception) {
            Toast.makeText(this, error.message ?: UiText.EXPORT_FAILED, Toast.LENGTH_LONG).show()
        }
    }

    private fun shareFile(file: File) {
        val uri: Uri = FileProvider.getUriForFile(this, "${packageName}.fileprovider", file)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/zip"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(intent, UiText.SHARE_CAPTURE_BUNDLE))
    }

    private fun hasCameraPermission(): Boolean {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
    }

    companion object {
        private const val CAMERA_PERMISSION_REQUEST = 1001
    }
}
