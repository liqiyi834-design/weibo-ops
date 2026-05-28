from app.llm.client import BaseLLMClient
from app.schemas.comment import HotTopic
from app.services.topic_selection_service import TopicSelectionService


class SelectionLLM(BaseLLMClient):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "items": [
                {
                    "keyword": "topic b",
                    "weibo_score": 94,
                    "reason": "clearer public conflict and stronger comment space",
                    "recommended_angle": "Discuss the rule cost for ordinary users.",
                    "needed_context": ["verify latest public response"],
                },
                {
                    "keyword": "topic a",
                    "weibo_score": 52,
                    "reason": "weak comment space",
                    "recommended_angle": "Keep as backup.",
                    "needed_context": [],
                },
            ]
        }


class BrokenSelectionLLM(BaseLLMClient):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {"items": [{"keyword": "topic a", "weibo_score": "bad"}]}


class CommercialSelectionLLM(BaseLLMClient):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "items": [
                {
                    "keyword": "brand sale topic",
                    "weibo_score": 98,
                    "reason": "LLM likes the heat, but policy should cap it.",
                    "recommended_angle": "Verify commercial rules first.",
                    "needed_context": [],
                }
            ]
        }


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


def test_topic_selection_uses_llm_scores_when_available():
    topics = [
        HotTopic(rank=1, keyword="topic a", hot_value="1000000", source="test"),
        HotTopic(rank=20, keyword="topic b", hot_value="100000", source="test"),
    ]

    response = TopicSelectionService(llm=SelectionLLM()).select(topics, max_results=2)

    assert response.selected[0].keyword == "topic b"
    assert response.selected[0].score == 94
    assert response.selected[0].llm_score == 94
    assert response.selected[0].llm_scored is True
    assert response.selected[0].base_score is not None
    assert "LLM评分" in response.selected[0].reason
    assert "verify latest public response" in response.selected[0].needed_context


def test_topic_selection_falls_back_to_rules_when_llm_response_is_invalid():
    topics = [
        HotTopic(rank=1, keyword="topic a", hot_value="1000000", source="test"),
        HotTopic(rank=2, keyword="topic b", hot_value="900000", source="test"),
    ]

    response = TopicSelectionService(llm=BrokenSelectionLLM()).select(topics, max_results=2)

    assert all(item.llm_scored is False for item in response.selected)
    assert all(item.llm_score is None for item in response.selected)
    assert any("回退规则分" in note for note in response.notes)


def test_topic_selection_caps_commercial_topic_even_with_high_llm_score():
    topics = [
        HotTopic(rank=1, keyword="brand sale topic", hot_value="1000000", label="ad", source="test"),
    ]

    response = TopicSelectionService(llm=CommercialSelectionLLM()).select(topics, max_results=3)

    assert response.selected[0].llm_scored is True
    assert response.selected[0].score <= 65
    assert response.selected[0].llm_score <= 65


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


def test_topic_selection_preserves_hot_category_label():
    topics = [
        HotTopic(
            rank=1,
            keyword="movie topic",
            hot_value="1033108",
            category_label="movie",
            label="hot",
            source="test",
        )
    ]

    response = TopicSelectionService().select(topics, max_results=3)

    assert response.selected[0].hot_value == "1033108"
    assert response.selected[0].category_label == "movie"
    assert response.selected[0].label == "hot"


def test_topic_selection_downranks_commercial_promotion_label():
    topics = [
        HotTopic(rank=1, keyword="京东618明星红包上线", hot_value=None, label="商", source="test"),
        HotTopic(rank=8, keyword="平台售后规则引发争议", hot_value="300000", source="test"),
    ]

    response = TopicSelectionService().select(topics, max_results=3)
    by_keyword = {item.keyword: item for item in response.selected}

    commercial = by_keyword["京东618明星红包上线"]
    consumer_issue = by_keyword["平台售后规则引发争议"]
    assert commercial.score <= 65
    assert consumer_issue.score > commercial.score
    assert "商业推广标记强" in commercial.reason


def test_topic_selection_lightly_downranks_launch_pr_topics():
    topics = [
        HotTopic(rank=1, keyword="某品牌新车上市售价公布", hot_value="1000000", source="test"),
        HotTopic(rank=6, keyword="平台售后规则引发争议", hot_value="300000", source="test"),
    ]

    response = TopicSelectionService().select(topics, max_results=3)
    by_keyword = {item.keyword: item for item in response.selected}

    launch_pr = by_keyword["某品牌新车上市售价公布"]
    consumer_issue = by_keyword["平台售后规则引发争议"]
    assert launch_pr.score <= 78
    assert consumer_issue.score > launch_pr.score
    assert "新品发布类 PR" in launch_pr.reason
