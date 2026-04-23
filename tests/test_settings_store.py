from app.utils.settings_store import (
    UserSettings,
    apply_user_settings,
    load_user_settings,
    save_user_settings,
)


def test_load_defaults_when_file_missing(tmp_path) -> None:
    settings = load_user_settings(path=tmp_path / "missing.json")
    assert settings == UserSettings()


def test_save_and_load_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    expected = UserSettings(silence_threshold_db=42.5, silence_timeout_seconds=2.25)
    save_user_settings(expected, path=path)
    loaded = load_user_settings(path=path)
    assert loaded == expected


def test_load_invalid_file_falls_back_to_defaults(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{invalid-json", encoding="utf-8")
    loaded = load_user_settings(path=path)
    assert loaded == UserSettings()


def test_load_clamps_out_of_range_values(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        '{"silence_threshold_db": 9999, "silence_timeout_seconds": -100}',
        encoding="utf-8",
    )
    loaded = load_user_settings(path=path)
    assert loaded.silence_threshold_db == 100.0
    assert loaded.silence_timeout_seconds == 0.1


def test_apply_user_settings_updates_recorder_fields() -> None:
    class _Recorder:
        silence_threshold_db = 30.0
        silence_timeout_seconds = 3.0

    recorder = _Recorder()
    apply_user_settings(
        recorder, UserSettings(silence_threshold_db=50.0, silence_timeout_seconds=1.5)
    )
    assert recorder.silence_threshold_db == 50.0
    assert recorder.silence_timeout_seconds == 1.5
