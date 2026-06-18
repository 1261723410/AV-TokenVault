from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.paths import safe_artifact_path
from app.db.models import AudioSegment, Embedding, JobLog, MediaAsset, ProcessingJob, VideoFrame
from app.db.session import get_db
from app.schemas.media import (
    AudioSegmentRead,
    JobLogRead,
    MediaAssetRead,
    MediaStatsRead,
    ProcessingJobRead,
    UploadResponse,
    VideoFrameRead,
)

router = APIRouter()

VIDEO_EXTENSIONS = {".mp4", ".mov"}
AUDIO_EXTENSIONS = {".wav", ".mp3"}


def _settings_dep() -> Settings:
    return get_settings()


def detect_media_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    raise ValueError("Unsupported media type")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/media/upload", response_model=UploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    frame_interval: float | None = Form(default=None),
    segment_seconds: float | None = Form(default=None),
    image_encoder: str | None = Form(default=None),
    audio_encoder: str | None = Form(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(_settings_dep),
) -> UploadResponse:
    try:
        media_type = detect_media_type(file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    settings.ensure_runtime_dirs()
    safe_name = Path(file.filename or "upload.bin").name
    stored_name = f"{uuid4().hex}_{safe_name}"
    upload_path = settings.upload_root / stored_name
    content = await file.read()
    upload_path.write_bytes(content)

    relative_upload_path = upload_path.relative_to(settings.data_root).as_posix()
    media = MediaAsset(
        filename=safe_name,
        original_path=relative_upload_path,
        media_type=media_type,
        mime_type=file.content_type,
        duration_seconds=None,
        file_size=len(content),
        created_at=datetime.now(UTC),
    )
    db.add(media)
    db.flush()

    job = ProcessingJob(
        media_id=media.id,
        status="pending",
        progress=0.0,
        mode="full",
        frame_interval=frame_interval or settings.default_frame_interval,
        segment_seconds=segment_seconds or settings.default_segment_seconds,
        image_encoder=image_encoder or settings.default_image_encoder,
        audio_encoder=audio_encoder or settings.default_audio_encoder,
        created_at=datetime.now(UTC),
    )
    db.add(job)
    db.commit()
    db.refresh(media)
    db.refresh(job)

    return UploadResponse(media=MediaAssetRead.model_validate(media), job=ProcessingJobRead.model_validate(job))


@router.get("/api/jobs", response_model=list[ProcessingJobRead])
def list_jobs(db: Session = Depends(get_db)) -> list[ProcessingJob]:
    return list(db.scalars(select(ProcessingJob).order_by(ProcessingJob.created_at.desc())).all())


@router.get("/api/jobs/{job_id}", response_model=ProcessingJobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/api/jobs/{job_id}/start", response_model=ProcessingJobRead)
def start_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in {"pending", "failed"}:
        return job

    from app.pipeline.jobs import process_job

    background_tasks.add_task(process_job, job_id)
    return job


@router.get("/api/jobs/{job_id}/logs", response_model=list[JobLogRead])
def get_job_logs(job_id: int, db: Session = Depends(get_db)) -> list[JobLog]:
    return list(db.scalars(select(JobLog).where(JobLog.job_id == job_id).order_by(JobLog.created_at)).all())


@router.get("/api/media/{media_id}", response_model=MediaAssetRead)
def get_media(media_id: int, db: Session = Depends(get_db)) -> MediaAsset:
    media = db.get(MediaAsset, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return media


@router.get("/api/media/{media_id}/frames", response_model=list[VideoFrameRead])
def get_media_frames(media_id: int, db: Session = Depends(get_db)) -> list[VideoFrame]:
    return list(db.scalars(select(VideoFrame).where(VideoFrame.media_id == media_id).order_by(VideoFrame.frame_index)).all())


@router.get("/api/media/{media_id}/audio-segments", response_model=list[AudioSegmentRead])
def get_media_audio_segments(media_id: int, db: Session = Depends(get_db)) -> list[AudioSegment]:
    return list(
        db.scalars(select(AudioSegment).where(AudioSegment.media_id == media_id).order_by(AudioSegment.segment_index)).all()
    )


@router.get("/api/media/{media_id}/stats", response_model=MediaStatsRead)
def get_media_stats(media_id: int, db: Session = Depends(get_db)) -> MediaStatsRead:
    frame_count = db.scalar(select(func.count()).select_from(VideoFrame).where(VideoFrame.media_id == media_id)) or 0
    audio_segment_count = db.scalar(
        select(func.count()).select_from(AudioSegment).where(AudioSegment.media_id == media_id)
    ) or 0
    embedding_count = db.scalar(select(func.count()).select_from(Embedding).where(Embedding.media_id == media_id)) or 0

    return MediaStatsRead(
        media_id=media_id,
        frame_count=frame_count,
        audio_segment_count=audio_segment_count,
        embedding_count=embedding_count,
    )


@router.get("/api/files/{artifact_path:path}")
def get_file(
    artifact_path: str,
    settings: Settings = Depends(_settings_dep),
) -> FileResponse:
    try:
        path = safe_artifact_path(artifact_path, settings=settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
