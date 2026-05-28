from __future__ import annotations

import httpx

from app.hot_sources.base import BaseHotSearchProvider, HotSearchItem, HotSearchResponse
from app.hot_sources.mock import MockHotSearchProvider


class BilibiliRankingProvider(BaseHotSearchProvider):
    source = "bilibili_ranking"
    platform = "bilibili"
    endpoint = "https://api.bilibili.com/x/web-interface/ranking/v2"
    legacy_endpoint = "https://api.bilibili.com/x/web-interface/ranking"

    def __init__(
        self,
        timeout: float = 10.0,
        rid: int = 0,
        fallback: BaseHotSearchProvider | None = None,
    ):
        self.timeout = timeout
        self.rid = rid
        self.fallback = fallback or MockHotSearchProvider(
            platform=self.platform,
            source="mock_bilibili",
            keywords=[
                "B站热门视频观察",
                "年轻人生活方式讨论",
                "影视综艺热点解读",
                "科技产品体验争议",
            ],
        )

    def fetch(self, limit: int = 20) -> HotSearchResponse:
        try:
            response = httpx.get(
                self.endpoint,
                params={"rid": self.rid, "type": "all"},
                timeout=self.timeout,
                trust_env=False,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
                    ),
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://www.bilibili.com/ranking/all",
                },
            )
            response.raise_for_status()
            items = self._parse_items(response.json(), limit=limit)
            if not items:
                return self._fetch_legacy(limit=limit)
            return HotSearchResponse(source=self.source, platform=self.platform, platforms=[self.platform], items=items)
        except Exception as exc:
            fallback_response = self.fallback.fetch(limit=limit)
            fallback_response.source = self.source
            fallback_response.fallback_used = True
            fallback_error = f"; fallback_error={fallback_response.error}" if fallback_response.error else ""
            fallback_response.error = f"bilibili_ranking_error={exc}{fallback_error}"
            return fallback_response

    def _fetch_legacy(self, limit: int = 20) -> HotSearchResponse:
        response = httpx.get(
            self.legacy_endpoint,
            params={"rid": self.rid, "type": "all"},
            timeout=self.timeout,
            trust_env=False,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.bilibili.com/ranking/all",
            },
        )
        response.raise_for_status()
        items = self._parse_items(response.json(), limit=limit)
        if not items:
            raise ValueError("No ranking items found in Bilibili response.")
        return HotSearchResponse(source=self.source, platform=self.platform, platforms=[self.platform], items=items)

    def _parse_items(self, payload: dict, limit: int = 20) -> list[HotSearchItem]:
        items: list[HotSearchItem] = []
        for raw in (payload.get("data") or {}).get("list") or []:
            keyword = str(raw.get("title") or "").strip()
            if not keyword:
                continue
            rank = len(items) + 1
            bvid = str(raw.get("bvid") or "")
            stat = raw.get("stat") or {}
            owner = raw.get("owner") or {}
            hot_value = stat.get("view")
            if hot_value is None:
                hot_value = raw.get("video_review")
            items.append(
                HotSearchItem(
                    rank=rank,
                    original_rank=rank,
                    keyword=keyword,
                    hot_value=str(hot_value) if hot_value is not None else None,
                    platform=self.platform,
                    source=self.source,
                    url=str(raw.get("short_link_v2") or f"https://www.bilibili.com/video/{bvid}"),
                    raw={
                        "bvid": bvid,
                        "desc": raw.get("desc"),
                        "author": owner.get("name") or raw.get("author"),
                        "pubdate": raw.get("pubdate"),
                        "view": stat.get("view"),
                    },
                )
            )
            if len(items) >= limit:
                break
        return items
