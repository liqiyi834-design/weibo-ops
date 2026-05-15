from app.services.zhihu_domain_service import ZhihuDomainService


def test_zhihu_domain_service_matches_consumer_domain():
    match = ZhihuDomainService().match("平台售后规则引争议", "social_issue")

    assert match.recommended_domain == "consumer"
    assert match.domain_scores["consumer"] > match.domain_scores["media_culture"]
    assert "平台" in match.domain_reason or "规则" in match.domain_reason


def test_zhihu_domain_service_matches_brand_pr_domain():
    match = ZhihuDomainService().match("某品牌广告文案翻车", "brand_pr")

    assert match.recommended_domain == "brand_pr"
    assert match.profile.preferred_angles
    assert match.profile.avoid_points
