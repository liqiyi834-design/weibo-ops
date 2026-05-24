from pathlib import Path

from fastapi.testclient import TestClient

import app.api.routes as routes
from app.core.config import Settings
from app.llm.client import BaseLLMClient, MockLLMClient
from app.main import app
from app.schemas.comment import ResearchSource, TopicRerankCandidate
from app.services.topic_rerank_service import TopicRerankService
from mcp_server.tools import rerank_topics_with_research_tool


class RankingLLM(BaseLLMClient):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "ranked": [
                {
                    "keyword": "topic b",
                    "final_score": 92,
                    "decision": "select",
                    "recommended_angle": "Use verified context.",
                    "reason": "Better sources and clearer comment space.",
                    "needed_context": [],
                    "risk_notes": [],
                },
                {
                    "keyword": "topic a",
                    "final_score": 55,
                    "decision": "backup",
                    "recommended_angle": "Wait for more facts.",
                    "reason": "Weak context.",
                    "needed_context": ["more sources"],
                    "risk_notes": ["avoid overclaiming"],
                },
            ]
        }


def _source(domain: str = "www.gov.cn", credibility: str = "high") -> ResearchSource:
    return ResearchSource(
        title="source title",
        url=f"https://{domain}/report",
        domain=domain,
        summary="verified public context",
        credibility=credibility,
    )


def test_topic_rerank_uses_rules_without_llm():
    candidates = [
        TopicRerankCandidate(keyword="topic without sources", original_score=90, research_sources=[]),
        TopicRerankCandidate(keyword="topic with sources", original_score=70, research_sources=[_source()]),
    ]

    response = TopicRerankService().rerank(candidates, max_results=1)

    assert response.llm_used is False
    assert response.selected[0].keyword == "topic with sources"
    assert response.selected[0].source_urls
    assert response.rejected


def test_topic_rerank_uses_llm_when_available():
    candidates = [
        TopicRerankCandidate(keyword="topic a", original_score=90),
        TopicRerankCandidate(keyword="topic b", original_score=60, research_sources=[_source()]),
    ]

    response = TopicRerankService(RankingLLM()).rerank(candidates, max_results=1)

    assert response.llm_used is True
    assert response.selected[0].keyword == "topic b"
    assert response.selected[0].final_score == 92
    assert response.selected[0].reason == "Better sources and clearer comment space."


def test_topic_rerank_api(monkeypatch):
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    client = TestClient(app)

    response = client.post(
        "/api/topics/rerank",
        json={
            "max_results": 1,
            "candidates": [
                {
                    "keyword": "test topic",
                    "original_score": 80,
                    "research_sources": [_source().model_dump()],
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["selected"]


def test_mcp_rerank_topics_with_research_tool():
    result = rerank_topics_with_research_tool(
        candidates=[
            {
                "keyword": "test topic",
                "original_score": 80,
                "research_sources": [_source().model_dump()],
            }
        ],
        llm=MockLLMClient(),
    )

    assert result["selected"]
    assert "final_score" in result["selected"][0]
