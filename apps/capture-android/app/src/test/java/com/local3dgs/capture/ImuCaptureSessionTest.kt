package com.local3dgs.capture

import com.local3dgs.capture.capture.ImuCaptureSession
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ImuCaptureSessionTest {
    @Test
    fun sessionRecordsEventsAndSamplesBetweenStartAndStop() {
        val session = ImuCaptureSession()

        session.start(1_000)
        session.recordSample(type = "gyro", timestampNs = 1_100, values = floatArrayOf(1.0f, 2.0f, 3.0f), accuracy = 3)
        session.recordSample(type = "accelerometer", timestampNs = 1_200, values = floatArrayOf(0.0f, 0.0f, 9.8f), accuracy = 3)
        session.stop(2_000)

        val capture = session.snapshot()
        assertEquals(2, capture.imuSamples.size)
        assertEquals("gyro", capture.imuSamples[0].type)
        assertEquals(1_000, capture.startedMonotonicNs)
        assertEquals(2_000, capture.stoppedMonotonicNs)
        assertTrue(capture.events.any { it.type == "capture_started" })
        assertTrue(capture.events.any { it.type == "capture_stopped" })
    }

    @Test
    fun sessionIgnoresSamplesWhenNotRecording() {
        val session = ImuCaptureSession()

        session.recordSample(type = "gyro", timestampNs = 1_100, values = floatArrayOf(1.0f, 2.0f, 3.0f), accuracy = 3)

        assertTrue(session.snapshot().imuSamples.isEmpty())
    }
}
