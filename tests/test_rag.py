from pathlib import Path
from uuid import uuid4

from app.rag.embeddings import LocalHashEmbeddingClient
from app.rag.knowledge import KnowledgeLoader
from app.rag.vector_store import LocalVectorStore, VectorRetriever


def test_local_vector_store_rebuild_and_retrieve():
    workspace = Path(".rag_index") / f"test-{uuid4().hex}"
    knowledge_dir = workspace / "knowledge"
    knowledge_dir.mkdir(parents=True)
    (knowledge_dir / "rules.md").write_text(
        "# 品牌公关\n\n品牌文案翻车时，应批评表达和机制，不攻击个人。",
        encoding="utf-8",
    )

    loader = KnowledgeLoader(knowledge_dir)
    embeddings = LocalHashEmbeddingClient()
    store = LocalVectorStore(workspace / "index.json")

    stats = store.rebuild(loader, embeddings)
    results = VectorRetriever(store, embeddings).retrieve("品牌文案翻车", top_k=1)

    assert stats == {"document_count": 1, "chunk_count": 1}
    assert results
    assert results[0].source == "rules.md"
    assert "品牌文案" in results[0].content
