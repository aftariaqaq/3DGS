package com.local3dgs.capture.camera

import android.content.Context

class CaptureSettingsStore(context: Context) {
    private val preferences = context.getSharedPreferences("capture_settings", Context.MODE_PRIVATE)

    fun load(): CaptureSettings {
        val defaults = CaptureSettings.defaults()
        return CaptureSettings(
            width = preferences.getInt("width", defaults.width),
            height = preferences.getInt("height", defaults.height),
            fps = preferences.getInt("fps", defaults.fps),
            bitrateBps = preferences.getInt("bitrate_bps", defaults.bitrateBps),
            focusMode = FocusMode.valueOf(preferences.getString("focus_mode", defaults.focusMode.name) ?: defaults.focusMode.name),
            stabilizationMode = StabilizationMode.valueOf(
                preferences.getString("stabilization_mode", defaults.stabilizationMode.name) ?: defaults.stabilizationMode.name
            ),
            warmupMs = preferences.getLong("warmup_ms", defaults.warmupMs)
        )
    }

    fun save(settings: CaptureSettings) {
        preferences.edit()
            .putInt("width", settings.width)
            .putInt("height", settings.height)
            .putInt("fps", settings.fps)
            .putInt("bitrate_bps", settings.bitrateBps)
            .putString("focus_mode", settings.focusMode.name)
            .putString("stabilization_mode", settings.stabilizationMode.name)
            .putLong("warmup_ms", settings.warmupMs)
            .apply()
    }
}
