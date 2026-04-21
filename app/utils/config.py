from dataclasses import dataclass


@dataclass(slots=True)
class AppConfig:
    hotkey: str = "<ctrl>+<shift>+space"
    model_name: str = "small"
    language: str = "en"
    sample_rate: int = 16000
    template_path: str = "app/templates/default_templates.json"


def load_config() -> AppConfig:
    return AppConfig()
