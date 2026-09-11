from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class EmbeddingResult:
    encoder_name: str
    modality: str
    vector: list[float]

    @property
    def dimension(self) -> int:
        return len(self.vector)


@dataclass(frozen=True)
class TranscriptChunkResult:
    text: str
    start_seconds: float
    end_seconds: float
    language: str | None
    source: str


class ImageEncoder(Protocol):
    encoder_name: str
    modality: str

    def encode(self, path: Path) -> EmbeddingResult:
        raise NotImplementedError


class AudioEncoder(Protocol):
    encoder_name: str
    modality: str

    def encode(self, path: Path) -> EmbeddingResult:
        raise NotImplementedError


class Transcriber(Protocol):
    transcriber_name: str

    def transcribe_segment(self, path: Path, *, start_seconds: float, end_seconds: float) -> TranscriptChunkResult:
        raise NotImplementedError


class TextEmbeddingEncoder(Protocol):
    encoder_name: str
    modality: str

    def encode_text(self, text: str) -> EmbeddingResult:
        raise NotImplementedError
