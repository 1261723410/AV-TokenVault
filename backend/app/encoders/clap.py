from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.encoders.base import EmbeddingResult


class MSCLAPAudioEncoder:
    modality = "audio"

    def __init__(
        self,
        *,
        version: str = "2023",
        use_cuda: bool = False,
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.version = version
        self.use_cuda = use_cuda
        self.encoder_name = f"msclap:{version}"
        self._model_factory = model_factory
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if self._model_factory is None:
            try:
                from msclap import CLAP
            except ImportError as exc:
                raise RuntimeError("msclap is not installed. Install optional CLAP dependencies first.") from exc

            self._model_factory = CLAP
        self._model = self._model_factory(version=self.version, use_cuda=self.use_cuda)
        return self._model

    def encode(self, path: Path) -> EmbeddingResult:
        model = self._load_model()
        embeddings = model.get_audio_embeddings([str(path)])
        vector = embeddings[0]
        if hasattr(vector, "tolist"):
            values = vector.tolist()
        else:
            values = list(vector)
        return EmbeddingResult(
            encoder_name=self.encoder_name,
            modality=self.modality,
            vector=[float(value) for value in values],
        )
