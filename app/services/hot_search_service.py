from app.core.config import Settings
from app.hot_sources.base import HotSearchResponse
from app.hot_sources.mock import MockHotSearchProvider
from app.hot_sources.visible_capture import VisibleCaptureHotSearchProvider
from app.hot_sources.weibo_cookie import WeiboCookieHotSearchProvider


class HotSearchService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_weibo_hot_topics(self, limit: int = 20) -> HotSearchResponse:
        mock = MockHotSearchProvider()
        visible = VisibleCaptureHotSearchProvider(fallback=mock)
        provider = WeiboCookieHotSearchProvider(
            cookie=self.settings.weibo_cookie,
            timeout=self.settings.request_timeout_seconds,
            fallback=visible,
        )
        return provider.fetch(limit=limit)
