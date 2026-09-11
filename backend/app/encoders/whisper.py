from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.encoders.base import TranscriptChunkResult


class FasterWhisperTranscriber:
    def __init__(
        self,
        *,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.transcriber_name = f"faster-whisper-{model_size}"
        self._model_factory = model_factory
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if self._model_factory is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "faster-whisper is not installed. Install optional model dependencies first."
                ) from exc

            self._model_factory = WhisperModel

        self._model = self._model_factory(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        return self._model

    def transcribe_segment(self, path: Path, *, start_seconds: float, end_seconds: float) -> TranscriptChunkResult:
        model = self._load_model()
        segments, info = model.transcribe(str(path), beam_size=5)
        segment_list = list(segments)
        text = " ".join(segment.text.strip() for segment in segment_list if segment.text.strip()).strip()
        language = getattr(info, "language", None)

        if not segment_list:
            return TranscriptChunkResult(
                text=text,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                language=language,
                source=self.transcriber_name,
            )

        first_start = min(segment.start for segment in segment_list)
        last_end = max(segment.end for segment in segment_list)
        return TranscriptChunkResult(
            text=text,
            start_seconds=start_seconds + first_start,
            end_seconds=start_seconds + last_end,
            language=language,
            source=self.transcriber_name,
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Transcribe one audio file with faster-whisper.")
    parser.add_argument("audio_path")
    parser.add_argument("--model-size", default="base")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    args = parser.parse_args()

    result = FasterWhisperTranscriber(
        model_size=args.model_size,
        device=args.device,
        compute_type=args.compute_type,
    ).transcribe_segment(Path(args.audio_path), start_seconds=0.0, end_seconds=0.0)
    print(result.text)


if __name__ == "__main__":
    main()
