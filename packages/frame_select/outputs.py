from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from packages.frame_select.selection import FrameDecision


def write_decisions_jsonl(path: Path, decisions: list[FrameDecision]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for decision in decisions:
            handle.write(json.dumps(asdict(decision), ensure_ascii=True, separators=(",", ":")))
            handle.write("\n")

