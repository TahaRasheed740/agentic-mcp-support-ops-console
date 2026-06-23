from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastembed import TextEmbedding

from tracedesk_api.config import get_settings


class LocalEmbeddingService:
    dimensions = 384

    def __init__(self, model_name: str, cache_dir: Path) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._model = TextEmbedding(model_name=model_name, cache_dir=str(cache_dir))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts, batch_size=32)]

    def embed_query(self, text: str) -> list[float]:
        vector = next(iter(self._model.query_embed(text)))
        return [float(value) for value in vector]


@lru_cache
def get_embedding_service() -> LocalEmbeddingService:
    settings = get_settings()
    return LocalEmbeddingService(settings.embedding_model, settings.embedding_cache_dir)
