from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from agent.config import AgentSettings, get_settings

logger = logging.getLogger(__name__)


class EmbeddingError(RuntimeError):
    pass


@dataclass(slots=True)
class EmbeddingService:
    settings: AgentSettings | None = None
    client: object | None = None

    def __post_init__(self) -> None:
        if self.settings is None:
            self.settings = get_settings()

    def _get_client(self):
        if self.client is not None:
            return self.client
        try:
            from google import genai
        except Exception as exc:
            raise EmbeddingError("google-genai no está instalado") from exc
        self.client = genai.Client(
            vertexai=True,
            project=self.settings.project_id or None,
            location=self.settings.region,
        )
        return self.client

    def embed_text(self, text: str, *, task_type: str = "RETRIEVAL_DOCUMENT", title: str | None = None) -> list[float]:
        text = text.strip()
        if not text:
            raise ValueError("No se puede generar embedding de texto vacío")
        try:
            from google.genai.types import EmbedContentConfig

            config_kwargs: dict = {
                "task_type": task_type,
                "output_dimensionality": self.settings.embedding_dimension,
            }
            if title:
                config_kwargs["title"] = title[:200]
            response = self._get_client().models.embed_content(
                model=self.settings.embedding_model,
                contents=text,
                config=EmbedContentConfig(**config_kwargs),
            )
            values = response.embeddings[0].values
            return [float(v) for v in values]
        except Exception as exc:
            logger.exception("embedding_generation_failed model=%s", self.settings.embedding_model)
            raise EmbeddingError(f"No se pudo generar embedding: {exc}") from exc

    def embed_texts(self, texts: Iterable[str], *, task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        return [self.embed_text(text, task_type=task_type) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_text(query, task_type="RETRIEVAL_QUERY")
