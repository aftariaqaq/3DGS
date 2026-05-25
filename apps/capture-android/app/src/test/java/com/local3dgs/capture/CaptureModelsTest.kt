package com.local3dgs.capture

import com.local3dgs.capture.export.JsonlWriter
import com.local3dgs.capture.model.CaptureMetadata
import com.local3dgs.capture.model.FrameTimestamp
import java.io.ByteArrayOutputStream
import kotlinx.serialization.json.Json
import org.junit.Assert.assertTrue
import org.junit.Test

class CaptureModelsTest {
    @Test
    fun metadataSerializesWithHostSchemaFieldNames() {
        val metadata = CaptureMetadata(
            schemaVersion = "1.0",
            captureId = "capture_001",
            appVersion = "0.1.0",
            platform = "android",
            deviceManufacturer = "Google",
            deviceModel = "Pixel",
            androidApiLevel = 35,
            cameraId = "0",
            lensFacing = "back",
            sensorOrientationDegrees = 90,
            videoWidth = 3840,
            videoHeight = 2160,
            targetFps = 30,
            actualVideoDurationUs = 1_000_000,
            videoCodec = "video/avc",
            bitrateBps = 80_000_000,
            startedMonotonicNs = 1_000,
            stoppedMonotonicNs = 1_001_000_000,
            zoomRatio = 1.0f,
            scalerCropRegion = listOf(0, 0, 3840, 2160),
            aeLockEnabled = true,
            afLockEnabled = true,
            awbLockEnabled = true
        )

        val encoded = Json.encodeToString(CaptureMetadata.serializer(), metadata)

        assertTrue(encoded.contains("\"capture_id\""))
        assertTrue(encoded.contains("\"zoom_ratio\""))
        assertTrue(encoded.contains("\"scaler_crop_region\""))
        assertTrue(encoded.contains("\"ae_lock_enabled\""))
    }

    @Test
    fun jsonlWriterWritesOneJsonObjectPerLine() {
        val output = ByteArrayOutputStream()
        JsonlWriter(output, FrameTimestamp.serializer()).use { writer ->
            writer.write(FrameTimestamp(frameIndex = 0, ptsUs = 0, sensorTimestampNs = 123))
            writer.write(FrameTimestamp(frameIndex = 1, ptsUs = 33_333, sensorTimestampNs = 456))
        }

        val lines = output.toString(Charsets.UTF_8.name()).trim().lines()
        assertTrue(lines.size == 2)
        assertTrue(lines[0].contains("\"frame_index\":0"))
        assertTrue(lines[1].contains("\"pts_us\":33333"))
    }
}
