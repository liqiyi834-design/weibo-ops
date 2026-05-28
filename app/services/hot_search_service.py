from datetime import datetime, timezone

from app.core.config import Settings
from app.hot_sources.baidu import BaiduTopHotSearchProvider
from app.hot_sources.bilibili import BilibiliRankingProvider
from app.hot_sources.base import BaseHotSearchProvider, HotSearchResponse
from app.hot_sources.mock import MockHotSearchProvider
from app.hot_sources.visible_capture import VisibleCaptureHotSearchProvider
from app.hot_sources.weibo_cookie import WeiboCookieHotSearchProvider
from app.hot_sources.zhihu import ZhihuHotListProvider


class HotSearchService:
    supported_platforms = ("weibo", "baidu", "zhihu", "bilibili")

    def __init__(self, settings: Settings):
        self.settings = settings

    def get_hot_topics(self, platform: str = "weibo", limit: int = 20) -> HotSearchResponse:
        platforms, requested_all = self._normalize_platforms(platform)
        if len(platforms) == 1 and not requested_all:
            provider = self._provider_for(platforms[0])
            return provider.fetch(limit=limit)

        responses = [self._provider_for(item).fetch(limit=limit) for item in platforms]
        merged_items = []
        notes: list[str] = []
        errors: list[str] = []
        fallback_used = False
        for response in responses:
            fallback_used = fallback_used or response.fallback_used
            if response.error:
                errors.append(f"{response.platform or response.source}: {response.error}")
            notes.extend(response.notes)
            merged_items.extend(response.items)

        merged_items = sorted(
            merged_items,
            key=lambda item: (item.rank, platforms.index(item.platform) if item.platform in platforms else 999),
        )[:limit]
        return HotSearchResponse(
            source=",".join(response.source for response in responses),
            platform="all",
            platforms=platforms,
            items=merged_items,
            fallback_used=fallback_used,
            error="; ".join(errors) if errors else None,
            notes=notes,
            timestamp=datetime.now(timezone.utc),
        )

    def get_weibo_hot_topics(self, limit: int = 20) -> HotSearchResponse:
        return self.get_hot_topics(platform="weibo", limit=limit)

    def get_weibo_ent_topics(self, limit: int = 20) -> HotSearchResponse:
        return self._weibo_provider(cate="entrank").fetch(limit=limit)

    def _provider_for(self, platform: str) -> BaseHotSearchProvider:
        if platform == "weibo":
            return self._weibo_provider(cate="realtimehot")
        if platform == "baidu":
            return BaiduTopHotSearchProvider(timeout=self.settings.request_timeout_seconds)
        if platform == "zhihu":
            return ZhihuHotListProvider(timeout=self.settings.request_timeout_seconds)
        if platform == "bilibili":
            return BilibiliRankingProvider(timeout=self.settings.request_timeout_seconds)
        raise ValueError(f"Unsupported hot topic platform: {platform}")

    def _weibo_provider(self, cate: str) -> BaseHotSearchProvider:
        mock = MockHotSearchProvider()
        visible = VisibleCaptureHotSearchProvider(fallback=mock)
        return WeiboCookieHotSearchProvider(
            cookie=self.settings.weibo_cookie,
            cate=cate,
            timeout=self.settings.request_timeout_seconds,
            fallback=visible,
        )

    def _normalize_platforms(self, platform: str) -> tuple[list[str], bool]:
        requested = [item.strip().lower() for item in platform.split(",") if item.strip()]
        if not requested:
            requested = ["weibo"]
        if requested == ["all"]:
            return list(self.supported_platforms), True
        unsupported = [item for item in requested if item not in self.supported_platforms]
        if unsupported:
            raise ValueError(f"Unsupported hot topic platform: {', '.join(unsupported)}")
        return requested, False
