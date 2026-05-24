from __future__ import annotations

from app.core.config import Settings, get_settings
from app.llm.client import BaseLLMClient, build_llm_client
from app.schemas.comment import (
    CommentOutput,
    DraftUpdateRequest,
    FactSummary,
    GenerationContextRequest,
    GenerateCommentRequest,
    HotTopic,
    KnowledgeIngestRequest,
    TopicRerankCandidate,
)
from app.services.draft_service import DraftService
from app.services.exa_research_service import ExaResearchService
from app.services.generation_context_service import GenerationContextService
from app.services.generation_pipeline import GenerationPipeline
from app.services.knowledge_ingestion_service import KnowledgeIngestionService
from app.services.hot_search_service import HotSearchService
from app.services.knowledge_service import KnowledgeService
from app.services.safety_checker import SafetyChecker
from app.services.topic_classifier import TopicClassifier
from app.services.topic_research_service import TopicResearchService
from app.services.topic_rerank_service import TopicRerankService
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


def retrieve_knowledge_tool(query: str, top_k: int = 5, settings: Settings | None = None) -> list[dict]:
    return search_knowledge_tool(query=query, top_k=top_k, settings=settings)


def ingest_knowledge_tool(
    topic: str,
    content: str,
    source_url: str | None = None,
    source_title: str | None = None,
    credibility: str = "unknown",
    needs_review: bool = True,
    candidate_pool_id: str | None = None,
    candidate_item_id: str | None = None,
    operator_note: str | None = None,
    rebuild_index: bool = True,
    settings: Settings | None = None,
) -> dict:
    active_settings = settings or get_settings()
    request = KnowledgeIngestRequest(
        topic=topic,
        content=content,
        source_url=source_url,
        source_title=source_title,
        credibility=credibility,
        needs_review=needs_review,
        candidate_pool_id=candidate_pool_id,
        candidate_item_id=candidate_item_id,
        operator_note=operator_note,
        rebuild_index=rebuild_index,
    )
    response = KnowledgeIngestionService(active_settings).ingest(request)
    return response.model_dump()


def ingest_research_sources_tool(
    topic: str,
    sources: list[dict],
    selected_indices: list[int],
    candidate_pool_id: str | None = None,
    candidate_item_id: str | None = None,
    operator_note: str | None = None,
    rebuild_index: bool = True,
    settings: Settings | None = None,
) -> dict:
    active_settings = settings or get_settings()
    selected_sources = _select_research_sources(sources, selected_indices)
    ingested = []
    for index, source in enumerate(selected_sources):
        should_rebuild = rebuild_index and index == len(selected_sources) - 1
        request = KnowledgeIngestRequest(
            topic=topic,
            content=_research_source_content(source),
            source_url=source.get("url") or None,
            source_title=source.get("title") or source.get("domain") or None,
            credibility=source.get("credibility") or "unknown",
            needs_review=True,
            candidate_pool_id=candidate_pool_id,
            candidate_item_id=candidate_item_id,
            operator_note=operator_note or "Hermes Exa 本轮检索资料，用户确认后入库。",
            rebuild_index=should_rebuild,
        )
        response = KnowledgeIngestionService(active_settings).ingest(request)
        ingested.append(response.model_dump())
    return {
        "topic": topic,
        "requested_indices": selected_indices,
        "ingested_count": len(ingested),
        "ingested": ingested,
        "rebuild_index": rebuild_index,
    }


def research_topic_sources_tool(
    topic: str,
    limit: int = 5,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    settings: Settings | None = None,
) -> dict:
    active_settings = settings or get_settings()
    response = ExaResearchService(active_settings).research_topic_sources(
        topic=topic,
        limit=limit,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
    )
    return response.model_dump()


