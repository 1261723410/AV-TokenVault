from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_sqlite_vector_store_persists_embedding_records():
    from app.db.models import Base, Embedding, MediaAsset, ProcessingJob
    from app.encoders.base import EmbeddingResult
    from app.storage.vector_store import SQLiteVectorStore

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
            status="running",
            progress=0.5,
            mode="full",
            frame_interval=2.0,
            segment_seconds=5.0,
            image_encoder="mock-image-encoder",
            audio_encoder="mock-audio-encoder",
            created_at=datetime.now(UTC),
        )
        session.add(job)
        session.flush()

        store = SQLiteVectorStore(session)
        record = store.add_embedding(
            media_id=media.id,
            job_id=job.id,
            source_type="audio_segment",
            source_id=7,
            result=EmbeddingResult(
                encoder_name="mock-audio-encoder",
                modality="audio",
                vector=[0.1, 0.2, 0.3],
            ),
        )
        session.commit()

        stored = session.get(Embedding, record.id)
        assert stored is not None
        assert stored.modality == "audio"
        assert stored.source_type == "audio_segment"
        assert stored.source_id == 7
        assert stored.vector_dimension == 3
        assert stored.vector_json == "[0.1, 0.2, 0.3]"
