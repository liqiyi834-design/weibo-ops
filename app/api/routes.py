from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.llm.client import build_llm_client
from app.schemas.comment import RetrievedKnowledge
from app.schemas.comment import CandidatePool, CandidatePoolCreateRequest, CandidatePoolSummary
from app.schemas.comment import CandidateStatusUpdateRequest
from app.schemas.comment import GenerateCommentRequest, GenerateCommentResponse
from app.schemas.comment import HotTopic, TopicSelectionRequest, TopicSelectionResponse
from app.services.candidate_pool_service import CandidatePoolService
from app.services.generation_pipeline import GenerationPipeline
from app.services.hot_search_service import HotSearchService
from app.services.knowledge_service import KnowledgeService
from app.services.style_service import StyleService
from app.services.topic_research_service import TopicResearchService
from app.services.topic_selection_service import TopicSelectionService

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


@router.post("/api/comment/generate", response_model=GenerateCommentResponse)
def generate_comment(request: GenerateCommentRequest) -> GenerateCommentResponse:
    settings = get_settings()
    llm = build_llm_client(settings)
    pipeline = GenerationPipeline(settings, llm)
    return pipeline.generate(request)


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


@router.post("/api/knowledge/search", response_model=list[RetrievedKnowledge])
def search_knowledge(request: KnowledgeSearchRequest) -> list[RetrievedKnowledge]:
    settings = get_settings()
    return KnowledgeService(settings).search(request.query, request.top_k)
