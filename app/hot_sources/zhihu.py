from __future__ import annotations

import re

import httpx

from app.hot_sources.base import BaseHotSearchProvider, HotSearchItem, HotSearchResponse, build_zhihu_search_url
from app.hot_sources.mock import MockHotSearchProvider


class ZhihuHotListProvider(BaseHotSearchProvider):
    source = "zhihu_hot"
    platform = "zhihu"
    endpoint = "https://api.zhihu.com/topstory/hot-lists/total"

    def __init__(
        self,
        timeout: float = 10.0,
        fallback: BaseHotSearchProvider | None = None,
    ):
        self.timeout = timeout
        self.fallback = fallback or MockHotSearchProvider(
            platform=self.platform,
            source="mock_zhihu",
            keywords=[
                "为什么年轻人越来越重视劳动权益",
                "平台售后规则应该如何改进",
                "如何看待公共事件中的信息核验",
                "食品安全通报后消费者该关注什么",
            ],
        )

    def fetch(self, limit: int = 20) -> HotSearchResponse:
        try:
            response = httpx.get(
                self.endpoint,
                params={"limit": max(limit, 50)},
                timeout=self.timeout,
                trust_env=False,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
                    ),
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://www.zhihu.com/hot",
                },
            )
            response.raise_for_status()
            items = self._parse_items(response.json(), limit=limit)
            if not items:
                raise ValueError("No hot list items found in Zhihu response.")
            return HotSearchResponse(source=self.source, platform=self.platform, platforms=[self.platform], items=items)
        except Exception as exc:
            fallback_response = self.fallback.fetch(limit=limit)
            fallback_response.source = self.source
            fallback_response.fallback_used = True
            fallback_error = f"; fallback_error={fallback_response.error}" if fallback_response.error else ""
            fallback_response.error = f"zhihu_hot_error={exc}{fallback_error}"
            return fallback_response

    def _parse_items(self, payload: dict, limit: int = 20) -> list[HotSearchItem]:
        items: list[HotSearchItem] = []
        for raw in payload.get("data") or []:
            target = raw.get("target") or {}
            keyword = str(target.get("title") or "").strip()
            if not keyword:
                continue
            rank = len(items) + 1
            url = self._question_url(target)
            detail_text = str(raw.get("detail_text") or "")
            items.append(
                HotSearchItem(
                    rank=rank,
                    original_rank=rank,
                    keyword=keyword,
                    hot_value=self._hot_value(detail_text),
                    platform=self.platform,
                    source=self.source,
                    url=url or build_zhihu_search_url(keyword),
                    raw={
                        "id": target.get("id"),
                        "excerpt": target.get("excerpt"),
                        "detail_text": detail_text,
                    },
                )
            )
            if len(items) >= limit:
                break
        return items

    def _question_url(self, target: dict) -> str | None:
        raw_url = str(target.get("url") or "")
        match = re.search(r"/questions?/(\d+)", raw_url)
        if match:
            return f"https://www.zhihu.com/question/{match.group(1)}"
        if target.get("id"):
            return f"https://www.zhihu.com/question/{target['id']}"
        return None

    def _hot_value(self, detail_text: str) -> str | None:
        if not detail_text:
            return None
        match = re.search(r"([\d.]+)\s*万", detail_text)
        if match:
            return str(int(float(match.group(1)) * 10000))
        digits = re.findall(r"\d+", detail_text)
        return digits[0] if digits else None
