from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx
from openai import OpenAI

from app.core.config import Settings


class LLMClientError(RuntimeError):
    pass


class BaseLLMClient(ABC):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        raise NotImplementedError


class OpenAICompatibleLLMClient(BaseLLMClient):
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise LLMClientError("OPENAI_API_KEY is not configured.")
        self.model = settings.openai_model
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            http_client=httpx.Client(timeout=settings.request_timeout_seconds, trust_env=False),
        )

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
        except Exception as exc:  # pragma: no cover - depends on provider/network
            raise LLMClientError(f"LLM request failed: {exc}") from exc

        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMClientError(f"LLM returned non-JSON content: {content[:200]}") from exc


class MockLLMClient(BaseLLMClient):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        lowered = user_prompt.lower()
        if "factschema" in lowered:
            return {
                "confirmed_facts": ["用户提供了话题和背景材料，需以公开信息为准。"],
                "controversy_points": ["争议点可能来自事实不足、立场冲突或表达方式。"],
                "uncertain_points": ["缺少可核验来源时不能下定论。"],
                "public_sentiment": "需要进一步观察评论区分歧。",
                "risk_level": "low",
            }
        if "opinionschema" in lowered:
            return {
                "core_conflict": "热点表达与事实边界之间的冲突。",
                "critique_angles": ["先讲事实，再讲判断", "批评行为和机制，不攻击个人"],
                "usable_lines": ["热闹可以追，结论最好慢半拍。", "真正值得看的，是这件事暴露出的规则缝隙。"],
            }
        return {
            "one_liner": "这事别急着站队，先把事实和情绪分开看。",
            "short_comment": "目前公开信息还有限，能写的是规则和表达问题，不能把猜测写成定论。热搜可以快，判断要稳。",
            "emotional_version": "这类事最烦人的地方，是大家还没看清事实，情绪已经先跑完一圈了。",
            "rational_version": "更稳妥的讨论方式是先确认事实来源，再分析争议背后的规则、责任和表达边界。",
            "ironic_version": "互联网不缺快嘴，缺的是能把话说狠但不说虚的人。",
            "comment_replies": ["你觉得这事该先追问事实，还是先讨论规则？"],
        }


def build_llm_client(settings: Settings) -> BaseLLMClient:
    if settings.openai_api_key:
        return OpenAICompatibleLLMClient(settings)
    return MockLLMClient()
