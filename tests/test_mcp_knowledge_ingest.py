from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.schemas.comment import ResearchSource, TopicResearchSourcesResponse
from mcp_server.tools import ingest_current_research_tool, ingest_knowledge_tool, ingest_research_sources_tool


def test_ingest_knowledge_tool_saves_and_retrieves_content():
    workspace = Path(".rag_index") / f"mcp-ingest-knowledge-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )

    result = ingest_knowledge_tool(
        topic="某热点事件",
        content="公开资料显示，事件争议集中在规则解释和沟通方式。",
        source_url="https://example.com/source",
        source_title="公开来源",
        credibility="medium",
        settings=settings,
    )
    saved_content = Path(result["path"]).read_text(encoding="utf-8")

    assert Path(result["path"]).exists()
    assert result["rebuild_stats"]["chunk_count"] >= 1
    assert "沟通方式" in saved_content
    assert "https://example.com/source" in saved_content


def test_ingest_research_sources_tool_uses_one_based_indices():
    workspace = Path(".rag_index") / f"mcp-ingest-sources-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )
    sources = [
        {
            "title": "来源一",
            "url": "https://example.com/one",
            "domain": "example.com",
            "summary": "第一条资料不应入库。",
            "credibility": "unknown",
        },
        {
            "title": "来源二",
            "url": "https://example.com/two",
            "domain": "example.com",
            "summary": "第二条资料包含可复用事实点。",
            "highlights": ["关键事实"],
            "credibility": "medium",
        },
    ]

    result = ingest_research_sources_tool(
        topic="某热点事件",
        sources=sources,
        selected_indices=[2],
        settings=settings,
    )
    saved_content = Path(result["ingested"][0]["path"]).read_text(encoding="utf-8")

    assert result["ingested_count"] == 1
    assert result["ingested"][0]["source_url"] == "https://example.com/two"
    assert "第二条资料包含可复用事实点" in saved_content
    assert "关键事实" in saved_content
    assert "第一条资料不应入库" not in saved_content


def test_ingest_research_sources_tool_rejects_out_of_range_index():
    settings = Settings(OPENAI_API_KEY=None)

    with pytest.raises(ValueError, match="out of range"):
        ingest_research_sources_tool(
            topic="某热点事件",
            sources=[{"title": "来源一", "url": "https://example.com"}],
            selected_indices=[2],
            settings=settings,
        )


def test_ingest_current_research_tool_uses_short_args(monkeypatch):
    workspace = Path(".rag_index") / f"mcp-current-research-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        EXA_API_KEY="test-exa",
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )

    class FakeExaResearchService:
        def __init__(self, settings):
            self.settings = settings

        def research_topic_sources(self, topic, limit=5, query=None):
            return TopicResearchSourcesResponse(
                topic=topic,
                query=query or f"{topic} query",
                sources=[
                    ResearchSource(
                        title="来源一",
                        url="https://example.com/one",
                        summary="第一条资料不应入库。",
                    ),
                    ResearchSource(
                        title="来源二",
                        url="https://example.com/two",
                        summary="第二条资料适合短参数入库。",
                        highlights=["短参数"],
                        credibility="medium",
                    ),
                ],
            )

    monkeypatch.setattr("mcp_server.tools.ExaResearchService", FakeExaResearchService)

    result = ingest_current_research_tool(
        topic="某热点事件",
        query="某热点事件 精确检索词",
        selected_indices=[2],
        settings=settings,
    )
    saved_content = Path(result["ingested"][0]["path"]).read_text(encoding="utf-8")

    assert result["ingested_count"] == 1
    assert result["query"] == "某热点事件 精确检索词"
    assert result["available_count"] == 2
    assert result["ingested"][0]["source_url"] == "https://example.com/two"
    assert "第二条资料适合短参数入库" in saved_content
    assert "第一条资料不应入库" not in saved_content
