from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

from openai import OpenAI

from app.core.config import Settings


class BaseEmbeddingClient(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class LocalHashEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in self._tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return normalize(vector)

    def _tokens(self, text: str) -> list[str]:
        lowered = text.lower()
        ascii_terms = re.findall(r"[a-z0-9_]{2,}", lowered)
        chinese_terms = [lowered[i : i + 2] for i in range(max(len(lowered) - 1, 0))]
        return ascii_terms + [term for term in chinese_terms if term.strip()]


class OpenAIEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        self.model = settings.openai_embedding_model
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.request_timeout_seconds,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    return sum(left[index] * right[index] for index in range(size))


def build_embedding_client(settings: Settings) -> BaseEmbeddingClient:
    if settings.use_openai_embeddings and settings.openai_api_key:
        return OpenAIEmbeddingClient(settings)
    return LocalHashEmbeddingClient()
