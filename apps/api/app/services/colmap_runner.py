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
            "--ImageReader.camera_model",
            "SIMPLE_RADIAL",
            "--ImageReader.single_camera",
            "1",
            "--FeatureExtraction.use_gpu",
            "1",
            "--FeatureExtraction.gpu_index",
            "0",
            "--SiftExtraction.max_image_size",
            "2400",
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
            "1",
            "--FeatureMatching.gpu_index",
            "0",
            "--SequentialMatching.overlap",
            "20",
            "--SequentialMatching.quadratic_overlap",
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
            "--Mapper.ba_global_max_num_iterations",
            "30",
            "--Mapper.ba_global_function_tolerance",
            "1e-5",
        ],
        storage.job_logs_dir(job_id) / "colmap_mapping.log",
    )
