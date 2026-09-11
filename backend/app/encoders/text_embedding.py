from collections.abc import Callable
from typing import Any

from app.encoders.base import EmbeddingResult


class SentenceTransformerTextEmbedder:
    modality = "text"

    def __init__(
        self,
        *,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str | None = None,
        cache_folder: str | None = None,
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.cache_folder = cache_folder
        self.encoder_name = f"sentence-transformers:{model_name}"
        self._model_factory = model_factory
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if self._model_factory is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is not installed. Install optional model dependencies first."
                ) from exc

            self._model_factory = SentenceTransformer

        self._model = self._model_factory(
            self.model_name,
            device=self.device,
            cache_folder=self.cache_folder,
        )
        return self._model

    def encode_text(self, text: str) -> EmbeddingResult:
        model = self._load_model()
        vector = model.encode(text, normalize_embeddings=True)
        if hasattr(vector, "tolist"):
            values = vector.tolist()
        else:
            values = list(vector)
        return EmbeddingResult(
            encoder_name=self.encoder_name,
            modality=self.modality,
            vector=[float(value) for value in values],
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Embed one text with sentence-transformers.")
    parser.add_argument("text")
    parser.add_argument("--model-name", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    result = SentenceTransformerTextEmbedder(model_name=args.model_name, device=args.device).encode_text(args.text)
    print({"encoder": result.encoder_name, "dimension": result.dimension, "preview": result.vector[:5]})


if __name__ == "__main__":
    main()
