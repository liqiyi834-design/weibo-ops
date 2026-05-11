import json

from app.llm.client import BaseLLMClient, LLMClientError
from app.schemas.comment import FactSummary, OpinionDraft, RetrievedKnowledge, TopicClassification
from app.services.prompt_loader import PromptLoader


class OpinionGenerator:
    def __init__(self, llm: BaseLLMClient, prompts: PromptLoader):
        self.llm = llm
        self.prompts = prompts

    def generate(
        self,
        fact_summary: FactSummary,
        retrieved: list[RetrievedKnowledge],
        classification: TopicClassification,
    ) -> OpinionDraft:
        system_prompt = self.prompts.load("system.md")
        user_prompt = self.prompts.load("opinion.md").format(
            fact_summary=fact_summary.model_dump_json(ensure_ascii=False),
            retrieved_knowledge=json.dumps([item.model_dump() for item in retrieved], ensure_ascii=False),
            topic_classification=classification.model_dump_json(ensure_ascii=False),
        )
        try:
            data = self.llm.generate_json(system_prompt, user_prompt)
        except LLMClientError:
            data = {
                "core_conflict": "事实不完整时，表达欲和事实边界之间的冲突。",
                "critique_angles": ["先确认事实，再输出观点", "批评公共表达，不攻击个人"],
                "usable_lines": ["热搜可以快，结论最好慢半拍。"],
            }
        return OpinionDraft(**data)
