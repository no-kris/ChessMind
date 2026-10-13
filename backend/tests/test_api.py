from fastapi.testclient import TestClient

from app.main import ORIGINS, app

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
