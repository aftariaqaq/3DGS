package com.local3dgs.capture

import com.local3dgs.capture.camera.CaptureSettings
import com.local3dgs.capture.camera.FocusMode
import com.local3dgs.capture.camera.StabilizationMode
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CaptureSettingsTest {
    @Test
    fun defaultsPreferStable1080pCapture() {
        val settings = CaptureSettings.defaults()

        assertEquals(1920, settings.width)
        assertEquals(1080, settings.height)
        assertEquals(30, settings.fps)
        assertEquals(20_000_000, settings.bitrateBps)
        assertEquals(FocusMode.CONTINUOUS, settings.focusMode)
        assertEquals(StabilizationMode.OFF, settings.stabilizationMode)
        assertEquals(1500, settings.warmupMs)
    }

    @Test
    fun bitrateLabelsMapToBitsPerSecond() {
        assertEquals(10_000_000, CaptureSettings.bitrateFromLabel("10 Mbps"))
        assertEquals(20_000_000, CaptureSettings.bitrateFromLabel("20 Mbps"))
        assertEquals(40_000_000, CaptureSettings.bitrateFromLabel("40 Mbps"))
        assertEquals(80_000_000, CaptureSettings.bitrateFromLabel("80 Mbps"))
        assertEquals(120_000_000, CaptureSettings.bitrateFromLabel("120 Mbps"))
    }

    @Test
    fun exposesExpandedCaptureOptions() {
        assertEquals(listOf("1280x720", "1920x1080", "3840x2160"), CaptureSettings.resolutionLabels)
        assertEquals(listOf("24", "30", "60"), CaptureSettings.fpsLabels)
        assertEquals(listOf("10 Mbps", "20 Mbps", "40 Mbps", "80 Mbps", "120 Mbps"), CaptureSettings.bitrateLabels)
    }

    @Test
    fun previewHeightPreservesSelectedAspectRatio() {
        assertEquals(675, CaptureSettings.previewHeightForWidth(parentWidth = 1200, videoWidth = 1920, videoHeight = 1080))
        assertEquals(675, CaptureSettings.previewHeightForWidth(parentWidth = 1200, videoWidth = 3840, videoHeight = 2160))
        assertEquals(900, CaptureSettings.previewHeightForWidth(parentWidth = 1200, videoWidth = 1280, videoHeight = 960))
    }

    @Test
    fun previewContentFitCenterDoesNotStretchPortraitDisplay() {
        val portraitFit = CaptureSettings.fitCenterContentSize(
            viewWidth = 1196,
            viewHeight = 672,
            videoWidth = 1920,
            videoHeight = 1080,
            isDisplayPortrait = true
        )
        assertTrue(portraitFit.first <= 1196)
        assertTrue(portraitFit.second <= 672)
        assertEquals(672, portraitFit.second)
        assertEquals(1080f / 1920f, portraitFit.first.toFloat() / portraitFit.second.toFloat(), 0.01f)

        val landscapeFit = CaptureSettings.fitCenterContentSize(
            viewWidth = 1196,
            viewHeight = 672,
            videoWidth = 1920,
            videoHeight = 1080,
            isDisplayPortrait = false
        )
        assertTrue(landscapeFit.first <= 1196)
        assertTrue(landscapeFit.second <= 672)
        assertEquals(672, landscapeFit.second)
        assertEquals(1920f / 1080f, landscapeFit.first.toFloat() / landscapeFit.second.toFloat(), 0.01f)
    }
}
