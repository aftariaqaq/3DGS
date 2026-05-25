from packages.capture_schema.models import FrameTimestamp, ImuSample
from packages.sensor_fusion.timeline import frame_time_ns, nearest_sample, samples_between


def test_frame_time_prefers_sensor_timestamp_then_monotonic_then_pts():
    assert (
        frame_time_ns(FrameTimestamp(frame_index=0, pts_us=10, sensor_timestamp_ns=123, monotonic_ns=456))
        == 123
    )
    assert frame_time_ns(FrameTimestamp(frame_index=0, pts_us=10, monotonic_ns=456)) == 456
    assert frame_time_ns(FrameTimestamp(frame_index=0, pts_us=10)) == 10_000


def test_nearest_sample_returns_closest_timestamp():
    samples = [
        ImuSample(type="gyro", timestamp_ns=100, x=0.0, y=0.0, z=0.0),
        ImuSample(type="gyro", timestamp_ns=200, x=0.0, y=0.0, z=0.0),
        ImuSample(type="gyro", timestamp_ns=500, x=0.0, y=0.0, z=0.0),
    ]

    assert nearest_sample(samples, 260).timestamp_ns == 200
    assert nearest_sample(samples, 400).timestamp_ns == 500


def test_samples_between_returns_inclusive_window():
    samples = [
        ImuSample(type="gyro", timestamp_ns=100, x=0.0, y=0.0, z=0.0),
        ImuSample(type="gyro", timestamp_ns=200, x=0.0, y=0.0, z=0.0),
        ImuSample(type="gyro", timestamp_ns=500, x=0.0, y=0.0, z=0.0),
    ]

    window = samples_between(samples, 100, 300)

    assert [sample.timestamp_ns for sample in window] == [100, 200]
