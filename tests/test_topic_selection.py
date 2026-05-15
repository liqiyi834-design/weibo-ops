from app.schemas.comment import HotTopic
from app.services.topic_selection_service import TopicSelectionService


def test_topic_selection_recommends_comment_worthy_topics():
    topics = [
        HotTopic(rank=1, keyword="习近平同外国总统举行会谈", hot_value="1200000", source="test"),
        HotTopic(rank=2, keyword="某品牌母亲节文案翻车", hot_value="1000000", label="热", source="test"),
        HotTopic(rank=3, keyword="平台售后规则引争议", hot_value="900000", source="test"),
        HotTopic(rank=4, keyword="热门综艺嘉宾阵容官宣", hot_value="800000", source="test"),
        HotTopic(rank=5, keyword="未成年消费退款争议", hot_value="700000", source="test"),
    ]

    response = TopicSelectionService().select(topics, max_results=3)

    assert response.evaluated_count == 5
    assert len(response.selected) == 3
    selected_keywords = {item.keyword for item in response.selected}
    assert "某品牌母亲节文案翻车" in selected_keywords
    assert "平台售后规则引争议" in selected_keywords
    assert response.selected[0].reason
    assert response.selected[0].recommended_angle
    assert response.selected[0].target_platform_scores["weibo"] == response.selected[0].score
    assert "zhihu" in response.selected[0].target_platform_scores
    assert response.selected[0].recommended_targets
    assert all(0 <= item.score <= 100 for item in response.selected)
    assert "不要自动发布" in response.selected[0].avoid_points


def test_topic_selection_scores_zhihu_fit_separately():
    topics = [
        HotTopic(rank=1, keyword="明星机场自拍", hot_value="1000000", source="test"),
        HotTopic(rank=2, keyword="平台售后规则引争议", hot_value="900000", source="test"),
    ]

    response = TopicSelectionService().select(topics, max_results=2)
    by_keyword = {item.keyword: item for item in response.selected}
    zhihu_item = by_keyword["平台售后规则引争议"]

    assert zhihu_item.target_platform_scores["zhihu"] > by_keyword["明星机场自拍"].target_platform_scores["zhihu"]
    assert "zhihu" in zhihu_item.recommended_targets
    assert zhihu_item.zhihu_question_title == "如何看待平台售后规则引争议？"
    assert zhihu_item.zhihu_answer_angle
    assert zhihu_item.zhihu_required_research
    assert zhihu_item.zhihu_recommended_domain == "consumer"
    assert zhihu_item.zhihu_domain_scores["consumer"] > zhihu_item.zhihu_domain_scores["media_culture"]
    assert zhihu_item.zhihu_domain_reason


def test_topic_selection_marks_high_risk_topics():
    topics = [HotTopic(rank=1, keyword="法院回应偷拍男生案件", hot_value="1000000", source="test")]

    response = TopicSelectionService().select(topics, max_results=3)

    assert response.selected[0].risk_level == "high"
    assert response.selected[0].score >= 80
    assert "不要定罪" in response.selected[0].avoid_points


def test_topic_selection_marks_political_public_affairs_as_high_risk():
    topics = [HotTopic(rank=1, keyword="特朗普访华", hot_value="1000000", source="test")]

    response = TopicSelectionService().select(topics, max_results=3)

    assert response.selected[0].risk_level == "high"
    assert response.selected[0].score > 0


def test_topic_selection_uses_research_metrics_in_reason_and_score():
    topics = [
        HotTopic(rank=10, keyword="普通话题", hot_value="300000", source="test"),
        HotTopic(
            rank=10,
            keyword="普通话题二次采样",
            hot_value="300000",
            read_count=120000000,
            discussion_count=300000,
            sampled_posts_count=20,
            controversy_score=80,
            source="test",
        ),
    ]

    response = TopicSelectionService().select(topics, max_results=3)

    assert response.selected[0].keyword == "普通话题二次采样"
    assert response.selected[0].score > response.selected[1].score
    assert "阅读量约 120000000" in response.selected[0].reason
    assert "讨论量约 300000" in response.selected[0].reason
