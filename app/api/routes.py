from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.llm.client import build_llm_client
from app.schemas.comment import RetrievedKnowledge
from app.schemas.comment import CandidatePool, CandidatePoolCreateRequest, CandidatePoolSummary
from app.schemas.comment import CandidateStatusUpdateRequest
from app.schemas.comment import DraftCreateRequest, DraftRecord, DraftSummary, DraftUpdateRequest
from app.schemas.comment import GenerationContextRequest, GenerationContextResponse
from app.schemas.comment import GenerateCommentRequest, GenerateCommentResponse
from app.schemas.comment import GenerateZhihuAnswerRequest, GenerateZhihuAnswerResponse, ZhihuDraftCreateRequest
from app.schemas.comment import HotTopicClusterResponse
from app.schemas.comment import HotTopic, TopicSelectionRequest, TopicSelectionResponse
from app.schemas.comment import KnowledgeIngestRequest, KnowledgeIngestResponse, KnowledgeRecord, KnowledgeRecordSummary
from app.schemas.comment import PlatformRoutingResponse
from app.schemas.comment import StyleMemoryExtractRequest, StyleMemoryExtractResponse
from app.schemas.comment import StyleMemoryIngestRequest, StyleMemoryIngestResponse
from app.schemas.comment import TopicRerankRequest, TopicRerankResponse
from app.schemas.comment import TopicResearchSourcesRequest, TopicResearchSourcesResponse
from app.schemas.comment import WeiboAiSearchResearchRequest
from app.schemas.comment import TopicAsset, TopicAssetCreateRequest, TopicAssetSummary, TopicAssetUpdateRequest
from app.schemas.feedback import (
    DraftFeedbackRecord,
    DraftFeedbackRequest,
    DraftFeedbackResponse,
    FeedbackMemorySummarizeRequest,
    FeedbackMemorySummarizeResponse,
)
from app.schemas.notification import ReviewMessageRequest, ReviewMessageResponse
from app.services.candidate_pool_service import CandidatePoolService
from app.services.candidate_context_service import build_candidate_background_context
from app.services.candidate_pool_rerank_service import CandidatePoolRerankService
from app.services.draft_service import DraftService
from app.services.draft_feedback_service import DraftFeedbackService
from app.services.exa_research_service import ExaResearchService
from app.services.generation_context_service import GenerationContextService
from app.services.generation_pipeline import GenerationPipeline
from app.services.hermes_status_service import HermesStatusService
from app.services.hot_search_service import HotSearchService
from app.services.hot_topic_cluster_service import HotTopicClusterService
from app.services.knowledge_ingestion_service import KnowledgeIngestionService
from app.services.knowledge_service import KnowledgeService
from app.services.notification_service import NotificationService
from app.services.platform_router import LLMPlatformRouter
from app.services.style_memory_service import StyleMemoryService
from app.services.style_service import StyleService
from app.services.topic_research_service import TopicResearchService
from app.services.topic_rerank_service import TopicRerankService
from app.services.topic_asset_service import TopicAssetService
from app.services.topic_selection_service import TopicSelectionService
from app.services.weibo_aisearch_research_service import WeiboAiSearchResearchService
from app.services.zhihu_answer_generator import ZhihuAnswerGenerator

router = APIRouter()


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


