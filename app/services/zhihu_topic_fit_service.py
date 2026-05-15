from __future__ import annotations

from dataclasses import dataclass, field

from app.hot_sources.base import HotSearchItem
from app.schemas.comment import HotTopic
from app.services.zhihu_domain_service import ZhihuDomainService


@dataclass(frozen=True)
class ZhihuTopicFit:
    score: float
    reason: str
    question_title: str
    answer_angle: str
    required_research: list[str] = field(default_factory=list)
    domain_scores: dict[str, float] = field(default_factory=dict)
    recommended_domain: str | None = None
    domain_reason: str | None = None


class ZhihuTopicFitService:
    def __init__(self):
        self.domain_service = ZhihuDomainService()

    def evaluate(self, topic: HotTopic | HotSearchItem, category: str, risk_level: str) -> ZhihuTopicFit:
        keyword = topic.keyword
        domain_match = self.domain_service.match(keyword, category)
        score = 35.0
        score += self._rank_bonus(topic.rank)
        score += self._explainability_bonus(keyword, category)
        score += self._evidence_bonus(keyword, category)
        score += self._search_value_bonus(keyword)
        score += min(18.0, domain_match.domain_scores[domain_match.recommended_domain] * 0.18)
        score -= self._pure_gossip_penalty(keyword)
        if risk_level == "high":
            score -= 18
        elif risk_level == "medium":
            score -= 6

        score = round(min(100.0, max(0.0, score)), 2)
        return ZhihuTopicFit(
            score=score,
            reason=self._reason(keyword, category, risk_level, score),
            question_title=self._question_title(keyword),
            answer_angle=self._answer_angle(keyword, category, risk_level, domain_match.profile.preferred_angles),
            required_research=self._required_research(keyword, category, risk_level),
            domain_scores=domain_match.domain_scores,
            recommended_domain=domain_match.recommended_domain,
            domain_reason=domain_match.domain_reason,
        )

    def _rank_bonus(self, rank: int | None) -> float:
        if not rank:
            return 4.0
        return max(0.0, 31 - rank) * 0.45

    def _explainability_bonus(self, keyword: str, category: str) -> float:
        bonus = 0.0
        if any(word in keyword for word in ["为什么", "如何看待", "回应", "争议", "质疑", "道歉", "翻车"]):
            bonus += 18
        if any(word in keyword for word in ["规则", "退款", "售后", "投诉", "维权", "职场", "平台", "消费"]):
            bonus += 18
        if category in {"brand_pr", "social_issue", "gender_issue"}:
            bonus += 14
        if category == "entertainment":
            bonus += 5
        return bonus

    def _evidence_bonus(self, keyword: str, category: str) -> float:
        if category in {"crime_case", "disaster", "political_sensitive", "minor_related"}:
            return 2
        if any(word in keyword for word in ["规则", "平台", "品牌", "政策", "判决", "回应"]):
            return 12
        return 6

    def _search_value_bonus(self, keyword: str) -> float:
        if any(word in keyword for word in ["怎么", "为什么", "如何", "规则", "影响", "原因"]):
            return 12
        return 5

    def _pure_gossip_penalty(self, keyword: str) -> float:
        gossip_words = ["恋情", "机场", "自拍", "生图", "撞衫", "小名", "官宣入行"]
        return 18.0 if any(word in keyword for word in gossip_words) else 0.0

    def _question_title(self, keyword: str) -> str:
        if keyword.startswith("如何看待") or keyword.startswith("为什么"):
            return keyword
        return f"如何看待{keyword}？"

    def _answer_angle(self, keyword: str, category: str, risk_level: str, preferred_angles: list[str]) -> str:
        domain_hint = "；".join(preferred_angles[:3])
        if risk_level == "high":
            return "从公开事实、信息边界和讨论风险切入，避免对个人或案件下定论。"
        if category == "brand_pr":
            return f"从品牌沟通、用户预期和公关失误的机制角度展开。可侧重：{domain_hint}"
        if category == "social_issue":
            return f"从规则设计、普通人体验和平台治理角度展开。可侧重：{domain_hint}"
        if category == "gender_issue":
            return f"从权责分配、社会期待和讨论边界角度展开。可侧重：{domain_hint}"
        if category == "entertainment":
            return f"从作品/节目机制、公众情绪和传播反差角度展开，避免粉圈攻击。可侧重：{domain_hint}"
        return f"围绕“{keyword}”的事实、争议和可验证背景做解释型回答。"

    def _required_research(self, keyword: str, category: str, risk_level: str) -> list[str]:
        items = ["核对至少一个可靠公开来源", "整理事件时间线或背景摘要"]
        if risk_level != "low":
            items.append("标注未核实信息和表达边界")
        if category in {"brand_pr", "social_issue"} or any(word in keyword for word in ["规则", "平台", "售后"]):
            items.append("补充规则条款、平台说明或当事方回应")
        return items

    def _reason(self, keyword: str, category: str, risk_level: str, score: float) -> str:
        parts = []
        if score >= 75:
            parts.append("适合展开成长回答")
        elif score >= 55:
            parts.append("可作为知乎备选题")
        else:
            parts.append("知乎展开价值一般")
        if any(word in keyword for word in ["规则", "平台", "售后", "消费", "职场"]):
            parts.append("有解释空间和搜索长尾价值")
        if any(word in keyword for word in ["争议", "质疑", "回应", "翻车"]):
            parts.append("具备可论证的核心争议")
        if category == "entertainment":
            parts.append("需要避免写成纯吃瓜")
        if risk_level != "low":
            parts.append(f"风险为 {risk_level}，需要更多事实核验")
        return "；".join(parts)
