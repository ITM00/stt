from app.main import create_app


def test_create_app_returns_qapplication_and_orchestrator():
    qt_app, orchestrator = create_app()
    assert qt_app is not None
    assert orchestrator is not None
