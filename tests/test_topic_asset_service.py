from pathlib import Path
from uuid import uuid4

from app.schemas.comment import TopicAssetCreateRequest, TopicAssetUpdateRequest
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
