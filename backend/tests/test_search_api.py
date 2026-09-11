from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client_with_session(tmp_path: Path):
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
    return TestClient(app), SessionLocal


def test_search_api_returns_matching_transcript_chunk(client_with_session):
    from app.db.models import AudioSegment, Embedding, MediaAsset, ProcessingJob, TranscriptChunk
    from app.encoders.mock import MockTextEmbedder

    client, SessionLocal = client_with_session
    with SessionLocal() as session:
        media = MediaAsset(
            filename="demo.wav",
            original_path="uploads/demo.wav",
            media_type="audio",
            mime_type="audio/wav",
            duration_seconds=5.0,
            file_size=100,
            created_at=datetime.now(UTC),
        )
        session.add(media)
        session.flush()
        job = ProcessingJob(
            media_id=media.id,
            status="completed",
            progress=1.0,
            mode="full",
            frame_interval=2.0,
            segment_seconds=5.0,
            image_encoder="mock-image-encoder",
            audio_encoder="mock-audio-encoder",
            created_at=datetime.now(UTC),
        )
        session.add(job)
        session.flush()
        segment = AudioSegment(
            media_id=media.id,
            job_id=job.id,
            segment_index=0,
            start_seconds=0.0,
            end_seconds=5.0,
            audio_path="extracted/job_1/segments/segment_000000.wav",
            duration_seconds=5.0,
        )
        session.add(segment)
        session.flush()
        chunk = TranscriptChunk(
            media_id=media.id,
            job_id=job.id,
            audio_segment_id=segment.id,
            chunk_index=0,
            start_seconds=0.0,
            end_seconds=5.0,
            text="音视频 token 化可以用于检索。",
            language="zh",
            source="mock-transcriber",
            created_at=datetime.now(UTC),
        )
        session.add(chunk)
        session.flush()
        result = MockTextEmbedder().encode_text(chunk.text)
        session.add(
            Embedding(
                media_id=media.id,
                job_id=job.id,
                modality=result.modality,
                source_type="transcript_chunk",
                source_id=chunk.id,
                encoder_name=result.encoder_name,
                vector_dimension=result.dimension,
                vector_json=str(result.vector),
                created_at=datetime.now(UTC),
            )
        )
        session.commit()

    response = client.post("/api/search", json={"query": "音视频 token 化可以用于检索。", "modality": "text", "limit": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "音视频 token 化可以用于检索。"
    assert payload["results"][0]["source_type"] == "transcript_chunk"
    assert payload["results"][0]["text"] == "音视频 token 化可以用于检索。"
    assert payload["results"][0]["score"] > 0.99


def test_search_api_rejects_image_modality(client_with_session):
    client, _ = client_with_session

    response = client.post("/api/search", json={"query": "会议室屏幕", "modality": "image", "limit": 3})

    assert response.status_code == 400
    assert "Only transcript text search" in response.json()["detail"]
