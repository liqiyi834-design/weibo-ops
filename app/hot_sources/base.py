from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel, Field


class HotSearchItem(BaseModel):
    rank: int
    original_rank: int | None = None
    keyword: str
    hot_value: str | None = None
    category_label: str | None = None
    url: str | None = None
    label: str | None = None
    platform: str = "unknown"
    source: str = "unknown"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict[str, Any] = Field(default_factory=dict)


class HotSearchResponse(BaseModel):
    source: str
    platform: str = "unknown"
    platforms: list[str] = Field(default_factory=list)
    items: list[HotSearchItem]
    fallback_used: bool = False
    error: str | None = None
    notes: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseHotSearchProvider(ABC):
    source: str
    platform: str = "unknown"

    @abstractmethod
    def fetch(self, limit: int = 20) -> HotSearchResponse:
        raise NotImplementedError


class HotTopicProvider(BaseHotSearchProvider):
    """Platform-level hot topic provider used by HotSearchService."""


def build_weibo_search_url(keyword: str) -> str:
    return f"https://s.weibo.com/weibo?q={quote(keyword)}"


def build_baidu_search_url(keyword: str) -> str:
    return f"https://www.baidu.com/s?wd={quote(keyword)}"


def build_zhihu_search_url(keyword: str) -> str:
    return f"https://www.zhihu.com/search?type=content&q={quote(keyword)}"
