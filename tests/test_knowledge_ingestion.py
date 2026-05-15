from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

import app.api.routes as routes
from app.core.config import Settings
from app.main import app
from app.rag.embeddings import LocalHashEmbeddingClient
from app.rag.knowledge import KnowledgeLoader
from app.rag.vector_store import LocalVectorStore, VectorRetriever
from app.schemas.comment import KnowledgeIngestRequest
from app.services.knowledge_ingestion_service import KnowledgeIngestionService


def test_knowledge_ingestion_saves_markdown_and_rebuilds_index():
    workspace = Path(".rag_index") / f"knowledge-ingest-test-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )

    result = KnowledgeIngestionService(settings).ingest(
        KnowledgeIngestRequest(
            topic="某品牌文案翻车",
            source_url="https://example.com/source",
            source_title="公开报道",
            credibility="medium",
            content="品牌文案被质疑表达不当，适合讨论公共表达边界。",
            candidate_pool_id="pool-1",
            candidate_item_id="item-1",
        )
    )

    path = Path(result.path)
    assert path.exists()
    assert "某品牌文案翻车" in path.read_text(encoding="utf-8")
    assert result.rebuild_stats
    assert result.rebuild_stats["chunk_count"] >= 1


def test_knowledge_loader_reads_inbox_recursively():
    workspace = Path(".rag_index") / f"knowledge-loader-inbox-test-{uuid4().hex}"
    inbox = workspace / "knowledge" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "topic.md").write_text("平台售后规则争议，需要整理事实点。", encoding="utf-8")

    loader = KnowledgeLoader(workspace / "knowledge")
    chunks = loader.load_chunks()

    assert chunks
    assert chunks[0].source == "inbox/topic.md"


def test_knowledge_ingestion_records_can_be_listed_and_read():
    workspace = Path(".rag_index") / f"knowledge-record-list-test-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )
    service = KnowledgeIngestionService(settings)
    result = service.ingest(
        KnowledgeIngestRequest(
            topic="平台售后规则争议",
            source_url="https://example.com/report",
            source_title="公开报道",
            credibility="high",
            content="公开资料显示，争议集中在售后规则解释和商家责任边界。",
            candidate_pool_id="pool-1",
            candidate_item_id="item-1",
            operator_note="人工确认过来源。",
            rebuild_index=False,
        )
    )

    records = service.list_records(candidate_pool_id="pool-1", candidate_item_id="item-1")
    detail = service.get_record(Path(result.path).stem)

    assert len(records) == 1
    assert records[0].source_title == "公开报道"
    assert records[0].preview
    assert detail.content == "公开资料显示，争议集中在售后规则解释和商家责任边界。"
    assert detail.operator_note == "人工确认过来源。"


def test_ingested_knowledge_can_be_retrieved():
    workspace = Path(".rag_index") / f"knowledge-ingest-retrieve-test-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )
    KnowledgeIngestionService(settings).ingest(
        KnowledgeIngestRequest(
            topic="平台售后规则争议",
            content="平台售后规则被质疑不透明，讨论重点是消费者权益和规则解释。",
            rebuild_index=False,
        )
    )

    loader = KnowledgeLoader(workspace / "knowledge")
    embeddings = LocalHashEmbeddingClient()
    store = LocalVectorStore(workspace / "index.json")
    store.rebuild(loader, embeddings)
    results = VectorRetriever(store, embeddings).retrieve("平台售后规则", top_k=1)

    assert results
    assert "消费者权益" in results[0].content


def test_knowledge_ingest_api(monkeypatch):
    workspace = Path(".rag_index") / f"api-knowledge-ingest-test-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )
    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    client = TestClient(app)

    response = client.post(
        "/api/knowledge/ingest",
        json={
            "topic": "平台售后规则争议",
            "content": "公开信息显示，争议集中在规则解释和售后责任边界。",
            "source_url": "https://example.com/report",
            "credibility": "medium",
            "rebuild_index": True,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert Path(body["path"]).exists()
    assert body["rebuild_stats"]["chunk_count"] >= 1


def test_knowledge_inbox_api(monkeypatch):
    workspace = Path(".rag_index") / f"api-knowledge-inbox-test-{uuid4().hex}"
    settings = Settings(
        OPENAI_API_KEY=None,
        KNOWLEDGE_DIR=workspace / "knowledge",
        RAG_INDEX_PATH=workspace / "index.json",
    )
    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    client = TestClient(app)

    ingest_response = client.post(
        "/api/knowledge/ingest",
        json={
            "topic": "平台售后规则争议",
            "content": "公开资料显示，争议集中在售后规则解释和商家责任边界。",
            "source_title": "公开报道",
            "candidate_pool_id": "pool-1",
            "candidate_item_id": "item-1",
            "rebuild_index": False,
        },
    )
    record_id = Path(ingest_response.json()["path"]).stem

    list_response = client.get(
        "/api/knowledge/inbox",
        params={"candidate_pool_id": "pool-1", "candidate_item_id": "item-1"},
    )
    detail_response = client.get(f"/api/knowledge/inbox/{record_id}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == record_id
    assert detail_response.status_code == 200
    assert "售后规则解释" in detail_response.json()["content"]
