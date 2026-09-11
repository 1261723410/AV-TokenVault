from pathlib import Path


class FakeWhisperSegment:
    def __init__(self, start: float, end: float, text: str) -> None:
        self.start = start
        self.end = end
        self.text = text


class FakeWhisperInfo:
    language = "zh"


class FakeWhisperModel:
    def transcribe(self, path: str, beam_size: int = 5):
        return [FakeWhisperSegment(0.25, 1.5, " 真实转写文本 ")], FakeWhisperInfo()


def test_faster_whisper_transcriber_offsets_segment_timestamps(tmp_path: Path):
    from app.encoders.whisper import FasterWhisperTranscriber

    audio_path = tmp_path / "segment.wav"
    audio_path.write_bytes(b"audio")
    transcriber = FasterWhisperTranscriber(model_size="tiny", model_factory=lambda *args, **kwargs: FakeWhisperModel())

    result = transcriber.transcribe_segment(audio_path, start_seconds=10.0, end_seconds=15.0)

    assert result.text == "真实转写文本"
    assert result.start_seconds == 10.25
    assert result.end_seconds == 11.5
    assert result.language == "zh"
    assert result.source == "faster-whisper-tiny"


def test_faster_whisper_transcriber_falls_back_to_input_bounds_for_empty_output(tmp_path: Path):
    from app.encoders.whisper import FasterWhisperTranscriber

    class EmptyModel:
        def transcribe(self, path: str, beam_size: int = 5):
            return [], FakeWhisperInfo()

    audio_path = tmp_path / "segment.wav"
    audio_path.write_bytes(b"audio")
    transcriber = FasterWhisperTranscriber(model_size="tiny", model_factory=lambda *args, **kwargs: EmptyModel())

    result = transcriber.transcribe_segment(audio_path, start_seconds=10.0, end_seconds=15.0)

    assert result.text == ""
    assert result.start_seconds == 10.0
    assert result.end_seconds == 15.0
