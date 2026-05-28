from __future__ import annotations

import re
from collections import OrderedDict

from app.hot_sources.base import HotSearchItem, HotSearchResponse
from app.schemas.comment import HotTopicCluster, HotTopicClusterItem, HotTopicClusterResponse


class HotTopicClusterService:
    stopwords = {
        "如何",
        "怎么看",
        "看待",
        "回应",
        "发声",
        "称",
        "曝",
        "为什么",
        "背后",
        "原因",
        "哪些",
        "事件",
    }

    def cluster(self, response: HotSearchResponse, max_clusters: int = 30) -> HotTopicClusterResponse:
        clusters: list[HotTopicCluster] = []
        for item in response.items:
            match = self._find_match(clusters, item)
            if match:
                self._append_item(match[0], item, confidence=match[1], reason=match[2])
            else:
                clusters.append(self._new_cluster(item))

        clusters = sorted(
            clusters,
            key=lambda cluster: (
                -len(cluster.source_platforms),
                cluster.best_rank or 999,
                -max((self._hot_number(value) or 0) for value in cluster.hot_signals.values() or [0]),
            ),
        )[:max_clusters]
        return HotTopicClusterResponse(
            source=response.source,
            platforms=response.platforms or sorted({item.platform for item in response.items if item.platform}),
            clusters=clusters,
            fallback_used=response.fallback_used,
            error=response.error,
            notes=response.notes,
            timestamp=response.timestamp,
        )

    def _find_match(self, clusters: list[HotTopicCluster], item: HotSearchItem) -> tuple[HotTopicCluster, float, str] | None:
        item_key = self._normalize(item.keyword)
        item_tokens = self._tokens(item.keyword)
        best: tuple[HotTopicCluster, float, str] | None = None
        for cluster in clusters:
            cluster_key = self._normalize(cluster.canonical_title)
            if item_key == cluster_key:
                return cluster, 1.0, "normalized_title"
            if self._contains_topic(cluster_key, item_key):
                candidate = (cluster, 0.86, "title_contains")
            else:
                score = self._jaccard(item_tokens, self._tokens(cluster.canonical_title))
                candidate = (cluster, score, "token_overlap") if score >= 0.58 and len(item_tokens) >= 2 else None
            if candidate and (best is None or candidate[1] > best[1]):
                best = candidate
        return best

    def _new_cluster(self, item: HotSearchItem) -> HotTopicCluster:
        cluster = HotTopicCluster(
            canonical_title=item.keyword,
            confidence=1.0,
            match_reason="single_source",
        )
        self._append_item(cluster, item, confidence=1.0, reason="single_source")
        return cluster

    def _append_item(self, cluster: HotTopicCluster, item: HotSearchItem, confidence: float, reason: str) -> None:
        cluster.items.append(
            HotTopicClusterItem(
                rank=item.rank,
                original_rank=item.original_rank,
                keyword=item.keyword,
                platform=item.platform,
                source=item.source,
                url=item.url,
                hot_value=item.hot_value,
            )
        )
        cluster.source_platforms = self._dedupe([*cluster.source_platforms, item.platform])
        if item.url:
            cluster.source_urls = self._dedupe([*cluster.source_urls, item.url])
        rank = item.original_rank or item.rank
        if rank is not None:
            existing_rank = cluster.platform_ranks.get(item.platform)
            cluster.platform_ranks[item.platform] = min(existing_rank, rank) if existing_rank else rank
            cluster.best_rank = min(cluster.platform_ranks.values())
        if item.hot_value is not None:
            cluster.hot_signals[f"{item.platform}_hot_value"] = item.hot_value
        cluster.confidence = min(cluster.confidence, confidence)
        if reason != "single_source":
            cluster.match_reason = reason
            cluster.canonical_title = self._choose_canonical_title(cluster)

    def _choose_canonical_title(self, cluster: HotTopicCluster) -> str:
        return min(cluster.items, key=lambda item: (len(item.keyword), item.original_rank or item.rank or 999)).keyword

    def _normalize(self, value: str) -> str:
        text = value.lower()
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"[#【】\[\]（）()“”\"'：:，,。.!！?？、\s_-]+", "", text)
        text = re.sub(r"(如何看待|怎么看待|如何解读|怎么回事|最新回应|官方回应|发声)$", "", text)
        return text.strip()

    def _contains_topic(self, left: str, right: str) -> bool:
        if min(len(left), len(right)) < 6:
            return False
        return left in right or right in left

    def _tokens(self, value: str) -> set[str]:
        normalized = self._normalize(value)
        tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9]{2,}", normalized))
        tokens.update(re.findall(r"[\u4e00-\u9fff]{2,4}", normalized))
        return {token for token in tokens if token not in self.stopwords}

    def _jaccard(self, left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)

    def _dedupe(self, values: list[str]) -> list[str]:
        return list(OrderedDict((value, None) for value in values if value).keys())

    def _hot_number(self, value: str | int | float | None) -> int | None:
        if value is None:
            return None
        matches = re.findall(r"\d+", str(value))
        return int(matches[-1]) if matches else None
