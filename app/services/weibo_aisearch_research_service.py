from __future__ import annotations

import re
import time
from html import unescape
from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.schemas.comment import ResearchSource, TopicResearchSourcesResponse


class WeiboAiSearchResearchService:
    endpoint = "https://ai.s.weibo.com/api/wis/show.json"

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.settings = settings
        self.client = client

    def research_topic_sources(
        self,
        topic: str,
        max_polls: int = 6,
        poll_interval_seconds: float = 1.5,
    ) -> TopicResearchSourcesResponse:
        normalized_topic = normalize_weibo_topic(topic)
        page_url = build_weibo_aisearch_url(normalized_topic)
        if not self.settings.weibo_cookie:
            return TopicResearchSourcesResponse(
                topic=topic,
                query=normalized_topic,
                source="weibo_aisearch",
                sources=[],
                notes=["WEIBO_COOKIE is not configured."],
                is_configured=False,
            )

        request_id = str(int(time.time() * 1000))
        notes: list[str] = []
        last_payload: dict = {}
        for loop_num in range(1, max_polls + 1):
            payload = self._request_payload(normalized_topic, request_id, loop_num)
            try:
                raw = self._post(payload, page_url)
            except Exception as exc:
                return TopicResearchSourcesResponse(
                    topic=topic,
                    query=normalized_topic,
                    source="weibo_aisearch",
                    sources=[],
                    notes=[f"Weibo AiSearch request failed: {exc}"],
                )
            last_payload = _extract_data(raw)
            status = str(last_payload.get("status") or raw.get("status") or "")
            stage = str(last_payload.get("stage") or raw.get("stage") or "")
            msg = str(last_payload.get("msg") or last_payload.get("content") or "").strip()
            if status == "2" and stage == "4" and msg:
                source = self._to_research_source(normalized_topic, page_url, last_payload)
                return TopicResearchSourcesResponse(
                    topic=topic,
                    query=normalized_topic,
                    source="weibo_aisearch",
                    sources=[source],
                    notes=notes,
                )
            if status == "3":
                notes.append("Weibo AiSearch rejected this topic.")
                break
            if loop_num < max_polls:
                time.sleep(poll_interval_seconds)

        if not notes:
            notes.append(
                "Weibo AiSearch did not return a completed summary "
                f"(status={last_payload.get('status')}, stage={last_payload.get('stage')})."
            )
        return TopicResearchSourcesResponse(
            topic=topic,
            query=normalized_topic,
            source="weibo_aisearch",
            sources=[],
            notes=notes,
        )

    def _post(self, payload: dict, page_url: str) -> dict:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://s.weibo.com",
            "Referer": page_url,
            "Cookie": self.settings.weibo_cookie or "",
        }
        timeout = self.settings.request_timeout_seconds
        if self.client is not None:
            response = self.client.post(self.endpoint, data=payload, headers=headers, timeout=timeout)
        else:
            with httpx.Client(timeout=timeout, follow_redirects=True, trust_env=False) as client:
                response = client.post(self.endpoint, data=payload, headers=headers)
        final_url = str(response.url)
        if "passport.weibo" in final_url or "login.sina.com.cn" in final_url:
            raise ValueError("Weibo login redirected; cookie may be expired.")
        response.raise_for_status()
        return response.json()

    def _request_payload(self, topic: str, request_id: str, loop_num: int) -> dict:
        return {
            "query": topic,
            "content_type": "loop",
            "request_id": request_id,
            "request_time": "0",
            "search_source": "default_init",
            "sid": "pc_search",
            "vstyle": "1",
            "cot": "1",
            "loop_num": str(loop_num),
        }

    def _to_research_source(self, topic: str, page_url: str, payload: dict) -> ResearchSource:
        msg = str(payload.get("msg") or payload.get("content") or "")
        summary = clean_weibo_aisearch_markdown(msg)
        links = _extract_links(payload)
        highlights = _extract_highlights(msg)
        for link in links[:5]:
            highlights.append(f"引用链接：{link}")
        return ResearchSource(
            title=f"微博智搜：{topic}",
            url=page_url,
            domain="s.weibo.com",
            summary=summary,
            highlights=highlights[:10],
            credibility="medium",
            ingest_recommendation="can_ingest_after_review",
        )


def normalize_weibo_topic(topic: str) -> str:
    cleaned = str(topic or "").strip()
    cleaned = cleaned.strip("#").strip()
    return f"#{cleaned}#" if cleaned else "##"


def build_weibo_aisearch_url(topic: str) -> str:
    return f"https://s.weibo.com/aisearch?q={quote(topic)}&Refer=weibo_aisearch"


def clean_weibo_aisearch_markdown(value: str) -> str:
    text = unescape(str(value or ""))
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"`{1,3}", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _extract_data(payload: dict) -> dict:
    data = payload.get("data") if isinstance(payload, dict) else None
    return data if isinstance(data, dict) else payload


def _extract_highlights(markdown: str) -> list[str]:
    highlights: list[str] = []
    for line in str(markdown or "").splitlines():
        text = clean_weibo_aisearch_markdown(line).strip(" -#*")
        if not text:
            continue
        if re.match(r"^\d+[.、]", text) or len(text) <= 80:
            highlights.append(text)
        if len(highlights) >= 8:
            break
    return highlights


def _extract_links(payload: dict) -> list[str]:
    links: list[str] = []
    candidates = payload.get("link_list") or payload.get("links") or []
    if isinstance(candidates, dict):
        candidates = list(candidates.values())
    if not isinstance(candidates, list):
        return links
    for item in candidates:
        if isinstance(item, str):
            url = item
        elif isinstance(item, dict):
            url = str(item.get("url") or item.get("scheme") or item.get("link") or "")
        else:
            continue
        if url and url not in links:
            links.append(url)
    return links
