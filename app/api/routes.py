from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.llm.client import build_llm_client
from app.schemas.comment import RetrievedKnowledge
from app.schemas.comment import GenerateCommentRequest, GenerateCommentResponse
from app.services.generation_pipeline import GenerationPipeline
from app.services.hot_search_service import HotSearchService
from app.services.knowledge_service import KnowledgeService

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


@router.post("/api/comment/generate", response_model=GenerateCommentResponse)
def generate_comment(request: GenerateCommentRequest) -> GenerateCommentResponse:
    settings = get_settings()
    llm = build_llm_client(settings)
    pipeline = GenerationPipeline(settings, llm)
    return pipeline.generate(request)


@router.get("/api/comment/personas")
def personas() -> dict[str, list[dict[str, str]]]:
    return {
        "personas": [
            {"id": "angry_netizen", "name": "暴躁网友型"},
            {"id": "ironic_observer", "name": "阴阳怪气型"},
            {"id": "rational_critic", "name": "理性拆解型"},
            {"id": "pr_critic", "name": "公关毒舌观察者"},
        ]
    }


@router.post("/api/knowledge/rebuild")
def rebuild_knowledge() -> dict[str, int | bool | str]:
    settings = get_settings()
    return KnowledgeService(settings).rebuild()


@router.post("/api/knowledge/search", response_model=list[RetrievedKnowledge])
def search_knowledge(request: KnowledgeSearchRequest) -> list[RetrievedKnowledge]:
    settings = get_settings()
    return KnowledgeService(settings).search(request.query, request.top_k)
