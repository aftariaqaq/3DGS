import shutil
from pathlib import Path

from app import config
from app.services import process_runner, storage

run_command = process_runner.run_command


def _copytree_replace(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _stage_nerfstudio_inputs(job_id: str) -> tuple[Path, Path, Path]:
    data_dir = storage.job_nerfstudio_data_dir(job_id)
    images_source = storage.job_images_dir(job_id)
    colmap_model_source = storage.job_colmap_dir(job_id) / "sparse" / "0"
    if not images_source.exists():
        raise RuntimeError(f"job images not found: {images_source}")
    if not colmap_model_source.exists():
        raise RuntimeError(f"COLMAP sparse/0 output not found: {colmap_model_source}")
    data_dir.mkdir(parents=True, exist_ok=True)
    images_target = data_dir / "images"
    colmap_model_target = data_dir / "colmap" / "sparse" / "0"
    _copytree_replace(images_source, images_target)
    colmap_model_target.parent.mkdir(parents=True, exist_ok=True)
    _copytree_replace(colmap_model_source, colmap_model_target)
    return data_dir, images_target, colmap_model_target


def _latest_config(outputs_dir: Path) -> Path:
    configs = sorted(outputs_dir.rglob("config.yml"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not configs:
        raise RuntimeError(f"Splatfacto config not found under {outputs_dir}")
    return configs[0]


def _exported_ply(export_dir: Path) -> Path:
    candidates = [export_dir / "splat.ply", export_dir / "splatfacto.ply"]
    candidates.extend(sorted(export_dir.glob("*.ply")))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(f"Splatfacto export not found under {export_dir}")


def run_splatfacto(job_id: str, max_num_iterations: int) -> Path:
    data_dir, images_dir, colmap_model_dir = _stage_nerfstudio_inputs(job_id)
    outputs_dir = storage.job_nerfstudio_outputs_dir(job_id)
    export_dir = storage.job_splatfacto_export_dir(job_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    process_command = [
        config.NERFSTUDIO_PROCESS_CMD,
        "images",
        "--data",
        str(images_dir),
        "--output-dir",
        str(data_dir),
        "--skip-colmap",
        "--skip-image-processing",
        "--colmap-model-path",
        str(colmap_model_dir),
    ]
    run_command(process_command, storage.job_logs_dir(job_id) / "nerfstudio-process-data.log")

    train_command = [
        config.NERFSTUDIO_CMD,
        config.SPLATFACTO_METHOD,
        "--data",
        str(data_dir),
        "--output-dir",
        str(outputs_dir),
        "--experiment-name",
        job_id,
        "--max-num-iterations",
        str(max_num_iterations),
        "--vis",
        "viewer",
    ]
    run_command(train_command, storage.job_logs_dir(job_id) / "splatfacto.log")

    config_path = _latest_config(outputs_dir)
    export_command = [
        config.NERFSTUDIO_EXPORT_CMD,
        "gaussian-splat",
        "--load-config",
        str(config_path),
        "--output-dir",
        str(export_dir),
    ]
    run_command(export_command, storage.job_logs_dir(job_id) / "splatfacto-export.log")
    return _exported_ply(export_dir)
