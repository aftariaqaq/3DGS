from __future__ import annotations

import argparse
from pathlib import Path

from packages.pipeline.capture_to_job import create_job_from_capture


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m packages.pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import-capture")
    import_parser.add_argument("capture_root", type=Path)
    import_parser.add_argument("--jobs-root", type=Path, default=Path("data/jobs"))
    import_parser.add_argument("--job-id", required=True)
    import_parser.add_argument("--max-frames", type=int, default=700)

    args = parser.parse_args()
    if args.command == "import-capture":
        job_root = create_job_from_capture(args.capture_root, args.jobs_root, args.job_id, args.max_frames)
        print(f"created job: {job_root}")
        print(f"report: {job_root / 'capture' / 'import_report.json'}")


if __name__ == "__main__":
    main()

