from app.utils.config import AppConfig, load_config


def test_load_config_returns_defaults():
    cfg = load_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.hotkey == "<ctrl>+<shift>+space"
    assert cfg.model_name == "small"
    assert cfg.template_path == "app/templates/punctuation_signs_en.json"


def test_template_path_switches_for_russian_language():
    cfg = AppConfig(language="ru")
    assert cfg.template_path == "app/templates/punctuation_signs_ru.json"
