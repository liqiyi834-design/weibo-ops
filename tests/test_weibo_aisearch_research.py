from pathlib import Path

import httpx
from fastapi.testclient import TestClient

import app.api.routes as routes
from app.core.config import Settings
from app.main import app
from app.services.weibo_aisearch_research_service import (
    WeiboAiSearchResearchService,
    build_weibo_aisearch_url,
    normalize_weibo_topic,
)
from mcp_server.tools import research_weibo_aisearch_tool


def test_weibo_aisearch_topic_url_encoding():
    topic = normalize_weibo_topic("看不到女干部救灾累哑却盯着金耳环")

    assert topic == "#看不到女干部救灾累哑却盯着金耳环#"
    assert build_weibo_aisearch_url(topic).startswith("https://s.weibo.com/aisearch?q=%23")
    assert "Refer=weibo_aisearch" in build_weibo_aisearch_url(topic)


def test_weibo_aisearch_service_polls_until_completed():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        form = request.read().decode("utf-8")
        calls.append(form)
        if "loop_num=1" in form:
            return httpx.Response(200, json={"data": {"status": 1, "stage": 0}})
        return httpx.Response(
            200,
            json={
                "data": {
                    "status": 2,
                    "msg": (
                        "<think>internal reasoning</think>\n"
                        "## 原因\n"
                        "1. 国际油价回落。wbCustomBlock{\"type\":\"quoted\",\"data\":{\"name\":\"source\"}}\n\n"
                        "[央视财经](https://example.com/news)"
                    ),
                    "link_list": [{"url": "https://weibo.com/123"}],
                }
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = Settings(
        OPENAI_API_KEY=None,
        WEIBO_COOKIE="SUB=fake",
        KNOWLEDGE_DIR=Path("app/knowledge"),
    )

    response = WeiboAiSearchResearchService(settings, client=client).research_topic_sources(
        "油价大跌了",
        max_polls=2,
        poll_interval_seconds=0,
    )

    assert len(calls) == 2
    assert response.source == "weibo_aisearch"
    assert response.query == "#油价大跌了#"
    assert response.sources[0].title == "微博智搜：#油价大跌了#"
    assert response.sources[0].domain == "s.weibo.com"
    assert "国际油价回落" in response.sources[0].summary
    assert "internal reasoning" not in response.sources[0].summary
    assert "wbCustomBlock" not in response.sources[0].summary
    assert any("https://weibo.com/123" in item for item in response.sources[0].highlights)


def test_weibo_aisearch_api(monkeypatch):
    class FakeService:
        def __init__(self, settings):
            self.settings = settings

        def research_topic_sources(self, topic, max_polls=6, poll_interval_seconds=1.5):
            from app.schemas.comment import TopicResearchSourcesResponse

            return TopicResearchSourcesResponse(
                topic=topic,
                query=f"#{topic}#",
                source="weibo_aisearch",
                notes=["fake"],
            )

    monkeypatch.setattr(routes, "get_settings", lambda: Settings(OPENAI_API_KEY=None, WEIBO_COOKIE="x"))
    monkeypatch.setattr(routes, "WeiboAiSearchResearchService", FakeService)
    client = TestClient(app)

    response = client.post("/api/research/weibo-aisearch", json={"topic": "test topic", "max_polls": 1})

    assert response.status_code == 200
    assert response.json()["source"] == "weibo_aisearch"
    assert response.json()["topic"] == "test topic"


def test_mcp_research_weibo_aisearch_tool(monkeypatch):
    class FakeService:
        def __init__(self, settings):
            self.settings = settings

        def research_topic_sources(self, topic, max_polls=6, poll_interval_seconds=1.5):
            from app.schemas.comment import TopicResearchSourcesResponse

            return TopicResearchSourcesResponse(
                topic=topic,
                query=f"#{topic}#",
                source="weibo_aisearch",
                notes=["fake"],
            )

    monkeypatch.setattr("mcp_server.tools.WeiboAiSearchResearchService", FakeService)
    settings = Settings(OPENAI_API_KEY=None, WEIBO_COOKIE="x")

    result = research_weibo_aisearch_tool("test topic", max_polls=1, settings=settings)

    assert result["topic"] == "test topic"
    assert result["source"] == "weibo_aisearch"
