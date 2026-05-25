package com.local3dgs.capture.export

import java.io.BufferedWriter
import java.io.OutputStream
import java.io.OutputStreamWriter
import kotlinx.serialization.KSerializer
import kotlinx.serialization.json.Json

class JsonlWriter<T>(
    outputStream: OutputStream,
    private val serializer: KSerializer<T>,
    private val json: Json = Json {
        encodeDefaults = false
        explicitNulls = false
    }
) : AutoCloseable {
    private val writer = BufferedWriter(OutputStreamWriter(outputStream, Charsets.UTF_8))

    fun write(record: T) {
        writer.write(json.encodeToString(serializer, record))
        writer.newLine()
    }

    override fun close() {
        writer.flush()
        writer.close()
    }
}
