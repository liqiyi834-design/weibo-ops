from app.schemas.comment import CommentOutput, FactSummary, TopicClassification
from app.services.safety_checker import SafetyChecker


def test_safety_checker_rewrites_high_risk_terms():
    output = CommentOutput(
        one_liner="这家公司肯定违法。",
        short_comment="这家公司肯定违法，太离谱。",
        emotional_version="骗子。",
        rational_version="需要查证。",
        ironic_version="无。",
        comment_replies=[],
    )
    result = SafetyChecker().check(
        output,
        FactSummary(topic="测试", risk_level="low"),
        TopicClassification(category="brand_pr", max_emotion_level=7),
    )

    assert result.is_safe is True
    assert result.risk_level == "medium"
    assert result.revised_output is not None


def test_safety_checker_blocks_privacy_and_mob_terms():
    output = CommentOutput(
        one_liner="去人肉他。",
        short_comment="去人肉他。",
        emotional_version="去网暴。",
        rational_version="无。",
        ironic_version="无。",
        comment_replies=[],
    )
    result = SafetyChecker().check(
        output,
        FactSummary(topic="测试", risk_level="low"),
        TopicClassification(),
    )

    assert result.is_safe is False
    assert result.risk_level == "blocked"
