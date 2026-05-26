package com.local3dgs.capture

import com.local3dgs.capture.export.CaptureBundleExporter
import com.local3dgs.capture.capture.ImuCaptureSession
import com.local3dgs.capture.capture.RecordedVideo
import java.io.File
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import java.util.zip.ZipFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CaptureBundleExporterTest {
    @Test
    fun sampleBundleZipContainsHostImportFiles() {
        val outputDir = createTempDir(prefix = "capture-export-test")

        val zip = CaptureBundleExporter().exportSampleBundle(outputDir)

        assertTrue(zip.name.endsWith(".zip"))
        ZipFile(zip).use { archive ->
            val names = archive.entries().asSequence().map { it.name }.toSet()
            assertEquals(
                setOf(
                    "video.mp4",
                    "metadata.json",
                    "frame_timestamps.jsonl",
                    "camera_samples.jsonl",
                    "imu_samples.jsonl",
                    "events.jsonl",
                    "checksums.json"
                ),
                names
            )
            val metadata = archive.getInputStream(archive.getEntry("metadata.json")).reader().readText()
            assertTrue(metadata.contains("\"capture_id\""))
            assertTrue(metadata.contains("\"zoom_ratio\""))
            assertTrue(metadata.contains("\"bitrate_bps\": 8000000"))

            val cameraSamples = archive.getInputStream(archive.getEntry("camera_samples.jsonl")).reader().readText()
            val lines = cameraSamples.trim().lines()
            assertEquals(1, lines.size)
            assertTrue(Json.parseToJsonElement(lines.single()).jsonObject.containsKey("sensor_timestamp_ns"))
        }

        outputDir.deleteRecursively()
    }

    @Test
    fun exportedBundleHasChecksumsForAllPayloadFiles() {
        val outputDir = createTempDir(prefix = "capture-export-test")

        val zip = CaptureBundleExporter().exportSampleBundle(outputDir)

        ZipFile(zip).use { archive ->
            val checksums = archive.getInputStream(archive.getEntry("checksums.json")).reader().readText()
            assertTrue(checksums.contains("\"video.mp4\""))
            assertTrue(checksums.contains("\"metadata.json\""))
            assertTrue(checksums.contains("\"events.jsonl\""))
        }

        outputDir.deleteRecursively()
    }

    @Test
    fun sessionBundleExportsRecordedImuSamples() {
        val outputDir = createTempDir(prefix = "capture-export-test")
        val session = ImuCaptureSession()
        session.start(10_000)
        session.recordSample(type = "gyro", timestampNs = 11_000, values = floatArrayOf(1.0f, 2.0f, 3.0f), accuracy = 3)
        session.stop(20_000)

        val zip = CaptureBundleExporter().exportSessionBundle(outputDir, session.snapshot())

        ZipFile(zip).use { archive ->
            val imuSamples = archive.getInputStream(archive.getEntry("imu_samples.jsonl")).reader().readText()
            assertTrue(imuSamples.contains("\"type\":\"gyro\""))
            assertTrue(imuSamples.contains("\"timestamp_ns\":11000"))
            val events = archive.getInputStream(archive.getEntry("events.jsonl")).reader().readText()
            assertTrue(events.contains("capture_started"))
            assertTrue(events.contains("capture_stopped"))
        }

        outputDir.deleteRecursively()
    }

    @Test
    fun recordedSessionBundleUsesCapturedVideoFile() {
        val outputDir = createTempDir(prefix = "capture-export-test")
        val video = File(outputDir, "recorded.mp4")
        video.writeBytes(byteArrayOf(0, 1, 2, 3, 4))
        val session = ImuCaptureSession()
        session.start(10_000)
        session.stop(1_010_000_000)

        val zip = CaptureBundleExporter().exportRecordedSessionBundle(
            outputDir = outputDir,
            snapshot = session.snapshot(),
            recordedVideo = RecordedVideo(
                file = video,
                width = 1920,
                height = 1080,
                fps = 30,
                bitrateBps = 20_000_000,
                codec = "video/avc",
                cameraId = "0",
                lensFacing = "back",
                sensorOrientationDegrees = 90,
                stabilizationMode = "off",
                focusMode = "continuous"
            )
        )

        ZipFile(zip).use { archive ->
            assertEquals(
                listOf<Byte>(0, 1, 2, 3, 4),
                archive.getInputStream(archive.getEntry("video.mp4")).readBytes().toList()
            )
            val metadata = archive.getInputStream(archive.getEntry("metadata.json")).reader().readText()
            assertTrue(metadata.contains("\"video_codec\": \"video/avc\""))
            assertTrue(metadata.contains("\"camera_id\": \"0\""))
            assertTrue(metadata.contains("\"bitrate_bps\": 20000000"))
            assertTrue(metadata.contains("\"stabilization_mode\": \"off\""))
            assertTrue(metadata.contains("\"focus_mode\": \"continuous\""))
        }

        outputDir.deleteRecursively()
    }

    private fun createTempDir(prefix: String): File {
        val dir = kotlin.io.path.createTempDirectory(prefix).toFile()
        dir.deleteOnExit()
        return dir
    }
}
