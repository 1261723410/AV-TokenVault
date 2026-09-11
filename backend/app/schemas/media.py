from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_path: str
    media_type: str
    mime_type: str | None
    duration_seconds: float | None
    file_size: int
    created_at: datetime


class ProcessingJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_id: int
    status: str
    progress: float
    mode: str
    frame_interval: float
    segment_seconds: float
    image_encoder: str
    audio_encoder: str
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class JobLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    level: str
    message: str
    created_at: datetime


class VideoFrameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_id: int
    job_id: int
    frame_index: int
    timestamp_seconds: float
    image_path: str
    width: int | None
    height: int | None


class AudioSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_id: int
    job_id: int
    segment_index: int
    start_seconds: float
    end_seconds: float
    audio_path: str
    duration_seconds: float


class TranscriptChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_id: int
    job_id: int
    audio_segment_id: int
    chunk_index: int
    start_seconds: float
    end_seconds: float
    text: str
    language: str | None
    source: str
    created_at: datetime


class UploadResponse(BaseModel):
    media: MediaAssetRead
    job: ProcessingJobRead


class MediaStatsRead(BaseModel):
    media_id: int
    frame_count: int
    audio_segment_count: int
    transcript_chunk_count: int
    embedding_count: int


class SearchRequest(BaseModel):
    query: str
    modality: str = "text"
    limit: int = 5


class SearchResultRead(BaseModel):
    embedding_id: int
    media_id: int
    job_id: int
    modality: str
    source_type: str
    source_id: int
    encoder_name: str
    score: float
    text: str | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultRead]
