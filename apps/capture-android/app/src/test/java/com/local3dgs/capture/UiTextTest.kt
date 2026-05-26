package com.local3dgs.capture

import org.junit.Assert.assertEquals
import org.junit.Test

class UiTextTest {
    @Test
    fun primaryUiTextIsChinese() {
        assertEquals("3DGS 采集", UiText.APP_TITLE)
        assertEquals("开始视频采集", UiText.START_CAPTURE)
        assertEquals("停止视频采集", UiText.STOP_CAPTURE)
        assertEquals("导出采集包", UiText.EXPORT_CAPTURE_BUNDLE)
        assertEquals("设置", UiText.OPEN_SETTINGS)
        assertEquals("采集设置", UiText.SETTINGS_TITLE)
        assertEquals("保存设置", UiText.SAVE_SETTINGS)
        assertEquals("分享采集包", UiText.SHARE_CAPTURE_BUNDLE)
        assertEquals("分辨率", UiText.SETTING_RESOLUTION)
        assertEquals("帧率", UiText.SETTING_FPS)
        assertEquals("码率", UiText.SETTING_BITRATE)
        assertEquals("对焦", UiText.SETTING_FOCUS)
        assertEquals("防抖", UiText.SETTING_STABILIZATION)
        assertEquals("预览中", UiText.STATUS_PREVIEW)
    }
}
