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


class EmptyOpinionLLM(MockLLMClient):
    def generate_json(self, system_prompt: str, user_prompt: str):
        if "观点" in user_prompt or "opinion" in user_prompt.lower():
            return {}
        return super().generate_json(system_prompt, user_prompt)


def test_generation_pipeline_recovers_from_empty_opinion_json():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    pipeline = GenerationPipeline(settings, EmptyOpinionLLM())

    response = pipeline.generate(
        GenerateCommentRequest(
            topic="某品牌文案翻车",
            context_text="品牌文案被质疑表达不当。",
            use_rag=False,
        )
    )

    assert response.opinion.core_conflict
    assert response.output.short_comment


class RetryOpinionLLM(MockLLMClient):
    def __init__(self):
        self.opinion_calls = 0

    def generate_json(self, system_prompt: str, user_prompt: str):
        if "opinionschema" in user_prompt.lower():
            self.opinion_calls += 1
            if self.opinion_calls == 1:
                return {}
        return super().generate_json(system_prompt, user_prompt)


def test_generation_pipeline_retries_empty_opinion_json():
    llm = RetryOpinionLLM()
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    pipeline = GenerationPipeline(settings, llm)

    response = pipeline.generate(
        GenerateCommentRequest(
            topic="某品牌文案翻车",
            context_text="品牌文案被质疑表达不当。",
            use_rag=False,
        )
    )

    assert llm.opinion_calls == 2
    assert response.opinion.core_conflict
    assert response.output.short_comment


class RetryRewriteLLM(MockLLMClient):
    def __init__(self):
        self.rewrite_calls = 0

    def generate_json(self, system_prompt: str, user_prompt: str):
        lowered = user_prompt.lower()
        if "one_liner" in lowered and "opinionschema" not in lowered:
            self.rewrite_calls += 1
            if self.rewrite_calls == 1:
                return {}
            return {
                "one_liner": "retry one liner",
                "short_comment": "retry short comment",
                "emotional_version": "retry emotional",
                "rational_version": "retry rational",
                "ironic_version": "retry ironic",
                "comment_replies": ["retry reply"],
            }
        return super().generate_json(system_prompt, user_prompt)


def test_generation_pipeline_retries_empty_rewrite_json():
    llm = RetryRewriteLLM()
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    pipeline = GenerationPipeline(settings, llm)

    response = pipeline.generate(
        GenerateCommentRequest(
            topic="某品牌文案翻车",
            context_text="品牌文案被质疑表达不当。",
            use_rag=False,
        )
    )

    assert llm.rewrite_calls == 2
    assert response.output.one_liner == "retry one liner"
    assert response.output.short_comment == "retry short comment"
