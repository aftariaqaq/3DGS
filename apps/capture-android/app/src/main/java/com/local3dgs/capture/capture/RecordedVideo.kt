package com.local3dgs.capture.capture

import java.io.File

data class RecordedVideo(
    val file: File,
    val width: Int,
    val height: Int,
    val fps: Int,
    val bitrateBps: Int,
    val codec: String,
    val cameraId: String,
    val lensFacing: String,
    val sensorOrientationDegrees: Int,
    val stabilizationMode: String,
    val focusMode: String
)
