import pytest


def test_encoder_registry_resolves_default_mock_encoders():
    from app.encoders.mock import MockAudioEncoder, MockImageEncoder, MockTextEmbedder, MockTranscriber
    from app.encoders.registry import get_audio_encoder, get_image_encoder, get_text_embedder, get_transcriber

    assert isinstance(get_image_encoder("mock-image-encoder"), MockImageEncoder)
    assert isinstance(get_audio_encoder("mock-audio-encoder"), MockAudioEncoder)
    assert isinstance(get_transcriber("mock-transcriber"), MockTranscriber)
    assert isinstance(get_text_embedder("mock-text-embedder"), MockTextEmbedder)


def test_encoder_registry_rejects_unknown_names():
    from app.encoders.registry import get_text_embedder

    with pytest.raises(ValueError, match="Unknown text encoder"):
        get_text_embedder("not-a-real-encoder")
