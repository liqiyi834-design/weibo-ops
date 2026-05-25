from fastapi.testclient import TestClient

from app.main import app
from app.schemas.comment import (
    GenerationContextRequest,
    ResearchSource,
    RetrievedKnowledge,
    RerankedTopic,
    TopicClassification,
)
from app.services.generation_context_service import GenerationContextService
from mcp_server.tools import build_generation_context_tool


def _request() -> GenerationContextRequest:
    return GenerationContextRequest(
        topic="test topic",
        research_sources=[
            ResearchSource(
                title="Official source",
                url="https://www.gov.cn/report",
                domain="www.gov.cn",
                summary="Officially verified background.",
                credibility="high",
            )
        ],
        rag_results=[
            RetrievedKnowledge(
                source="style_rules.md",
                content="先写事实边界，再给观点。",
                score=0.82,
            )
        ],
        reranked_topic=RerankedTopic(
            keyword="test topic",
            final_score=91,
            decision="select",
            recommended_angle="Use rule boundary angle.",
            risk_level="medium",
            reason="Good context but needs caution.",
            needed_context=["核验时间线"],
            risk_notes=["避免定性个人"],
            research_summary="Official source confirms key background.",
        ),
        classification=TopicClassification(
            category="social_issue",
            recommended_persona="rational_critic",
            max_emotion_level=6,
            risk_notes=["保持克制"],
        ),
    )


def test_generation_context_service_builds_stable_context():
    response = GenerationContextService().build(_request())

    assert response.topic == "test topic"
    assert "## 本轮临时背景" in response.context_text
    assert "Official source" in response.context_text
    assert "## RAG 编辑记忆" in response.context_text
    assert "style_rules.md" in response.context_text
    assert "## 选题判断" in response.context_text
    assert "Use rule boundary angle." in response.context_text
    assert "## 风险与生成约束" in response.context_text
    assert "核验时间线" in response.needs_verification
    assert response.source_urls == ["https://www.gov.cn/report"]


def test_generation_context_service_handles_missing_inputs():
    response = GenerationContextService().build(GenerationContextRequest(topic="test topic"))

    assert "不要编造具体事实" in response.context_text
    assert "暂无本地 RAG 结果" in response.context_text
    assert response.needs_verification == ["补充公开背景来源"]
    assert response.notes


def test_generation_context_api():
    client = TestClient(app)
    response = client.post("/api/comment/context", json=_request().model_dump())

    assert response.status_code == 200
    assert "context_text" in response.json()
    assert "Officially verified background." in response.json()["context_text"]


def test_mcp_build_generation_context_tool():
    response = build_generation_context_tool(
        topic="test topic",
        research_sources=[_request().research_sources[0].model_dump()],
        rag_results=[_request().rag_results[0].model_dump()],
        reranked_topic=_request().reranked_topic.model_dump(),
        classification=_request().classification.model_dump(),
    )

    assert response["topic"] == "test topic"
    assert "## 本轮临时背景" in response["context_text"]
    assert response["source_urls"]


def test_mcp_build_generation_context_accepts_source_without_url():
    response = build_generation_context_tool(
        topic="test topic",
        research_sources=[
            {
                "title": "Weibo AiSearch summary",
                "domain": "weibo_aisearch",
                "summary": "Structured background summary from Weibo AiSearch.",
                "credibility": "medium",
            }
        ],
    )

    assert response["topic"] == "test topic"
    assert "Weibo AiSearch summary" in response["context_text"]
    assert response["source_urls"] == []
