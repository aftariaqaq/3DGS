package com.local3dgs.capture

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.local3dgs.capture.camera.CaptureSettingsStore
import com.local3dgs.capture.ui.SettingsPanel

class SettingsActivity : Activity() {
    private lateinit var settingsStore: CaptureSettingsStore
    private lateinit var settingsPanel: SettingsPanel

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        settingsStore = CaptureSettingsStore(this)
        settingsPanel = SettingsPanel(this, settingsStore.load())

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }
        root.addView(TextView(this).apply {
            text = UiText.SETTINGS_TITLE
            textSize = 20f
        })
        root.addView(settingsPanel)
        root.addView(Button(this).apply {
            text = UiText.SAVE_SETTINGS
            setOnClickListener {
                settingsStore.save(settingsPanel.currentSettings())
                Toast.makeText(this@SettingsActivity, UiText.SETTINGS_SAVED, Toast.LENGTH_SHORT).show()
                finish()
            }
        })
        setContentView(ScrollView(this).apply { addView(root) })
    }
}
