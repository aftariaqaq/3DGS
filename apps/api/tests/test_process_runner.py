from pathlib import Path

import pytest

from app.services.process_runner import run_command


def test_run_command_writes_output_to_log(tmp_path):
    log_path = tmp_path / "success.log"

    run_command(
        ["powershell", "-NoProfile", "-Command", "Write-Output hello"],
        log_path,
    )

    text = log_path.read_text(encoding="utf-8")
    assert "COMMAND:" in text
    assert "hello" in text


def test_run_command_raises_on_failure_and_logs_exit_code(tmp_path):
    log_path = tmp_path / "failure.log"

    with pytest.raises(RuntimeError, match="exit code 7"):
        run_command(
            ["powershell", "-NoProfile", "-Command", "Write-Error bad; exit 7"],
            log_path,
        )

    text = log_path.read_text(encoding="utf-8")
    assert "bad" in text
    assert "EXIT_CODE: 7" in text


def test_run_command_passes_extra_environment(tmp_path):
    log_path = tmp_path / "env.log"

    run_command(
        ["powershell", "-NoProfile", "-Command", "Write-Output $env:THREE_DGS_TEST_FLAG"],
        log_path,
        env={"THREE_DGS_TEST_FLAG": "enabled"},
    )

    assert "enabled" in log_path.read_text(encoding="utf-8")
