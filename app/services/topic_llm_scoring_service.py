from __future__ import annotations

import json
from dataclasses import dataclass

from app.llm.client import BaseLLMClient
from app.schemas.comment import SelectedTopic
from app.services.style_service import StyleService


@dataclass(frozen=True)
class TopicLLMScore:
    keyword: str
    score: float
    reason: str
    recommended_angle: str
    needed_context: list[str]


class TopicLLMScoringService:
    def __init__(self, llm: BaseLLMClient, style_service: StyleService | None = None):
        self.llm = llm
        self.style_service = style_service or StyleService()

    def score(
        self,
        candidates: list[SelectedTopic],
        max_results: int,
        account_id: str = "today_direct",
    ) -> dict[str, TopicLLMScore]:
        if not candidates:
            return {}

        system_prompt = (
            "You are an editor for HotComment-AI. Score Weibo hot-topic candidates for "
            "human-reviewed Chinese social commentary. Return JSON only."
        )
        user_prompt = "\n".join(
            [
                "TopicSelectionScoringSchema:",
                json.dumps(
                    {
                        "items": [
                            {
                                "keyword": "string",
                                "weibo_score": 0,
                                "reason": "string",
                                "recommended_angle": "string",
                                "needed_context": ["string"],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                "",
                "Score each candidate from 0 to 100 for Weibo short commentary.",
                "Use the rule score only as a baseline; prefer judgment about comment space, freshness, factual clarity, risk, and account fit.",
                "Do not reward pure promotion, unclear claims, or topics that need major verification.",
                f"Return all {len(candidates)} candidates. The caller will select at most {max_results}.",
                f"Account: {account_id}",
                self._account_note(account_id),
                "Candidates:",
                json.dumps([self._candidate_payload(item) for item in candidates], ensure_ascii=False),
            ]
        )

        try:
            payload = self.llm.generate_json(system_prompt, user_prompt)
        except Exception as exc:
            raise ValueError(f"LLM topic scoring failed: {exc}") from exc

        if not isinstance(payload, dict):
            raise ValueError("LLM topic scoring returned a non-object payload.")
        raw_items = payload.get("items") or payload.get("ranked") or payload.get("selected")
        if not isinstance(raw_items, list):
            raise ValueError("LLM topic scoring returned no item list.")

        candidate_keywords = {item.keyword for item in candidates}
        scores: dict[str, TopicLLMScore] = {}
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            keyword = str(raw.get("keyword") or "").strip()
            if keyword not in candidate_keywords:
                continue
            scores[keyword] = TopicLLMScore(
                keyword=keyword,
                score=_clamp_score(raw.get("weibo_score", raw.get("score", raw.get("final_score")))),
                reason=str(raw.get("reason") or "").strip(),
                recommended_angle=str(raw.get("recommended_angle") or "").strip(),
                needed_context=_string_list(raw.get("needed_context")),
            )

        if set(scores) != candidate_keywords:
            missing = sorted(candidate_keywords - set(scores))
            raise ValueError(f"LLM topic scoring missed candidates: {missing[:3]}")
        return scores

    def _candidate_payload(self, item: SelectedTopic) -> dict:
        return {
            "keyword": item.keyword,
            "rank": item.rank,
            "hot_value": item.hot_value,
            "label": item.label,
            "category_label": item.category_label,
            "category": item.category,
            "risk_level": item.risk_level,
            "base_score": item.base_score if item.base_score is not None else item.score,
            "rule_reason": item.reason,
            "recommended_angle": item.recommended_angle,
            "platform": item.platform,
            "source": item.source,
            "metrics": {
                "read_count": item.read_count,
                "discussion_count": item.discussion_count,
                "sampled_posts_count": item.sampled_posts_count,
                "controversy_score": item.controversy_score,
            },
        }

    def _account_note(self, account_id: str) -> str:
        try:
            account = self.style_service.get_account(account_id)
        except FileNotFoundError:
            return ""
        return json.dumps(account.model_dump(), ensure_ascii=False)


def _clamp_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        raise ValueError("LLM topic score is not numeric.")
    return round(max(0, min(100, score)), 2)


def _string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
