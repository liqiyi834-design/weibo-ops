from __future__ import annotations

from app.core.config import Settings, get_settings
from app.llm.client import BaseLLMClient, build_llm_client
from app.schemas.comment import DraftUpdateRequest, GenerateCommentRequest, HotTopic
from app.services.draft_service import DraftService
from app.services.generation_pipeline import GenerationPipeline
from app.services.hot_search_service import HotSearchService
from app.services.knowledge_service import KnowledgeService
from app.services.topic_research_service import TopicResearchService
from app.services.topic_selection_service import TopicSelectionService


def generate_comment_tool(
    topic: str,
    context_text: str = "",
    style: str | None = None,
    persona: str | None = None,
    account_id: str = "today_direct",
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
            account_id=account_id,
            context_text=context_text,
            style=style,
            persona=persona,
            emotion_level=emotion_level,
            use_rag=use_rag,
        )
    )
    return response.model_dump()


def save_draft_tool(
    topic: str,
    context_text: str = "",
    style: str | None = None,
    persona: str | None = None,
    account_id: str = "today_direct",
    emotion_level: int = 6,
    use_rag: bool = True,
    title: str | None = None,
    candidate_pool_id: str | None = None,
    candidate_item_id: str | None = None,
    settings: Settings | None = None,
    llm: BaseLLMClient | None = None,
) -> dict:
    active_settings = settings or get_settings()
    active_llm = llm or build_llm_client(active_settings)
    pipeline = GenerationPipeline(active_settings, active_llm)
    generated = pipeline.generate(
        GenerateCommentRequest(
            topic=topic,
            account_id=account_id,
            context_text=context_text,
            style=style,
            persona=persona,
            emotion_level=emotion_level,
            use_rag=use_rag,
        )
    )
    draft = DraftService().save(
        generated=generated,
        title=title,
        candidate_pool_id=candidate_pool_id,
        candidate_item_id=candidate_item_id,
    )
    return draft.model_dump()


def list_drafts_tool() -> list[dict]:
    return [draft.model_dump() for draft in DraftService().list_drafts()]


def update_draft_tool(
    draft_id: str,
    status: str | None = None,
    operator_note: str | None = None,
    edited_text: str | None = None,
) -> dict:
    request = DraftUpdateRequest(status=status, operator_note=operator_note, edited_text=edited_text)
    draft = DraftService().update(
        draft_id=draft_id,
        status=request.status,
        operator_note=request.operator_note,
        edited_text=request.edited_text,
    )
    return draft.model_dump()


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


def get_ent_topics_tool(limit: int = 20, settings: Settings | None = None) -> dict:
    active_settings = settings or get_settings()
    response = HotSearchService(active_settings).get_weibo_ent_topics(limit=limit)
    return response.model_dump()


def select_comment_topics_tool(
    topics: list[dict] | None = None,
    max_results: int = 5,
    source_limit: int = 50,
    enrich_metrics: bool = False,
    research_limit: int = 10,
    settings: Settings | None = None,
) -> dict:
    active_settings = settings or get_settings()
    if topics:
        hot_topics = [HotTopic(**topic) for topic in topics]
    else:
        response = HotSearchService(active_settings).get_weibo_hot_topics(limit=source_limit)
        hot_topics = [
            HotTopic(
                rank=item.rank,
                keyword=item.keyword,
                hot_value=item.hot_value,
                category_label=item.category_label,
                url=item.url,
                label=item.label,
                source=item.source,
                timestamp=item.timestamp,
            )
            for item in response.items
        ]
    if enrich_metrics:
        research_service = TopicResearchService(active_settings)
        for index, topic in enumerate(hot_topics):
            if index >= research_limit:
                break
            metrics = research_service.research(topic.keyword)
            topic.read_count = metrics.read_count
            topic.discussion_count = metrics.discussion_count
            topic.sampled_posts_count = metrics.sampled_posts_count
            topic.controversy_score = metrics.controversy_score
    result = TopicSelectionService().select(hot_topics, max_results=max_results)
    return result.model_dump()
