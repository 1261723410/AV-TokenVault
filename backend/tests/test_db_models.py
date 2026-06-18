from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_database_models_persist_core_relationships():
    from app.db.models import (
        AudioSegment,
        Base,
        Embedding,
        JobLog,
        MediaAsset,
        ProcessingJob,
        VideoFrame,
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        media = MediaAsset(
            filename="demo.mp4",
            original_path="uploads/demo.mp4",
            media_type="video",
            mime_type="video/mp4",
            duration_seconds=12.5,
            file_size=1024,
            created_at=datetime.now(UTC),
        )
        session.add(media)
        session.flush()

        job = ProcessingJob(
            media_id=media.id,
            status="pending",
            progress=0.0,
            mode="full",
            frame_interval=2.0,
            segment_seconds=5.0,
            image_encoder="mock-image-encoder",
            audio_encoder="mock-audio-encoder",
            created_at=datetime.now(UTC),
        )
        session.add(job)
        session.flush()

        session.add(
            JobLog(
                job_id=job.id,
                level="info",
                message="created",
                created_at=datetime.now(UTC),
            )
        )
        frame = VideoFrame(
            media_id=media.id,
            job_id=job.id,
            frame_index=0,
            timestamp_seconds=0.0,
            image_path="extracted/demo/frame_000001.jpg",
            width=320,
            height=180,
        )
        segment = AudioSegment(
            media_id=media.id,
            job_id=job.id,
            segment_index=0,
            start_seconds=0.0,
            end_seconds=5.0,
            audio_path="extracted/demo/audio_000001.wav",
            duration_seconds=5.0,
        )
        session.add_all([frame, segment])
        session.flush()

        session.add(
            Embedding(
                media_id=media.id,
                job_id=job.id,
                modality="image",
                source_type="frame",
                source_id=frame.id,
                encoder_name="mock-image-encoder",
                vector_dimension=4,
                vector_json="[0.1, 0.2, 0.3, 0.4]",
                created_at=datetime.now(UTC),
            )
        )
        session.commit()

        stored_job = session.get(ProcessingJob, job.id)
        stored_media = session.get(MediaAsset, media.id)

        assert stored_job is not None
        assert stored_job.media.filename == "demo.mp4"
        assert len(stored_job.logs) == 1
        assert len(stored_media.frames) == 1
        assert len(stored_media.audio_segments) == 1
        assert len(stored_media.embeddings) == 1
