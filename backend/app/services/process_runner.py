import subprocess
from pathlib import Path


def run_command(args: list[str], log_path: Path, cwd: Path | None = None) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"COMMAND: {' '.join(args)}\n")
        log_file.flush()

        process = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        assert process.stdout is not None
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()

        exit_code = process.wait()
        log_file.write(f"EXIT_CODE: {exit_code}\n")

    if exit_code != 0:
        raise RuntimeError(f"Command failed with exit code {exit_code}: {' '.join(args)}")

