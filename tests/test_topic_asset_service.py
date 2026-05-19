from pathlib import Path
from uuid import uuid4

from app.schemas.comment import TopicAssetCreateRequest, TopicAssetUpdateRequest
from app.llm.client import MockLLMClient
from app.services.platform_router import LLMPlatformRouter
from app.services.topic_asset_service import TopicAssetService


def test_topic_asset_service_creates_lists_gets_and_updates():
    test_root = Path(".rag_index") / f"topic-asset-test-{uuid4().hex}"
    service = TopicAssetService(root=test_root)

    asset = service.create(
        TopicAssetCreateRequest(
            canonical_title="某品牌文案翻车",
            summary="品牌文案被质疑表达不当。",
            source_platforms=["weibo", "weibo"],
            source_urls=["https://example.com/a"],
            hot_signals={"rank": 2, "weibo_score": 92.5},
            tags=["brand_pr", "brand_pr"],
            risk_level="low",
            research_status="needed",
            status="candidate",
        )
    )
    summaries = service.list_assets()
    loaded = service.get(asset.id)
    updated = service.update(
        asset.id,
        TopicAssetUpdateRequest(status="researched", research_status="complete"),
    )

    assert asset.id
    assert asset.source_platforms == ["weibo"]
    assert asset.tags == ["brand_pr"]
    assert summaries[0].id == asset.id
    assert loaded.canonical_title == "某品牌文案翻车"
    assert updated.status == "researched"
    assert updated.research_status == "complete"


def test_llm_platform_router_returns_human_review_decisions():
    test_root = Path(".rag_index") / f"topic-routing-test-{uuid4().hex}"
    service = TopicAssetService(root=test_root)
    asset = service.create(
        TopicAssetCreateRequest(
            canonical_title="平台售后规则引争议",
            summary="争议集中在规则解释、售后责任和消费者体验。",
            source_platforms=["weibo"],
            hot_signals={"weibo_score": 88, "zhihu_score": 76},
            tags=["consumer"],
            risk_level="low",
            research_status="needed",
            status="candidate",
        )
    )

    result = LLMPlatformRouter(MockLLMClient()).route(asset)

    assert result.topic_asset_id == asset.id
    assert result.llm_used is True
    assert {item.target_platform for item in result.decisions} == {"weibo", "zhihu", "video"}
    assert result.decisions[0].decision in {"recommended", "optional", "not_recommended"}
    assert all(item.suggested_angle for item in result.decisions)


def test_llm_platform_router_keeps_high_risk_constraints():
    test_root = Path(".rag_index") / f"topic-routing-risk-test-{uuid4().hex}"
    service = TopicAssetService(root=test_root)
    asset = service.create(
        TopicAssetCreateRequest(
            canonical_title="法院回应案件争议",
            summary="司法相关公共事件，需要谨慎表达。",
            source_platforms=["weibo"],
            risk_level="high",
            research_status="needed",
            status="candidate",
        )
    )

    result = LLMPlatformRouter(MockLLMClient()).route(asset)
    by_platform = {item.target_platform: item for item in result.decisions}

    assert by_platform["weibo"].fit_score <= 60
    assert by_platform["weibo"].decision != "recommended"
    assert by_platform["video"].fit_score <= 60
    assert by_platform["video"].decision != "recommended"
