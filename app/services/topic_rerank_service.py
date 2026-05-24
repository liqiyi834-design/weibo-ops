from __future__ import annotations

import json
from collections.abc import Iterable

from app.llm.client import BaseLLMClient, LLMClientError
from app.schemas.comment import RerankedTopic, TopicRerankCandidate, TopicRerankResponse
from app.services.style_service import StyleService


class TopicRerankService:
    def __init__(self, llm: BaseLLMClient | None = None, style_service: StyleService | None = None):
        self.llm = llm
        self.style_service = style_service or StyleService()

    def rerank(
        self,
        candidates: list[TopicRerankCandidate],
        max_results: int = 3,
        account_id: str = "today_direct",
    ) -> TopicRerankResponse:
        if not candidates:
            return TopicRerankResponse(notes=["No candidates to rerank."])

        llm_items = self._llm_rerank(candidates, max_results, account_id) if self.llm else []
        if llm_items:
            selected = llm_items[:max_results]
            selected_keywords = {item.keyword for item in selected}
            rejected = [self._rule_item(candidate, "reject") for candidate in candidates if candidate.keyword not in selected_keywords]
            return TopicRerankResponse(selected=selected, rejected=rejected, llm_used=True)

        ranked = sorted(
            (self._rule_item(candidate) for candidate in candidates),
            key=lambda item: item.final_score,
            reverse=True,
        )
        selected = []
        rejected = []
        for index, item in enumerate(ranked):
            if index < max_results and item.decision != "reject":
                selected.append(item.model_copy(update={"decision": "select"}))
            else:
                rejected.append(item.model_copy(update={"decision": "reject"}))
        return TopicRerankResponse(
            selected=selected,
            rejected=rejected,
            llm_used=False,
            notes=["Used deterministic rerank fallback."],
        )

    def _llm_rerank(
        self,
        candidates: list[TopicRerankCandidate],
        max_results: int,
        account_id: str,
    ) -> list[RerankedTopic]:
        system_prompt = (
            "You are an editor for HotComment-AI. Rerank hot-topic candidates for human-reviewed "
            "Chinese social commentary. Return JSON only."
        )
        account_note = self._account_note(account_id)
        user_prompt = "\n".join(
            [
                "TopicRerankSchema:",
                json.dumps(
                    {
                        "ranked": [
                            {
                                "keyword": "string",
                                "final_score": 0,
                                "decision": "select|backup|reject",
                                "recommended_angle": "string",
                                "reason": "string",
                                "needed_context": ["string"],
                                "risk_notes": ["string"],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                "",
                "Scoring dimensions: factual clarity, source reliability, comment space, risk, account fit, freshness.",
                f"Select at most {max_results} topics. Reject topics with weak or conflicting context.",
                f"Account: {account_id}",
                account_note,
                "Candidates:",
                json.dumps([candidate.model_dump() for candidate in candidates], ensure_ascii=False),
            ]
        )
        try:
            payload = self.llm.generate_json(system_prompt, user_prompt)
        except LLMClientError:
            return []

        raw_items = payload.get("ranked") or payload.get("selected") or []
        if not isinstance(raw_items, list):
            return []

        by_keyword = {candidate.keyword: candidate for candidate in candidates}
        result: list[RerankedTopic] = []
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            keyword = str(raw.get("keyword") or "").strip()
            candidate = by_keyword.get(keyword)
            if not candidate:
                continue
            item = self._rule_item(candidate).model_copy(
                update={
                    "final_score": _clamp_score(raw.get("final_score")),
                    "decision": _coerce_decision(raw.get("decision")),
                    "recommended_angle": str(raw.get("recommended_angle") or candidate.recommended_angle),
                    "reason": str(raw.get("reason") or ""),
                    "needed_context": _string_list(raw.get("needed_context")),
                    "risk_notes": _string_list(raw.get("risk_notes")),
                }
            )
            result.append(item)
        return sorted(result, key=lambda item: item.final_score, reverse=True)

    def _rule_item(self, candidate: TopicRerankCandidate, decision: str | None = None) -> RerankedTopic:
        sources = candidate.research_sources
        score = candidate.original_score * 0.55
        score += min(20.0, len(sources) * 5)
        score += self._credibility_bonus(sources)
        score += self._summary_bonus(sources)
        if candidate.risk_level == "high":
            score -= 18
        elif candidate.risk_level == "medium":
            score -= 6
        if not sources:
            score -= 12

        needed_context = []
        if not sources:
            needed_context.append("补充公开背景来源")
        if candidate.risk_level != "low":
            needed_context.append("核验关键事实和风险边界")

        final_score = round(max(0, min(100, score)), 2)
        resolved_decision = decision or ("select" if final_score >= 70 else "backup" if final_score >= 50 else "reject")
        return RerankedTopic(
            keyword=candidate.keyword,
            final_score=final_score,
            decision=resolved_decision,
            recommended_angle=candidate.recommended_angle,
            risk_level=candidate.risk_level,
            reason=self._rule_reason(candidate, final_score),
            needed_context=needed_context,
            risk_notes=["高风险话题需降温表达"] if candidate.risk_level == "high" else [],
            research_summary=self._research_summary(sources),
            source_urls=[source.url for source in sources if source.url],
        )

    def _account_note(self, account_id: str) -> str:
        try:
            account = self.style_service.get_account(account_id)
        except FileNotFoundError:
            return ""
        return json.dumps(account.model_dump(), ensure_ascii=False)

    def _credibility_bonus(self, sources: Iterable) -> float:
        points = {"high": 10.0, "medium": 6.0, "unknown": 2.0, "low": -4.0}
        return min(18.0, sum(points.get(source.credibility, 0.0) for source in sources))

    def _summary_bonus(self, sources: Iterable) -> float:
        return min(10.0, sum(2.5 for source in sources if source.summary or source.highlights))

    def _rule_reason(self, candidate: TopicRerankCandidate, final_score: float) -> str:
        source_count = len(candidate.research_sources)
        if source_count:
            return f"原始分 {candidate.original_score}，检索到 {source_count} 条背景来源，规则重排分 {final_score}。"
        return f"原始分 {candidate.original_score}，缺少背景来源，规则重排分 {final_score}。"

    def _research_summary(self, sources: list) -> str:
        parts = []
        for source in sources[:3]:
            text = source.summary or " ".join(source.highlights[:2])
            if text:
                parts.append(f"{source.title or source.domain}: {text}")
        return "\n".join(parts)


def _clamp_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0, min(100, score)), 2)


def _coerce_decision(value) -> str:
    if value in {"select", "backup", "reject"}:
        return value
    return "backup"


def _string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
