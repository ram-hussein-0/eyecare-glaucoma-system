from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterator

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.core.config import get_settings
from backend.db.database import fetch_all
from backend.services.llm_service import (
    LLMService,
    LLMStreamError,
)
from backend.services.reranker_service import (
    RerankerService,
)
from backend.services.text_preprocessing_service import (
    chunk_text,
    clean_for_rag,
)
from backend.services.vector_store_service import (
    RAGVectorStore,
)


@dataclass
class RetrievedChunk:
    title: str
    content: str
    score: float
    source: str = "knowledge_base"
    chunk_id: str | None = None
    retrieval_mode: str = "unknown"


class RAGService:
    """RAG orchestration service."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = LLMService()
        self.reranker = RerankerService()

    @staticmethod
    def _bool_env(
        name: str,
        default: bool,
    ) -> bool:
        raw = os.getenv(
            name,
            "true"
            if default
            else "false",
        )

        return (
            raw.strip().lower()
            in {
                "1",
                "true",
                "yes",
                "on",
            }
        )

    def warm_up(self) -> dict:
        """Prepare local RAG models/index before the first chat request."""

        mode = os.getenv(
            "RAG_RETRIEVAL_MODE",
            "embedding",
        ).strip().lower()

        status: dict = {
            "retrieval_mode":
                mode,
            "vector_store":
                None,
            "reranker":
                self.reranker.mode(),
        }

        if mode == "embedding":
            status[
                "vector_store"
            ] = (
                RAGVectorStore()
                .warm_up()
            )

        self.reranker.warm_up()

        return status

    def _load_documents_for_fallback(
        self,
    ) -> list[dict]:
        docs: list[dict] = []

        for p in sorted(
            self.settings.rag_docs_path.glob(
                "*.md"
            )
        ):
            processed = clean_for_rag(
                p.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )

            if processed.text:
                docs.append(
                    {
                        "title":
                            p.stem.replace(
                                "_",
                                " ",
                            ).title(),
                        "content":
                            processed.text,
                        "source":
                            f"file:{p.name}",
                    }
                )

        for row in fetch_all(
            "SELECT title, content "
            "FROM rag_documents "
            "WHERE is_active = 1 "
            "ORDER BY updated_at DESC, created_at DESC"
        ):
            processed = clean_for_rag(
                row["content"]
            )

            if processed.text:
                docs.append(
                    {
                        "title":
                            row["title"],
                        "content":
                            processed.text,
                        "source":
                            "database:rag_documents",
                    }
                )

        return docs

    def _retrieve_tfidf_fallback(
        self,
        query: str,
        k: int = 12,
    ) -> list[RetrievedChunk]:
        docs = (
            self
            ._load_documents_for_fallback()
        )

        units: list[dict] = []

        for doc in docs:
            for index, chunk in enumerate(
                chunk_text(
                    doc["content"]
                ),
                start=1,
            ):
                units.append(
                    {
                        "title":
                            f"{doc['title']} "
                            f"· chunk {index}",
                        "content":
                            chunk,
                        "source":
                            doc["source"],
                        "chunk_id":
                            f"{doc['source']}"
                            f"#chunk:{index}",
                    }
                )

        if not units:
            return []

        processed_query = (
            clean_for_rag(
                query
            ).text
            or query
        )

        corpus = [
            u["title"]
            + "\n"
            + u["content"]
            for u
            in units
        ]

        vectorizer = TfidfVectorizer(
            stop_words=None,
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
        )

        matrix = (
            vectorizer
            .fit_transform(
                corpus
                + [
                    processed_query
                ]
            )
        )

        scores = cosine_similarity(
            matrix[-1],
            matrix[:-1],
        ).ravel()

        ranked = sorted(
            enumerate(
                scores
            ),
            key=lambda x: x[1],
            reverse=True,
        )[:k]

        return [
            RetrievedChunk(
                title=units[i][
                    "title"
                ],
                content=units[i][
                    "content"
                ],
                score=float(
                    score
                ),
                source=units[i][
                    "source"
                ],
                chunk_id=units[i][
                    "chunk_id"
                ],
                retrieval_mode=(
                    "tfidf_fallback"
                ),
            )
            for i, score
            in ranked
            if score > 0
        ]

    def retrieve(
        self,
        query: str,
        k: int | None = None,
    ) -> list[RetrievedChunk]:
        final_k = (
            k
            or int(
                os.getenv(
                    "RAG_TOP_K",
                    "4",
                )
            )
        )

        candidate_k = int(
            os.getenv(
                "RAG_CANDIDATE_K",
                "12",
            )
        )

        mode = os.getenv(
            "RAG_RETRIEVAL_MODE",
            "embedding",
        ).strip().lower()

        candidates: list[
            RetrievedChunk
        ] = []

        if mode == "embedding":
            try:
                results = (
                    RAGVectorStore()
                    .search(
                        query,
                        k=candidate_k,
                    )
                )

                candidates = [
                    RetrievedChunk(
                        title=r.title,
                        content=r.content,
                        score=r.score,
                        source=r.source,
                        chunk_id=r.chunk_id,
                        retrieval_mode=(
                            "chroma_embedding"
                        ),
                    )
                    for r
                    in results
                ]

            except Exception as exc:
                candidates = (
                    self
                    ._retrieve_tfidf_fallback(
                        query,
                        k=candidate_k,
                    )
                )

                if candidates:
                    candidates[
                        0
                    ].content = (
                        "[Embedding retrieval "
                        "was unavailable, so a "
                        "local fallback was used.]\n\n"
                        + candidates[
                            0
                        ].content
                    )

        if not candidates:
            candidates = (
                self
                ._retrieve_tfidf_fallback(
                    query,
                    k=candidate_k,
                )
            )

        return self.reranker.rerank(
            query,
            candidates,
            top_n=final_k,
        )

    @staticmethod
    def _context(
        chunks: list[
            RetrievedChunk
        ],
    ) -> str:
        return "\n\n---\n\n".join(
            f"Title: {c.title}\n"
            f"Source: {c.source}\n"
            f"Vector score: "
            f"{c.score:.3f}\n"
            f"Rerank score: "
            f"{getattr(c, 'rerank_score', None)}\n"
            f"Mode: "
            f"{c.retrieval_mode}\n"
            f"{c.content}"
            for c
            in chunks
        )

    @staticmethod
    def _sources(
        chunks: list[
            RetrievedChunk
        ],
    ) -> list[dict]:
        return [
            {
                "title":
                    c.title,
                "score":
                    round(
                        c.score,
                        4,
                    ),
                "rerank_score":
                    getattr(
                        c,
                        "rerank_score",
                        None,
                    ),
                "source":
                    c.source,
                "chunk_id":
                    c.chunk_id,
                "retrieval_mode":
                    c.retrieval_mode,
            }
            for c
            in chunks
        ]

    @staticmethod
    def _retrieval_only_answer(
        chunks: list[
            RetrievedChunk
        ],
    ) -> str:
        return (
            "I found the following relevant "
            "information in the knowledge base:\n\n"
            + "\n\n".join(
                f"- {c.title}: "
                f"{c.content[:850]}"
                for c
                in chunks[:3]
            )
        )

    def answer(
        self,
        query: str,
    ) -> dict:
        chunks = self.retrieve(
            query
        )

        if not chunks:
            return {
                "answer": (
                    "I could not find relevant "
                    "knowledge-base content for "
                    "this question. Please add "
                    "a document from the admin "
                    "panel or ask a more specific "
                    "question."
                ),
                "mode":
                    "no_retrieval_results",
                "sources":
                    [],
            }

        context = self._context(
            chunks
        )

        llm_result = (
            self.llm
            .answer_with_context(
                query,
                context,
            )
        )

        if (
            llm_result.enabled
            and llm_result.answer
        ):
            answer = (
                llm_result.answer
            )
            answer_mode = (
                "chroma_retrieval_"
                "rerank_plus_llm"
            )
        else:
            answer = (
                self
                ._retrieval_only_answer(
                    chunks
                )
            )
            answer_mode = (
                "chroma_retrieval_"
                "rerank_only"
            )

        return {
            "answer":
                answer,
            "mode":
                answer_mode,
            "sources":
                self._sources(
                    chunks
                ),
        }

    def stream_answer(
        self,
        query: str,
    ) -> Iterator[dict]:
        """Yield user-facing streaming events without changing RAG grounding."""

        yield {
            "type":
                "status",
            "stage":
                "retrieval",
            "message": (
                "Reviewing approved "
                "reference material..."
            ),
        }

        chunks = self.retrieve(
            query
        )

        if not chunks:
            answer = (
                "I could not find relevant "
                "knowledge-base content for "
                "this question. Please add "
                "a document from the admin "
                "panel or ask a more specific "
                "question."
            )

            yield {
                "type":
                    "delta",
                "text":
                    answer,
            }

            yield {
                "type":
                    "done",
                "mode":
                    "no_retrieval_results",
                "sources":
                    [],
            }

            return

        sources = self._sources(
            chunks
        )

        yield {
            "type":
                "status",
            "stage":
                "generation",
            "message": (
                "Preparing the answer..."
            ),
        }

        if not self.llm.is_enabled():
            answer = (
                self
                ._retrieval_only_answer(
                    chunks
                )
            )

            yield {
                "type":
                    "delta",
                "text":
                    answer,
            }

            yield {
                "type":
                    "done",
                "mode": (
                    "chroma_retrieval_"
                    "rerank_only"
                ),
                "sources":
                    sources,
            }

            return

        context = self._context(
            chunks
        )

        emitted = False

        try:
            for delta in (
                self.llm
                .stream_answer_with_context(
                    query,
                    context,
                )
            ):
                emitted = True

                yield {
                    "type":
                        "delta",
                    "text":
                        delta,
                }

        except LLMStreamError:
            if not emitted:
                fallback = (
                    self
                    ._retrieval_only_answer(
                        chunks
                    )
                )

                yield {
                    "type":
                        "delta",
                    "text":
                        fallback,
                }

                yield {
                    "type":
                        "done",
                    "mode": (
                        "chroma_retrieval_"
                        "rerank_only"
                    ),
                    "sources":
                        sources,
                }

                return

            yield {
                "type":
                    "error",
                "message": (
                    "The answer stream was "
                    "interrupted before completion."
                ),
            }

            yield {
                "type":
                    "done",
                "mode": (
                    "chroma_retrieval_"
                    "rerank_plus_llm_stream_partial"
                ),
                "sources":
                    sources,
            }

            return

        yield {
            "type":
                "done",
            "mode": (
                "chroma_retrieval_"
                "rerank_plus_llm_stream"
            ),
            "sources":
                sources,
        }
