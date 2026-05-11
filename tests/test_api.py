from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_knowledge_rebuild():
    client = TestClient(app)
    response = client.post("/api/knowledge/rebuild")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["chunk_count"] > 0
