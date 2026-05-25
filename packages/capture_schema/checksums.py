from __future__ import annotations

import hashlib
from pathlib import Path

from packages.capture_schema.models import ChecksumManifest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_checksums(bundle_root: Path, manifest: ChecksumManifest) -> list[str]:
    errors: list[str] = []
    for relative_path, expected_digest in manifest.files.items():
        path = bundle_root / relative_path
        if not path.exists():
            errors.append(f"missing file: {relative_path}")
            continue
        actual_digest = sha256_file(path)
        if actual_digest != expected_digest:
            errors.append(f"checksum mismatch: {relative_path}")
    return errors

