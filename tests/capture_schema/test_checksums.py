from packages.capture_schema.checksums import sha256_file, validate_checksums
from packages.capture_schema.models import ChecksumManifest


def test_sha256_file_hashes_file_contents(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("capture", encoding="utf-8")

    assert sha256_file(path) == "460ee6aa3a80359181b794cc31a7185addba77626e9f719c10e3c8efb8668a1d"


def test_validate_checksums_reports_missing_and_mismatched_files(tmp_path):
    (tmp_path / "video.mp4").write_text("video", encoding="utf-8")
    manifest = ChecksumManifest(
        files={
            "video.mp4": "0" * 64,
            "metadata.json": "1" * 64,
        }
    )

    errors = validate_checksums(tmp_path, manifest)

    assert any("checksum mismatch: video.mp4" in error for error in errors)
    assert any("missing file: metadata.json" in error for error in errors)
