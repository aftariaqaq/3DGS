from app import config


def test_project_dir_points_to_repository_root():
    assert (config.PROJECT_DIR / "backend" / "app" / "config.py").exists()
    assert config.DATA_DIR == config.PROJECT_DIR / "data"
