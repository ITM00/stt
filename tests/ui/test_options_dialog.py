from pathlib import Path

from app.ui.options_dialog import resolve_output_txt_path


def test_resolve_output_txt_path_keeps_explicit_file_name(tmp_path: Path) -> None:
    audio_path = tmp_path / "meeting.wav"
    output = resolve_output_txt_path(tmp_path / "custom_name.txt", audio_path)
    assert output == tmp_path / "custom_name.txt"


def test_resolve_output_txt_path_uses_audio_stem_for_existing_directory(tmp_path: Path) -> None:
    audio_path = tmp_path / "call.mp3"
    output = resolve_output_txt_path(tmp_path, audio_path)
    assert output == tmp_path / "call.txt"


def test_resolve_output_txt_path_uses_audio_stem_for_directory_with_separator(tmp_path: Path) -> None:
    audio_path = tmp_path / "voice.m4a"
    output = resolve_output_txt_path(f"{tmp_path}\\", audio_path)
    assert output == tmp_path / "voice.txt"


def test_resolve_output_txt_path_treats_missing_suffix_path_as_directory(tmp_path: Path) -> None:
    audio_path = tmp_path / "lecture.flac"
    output = resolve_output_txt_path(tmp_path / "new-output-dir", audio_path)
    assert output == tmp_path / "new-output-dir" / "lecture.txt"
