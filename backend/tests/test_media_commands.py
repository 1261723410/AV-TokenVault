from pathlib import Path


def test_build_extract_frames_command_uses_interval_and_max_frames(tmp_path: Path):
    from app.media.extract import build_extract_frames_command

    command = build_extract_frames_command(
        input_path=tmp_path / "demo.mp4",
        output_pattern=tmp_path / "frames" / "frame_%06d.jpg",
        frame_interval=2.0,
        max_frames=120,
    )

    assert command[:2] == ["ffmpeg", "-y"]
    assert "-i" in command
    assert "fps=1/2.0" in command
    assert "-frames:v" in command
    assert "120" in command


def test_build_extract_frames_command_spreads_long_video_across_max_frames(tmp_path: Path):
    from app.media.extract import build_extract_frames_command

    command = build_extract_frames_command(
        input_path=tmp_path / "meeting.mp4",
        output_pattern=tmp_path / "frames" / "frame_%06d.jpg",
        frame_interval=1.0,
        max_frames=600,
        duration_seconds=2400.0,
    )

    assert "fps=1/4.0" in command
    assert "-frames:v" in command
    assert "600" in command


def test_build_extract_frames_command_keeps_requested_interval_when_under_limit(tmp_path: Path):
    from app.media.extract import build_extract_frames_command

    command = build_extract_frames_command(
        input_path=tmp_path / "clip.mp4",
        output_pattern=tmp_path / "frames" / "frame_%06d.jpg",
        frame_interval=2.0,
        max_frames=600,
        duration_seconds=60.0,
    )

    assert "fps=1/2.0" in command


def test_build_extract_audio_command_outputs_wav(tmp_path: Path):
    from app.media.extract import build_extract_audio_command

    output_path = tmp_path / "audio.wav"
    command = build_extract_audio_command(tmp_path / "demo.mp4", output_path)

    assert command[:2] == ["ffmpeg", "-y"]
    assert "-vn" in command
    assert "-acodec" in command
    assert "pcm_s16le" in command
    assert str(output_path) == command[-1]


def test_build_segment_audio_command_uses_segment_duration(tmp_path: Path):
    from app.media.extract import build_segment_audio_command

    command = build_segment_audio_command(
        input_path=tmp_path / "audio.wav",
        output_pattern=tmp_path / "segments" / "segment_%06d.wav",
        segment_seconds=5.0,
    )

    assert command[:2] == ["ffmpeg", "-y"]
    assert "-f" in command
    assert "segment" in command
    assert "-segment_time" in command
    assert "5.0" in command
