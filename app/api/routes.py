from fastapi import APIRouter

from app.core.config import get_settings
from app.llm.client import build_llm_client
from app.schemas.comment import GenerateCommentRequest, GenerateCommentResponse
from app.services.generation_pipeline import GenerationPipeline
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.get("/")
def root() -> dict[str, str]:
    return {
        "name": "HotComment-AI",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "generate": "/api/comment/generate",
        "knowledge_rebuild": "/api/knowledge/rebuild",
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
