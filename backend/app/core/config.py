from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AV_TOKENVAULT_", env_file=".env")

    project_root: Path = Field(default_factory=_default_project_root)
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_origin_regex: str = r"^https?://[^/]+:3000$"

    default_frame_interval: float = 2.0
    default_segment_seconds: float = 5.0
    max_frames: int = 600
    default_image_encoder: str = "mock-image-encoder"
    default_audio_encoder: str = "mock-audio-encoder"
    default_transcriber: str = "mock-transcriber"
    default_text_encoder: str = "mock-text-embedder"

    @property
    def data_root(self) -> Path:
        return self.project_root / "data"

    @property
    def upload_root(self) -> Path:
        return self.data_root / "uploads"

    @property
    def extracted_root(self) -> Path:
        return self.data_root / "extracted"

    @property
    def sqlite_dir(self) -> Path:
        return self.data_root / "sqlite"

    @property
    def sqlite_path(self) -> Path:
        return self.sqlite_dir / "av_tokenvault.db"

    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{self.sqlite_path}"

    def ensure_runtime_dirs(self) -> None:
        for path in (self.data_root, self.upload_root, self.extracted_root, self.sqlite_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
