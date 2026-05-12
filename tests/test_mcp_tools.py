from pathlib import Path

from app.core.config import Settings
from app.llm.client import MockLLMClient
from mcp_server.tools import (
    generate_comment_tool,
    get_hot_topics_tool,
    rebuild_knowledge_tool,
    search_knowledge_tool,
)


def test_mcp_generate_comment_tool_uses_pipeline():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    result = generate_comment_tool(
        topic="某品牌文案翻车",
        context_text="品牌文案被质疑表达不当。",
        persona="pr_critic",
        settings=settings,
        llm=MockLLMClient(),
    )

    assert result["topic"] == "某品牌文案翻车"
    assert result["output"]["short_comment"]
    assert result["safety"]["is_safe"] is True


def test_mcp_knowledge_tools():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    rebuild_result = rebuild_knowledge_tool(settings=settings)
    search_result = search_knowledge_tool("品牌文案翻车", settings=settings)

    assert rebuild_result["success"] is True
    assert rebuild_result["chunk_count"] > 0
    assert search_result
    assert "source" in search_result[0]


def test_mcp_get_hot_topics_tool():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    result = get_hot_topics_tool(limit=3, settings=settings)

    assert result["items"]
    assert len(result["items"]) <= 3
    assert "keyword" in result["items"][0]
