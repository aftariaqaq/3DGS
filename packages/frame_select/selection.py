from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FrameCandidate:
    frame_index: int
    timestamp_ns: int
    blur: float
    exposure: float
    texture: float
    duplicate: float | None = None
    sensor_flags: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        duplicate_component = 1.0 if self.duplicate is None else self.duplicate
        return (self.blur * 0.35) + (self.exposure * 0.25) + (self.texture * 0.25) + (duplicate_component * 0.15)


@dataclass(slots=True)
class FrameDecision:
    frame_index: int
    timestamp_ns: int
    selected: bool
    score: float
    reasons: list[str]


def _quality_reasons(candidate: FrameCandidate) -> list[str]:
    reasons: list[str] = []
    if candidate.blur < 0.2:
        reasons.append("blur")
    if candidate.exposure < 0.2:
        reasons.append("exposure")
    if candidate.texture < 0.1:
        reasons.append("low_texture")
    if candidate.duplicate is not None and candidate.duplicate < 0.05:
        reasons.append("duplicate")
    if "fast_rotation" in candidate.sensor_flags:
        reasons.append("fast_rotation")
    metadata_flags = {
        "exposure_jump_nearby",
        "focus_jump_nearby",
        "zoom_or_crop_change_nearby",
        "stabilization_change_nearby",
        "metadata_missing",
    }
    for flag in candidate.sensor_flags:
        if flag in metadata_flags:
            reasons.append(flag)
    return reasons


def select_keyframes(
    candidates: list[FrameCandidate],
    *,
    max_frames: int,
    min_time_distance_ns: int,
) -> list[FrameDecision]:
    decisions: list[FrameDecision] = []
    selected_timestamps: list[int] = []
    selected_count = 0

    for candidate in sorted(candidates, key=lambda item: item.timestamp_ns):
        reasons = _quality_reasons(candidate)
        if any(abs(candidate.timestamp_ns - timestamp) < min_time_distance_ns for timestamp in selected_timestamps):
            reasons.append("too_close_temporally")
        if selected_count >= max_frames:
            reasons.append("max_frame_cap")

        selected = not reasons
        if selected:
            selected_count += 1
            selected_timestamps.append(candidate.timestamp_ns)
            reasons = ["selected"]

        decisions.append(
            FrameDecision(
                frame_index=candidate.frame_index,
                timestamp_ns=candidate.timestamp_ns,
                selected=selected,
                score=candidate.score,
                reasons=sorted(set(reasons)),
            )
        )
    if any(decision.selected for decision in decisions):
        return decisions
    return _best_effort_decisions(candidates, decisions, max_frames=max_frames, min_time_distance_ns=min_time_distance_ns)


def _best_effort_decisions(
    candidates: list[FrameCandidate],
    decisions: list[FrameDecision],
    *,
    max_frames: int,
    min_time_distance_ns: int,
) -> list[FrameDecision]:
    selected_indexes: set[int] = set()
    selected_timestamps: list[int] = []
    by_score = sorted(candidates, key=lambda item: item.score, reverse=True)
    for candidate in by_score:
        if len(selected_indexes) >= max_frames:
            break
        if any(abs(candidate.timestamp_ns - timestamp) < min_time_distance_ns for timestamp in selected_timestamps):
            continue
        selected_indexes.add(candidate.frame_index)
        selected_timestamps.append(candidate.timestamp_ns)

    return [
        FrameDecision(
            frame_index=decision.frame_index,
            timestamp_ns=decision.timestamp_ns,
            selected=decision.frame_index in selected_indexes,
            score=decision.score,
            reasons=["selected_best_effort"] if decision.frame_index in selected_indexes else decision.reasons,
        )
        for decision in decisions
    ]
