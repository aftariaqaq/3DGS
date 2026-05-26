package com.local3dgs.capture

import org.junit.Assert.assertEquals
import org.junit.Test

class UiTextTest {
    @Test
    fun primaryUiTextIsChinese() {
        assertEquals("3DGS 采集", UiText.APP_TITLE)
        assertEquals("开始 IMU 采集", UiText.START_IMU_CAPTURE)
        assertEquals("停止 IMU 采集", UiText.STOP_IMU_CAPTURE)
        assertEquals("导出采集包", UiText.EXPORT_CAPTURE_BUNDLE)
        assertEquals("分享采集包", UiText.SHARE_CAPTURE_BUNDLE)
    }
}
