from app.hot_sources.base import HotSearchItem, HotSearchResponse
from app.services.hot_topic_cluster_service import HotTopicClusterService


def test_hot_topic_cluster_merges_normalized_titles():
    response = HotSearchResponse(
        source="test",
        platform="all",
        platforms=["baidu", "zhihu"],
        items=[
            HotSearchItem(
                rank=1,
                original_rank=1,
                keyword="双汇回应抗生素超标37.5倍",
                platform="baidu",
                source="baidu_top",
                hot_value="1000",
                url="https://example.com/baidu",
            ),
            HotSearchItem(
                rank=2,
                original_rank=2,
                keyword="如何看待双汇回应抗生素超标37.5倍？",
                platform="zhihu",
                source="zhihu_hot",
                hot_value="900",
                url="https://example.com/zhihu",
            ),
        ],
    )

    result = HotTopicClusterService().cluster(response)

    assert len(result.clusters) == 1
    cluster = result.clusters[0]
    assert cluster.source_platforms == ["baidu", "zhihu"]
    assert cluster.platform_ranks == {"baidu": 1, "zhihu": 2}
    assert cluster.best_rank == 1
    assert cluster.match_reason in {"normalized_title", "title_contains", "token_overlap"}
    assert len(cluster.source_urls) == 2


def test_hot_topic_cluster_keeps_unrelated_topics_apart():
    response = HotSearchResponse(
        source="test",
        platform="all",
        platforms=["baidu", "bilibili"],
        items=[
            HotSearchItem(rank=1, keyword="儿童智能手表怎么成了家长的烦恼", platform="baidu", source="baidu_top"),
            HotSearchItem(rank=1, keyword="全世界笑点下降1000倍而我不变", platform="bilibili", source="bilibili_ranking"),
        ],
    )

    result = HotTopicClusterService().cluster(response)

    assert len(result.clusters) == 2
    assert all(len(cluster.source_platforms) == 1 for cluster in result.clusters)


def test_hot_topic_cluster_sorts_cross_platform_topics_first():
    response = HotSearchResponse(
        source="test",
        platform="all",
        platforms=["baidu", "zhihu", "bilibili"],
        items=[
            HotSearchItem(rank=1, keyword="单平台高位话题", platform="baidu", source="baidu_top"),
            HotSearchItem(rank=8, keyword="双汇回应抗生素超标37.5倍", platform="baidu", source="baidu_top"),
            HotSearchItem(rank=9, keyword="如何看待双汇回应抗生素超标37.5倍？", platform="zhihu", source="zhihu_hot"),
        ],
    )

    result = HotTopicClusterService().cluster(response)

    assert result.clusters[0].source_platforms == ["baidu", "zhihu"]
