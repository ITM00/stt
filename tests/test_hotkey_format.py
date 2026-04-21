from app.utils.hotkey_format import as_pynput_global_hotkey


def test_wraps_space_for_pynput() -> None:
    assert as_pynput_global_hotkey("<ctrl>+<shift>+space") == "<ctrl>+<shift>+<space>"


def test_normalizes_modifier_aliases() -> None:
    assert as_pynput_global_hotkey("ctrl+shift+a") == "<ctrl>+<shift>+a"
