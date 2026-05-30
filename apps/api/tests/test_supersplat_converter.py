from pathlib import Path

import pytest

from app.services import supersplat_converter


def test_convert_to_supersplat_writes_sog_with_nerfstudio_rotation(monkeypatch, tmp_path):
    source = tmp_path / "splat.ply"
    source.write_text("ply data", encoding="utf-8")
    target_dir = tmp_path / "scene"
    log_path = tmp_path / "convert.log"
    calls = []

    def fake_run_command(args, log, cwd=None, env=None):
        calls.append((args, log, cwd, env))
        if args[-1].endswith("scene.sog"):
            (target_dir / "scene.sog").write_text("sog data", encoding="utf-8")
        if args[-1].endswith("supersplat.html"):
            (target_dir / "supersplat.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(supersplat_converter.process_runner, "run_command", fake_run_command)

    output = supersplat_converter.convert_to_supersplat(source, target_dir, log_path)

    assert output == target_dir / "scene.sog"
    assert output.read_text(encoding="utf-8") == "sog data"
    assert calls[0] == (
        [
            "npx",
            "--yes",
            "@playcanvas/splat-transform@2.4.0",
            "-w",
            str(source),
            "--filter-nan",
            "-r",
            "180,0,0",
            str(target_dir / "scene.sog"),
        ],
        log_path,
        None,
        None,
    )
    assert calls[1] == (
        [
                "npx",
                "--yes",
                "@playcanvas/splat-transform@2.4.0",
                "-w",
                str(source),
                "--filter-nan",
                "-r",
                "180,0,0",
                str(target_dir / "supersplat.html"),
            ],
            log_path,
            None,
            None,
    )


def test_convert_to_supersplat_raises_when_output_missing(monkeypatch, tmp_path):
    source = tmp_path / "splat.ply"
    source.write_text("ply data", encoding="utf-8")

    monkeypatch.setattr(supersplat_converter.process_runner, "run_command", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="SuperSplat conversion did not create"):
        supersplat_converter.convert_to_supersplat(source, tmp_path / "scene", tmp_path / "convert.log")


def test_convert_to_supersplat_allows_command_override(monkeypatch, tmp_path):
    source = tmp_path / "splat.ply"
    source.write_text("ply data", encoding="utf-8")
    target_dir = tmp_path / "scene"
    calls = []

    def fake_run_command(args, log, cwd=None, env=None):
        calls.append(args)
        if args[-1].endswith("scene.sog"):
            (target_dir / "scene.sog").write_text("sog data", encoding="utf-8")
        if args[-1].endswith("supersplat.html"):
            (target_dir / "supersplat.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setenv("SPLAT_TRANSFORM_COMMAND", "splat-transform")
    monkeypatch.setattr(supersplat_converter.process_runner, "run_command", fake_run_command)

    supersplat_converter.convert_to_supersplat(source, target_dir, tmp_path / "convert.log")

    assert calls[0][0] == "splat-transform"
