from __future__ import annotations

import re
from html import unescape
from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.schemas.comment import TopicResearchMetrics


class TopicResearchService:
    endpoint = "https://s.weibo.com/weibo"

    def __init__(self, settings: Settings):
        self.settings = settings

    def research(self, keyword: str) -> TopicResearchMetrics:
        source_url = f"{self.endpoint}?q={quote(keyword)}"
        try:
            if not self.settings.weibo_cookie:
                raise ValueError("WEIBO_COOKIE is not configured.")
            response = httpx.get(
                self.endpoint,
                params={"q": keyword},
                timeout=self.settings.request_timeout_seconds,
                trust_env=False,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Referer": "https://s.weibo.com/",
                    "Cookie": self.settings.weibo_cookie,
                },
            )
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            return self.parse(keyword, response.text, source_url=source_url)
        except Exception as exc:
            return TopicResearchMetrics(keyword=keyword, source_url=source_url, error=str(exc))

    def parse(self, keyword: str, html: str, source_url: str | None = None) -> TopicResearchMetrics:
        text = self._clean_text(html)
        return TopicResearchMetrics(
            keyword=keyword,
            read_count=self._extract_count(text, ["阅读", "阅读量"]),
            discussion_count=self._extract_count(text, ["讨论", "讨论量"]),
            sampled_posts_count=self._count_posts(html, text),
            controversy_score=self._controversy_score(text),
            source_url=source_url,
        )

    def _clean_text(self, html: str) -> str:
        text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    def _extract_count(self, text: str, labels: list[str]) -> int | None:
        label_pattern = "|".join(re.escape(label) for label in labels)
        patterns = [
            rf"(?:{label_pattern})\s*[:：]?\s*(\d+(?:\.\d+)?)\s*([万亿]?)",
            rf"(\d+(?:\.\d+)?)\s*([万亿]?)\s*(?:{label_pattern})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._to_int(match.group(1), match.group(2))
        return None

    def _to_int(self, value: str, unit: str) -> int:
        number = float(value)
        if unit == "亿":
            number *= 100000000
        elif unit == "万":
            number *= 10000
        return int(number)

    def _count_posts(self, html: str, text: str) -> int:
        card_count = len(re.findall(r'action-type="feed_list_item"|card-wrap|mid="', html))
        if card_count:
            return min(card_count, 50)
        time_markers = len(re.findall(r"\d{1,2}分钟前|今天 \d{1,2}:\d{2}|来自", text))
        return min(time_markers, 50)

    def _controversy_score(self, text: str) -> float | None:
        positive = len(re.findall(r"支持|合理|应该|没问题|理解|正常", text))
        negative = len(re.findall(r"反对|离谱|质疑|争议|投诉|抵制|恶心|低俗|偷拍|道歉|翻车", text))
        total = positive + negative
        if total == 0:
            return None
        balance = 1 - abs(positive - negative) / total
        intensity = min(1.0, total / 20)
        return round((balance * 0.6 + intensity * 0.4) * 100, 2)
