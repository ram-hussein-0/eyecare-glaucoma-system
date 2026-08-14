from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)


class EmbeddingConfigurationError(RuntimeError):
    pass


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


def _bool_env(name: str, default: bool = False) -> bool:
    raw = _env(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _model_name() -> str:
    return _env("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-base")


@lru_cache(maxsize=1)
def _load_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:
        raise EmbeddingConfigurationError(
            "sentence-transformers is not installed. Run: python3 -m pip install -r requirements.txt"
        ) from exc

    model_name = _model_name()
    local_files_only = _bool_env("EMBEDDING_LOCAL_FILES_ONLY", True)
    device = _env("EMBEDDING_DEVICE", "cpu")

    try:
        return SentenceTransformer(model_name, device=device, local_files_only=local_files_only)
    except Exception as exc:
        raise EmbeddingConfigurationError(
            f"Could not load embedding model {model_name!r}. "
            "If EMBEDDING_LOCAL_FILES_ONLY=true, make sure the model exists in Hugging Face cache. "
            f"Original error: {exc}"
        ) from exc


class EmbeddingService:
    """Local embedding service.

    Uses a local SentenceTransformer model. For intfloat/e5 models:
    - documents should be prefixed with 'passage:'
    - questions should be prefixed with 'query:'
    """

    def __init__(self) -> None:
        self.model_name = _model_name()

    def _format_document(self, text: str) -> str:
        if "e5" in self.model_name.lower():
            return "passage: " + (text or "")
        return text or ""

    def _format_query(self, text: str) -> str:
        if "e5" in self.model_name.lower():
            return "query: " + (text or "")
        return text or ""

    def warm_up(self) -> None:
        # Load the cached local model and execute one tiny inference so the
        # first real user query does not pay the model initialization cost.
        self.encode_query("glaucoma screening")

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        model = _load_sentence_transformer()
        formatted = [self._format_document(t) for t in texts]
        vectors = model.encode(
            formatted,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype="float32")

    def encode_query(self, query: str) -> np.ndarray:
        model = _load_sentence_transformer()
        vector = model.encode(
            [self._format_query(query)],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vector, dtype="float32")
