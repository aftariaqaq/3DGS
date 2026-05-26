package com.local3dgs.capture.capture

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.SystemClock

class ImuSensorRecorder(
    context: Context,
    private val session: ImuCaptureSession
) : SensorEventListener {
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val sensors = listOfNotNull(
        sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE),
        sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER),
        sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD),
        sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR),
        sensorManager.getDefaultSensor(Sensor.TYPE_GAME_ROTATION_VECTOR)
    )

    fun start() {
        session.start(SystemClock.elapsedRealtimeNanos())
        sensors.forEach { sensor ->
            sensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME)
        }
    }

    fun stop() {
        sensorManager.unregisterListener(this)
        session.stop(SystemClock.elapsedRealtimeNanos())
    }

    override fun onSensorChanged(event: SensorEvent) {
        session.recordSample(
            type = sensorTypeName(event.sensor.type),
            timestampNs = event.timestamp,
            values = event.values,
            accuracy = event.accuracy
        )
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit

    private fun sensorTypeName(type: Int): String {
        return when (type) {
            Sensor.TYPE_GYROSCOPE -> "gyro"
            Sensor.TYPE_ACCELEROMETER -> "accelerometer"
            Sensor.TYPE_MAGNETIC_FIELD -> "magnetometer"
            Sensor.TYPE_ROTATION_VECTOR -> "rotation_vector"
            Sensor.TYPE_GAME_ROTATION_VECTOR -> "game_rotation_vector"
            else -> "unknown"
        }
    }
}
