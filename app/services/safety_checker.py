from app.schemas.comment import CommentOutput, FactSummary, SafetyResult, TopicClassification


class SafetyChecker:
    blocked_terms = ["人肉", "身份证", "手机号", "住址", "去网暴"]
    high_risk_terms = ["骗子", "肯定违法", "一定犯罪", "畜生", "贱", "该死"]

    def check(
        self,
        output: CommentOutput,
        fact_summary: FactSummary,
        classification: TopicClassification,
    ) -> SafetyResult:
        text = " ".join(
            [
                output.one_liner,
                output.short_comment,
                output.emotional_version,
                output.rational_version,
                output.ironic_version,
                " ".join(output.comment_replies),
            ]
        )

        issues: list[str] = []
        if any(term in text for term in self.blocked_terms):
            issues.append("包含隐私扩散或网暴引导风险。")
            return SafetyResult(is_safe=False, risk_level="blocked", issues=issues)

        if any(term in text for term in self.high_risk_terms):
            issues.append("包含未经证实的定性或侮辱性表达。")

        if fact_summary.risk_level == "high" or classification.max_emotion_level <= 4:
            issues.append("高风险话题需要降低情绪强度。")

        if issues:
            revised = CommentOutput(
                one_liner="目前公开信息有限，先把事实边界说清楚。",
                short_comment="这类话题更适合讨论公开信息、规则流程和责任边界，不适合对个人动机或违法事实下定论。",
                emotional_version="可以有情绪，但不能让情绪替代证据。",
                rational_version="更稳妥的写法是列出已确认事实、待确认信息和可讨论的公共议题。",
                ironic_version="慢一点下结论，通常比快一点翻车更划算。",
                comment_replies=["你觉得现在最需要补充哪条事实来源？"],
            )
            return SafetyResult(is_safe=True, risk_level="medium", issues=issues, revised_output=revised)

        return SafetyResult(is_safe=True, risk_level="low", issues=[])
