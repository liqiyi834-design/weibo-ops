from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.core.config import Settings
from app.schemas.comment import ResearchSource, TopicResearchSourcesResponse


class ExaResearchService:
    endpoint = "https://api.exa.ai/search"

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.settings = settings
        self.client = client

    def research_topic_sources(
        self,
        topic: str,
        limit: int = 5,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> TopicResearchSourcesResponse:
        query = self._build_query(topic)
        if not self.settings.exa_api_key:
            return TopicResearchSourcesResponse(
                topic=topic,
                query=query,
                sources=[],
                notes=["EXA_API_KEY is not configured."],
                is_configured=False,
            )

        payload: dict = {
            "query": query,
            "numResults": limit,
            "contents": {
                "highlights": {
                    "query": topic,
                    "maxCharacters": 700,
                },
                "summary": True,
            },
        }
        if include_domains:
            payload["includeDomains"] = include_domains
        if exclude_domains:
            payload["excludeDomains"] = exclude_domains

        response = self._post(payload)
        results = response.get("results") or []
        sources = [self._to_source(item) for item in results[:limit] if item.get("url")]
        notes = []
        if not sources:
            notes.append("Exa returned no usable sources.")
        return TopicResearchSourcesResponse(topic=topic, query=query, sources=sources, notes=notes)

    def _post(self, payload: dict) -> dict:
        headers = {
            "x-api-key": self.settings.exa_api_key or "",
            "Content-Type": "application/json",
        }
        timeout = self.settings.request_timeout_seconds
        if self.client is not None:
            response = self.client.post(self.endpoint, headers=headers, json=payload, timeout=timeout)
        else:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(self.endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def _to_source(self, item: dict) -> ResearchSource:
        url = item.get("url") or ""
        domain = urlparse(url).netloc.lower()
        highlights = [str(value) for value in item.get("highlights") or [] if str(value).strip()]
        summary = str(item.get("summary") or "").strip()
        if not summary and highlights:
            summary = " ".join(highlights[:2])
        credibility = _estimate_credibility(domain)
        return ResearchSource(
            title=str(item.get("title") or ""),
            url=url,
            domain=domain,
            published_date=item.get("publishedDate"),
            author=item.get("author"),
            summary=summary,
            highlights=highlights,
            relevance_score=item.get("score"),
            credibility=credibility,
            ingest_recommendation="can_ingest_after_review" if credibility in {"medium", "high"} else "candidate_only",
        )

    def _build_query(self, topic: str) -> str:
        return f"{topic} 背景 官方 通报 媒体 报道"


def _estimate_credibility(domain: str) -> str:
    if not domain:
        return "unknown"
    high_suffixes = (".gov.cn", ".edu.cn")
    high_domains = {
        "www.court.gov.cn",
        "www.mps.gov.cn",
        "www.samr.gov.cn",
        "www.gov.cn",
    }
    medium_domains = {
        "www.xinhuanet.com",
        "www.people.com.cn",
        "www.chinanews.com.cn",
        "www.thepaper.cn",
        "www.yicai.com",
        "www.caixin.com",
        "finance.sina.com.cn",
        "news.cctv.com",
    }
    if domain in high_domains or domain.endswith(high_suffixes):
        return "high"
    if domain in medium_domains:
        return "medium"
    return "unknown"
