from pathlib import Path


def test_msclap_audio_encoder_returns_embedding(tmp_path: Path):
    from app.encoders.clap import MSCLAPAudioEncoder

    class FakeCLAP:
        def get_audio_embeddings(self, paths):
            assert len(paths) == 1
            return [[0.1, 0.2, 0.3]]

    audio_path = tmp_path / "segment.wav"
    audio_path.write_bytes(b"audio")
    encoder = MSCLAPAudioEncoder(version="2023", model_factory=lambda **kwargs: FakeCLAP())

    result = encoder.encode(audio_path)

    assert result.encoder_name == "msclap:2023"
    assert result.modality == "audio"
    assert result.vector == [0.1, 0.2, 0.3]
