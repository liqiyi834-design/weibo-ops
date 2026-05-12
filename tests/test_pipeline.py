from pathlib import Path

from app.core.config import Settings
from app.llm.client import MockLLMClient
from app.schemas.comment import GenerateCommentRequest
from app.services.generation_pipeline import GenerationPipeline


def test_generation_pipeline_returns_complete_response():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    pipeline = GenerationPipeline(settings, MockLLMClient())

    response = pipeline.generate(
        GenerateCommentRequest(
            topic="某品牌母亲节文案翻车",
            context_text="用户提供背景：品牌文案被质疑把母亲角色工具化。",
            persona="pr_critic",
            emotion_level=7,
        )
    )

    assert response.topic == "某品牌母亲节文案翻车"
    assert response.account_id == "today_direct"
    assert response.style == "pr_critic"
    assert response.fact_summary.confirmed_facts
    assert response.topic_classification.category == "brand_pr"
    assert response.opinion.core_conflict
    assert response.output.short_comment
    assert response.safety.is_safe is True


def test_generation_pipeline_blocks_high_risk_angry_style():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    pipeline = GenerationPipeline(settings, MockLLMClient())

    response = pipeline.generate(
        GenerateCommentRequest(
            topic="法院回应偷拍男生案件",
            context_text="法院发布案件相关回应。",
            style="angry_netizen",
            emotion_level=9,
            use_rag=False,
        )
    )

    assert response.style == "rational_critic"
    assert response.topic_classification.risk_notes
