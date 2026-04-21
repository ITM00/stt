from app.core.text_postprocessor import TextPostProcessor


def test_applies_templates_in_order(tmp_path):
    templates = tmp_path / "templates.json"
    templates.write_text(
        '[{"pattern":"\\\\s+","replacement":" "},{"pattern":"teh","replacement":"the"}]',
        encoding="utf-8",
    )
    processor = TextPostProcessor(str(templates))
    assert processor.process("teh   quick") == "the quick"


def test_backslash_replacement_does_not_use_replacement_templates(tmp_path):
    templates = tmp_path / "templates.json"
    templates.write_text(
        '[{"pattern":"backslash","replacement":"\\\\"}]',
        encoding="utf-8",
    )
    processor = TextPostProcessor(str(templates))
    assert processor.process("path backslash here") == "path \\ here"
