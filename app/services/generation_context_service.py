from __future__ import annotations

from app.schemas.comment import (
    GenerationContextRequest,
    GenerationContextResponse,
    ResearchSource,
    RetrievedKnowledge,
)


class GenerationContextService:
    def build(self, request: GenerationContextRequest) -> GenerationContextResponse:
        source_urls = [source.url for source in request.research_sources if source.url]
        needs_verification = self._needs_verification(request)
        sections = [
            f"# Generation Context: {request.topic}",
            "",
            "## Exa 临时背景",
            self._research_section(request.research_sources[: request.max_sources]),
            "",
            "## RAG 编辑记忆",
            self._rag_section(request.rag_results[: request.max_rag_items]),
            "",
            "## 选题判断",
            self._rerank_section(request),
            "",
            "## 风险与生成约束",
            self._constraint_section(request, needs_verification),
        ]
        notes = []
        if not request.research_sources:
            notes.append("No Exa research sources were provided.")
        if not request.rag_results:
            notes.append("No RAG results were provided.")
        return GenerationContextResponse(
            topic=request.topic,
            context_text="\n".join(sections).strip() + "\n",
            source_urls=source_urls,
            needs_verification=needs_verification,
            notes=notes,
        )

    def _research_section(self, sources: list[ResearchSource]) -> str:
        if not sources:
            return "- 暂无 Exa 背景来源；不要编造具体事实。"
        lines = []
        for index, source in enumerate(sources, 1):
            summary = source.summary or " ".join(source.highlights[:2]) or "无摘要"
            lines.extend(
                [
                    f"{index}. {source.title or source.domain or source.url}",
                    f"   - URL: {source.url}",
                    f"   - Domain: {source.domain or 'unknown'}",
                    f"   - Credibility: {source.credibility}",
                    f"   - Published: {source.published_date or 'unknown'}",
                    f"   - Summary: {_compact(summary)}",
                ]
            )
        return "\n".join(lines)

    def _rag_section(self, results: list[RetrievedKnowledge]) -> str:
        if not results:
            return "- 暂无本地 RAG 结果；仅可使用 Exa 临时背景和通用安全规则。"
        lines = []
        for index, item in enumerate(results, 1):
            score = "" if item.score is None else f" score={round(item.score, 4)}"
            lines.extend(
                [
                    f"{index}. Source: {item.source}{score}",
                    f"   - Content: {_compact(item.content, limit=420)}",
                ]
            )
        return "\n".join(lines)

    def _rerank_section(self, request: GenerationContextRequest) -> str:
        if not request.reranked_topic:
            return "- 暂无重排结果；按候选原始信息谨慎生成。"
        item = request.reranked_topic
        lines = [
            f"- Final score: {item.final_score}",
            f"- Decision: {item.decision}",
            f"- Recommended angle: {item.recommended_angle or '未提供'}",
            f"- Reason: {item.reason or '未提供'}",
        ]
        if item.research_summary:
            lines.append(f"- Research summary: {_compact(item.research_summary, limit=500)}")
        if item.needed_context:
            lines.append("- Needed context: " + "；".join(item.needed_context))
        if item.risk_notes:
            lines.append("- Risk notes: " + "；".join(item.risk_notes))
        return "\n".join(lines)

    def _constraint_section(self, request: GenerationContextRequest, needs_verification: list[str]) -> str:
        lines = []
        if request.classification:
            lines.extend(
                [
                    f"- Category: {request.classification.category}",
                    f"- Recommended persona: {request.classification.recommended_persona}",
                    f"- Max emotion level: {request.classification.max_emotion_level}",
                ]
            )
            if request.classification.risk_notes:
                lines.append("- Classification risk notes: " + "；".join(request.classification.risk_notes))
        if request.reranked_topic:
            lines.append(f"- Rerank risk level: {request.reranked_topic.risk_level}")
        if needs_verification:
            lines.append("- 需要核验: " + "；".join(needs_verification))
        lines.extend(
            [
                "- 不要把 Exa 摘要写成已核实结论；缺少 A/B 级来源时要保守表述。",
                "- 不要自动发布，不要引导网暴，不要输出隐私信息。",
                "- 先写事实边界，再给观点；中高风险话题要降温。",
            ]
        )
        return "\n".join(lines)

    def _needs_verification(self, request: GenerationContextRequest) -> list[str]:
        items: list[str] = []
        if request.reranked_topic:
            items.extend(request.reranked_topic.needed_context)
        if not request.research_sources:
            items.append("补充公开背景来源")
        if request.research_sources and not any(source.credibility in {"medium", "high"} for source in request.research_sources):
            items.append("当前来源可信度不足，需要人工核验")
        if request.reranked_topic and request.reranked_topic.risk_level != "low":
            items.append("核验风险话题的关键事实和表达边界")
        return list(dict.fromkeys(item for item in items if item))


def _compact(text: str, limit: int = 280) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "..."
