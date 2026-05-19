from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any

from app.hot_sources.base import BaseHotSearchProvider, HotSearchItem, HotSearchResponse, build_weibo_search_url
from app.hot_sources.mock import MockHotSearchProvider


class VisibleCaptureHotSearchProvider(BaseHotSearchProvider):
    source = "weibo_visible_capture"

    def __init__(
        self,
        sample_dirs: list[Path] | None = None,
        fallback: BaseHotSearchProvider | None = None,
    ):
        self.sample_dirs = sample_dirs or [Path("samples/inbox"), Path("samples/processed")]
        self.fallback = fallback or MockHotSearchProvider()

    def fetch(self, limit: int = 20) -> HotSearchResponse:
        try:
            keywords = self._load_keywords(limit=limit)
            if not keywords:
                raise ValueError("No visible capture hot topics found.")
            items = [
                HotSearchItem(
                    rank=index + 1,
                    keyword=keyword,
                    label="visible",
                    source=self.source,
                    url=build_weibo_search_url(keyword),
                )
                for index, keyword in enumerate(keywords)
            ]
            return HotSearchResponse(source=self.source, items=items)
        except Exception as exc:
            fallback_response = self.fallback.fetch(limit=limit)
            fallback_response.source = self.source
            fallback_response.fallback_used = True
            fallback_error = f"; fallback_error={fallback_response.error}" if fallback_response.error else ""
            fallback_response.error = f"visible_capture_error={exc}{fallback_error}"
            return fallback_response

    def _load_keywords(self, limit: int) -> list[str]:
        candidates: OrderedDict[str, None] = OrderedDict()
        for path in self._iter_json_files():
            payload = json.loads(path.read_text(encoding="utf-8"))
            for keyword in self._extract_keywords(payload):
                if keyword not in candidates:
                    candidates[keyword] = None
                if len(candidates) >= limit:
                    return list(candidates.keys())
        return list(candidates.keys())

    def _iter_json_files(self) -> list[Path]:
        files: list[Path] = []
        for directory in self.sample_dirs:
            if directory.exists():
                files.extend(directory.glob("*.json"))
        return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)

    def _extract_keywords(self, payload: dict[str, Any]) -> list[str]:
        texts: list[str] = []
        if isinstance(payload.get("page_title"), str):
            texts.append(payload["page_title"])
        if isinstance(payload.get("visible_text"), str):
            texts.append(payload["visible_text"])
        for sample in payload.get("samples") or []:
            if isinstance(sample, dict):
                for key in ("body_text", "page_title"):
                    value = sample.get(key)
                    if isinstance(value, str):
                        texts.append(value)

        keywords: list[str] = []
        for text in texts:
            keywords.extend(self._extract_from_text(text))
        return keywords

    def _extract_from_text(self, text: str) -> list[str]:
        keywords: list[str] = []
        for hashtag in re.findall(r"#([^#\s]{2,40})#", text):
            cleaned = self._clean_keyword(hashtag)
            if cleaned:
                keywords.append(cleaned)

        for line in re.split(r"[\r\n。！？!?|]", text):
            cleaned = self._clean_keyword(line)
            if self._looks_like_hot_topic(cleaned):
                keywords.append(cleaned)
        return keywords

    def _clean_keyword(self, value: str) -> str:
        text = re.sub(r"\s+", " ", value).strip()
        text = re.sub(r"^(微博热搜|热搜|#)", "", text).strip()
        text = re.sub(r"^([^#]{2,40})#.*$", r"\1", text).strip()
        text = re.sub(r"(阅读|讨论|主持人|导语).*$", "", text).strip()
        return text[:40]

    def _looks_like_hot_topic(self, value: str) -> bool:
        if not value:
            return False
        if len(value) < 4 or len(value) > 24:
            return False
        if re.search(r"https?://|登录|转发|评论|赞|关注|展开|全文|客户端|广告", value):
            return False
        if value in {"微博 – 随时随地发现新鲜事", "微博-随时随地发现新鲜事", "今日观察"}:
            return False
        if value.startswith("微博 ") or value.startswith("微博–") or value.startswith("微博-"):
            return False
        return bool(re.search(r"[\u4e00-\u9fff]", value))