@router.get("/")
def root() -> dict[str, str]:
    return {
        "name": "HotComment-AI",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "hot": "/api/hot",
        "hot_clusters": "/api/hot/clusters",
        "hot_weibo": "/api/hot/weibo",
        "generate": "/api/comment/generate",
        "knowledge_rebuild": "/api/knowledge/rebuild",
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/system/hermes-status")
def hermes_status() -> dict:
    return HermesStatusService().status()


@router.post("/api/notifications/review-message", response_model=ReviewMessageResponse)
def send_review_message(request: ReviewMessageRequest) -> ReviewMessageResponse:
    return NotificationService().send_review_message(request)


@router.get("/api/hot/weibo")
def get_weibo_hot_topics(limit: int = 20) -> dict:
    settings = get_settings()
    response = HotSearchService(settings).get_weibo_hot_topics(limit=limit)
    return response.model_dump()


@router.get("/api/hot")
def get_hot_topics(platform: str = "weibo", limit: int = 20) -> dict:
    settings = get_settings()
    try:
        response = HotSearchService(settings).get_hot_topics(platform=platform, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return response.model_dump()


@router.get("/api/hot/clusters", response_model=HotTopicClusterResponse)
def get_hot_topic_clusters(platform: str = "all", limit: int = 50, max_clusters: int = 30) -> HotTopicClusterResponse:
    settings = get_settings()
    try:
        response = HotSearchService(settings).get_hot_topics(platform=platform, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return HotTopicClusterService().cluster(response, max_clusters=max_clusters)


@router.post("/api/topics/select", response_model=TopicSelectionResponse)
def select_comment_topics(request: TopicSelectionRequest) -> TopicSelectionResponse:
    settings = get_settings()
    topics = request.topics
    if not topics:
        try:
            hot_response = HotSearchService(settings).get_hot_topics(
                platform=request.source_platform,
                limit=request.source_limit,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        topics = [
            HotTopic(
                rank=item.rank,
                original_rank=item.original_rank or item.rank,
                keyword=item.keyword,
                hot_value=item.hot_value,
                category_label=item.category_label,
                url=item.url,
                label=item.label,
                platform=item.platform,
                source=item.source,
                timestamp=item.timestamp,
            )
            for item in hot_response.items
        ]
    if request.enrich_metrics:
        research_service = TopicResearchService(settings)
        topics = [
            _merge_topic_metrics(topic, research_service.research(topic.keyword))
            if index < request.research_limit
            else topic
            for index, topic in enumerate(topics)
        ]
    return TopicSelectionService().select(topics, max_results=request.max_results)


@router.post("/api/topic-candidates/pools", response_model=CandidatePool)
def create_candidate_pool(request: CandidatePoolCreateRequest) -> CandidatePool:
    selection = select_comment_topics(request)
    selected = selection.selected
    notes = list(selection.notes)
    source = selection.source
    if request.use_exa_rerank:
        settings = get_settings()
        llm = build_llm_client(settings)
        selected, rerank_notes = CandidatePoolRerankService(settings, llm).rerank_selected(
            selected=selection.selected,
            max_results=request.max_results,
        research_limit=request.exa_research_limit,
        sources_per_topic=request.exa_sources_per_topic,
        account_id=request.rerank_account_id,
        use_weibo_aisearch=request.use_weibo_aisearch_rerank,
    )
        notes.extend(rerank_notes)
        source = f"{selection.source}+research_rerank"
    return CandidatePoolService().save(
        selected=selected,
        source=source,
        title=request.title,
        notes=notes,
    )


@router.get("/api/topic-candidates/pools", response_model=list[CandidatePoolSummary])
def list_candidate_pools() -> list[CandidatePoolSummary]:
    return CandidatePoolService().list_pools()


@router.get("/api/topic-candidates/pools/{pool_id}", response_model=CandidatePool)
def get_candidate_pool(pool_id: str) -> CandidatePool:
    try:
        return CandidatePoolService().get(pool_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/api/topic-candidates/pools/{pool_id}/items/{item_id}", response_model=CandidatePool)
def update_candidate_item(
    pool_id: str,
    item_id: str,
    request: CandidateStatusUpdateRequest,
) -> CandidatePool:
    try:
        return CandidatePoolService().update_item(
            pool_id=pool_id,
            item_id=item_id,
            status=request.status,
            operator_note=request.operator_note,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _merge_topic_metrics(topic: HotTopic, metrics) -> HotTopic:
    topic.read_count = metrics.read_count
    topic.discussion_count = metrics.discussion_count
    topic.sampled_posts_count = metrics.sampled_posts_count
    topic.controversy_score = metrics.controversy_score
    return topic


@router.post("/api/topic-assets", response_model=TopicAsset)
def create_topic_asset(request: TopicAssetCreateRequest) -> TopicAsset:
    return TopicAssetService().create(request)


@router.get("/api/topic-assets", response_model=list[TopicAssetSummary])
def list_topic_assets(status: str | None = None, limit: int = 100) -> list[TopicAssetSummary]:
    return TopicAssetService().list_assets(status=status, limit=limit)


@router.get("/api/topic-assets/{asset_id}", response_model=TopicAsset)
def get_topic_asset(asset_id: str) -> TopicAsset:
    try:
        return TopicAssetService().get(asset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/api/topic-assets/{asset_id}", response_model=TopicAsset)
def update_topic_asset(asset_id: str, request: TopicAssetUpdateRequest) -> TopicAsset:
    try:
        return TopicAssetService().update(asset_id, request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/topic-assets/{asset_id}/routing", response_model=PlatformRoutingResponse)
def route_topic_asset(asset_id: str) -> PlatformRoutingResponse:
    settings = get_settings()
    try:
        asset = TopicAssetService().get(asset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    llm = build_llm_client(settings)
    return LLMPlatformRouter(llm).route(asset)


@router.post("/api/comment/generate", response_model=GenerateCommentResponse)
def generate_comment(request: GenerateCommentRequest) -> GenerateCommentResponse:
    settings = get_settings()
    llm = build_llm_client(settings)
    pipeline = GenerationPipeline(settings, llm)
    return pipeline.generate(request)


@router.post("/api/zhihu/answer/generate", response_model=GenerateZhihuAnswerResponse)
def generate_zhihu_answer(request: GenerateZhihuAnswerRequest) -> GenerateZhihuAnswerResponse:
    settings = get_settings()
    llm = build_llm_client(settings)
    return ZhihuAnswerGenerator(settings, llm).generate(request)


@router.post("/api/drafts", response_model=DraftRecord)
def create_draft(request: DraftCreateRequest) -> DraftRecord:
    request = _with_candidate_background_context(request)
    generated = generate_comment(request)
    return DraftService().save(
        generated=generated,
        title=request.title,
        candidate_pool_id=request.candidate_pool_id,
        candidate_item_id=request.candidate_item_id,
        platform=request.platform,
        draft_type=request.draft_type,
    )


@router.post("/api/drafts/zhihu", response_model=DraftRecord)
def create_zhihu_draft(request: ZhihuDraftCreateRequest) -> DraftRecord:
    request = _with_candidate_background_context(request)
    generated = generate_zhihu_answer(request)
    return DraftService().save_zhihu_answer(
        generated=generated,
        title=request.title,
        candidate_pool_id=request.candidate_pool_id,
        candidate_item_id=request.candidate_item_id,
    )


def _with_candidate_background_context(request: DraftCreateRequest | ZhihuDraftCreateRequest):
    if not request.candidate_pool_id or not request.candidate_item_id:
        return request
    try:
        pool = CandidatePoolService().get(request.candidate_pool_id)
    except FileNotFoundError:
        return request
    item = next((candidate for candidate in pool.items if candidate.id == request.candidate_item_id), None)
    if not item:
        return request
    context_text = build_candidate_background_context(
        item.model_dump(mode="json"),
        request.context_text,
    )
    return request.model_copy(update={"context_text": context_text})


@router.get("/api/drafts", response_model=list[DraftSummary])
def list_drafts() -> list[DraftSummary]:
    return DraftService().list_drafts()


@router.post("/api/draft-feedback", response_model=DraftFeedbackResponse)
def record_draft_feedback(request: DraftFeedbackRequest) -> DraftFeedbackResponse:
    return DraftFeedbackService().record(request)


@router.get("/api/draft-feedback", response_model=list[DraftFeedbackRecord])
def list_draft_feedback(limit: int = 50) -> list[DraftFeedbackRecord]:
    return DraftFeedbackService().list_records(limit=limit)


@router.post("/api/draft-feedback/summarize", response_model=FeedbackMemorySummarizeResponse)
def summarize_draft_feedback(request: FeedbackMemorySummarizeRequest) -> FeedbackMemorySummarizeResponse:
    settings = get_settings()
    llm = build_llm_client(settings) if request.use_llm else None
    return DraftFeedbackService(settings=settings, llm=llm).summarize_memory(request)


@router.get("/api/drafts/{draft_id}", response_model=DraftRecord)
def get_draft(draft_id: str) -> DraftRecord:
    try:
        return DraftService().get(draft_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/api/drafts/{draft_id}", response_model=DraftRecord)
def update_draft(draft_id: str, request: DraftUpdateRequest) -> DraftRecord:
    try:
        return DraftService().update(
            draft_id=draft_id,
            status=request.status,
            operator_note=request.operator_note,
            edited_text=request.edited_text,
            published_url=request.published_url,
            published_at=request.published_at,
            performance_note=request.performance_note,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/comment/personas")
def personas() -> dict[str, list[dict[str, str]]]:
    styles = StyleService().list_styles()
    return {
        "personas": [
            {"id": style.id, "name": style.name, "description": style.description}
            for style in styles
        ]
    }


@router.get("/api/comment/styles")
def styles() -> dict:
    return {"styles": [style.model_dump() for style in StyleService().list_styles()]}


@router.get("/api/accounts")
def accounts() -> dict:
    return {"accounts": [account.model_dump() for account in StyleService().list_accounts()]}


@router.post("/api/knowledge/rebuild")
def rebuild_knowledge() -> dict[str, int | bool | str]:
    settings = get_settings()
    return KnowledgeService(settings).rebuild()


@router.post("/api/knowledge/ingest", response_model=KnowledgeIngestResponse)
def ingest_knowledge(request: KnowledgeIngestRequest) -> KnowledgeIngestResponse:
    settings = get_settings()
    return KnowledgeIngestionService(settings).ingest(request)


@router.get("/api/knowledge/inbox", response_model=list[KnowledgeRecordSummary])
def list_knowledge_records(
    candidate_pool_id: str | None = None,
    candidate_item_id: str | None = None,
    limit: int = 50,
) -> list[KnowledgeRecordSummary]:
    settings = get_settings()
    return KnowledgeIngestionService(settings).list_records(
        candidate_pool_id=candidate_pool_id,
        candidate_item_id=candidate_item_id,
        limit=limit,
    )


@router.get("/api/knowledge/inbox/{record_id}", response_model=KnowledgeRecord)
def get_knowledge_record(record_id: str) -> KnowledgeRecord:
    settings = get_settings()
    try:
        return KnowledgeIngestionService(settings).get_record(record_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/knowledge/search", response_model=list[RetrievedKnowledge])
def search_knowledge(request: KnowledgeSearchRequest) -> list[RetrievedKnowledge]:
    settings = get_settings()
    return KnowledgeService(settings).search(request.query, request.top_k)


@router.post("/api/style-memory/extract", response_model=StyleMemoryExtractResponse)
def extract_style_memory(request: StyleMemoryExtractRequest) -> StyleMemoryExtractResponse:
    settings = get_settings()
    llm = build_llm_client(settings)
    return StyleMemoryService(settings, llm).extract(request)


@router.post("/api/style-memory/ingest", response_model=StyleMemoryIngestResponse)
def ingest_style_memory(request: StyleMemoryIngestRequest) -> StyleMemoryIngestResponse:
    settings = get_settings()
    return StyleMemoryService(settings).ingest(request)


@router.get("/api/style-memory/cards")
def list_style_memory_cards(limit: int = 50) -> dict:
    settings = get_settings()
    return {"cards": StyleMemoryService(settings).list_cards(limit=limit)}


@router.post("/api/research/exa", response_model=TopicResearchSourcesResponse)
def research_topic_sources(request: TopicResearchSourcesRequest) -> TopicResearchSourcesResponse:
    settings = get_settings()
    return ExaResearchService(settings).research_topic_sources(
        topic=request.topic,
        limit=request.limit,
        include_domains=request.include_domains,
        exclude_domains=request.exclude_domains,
        query=request.query,
    )


@router.post("/api/research/weibo-aisearch", response_model=TopicResearchSourcesResponse)
def research_weibo_aisearch(request: WeiboAiSearchResearchRequest) -> TopicResearchSourcesResponse:
    settings = get_settings()
    return WeiboAiSearchResearchService(settings).research_topic_sources(
        topic=request.topic,
        max_polls=request.max_polls,
        poll_interval_seconds=request.poll_interval_seconds,
    )


@router.post("/api/topics/rerank", response_model=TopicRerankResponse)
def rerank_topics_with_research(request: TopicRerankRequest) -> TopicRerankResponse:
    settings = get_settings()
    llm = build_llm_client(settings)
    return TopicRerankService(llm).rerank(
        candidates=request.candidates,
        max_results=request.max_results,
        account_id=request.account_id,
    )


@router.post("/api/comment/context", response_model=GenerationContextResponse)
def build_generation_context(request: GenerationContextRequest) -> GenerationContextResponse:
    return GenerationContextService().build(request)
