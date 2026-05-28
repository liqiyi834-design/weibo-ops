from pathlib import Path
from uuid import uuid4

from app.hot_sources.baidu import BaiduTopHotSearchProvider
from app.hot_sources.bilibili import BilibiliRankingProvider
from app.hot_sources.mock import MockHotSearchProvider
from app.hot_sources.visible_capture import VisibleCaptureHotSearchProvider
from app.hot_sources.weibo_cookie import WeiboCookieHotSearchProvider
from app.hot_sources.zhihu import ZhihuHotListProvider


def test_mock_hot_search_provider_returns_items():
    response = MockHotSearchProvider().fetch(limit=3)

    assert response.fallback_used is True
    assert len(response.items) == 3
    assert response.items[0].rank == 1
    assert response.items[0].keyword


def test_weibo_cookie_provider_parses_summary_html():
    html = """
    <table>
      <tr>
        <td class="td-01 ranktop">1</td>
        <td class="td-02"><a href="/weibo?q=test">测试网页热搜一</a><span>123456</span><i>热</i></td>
      </tr>
      <tr>
        <td class="td-01">2</td>
        <td class="td-02"><a href="/weibo?q=test2">测试网页热搜二</a><span>7890</span></td>
      </tr>
    </table>
    """

    items = WeiboCookieHotSearchProvider(cookie="SUB=fake")._parse_items(html, limit=2)

    assert len(items) == 2
    assert items[0].keyword == "测试网页热搜一"
    assert items[0].hot_value == "123456"
    assert items[0].label == "热"
    assert items[1].keyword == "测试网页热搜二"


def test_weibo_cookie_provider_splits_hot_value_category():
    html = """
    <table>
      <tr>
        <td class="td-01">1</td>
        <td class="td-02"><a href="/weibo?q=movie">movie topic</a><span>movie 1033108</span><i>hot</i></td>
      </tr>
      <tr>
        <td class="td-01">2</td>
        <td class="td-02"><a href="/weibo?q=plain">plain topic</a><span>98765</span></td>
      </tr>
    </table>
    """

    items = WeiboCookieHotSearchProvider(cookie="SUB=fake")._parse_items(html, limit=2)

    assert items[0].hot_value == "1033108"
    assert items[0].category_label == "movie"
    assert items[0].label == "hot"
    assert items[0].raw["hot_value_raw"] == "movie 1033108"
    assert items[1].hot_value == "98765"
    assert items[1].category_label is None


def test_weibo_cookie_provider_falls_back_without_cookie():
    response = WeiboCookieHotSearchProvider(cookie=None).fetch(limit=2)

    assert response.fallback_used is True
    assert len(response.items) == 2
    assert "WEIBO_COOKIE" in (response.error or "")


def test_baidu_top_provider_parses_json_payload():
    html = r'''
    <script>
      window.__DATA__ = {
        "cards":[
          {"content":[
            {"word":"百度热榜话题一","index":"1","hotScore":"998877","rawUrl":"https:\/\/example.com\/a"},
            {"word":"百度热榜话题二","index":"2","hotScore":"123456"}
          ]}
        ]
      }
    </script>
    '''

    items = BaiduTopHotSearchProvider()._parse_items(html, limit=2)

    assert [item.keyword for item in items] == ["百度热榜话题一", "百度热榜话题二"]
    assert items[0].platform == "baidu"
    assert items[0].original_rank == 1
    assert items[0].hot_value == "998877"
    assert items[0].url == "https://example.com/a"


def test_zhihu_hot_provider_parses_api_payload():
    payload = {
        "data": [
            {
                "target": {
                    "id": "123",
                    "title": "知乎热榜问题一",
                    "excerpt": "问题摘要",
                    "url": "https://api.zhihu.com/questions/123",
                },
                "detail_text": "123 万热度",
            }
        ]
    }

    items = ZhihuHotListProvider()._parse_items(payload, limit=1)

    assert items[0].keyword == "知乎热榜问题一"
    assert items[0].platform == "zhihu"
    assert items[0].hot_value == "1230000"
    assert items[0].url == "https://www.zhihu.com/question/123"


def test_bilibili_ranking_provider_parses_api_payload():
    payload = {
        "data": {
            "list": [
                {
                    "bvid": "BV123",
                    "title": "B站热门视频一",
                    "desc": "视频简介",
                    "owner": {"name": "UP主"},
                    "stat": {"view": 456789},
                    "short_link_v2": "https://b23.tv/BV123",
                }
            ]
        }
    }

    items = BilibiliRankingProvider()._parse_items(payload, limit=1)

    assert items[0].keyword == "B站热门视频一"
    assert items[0].platform == "bilibili"
    assert items[0].hot_value == "456789"
    assert items[0].url == "https://b23.tv/BV123"
    assert items[0].raw["author"] == "UP主"


def test_bilibili_ranking_provider_parses_legacy_payload():
    payload = {
        "data": {
            "list": [
                {
                    "bvid": "BV456",
                    "title": "B站旧接口热门视频",
                    "author": "旧接口UP",
                    "video_review": 12345,
                }
            ]
        }
    }

    items = BilibiliRankingProvider()._parse_items(payload, limit=1)

    assert items[0].keyword == "B站旧接口热门视频"
    assert items[0].hot_value == "12345"
    assert items[0].url == "https://www.bilibili.com/video/BV456"
    assert items[0].raw["author"] == "旧接口UP"


def test_weibo_cookie_provider_detects_login_redirect():
    class Response:
        url = "https://login.sina.com.cn/sso/login.php"
        text = ""

    try:
        WeiboCookieHotSearchProvider(cookie="SUB=fake")._raise_for_login_redirect(Response())
    except ValueError as exc:
        assert "invalid or expired" in str(exc)
    else:
        raise AssertionError("login redirect should raise ValueError")


def test_visible_capture_provider_extracts_hashtags():
    sample_dir = Path(".rag_index") / f"visible-test-{uuid4().hex}"
    sample_dir.mkdir(parents=True)
    (sample_dir / "capture.json").write_text(
        """
        {
          "page_title": "微博热搜",
          "samples": [
            {
              "body_text": "#测试热搜一# 正文内容 转发 评论 赞\\n#测试热搜二# 另一条内容"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    response = VisibleCaptureHotSearchProvider(sample_dirs=[sample_dir]).fetch(limit=2)

    assert response.fallback_used is False
    assert [item.keyword for item in response.items] == ["测试热搜一", "测试热搜二"]
    assert response.items[0].source == "weibo_visible_capture"


def test_visible_capture_provider_filters_page_title_noise():
    sample_dir = Path(".rag_index") / f"visible-noise-test-{uuid4().hex}"
    sample_dir.mkdir(parents=True)
    (sample_dir / "capture.json").write_text(
        """
        {
          "page_title": "微博 – 随时随地发现新鲜事",
          "samples": [
            {
              "body_text": "微博 – 随时随地发现新鲜事\\n#真实热搜话题# 正文内容\\n今日观察"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    response = VisibleCaptureHotSearchProvider(sample_dirs=[sample_dir]).fetch(limit=3)

    assert [item.keyword for item in response.items] == ["真实热搜话题"]
