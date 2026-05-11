import json

from app.llm.client import BaseLLMClient, LLMClientError
from app.schemas.comment import FactSummary
from app.services.prompt_loader import PromptLoader


class FactSummarizer:
    def __init__(self, llm: BaseLLMClient, prompts: PromptLoader):
        self.llm = llm
        self.prompts = prompts

    def summarize(self, topic: str, context_text: str) -> FactSummary:
        system_prompt = self.prompts.load("system.md")
        user_prompt = self.prompts.load("fact_summary.md").format(
            topic=topic,
            context_text=context_text or "用户未提供背景材料。",
        )
        try:
            data = self.llm.generate_json(system_prompt, user_prompt)
        except LLMClientError:
            data = {
                "confirmed_facts": [f"话题：{topic}。当前缺少可核验背景材料。"],
                "controversy_points": [],
                "uncertain_points": ["需要补充可靠来源后再生成强观点。"],
                "public_sentiment": None,
                "risk_level": "medium",
            }
        return FactSummary(topic=topic, **data)
