from app.hot_sources.base import BaseHotSearchProvider, HotSearchItem, HotSearchResponse, build_weibo_search_url


class MockHotSearchProvider(BaseHotSearchProvider):
    source = "mock_weibo"

    def fetch(self, limit: int = 20) -> HotSearchResponse:
        keywords = [
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
                keyword=keyword,
                hot_value=None,
                label="mock",
                source=self.source,
                url=build_weibo_search_url(keyword),
            )
            for index, keyword in enumerate(keywords[:limit])
        ]
        return HotSearchResponse(source=self.source, items=items, fallback_used=True)
