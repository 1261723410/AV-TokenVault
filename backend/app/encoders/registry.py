from app.encoders.base import AudioEncoder, ImageEncoder, TextEmbeddingEncoder, Transcriber
from app.encoders.mock import MockAudioEncoder, MockImageEncoder, MockTextEmbedder, MockTranscriber


def get_image_encoder(name: str) -> ImageEncoder:
    if name == MockImageEncoder.encoder_name:
        return MockImageEncoder()
    if name.startswith("open-clip:"):
        from app.encoders.clip import OpenCLIPImageEncoder

        _, model_name, pretrained = name.split(":", maxsplit=2)
        return OpenCLIPImageEncoder(model_name=model_name, pretrained=pretrained)
    raise ValueError(f"Unknown image encoder: {name}")


def get_audio_encoder(name: str) -> AudioEncoder:
    if name == MockAudioEncoder.encoder_name:
        return MockAudioEncoder()
    if name.startswith("msclap:"):
        from app.encoders.clap import MSCLAPAudioEncoder

        return MSCLAPAudioEncoder(version=name.removeprefix("msclap:"))
    raise ValueError(f"Unknown audio encoder: {name}")


def get_text_embedder(name: str) -> TextEmbeddingEncoder:
    if name == MockTextEmbedder.encoder_name:
        return MockTextEmbedder()
    if name.startswith("sentence-transformers:"):
        from app.encoders.text_embedding import SentenceTransformerTextEmbedder

        return SentenceTransformerTextEmbedder(model_name=name.removeprefix("sentence-transformers:"))
    raise ValueError(f"Unknown text encoder: {name}")


def get_transcriber(name: str) -> Transcriber:
    if name == MockTranscriber.transcriber_name:
        return MockTranscriber()
    if name.startswith("faster-whisper-"):
        from app.encoders.whisper import FasterWhisperTranscriber

        return FasterWhisperTranscriber(model_size=name.removeprefix("faster-whisper-"))
    raise ValueError(f"Unknown transcriber: {name}")
