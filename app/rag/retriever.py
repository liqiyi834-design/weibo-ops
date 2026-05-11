import re

from app.rag.knowledge import KnowledgeChunk, KnowledgeLoader
from app.schemas.comment import RetrievedKnowledge


class KeywordRetriever:
    def __init__(self, loader: KnowledgeLoader):
        self.loader = loader

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedKnowledge]:
        chunks = self.loader.load_chunks()
        if not chunks:
            return []

        terms = self._terms(query)
        scored = [(self._score(chunk, terms), chunk) for chunk in chunks]
        scored = [(score, chunk) for score, chunk in scored if score > 0]
        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            RetrievedKnowledge(content=chunk.content, source=chunk.source, score=score)
            for score, chunk in scored[:top_k]
        ]

    def _terms(self, query: str) -> list[str]:
        ascii_terms = re.findall(r"[A-Za-z0-9_]{2,}", query.lower())
        chinese_terms = [query[i : i + 2] for i in range(max(len(query) - 1, 0))]
        return list(dict.fromkeys(ascii_terms + chinese_terms))

    def _score(self, chunk: KnowledgeChunk, terms: list[str]) -> float:
        text = chunk.content.lower()
        hits = sum(text.count(term) for term in terms if term.strip())
        return round(hits / max(len(terms), 1), 4)
