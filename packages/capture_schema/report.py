from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class ImportReport:
    capture_id: str
    source_path: str
    capture_root: str
    raw_file_count: int
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

