from pathlib import Path

import httpx
from fastapi.testclient import TestClient

import app.api.routes as routes
from app.core.config import Settings
from app.main import app
from app.services.exa_research_service import ExaResearchService
from mcp_server.tools import research_topic_sources_tool


def test_exa_research_service_returns_unconfigured_note():
    settings = Settings(OPENAI_API_KEY=None, EXA_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))

    response = ExaResearchService(settings).research_topic_sources("test topic")

    assert response.is_configured is False
    assert response.sources == []
    assert response.notes


def test_exa_research_service_maps_results():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-exa-key"
        payload = request.read().decode("utf-8")
        assert "test topic" in payload
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Official report",
                        "url": "https://www.gov.cn/example",
                        "publishedDate": "2026-05-24T00:00:00Z",
                        "author": "Official",
                        "summary": "A concise official summary.",
                        "highlights": ["Important fact one.", "Important fact two."],
                        "score": 0.91,
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY=None, EXA_API_KEY="test-exa-key", KNOWLEDGE_DIR=Path("app/knowledge"))

    response = ExaResearchService(settings, client=client).research_topic_sources("test topic", limit=1)

    assert response.is_configured is True
    assert response.sources[0].title == "Official report"
    assert response.sources[0].domain == "www.gov.cn"
    assert response.sources[0].credibility == "high"
    assert response.sources[0].ingest_recommendation == "can_ingest_after_review"


def test_exa_research_api(monkeypatch):
    class FakeService:
        def __init__(self, settings):
            self.settings = settings

        def research_topic_sources(self, topic, limit=5, include_domains=None, exclude_domains=None):
            return {
                "topic": topic,
                "query": f"{topic} query",
                "source": "exa",
                "sources": [],
                "notes": ["fake"],
                "is_configured": True,
            }

    monkeypatch.setattr(routes, "get_settings", lambda: Settings(OPENAI_API_KEY=None, EXA_API_KEY="x"))
    monkeypatch.setattr(routes, "ExaResearchService", FakeService)
    client = TestClient(app)

    response = client.post("/api/research/exa", json={"topic": "test topic", "limit": 3})

    assert response.status_code == 200
    assert response.json()["topic"] == "test topic"


def test_mcp_research_topic_sources_tool(monkeypatch):
    class FakeService:
        def __init__(self, settings):
            self.settings = settings

        def research_topic_sources(self, topic, limit=5, include_domains=None, exclude_domains=None):
            from app.schemas.comment import TopicResearchSourcesResponse

            return TopicResearchSourcesResponse(topic=topic, query="fake query", notes=["fake"])

    monkeypatch.setattr("mcp_server.tools.ExaResearchService", FakeService)
    settings = Settings(OPENAI_API_KEY=None, EXA_API_KEY="x")

    result = research_topic_sources_tool("test topic", settings=settings)

    assert result["topic"] == "test topic"
    assert result["source"] == "exa"
