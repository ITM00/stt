from app.utils.logger import get_logger


def test_get_logger_returns_named_logger():
    logger = get_logger("stt")
    assert logger.name == "stt"
