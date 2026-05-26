package com.local3dgs.capture.export

import com.local3dgs.capture.capture.ImuCaptureSnapshot
import com.local3dgs.capture.capture.RecordedVideo
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
            stabilizationMode = "off",
            focusMode = "continuous",
            zoomRatio = 1.0f,
            scalerCropRegion = listOf(0, 0, 1920, 1080),
            aeLockEnabled = true,
            afLockEnabled = true,
            awbLockEnabled = true
        )

        val payloads = buildPayloads(
            metadata = metadata,
            frameTimestamps = listOf(FrameTimestamp(frameIndex = 0, ptsUs = 0, sensorTimestampNs = 1_000, monotonicNs = 1_000)),
            cameraSamples = listOf(CameraSample(sensorTimestampNs = 1_000, zoomRatio = 1.0f, scalerCropRegion = listOf(0, 0, 1920, 1080))),
            imuSamples = listOf(ImuSample(type = "gyro", timestampNs = 1_000, x = 0.0f, y = 0.0f, z = 0.0f)),
            events = listOf(CaptureEvent(timestampNs = 1_000, type = "export_started", message = "sample export"))
        )
        return writeZip(outputDir, captureId, payloads)
    }

    fun exportSessionBundle(outputDir: File, snapshot: ImuCaptureSnapshot): File {
        outputDir.mkdirs()
        val captureId = "capture_imu_${System.currentTimeMillis()}"
        val durationUs = ((snapshot.stoppedMonotonicNs - snapshot.startedMonotonicNs).coerceAtLeast(0L)) / 1_000L
        val metadata = CaptureMetadata(
            schemaVersion = "1.0",
            captureId = captureId,
            appVersion = "0.1.0",
            platform = "android",
            deviceManufacturer = android.os.Build.MANUFACTURER ?: "unknown",
            deviceModel = android.os.Build.MODEL ?: "unknown",
            androidApiLevel = android.os.Build.VERSION.SDK_INT,
            cameraId = "imu_only",
            lensFacing = "back",
            sensorOrientationDegrees = 90,
            videoWidth = 1920,
            videoHeight = 1080,
            targetFps = 30,
            actualVideoDurationUs = durationUs.coerceAtLeast(1L),
            videoCodec = "imu_only_placeholder",
            bitrateBps = 8_000_000,
            startedMonotonicNs = snapshot.startedMonotonicNs,
            stoppedMonotonicNs = snapshot.stoppedMonotonicNs,
            stabilizationMode = "off",
            focusMode = "continuous",
            zoomRatio = 1.0f,
            scalerCropRegion = listOf(0, 0, 1920, 1080),
            aeLockEnabled = true,
            afLockEnabled = true,
            awbLockEnabled = true
        )
        val frameTime = snapshot.startedMonotonicNs
        val payloads = buildPayloads(
            metadata = metadata,
            frameTimestamps = listOf(FrameTimestamp(frameIndex = 0, ptsUs = 0, sensorTimestampNs = frameTime, monotonicNs = frameTime)),
            cameraSamples = listOf(CameraSample(sensorTimestampNs = frameTime, zoomRatio = 1.0f, scalerCropRegion = listOf(0, 0, 1920, 1080))),
            imuSamples = snapshot.imuSamples,
            events = snapshot.events
        )
        return writeZip(outputDir, captureId, payloads)
    }

    fun exportRecordedSessionBundle(outputDir: File, snapshot: ImuCaptureSnapshot, recordedVideo: RecordedVideo): File {
        outputDir.mkdirs()
        if (!recordedVideo.file.exists() || recordedVideo.file.length() <= 0) {
            throw IllegalArgumentException("recorded video is missing or empty")
        }
        val captureId = "capture_video_${System.currentTimeMillis()}"
        val durationUs = ((snapshot.stoppedMonotonicNs - snapshot.startedMonotonicNs).coerceAtLeast(0L)) / 1_000L
        val metadata = CaptureMetadata(
            schemaVersion = "1.0",
            captureId = captureId,
            appVersion = "0.1.0",
            platform = "android",
            deviceManufacturer = android.os.Build.MANUFACTURER ?: "unknown",
            deviceModel = android.os.Build.MODEL ?: "unknown",
            androidApiLevel = android.os.Build.VERSION.SDK_INT,
            cameraId = recordedVideo.cameraId,
            lensFacing = recordedVideo.lensFacing,
            sensorOrientationDegrees = recordedVideo.sensorOrientationDegrees,
            videoWidth = recordedVideo.width,
            videoHeight = recordedVideo.height,
            targetFps = recordedVideo.fps,
            actualVideoDurationUs = durationUs.coerceAtLeast(1L),
            videoCodec = recordedVideo.codec,
            bitrateBps = recordedVideo.bitrateBps.toLong(),
            startedMonotonicNs = snapshot.startedMonotonicNs,
            stoppedMonotonicNs = snapshot.stoppedMonotonicNs,
            stabilizationMode = recordedVideo.stabilizationMode,
            focusMode = recordedVideo.focusMode,
            zoomRatio = 1.0f,
            scalerCropRegion = listOf(0, 0, recordedVideo.width, recordedVideo.height),
            aeLockEnabled = true,
            afLockEnabled = true,
            awbLockEnabled = true
        )
        val frameTimestamps = buildFrameTimestamps(snapshot, recordedVideo.fps)
        val cameraSamples = frameTimestamps.map { frame ->
            CameraSample(
                sensorTimestampNs = frame.sensorTimestampNs ?: frame.monotonicNs ?: snapshot.startedMonotonicNs,
                zoomRatio = 1.0f,
                scalerCropRegion = listOf(0, 0, recordedVideo.width, recordedVideo.height)
            )
        }
        val payloads = buildPayloads(
            videoBytes = recordedVideo.file.readBytes(),
            metadata = metadata,
            frameTimestamps = frameTimestamps,
            cameraSamples = cameraSamples,
            imuSamples = snapshot.imuSamples,
            events = snapshot.events
        )
        return writeZip(outputDir, captureId, payloads)
    }

    private fun buildPayloads(
        metadata: CaptureMetadata,
        frameTimestamps: List<FrameTimestamp>,
        cameraSamples: List<CameraSample>,
        imuSamples: List<ImuSample>,
        events: List<CaptureEvent>
    ): LinkedHashMap<String, ByteArray> {
        return buildPayloads(
            videoBytes = "video placeholder\n".toByteArray(Charsets.UTF_8),
            metadata = metadata,
            frameTimestamps = frameTimestamps,
            cameraSamples = cameraSamples,
            imuSamples = imuSamples,
            events = events
        )
    }

    private fun buildPayloads(
        videoBytes: ByteArray,
        metadata: CaptureMetadata,
        frameTimestamps: List<FrameTimestamp>,
        cameraSamples: List<CameraSample>,
        imuSamples: List<ImuSample>,
        events: List<CaptureEvent>
    ): LinkedHashMap<String, ByteArray> {
        val payloads = linkedMapOf<String, ByteArray>()
        payloads["video.mp4"] = videoBytes
        payloads["metadata.json"] = json.encodeToString(CaptureMetadata.serializer(), metadata).toByteArray(Charsets.UTF_8)
        payloads["frame_timestamps.jsonl"] = jsonl(FrameTimestamp.serializer(), frameTimestamps)
        payloads["camera_samples.jsonl"] = jsonl(CameraSample.serializer(), cameraSamples)
        payloads["imu_samples.jsonl"] = jsonl(ImuSample.serializer(), imuSamples)
        payloads["events.jsonl"] = jsonl(CaptureEvent.serializer(), events)
        payloads["checksums.json"] = json.encodeToString(
            ChecksumManifest.serializer(),
            ChecksumManifest(payloads.mapValues { (_, bytes) -> sha256(bytes) })
        ).toByteArray(Charsets.UTF_8)
        return payloads
    }

    private fun buildFrameTimestamps(snapshot: ImuCaptureSnapshot, fps: Int): List<FrameTimestamp> {
        val started = snapshot.startedMonotonicNs
        val stopped = snapshot.stoppedMonotonicNs.coerceAtLeast(started)
        val stepNs = (1_000_000_000L / fps.coerceAtLeast(1)).coerceAtLeast(1L)
        val frames = mutableListOf<FrameTimestamp>()
        var timestamp = started
        var index = 0
        while (timestamp <= stopped) {
            frames.add(
                FrameTimestamp(
                    frameIndex = index,
                    ptsUs = ((timestamp - started) / 1_000L),
                    sensorTimestampNs = timestamp,
                    monotonicNs = timestamp
                )
            )
            timestamp += stepNs
            index += 1
        }
        return frames.ifEmpty {
            listOf(FrameTimestamp(frameIndex = 0, ptsUs = 0, sensorTimestampNs = started, monotonicNs = started))
        }
    }

    private fun writeZip(outputDir: File, captureId: String, payloads: Map<String, ByteArray>): File {
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
