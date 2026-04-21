from app.core.hotkey_manager import HotkeyManager


class _FakeListener:
    def __init__(self, on_activate, hotkey: str) -> None:
        self.on_activate = on_activate
        self.hotkey = hotkey
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def test_hotkey_manager_registers_and_starts_listener() -> None:
    activations: list[str] = []

    def listener_factory(on_activate, hotkey: str):
        return _FakeListener(on_activate=on_activate, hotkey=hotkey)

    manager = HotkeyManager(listener_factory=listener_factory)
    manager.register("ctrl+shift+space", lambda: activations.append("fired"))

    assert manager.listener is not None
    assert manager.listener.started is True
    assert manager.listener.hotkey == "ctrl+shift+space"

    manager.listener.on_activate()
    assert activations == ["fired"]


def test_hotkey_manager_stop_stops_listener() -> None:
    manager = HotkeyManager(listener_factory=lambda on_activate, hotkey: _FakeListener(on_activate, hotkey))
    manager.register("ctrl+shift+space", lambda: None)

    manager.stop()

    assert manager.listener is not None
    assert manager.listener.stopped is True
