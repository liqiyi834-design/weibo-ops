from app_ui.streamlit_app import research_source_content, research_source_to_knowledge_payload


def test_research_source_content_includes_summary_and_highlights():
    content = research_source_content(
        {
            "title": "官方通报",
            "url": "https://www.gov.cn/example",
            "domain": "www.gov.cn",
            "credibility": "high",
            "published_date": "2026-05-24",
            "summary": "事件已有官方说明。",
            "highlights": ["事实一", "事实二"],
        }
    )

    assert "官方通报" in content
    assert "事件已有官方说明" in content
    assert "- 事实一" in content
    assert "www.gov.cn" in content


def test_research_source_to_knowledge_payload_links_candidate_and_rebuilds():
    payload = research_source_to_knowledge_payload(
        {
            "title": "媒体报道",
            "url": "https://example.com/report",
            "domain": "example.com",
            "credibility": "medium",
            "summary": "报道梳理了事件背景。",
        },
        pool={"id": "pool-1"},
        item={"id": "item-1", "keyword": "某热点事件"},
        rebuild_index=True,
    )

    assert payload["topic"] == "某热点事件"
    assert payload["source_url"] == "https://example.com/report"
    assert payload["source_title"] == "媒体报道"
    assert payload["credibility"] == "medium"
    assert payload["candidate_pool_id"] == "pool-1"
    assert payload["candidate_item_id"] == "item-1"
    assert payload["needs_review"] is True
    assert payload["rebuild_index"] is True
