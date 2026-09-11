from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_mock_text_embedder_returns_deterministic_text_embedding():
    from app.encoders.mock import MockTextEmbedder

    embedder = MockTextEmbedder(dimension=8)
    first = embedder.encode_text("音视频 token 化")
    second = embedder.encode_text("音视频 token 化")

    assert first.encoder_name == "mock-text-embedder"
    assert first.modality == "text"
    assert first.dimension == 8
    assert first.vector == second.vector


def test_sqlite_vector_store_ranks_by_cosine_similarity():
    from app.db.models import Base, Embedding, MediaAsset, ProcessingJob
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
        session.add_all(
            [
                Embedding(
                    media_id=media.id,
                    job_id=job.id,
                    modality="text",
                    source_type="transcript_chunk",
                    source_id=1,
                    encoder_name="mock-text-embedder",
                    vector_dimension=3,
                    vector_json="[1.0, 0.0, 0.0]",
                    created_at=datetime.now(UTC),
                ),
                Embedding(
                    media_id=media.id,
                    job_id=job.id,
                    modality="text",
                    source_type="transcript_chunk",
                    source_id=2,
                    encoder_name="mock-text-embedder",
                    vector_dimension=3,
                    vector_json="[0.0, 1.0, 0.0]",
                    created_at=datetime.now(UTC),
                ),
            ]
        )
        session.commit()

        hits = SQLiteVectorStore(session).search_embeddings([0.9, 0.1, 0.0], modality="text", limit=2)

        assert [hit.source_id for hit in hits] == [1, 2]
        assert hits[0].score > hits[1].score
