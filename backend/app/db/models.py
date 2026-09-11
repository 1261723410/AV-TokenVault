from datetime import UTC, datetime

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="media")
    frames: Mapped[list["VideoFrame"]] = relationship(back_populates="media")
    audio_segments: Mapped[list["AudioSegment"]] = relationship(back_populates="media")
    embeddings: Mapped[list["Embedding"]] = relationship(back_populates="media")
    transcript_chunks: Mapped[list["TranscriptChunk"]] = relationship(back_populates="media")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="full")
    frame_interval: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    segment_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    image_encoder: Mapped[str] = mapped_column(String(128), nullable=False, default="mock-image-encoder")
    audio_encoder: Mapped[str] = mapped_column(String(128), nullable=False, default="mock-audio-encoder")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    media: Mapped[MediaAsset] = relationship(back_populates="jobs")
    logs: Mapped[list["JobLog"]] = relationship(back_populates="job")
    frames: Mapped[list["VideoFrame"]] = relationship(back_populates="job")
    audio_segments: Mapped[list["AudioSegment"]] = relationship(back_populates="job")
    embeddings: Mapped[list["Embedding"]] = relationship(back_populates="job")
    transcript_chunks: Mapped[list["TranscriptChunk"]] = relationship(back_populates="job")


class JobLog(Base):
    __tablename__ = "job_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    job: Mapped[ProcessingJob] = relationship(back_populates="logs")


class VideoFrame(Base):
    __tablename__ = "video_frames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False)
    frame_index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    media: Mapped[MediaAsset] = relationship(back_populates="frames")
    job: Mapped[ProcessingJob] = relationship(back_populates="frames")


class AudioSegment(Base):
    __tablename__ = "audio_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    audio_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    media: Mapped[MediaAsset] = relationship(back_populates="audio_segments")
    job: Mapped[ProcessingJob] = relationship(back_populates="audio_segments")
    transcript_chunks: Mapped[list["TranscriptChunk"]] = relationship(back_populates="audio_segment")


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False)
    audio_segment_id: Mapped[int] = mapped_column(ForeignKey("audio_segments.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    media: Mapped[MediaAsset] = relationship(back_populates="transcript_chunks")
    job: Mapped[ProcessingJob] = relationship(back_populates="transcript_chunks")
    audio_segment: Mapped[AudioSegment] = relationship(back_populates="transcript_chunks")


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False)
    modality: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    encoder_name: Mapped[str] = mapped_column(String(128), nullable=False)
    vector_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    media: Mapped[MediaAsset] = relationship(back_populates="embeddings")
    job: Mapped[ProcessingJob] = relationship(back_populates="embeddings")
