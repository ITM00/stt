from app.utils.config import AppConfig, load_config


def test_load_config_returns_defaults():
    cfg = load_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.hotkey == "<ctrl>+<shift>+space"
    assert cfg.model_name == "small"
