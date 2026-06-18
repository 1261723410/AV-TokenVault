import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class MediaProcessingError(RuntimeError):
    pass


@dataclass(frozen=True)
class MediaProbe:
    duration_seconds: float | None
    width: int | None
    height: int | None
    has_video: bool
    has_audio: bool


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def probe_media(path: Path) -> MediaProbe:
    if shutil.which("ffprobe") is None:
        raise MediaProcessingError("ffprobe is not installed. Install FFmpeg first.")

    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaProcessingError(completed.stderr.strip() or "ffprobe failed")

    payload = json.loads(completed.stdout)
    streams = payload.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    duration = payload.get("format", {}).get("duration")

    return MediaProbe(
        duration_seconds=float(duration) if duration is not None else None,
        width=int(video_stream["width"]) if video_stream and video_stream.get("width") else None,
        height=int(video_stream["height"]) if video_stream and video_stream.get("height") else None,
        has_video=video_stream is not None,
        has_audio=audio_stream is not None,
    )
