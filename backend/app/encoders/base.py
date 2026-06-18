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
