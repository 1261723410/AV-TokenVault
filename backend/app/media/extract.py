import shutil
import subprocess
from pathlib import Path

from app.media.probe import MediaProcessingError


def build_extract_frames_command(
    *,
    input_path: Path,
    output_pattern: Path,
    frame_interval: float,
    max_frames: int,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        f"fps=1/{frame_interval}",
        "-frames:v",
        str(max_frames),
        str(output_pattern),
    ]


def build_extract_audio_command(input_path: Path, output_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_path),
    ]


def build_segment_audio_command(
    *,
    input_path: Path,
    output_pattern: Path,
    segment_seconds: float,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-c",
        "copy",
        str(output_pattern),
    ]


def run_ffmpeg(command: list[str]) -> None:
    if shutil.which("ffmpeg") is None:
        raise MediaProcessingError("ffmpeg is not installed. Install FFmpeg first.")

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaProcessingError(completed.stderr.strip() or "ffmpeg command failed")


def extract_frames(input_path: Path, output_dir: Path, frame_interval: float, max_frames: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / "frame_%06d.jpg"
    run_ffmpeg(
        build_extract_frames_command(
            input_path=input_path,
            output_pattern=output_pattern,
            frame_interval=frame_interval,
            max_frames=max_frames,
        )
    )
    return sorted(output_dir.glob("frame_*.jpg"))


def extract_audio(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(build_extract_audio_command(input_path, output_path))
    return output_path


def segment_audio(input_path: Path, output_dir: Path, segment_seconds: float) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / "segment_%06d.wav"
    run_ffmpeg(
        build_segment_audio_command(
            input_path=input_path,
            output_pattern=output_pattern,
            segment_seconds=segment_seconds,
        )
    )
    return sorted(output_dir.glob("segment_*.wav"))
