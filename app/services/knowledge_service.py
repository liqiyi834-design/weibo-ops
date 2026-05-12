from pathlib import Path

from app.core.config import Settings
from app.rag.embeddings import build_embedding_client
from app.rag.vector_store import LocalVectorStore
from app.rag.vector_store import VectorRetriever
from app.rag.retriever import KeywordRetriever
from app.schemas.comment import RetrievedKnowledge
from app.services.generation_pipeline import build_knowledge_loader


class KnowledgeService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.loader = build_knowledge_loader(Path(settings.knowledge_dir))
        self.embeddings = build_embedding_client(settings)
        self.store = LocalVectorStore(Path(settings.rag_index_path))
        self.keyword_retriever = KeywordRetriever(self.loader)
        self.vector_retriever = VectorRetriever(self.store, self.embeddings)

    def rebuild(self) -> dict[str, int | bool | str]:
        stats = self.store.rebuild(self.loader, self.embeddings)
        return {
            "success": True,
            "index_path": str(self.settings.rag_index_path),
            **stats,
        }

    def search(self, query: str, top_k: int = 5) -> list[RetrievedKnowledge]:
        results = self.vector_retriever.retrieve(query, top_k=top_k)
        if results:
            return results
        return self.keyword_retriever.retrieve(query, top_k=top_k)
