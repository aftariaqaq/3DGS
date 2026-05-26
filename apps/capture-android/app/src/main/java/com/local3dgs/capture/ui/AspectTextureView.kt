package com.local3dgs.capture.ui

import android.content.Context
import android.content.res.Configuration
import android.graphics.Matrix
import android.graphics.RectF
import android.util.AttributeSet
import android.view.TextureView
import com.local3dgs.capture.camera.CaptureSettings

class AspectTextureView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : TextureView(context, attrs) {
    private var videoWidth: Int = 1920
    private var videoHeight: Int = 1080

    fun setAspectRatio(width: Int, height: Int) {
        if (width <= 0 || height <= 0) {
            return
        }
        videoWidth = width
        videoHeight = height
        requestLayout()
        post { updateTransform() }
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val parentWidth = MeasureSpec.getSize(widthMeasureSpec)
        val heightMode = MeasureSpec.getMode(heightMeasureSpec)
        val measuredHeight = if (heightMode == MeasureSpec.EXACTLY || heightMode == MeasureSpec.AT_MOST) {
            MeasureSpec.getSize(heightMeasureSpec)
        } else {
            CaptureSettings.previewHeightForDisplay(
                parentWidth = parentWidth,
                videoWidth = videoWidth,
                videoHeight = videoHeight,
                isDisplayPortrait = resources.configuration.orientation == Configuration.ORIENTATION_PORTRAIT
            )
        }
        setMeasuredDimension(parentWidth, measuredHeight)
    }

    override fun onSizeChanged(width: Int, height: Int, oldWidth: Int, oldHeight: Int) {
        super.onSizeChanged(width, height, oldWidth, oldHeight)
        updateTransform()
    }

    private fun updateTransform() {
        if (width <= 0 || height <= 0 || videoWidth <= 0 || videoHeight <= 0) {
            return
        }
        val isPortrait = resources.configuration.orientation == Configuration.ORIENTATION_PORTRAIT
        val (contentWidth, contentHeight) = CaptureSettings.fitCenterContentSize(
            viewWidth = width,
            viewHeight = height,
            videoWidth = videoWidth,
            videoHeight = videoHeight,
            isDisplayPortrait = isPortrait
        )
        if (contentWidth <= 0 || contentHeight <= 0) {
            return
        }
        val source = RectF(0f, 0f, width.toFloat(), height.toFloat())
        val target = RectF(
            (width - contentWidth) / 2f,
            (height - contentHeight) / 2f,
            (width + contentWidth) / 2f,
            (height + contentHeight) / 2f
        )
        setTransform(Matrix().apply {
            setRectToRect(source, target, Matrix.ScaleToFit.CENTER)
        })
    }
}
