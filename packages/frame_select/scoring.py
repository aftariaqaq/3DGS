from __future__ import annotations

from collections import Counter
from math import log2

GrayImage = list[list[int]]


def _pixels(image: GrayImage) -> list[int]:
    return [max(0, min(255, int(value))) for row in image for value in row]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def blur_score(image: GrayImage) -> float:
    if len(image) < 3 or len(image[0]) < 3:
        return 0.0
    responses: list[float] = []
    for y in range(1, len(image) - 1):
        for x in range(1, len(image[y]) - 1):
            center = image[y][x] * 4
            response = center - image[y - 1][x] - image[y + 1][x] - image[y][x - 1] - image[y][x + 1]
            responses.append(float(response))
    if not responses:
        return 0.0
    mean_absolute_response = sum(abs(value) for value in responses) / len(responses)
    return _clamp01(mean_absolute_response / (255.0 * 4.0))


def exposure_score(image: GrayImage) -> float:
    pixels = _pixels(image)
    if not pixels:
        return 0.0
    mean = sum(pixels) / len(pixels)
    return _clamp01(1.0 - abs(mean - 128.0) / 128.0)


def texture_score(image: GrayImage) -> float:
    pixels = _pixels(image)
    if not pixels:
        return 0.0
    counts = Counter(pixels)
    entropy = 0.0
    for count in counts.values():
        probability = count / len(pixels)
        entropy -= probability * log2(probability)
    return _clamp01(entropy / 8.0)


def duplicate_score(current: GrayImage, previous: GrayImage) -> float:
    current_pixels = _pixels(current)
    previous_pixels = _pixels(previous)
    if not current_pixels or not previous_pixels or len(current_pixels) != len(previous_pixels):
        return 1.0
    mean_difference = sum(abs(a - b) for a, b in zip(current_pixels, previous_pixels)) / len(current_pixels)
    return _clamp01(mean_difference / 255.0)
