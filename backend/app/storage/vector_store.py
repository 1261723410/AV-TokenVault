import json
import math
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Embedding
from app.encoders.base import EmbeddingResult


@dataclass(frozen=True)
class SearchHit:
    embedding_id: int
    media_id: int
    job_id: int
    modality: str
    source_type: str
    source_id: int
    encoder_name: str
    score: float


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return -1.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return -1.0
    return dot / (left_norm * right_norm)


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

    def search_embeddings(
        self,
        query_vector: list[float],
        *,
        modality: str | None = None,
        encoder_name: str | None = None,
        limit: int = 5,
    ) -> list[SearchHit]:
        statement = select(Embedding)
        if modality and modality != "all":
            statement = statement.where(Embedding.modality == modality)
        if encoder_name:
            statement = statement.where(Embedding.encoder_name == encoder_name)

        hits: list[SearchHit] = []
        for record in self._session.scalars(statement):
            vector = json.loads(record.vector_json)
            score = _cosine_similarity(query_vector, vector)
            if score < -0.5:
                continue
            hits.append(
                SearchHit(
                    embedding_id=record.id,
                    media_id=record.media_id,
                    job_id=record.job_id,
                    modality=record.modality,
                    source_type=record.source_type,
                    source_id=record.source_id,
                    encoder_name=record.encoder_name,
                    score=score,
                )
            )

        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]
