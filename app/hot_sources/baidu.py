from __future__ import annotations

import json
import re
from html import unescape

import httpx

from app.hot_sources.base import BaseHotSearchProvider, HotSearchItem, HotSearchResponse, build_baidu_search_url
from app.hot_sources.mock import MockHotSearchProvider


class BaiduTopHotSearchProvider(BaseHotSearchProvider):
    source = "baidu_top"
    platform = "baidu"
    endpoint = "https://top.baidu.com/board"

    def __init__(
        self,
        timeout: float = 10.0,
        tab: str = "realtime",
        fallback: BaseHotSearchProvider | None = None,
    ):
        self.timeout = timeout
        self.tab = tab
        self.fallback = fallback or MockHotSearchProvider(
            platform=self.platform,
            source="mock_baidu",
            keywords=[
                "平台售后规则引争议",
                "假期消费避坑指南",
                "食品安全通报",
                "年轻人为什么不爱加班",
            ],
        )

    def fetch(self, limit: int = 20) -> HotSearchResponse:
        try:
            response = httpx.get(
                self.endpoint,
                params={"tab": self.tab},
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
                },
            )
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            items = self._parse_items(response.text, limit=limit)
            if not items:
                raise ValueError("No hot search items found in Baidu top response.")
            return HotSearchResponse(source=self.source, platform=self.platform, platforms=[self.platform], items=items)
        except Exception as exc:
            fallback_response = self.fallback.fetch(limit=limit)
            fallback_response.source = self.source
            fallback_response.fallback_used = True
            fallback_error = f"; fallback_error={fallback_response.error}" if fallback_response.error else ""
            fallback_response.error = f"baidu_top_error={exc}{fallback_error}"
            return fallback_response

    def _parse_items(self, html: str, limit: int = 20) -> list[HotSearchItem]:
        records = self._records_from_json(html)
        if not records:
            records = self._records_from_html(html)

        items: list[HotSearchItem] = []
        seen: set[str] = set()
        for record in records:
            keyword = self._clean_text(str(record.get("keyword") or ""))
            if not keyword or keyword in seen:
                continue
            seen.add(keyword)
            rank = len(items) + 1
            items.append(
                HotSearchItem(
                    rank=rank,
                    original_rank=rank,
                    keyword=keyword,
                    hot_value=self._clean_hot_value(record.get("hot_value")),
                    platform=self.platform,
                    source=self.source,
                    url=str(record.get("url") or build_baidu_search_url(keyword)),
                    raw={key: value for key, value in record.items() if value is not None},
                )
            )
            if len(items) >= limit:
                break
        return items

    def _records_from_json(self, html: str) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for match in re.finditer(r'"word"\s*:\s*"(?P<word>(?:\\.|[^"\\])*)"', html):
            start = max(0, match.start() - 800)
            end = min(len(html), match.end() + 1200)
            block = html[start:end]
            keyword = self._json_unescape(match.group("word"))
            records.append(
                {
                    "keyword": keyword,
                    "hot_value": self._first_match(block, [r'"hotScore"\s*:\s*"?([\d,]+)"?', r'"desc"\s*:\s*"([^"]+)"']),
                    "url": self._json_unescape(
                        self._first_match(block, [r'"rawUrl"\s*:\s*"((?:\\.|[^"\\])*)"', r'"url"\s*:\s*"((?:\\.|[^"\\])*)"'])
                    ),
                }
            )
        return records

    def _records_from_html(self, html: str) -> list[dict[str, object]]:
        text = unescape(html)
        records: list[dict[str, object]] = []
        for match in re.finditer(r'<div[^>]+class="[^"]*c-single-text-ellipsis[^"]*"[^>]*>(.*?)</div>', text, re.S):
            keyword = self._clean_text(match.group(1))
            if keyword:
                records.append({"keyword": keyword})
        return records

    def _first_match(self, text: str, patterns: list[str]) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.S)
            if match:
                return match.group(1)
        return None

    def _json_unescape(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            return json.loads(f'"{value}"')
        except json.JSONDecodeError:
            return value

    def _clean_hot_value(self, value: object) -> str | None:
        if value is None:
            return None
        matches = re.findall(r"\d+", str(value).replace(",", ""))
        return matches[-1] if matches else None

    def _int_or_none(self, value: object) -> int | None:
        if value is None:
            return None
        matches = re.findall(r"\d+", str(value))
        return int(matches[-1]) if matches else None

    def _clean_text(self, value: str) -> str:
        text = re.sub(r"<[^>]+>", "", value)
        text = unescape(text)
        return re.sub(r"\s+", " ", text).strip()
