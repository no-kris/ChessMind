import logging

import pytest
from fastapi.testclient import TestClient

from app.main import ORIGINS, app, configure_logging

client = TestClient(app)


def test_root_returns_health_message():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"message": "ChessMind API up and running."}


def test_analyze_returns_placeholder_message():
    res = client.get("/api/analyze")
    assert res.status_code == 200
    assert res.json() == {"message": "Frontend can talk to backend."}


def test_cors_allows_configured_origin():
    origin = ORIGINS[0]
    res = client.get("/", headers={"Origin": origin})
    assert res.headers["access-control-allow-origin"] == origin


def test_validation_error_returns_422_with_string_detail_naming_the_field():
    """FastAPI validation errors use the same string detail shape as every other error."""
    res = client.post("/api/games/any/moves", json={"fen": "8/8/8/8/8/8/8/8 w - - 0 1"})
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert isinstance(detail, str)
    assert "body.move: Field required" in detail


def test_validation_error_does_not_echo_submitted_values():
    """The 422 detail names bad fields but never repeats what the client sent."""
    res = client.post("/api/games/any/moves", json={"fen": "SECRET-LOOKING-VALUE", "move": 42})
    assert res.status_code == 422
    assert "SECRET-LOOKING-VALUE" not in res.json()["detail"]


def test_app_loggers_emit_info_after_startup():
    """Importing the app enables INFO logs for app.* loggers, so create/update/delete logs are not dropped."""
    assert logging.getLogger("app.services.game_store").isEnabledFor(logging.INFO)


def test_invalid_log_level_is_rejected_with_clear_message():
    """An unknown LOG_LEVEL fails fast and names the bad value."""
    with pytest.raises(ValueError, match="LOG_LEVEL='verbose'"):
        configure_logging("verbose")
