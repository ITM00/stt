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


def test_patterns_are_applied_case_insensitively(tmp_path):
    templates = tmp_path / "templates.json"
    templates.write_text(
        '[{"pattern":"teh","replacement":"the"}]',
        encoding="utf-8",
    )
    processor = TextPostProcessor(str(templates))
    assert processor.process("TEH quick") == "the quick"


def test_spoken_new_line_becomes_actual_line_break(tmp_path):
    templates = tmp_path / "templates.json"
    templates.write_text("[]", encoding="utf-8")
    processor = TextPostProcessor(str(templates))
    assert processor.process("hello new line world") == "hello\nworld"


def test_spoken_newline_becomes_actual_line_break(tmp_path):
    templates = tmp_path / "templates.json"
    templates.write_text("[]", encoding="utf-8")
    processor = TextPostProcessor(str(templates))
    assert processor.process("hello newline world") == "hello\nworld"


def test_dev_dialect_matches_any_separator_and_joins_with_backslashes(tmp_path):
    templates = tmp_path / "templates.json"
    templates.write_text(
        '[{"pattern":"\\\\b(file|function|class|path)\\\\b(.*?)\\\\bstop\\\\b","handler":"dev_dialect"}]',
        encoding="utf-8",
    )
    processor = TextPostProcessor(str(templates))
    assert (
        processor.process("What files are under the path, app, core, stop?")
        == "What files are under the path app\\core?"
    )


def test_dev_dialect_drops_stop_and_keeps_keyword_separate(tmp_path):
    templates = tmp_path / "templates.json"
    templates.write_text(
        '[{"pattern":"\\\\b(file|function|class|path)\\\\b(.*?)\\\\bstop\\\\b","handler":"dev_dialect"}]',
        encoding="utf-8",
    )
    processor = TextPostProcessor(str(templates))
    assert processor.process("Use class---My,Great-Class!!! stop now") == "Use class My\\Great\\Class now"


def test_dev_dialect_is_always_applied_after_primary_templates(tmp_path):
    templates = tmp_path / "templates.json"
    templates.write_text(
        '[{"pattern":"\\\\bdot\\\\b","replacement":"."}]',
        encoding="utf-8",
    )
    processor = TextPostProcessor(str(templates))
    assert (
        processor.process("Another test for path dot app dot score dot stop.")
        == "Another test for path app\\score."
    )
