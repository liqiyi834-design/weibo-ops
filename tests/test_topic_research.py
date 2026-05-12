from app.core.config import Settings
from app.services.topic_research_service import TopicResearchService


def test_topic_research_parses_visible_metrics():
    service = TopicResearchService(Settings(OPENAI_API_KEY=None, WEIBO_COOKIE="SUB=fake"))
    html = """
    <html>
      <body>
        <div>阅读 1.2亿 讨论 35.6万</div>
        <div action-type="feed_list_item">支持这个处理</div>
        <div action-type="feed_list_item">也有人质疑规则是否合理</div>
        <div action-type="feed_list_item">争议还在发酵</div>
      </body>
    </html>
    """

    metrics = service.parse("测试话题", html, source_url="https://example.test")

    assert metrics.read_count == 120000000
    assert metrics.discussion_count == 356000
    assert metrics.sampled_posts_count == 3
    assert metrics.controversy_score is not None
    assert metrics.source_url == "https://example.test"
