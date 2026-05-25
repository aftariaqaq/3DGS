from packages.frame_select.scoring import (
    blur_score,
    duplicate_score,
    exposure_score,
    texture_score,
)


def test_blur_score_is_higher_for_edge_rich_frames():
    flat = [
        [100, 100, 100],
        [100, 100, 100],
        [100, 100, 100],
    ]
    edge_rich = [
        [0, 255, 0],
        [255, 0, 255],
        [0, 255, 0],
    ]

    assert blur_score(edge_rich) > blur_score(flat)


def test_exposure_score_prefers_mid_luminance():
    mid = [[128, 128], [128, 128]]
    dark = [[5, 5], [5, 5]]
    bright = [[250, 250], [250, 250]]

    assert exposure_score(mid) > exposure_score(dark)
    assert exposure_score(mid) > exposure_score(bright)


def test_texture_score_increases_with_luminance_diversity():
    flat = [[100, 100], [100, 100]]
    varied = [[0, 80], [160, 255]]

    assert texture_score(varied) > texture_score(flat)


def test_duplicate_score_is_low_for_identical_frames_and_high_for_different_frames():
    current = [[0, 0], [255, 255]]
    same = [[0, 0], [255, 255]]
    different = [[255, 255], [0, 0]]

    assert duplicate_score(current, same) == 0.0
    assert duplicate_score(current, different) > 0.9
