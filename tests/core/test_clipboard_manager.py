from app.core.clipboard_manager import ClipboardManager


def test_copy_text_uses_injected_copy_callable() -> None:
    copied_values: list[str] = []
    manager = ClipboardManager(copy_fn=copied_values.append)

    manager.copy_text("hello")

    assert copied_values == ["hello"]
