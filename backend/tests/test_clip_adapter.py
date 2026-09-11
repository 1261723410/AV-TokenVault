from pathlib import Path

from PIL import Image


def test_open_clip_image_encoder_returns_embedding(tmp_path: Path):
    from app.encoders.clip import OpenCLIPImageEncoder

    class FakeTensor:
        def unsqueeze(self, dim: int):
            return self

        def to(self, device: str):
            return self

        def tolist(self):
            return [0.1, 0.2, 0.3]

    class FakeModel:
        def to(self, device: str):
            return self

        def eval(self):
            return self

        def encode_image(self, image):
            return FakeTensor()

    def fake_preprocess(image):
        return FakeTensor()

    def fake_model_factory(model_name: str, pretrained: str, device: str):
        return FakeModel(), None, fake_preprocess

    image_path = tmp_path / "frame.jpg"
    Image.new("RGB", (8, 8), color="white").save(image_path)
    encoder = OpenCLIPImageEncoder(
        model_name="ViT-B-32",
        pretrained="laion2b_s34b_b79k",
        model_factory=fake_model_factory,
        no_grad=lambda: _NoopContext(),
    )

    result = encoder.encode(image_path)

    assert result.encoder_name == "open-clip:ViT-B-32:laion2b_s34b_b79k"
    assert result.modality == "image"
    assert result.vector == [0.1, 0.2, 0.3]


class _NoopContext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False
