from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ZhihuDomainProfile:
    id: str
    name: str
    description: str
    keywords: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    preferred_angles: list[str] = field(default_factory=list)
    avoid_points: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ZhihuDomainMatch:
    recommended_domain: str
    domain_name: str
    domain_reason: str
    domain_scores: dict[str, float]
    profile: ZhihuDomainProfile


class ZhihuDomainService:
    def __init__(self, config_path: Path | str = Path("configs/zhihu_domains.json")):
        self.config_path = Path(config_path)
        self._profiles = self._load_profiles()

    def list_profiles(self) -> list[ZhihuDomainProfile]:
        return self._profiles

    def match(self, keyword: str, category: str) -> ZhihuDomainMatch:
        scores = {
            profile.id: self._score_profile(keyword, category, profile)
            for profile in self._profiles
        }
        if not scores:
            fallback = self._fallback_profile()
            return ZhihuDomainMatch(
                recommended_domain=fallback.id,
                domain_name=fallback.name,
                domain_reason="未配置领域，使用通用解释型回答。",
                domain_scores={fallback.id: 40.0},
                profile=fallback,
            )

        recommended_id = max(scores, key=scores.get)
        profile = next(item for item in self._profiles if item.id == recommended_id)
        return ZhihuDomainMatch(
            recommended_domain=profile.id,
            domain_name=profile.name,
            domain_reason=self._reason(keyword, category, profile, scores[profile.id]),
            domain_scores={key: round(value, 2) for key, value in scores.items()},
            profile=profile,
        )

    def _load_profiles(self) -> list[ZhihuDomainProfile]:
        if not self.config_path.exists():
            return [self._fallback_profile()]
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        return [ZhihuDomainProfile(**item) for item in data]

    def _score_profile(self, keyword: str, category: str, profile: ZhihuDomainProfile) -> float:
        score = 20.0
        keyword_hits = [word for word in profile.keywords if word in keyword]
        score += min(45.0, len(keyword_hits) * 12.0)
        if category in profile.categories:
            score += 30.0
        if keyword_hits and category in profile.categories:
            score += 10.0
        return min(100.0, score)

    def _reason(self, keyword: str, category: str, profile: ZhihuDomainProfile, score: float) -> str:
        hits = [word for word in profile.keywords if word in keyword]
        parts = [f"推荐领域：{profile.name}"]
        if hits:
            parts.append("命中关键词：" + "、".join(hits[:5]))
        if category in profile.categories:
            parts.append(f"话题分类 {category} 与领域匹配")
        if score < 45:
            parts.append("领域匹配较弱，建议人工确认是否适合该知乎账号")
        return "；".join(parts)

    def _fallback_profile(self) -> ZhihuDomainProfile:
        return ZhihuDomainProfile(
            id="general",
            name="通用解释型回答",
            description="用于未命中明确垂直领域的话题。",
            preferred_angles=["事实梳理", "争议拆解", "表达边界"],
            avoid_points=["不要编造事实", "不要过度定性"],
        )
