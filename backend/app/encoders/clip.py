from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from app.encoders.base import EmbeddingResult


class OpenCLIPImageEncoder:
    modality = "image"

    def __init__(
        self,
        *,
        model_name: str = "ViT-B-32",
        pretrained: str = "laion2b_s34b_b79k",
        device: str = "cpu",
        model_factory: Callable[..., tuple[Any, Any, Callable[[Image.Image], Any]]] | None = None,
        no_grad: Callable[[], Any] | None = None,
    ) -> None:
        self.model_name = model_name
        self.pretrained = pretrained
        self.device = device
        self.encoder_name = f"open-clip:{model_name}:{pretrained}"
        self._model_factory = model_factory
        self._no_grad = no_grad
        self._model: Any | None = None
        self._preprocess: Callable[[Image.Image], Any] | None = None

    def _load_model(self) -> tuple[Any, Callable[[Image.Image], Any], Callable[[], Any]]:
        if self._model is not None and self._preprocess is not None and self._no_grad is not None:
            return self._model, self._preprocess, self._no_grad

        if self._model_factory is None or self._no_grad is None:
            try:
                import open_clip
                import torch
            except ImportError as exc:
                raise RuntimeError("open-clip-torch and torch are not installed.") from exc

            self._model_factory = open_clip.create_model_and_transforms
            self._no_grad = torch.no_grad

        model, _, preprocess = self._model_factory(
            self.model_name,
            pretrained=self.pretrained,
            device=self.device,
        )
        self._model = model.to(self.device).eval()
        self._preprocess = preprocess
        return self._model, self._preprocess, self._no_grad

    def encode(self, path: Path) -> EmbeddingResult:
        model, preprocess, no_grad = self._load_model()
        with Image.open(path) as image:
            image_input = preprocess(image.convert("RGB")).unsqueeze(0).to(self.device)

        with no_grad():
            vector = model.encode_image(image_input)

        if hasattr(vector, "squeeze"):
            vector = vector.squeeze(0)
        if hasattr(vector, "detach"):
            vector = vector.detach()
        if hasattr(vector, "cpu"):
            vector = vector.cpu()
        if hasattr(vector, "tolist"):
            values = vector.tolist()
        else:
            values = list(vector)

        return EmbeddingResult(
            encoder_name=self.encoder_name,
            modality=self.modality,
            vector=[float(value) for value in values],
        )
