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
import com.local3dgs.capture.export.CaptureBundleExporter
import java.io.File

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }
        val label = TextView(this).apply {
            text = "3DGS Capture"
            textSize = 20f
        }
        val button = Button(this).apply {
            text = "Export sample bundle"
            setOnClickListener { exportSampleBundle() }
        }
        root.addView(label)
        root.addView(button)
        setContentView(root)
    }

    private fun exportSampleBundle() {
        try {
            val outputDir = File(cacheDir, "exports")
            val zip = CaptureBundleExporter().exportSampleBundle(outputDir)
            shareFile(zip)
        } catch (error: Exception) {
            Toast.makeText(this, error.message ?: "Export failed", Toast.LENGTH_LONG).show()
        }
    }

    private fun shareFile(file: File) {
        val uri: Uri = FileProvider.getUriForFile(this, "${packageName}.fileprovider", file)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/zip"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(intent, "Share capture bundle"))
    }
}
