package com.local3dgs.capture

import android.app.Activity
import android.os.Bundle
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val label = TextView(this).apply {
            text = "3DGS Capture"
            textSize = 20f
            setPadding(32, 32, 32, 32)
        }
        setContentView(label)
    }
}
