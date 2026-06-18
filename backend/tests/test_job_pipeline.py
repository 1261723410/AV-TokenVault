from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_process_job_completes_video_with_fake_extractors(tmp_path: Path, monkeypatch):
    from app.core.config import Settings
    from app.db.models import AudioSegment, Base, Embedding, MediaAsset, ProcessingJob, VideoFrame
    from app.pipeline import jobs

    settings = Settings(project_root=tmp_path)
    settings.ensure_runtime_dirs()
    engine = create_engine(f"sqlite:///{settings.sqlite_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    upload_path = settings.upload_root / "demo.mp4"
    upload_path.write_bytes(b"video")

    with SessionLocal() as session:
        media = MediaAsset(
            filename="demo.mp4",
            original_path=upload_path.relative_to(settings.data_root).as_posix(),
            media_type="video",
            mime_type="video/mp4",
            duration_seconds=None,
            file_size=5,
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
        session.commit()
        job_id = job.id
        media_id = media.id

    def fake_probe_media(path: Path):
        return jobs.MediaProbe(
            duration_seconds=10.0,
            width=640,
            height=360,
            has_video=True,
            has_audio=True,
        )

    def fake_extract_frames(input_path: Path, output_dir: Path, frame_interval: float, max_frames: int):
        output_dir.mkdir(parents=True, exist_ok=True)
        frame = output_dir / "frame_000001.jpg"
        frame.write_bytes(b"frame")
        return [frame]

    def fake_extract_audio(input_path: Path, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")
        return output_path

    def fake_segment_audio(input_path: Path, output_dir: Path, segment_seconds: float):
        output_dir.mkdir(parents=True, exist_ok=True)
        segment = output_dir / "segment_000001.wav"
        segment.write_bytes(b"segment")
        return [segment]

    monkeypatch.setattr(jobs, "probe_media", fake_probe_media)
    monkeypatch.setattr(jobs, "extract_frames", fake_extract_frames)
    monkeypatch.setattr(jobs, "extract_audio", fake_extract_audio)
    monkeypatch.setattr(jobs, "segment_audio", fake_segment_audio)

    jobs.process_job(job_id, settings=settings, session_factory=SessionLocal)

    with SessionLocal() as session:
        stored_job = session.get(ProcessingJob, job_id)
        assert stored_job is not None
        assert stored_job.status == "completed"
        assert stored_job.progress == 1.0
        assert stored_job.started_at is not None
        assert stored_job.completed_at is not None
        assert len(stored_job.logs) >= 2
        assert session.query(VideoFrame).filter_by(media_id=media_id).count() == 1
        assert session.query(AudioSegment).filter_by(media_id=media_id).count() == 1
        assert session.query(Embedding).filter_by(media_id=media_id).count() == 2
