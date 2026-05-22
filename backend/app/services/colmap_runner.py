from app.config import COLMAP_CMD
from app.services import storage
from app.services.process_runner import run_command


def run_feature_extractor(job_id: str) -> None:
    run_command(
        [
            COLMAP_CMD,
            "feature_extractor",
            "--database_path",
            str(storage.job_colmap_dir(job_id) / "database.db"),
            "--image_path",
            str(storage.job_images_dir(job_id)),
            "--FeatureExtraction.use_gpu",
            "0",
            "--FeatureExtraction.max_image_size",
            "1600",
        ],
        storage.job_logs_dir(job_id) / "colmap_features.log",
    )


def run_sequential_matcher(job_id: str) -> None:
    run_command(
        [
            COLMAP_CMD,
            "sequential_matcher",
            "--database_path",
            str(storage.job_colmap_dir(job_id) / "database.db"),
            "--FeatureMatching.use_gpu",
            "0",
            "--SiftMatching.cpu_brute_force_matcher",
            "1",
        ],
        storage.job_logs_dir(job_id) / "colmap_matching.log",
    )


def run_mapper(job_id: str) -> None:
    sparse_dir = storage.job_colmap_dir(job_id) / "sparse"
    sparse_dir.mkdir(parents=True, exist_ok=True)

    run_command(
        [
            COLMAP_CMD,
            "mapper",
            "--database_path",
            str(storage.job_colmap_dir(job_id) / "database.db"),
            "--image_path",
            str(storage.job_images_dir(job_id)),
            "--output_path",
            str(sparse_dir),
        ],
        storage.job_logs_dir(job_id) / "colmap_mapping.log",
    )

