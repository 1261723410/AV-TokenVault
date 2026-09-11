import hashlib
from pathlib import Path

from app.encoders.base import EmbeddingResult, TranscriptChunkResult


def _deterministic_vector(seed: str, dimension: int) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < dimension:
        digest = hashlib.sha256(f"{seed}:{counter}".encode("utf-8")).digest()
        for byte in digest:
            values.append(round((byte / 255.0) * 2.0 - 1.0, 6))
            if len(values) == dimension:
                break
        counter += 1
    return values


class MockImageEncoder:
    encoder_name = "mock-image-encoder"
    modality = "image"

    def __init__(self, dimension: int = 32) -> None:
        self._dimension = dimension

    def encode(self, path: Path) -> EmbeddingResult:
        seed = f"{self.encoder_name}:{Path(path).as_posix()}"
        return EmbeddingResult(
            encoder_name=self.encoder_name,
            modality=self.modality,
            vector=_deterministic_vector(seed, self._dimension),
        )


class MockAudioEncoder:
    encoder_name = "mock-audio-encoder"
    modality = "audio"

    def __init__(self, dimension: int = 32) -> None:
        self._dimension = dimension

    def encode(self, path: Path) -> EmbeddingResult:
        seed = f"{self.encoder_name}:{Path(path).as_posix()}"
        return EmbeddingResult(
            encoder_name=self.encoder_name,
            modality=self.modality,
            vector=_deterministic_vector(seed, self._dimension),
        )


class MockTextEmbedder:
    encoder_name = "mock-text-embedder"
    modality = "text"

    def __init__(self, dimension: int = 32) -> None:
        self._dimension = dimension

    def encode_text(self, text: str) -> EmbeddingResult:
        seed = f"{self.encoder_name}:{text}"
        return EmbeddingResult(
            encoder_name=self.encoder_name,
            modality=self.modality,
            vector=_deterministic_vector(seed, self._dimension),
        )


class MockTranscriber:
    transcriber_name = "mock-transcriber"

    def transcribe_segment(self, path: Path, *, start_seconds: float, end_seconds: float) -> TranscriptChunkResult:
        segment_name = Path(path).stem
        text = f"mock transcript {segment_name} {start_seconds:.1f}-{end_seconds:.1f}s"
        return TranscriptChunkResult(
            text=text,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            language="und",
            source=self.transcriber_name,
        )
