package com.local3dgs.capture

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.FileProvider
import com.local3dgs.capture.capture.ImuCaptureSession
import com.local3dgs.capture.capture.ImuSensorRecorder
import com.local3dgs.capture.export.CaptureBundleExporter
import java.io.File

class MainActivity : Activity() {
    private val imuSession = ImuCaptureSession()
    private lateinit var imuRecorder: ImuSensorRecorder

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        imuRecorder = ImuSensorRecorder(this, imuSession)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }
        val label = TextView(this).apply {
            text = UiText.APP_TITLE
            textSize = 20f
        }
        val startButton = Button(this).apply {
            text = UiText.START_IMU_CAPTURE
            setOnClickListener { startImuCapture() }
        }
        val stopButton = Button(this).apply {
            text = UiText.STOP_IMU_CAPTURE
            setOnClickListener { stopImuCapture() }
        }
        val exportButton = Button(this).apply {
            text = UiText.EXPORT_CAPTURE_BUNDLE
            setOnClickListener { exportCaptureBundle() }
        }
        root.addView(label)
        root.addView(startButton)
        root.addView(stopButton)
        root.addView(exportButton)
        setContentView(root)
    }

    override fun onStop() {
        if (imuSession.isRecording()) {
            imuRecorder.stop()
        }
        super.onStop()
    }

    private fun startImuCapture() {
        imuRecorder.start()
        Toast.makeText(this, UiText.CAPTURE_STARTED, Toast.LENGTH_SHORT).show()
    }

    private fun stopImuCapture() {
        imuRecorder.stop()
        Toast.makeText(this, UiText.CAPTURE_STOPPED, Toast.LENGTH_SHORT).show()
    }

    private fun exportCaptureBundle() {
        try {
            val outputDir = File(cacheDir, "exports")
            val snapshot = imuSession.snapshot()
            val zip = CaptureBundleExporter().exportSessionBundle(outputDir, snapshot)
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
}
