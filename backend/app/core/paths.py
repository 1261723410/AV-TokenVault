from pathlib import Path

from app.core.config import Settings, get_settings


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def safe_artifact_path(artifact_path: str, settings: Settings | None = None) -> Path:
    active_settings = settings or get_settings()
    data_root = active_settings.data_root.resolve()
    candidate = (data_root / artifact_path).resolve()

    if not _is_relative_to(candidate, data_root):
        raise ValueError("artifact path resolves outside data directory")

    return candidate
