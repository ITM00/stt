from app.utils.settings_store import UserSettings

from app.main import create_app
from app.utils.config import load_config
from app.utils.hotkey_format import as_pynput_global_hotkey


def test_create_app_returns_qapplication_and_orchestrator():
    class _FakeListener:
        def __init__(self, on_activate, hotkey: str) -> None:
            self.on_activate = on_activate
            self.hotkey = hotkey

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    def listener_factory(on_activate, hotkey: str):
        return _FakeListener(on_activate=on_activate, hotkey=hotkey)

    qt_app, orchestrator, hotkeys = create_app(hotkey_listener_factory=listener_factory)
    assert qt_app is not None
    assert orchestrator is not None
    assert hotkeys.listener is not None
    assert hotkeys.listener.hotkey == as_pynput_global_hotkey(load_config().hotkey)


def test_create_app_applies_loaded_user_settings(monkeypatch):
    class _FakeListener:
        def __init__(self, on_activate, hotkey: str) -> None:
            self.on_activate = on_activate
            self.hotkey = hotkey

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    def listener_factory(on_activate, hotkey: str):
        return _FakeListener(on_activate=on_activate, hotkey=hotkey)

    monkeypatch.setattr(
        "app.main.load_user_settings",
        lambda: UserSettings(silence_threshold_db=37.0, silence_timeout_seconds=1.25),
    )
    qt_app, orchestrator, _ = create_app(hotkey_listener_factory=listener_factory)
    assert qt_app is not None
    assert orchestrator.recorder.silence_threshold_db == 37.0
    assert orchestrator.recorder.silence_timeout_seconds == 1.25


def test_open_settings_save_failure_keeps_runtime_values(monkeypatch):
    class _FakeListener:
        def __init__(self, on_activate, hotkey: str) -> None:
            self.on_activate = on_activate
            self.hotkey = hotkey

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    class _AcceptedDialog:
        class DialogCode:
            Accepted = 1

        def __init__(self, *_args, **_kwargs) -> None:
            return None

        def adjustSize(self) -> None:
            return None

        def setWindowFlag(self, *_args, **_kwargs) -> None:
            return None

        def raise_(self) -> None:
            return None

        def activateWindow(self) -> None:
            return None

        def width(self) -> int:
            return 200

        def height(self) -> int:
            return 100

        def move(self, *_args, **_kwargs) -> None:
            return None

        def exec(self) -> int:
            return self.DialogCode.Accepted

        def values(self) -> UserSettings:
            return UserSettings(silence_threshold_db=99.0, silence_timeout_seconds=0.5)

    def listener_factory(on_activate, hotkey: str):
        return _FakeListener(on_activate=on_activate, hotkey=hotkey)

    monkeypatch.setattr(
        "app.main.load_user_settings",
        lambda: UserSettings(silence_threshold_db=37.0, silence_timeout_seconds=1.25),
    )
    monkeypatch.setattr("app.main.SettingsDialog", _AcceptedDialog)
    monkeypatch.setattr(
        "app.main.save_user_settings",
        lambda _settings: (_ for _ in ()).throw(OSError("cannot write settings")),
    )

    qt_app, orchestrator, _ = create_app(hotkey_listener_factory=listener_factory)
    qt_app._open_settings()  # type: ignore[attr-defined]
    assert orchestrator.recorder.silence_threshold_db == 37.0
    assert orchestrator.recorder.silence_timeout_seconds == 1.25
