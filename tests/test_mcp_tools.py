from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.llm.client import MockLLMClient
from app.services.draft_service import DraftService
import mcp_server.tools as tools
from mcp_server.tools import (
    classify_topic_tool,
    generate_comment_tool,
    get_hot_topics_tool,
    list_drafts_tool,
    rebuild_knowledge_tool,
    retrieve_knowledge_tool,
    safety_check_tool,
    search_knowledge_tool,
    select_comment_topics_tool,
    send_review_message_tool,
    save_draft_tool,
    update_draft_tool,
)


def test_mcp_generate_comment_tool_uses_pipeline():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    result = generate_comment_tool(
        topic="某品牌文案翻车",
        context_text="品牌文案被质疑表达不当。",
        style="pr_critic",
        settings=settings,
        llm=MockLLMClient(),
    )

    assert result["topic"] == "某品牌文案翻车"
    assert result["style"] == "pr_critic"
    assert result["output"]["short_comment"]
    assert result["safety"]["is_safe"] is True


def test_mcp_knowledge_tools():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    rebuild_result = rebuild_knowledge_tool(settings=settings)
    search_result = search_knowledge_tool("品牌文案翻车", settings=settings)
    retrieve_result = retrieve_knowledge_tool("品牌文案翻车", settings=settings)

    assert rebuild_result["success"] is True
    assert rebuild_result["chunk_count"] > 0
    assert search_result
    assert retrieve_result
    assert "source" in search_result[0]
    assert "source" in retrieve_result[0]


def test_mcp_classify_topic_tool():
    result = classify_topic_tool(
        topic="某品牌母亲节文案翻车",
        context_text="品牌文案被质疑表达不当。",
    )

    assert result["topic"] == "某品牌母亲节文案翻车"
    assert result["category"]
    assert result["risk_level"] in {"low", "medium", "high"}
    assert result["recommended_style"]
    assert isinstance(result["risk_notes"], list)


def test_mcp_safety_check_tool_reviews_text_without_publishing():
    result = safety_check_tool(
        text="目前公开信息有限，先讨论事实边界和规则责任。",
        topic="平台售后规则引争议",
    )

    assert result["topic"] == "平台售后规则引争议"
    assert result["risk_level"] in {"low", "medium", "high", "blocked"}
    assert result["recommendation"] in {"review_before_publish", "human_review_required", "blocked"}
    assert "issues" in result


def test_mcp_send_review_message_tool_uses_controlled_sender():
    class FakeSender:
        def send_review_message(self, request):
            return type(
                "Response",
                (),
                {
                    "model_dump": lambda self: {
                        "ok": True,
                        "channel": request.channel,
                        "configured": True,
                        "skipped": False,
                        "chunk_count": 1,
                        "sent_count": 1,
                        "message_ids": [42],
                        "errors": [],
                        "dedupe_key": request.dedupe_key,
                    }
                },
            )()

    result = send_review_message_tool(
        title="本轮候选摘要",
        body="候选 A",
        message_type="candidate_summary",
        dedupe_key="test-key",
        service=FakeSender(),
    )

    assert result["ok"] is True
    assert result["message_ids"] == [42]
    assert result["dedupe_key"] == "test-key"


def test_mcp_get_hot_topics_tool():
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))
    result = get_hot_topics_tool(limit=3, settings=settings)

    assert result["items"]
    assert len(result["items"]) <= 3
    assert "keyword" in result["items"][0]


def test_mcp_select_comment_topics_tool():
    result = select_comment_topics_tool(
        topics=[
            {"rank": 1, "keyword": "某品牌母亲节文案翻车", "hot_value": "1000000", "label": "热"},
            {"rank": 2, "keyword": "平台售后规则引争议", "hot_value": "900000"},
            {"rank": 3, "keyword": "外交会谈相关消息", "hot_value": "800000"},
        ],
        max_results=3,
        enrich_metrics=False,
    )

    assert result["evaluated_count"] == 3
    assert result["selected"]
    assert result["selected"][0]["reason"]


def test_mcp_draft_tools(monkeypatch):
    test_root = Path(".rag_index") / f"mcp-draft-test-{uuid4().hex}"
    monkeypatch.setattr(tools, "DraftService", lambda: DraftService(root=test_root))
    settings = Settings(OPENAI_API_KEY=None, KNOWLEDGE_DIR=Path("app/knowledge"))

    draft = save_draft_tool(
        topic="某品牌文案翻车",
        context_text="品牌文案被质疑表达不当。",
        style="pr_critic",
        settings=settings,
        llm=MockLLMClient(),
    )
    listed = list_drafts_tool()
    updated = update_draft_tool(draft["id"], status="reviewed", operator_note="已审")

    assert draft["status"] == "draft"
    assert listed[0]["id"] == draft["id"]
    assert updated["status"] == "reviewed"
    assert updated["operator_note"] == "已审"
