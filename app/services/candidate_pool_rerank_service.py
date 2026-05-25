from __future__ import annotations

from app.core.config import Settings
from app.llm.client import BaseLLMClient
from app.schemas.comment import (
    ResearchSource,
    RerankedTopic,
    SelectedTopic,
    TopicRerankCandidate,
    TopicRerankResponse,
)
from app.services.exa_research_service import ExaResearchService
from app.services.topic_rerank_service import TopicRerankService
from app.services.weibo_aisearch_research_service import WeiboAiSearchResearchService


class CandidatePoolRerankService:
    def __init__(
        self,
        settings: Settings,
        llm: BaseLLMClient | None = None,
        exa_service: ExaResearchService | None = None,
        weibo_aisearch_service: WeiboAiSearchResearchService | None = None,
        rerank_service: TopicRerankService | None = None,
    ):
        self.settings = settings
        self.exa_service = exa_service or ExaResearchService(settings)
        self.weibo_aisearch_service = weibo_aisearch_service or WeiboAiSearchResearchService(settings)
        self.rerank_service = rerank_service or TopicRerankService(llm)

    def rerank_selected(
        self,
        selected: list[SelectedTopic],
        max_results: int,
        research_limit: int = 5,
        sources_per_topic: int = 3,
        account_id: str = "today_direct",
        use_weibo_aisearch: bool = True,
    ) -> tuple[list[SelectedTopic], list[str]]:
        if not selected:
            return [], ["没有可重排的候选话题。"]

        notes: list[str] = []
        research_by_keyword = self._research_sources(
            selected,
            research_limit,
            sources_per_topic,
            notes,
            use_weibo_aisearch=use_weibo_aisearch,
        )
        candidates = [
            self._to_rerank_candidate(item, research_by_keyword.get(item.keyword, []))
            for item in selected
        ]
        rerank_response = self.rerank_service.rerank(
            candidates=candidates,
            max_results=max_results,
            account_id=account_id,
        )
        updated = self._apply_rerank(selected, rerank_response)
        notes.extend(rerank_response.notes)
        notes.append(
            "背景检索重排已应用："
            f"检索 {min(len(selected), research_limit)} 个候选，"
            f"Exa 每个最多 {sources_per_topic} 个来源，"
            f"微博智搜={'yes' if use_weibo_aisearch else 'no'}，"
            f"LLM={'yes' if rerank_response.llm_used else 'no'}。"
        )
        if rerank_response.rejected:
            notes.append(f"重排后过滤/降级 {len(rerank_response.rejected)} 个候选。")
        return updated, _dedupe(notes)

    def _research_sources(
        self,
        selected: list[SelectedTopic],
        research_limit: int,
        sources_per_topic: int,
        notes: list[str],
        use_weibo_aisearch: bool,
    ) -> dict[str, list[ResearchSource]]:
        research_by_keyword: dict[str, list[ResearchSource]] = {}
        for index, item in enumerate(selected):
            if index >= research_limit:
                break
            sources: list[ResearchSource] = []
            if use_weibo_aisearch:
                weibo_response = self.weibo_aisearch_service.research_topic_sources(
                    topic=item.keyword,
                    max_polls=3,
                    poll_interval_seconds=1.0,
                )
                if weibo_response.notes:
                    notes.extend(f"{item.keyword} / 微博智搜: {note}" for note in weibo_response.notes)
                sources.extend(weibo_response.sources)
            response = self.exa_service.research_topic_sources(
                topic=item.keyword,
                limit=sources_per_topic,
            )
            if response.notes:
                notes.extend(f"{item.keyword} / Exa: {note}" for note in response.notes)
            sources.extend(response.sources)
            research_by_keyword[item.keyword] = _dedupe_sources(sources)
            if not response.is_configured:
                notes.append("Exa 未配置，已退回无网页资料的重排评分。")
        return research_by_keyword

    def _to_rerank_candidate(
        self,
        item: SelectedTopic,
        sources: list[ResearchSource],
    ) -> TopicRerankCandidate:
        return TopicRerankCandidate(
            keyword=item.keyword,
            original_score=item.score,
            reason=item.reason,
            recommended_angle=item.recommended_angle,
            risk_level=item.risk_level,
            category=item.category,
            hot_value=item.hot_value,
            rank=item.rank,
            label=item.label,
            category_label=item.category_label,
            url=item.url,
            research_sources=sources,
        )

    def _apply_rerank(
        self,
        selected: list[SelectedTopic],
        response: TopicRerankResponse,
    ) -> list[SelectedTopic]:
        by_keyword = {item.keyword: item for item in selected}
        reranked_items = response.selected or []
        updated: list[SelectedTopic] = []
        for reranked in reranked_items:
            original = by_keyword.get(reranked.keyword)
            if not original:
                continue
            updated.append(self._merge_topic(original, reranked, response.llm_used))
        return updated or selected

    def _merge_topic(
        self,
        original: SelectedTopic,
        reranked: RerankedTopic,
        llm_used: bool,
    ) -> SelectedTopic:
        target_scores = dict(original.target_platform_scores)
        target_scores["weibo"] = reranked.final_score
        avoid_points = _dedupe(
            [
                *original.avoid_points,
                *reranked.needed_context,
                *reranked.risk_notes,
            ]
        )
        reason_parts = [f"背景检索重排：{reranked.reason}".strip()]
        if original.reason:
            reason_parts.append(f"原始理由：{original.reason}")
        reason = "\n".join(part for part in reason_parts if part)
        return original.model_copy(
            update={
                "score": reranked.final_score,
                "risk_level": reranked.risk_level,
                "reason": reason,
                "recommended_angle": reranked.recommended_angle or original.recommended_angle,
                "avoid_points": avoid_points,
                "target_platform_scores": target_scores,
                "rerank_score": reranked.final_score,
                "rerank_decision": reranked.decision,
                "rerank_reason": reranked.reason,
                "needed_context": reranked.needed_context,
                "research_summary": reranked.research_summary,
                "source_urls": reranked.source_urls,
                "llm_reranked": llm_used,
            }
        )


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _dedupe_sources(sources: list[ResearchSource]) -> list[ResearchSource]:
    result: list[ResearchSource] = []
    seen: set[str] = set()
    for source in sources:
        key = source.url or f"{source.domain}:{source.title}"
        if key and key not in seen:
            result.append(source)
            seen.add(key)
    return result
