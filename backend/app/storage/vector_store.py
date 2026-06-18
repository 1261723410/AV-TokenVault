import json
from typing import Protocol

from sqlalchemy.orm import Session

from app.db.models import Embedding
from app.encoders.base import EmbeddingResult


class VectorStore(Protocol):
    def add_embedding(
        self,
        *,
        media_id: int,
        job_id: int,
        source_type: str,
        source_id: int,
        result: EmbeddingResult,
    ) -> Embedding:
        raise NotImplementedError


class SQLiteVectorStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_embedding(
        self,
        *,
        media_id: int,
        job_id: int,
        source_type: str,
        source_id: int,
        result: EmbeddingResult,
    ) -> Embedding:
        record = Embedding(
            media_id=media_id,
            job_id=job_id,
            modality=result.modality,
            source_type=source_type,
            source_id=source_id,
            encoder_name=result.encoder_name,
            vector_dimension=result.dimension,
            vector_json=json.dumps(result.vector),
        )
        self._session.add(record)
        self._session.flush()
        return record
