package com.local3dgs.capture

import org.junit.Assert.assertEquals
import org.junit.Test

class UiTextTest {
    @Test
    fun primaryUiTextIsChinese() {
        assertEquals("3DGS 采集", UiText.APP_TITLE)
        assertEquals("导出示例采集包", UiText.EXPORT_SAMPLE_BUNDLE)
        assertEquals("分享采集包", UiText.SHARE_CAPTURE_BUNDLE)
    }
}
