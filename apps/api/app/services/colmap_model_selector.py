from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services import storage


@dataclass(frozen=True)
class SparseModelSummary:
    model_id: str
    path: Path
    registered_images: int
    points3d: int


def _read_bin_count(path: Path) -> int:
    if not path.exists():
        return 0
    data = path.read_bytes()[:8]
    if len(data) < 8:
        return 0
    return int.from_bytes(data, "little", signed=False)


def _read_text_count(path: Path, *, images_txt: bool = False) -> int:
    if not path.exists():
        return 0
    lines = [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line and not line.startswith("#")]
    if images_txt:
        return (len(lines) + 1) // 2
    return len(lines)


def _model_summary(model_dir: Path) -> SparseModelSummary:
    registered_images = _read_bin_count(model_dir / "images.bin")
    points3d = _read_bin_count(model_dir / "points3D.bin")
    if not registered_images:
        registered_images = _read_text_count(model_dir / "images.txt", images_txt=True)
    if not points3d:
        points3d = _read_text_count(model_dir / "points3D.txt")
    return SparseModelSummary(
        model_id=model_dir.name,
        path=model_dir,
        registered_images=registered_images,
        points3d=points3d,
    )


def list_sparse_models(job_id: str) -> list[SparseModelSummary]:
    sparse_root = storage.job_colmap_dir(job_id) / "sparse"
    if not sparse_root.exists():
        return []
    models = []
    for candidate in sparse_root.iterdir():
        if not candidate.is_dir():
            continue
        models.append(_model_summary(candidate))
    return sorted(models, key=lambda model: model.model_id)


def select_best_sparse_model(job_id: str) -> SparseModelSummary:
    models = list_sparse_models(job_id)
    if not models:
        sparse_root = storage.job_colmap_dir(job_id) / "sparse"
        raise RuntimeError(f"COLMAP sparse output not found under {sparse_root}")
    return max(models, key=lambda model: (model.registered_images, model.points3d, -_model_sort_number(model.model_id)))


def _model_sort_number(model_id: str) -> int:
    try:
        return int(model_id)
    except ValueError:
        return 10**9
