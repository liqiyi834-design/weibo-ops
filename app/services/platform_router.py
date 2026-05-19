from __future__ import annotations

import json

from app.llm.client import BaseLLMClient, LLMClientError
from app.schemas.comment import PlatformRoutingDecision, PlatformRoutingResponse, TopicAsset


class LLMPlatformRouter:
    def __init__(self, llm: BaseLLMClient):
        self.llm = llm

    def route(self, asset: TopicAsset) -> PlatformRoutingResponse:
        rule_decisions = _rule_based_decisions(asset)
        try:
            llm_decisions = self._llm_decisions(asset, rule_decisions)
        except (LLMClientError, KeyError, TypeError, ValueError):
            return PlatformRoutingResponse(
                topic_asset_id=asset.id,
                llm_used=False,
                decisions=rule_decisions,
            )
        return PlatformRoutingResponse(
            topic_asset_id=asset.id,
            llm_used=True,
            decisions=_merge_with_hard_constraints(asset, llm_decisions),
        )

    def _llm_decisions(
        self,
        asset: TopicAsset,
        rule_decisions: list[PlatformRoutingDecision],
    ) -> list[PlatformRoutingDecision]:
        system_prompt = (
            "你是一个中文内容运营编辑，只做平台分发建议，不自动发布、不自动互动。"
            "你必须尊重风险边界：高风险司法、未成年人、灾难、政治敏感、未核实爆料，"
            "不能推荐情绪化发布。只返回 JSON。"
        )
        user_prompt = "\n".join(
            [
                "PlatformRoutingSchema",
                "请为 TopicAsset 判断适合进入 weibo、zhihu、video 哪些平台池。",
                "必须返回 JSON：{'decisions':[...]}。",
                "每个 decision 必须包含 target_platform、fit_score、decision、reasons、blockers、suggested_angle、required_research。",
                "decision 只能是 recommended、optional、not_recommended。",
                "fit_score 是 0-100。",
                "",
                f"TopicAsset: {asset.model_dump_json(ensure_ascii=False)}",
                f"Rule baseline: {json.dumps([item.model_dump() for item in rule_decisions], ensure_ascii=False)}",
            ]
        )
        data = self.llm.generate_json(system_prompt, user_prompt)
        by_platform = {}
        for item in data["decisions"]:
            decision = PlatformRoutingDecision(topic_asset_id=asset.id, **item)
            by_platform[decision.target_platform] = decision
        return [by_platform[platform] for platform in ["weibo", "zhihu", "video"] if platform in by_platform]


def _rule_based_decisions(asset: TopicAsset) -> list[PlatformRoutingDecision]:
    text = " ".join([asset.canonical_title, asset.summary, " ".join(asset.tags)]).lower()
    hot_signals = asset.hot_signals or {}
    weibo_score = _number(hot_signals.get("weibo_score")) or 55.0
    zhihu_score = _number(hot_signals.get("zhihu_score")) or 50.0
    video_score = 45.0

    if asset.risk_level == "high":
        weibo_score -= 28
        zhihu_score -= 12
        video_score -= 24
    if asset.research_status in {"needed", "none"}:
        zhihu_score -= 12
        video_score -= 8
    if any(word in text for word in ["品牌", "公关", "消费", "规则", "平台", "职场", "维权"]):
        zhihu_score += 18
        weibo_score += 8
    if any(word in text for word in ["明星", "综艺", "电影", "剧集", "粉丝"]):
        weibo_score += 12
        video_score += 8
    if any(word in text for word in ["视觉", "反差", "场景", "视频", "ai"]):
        video_score += 20

    return [
        _decision(
            asset.id,
            "weibo",
            weibo_score,
            ["适合即时讨论和短评表达。"],
            ["高风险话题需要降低情绪强度。"] if asset.risk_level == "high" else [],
            "围绕公共讨论里的冲突点做短判断，保留事实边界。",
            ["补充公开来源"] if asset.research_status in {"needed", "none"} else [],
        ),
        _decision(
            asset.id,
            "zhihu",
            zhihu_score,
            ["适合展开背景、规则和责任分析。"],
            ["资料不足时不建议直接生成长回答。"] if asset.research_status in {"needed", "none"} else [],
            "改写成“如何看待”问题，围绕事实、规则、影响展开。",
            ["补充来源链接", "整理关键事实时间线"] if asset.research_status in {"needed", "none"} else [],
        ),
        _decision(
            asset.id,
            "video",
            video_score,
            ["可评估是否具备视觉化、反差或栏目化表达空间。"],
            ["公共事件和真人相关内容需要避免误导性画面。"] if asset.risk_level != "low" else [],
            "仅在能转化为非误导性创意提示词时进入视频创意池。",
            ["明确画面边界和不可生成内容"] if asset.risk_level != "low" else [],
        ),
    ]


def _merge_with_hard_constraints(
    asset: TopicAsset,
    decisions: list[PlatformRoutingDecision],
) -> list[PlatformRoutingDecision]:
    existing = {item.target_platform: item for item in decisions}
    rule_fallback = {item.target_platform: item for item in _rule_based_decisions(asset)}
    merged = []
    for platform in ["weibo", "zhihu", "video"]:
        item = existing.get(platform) or rule_fallback[platform]
        if asset.risk_level == "high" and platform in {"weibo", "video"}:
            item.fit_score = min(item.fit_score, 60)
            item.decision = "optional" if item.fit_score >= 45 else "not_recommended"
            blocker = "高风险话题必须人工复核，不能情绪化表达或自动发布。"
            if blocker not in item.blockers:
                item.blockers.append(blocker)
        if asset.research_status in {"needed", "none"} and platform == "zhihu":
            item.decision = "optional" if item.decision == "recommended" else item.decision
            research = "补充可靠来源后再生成长回答"
            if research not in item.required_research:
                item.required_research.append(research)
        merged.append(item)
    return merged


def _decision(
    asset_id: str,
    platform: str,
    score: float,
    reasons: list[str],
    blockers: list[str],
    angle: str,
    required_research: list[str],
) -> PlatformRoutingDecision:
    fit_score = min(100.0, max(0.0, round(score, 2)))
    decision = "recommended" if fit_score >= 75 else "optional" if fit_score >= 55 else "not_recommended"
    return PlatformRoutingDecision(
        topic_asset_id=asset_id,
        target_platform=platform,
        fit_score=fit_score,
        decision=decision,
        reasons=reasons,
        blockers=blockers,
        suggested_angle=angle,
        required_research=required_research,
    )


def _number(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
