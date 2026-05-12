from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel, Field


class HotSearchItem(BaseModel):
    rank: int
    keyword: str
    hot_value: str | None = None
    url: str | None = None
    label: str | None = None
    source: str = "unknown"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict[str, Any] = Field(default_factory=dict)


class HotSearchResponse(BaseModel):
    source: str
    items: list[HotSearchItem]
    fallback_used: bool = False
    error: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseHotSearchProvider(ABC):
    source: str

    @abstractmethod
    def fetch(self, limit: int = 20) -> HotSearchResponse:
        raise NotImplementedError


def build_weibo_search_url(keyword: str) -> str:
    return f"https://s.weibo.com/weibo?q={quote(keyword)}"
