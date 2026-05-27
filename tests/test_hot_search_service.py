from app.core.config import Settings
from app.hot_sources.base import BaseHotSearchProvider, HotSearchItem, HotSearchResponse
from app.services.hot_search_service import HotSearchService


class FakeHotTopicProvider(BaseHotSearchProvider):
    source = "fake_source"

    def __init__(self, platform: str, keywords: list[str]):
        self.platform = platform
        self.keywords = keywords
        self.source = f"{platform}_fake"

    def fetch(self, limit: int = 20) -> HotSearchResponse:
        items = [
            HotSearchItem(
                rank=index + 1,
                original_rank=index + 1,
                keyword=keyword,
                hot_value=str(1000 - index),
                platform=self.platform,
                source=self.source,
                url=f"https://example.com/{self.platform}/{index + 1}",
            )
            for index, keyword in enumerate(self.keywords[:limit])
        ]
        return HotSearchResponse(
            source=self.source,
            platform=self.platform,
            platforms=[self.platform],
            items=items,
        )


def test_hot_search_service_fetches_registered_platform(monkeypatch):
    service = HotSearchService(Settings())
    monkeypatch.setattr(
        service,
        "_provider_for",
        lambda platform: FakeHotTopicProvider(platform, ["平台售后规则引争议"]),
    )

    response = service.get_hot_topics(platform="weibo", limit=1)

    assert response.platform == "weibo"
    assert response.platforms == ["weibo"]
    assert response.items[0].platform == "weibo"
    assert response.items[0].original_rank == 1


def test_hot_search_service_all_keeps_platform_metadata(monkeypatch):
    service = HotSearchService(Settings())
    monkeypatch.setattr(service, "supported_platforms", ("weibo", "zhihu"))
    monkeypatch.setattr(
        service,
        "_provider_for",
        lambda platform: FakeHotTopicProvider(platform, [f"{platform} 热榜话题"]),
    )

    response = service.get_hot_topics(platform="all", limit=10)

    assert response.platform == "all"
    assert response.platforms == ["weibo", "zhihu"]
    assert [item.platform for item in response.items] == ["weibo", "zhihu"]


def test_hot_search_service_all_interleaves_by_original_rank(monkeypatch):
    service = HotSearchService(Settings())
    monkeypatch.setattr(service, "supported_platforms", ("weibo", "baidu"))
    monkeypatch.setattr(
        service,
        "_provider_for",
        lambda platform: FakeHotTopicProvider(platform, [f"{platform} 话题一", f"{platform} 话题二"]),
    )

    response = service.get_hot_topics(platform="all", limit=3)

    assert [item.platform for item in response.items] == ["weibo", "baidu", "weibo"]
    assert [item.original_rank for item in response.items] == [1, 1, 2]


def test_hot_search_service_rejects_unknown_platform():
    service = HotSearchService(Settings())

    try:
        service.get_hot_topics(platform="unknown", limit=1)
    except ValueError as exc:
        assert "Unsupported hot topic platform" in str(exc)
    else:
        raise AssertionError("Expected unknown platform to be rejected.")
