from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


def _bool_env(name: str, default: bool = False) -> bool:
    raw = _env(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int, min_value: int, max_value: int) -> int:
    try:
        value = int(_env(name, str(default)))
    except ValueError:
        value = default
    return max(min_value, min(max_value, value))


def _model_name() -> str:
    return _env("RERANKER_MODEL_NAME", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")


@lru_cache(maxsize=1)
def _load_cross_encoder():
    try:
        from sentence_transformers import CrossEncoder
    except Exception as exc:
        raise RuntimeError(
            "sentence-transformers is required for cross-encoder reranking. "
            "Run: python3 -m pip install -r requirements.txt"
        ) from exc

    model_name = _model_name()
    device = _env("RERANKER_DEVICE", "cpu")
    local_files_only = _bool_env("RERANKER_LOCAL_FILES_ONLY", False)

    try:
        return CrossEncoder(
            model_name,
            device=device,
            local_files_only=local_files_only,
        )
    except TypeError:
        # Compatibility fallback for older sentence-transformers versions.
        return CrossEncoder(model_name, device=device)


class RerankerService:
    """Second-stage ranking service for RAG.

    First stage:
        vector_store_service retrieves candidate chunks quickly.

    Second stage:
        this service uses a Cross-Encoder to score (question, chunk) pairs
        more accurately, then keeps the strongest chunks for answer generation.
    """

    def mode(self) -> str:
        return _env("RERANKER_MODE", "cross_encoder").strip().lower()

    def _heuristic_rerank(self, query: str, chunks: list[Any], top_n: int) -> list[Any]:
        query_terms = set(re.findall(r"[\w\u0600-\u06FF]{3,}", query.lower()))

        scored = []
        for chunk in chunks:
            text = f"{getattr(chunk, 'title', '')} {getattr(chunk, 'content', '')}".lower()
            chunk_terms = set(re.findall(r"[\w\u0600-\u06FF]{3,}", text))
            overlap = len(query_terms & chunk_terms)
            base_score = float(getattr(chunk, "score", 0.0))
            final_score = base_score + (0.03 * overlap)

            setattr(chunk, "rerank_score", final_score)
            setattr(chunk, "retrieval_mode", getattr(chunk, "retrieval_mode", "embedding") + "+heuristic_rerank")
            scored.append((final_score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_n]]

    def rerank(self, query: str, chunks: list[Any], top_n: int | None = None) -> list[Any]:
        if not chunks:
            return []

        top_n = top_n or _int_env("RERANKER_TOP_N", 4, 1, 20)
        mode = self.mode()

        if mode in {"", "none", "off", "disabled"}:
            return chunks[:top_n]

        if mode == "heuristic":
            return self._heuristic_rerank(query, chunks, top_n)

        if mode != "cross_encoder":
            return chunks[:top_n]

        try:
            model = _load_cross_encoder()
            batch_size = _int_env("RERANKER_BATCH_SIZE", 4, 1, 32)

            pairs = [(query, getattr(c, "content", "")) for c in chunks]
            scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=False)

            scored = []
            for chunk, score in zip(chunks, scores):
                rerank_score = float(score)
                setattr(chunk, "rerank_score", rerank_score)
                setattr(chunk, "retrieval_mode", getattr(chunk, "retrieval_mode", "embedding") + "+cross_encoder_rerank")
                scored.append((rerank_score, chunk))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for _, c in scored[:top_n]]

        except Exception as exc:
            # Keep the system working even if the reranker model fails to load.
            fallback = self._heuristic_rerank(query, chunks, top_n)
            if fallback:
                fallback[0].content = (
                    "[Cross-encoder reranker failed; heuristic reranking was used instead. "
                    f"Reason: {exc}]\n\n" + fallback[0].content
                )
            return fallback
