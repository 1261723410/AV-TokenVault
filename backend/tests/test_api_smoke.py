from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.core.config import Settings
    from app.db.models import Base
    from app.db.session import get_db
    from app.main import create_app

    settings = Settings(project_root=tmp_path)
    settings.ensure_runtime_dirs()
    engine = create_engine(f"sqlite:///{settings.sqlite_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def test_health_endpoint(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_lan_frontend_origin(client: TestClient):
    response = client.options(
        "/api/jobs",
        headers={
            "Origin": "http://192.168.100.67:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://192.168.100.67:3000"


def test_upload_rejects_unsupported_extension(client: TestClient):
    response = client.post(
        "/api/media/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported media type" in response.json()["detail"]


def test_upload_wav_creates_media_and_pending_job(client: TestClient):
    response = client.post(
        "/api/media/upload",
        files={"file": ("demo.wav", b"RIFF....WAVE", "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["media"]["filename"] == "demo.wav"
    assert payload["media"]["media_type"] == "audio"
    assert payload["job"]["status"] == "pending"
    assert payload["job"]["progress"] == 0.0


def test_upload_uses_app_settings_data_directory(client: TestClient, tmp_path: Path):
    response = client.post(
        "/api/media/upload",
        files={"file": ("demo.wav", b"RIFF....WAVE", "audio/wav")},
    )

    assert response.status_code == 200
    uploaded_files = list((tmp_path / "data" / "uploads").glob("*_demo.wav"))
    assert len(uploaded_files) == 1


def test_upload_accepts_processing_parameters(client: TestClient):
    response = client.post(
        "/api/media/upload",
        files={"file": ("demo.wav", b"RIFF....WAVE", "audio/wav")},
        data={
            "frame_interval": "3.5",
            "segment_seconds": "8.0",
            "image_encoder": "mock-image-encoder",
            "audio_encoder": "mock-audio-encoder",
        },
    )

    assert response.status_code == 200
    job = response.json()["job"]
    assert job["frame_interval"] == 3.5
    assert job["segment_seconds"] == 8.0
    assert job["image_encoder"] == "mock-image-encoder"
    assert job["audio_encoder"] == "mock-audio-encoder"


def test_stats_for_unprocessed_upload_are_zero(client: TestClient):
    upload = client.post(
        "/api/media/upload",
        files={"file": ("demo.wav", b"RIFF....WAVE", "audio/wav")},
    ).json()

    response = client.get(f"/api/media/{upload['media']['id']}/stats")

    assert response.status_code == 200
    assert response.json() == {
        "media_id": upload["media"]["id"],
        "frame_count": 0,
        "audio_segment_count": 0,
        "transcript_chunk_count": 0,
        "embedding_count": 0,
    }
