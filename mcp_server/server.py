from __future__ import annotations

from fastmcp import FastMCP

from mcp_server.tools import (
    generate_comment_tool,
    get_hot_topics_tool,
    rebuild_knowledge_tool,
    search_knowledge_tool,
    select_comment_topics_tool,
)

mcp = FastMCP("weibo-ops-hotcomment")


@mcp.tool
def get_hot_topics(limit: int = 20) -> dict:
    """Fetch current Weibo hot topics, falling back to mock topics if Weibo is unavailable."""
    return get_hot_topics_tool(limit=limit)


@mcp.tool
def select_comment_topics(
    topics: list[dict] | None = None,
    max_results: int = 5,
    source_limit: int = 50,
    enrich_metrics: bool = False,
    research_limit: int = 10,
) -> dict:
    """Recommend hot topics worth human review for sharp commentary."""
    return select_comment_topics_tool(
        topics=topics,
        max_results=max_results,
        source_limit=source_limit,
        enrich_metrics=enrich_metrics,
        research_limit=research_limit,
    )


@mcp.tool
def generate_comment(
    topic: str,
    context_text: str = "",
    style: str | None = None,
    persona: str | None = None,
    account_id: str = "today_direct",
    emotion_level: int = 6,
    use_rag: bool = True,
) -> dict:
    """Generate a fact-grounded, style-controlled Weibo commentary draft."""
    return generate_comment_tool(
        topic=topic,
        context_text=context_text,
        style=style,
        persona=persona,
        account_id=account_id,
        emotion_level=emotion_level,
        use_rag=use_rag,
    )


@mcp.tool
def rebuild_knowledge() -> dict:
    """Rebuild the local RAG index from Markdown knowledge files and selected ops docs."""
    return rebuild_knowledge_tool()


@mcp.tool
def search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """Search the local RAG knowledge index, falling back to keyword retrieval if needed."""
    return search_knowledge_tool(query=query, top_k=top_k)


if __name__ == "__main__":
    mcp.run()