def rerank_topics_with_research_tool(
    candidates: list[dict],
    max_results: int = 3,
    account_id: str = "today_direct",
    settings: Settings | None = None,
    llm: BaseLLMClient | None = None,
) -> dict:
    active_settings = settings or get_settings()
    active_llm = llm or build_llm_client(active_settings)
    parsed = [TopicRerankCandidate(**candidate) for candidate in candidates]
    response = TopicRerankService(active_llm).rerank(
        candidates=parsed,
        max_results=max_results,
        account_id=account_id,
    )
    return response.model_dump()


def build_generation_context_tool(
    topic: str,
    research_sources: list[dict] | None = None,
    rag_results: list[dict] | None = None,
    reranked_topic: dict | None = None,
    classification: dict | None = None,
    max_sources: int = 5,
    max_rag_items: int = 5,
) -> dict:
    request = GenerationContextRequest(
        topic=topic,
        research_sources=research_sources or [],
        rag_results=rag_results or [],
        reranked_topic=reranked_topic,
        classification=classification,
        max_sources=max_sources,
        max_rag_items=max_rag_items,
    )
    return GenerationContextService().build(request).model_dump()


def classify_topic_tool(topic: str, context_text: str = "") -> dict:
    fact_summary = FactSummary(topic=topic)
    classification = TopicClassifier().classify(topic, context_text, fact_summary)
    risk_level = _classification_risk_level(classification.max_emotion_level, classification.category)
    return {
        "topic": topic,
        "category": classification.category,
        "risk_level": risk_level,
        "recommended_style": classification.recommended_persona,
        "max_emotion_level": classification.max_emotion_level,
        "risk_notes": classification.risk_notes,
    }


def safety_check_tool(text: str, topic: str = "", context_text: str = "") -> dict:
    subject = topic or text[:80] or "manual_text"
    fact_summary = FactSummary(topic=subject)
    classification = TopicClassifier().classify(subject, f"{context_text} {text}", fact_summary)
    output = CommentOutput(
        one_liner=text,
        short_comment=text,
        emotional_version="",
        rational_version=text,
        ironic_version="",
        comment_replies=[],
    )
    result = SafetyChecker().check(output, fact_summary, classification)
    recommendation = "blocked" if result.risk_level == "blocked" else "human_review_required"
    if result.is_safe and result.risk_level == "low":
        recommendation = "review_before_publish"
    return {
        "topic": subject,
        "is_safe": result.is_safe,
        "risk_level": result.risk_level,
        "issues": result.issues,
        "recommendation": recommendation,
        "revised_output": result.revised_output.model_dump() if result.revised_output else None,
    }


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


def _classification_risk_level(max_emotion_level: int, category: str) -> str:
    if category in {"political_sensitive", "crime_case", "disaster", "minor_related"}:
        return "high"
    if max_emotion_level <= 4:
        return "high"
    if max_emotion_level <= 6:
        return "medium"
    return "low"


def _select_research_sources(sources: list[dict], selected_indices: list[int]) -> list[dict]:
    if not selected_indices:
        raise ValueError("selected_indices must contain at least one 1-based source index.")
    selected = []
    for source_index in selected_indices:
        zero_based = source_index - 1
        if zero_based < 0 or zero_based >= len(sources):
            raise ValueError(f"selected index out of range: {source_index}")
        selected.append(sources[zero_based])
    return selected


def _research_source_content(source: dict) -> str:
    title = source.get("title") or source.get("domain") or source.get("url") or "未命名来源"
    highlights = [str(value).strip() for value in source.get("highlights") or [] if str(value).strip()]
    lines = [
        f"来源：{title}",
        f"URL：{source.get('url') or ''}",
        f"域名：{source.get('domain') or ''}",
        f"可信度：{source.get('credibility') or 'unknown'}",
        f"发布时间：{source.get('published_date') or ''}",
        "",
        "摘要：",
        source.get("summary") or "",
    ]
    if highlights:
        lines.extend(["", "高亮："])
        lines.extend(f"- {highlight}" for highlight in highlights)
    return "\n".join(lines).strip()
