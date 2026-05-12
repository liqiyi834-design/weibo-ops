from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_weibo_hot_topics():
    client = TestClient(app)
    response = client.get("/api/hot/weibo?limit=5")
    body = response.json()

    assert response.status_code == 200
    assert body["items"]
    assert len(body["items"]) <= 5
    assert "keyword" in body["items"][0]


def test_knowledge_rebuild():
    client = TestClient(app)
    response = client.post("/api/knowledge/rebuild")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["chunk_count"] > 0


def test_knowledge_search():
    client = TestClient(app)
    client.post("/api/knowledge/rebuild")
    response = client.post("/api/knowledge/search", json={"query": "品牌文案翻车", "top_k": 3})

    assert response.status_code == 200
    assert response.json()
