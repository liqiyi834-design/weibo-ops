from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

import app.api.routes as routes
from app.core.config import Settings
from app.llm.client import MockLLMClient
from app.main import app
from app.services.knowledge_service import KnowledgeService
from app.services.style_memory_service import StyleMemoryService
from app.schemas.comment import StyleMemoryExtractRequest, StyleMemoryIngestRequest
from mcp_server.tools import extract_style_memory_tool, ingest_style_memory_tool


def test_style_memory_extract_and_ingest_rebuilds_rag():
    workspace = Path(".rag_index") / f"style-memory-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )
    service = StyleMemoryService(settings, MockLLMClient())

    extracted = service.extract(
        StyleMemoryExtractRequest(
            creator_name="测试博主",
            platform="weibo",
            source_text="这事别急着站队，先把事实和情绪分开看。真正值得看的，是规则缝隙。",
            account_id="today_direct",
            style_name="rational_critic",
        )
    )
    ingested = service.ingest(StyleMemoryIngestRequest(observation=extracted.observation))
    retrieved = KnowledgeService(settings).search("风格记忆库 rational_critic 规则缝隙", top_k=3)

    assert Path(ingested.path).exists()
    assert ingested.rebuild_stats
    assert extracted.observation.reusable_rules
    assert any("风格记忆库" in item.content for item in retrieved)


def test_style_memory_api_auto_ingest(monkeypatch):
    workspace = Path(".rag_index") / f"style-memory-api-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )
    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    client = TestClient(app)

    response = client.post(
        "/api/style-memory/extract",
        json={
            "creator_name": "测试博主",
            "platform": "weibo",
            "source_text": "开头先抛判断，后面补事实，最后留一个讨论问题。",
            "account_id": "today_direct",
            "style_name": "rational_critic",
            "auto_ingest": True,
        },
    )
    cards_response = client.get("/api/style-memory/cards")

    assert response.status_code == 200
    assert response.json()["ingested"]["path"]
    assert cards_response.json()["cards"]


def test_style_memory_mcp_tools():
    workspace = Path(".rag_index") / f"style-memory-mcp-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )
    extracted = extract_style_memory_tool(
        source_text="短句开场，先给态度，再把事实边界补齐。",
        creator_name="测试博主",
        account_id="today_direct",
        style_name="rational_critic",
        auto_ingest=False,
        settings=settings,
        llm=MockLLMClient(),
    )
    ingested = ingest_style_memory_tool(extracted["observation"], settings=settings)

    assert extracted["observation"]["hook_patterns"]
    assert Path(ingested["path"]).exists()
