from pathlib import Path


def test_mock_image_encoder_returns_deterministic_embedding(tmp_path: Path):
    from app.encoders.mock import MockImageEncoder

    image_path = tmp_path / "frame.jpg"
    image_path.write_bytes(b"frame")

    encoder = MockImageEncoder(dimension=8)
    first = encoder.encode(image_path)
    second = encoder.encode(image_path)

    assert first.encoder_name == "mock-image-encoder"
    assert first.modality == "image"
    assert first.dimension == 8
    assert first.vector == second.vector
    assert len(first.vector) == 8


def test_mock_audio_encoder_returns_deterministic_embedding(tmp_path: Path):
    from app.encoders.mock import MockAudioEncoder

    audio_path = tmp_path / "segment.wav"
    audio_path.write_bytes(b"audio")

    encoder = MockAudioEncoder(dimension=6)
    result = encoder.encode(audio_path)

    assert result.encoder_name == "mock-audio-encoder"
    assert result.modality == "audio"
    assert result.dimension == 6
    assert len(result.vector) == 6
    assert result.vector == encoder.encode(audio_path).vector
