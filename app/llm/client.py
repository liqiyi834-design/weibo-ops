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
        if "platformroutingschema" in lowered:
            return {
                "decisions": [
                    {
                        "target_platform": "weibo",
                        "fit_score": 82,
                        "decision": "recommended",
                        "reasons": ["话题有即时讨论空间，适合短评切入。"],
                        "blockers": [],
                        "suggested_angle": "从公共讨论中的冲突点切入，先给判断再补边界。",
                        "required_research": ["补充可靠来源和关键事实时间线"],
                    },
                    {
                        "target_platform": "zhihu",
                        "fit_score": 74,
                        "decision": "optional",
                        "reasons": ["具备解释空间，但需要更多背景资料支撑。"],
                        "blockers": ["资料不足时不适合直接写长回答"],
                        "suggested_angle": "改写成如何看待类问题，展开规则、责任和影响。",
                        "required_research": ["补充来源链接", "确认争议各方公开回应"],
                    },
                    {
                        "target_platform": "video",
                        "fit_score": 48,
                        "decision": "not_recommended",
                        "reasons": ["视觉化表达空间一般。"],
                        "blockers": ["如果涉及真实公共事件，需要避免误导性画面"],
                        "suggested_angle": "暂不作为视频优先选题。",
                        "required_research": [],
                    },
                ]
            }
        if "topicrerankschema" in lowered:
            return {
                "ranked": [
                    {
                        "keyword": "test topic",
                        "final_score": 88,
                        "decision": "select",
                        "recommended_angle": "先核对公开来源，再从规则和责任边界切入。",
                        "reason": "资料有公开来源支撑，适合生成短评。",
                        "needed_context": [],
                        "risk_notes": [],
                    }
                ]
            }
        if "stylememoryschema" in lowered:
            return {
                "hook_patterns": ["先抛判断，再补事实边界"],
                "sentence_rhythm": "短句为主，转折明显，结尾留一个可讨论的问题。",
                "argument_structure": ["判断", "事实依据", "规则或人性层面的解释", "克制收束"],
                "rhetorical_devices": ["反差", "设问", "轻讽刺"],
                "emotion_level": 6,
                "suitable_topics": ["公共表达争议", "平台规则", "娱乐舆情"],
                "avoid_points": ["不照搬原句", "不攻击个人", "不把猜测写成事实"],
                "reusable_rules": ["观点可以锋利，但事实边界要先立住。"],
                "example_lines": ["热闹可以追，结论最好慢半拍。"],
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
