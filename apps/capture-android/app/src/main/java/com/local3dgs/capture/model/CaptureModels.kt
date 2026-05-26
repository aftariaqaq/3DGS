package com.local3dgs.capture.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class CaptureMetadata(
    @SerialName("schema_version") val schemaVersion: String,
    @SerialName("capture_id") val captureId: String,
    @SerialName("app_version") val appVersion: String,
    val platform: String,
    @SerialName("device_manufacturer") val deviceManufacturer: String,
    @SerialName("device_model") val deviceModel: String,
    @SerialName("android_api_level") val androidApiLevel: Int,
    @SerialName("camera_id") val cameraId: String,
    @SerialName("lens_facing") val lensFacing: String,
    @SerialName("sensor_orientation_degrees") val sensorOrientationDegrees: Int,
    @SerialName("video_width") val videoWidth: Int,
    @SerialName("video_height") val videoHeight: Int,
    @SerialName("target_fps") val targetFps: Int,
    @SerialName("actual_video_duration_us") val actualVideoDurationUs: Long,
    @SerialName("video_codec") val videoCodec: String,
    @SerialName("bitrate_bps") val bitrateBps: Long,
    @SerialName("started_monotonic_ns") val startedMonotonicNs: Long,
    @SerialName("stopped_monotonic_ns") val stoppedMonotonicNs: Long,
    @SerialName("stabilization_mode") val stabilizationMode: String? = null,
    @SerialName("focus_mode") val focusMode: String? = null,
    @SerialName("exposure_mode") val exposureMode: String? = null,
    @SerialName("white_balance_mode") val whiteBalanceMode: String? = null,
    @SerialName("zoom_ratio") val zoomRatio: Float? = null,
    @SerialName("scaler_crop_region") val scalerCropRegion: List<Int>? = null,
    @SerialName("ae_lock_enabled") val aeLockEnabled: Boolean? = null,
    @SerialName("af_lock_enabled") val afLockEnabled: Boolean? = null,
    @SerialName("awb_lock_enabled") val awbLockEnabled: Boolean? = null,
    @SerialName("calibration_profile_id") val calibrationProfileId: String? = null
)

@Serializable
data class FrameTimestamp(
    @SerialName("frame_index") val frameIndex: Int,
    @SerialName("pts_us") val ptsUs: Long,
    @SerialName("sensor_timestamp_ns") val sensorTimestampNs: Long? = null,
    @SerialName("monotonic_ns") val monotonicNs: Long? = null
)

@Serializable
data class CameraSample(
    @SerialName("sensor_timestamp_ns") val sensorTimestampNs: Long,
    @SerialName("exposure_time_ns") val exposureTimeNs: Long? = null,
    val iso: Int? = null,
    @SerialName("focal_length_mm") val focalLengthMm: Float? = null,
    @SerialName("focus_distance_diopters") val focusDistanceDiopters: Float? = null,
    val aperture: Float? = null,
    @SerialName("zoom_ratio") val zoomRatio: Float? = null,
    @SerialName("scaler_crop_region") val scalerCropRegion: List<Int>? = null,
    @SerialName("video_stabilization_mode") val videoStabilizationMode: String? = null,
    @SerialName("ae_state") val aeState: String? = null,
    @SerialName("af_state") val afState: String? = null,
    @SerialName("awb_state") val awbState: String? = null
)

@Serializable
data class ImuSample(
    val type: String,
    @SerialName("timestamp_ns") val timestampNs: Long,
    val x: Float,
    val y: Float,
    val z: Float,
    val w: Float? = null,
    val accuracy: Int? = null
)

@Serializable
data class CaptureEvent(
    @SerialName("timestamp_ns") val timestampNs: Long,
    val type: String,
    val message: String? = null
)

@Serializable
data class ChecksumManifest(
    val files: Map<String, String>
)
