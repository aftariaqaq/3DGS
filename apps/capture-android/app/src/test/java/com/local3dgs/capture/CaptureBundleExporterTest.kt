package com.local3dgs.capture

import com.local3dgs.capture.export.CaptureBundleExporter
import java.io.File
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

    private fun createTempDir(prefix: String): File {
        val dir = kotlin.io.path.createTempDirectory(prefix).toFile()
        dir.deleteOnExit()
        return dir
    }
}
