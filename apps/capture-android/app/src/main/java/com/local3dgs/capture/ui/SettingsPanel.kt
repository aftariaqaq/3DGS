package com.local3dgs.capture.ui

import android.content.Context
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.AdapterView
import android.widget.LinearLayout
import android.widget.Spinner
import android.widget.Switch
import android.widget.TextView
import com.local3dgs.capture.UiText
import com.local3dgs.capture.camera.CaptureSettings
import com.local3dgs.capture.camera.FocusMode
import com.local3dgs.capture.camera.StabilizationMode

class SettingsPanel(
    context: Context,
    initialSettings: CaptureSettings = CaptureSettings.defaults()
) : LinearLayout(context) {
    private val resolutionSpinner = spinner(CaptureSettings.resolutionLabels)
    private val fpsSpinner = spinner(CaptureSettings.fpsLabels)
    private val bitrateSpinner = spinner(CaptureSettings.bitrateLabels)
    private val focusSpinner = spinner(listOf("连续对焦", "中心锁定"))
    private val stabilizationSwitch = Switch(context).apply {
        text = UiText.SETTING_STABILIZATION
    }
    var onSettingsChanged: ((CaptureSettings) -> Unit)? = null

    init {
        orientation = VERTICAL
        addSetting(UiText.SETTING_RESOLUTION, resolutionSpinner)
        addSetting(UiText.SETTING_FPS, fpsSpinner)
        addSetting(UiText.SETTING_BITRATE, bitrateSpinner)
        addSetting(UiText.SETTING_FOCUS, focusSpinner)
        addView(stabilizationSwitch)
        resolutionSpinner.setSelection(CaptureSettings.resolutionLabels.indexOf("${initialSettings.width}x${initialSettings.height}").coerceAtLeast(0))
        fpsSpinner.setSelection(CaptureSettings.fpsLabels.indexOf(initialSettings.fps.toString()).coerceAtLeast(0))
        bitrateSpinner.setSelection(CaptureSettings.bitrateLabels.indexOf(CaptureSettings.labelForBitrate(initialSettings.bitrateBps)).coerceAtLeast(0))
        focusSpinner.setSelection(if (initialSettings.focusMode == FocusMode.LOCK_CENTER_AFTER_WARMUP) 1 else 0)
        stabilizationSwitch.isChecked = initialSettings.stabilizationMode == StabilizationMode.ON_IF_NEEDED
        listOf(resolutionSpinner, fpsSpinner, bitrateSpinner, focusSpinner).forEach { spinner ->
            spinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
                override fun onItemSelected(parent: AdapterView<*>?, view: android.view.View?, position: Int, id: Long) {
                    onSettingsChanged?.invoke(currentSettings())
                }

                override fun onNothingSelected(parent: AdapterView<*>?) = Unit
            }
        }
        stabilizationSwitch.setOnCheckedChangeListener { _, _ -> onSettingsChanged?.invoke(currentSettings()) }
    }

    fun currentSettings(): CaptureSettings {
        val resolution = resolutionSpinner.selectedItem.toString()
        val parts = resolution.split("x")
        val focusMode = if (focusSpinner.selectedItem.toString() == "中心锁定") {
            FocusMode.LOCK_CENTER_AFTER_WARMUP
        } else {
            FocusMode.CONTINUOUS
        }
        val stabilizationMode = if (stabilizationSwitch.isChecked) {
            StabilizationMode.ON_IF_NEEDED
        } else {
            StabilizationMode.OFF
        }
        return CaptureSettings(
            width = parts[0].toInt(),
            height = parts[1].toInt(),
            fps = fpsSpinner.selectedItem.toString().toInt(),
            bitrateBps = CaptureSettings.bitrateFromLabel(bitrateSpinner.selectedItem.toString()),
            focusMode = focusMode,
            stabilizationMode = stabilizationMode,
            warmupMs = CaptureSettings.defaults().warmupMs
        )
    }

    private fun addSetting(label: String, control: Spinner) {
        addView(TextView(context).apply { text = label })
        addView(control)
    }

    private fun spinner(items: List<String>): Spinner {
        return Spinner(context).apply {
            adapter = ArrayAdapter(context, android.R.layout.simple_spinner_dropdown_item, items)
            setSelection(0)
            layoutParams = LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
        }
    }
}
