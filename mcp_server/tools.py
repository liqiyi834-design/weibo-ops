from __future__ import annotations

from app.core.config import Settings, get_settings
from app.llm.client import BaseLLMClient, build_llm_client
from app.schemas.comment import GenerateCommentRequest
from app.services.generation_pipeline import GenerationPipeline
from app.services.hot_search_service import HotSearchService
from app.services.knowledge_service import KnowledgeService


def generate_comment_tool(
    topic: str,
    context_text: str = "",
    persona: str = "rational_critic",
    emotion_level: int = 6,
    use_rag: bool = True,
    settings: Settings | None = None,
    llm: BaseLLMClient | None = None,
) -> dict:
    active_settings = settings or get_settings()
    active_llm = llm or build_llm_client(active_settings)
    pipeline = GenerationPipeline(active_settings, active_llm)
    response = pipeline.generate(
        GenerateCommentRequest(
            topic=topic,
            context_text=context_text,
            persona=persona,
            emotion_level=emotion_level,
            use_rag=use_rag,
        )
    )
    return response.model_dump()


def rebuild_knowledge_tool(settings: Settings | None = None) -> dict:
    active_settings = settings or get_settings()
    return KnowledgeService(active_settings).rebuild()


def search_knowledge_tool(query: str, top_k: int = 5, settings: Settings | None = None) -> list[dict]:
    active_settings = settings or get_settings()
    results = KnowledgeService(active_settings).search(query=query, top_k=top_k)
    return [item.model_dump() for item in results]


def get_hot_topics_tool(limit: int = 20, settings: Settings | None = None) -> dict:
    active_settings = settings or get_settings()
    response = HotSearchService(active_settings).get_weibo_hot_topics(limit=limit)
    return response.model_dump()
