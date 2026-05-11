from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.rag.embeddings import BaseEmbeddingClient, cosine_similarity
from app.rag.knowledge import KnowledgeLoader
from app.schemas.comment import RetrievedKnowledge


@dataclass
class VectorRecord:
    chunk_id: str
    source: str
    content: str
    embedding: list[float]


class LocalVectorStore:
    def __init__(self, index_path: Path):
        self.index_path = index_path

    def rebuild(self, loader: KnowledgeLoader, embeddings: BaseEmbeddingClient) -> dict[str, int]:
        chunks = loader.load_chunks()
        vectors = embeddings.embed_texts([chunk.content for chunk in chunks]) if chunks else []
        records = [
            VectorRecord(
                chunk_id=chunk.chunk_id,
                source=chunk.source,
                content=chunk.content,
                embedding=vector,
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"document_count": len({chunk.source for chunk in chunks}), "chunk_count": len(chunks)}

    def load(self) -> list[VectorRecord]:
        if not self.index_path.exists():
            return []
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        return [VectorRecord(**item) for item in data]


class VectorRetriever:
    def __init__(self, store: LocalVectorStore, embeddings: BaseEmbeddingClient):
        self.store = store
        self.embeddings = embeddings

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedKnowledge]:
        records = self.store.load()
        if not records:
            return []

        query_embedding = self.embeddings.embed_query(query)
        scored = [
            (cosine_similarity(query_embedding, record.embedding), record)
            for record in records
        ]
        scored = [(score, record) for score, record in scored if score > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievedKnowledge(content=record.content, source=record.source, score=round(score, 4))
            for score, record in scored[:top_k]
        ]
