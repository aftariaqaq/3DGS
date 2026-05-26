package com.local3dgs.capture.capture

import com.local3dgs.capture.model.CaptureEvent
import com.local3dgs.capture.model.ImuSample

data class ImuCaptureSnapshot(
    val startedMonotonicNs: Long,
    val stoppedMonotonicNs: Long,
    val imuSamples: List<ImuSample>,
    val events: List<CaptureEvent>
)

class ImuCaptureSession {
    private val imuSamples = mutableListOf<ImuSample>()
    private val events = mutableListOf<CaptureEvent>()
    private var recording = false
    private var startedMonotonicNs = 0L
    private var stoppedMonotonicNs = 0L

    fun start(timestampNs: Long) {
        imuSamples.clear()
        events.clear()
        recording = true
        startedMonotonicNs = timestampNs
        stoppedMonotonicNs = timestampNs
        events.add(CaptureEvent(timestampNs = timestampNs, type = "capture_started", message = "IMU capture started"))
    }

    fun stop(timestampNs: Long) {
        if (!recording) {
            return
        }
        recording = false
        stoppedMonotonicNs = timestampNs
        events.add(CaptureEvent(timestampNs = timestampNs, type = "capture_stopped", message = "IMU capture stopped"))
    }

    fun recordSample(type: String, timestampNs: Long, values: FloatArray, accuracy: Int?) {
        if (!recording || values.size < 3) {
            return
        }
        imuSamples.add(
            ImuSample(
                type = type,
                timestampNs = timestampNs,
                x = values[0],
                y = values[1],
                z = values[2],
                w = values.getOrNull(3),
                accuracy = accuracy
            )
        )
    }

    fun isRecording(): Boolean = recording

    fun snapshot(): ImuCaptureSnapshot {
        return ImuCaptureSnapshot(
            startedMonotonicNs = startedMonotonicNs,
            stoppedMonotonicNs = stoppedMonotonicNs,
            imuSamples = imuSamples.toList(),
            events = events.toList()
        )
    }
}
