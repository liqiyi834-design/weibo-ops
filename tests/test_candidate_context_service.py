from app.services.candidate_context_service import build_candidate_background_context


def test_build_candidate_background_context_includes_rerank_research():
    context = build_candidate_background_context(
        {
            "recommended_angle": "从规则透明度切入",
            "research_summary": "微博智搜和 Exa 都显示规则细节仍不清楚。",
            "rerank_reason": "背景足够，但需要核验关键条件。",
            "needed_context": ["核验领取规则", "确认是否可叠加"],
            "avoid_points": ["不要替平台做广告"],
            "source_urls": ["https://s.weibo.com/aisearch?q=test", "https://example.com/report"],
        },
        "用户补充：保持克制。",
    )

    assert "用户补充：保持克制。" in context
    assert "候选池背景摘要" in context
    assert "微博智搜和 Exa 都显示" in context
    assert "核验领取规则" in context
    assert "https://s.weibo.com/aisearch?q=test" in context
