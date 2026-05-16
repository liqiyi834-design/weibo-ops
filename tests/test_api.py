from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

import app.api.routes as routes
from app.main import app
from app.services.candidate_pool_service import CandidatePoolService
from app.services.draft_service import DraftService
from app.services.topic_asset_service import TopicAssetService


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_weibo_hot_topics():
    client = TestClient(app)
    response = client.get("/api/hot/weibo?limit=5")
    body = response.json()

    assert response.status_code == 200
    assert body["items"]
    assert len(body["items"]) <= 5
    assert "keyword" in body["items"][0]


def test_knowledge_rebuild():
    client = TestClient(app)
    response = client.post("/api/knowledge/rebuild")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["chunk_count"] > 0


def test_knowledge_search():
    client = TestClient(app)
    client.post("/api/knowledge/rebuild")
    response = client.post("/api/knowledge/search", json={"query": "品牌文案翻车", "top_k": 3})

    assert response.status_code == 200
    assert response.json()


def test_select_comment_topics():
    client = TestClient(app)
    response = client.post(
        "/api/topics/select",
        json={
            "max_results": 3,
            "enrich_metrics": False,
            "topics": [
                {"rank": 1, "keyword": "某品牌母亲节文案翻车", "hot_value": "1000000", "label": "热"},
                {"rank": 2, "keyword": "平台售后规则引争议", "hot_value": "900000"},
                {"rank": 3, "keyword": "外交会谈相关消息", "hot_value": "800000"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["evaluated_count"] == 3
    assert 1 <= len(body["selected"]) <= 3
    assert body["selected"][0]["reason"]
    assert body["selected"][0]["recommended_angle"]


def test_styles_and_accounts_endpoints():
    client = TestClient(app)
    styles_response = client.get("/api/comment/styles")
    accounts_response = client.get("/api/accounts")

    assert styles_response.status_code == 200
    assert accounts_response.status_code == 200
    assert any(style["id"] == "rational_critic" for style in styles_response.json()["styles"])
    assert accounts_response.json()["accounts"][0]["id"] == "today_direct"


def test_create_and_update_candidate_pool(monkeypatch):
    test_root = Path(".rag_index") / f"api-candidate-pool-test-{uuid4().hex}"
    monkeypatch.setattr(routes, "CandidatePoolService", lambda: CandidatePoolService(root=test_root))
    client = TestClient(app)

    create_response = client.post(
        "/api/topic-candidates/pools",
        json={
            "title": "测试候选池",
            "max_results": 3,
            "topics": [
                {"rank": 1, "keyword": "某品牌母亲节文案翻车", "hot_value": "1000000", "label": "热"},
                {"rank": 2, "keyword": "平台售后规则引争议", "hot_value": "900000"},
                {"rank": 3, "keyword": "外交会谈相关消息", "hot_value": "800000"},
            ],
        },
    )
    pool = create_response.json()
    item_id = pool["items"][0]["id"]

    assert create_response.status_code == 200
    assert pool["title"] == "测试候选池"
    assert pool["items"][0]["status"] == "candidate"

    update_response = client.patch(
        f"/api/topic-candidates/pools/{pool['id']}/items/{item_id}",
        json={"status": "selected", "operator_note": "人工确认"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["items"][0]["status"] == "selected"


def test_topic_asset_api(monkeypatch):
    test_root = Path(".rag_index") / f"api-topic-asset-test-{uuid4().hex}"
    monkeypatch.setattr(routes, "TopicAssetService", lambda: TopicAssetService(root=test_root))
    client = TestClient(app)

    create_response = client.post(
        "/api/topic-assets",
        json={
            "canonical_title": "平台售后规则引争议",
            "summary": "适合沉淀为选题资产。",
            "source_platforms": ["weibo"],
            "source_urls": ["https://example.com/topic"],
            "hot_signals": {"rank": 3, "hot_value": "900000"},
            "tags": ["consumer"],
            "risk_level": "low",
            "research_status": "needed",
            "status": "candidate",
        },
    )
    asset = create_response.json()

    assert create_response.status_code == 200
    assert asset["canonical_title"] == "平台售后规则引争议"
    assert asset["status"] == "candidate"

    list_response = client.get("/api/topic-assets")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == asset["id"]

    update_response = client.patch(
        f"/api/topic-assets/{asset['id']}",
        json={"status": "researched", "research_status": "complete"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "researched"
    assert update_response.json()["research_status"] == "complete"


def test_create_and_update_draft(monkeypatch):
    test_root = Path(".rag_index") / f"api-draft-test-{uuid4().hex}"
    monkeypatch.setattr(routes, "DraftService", lambda: DraftService(root=test_root))
    client = TestClient(app)

    create_response = client.post(
        "/api/drafts",
        json={
            "title": "测试草稿",
            "topic": "某品牌文案翻车",
            "context_text": "品牌文案被质疑表达不当。",
            "style": "pr_critic",
            "emotion_level": 6,
            "use_rag": False,
            "candidate_pool_id": "pool-1",
            "candidate_item_id": "item-1",
        },
    )
    draft = create_response.json()

    assert create_response.status_code == 200
    assert draft["title"] == "测试草稿"
    assert draft["status"] == "draft"
    assert draft["generated"]["output"]["short_comment"]

    update_response = client.patch(
        f"/api/drafts/{draft['id']}",
        json={
            "status": "reviewed",
            "operator_note": "已人工审核",
            "edited_text": "人工编辑正文",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "reviewed"
    assert update_response.json()["edited_text"] == "人工编辑正文"


def test_create_zhihu_draft(monkeypatch):
    test_root = Path(".rag_index") / f"api-zhihu-draft-test-{uuid4().hex}"
    monkeypatch.setattr(routes, "DraftService", lambda: DraftService(root=test_root))
    client = TestClient(app)

    create_response = client.post(
        "/api/drafts/zhihu",
        json={
            "title": "知乎测试回答",
            "topic": "平台售后规则争议",
            "question_title": "如何看待平台售后规则争议？",
            "context_text": "公开信息显示，争议集中在规则解释和售后责任边界。",
            "style": "rational_critic",
            "emotion_level": 4,
            "use_rag": False,
            "candidate_pool_id": "pool-1",
            "candidate_item_id": "item-1",
        },
    )
    draft = create_response.json()

    assert create_response.status_code == 200
    assert draft["platform"] == "zhihu"
    assert draft["draft_type"] == "zhihu_answer"
    assert draft["zhihu_answer"]["zhihu_domain"]
    assert draft["zhihu_answer"]["output"]["answer_body"]

    update_response = client.patch(
        f"/api/drafts/{draft['id']}",
        json={
            "status": "published_manually",
            "published_url": "https://www.zhihu.com/question/1/answer/2",
            "performance_note": "人工记录数据。",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["published_url"] == "https://www.zhihu.com/question/1/answer/2"
