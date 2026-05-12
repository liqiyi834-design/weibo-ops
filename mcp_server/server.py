from __future__ import annotations

from fastmcp import FastMCP

from mcp_server.tools import (
    generate_comment_tool,
    get_hot_topics_tool,
    rebuild_knowledge_tool,
    search_knowledge_tool,
)

mcp = FastMCP("weibo-ops-hotcomment")


@mcp.tool
def get_hot_topics(limit: int = 20) -> dict:
    """Fetch current Weibo hot topics, falling back to mock topics if Weibo is unavailable."""
    return get_hot_topics_tool(limit=limit)


@mcp.tool
def generate_comment(
    topic: str,
    context_text: str = "",
    persona: str = "rational_critic",
    emotion_level: int = 6,
    use_rag: bool = True,
) -> dict:
    """Generate a fact-grounded, persona-styled Weibo commentary draft."""
    return generate_comment_tool(
        topic=topic,
        context_text=context_text,
        persona=persona,
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
