from __future__ import annotations

import re
from html import unescape

import httpx

from app.hot_sources.base import BaseHotSearchProvider, HotSearchItem, HotSearchResponse, build_weibo_search_url
from app.hot_sources.mock import MockHotSearchProvider


class WeiboCookieHotSearchProvider(BaseHotSearchProvider):
    source = "weibo_cookie"
    endpoint = "https://s.weibo.com/top/summary"

    def __init__(
        self,
        cookie: str | None,
        cate: str = "realtimehot",
        timeout: float = 10.0,
        fallback: BaseHotSearchProvider | None = None,
    ):
        self.cookie = cookie
        self.cate = cate
        self.timeout = timeout
        self.fallback = fallback or MockHotSearchProvider()

    def fetch(self, limit: int = 20) -> HotSearchResponse:
        try:
            if not self.cookie:
                raise ValueError("WEIBO_COOKIE is not configured.")
            response = httpx.get(
                self.endpoint,
                params={"cate": self.cate},
                timeout=self.timeout,
                trust_env=False,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Referer": "https://s.weibo.com/top/summary",
                    "Cookie": self.cookie,
                },
            )
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            items = self._parse_items(response.text, limit=limit)
            if not items:
                raise ValueError("No hot search items found in Weibo cookie response.")
            return HotSearchResponse(source=self.source, items=items)
        except Exception as exc:
            fallback_response = self.fallback.fetch(limit=limit)
            fallback_response.source = self.source
            fallback_response.fallback_used = True
            fallback_error = f"; fallback_error={fallback_response.error}" if fallback_response.error else ""
            fallback_response.error = f"cookie_error={exc}{fallback_error}"
            return fallback_response

    def _parse_items(self, html: str, limit: int = 20) -> list[HotSearchItem]:
        items: list[HotSearchItem] = []
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.S | re.I)
        for row in rows:
            if "td-02" not in row:
                continue
            keyword = self._extract_keyword(row)
            if not keyword or keyword in {"实时热点", "查看更多"}:
                continue
            rank = len(items) + 1
            items.append(
                HotSearchItem(
                    rank=rank,
                    keyword=keyword,
                    hot_value=self._extract_hot_value(row),
                    label=self._extract_label(row),
                    source=self.source,
                    url=build_weibo_search_url(keyword),
                )
            )
            if len(items) >= limit:
                break
        return items

    def _extract_keyword(self, row: str) -> str | None:
        match = re.search(r'<td[^>]*class="td-02"[^>]*>.*?<a[^>]*>(.*?)</a>', row, flags=re.S | re.I)
        if not match:
            return None
        return self._clean_text(match.group(1))

    def _extract_hot_value(self, row: str) -> str | None:
        match = re.search(r'<span[^>]*>(.*?)</span>', row, flags=re.S | re.I)
        if not match:
            return None
        value = self._clean_text(match.group(1))
        return value or None

    def _extract_label(self, row: str) -> str | None:
        match = re.search(r'<i[^>]*>(.*?)</i>', row, flags=re.S | re.I)
        if not match:
            return None
        label = self._clean_text(match.group(1))
        return label or None

    def _clean_text(self, value: str) -> str:
        text = re.sub(r"<[^>]+>", "", value)
        text = unescape(text)
        return re.sub(r"\s+", " ", text).strip()
