package com.local3dgs.capture.export

import com.local3dgs.capture.model.CameraSample
import com.local3dgs.capture.model.CaptureEvent
import com.local3dgs.capture.model.CaptureMetadata
import com.local3dgs.capture.model.ChecksumManifest
import com.local3dgs.capture.model.FrameTimestamp
import com.local3dgs.capture.model.ImuSample
import java.io.ByteArrayOutputStream
import java.io.File
import java.security.MessageDigest
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlinx.serialization.KSerializer
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class CaptureBundleExporter(
    private val json: Json = Json {
        encodeDefaults = false
        explicitNulls = false
        prettyPrint = true
    }
) {
    private val jsonlJson = Json {
        encodeDefaults = false
        explicitNulls = false
        prettyPrint = false
    }

    fun exportSampleBundle(outputDir: File): File {
        outputDir.mkdirs()
        val captureId = "capture_sample_${System.currentTimeMillis()}"
        val payloads = linkedMapOf<String, ByteArray>()
        val metadata = CaptureMetadata(
            schemaVersion = "1.0",
            captureId = captureId,
            appVersion = "0.1.0",
            platform = "android",
            deviceManufacturer = android.os.Build.MANUFACTURER ?: "unknown",
            deviceModel = android.os.Build.MODEL ?: "unknown",
            androidApiLevel = android.os.Build.VERSION.SDK_INT,
            cameraId = "sample",
            lensFacing = "back",
            sensorOrientationDegrees = 90,
            videoWidth = 1920,
            videoHeight = 1080,
            targetFps = 30,
            actualVideoDurationUs = 1_000_000,
            videoCodec = "sample",
            bitrateBps = 8_000_000,
            startedMonotonicNs = 1_000,
            stoppedMonotonicNs = 1_001_000_000,
            zoomRatio = 1.0f,
            scalerCropRegion = listOf(0, 0, 1920, 1080),
            aeLockEnabled = true,
            afLockEnabled = true,
            awbLockEnabled = true
        )

        payloads["video.mp4"] = "sample video placeholder\n".toByteArray(Charsets.UTF_8)
        payloads["metadata.json"] = json.encodeToString(CaptureMetadata.serializer(), metadata).toByteArray(Charsets.UTF_8)
        payloads["frame_timestamps.jsonl"] = jsonl(
            FrameTimestamp.serializer(),
            listOf(FrameTimestamp(frameIndex = 0, ptsUs = 0, sensorTimestampNs = 1_000, monotonicNs = 1_000))
        )
        payloads["camera_samples.jsonl"] = jsonl(
            CameraSample.serializer(),
            listOf(CameraSample(sensorTimestampNs = 1_000, zoomRatio = 1.0f, scalerCropRegion = listOf(0, 0, 1920, 1080)))
        )
        payloads["imu_samples.jsonl"] = jsonl(
            ImuSample.serializer(),
            listOf(ImuSample(type = "gyro", timestampNs = 1_000, x = 0.0f, y = 0.0f, z = 0.0f))
        )
        payloads["events.jsonl"] = jsonl(
            CaptureEvent.serializer(),
            listOf(CaptureEvent(timestampNs = 1_000, type = "export_started", message = "sample export"))
        )
        payloads["checksums.json"] = json.encodeToString(
            ChecksumManifest.serializer(),
            ChecksumManifest(payloads.mapValues { (_, bytes) -> sha256(bytes) })
        ).toByteArray(Charsets.UTF_8)

        val zipFile = File(outputDir, "$captureId.zip")
        ZipOutputStream(zipFile.outputStream().buffered()).use { zip ->
            for ((name, bytes) in payloads) {
                zip.putNextEntry(ZipEntry(name))
                zip.write(bytes)
                zip.closeEntry()
            }
        }
        return zipFile
    }

    private fun <T> jsonl(serializer: KSerializer<T>, records: List<T>): ByteArray {
        val output = ByteArrayOutputStream()
        JsonlWriter(output, serializer, jsonlJson).use { writer ->
            records.forEach { writer.write(it) }
        }
        return output.toByteArray()
    }

    private fun sha256(bytes: ByteArray): String {
        val digest = MessageDigest.getInstance("SHA-256").digest(bytes)
        return digest.joinToString(separator = "") { value -> "%02x".format(value) }
    }
}
