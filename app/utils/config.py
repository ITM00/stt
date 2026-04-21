from dataclasses import dataclass


@dataclass(slots=True)
class AppConfig:
    hotkey: str = "<ctrl>+<shift>+space"
    model_name: str = "small"
    language: str = "en"
    sample_rate: int = 16000
    template_path_en: str = "app/templates/punctuation_signs_en.json"
    template_path_ru: str = "app/templates/punctuation_signs_ru.json"

    @property
    def template_path(self) -> str:
        if self.language.lower() == "ru":
            return self.template_path_ru
        return self.template_path_en


def load_config() -> AppConfig:
    return AppConfig()
