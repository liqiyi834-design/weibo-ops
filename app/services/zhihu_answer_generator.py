from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.llm.client import BaseLLMClient
from app.rag.embeddings import build_embedding_client
from app.rag.knowledge import KnowledgeLoader
from app.rag.retriever import KeywordRetriever
from app.rag.vector_store import LocalVectorStore, VectorRetriever
from app.schemas.comment import (
    GenerateZhihuAnswerRequest,
    GenerateZhihuAnswerResponse,
    ZhihuAnswerOutput,
)
from app.services.fact_summarizer import FactSummarizer
from app.services.generation_pipeline import build_knowledge_loader
from app.services.json_retry import complete_json_with_retry
from app.services.opinion_generator import OpinionGenerator
from app.services.prompt_loader import PromptLoader
from app.services.style_service import StyleService
from app.services.topic_classifier import TopicClassifier
from app.services.zhihu_domain_service import ZhihuDomainService


class ZhihuAnswerGenerator:
    def __init__(self, settings: Settings, llm: BaseLLMClient):
        prompts = PromptLoader()
        loader = build_knowledge_loader(Path(settings.knowledge_dir))
        self.settings = settings
        self.llm = llm
        self.prompts = prompts
        self.keyword_retriever = KeywordRetriever(loader)
        self.vector_store = LocalVectorStore(Path(settings.rag_index_path))
        self.vector_retriever = VectorRetriever(self.vector_store, build_embedding_client(settings))
        self.fact_summarizer = FactSummarizer(llm, prompts)
        self.topic_classifier = TopicClassifier()
        self.opinion_generator = OpinionGenerator(llm, prompts)
        self.style_service = StyleService()
        self.domain_service = ZhihuDomainService()

    def generate(self, request: GenerateZhihuAnswerRequest) -> GenerateZhihuAnswerResponse:
        fact_summary = self.fact_summarizer.summarize(request.topic, request.context_text)
        classification = self.topic_classifier.classify(request.topic, request.context_text, fact_summary)
        requested_style = request.style or request.persona
        style, style_notes = self.style_service.resolve_style(
            account_id=request.account_id,
            requested_style=requested_style,
            classification=classification,
        )
        classification.risk_notes.extend(style_notes)
        retrieved = self._retrieve(request.topic + " " + request.context_text) if request.use_rag else []
        opinion = self.opinion_generator.generate(fact_summary, retrieved, classification)
        domain_context = self._domain_context(request, classification.category)
        data = complete_json_with_retry(
            llm=self.llm,
            system_prompt=self.prompts.load("system.md"),
            user_prompt=self._build_prompt(request, style, fact_summary, classification, retrieved, opinion, domain_context),
            required_fields=[
                "question_title",
                "answer_title",
                "opening_judgement",
                "background_summary",
                "core_argument",
                "answer_body",
            ],
            defaults=_default_zhihu_output(request.topic, request.question_title),
        )
        return GenerateZhihuAnswerResponse(
            topic=request.topic,
            account_id=request.account_id,
            style=style,
            zhihu_domain=request.zhihu_domain or domain_context["id"],
            fact_summary=fact_summary,
            topic_classification=classification,
            retrieved_knowledge=retrieved,
            opinion=opinion,
            output=ZhihuAnswerOutput(**data),
        )

    def _retrieve(self, query: str):
        vector_results = self.vector_retriever.retrieve(query)
        if vector_results:
            return vector_results
        return self.keyword_retriever.retrieve(query)

    def _domain_context(self, request: GenerateZhihuAnswerRequest, category: str) -> dict:
        if request.zhihu_domain_context:
            return {
                "id": request.zhihu_domain or "custom",
                "text": request.zhihu_domain_context,
            }
        match = self.domain_service.match(request.topic, category)
        profile = match.profile
        return {
            "id": request.zhihu_domain or profile.id,
            "text": "\n".join(
                [
                    f"领域：{profile.name}",
                    f"领域说明：{profile.description}",
                    "推荐角度：" + "；".join(profile.preferred_angles),
                    "避坑点：" + "；".join(profile.avoid_points),
                    f"领域匹配理由：{match.domain_reason}",
                ]
            ),
        }

    def _build_prompt(self, request, style, fact_summary, classification, retrieved, opinion, domain_context) -> str:
        return "\n".join(
            [
                "You are generating a Zhihu answer draft in Chinese.",
                "Return only one JSON object.",
                "Do not fabricate facts. Mark uncertain information as uncertain.",
                "The answer should be explanatory, argumentative, and suitable for human review.",
                "",
                "Required JSON schema:",
                json.dumps(_default_zhihu_output(request.topic, request.question_title), ensure_ascii=False),
                "",
                f"topic: {request.topic}",
                f"question_title: {request.question_title or ''}",
                f"zhihu_domain: {domain_context['id']}",
                f"zhihu_domain_context: {domain_context['text']}",
                f"style: {style}",
                f"emotion_level: {request.emotion_level}",
                f"fact_summary: {fact_summary.model_dump_json(ensure_ascii=False)}",
                f"topic_classification: {classification.model_dump_json(ensure_ascii=False)}",
                f"opinion: {opinion.model_dump_json(ensure_ascii=False)}",
                "retrieved_knowledge:",
                json.dumps([item.model_dump() for item in retrieved], ensure_ascii=False),
            ]
        )


def _default_zhihu_output(topic: str, question_title: str | None = None) -> dict:
    title = question_title or f"如何看待{topic}？"
    return {
        "question_title": title,
        "answer_title": f"{topic}：先把事实和判断分开",
        "opening_judgement": "这个问题值得讨论，但前提是先把已确认事实和情绪判断分开。",
        "background_summary": "目前公开信息仍有限，适合先围绕规则、责任边界和公共表达展开分析。",
        "core_argument": "真正值得追问的不是单一情绪结论，而是事件背后的机制、沟通方式和可验证事实。",
        "supporting_points": ["先确认事实来源", "讨论规则和机制", "避免把猜测写成定论"],
        "counter_arguments": ["如果后续事实反转，观点也需要同步修正"],
        "risk_notes": ["未核实信息不得定性", "避免人身攻击和隐私扩散"],
        "answer_body": "这个问题可以讨论，但不适合在信息不足时直接下定论。更稳妥的写法，是先列出已经确认的事实，再分析争议背后的规则、责任边界和公共表达问题。这样既能保留观点，也能避免把情绪写成事实。",
        "references": [],
    }
