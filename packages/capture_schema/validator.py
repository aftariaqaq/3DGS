from __future__ import annotations

from pathlib import Path

from packages.capture_schema.checksums import validate_checksums
from packages.capture_schema.models import ChecksumManifest


def validate_bundle_checksums(bundle_root: Path, manifest: ChecksumManifest) -> list[str]:
    return validate_checksums(bundle_root, manifest)
