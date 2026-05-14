from app.llm.client import BaseLLMClient
from app.schemas.comment import CommentOutput, FactSummary, OpinionDraft, TopicClassification
from app.services.json_retry import complete_json_with_retry
from app.services.prompt_loader import PromptLoader


def default_comment_output() -> dict:
    return {
        "one_liner": "这事先别急着站队，事实和情绪得分开看。",
        "short_comment": "目前能稳妥讨论的是公开信息里的规则问题。没有更多可靠来源前，不适合给个人或机构直接定性。",
        "emotional_version": "最怕的不是热点吵起来，而是事实还没站稳，结论已经满天飞。",
        "rational_version": "建议先确认事实来源，再讨论责任边界、流程漏洞和公共表达是否得当。",
        "ironic_version": "热搜最不缺的是声音，缺的是把话说准。",
        "comment_replies": ["你觉得这件事更该追问事实，还是追问规则？"],
    }


class PersonaRewriter:
    def __init__(self, llm: BaseLLMClient, prompts: PromptLoader):
        self.llm = llm
        self.prompts = prompts

    def rewrite(
        self,
        fact_summary: FactSummary,
        opinion: OpinionDraft,
        classification: TopicClassification,
        persona: str,
        emotion_level: int,
    ) -> CommentOutput:
        capped_emotion = min(emotion_level, classification.max_emotion_level)
        system_prompt = self.prompts.load("system.md")
        user_prompt = self.prompts.load("persona_rewrite.md").format(
            fact_summary=fact_summary.model_dump_json(ensure_ascii=False),
            opinion=opinion.model_dump_json(ensure_ascii=False),
            topic_classification=classification.model_dump_json(ensure_ascii=False),
            persona=persona,
            emotion_level=capped_emotion,
        )
        data = complete_json_with_retry(
            llm=self.llm,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            required_fields=[
                "one_liner",
                "short_comment",
                "emotional_version",
                "rational_version",
                "ironic_version",
            ],
            defaults=default_comment_output(),
        )
        return CommentOutput(**data)
