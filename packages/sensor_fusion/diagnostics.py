from __future__ import annotations

EVENT_FLAG_MAP = {
    "exposure_jump": "exposure_jump_nearby",
    "focus_jump": "focus_jump_nearby",
    "zoom_changed": "zoom_or_crop_change_nearby",
    "crop_region_changed": "zoom_or_crop_change_nearby",
    "stabilization_changed": "stabilization_change_nearby",
    "camera_metadata_missing": "metadata_missing",
}


def flags_for_event_types(event_types: set[str]) -> list[str]:
    return sorted({EVENT_FLAG_MAP[event_type] for event_type in event_types if event_type in EVENT_FLAG_MAP})

