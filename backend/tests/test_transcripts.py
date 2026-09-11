from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_transcript_chunks_belong_to_media_job_and_audio_segment():
    from app.db.models import AudioSegment, Base, MediaAsset, ProcessingJob, TranscriptChunk

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

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
            text="老师讲到音视频 token 化。",
            language="zh",
            source="mock-transcriber",
            created_at=datetime.now(UTC),
        )
        session.add(chunk)
        session.commit()

        stored = session.get(TranscriptChunk, chunk.id)
        assert stored is not None
        assert stored.media.filename == "demo.wav"
        assert stored.job.id == job.id
        assert stored.audio_segment.id == segment.id
        assert stored.text == "老师讲到音视频 token 化。"


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


def test_get_media_transcripts_returns_ordered_chunks(client_with_session):
    from app.db.models import AudioSegment, MediaAsset, ProcessingJob, TranscriptChunk

    client, SessionLocal = client_with_session
    with SessionLocal() as session:
        media = MediaAsset(
            filename="demo.wav",
            original_path="uploads/demo.wav",
            media_type="audio",
            mime_type="audio/wav",
            duration_seconds=10.0,
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
        session.add_all(
            [
                TranscriptChunk(
                    media_id=media.id,
                    job_id=job.id,
                    audio_segment_id=segment.id,
                    chunk_index=1,
                    start_seconds=5.0,
                    end_seconds=10.0,
                    text="第二段",
                    language="zh",
                    source="mock-transcriber",
                    created_at=datetime.now(UTC),
                ),
                TranscriptChunk(
                    media_id=media.id,
                    job_id=job.id,
                    audio_segment_id=segment.id,
                    chunk_index=0,
                    start_seconds=0.0,
                    end_seconds=5.0,
                    text="第一段",
                    language="zh",
                    source="mock-transcriber",
                    created_at=datetime.now(UTC),
                ),
            ]
        )
        session.commit()
        media_id = media.id

    response = client.get(f"/api/media/{media_id}/transcripts")

    assert response.status_code == 200
    assert [chunk["text"] for chunk in response.json()] == ["第一段", "第二段"]
