package com.local3dgs.capture.camera

enum class FocusMode {
    CONTINUOUS,
    LOCK_CENTER_AFTER_WARMUP
}

enum class StabilizationMode {
    OFF,
    ON_IF_NEEDED
}

data class CaptureSettings(
    val width: Int,
    val height: Int,
    val fps: Int,
    val bitrateBps: Int,
    val focusMode: FocusMode,
    val stabilizationMode: StabilizationMode,
    val warmupMs: Long
) {
    companion object {
        val resolutionLabels = listOf("1280x720", "1920x1080", "3840x2160")
        val fpsLabels = listOf("24", "30", "60")
        val bitrateLabels = listOf("10 Mbps", "20 Mbps", "40 Mbps", "80 Mbps", "120 Mbps")

        fun defaults(): CaptureSettings {
            return CaptureSettings(
                width = 1920,
                height = 1080,
                fps = 30,
                bitrateBps = 20_000_000,
                focusMode = FocusMode.CONTINUOUS,
                stabilizationMode = StabilizationMode.OFF,
                warmupMs = 1500
            )
        }

        fun bitrateFromLabel(label: String): Int {
            return when (label) {
                "10 Mbps" -> 10_000_000
                "20 Mbps" -> 20_000_000
                "40 Mbps" -> 40_000_000
                "80 Mbps" -> 80_000_000
                "120 Mbps" -> 120_000_000
                else -> defaults().bitrateBps
            }
        }

        fun labelForBitrate(bitrateBps: Int): String {
            return when (bitrateBps) {
                10_000_000 -> "10 Mbps"
                20_000_000 -> "20 Mbps"
                40_000_000 -> "40 Mbps"
                80_000_000 -> "80 Mbps"
                120_000_000 -> "120 Mbps"
                else -> "20 Mbps"
            }
        }

        fun previewHeightForWidth(parentWidth: Int, videoWidth: Int, videoHeight: Int): Int {
            if (parentWidth <= 0 || videoWidth <= 0 || videoHeight <= 0) {
                return 0
            }
            return ((parentWidth.toLong() * videoHeight.toLong()) / videoWidth.toLong()).toInt()
        }

        fun previewHeightForDisplay(
            parentWidth: Int,
            videoWidth: Int,
            videoHeight: Int,
            isDisplayPortrait: Boolean
        ): Int {
            return if (isDisplayPortrait && videoWidth > videoHeight) {
                previewHeightForWidth(parentWidth, videoHeight, videoWidth)
            } else {
                previewHeightForWidth(parentWidth, videoWidth, videoHeight)
            }
        }

        fun fitCenterContentSize(
            viewWidth: Int,
            viewHeight: Int,
            videoWidth: Int,
            videoHeight: Int,
            isDisplayPortrait: Boolean
        ): Pair<Int, Int> {
            if (viewWidth <= 0 || viewHeight <= 0 || videoWidth <= 0 || videoHeight <= 0) {
                return Pair(0, 0)
            }
            val displayWidth = if (isDisplayPortrait && videoWidth > videoHeight) videoHeight else videoWidth
            val displayHeight = if (isDisplayPortrait && videoWidth > videoHeight) videoWidth else videoHeight
            val scale = minOf(
                viewWidth.toFloat() / displayWidth.toFloat(),
                viewHeight.toFloat() / displayHeight.toFloat()
            )
            return Pair((displayWidth * scale).toInt(), (displayHeight * scale).toInt())
        }
    }
}
