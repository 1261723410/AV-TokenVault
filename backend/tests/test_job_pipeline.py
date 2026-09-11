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

    def fake_extract_frames(
        input_path: Path,
        output_dir: Path,
        frame_interval: float,
        max_frames: int,
        duration_seconds: float | None = None,
    ):
        assert duration_seconds == 10.0
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
        assert session.query(Embedding).filter_by(media_id=media_id).count() == 3


def test_process_job_stores_actual_final_audio_segment_duration(tmp_path: Path, monkeypatch):
    from app.core.config import Settings
    from app.db.models import AudioSegment, Base, MediaAsset, ProcessingJob
    from app.pipeline import jobs

    settings = Settings(project_root=tmp_path)
    settings.ensure_runtime_dirs()
    engine = create_engine(f"sqlite:///{settings.sqlite_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    upload_path = settings.upload_root / "short.mp4"
    upload_path.write_bytes(b"video")

    with SessionLocal() as session:
        media = MediaAsset(
            filename="short.mp4",
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

    def fake_probe_media(path: Path):
        return jobs.MediaProbe(
            duration_seconds=9.25,
            width=640,
            height=360,
            has_video=path.suffix == ".mp4",
            has_audio=True,
        )

    def fake_extract_frames(
        input_path: Path,
        output_dir: Path,
        frame_interval: float,
        max_frames: int,
        duration_seconds: float | None = None,
    ):
        output_dir.mkdir(parents=True, exist_ok=True)
        return []

    def fake_extract_audio(input_path: Path, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")
        return output_path

    def fake_segment_audio(input_path: Path, output_dir: Path, segment_seconds: float):
        output_dir.mkdir(parents=True, exist_ok=True)
        first = output_dir / "segment_000000.wav"
        second = output_dir / "segment_000001.wav"
        first.write_bytes(b"first")
        second.write_bytes(b"second")
        return [first, second]

    monkeypatch.setattr(jobs, "probe_media", fake_probe_media)
    monkeypatch.setattr(jobs, "extract_frames", fake_extract_frames)
    monkeypatch.setattr(jobs, "extract_audio", fake_extract_audio)
    monkeypatch.setattr(jobs, "segment_audio", fake_segment_audio)

    jobs.process_job(job_id, settings=settings, session_factory=SessionLocal)

    with SessionLocal() as session:
        segments = session.query(AudioSegment).order_by(AudioSegment.segment_index).all()
        assert [segment.duration_seconds for segment in segments] == [5.0, 4.25]
        assert [segment.start_seconds for segment in segments] == [0.0, 5.0]
        assert [segment.end_seconds for segment in segments] == [5.0, 9.25]


def test_process_job_creates_transcript_text_embeddings(tmp_path: Path, monkeypatch):
    from app.core.config import Settings
    from app.db.models import AudioSegment, Base, Embedding, MediaAsset, ProcessingJob, TranscriptChunk
    from app.pipeline import jobs

    settings = Settings(project_root=tmp_path)
    settings.ensure_runtime_dirs()
    engine = create_engine(f"sqlite:///{settings.sqlite_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    upload_path = settings.upload_root / "speech.wav"
    upload_path.write_bytes(b"audio")

    with SessionLocal() as session:
        media = MediaAsset(
            filename="speech.wav",
            original_path=upload_path.relative_to(settings.data_root).as_posix(),
            media_type="audio",
            mime_type="audio/wav",
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
            duration_seconds=5.0,
            width=None,
            height=None,
            has_video=False,
            has_audio=True,
        )

    def fake_extract_audio(input_path: Path, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")
        return output_path

    def fake_segment_audio(input_path: Path, output_dir: Path, segment_seconds: float):
        output_dir.mkdir(parents=True, exist_ok=True)
        segment = output_dir / "segment_000000.wav"
        segment.write_bytes(b"segment")
        return [segment]

    monkeypatch.setattr(jobs, "probe_media", fake_probe_media)
    monkeypatch.setattr(jobs, "extract_audio", fake_extract_audio)
    monkeypatch.setattr(jobs, "segment_audio", fake_segment_audio)

    jobs.process_job(job_id, settings=settings, session_factory=SessionLocal)

    with SessionLocal() as session:
        segments = session.query(AudioSegment).filter_by(media_id=media_id).all()
        transcript_chunks = session.query(TranscriptChunk).filter_by(media_id=media_id).all()
        text_embeddings = session.query(Embedding).filter_by(media_id=media_id, modality="text").all()
        audio_embeddings = session.query(Embedding).filter_by(media_id=media_id, modality="audio").all()

        assert len(segments) == 1
        assert len(transcript_chunks) == 1
        assert transcript_chunks[0].text
        assert transcript_chunks[0].audio_segment_id == segments[0].id
        assert len(text_embeddings) == 1
        assert text_embeddings[0].source_type == "transcript_chunk"
        assert text_embeddings[0].source_id == transcript_chunks[0].id
        assert len(audio_embeddings) == 1
