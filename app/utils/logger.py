import logging
from pathlib import Path

_IS_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    global _IS_CONFIGURED
    if not _IS_CONFIGURED:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "stt-desktop.log"

        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)
        _IS_CONFIGURED = True

    return logging.getLogger(name)
