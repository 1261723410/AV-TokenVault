from pathlib import Path

import pytest


def test_default_runtime_paths_stay_under_project_root():
    from app.core.config import Settings

    settings = Settings()

    assert settings.project_root.name == "mvp"
    assert settings.data_root == settings.project_root / "data"
    assert settings.upload_root == settings.data_root / "uploads"
    assert settings.extracted_root == settings.data_root / "extracted"
    assert settings.sqlite_path == settings.data_root / "sqlite" / "av_tokenvault.db"


def test_safe_artifact_path_rejects_path_traversal():
    from app.core.config import Settings
    from app.core.paths import safe_artifact_path

    settings = Settings()

    with pytest.raises(ValueError, match="outside data directory"):
        safe_artifact_path("../secret.txt", settings=settings)


def test_safe_artifact_path_resolves_inside_data_directory():
    from app.core.config import Settings
    from app.core.paths import safe_artifact_path

    settings = Settings()
    resolved = safe_artifact_path("extracted/sample/frame.jpg", settings=settings)

    assert resolved == settings.data_root / "extracted" / "sample" / "frame.jpg"
    assert Path(resolved).is_absolute()
