from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.llm.client import build_llm_client
from app.schemas.comment import RetrievedKnowledge
from app.schemas.comment import CandidatePool, CandidatePoolCreateRequest, CandidatePoolSummary
from app.schemas.comment import CandidateStatusUpdateRequest
from app.schemas.comment import DraftCreateRequest, DraftRecord, DraftSummary, DraftUpdateRequest
from app.schemas.comment import GenerateCommentRequest, GenerateCommentResponse
from app.schemas.comment import GenerateZhihuAnswerRequest, GenerateZhihuAnswerResponse, ZhihuDraftCreateRequest
from app.schemas.comment import HotTopic, TopicSelectionRequest, TopicSelectionResponse
from app.schemas.comment import KnowledgeIngestRequest, KnowledgeIngestResponse, KnowledgeRecord, KnowledgeRecordSummary
from app.schemas.comment import PlatformRoutingResponse
from app.schemas.comment import TopicRerankRequest, TopicRerankResponse
from app.schemas.comment import TopicResearchSourcesRequest, TopicResearchSourcesResponse
from app.schemas.comment import TopicAsset, TopicAssetCreateRequest, TopicAssetSummary, TopicAssetUpdateRequest
from app.services.candidate_pool_service import CandidatePoolService
from app.services.draft_service import DraftService
from app.services.exa_research_service import ExaResearchService
from app.services.generation_pipeline import GenerationPipeline
from app.services.hot_search_service import HotSearchService
from app.services.knowledge_ingestion_service import KnowledgeIngestionService
from app.services.knowledge_service import KnowledgeService
from app.services.platform_router import LLMPlatformRouter
from app.services.style_service import StyleService
from app.services.topic_research_service import TopicResearchService
from app.services.topic_rerank_service import TopicRerankService
from app.services.topic_asset_service import TopicAssetService
from app.services.topic_selection_service import TopicSelectionService
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
        "hot_weibo": "/api/hot/weibo",
        "generate": "/api/comment/generate",
        "knowledge_rebuild": "/api/knowledge/rebuild",
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/hot/weibo")
def get_weibo_hot_topics(limit: int = 20) -> dict:
    settings = get_settings()
    response = HotSearchService(settings).get_weibo_hot_topics(limit=limit)
    return response.model_dump()


@router.post("/api/topics/select", response_model=TopicSelectionResponse)
def select_comment_topics(request: TopicSelectionRequest) -> TopicSelectionResponse:
    settings = get_settings()
    topics = request.topics
    if not topics:
        hot_response = HotSearchService(settings).get_weibo_hot_topics(limit=request.source_limit)
        topics = [
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
    return CandidatePoolService().save(
        selected=selection.selected,
        source=selection.source,
        title=request.title,
        notes=selection.notes,
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
    generated = generate_zhihu_answer(request)
    return DraftService().save_zhihu_answer(
        generated=generated,
        title=request.title,
        candidate_pool_id=request.candidate_pool_id,
        candidate_item_id=request.candidate_item_id,
    )


@router.get("/api/drafts", response_model=list[DraftSummary])
def list_drafts() -> list[DraftSummary]:
    return DraftService().list_drafts()


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


@router.post("/api/research/exa", response_model=TopicResearchSourcesResponse)
def research_topic_sources(request: TopicResearchSourcesRequest) -> TopicResearchSourcesResponse:
    settings = get_settings()
    return ExaResearchService(settings).research_topic_sources(
        topic=request.topic,
        limit=request.limit,
        include_domains=request.include_domains,
        exclude_domains=request.exclude_domains,
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
