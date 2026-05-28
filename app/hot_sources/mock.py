from collections.abc import Callable

from app.hot_sources.base import (
    BaseHotSearchProvider,
    HotSearchItem,
    HotSearchResponse,
    build_baidu_search_url,
    build_weibo_search_url,
    build_zhihu_search_url,
)


class MockHotSearchProvider(BaseHotSearchProvider):
    source = "mock_weibo"
    platform = "weibo"

    def __init__(
        self,
        platform: str = "weibo",
        source: str | None = None,
        keywords: list[str] | None = None,
        url_builder: Callable[[str], str] | None = None,
    ):
        self.platform = platform
        self.source = source or f"mock_{platform}"
        self.keywords = keywords
        if url_builder:
            self.url_builder = url_builder
        elif platform == "baidu":
            self.url_builder = build_baidu_search_url
        elif platform == "zhihu":
            self.url_builder = build_zhihu_search_url
        else:
            self.url_builder = build_weibo_search_url

    def fetch(self, limit: int = 20) -> HotSearchResponse:
        keywords = self.keywords or [
            "某品牌母亲节文案翻车",
            "平台售后规则引争议",
            "年轻人为什么不爱加班",
            "热门综艺嘉宾阵容官宣",
            "食品安全通报",
            "假期消费避坑指南",
        ]
        items = [
            HotSearchItem(
                rank=index + 1,
                original_rank=index + 1,
                keyword=keyword,
                hot_value=None,
                label="mock",
                platform=self.platform,
                source=self.source,
                url=self.url_builder(keyword),
            )
            for index, keyword in enumerate(keywords[:limit])
        ]
        return HotSearchResponse(
            source=self.source,
            platform=self.platform,
            platforms=[self.platform],
            items=items,
            fallback_used=True,
        )
