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
