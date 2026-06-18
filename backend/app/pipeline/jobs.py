from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.db.models import AudioSegment, JobLog, ProcessingJob, VideoFrame
from app.db.session import SessionLocal
from app.encoders.mock import MockAudioEncoder, MockImageEncoder
from app.media.extract import extract_audio, extract_frames, segment_audio
from app.media.probe import MediaProbe, probe_media
from app.storage.vector_store import SQLiteVectorStore

_job_lock = Lock()


def _now() -> datetime:
    return datetime.now(UTC)


def _log(db: Session, job_id: int, message: str, level: str = "info") -> None:
    db.add(JobLog(job_id=job_id, level=level, message=message, created_at=_now()))
    db.flush()


def _set_progress(db: Session, job: ProcessingJob, progress: float) -> None:
    job.progress = progress
    db.add(job)
    db.flush()


def _relative_to_data(path: Path, settings: Settings) -> str:
    return path.relative_to(settings.data_root).as_posix()


def _timestamp_for_frame(index: int, frame_interval: float) -> float:
    return index * frame_interval


def _create_frame_records(
    db: Session,
    *,
    job: ProcessingJob,
    frame_paths: list[Path],
    media_width: int | None,
    media_height: int | None,
    settings: Settings,
) -> list[VideoFrame]:
    records: list[VideoFrame] = []
    for index, frame_path in enumerate(frame_paths):
        record = VideoFrame(
            media_id=job.media_id,
            job_id=job.id,
            frame_index=index,
            timestamp_seconds=_timestamp_for_frame(index, job.frame_interval),
            image_path=_relative_to_data(frame_path, settings),
            width=media_width,
            height=media_height,
        )
        db.add(record)
        records.append(record)
    db.flush()
    return records


def _create_audio_segment_records(
    db: Session,
    *,
    job: ProcessingJob,
    segment_paths: list[Path],
    settings: Settings,
) -> list[AudioSegment]:
    records: list[AudioSegment] = []
    for index, segment_path in enumerate(segment_paths):
        start = index * job.segment_seconds
        end = start + job.segment_seconds
        record = AudioSegment(
            media_id=job.media_id,
            job_id=job.id,
            segment_index=index,
            start_seconds=start,
            end_seconds=end,
            audio_path=_relative_to_data(segment_path, settings),
            duration_seconds=job.segment_seconds,
        )
        db.add(record)
        records.append(record)
    db.flush()
    return records


def _encode_frames(
    db: Session,
    *,
    job: ProcessingJob,
    frames: list[VideoFrame],
    settings: Settings,
) -> None:
    encoder = MockImageEncoder()
    vector_store = SQLiteVectorStore(db)
    for frame in frames:
        result = encoder.encode(settings.data_root / frame.image_path)
        vector_store.add_embedding(
            media_id=job.media_id,
            job_id=job.id,
            source_type="frame",
            source_id=frame.id,
            result=result,
        )


def _encode_audio_segments(
    db: Session,
    *,
    job: ProcessingJob,
    segments: list[AudioSegment],
    settings: Settings,
) -> None:
    encoder = MockAudioEncoder()
    vector_store = SQLiteVectorStore(db)
    for segment in segments:
        result = encoder.encode(settings.data_root / segment.audio_path)
        vector_store.add_embedding(
            media_id=job.media_id,
            job_id=job.id,
            source_type="audio_segment",
            source_id=segment.id,
            result=result,
        )


def process_job(
    job_id: int,
    *,
    settings: Settings | None = None,
    session_factory: sessionmaker | Callable[[], Session] = SessionLocal,
) -> None:
    active_settings = settings or get_settings()
    active_settings.ensure_runtime_dirs()

    with _job_lock:
        with session_factory() as db:
            job = db.get(ProcessingJob, job_id)
            if job is None:
                return

            job.status = "running"
            job.progress = 0.05
            job.started_at = _now()
            job.error_message = None
            db.add(job)
            _log(db, job.id, "任务开始")
            db.commit()

            try:
                media = job.media
                input_path = active_settings.data_root / media.original_path
                media_info = probe_media(input_path)
                media.duration_seconds = media_info.duration_seconds
                db.add(media)
                _set_progress(db, job, 0.15)
                _log(db, job.id, "媒体元信息读取完成")

                job_output_root = active_settings.extracted_root / f"job_{job.id}"
                frame_records: list[VideoFrame] = []
                segment_records: list[AudioSegment] = []

                if media.media_type == "video":
                    frame_paths = extract_frames(
                        input_path,
                        job_output_root / "frames",
                        job.frame_interval,
                        active_settings.max_frames,
                    )
                    frame_records = _create_frame_records(
                        db,
                        job=job,
                        frame_paths=frame_paths,
                        media_width=media_info.width,
                        media_height=media_info.height,
                        settings=active_settings,
                    )
                    _set_progress(db, job, 0.4)
                    _log(db, job.id, f"抽取视频帧 {len(frame_records)} 个")

                    audio_path = extract_audio(input_path, job_output_root / "audio" / "track.wav")
                    segment_paths = segment_audio(audio_path, job_output_root / "segments", job.segment_seconds)
                    segment_records = _create_audio_segment_records(
                        db,
                        job=job,
                        segment_paths=segment_paths,
                        settings=active_settings,
                    )
                    _set_progress(db, job, 0.65)
                    _log(db, job.id, f"切分音频片段 {len(segment_records)} 个")

                elif media.media_type == "audio":
                    wav_path = extract_audio(input_path, job_output_root / "audio" / "source.wav")
                    segment_paths = segment_audio(wav_path, job_output_root / "segments", job.segment_seconds)
                    segment_records = _create_audio_segment_records(
                        db,
                        job=job,
                        segment_paths=segment_paths,
                        settings=active_settings,
                    )
                    _set_progress(db, job, 0.65)
                    _log(db, job.id, f"切分音频片段 {len(segment_records)} 个")

                _encode_frames(db, job=job, frames=frame_records, settings=active_settings)
                _encode_audio_segments(db, job=job, segments=segment_records, settings=active_settings)
                _set_progress(db, job, 0.9)
                _log(db, job.id, "embedding 写入完成")

                job.status = "completed"
                job.progress = 1.0
                job.completed_at = _now()
                db.add(job)
                _log(db, job.id, "任务完成")
                db.commit()

            except Exception as exc:
                job.status = "failed"
                job.error_message = str(exc)
                job.completed_at = _now()
                db.add(job)
                _log(db, job.id, f"任务失败：{exc}", level="error")
                db.commit()
