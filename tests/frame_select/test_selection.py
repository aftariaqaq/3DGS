from packages.frame_select.selection import FrameCandidate, select_keyframes


def test_select_keyframes_keeps_high_quality_motion_diverse_frames():
    candidates = [
        FrameCandidate(frame_index=0, timestamp_ns=0, blur=0.9, exposure=0.9, texture=0.9),
        FrameCandidate(frame_index=1, timestamp_ns=10, blur=0.1, exposure=0.9, texture=0.9),
        FrameCandidate(frame_index=2, timestamp_ns=200, blur=0.9, exposure=0.1, texture=0.9),
        FrameCandidate(frame_index=3, timestamp_ns=400, blur=0.9, exposure=0.9, texture=0.9),
        FrameCandidate(
            frame_index=4,
            timestamp_ns=800,
            blur=0.9,
            exposure=0.9,
            texture=0.9,
            sensor_flags=["fast_rotation"],
        ),
    ]

    decisions = select_keyframes(candidates, max_frames=2, min_time_distance_ns=100)

    selected = [decision.frame_index for decision in decisions if decision.selected]
    rejected = {decision.frame_index: decision.reasons for decision in decisions if not decision.selected}
    assert selected == [0, 3]
    assert "blur" in rejected[1]
    assert "exposure" in rejected[2]
    assert "fast_rotation" in rejected[4]


def test_select_keyframes_rejects_temporally_close_duplicates():
    candidates = [
        FrameCandidate(frame_index=0, timestamp_ns=0, blur=0.9, exposure=0.9, texture=0.9),
        FrameCandidate(frame_index=1, timestamp_ns=50, blur=0.9, exposure=0.9, texture=0.9),
    ]

    decisions = select_keyframes(candidates, max_frames=5, min_time_distance_ns=100)

    assert decisions[0].selected is True
    assert decisions[1].selected is False
    assert "too_close_temporally" in decisions[1].reasons
