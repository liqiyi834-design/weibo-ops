from __future__ import annotations

import re

from app.hot_sources.base import HotSearchItem
from app.llm.client import BaseLLMClient
from app.schemas.comment import FactSummary, HotTopic, SelectedTopic, TopicSelectionResponse
from app.services.topic_classifier import TopicClassifier
from app.services.topic_llm_scoring_service import TopicLLMScoringService, TopicLLMScore
from app.services.zhihu_topic_fit_service import ZhihuTopicFitService


class TopicSelectionService:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.classifier = TopicClassifier()
        self.zhihu_fit = ZhihuTopicFitService()
        self.llm_scorer = TopicLLMScoringService(llm) if llm else None

    def select(
        self,
        topics: list[HotTopic | HotSearchItem],
        max_results: int = 5,
        account_id: str = "today_direct",
    ) -> TopicSelectionResponse:
        evaluated = [self._evaluate(topic) for topic in topics if topic.keyword.strip()]
        notes = [
            "推荐结果只用于选题决策，最终选题由人工确认。",
            "风险边界和商业推广封顶规则作为安全约束，最终选题由人工确认。",
        ]
        if self.llm_scorer:
            try:
                llm_scores = self.llm_scorer.score(evaluated, max_results=max_results, account_id=account_id)
            except ValueError as exc:
                notes.append(f"LLM 选题评分不可用，已回退规则分：{exc}")
            else:
                evaluated = [self._apply_llm_score(item, llm_scores[item.keyword]) for item in evaluated]
                notes.append("LLM 选题评分已应用，规则分作为基线和安全封顶。")
        else:
            notes.append("未配置真实 LLM，使用规则评分。")
        selected = sorted(evaluated, key=lambda item: item.score, reverse=True)[:max_results]
        return TopicSelectionResponse(
            source=self._source_name(topics),
            evaluated_count=len(evaluated),
            selected=selected,
            notes=notes,
        )

    def _evaluate(self, topic: HotTopic | HotSearchItem) -> SelectedTopic:
        fact_summary = FactSummary(topic=topic.keyword)
        classification = self.classifier.classify(topic.keyword, "", fact_summary)
        risk_level = self._risk_level(classification.category, topic.keyword)
        score = self._score(topic, classification.category, risk_level)
        reason = self._reason(topic, classification.category, risk_level)
        zhihu_fit = self.zhihu_fit.evaluate(topic, classification.category, risk_level)
        recommended_targets = self._recommended_targets(score, zhihu_fit.score, risk_level)
        return SelectedTopic(
            rank=topic.rank,
            original_rank=getattr(topic, "original_rank", None) or topic.rank,
            keyword=topic.keyword,
            score=round(score, 2),
            base_score=round(score, 2),
            category=classification.category,
            risk_level=risk_level,
            reason=reason,
            recommended_angle=self._recommended_angle(topic.keyword, classification.category, risk_level),
            avoid_points=self._avoid_points(classification.category, risk_level),
            hot_value=topic.hot_value,
            category_label=getattr(topic, "category_label", None),
            read_count=getattr(topic, "read_count", None),
            discussion_count=getattr(topic, "discussion_count", None),
            sampled_posts_count=getattr(topic, "sampled_posts_count", None),
            controversy_score=getattr(topic, "controversy_score", None),
            label=getattr(topic, "label", None),
            url=topic.url,
            platform=getattr(topic, "platform", None) or "manual",
            source=topic.source,
            target_platform_scores={
                "weibo": round(score, 2),
                "zhihu": zhihu_fit.score,
            },
            recommended_targets=recommended_targets,
            zhihu_question_title=zhihu_fit.question_title,
            zhihu_answer_angle=zhihu_fit.answer_angle,
            zhihu_required_research=zhihu_fit.required_research,
            zhihu_reason=zhihu_fit.reason,
            zhihu_domain_scores=zhihu_fit.domain_scores,
            zhihu_recommended_domain=zhihu_fit.recommended_domain,
            zhihu_domain_reason=zhihu_fit.domain_reason,
        )

    def _apply_llm_score(self, item: SelectedTopic, llm_score: TopicLLMScore) -> SelectedTopic:
        final_score = self._apply_score_caps(llm_score.score, item)
        target_scores = dict(item.target_platform_scores)
        target_scores["weibo"] = final_score
        base_score = item.base_score if item.base_score is not None else item.score
        reason_parts = []
        if llm_score.reason:
            reason_parts.append(f"LLM评分：{llm_score.reason}")
        if item.reason:
            reason_parts.append(f"规则基线：{item.reason}")
        return item.model_copy(
            update={
                "score": final_score,
                "base_score": base_score,
                "llm_score": final_score,
                "llm_scored": True,
                "reason": "\n".join(reason_parts) or item.reason,
                "recommended_angle": llm_score.recommended_angle or item.recommended_angle,
                "needed_context": _dedupe([*item.needed_context, *llm_score.needed_context]),
                "target_platform_scores": target_scores,
                "recommended_targets": self._recommended_targets(
                    final_score,
                    item.target_platform_scores.get("zhihu", 0),
                    item.risk_level,
                ),
            }
        )

    def _apply_score_caps(self, score: float, item: SelectedTopic) -> float:
        signal = self._commercial_promotion_signal(item.keyword, item)
        if signal == "explicit":
            score = min(score, 65)
        elif signal == "implicit":
            score = min(score, 70)
        elif signal == "light":
            score = min(score, 78)
        return round(max(0, min(100, score)), 2)

    def _recommended_targets(self, weibo_score: float, zhihu_score: float, risk_level: str) -> list[str]:
        targets = []
        if weibo_score >= 70:
            targets.append("weibo")
        if zhihu_score >= 65:
            targets.append("zhihu")
        if not targets and risk_level != "high":
            targets.append("weibo" if weibo_score >= zhihu_score else "zhihu")
        return targets

    def _score(self, topic: HotTopic | HotSearchItem, category: str, risk_level: str) -> float:
        score = 40.0
        if topic.rank:
            score += max(0, 51 - topic.rank) * 0.55

        hot_number = self._hot_number(topic.hot_value)
        if hot_number:
            score += min(16.0, hot_number / 120000)

        score += self._metric_bonus(topic)

        label = getattr(topic, "label", None) or ""
        label_bonus = {"爆": 18, "沸": 14, "热": 10, "新": 8, "荐": -4}
        score += label_bonus.get(label, 0)

        score += self._keyword_bonus(topic.keyword)
        score -= self._low_comment_space_penalty(topic.keyword)
        score += {
            "brand_pr": 15,
            "social_issue": 14,
            "entertainment": 11,
            "gender_issue": 8,
            "unknown": 0,
            "crime_case": 0,
            "disaster": 0,
            "minor_related": 0,
            "political_sensitive": 0,
        }.get(category, 0)

        commercial_signal = self._commercial_promotion_signal(topic.keyword, topic)
        if commercial_signal == "explicit":
            score -= 28
            score = min(score, 65)
        elif commercial_signal == "implicit":
            score -= 18
            score = min(score, 70)
        elif commercial_signal == "light":
            score -= 8
            score = min(score, 78)

        return min(100.0, max(score, 0))

    def _metric_bonus(self, topic: HotTopic | HotSearchItem) -> float:
        read_count = getattr(topic, "read_count", None)
        discussion_count = getattr(topic, "discussion_count", None)
        sampled_posts_count = getattr(topic, "sampled_posts_count", None)
        controversy_score = getattr(topic, "controversy_score", None)

        bonus = 0.0
        if read_count:
            bonus += min(8.0, read_count / 20000000)
        if discussion_count:
            bonus += min(10.0, discussion_count / 50000)
        if sampled_posts_count:
            bonus += min(5.0, sampled_posts_count / 6)
        if controversy_score is not None:
            bonus += min(8.0, controversy_score / 12.5)
        return bonus

    def _keyword_bonus(self, keyword: str) -> float:
        bonuses = [
            (18, ["翻车", "回应", "道歉", "争议", "质疑"]),
            (14, ["规则", "退款", "售后", "投诉", "维权", "锁电"]),
            (10, ["为什么", "建议", "年轻人", "职场", "消费"]),
            (8, ["综艺", "演唱会", "电影", "明星"]),
        ]
        return sum(points for points, words in bonuses if any(word in keyword for word in words))

    def _low_comment_space_penalty(self, keyword: str) -> float:
        official_words = [
            "习近平",
            "总统",
            "会谈",
            "外交",
            "中方",
            "我国",
            "经济持续向好",
            "先行指标",
            "强烈谴责",
        ]
        if any(word in keyword for word in official_words):
            return 42.0
        return 0.0

    def _commercial_promotion_signal(self, keyword: str, topic: HotTopic | HotSearchItem) -> str | None:
        label = str(getattr(topic, "label", None) or "").strip().lower()
        category_label = str(getattr(topic, "category_label", None) or "").strip().lower()
        if label in {"商", "ad", "ads", "commercial", "promotion", "promoted"}:
            return "explicit"
        if category_label in {"商", "ad", "ads", "commercial", "promotion", "promoted"}:
            return "explicit"

        commercial_words = [
            "红包",
            "优惠券",
            "满减",
            "补贴",
            "大促",
            "促销",
            "618",
            "双11",
            "双十二",
            "开售",
            "预售",
            "直播间",
            "带货",
        ]
        brand_words = [
            "京东",
            "淘宝",
            "天猫",
            "拼多多",
            "抖音商城",
            "美团",
            "饿了么",
            "小红书",
        ]
        if any(word in keyword for word in commercial_words) and any(word in keyword for word in brand_words):
            return "implicit"
        launch_pr_words = ["上市", "新车", "发布", "售价", "价格", "亮相", "焕新", "预订"]
        if any(word in keyword for word in launch_pr_words):
            return "light"
        return None

    def _risk_level(self, category: str, keyword: str) -> str:
        high_words = [
            "习近平",
            "特朗普",
            "访华",
            "外交",
            "总统",
            "会谈",
            "死亡",
            "未成年",
            "偷拍",
            "刑事",
            "法院",
            "判刑",
        ]
        if category in {"political_sensitive", "crime_case", "disaster", "minor_related"}:
            return "high"
        if any(word in keyword for word in high_words):
            return "high"
        medium_words = ["性别", "婚育", "低俗", "隐私", "举报", "网暴"]
        if category == "gender_issue" or any(word in keyword for word in medium_words):
            return "medium"
        return "low"

    def _reason(self, topic: HotTopic | HotSearchItem, category: str, risk_level: str) -> str:
        parts = []
        if topic.rank:
            parts.append(f"热搜排名第 {topic.rank}，时效性强")
        if getattr(topic, "label", None):
            parts.append(f"榜单标记为“{getattr(topic, 'label')}”")
        if self._hot_number(topic.hot_value):
            parts.append(f"热度约 {self._hot_number(topic.hot_value)}")
        metric_parts = self._metric_reason_parts(topic)
        parts.extend(metric_parts)
        parts.extend(self._editor_reason_parts(topic.keyword, category))
        commercial_signal = self._commercial_promotion_signal(topic.keyword, topic)
        if commercial_signal == "explicit":
            parts.append("商业推广标记强，默认降权并转为备选观察")
        elif commercial_signal == "implicit":
            parts.append("疑似大促/红包营销词条，需要先确认是否有真实公共议题")
        elif commercial_signal == "light":
            parts.append("疑似新品发布类 PR 词条，已轻量降权")
        if risk_level != "low":
            parts.append(f"风险等级为 {risk_level}，需要降温表达")
        return "；".join(parts) or "具备基础热度，可作为备选观察题。"

    def _metric_reason_parts(self, topic: HotTopic | HotSearchItem) -> list[str]:
        parts = []
        read_count = getattr(topic, "read_count", None)
        discussion_count = getattr(topic, "discussion_count", None)
        sampled_posts_count = getattr(topic, "sampled_posts_count", None)
        controversy_score = getattr(topic, "controversy_score", None)
        if read_count:
            parts.append(f"阅读量约 {read_count}")
        if discussion_count:
            parts.append(f"讨论量约 {discussion_count}")
        if sampled_posts_count:
            parts.append(f"搜索页采样到 {sampled_posts_count} 条内容")
        if controversy_score is not None:
            parts.append(f"争议度约 {controversy_score}/100")
        return parts

    def _editor_reason_parts(self, keyword: str, category: str) -> list[str]:
        parts = []
        if any(word in keyword for word in ["翻车", "回应", "道歉", "争议", "质疑"]):
            parts.append("有冲突点，容易形成鲜明判断")
        if any(word in keyword for word in ["规则", "退款", "售后", "锁电", "消费", "平台"]):
            parts.append("能落到普通人的规则成本和消费体验")
        if any(word in keyword for word in ["为什么", "建议", "年轻人", "职场", "小环境"]):
            parts.append("适合做生活经验型锐评，互动门槛低")
        if any(word in keyword for word in ["综艺", "演唱会", "明星", "电影", "游戏"]):
            parts.append("文娱属性强，适合用反差和评论区分歧切入")
        if category in {"brand_pr", "social_issue", "entertainment", "gender_issue"}:
            parts.append("与账号锐评风格匹配度较高")
        if not parts:
            parts.append("具备公共讨论入口，但需要先补背景材料")
        return parts

    def _recommended_angle(self, keyword: str, category: str, risk_level: str) -> str:
        if risk_level == "high":
            return "只讨论公开事实、制度边界和责任分工，避免定性个人或扩散未经核实细节。"
        angles = {
            "brand_pr": "从公关边界、用户感受和品牌自救角度切入。",
            "social_issue": "从规则成本、普通人体验和平台治理角度切入。",
            "entertainment": "从粉丝情绪、作品/节目机制和舆论反差角度切入。",
            "gender_issue": "从社会期待、权责分配和公共讨论边界角度切入。",
        }
        return angles.get(category, f"围绕“{keyword}”里的反差点，先做事实核对再给判断。")

    def _avoid_points(self, category: str, risk_level: str) -> list[str]:
        avoid = ["不要编造事实", "不要引导网暴", "不要自动发布"]
        if risk_level == "high":
            avoid.extend(["不要定罪", "不要曝光隐私", "不要使用侮辱性标签"])
        if category == "gender_issue":
            avoid.append("不要扩大到性别群体攻击")
        if category == "entertainment":
            avoid.append("不要攻击粉丝群体")
        return avoid

    def _hot_number(self, value: str | None) -> int | None:
        if not value:
            return None
        matches = re.findall(r"\d+", value)
        if not matches:
            return None
        return int(matches[-1])

    def _source_name(self, topics: list[HotTopic | HotSearchItem]) -> str:
        sources = {topic.source for topic in topics if topic.source}
        if len(sources) == 1:
            return next(iter(sources))
        return "mixed" if sources else "manual"


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
