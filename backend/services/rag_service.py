from __future__ import annotations

import os
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.core.config import get_settings
from backend.db.database import fetch_all
from backend.services.llm_service import LLMService
from backend.services.reranker_service import RerankerService
from backend.services.text_preprocessing_service import chunk_text, clean_for_rag
from backend.services.vector_store_service import RAGVectorStore


@dataclass
class RetrievedChunk:
    title: str
    content: str
    score: float
    source: str = "knowledge_base"
    chunk_id: str | None = None
    retrieval_mode: str = "unknown"


class RAGService:
    """RAG orchestration service.

    AI service boundaries:
    - OCR: backend/services/ocr_service.py
    - NLP cleaning/chunking: backend/services/text_preprocessing_service.py
    - Embeddings: backend/services/embedding_service.py
    - Vector DB: backend/services/vector_store_service.py
    - Reranking: backend/services/reranker_service.py
    - LLM: backend/services/llm_service.py
    - RAG orchestration: this file
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = LLMService()
        self.reranker = RerankerService()

    def _load_documents_for_fallback(self) -> list[dict]:
        docs: list[dict] = []

        for p in sorted(self.settings.rag_docs_path.glob("*.md")):
            processed = clean_for_rag(p.read_text(encoding="utf-8", errors="replace"))
            if processed.text:
                docs.append({
                    "title": p.stem.replace("_", " ").title(),
                    "content": processed.text,
                    "source": f"file:{p.name}",
                })

        for row in fetch_all("SELECT title, content FROM rag_documents WHERE is_active = 1 ORDER BY updated_at DESC, created_at DESC"):
            processed = clean_for_rag(row["content"])
            if processed.text:
                docs.append({
                    "title": row["title"],
                    "content": processed.text,
                    "source": "database:rag_documents",
                })

        return docs

    def _retrieve_tfidf_fallback(self, query: str, k: int = 12) -> list[RetrievedChunk]:
        docs = self._load_documents_for_fallback()
        units: list[dict] = []

        for doc in docs:
            for index, chunk in enumerate(chunk_text(doc["content"]), start=1):
                units.append({
                    "title": f"{doc['title']} · chunk {index}",
                    "content": chunk,
                    "source": doc["source"],
                    "chunk_id": f"{doc['source']}#chunk:{index}",
                })

        if not units:
            return []

        processed_query = clean_for_rag(query).text or query
        corpus = [u["title"] + "\n" + u["content"] for u in units]

        vectorizer = TfidfVectorizer(
            stop_words=None,
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
        )

        matrix = vectorizer.fit_transform(corpus + [processed_query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]

        return [
            RetrievedChunk(
                title=units[i]["title"],
                content=units[i]["content"],
                score=float(score),
                source=units[i]["source"],
                chunk_id=units[i]["chunk_id"],
                retrieval_mode="tfidf_fallback",
            )
            for i, score in ranked
            if score > 0
        ]

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        final_k = k or int(os.getenv("RAG_TOP_K", "4"))
        candidate_k = int(os.getenv("RAG_CANDIDATE_K", "12"))
        mode = os.getenv("RAG_RETRIEVAL_MODE", "embedding").strip().lower()

        candidates: list[RetrievedChunk] = []

        if mode == "embedding":
            try:
                results = RAGVectorStore().search(query, k=candidate_k)
                candidates = [
                    RetrievedChunk(
                        title=r.title,
                        content=r.content,
                        score=r.score,
                        source=r.source,
                        chunk_id=r.chunk_id,
                        retrieval_mode="chroma_embedding",
                    )
                    for r in results
                ]
            except Exception as exc:
                candidates = self._retrieve_tfidf_fallback(query, k=candidate_k)
                if candidates:
                    candidates[0].content = (
                        "[Embedding/Chroma retrieval failed, so TF-IDF fallback was used. "
                        f"Reason: {exc}]\n\n" + candidates[0].content
                    )

        if not candidates:
            candidates = self._retrieve_tfidf_fallback(query, k=candidate_k)

        return self.reranker.rerank(query, candidates, top_n=final_k)

    def answer(self, query: str) -> dict:
        chunks = self.retrieve(query)

        if not chunks:
            answer = (
                "I could not find relevant knowledge-base content for this question. "
                "Please add a document from the admin panel or ask a more specific question."
            )
            return {"answer": answer, "mode": "no_retrieval_results", "sources": []}

        context = "\n\n---\n\n".join(
            f"Title: {c.title}\n"
            f"Source: {c.source}\n"
            f"Vector score: {c.score:.3f}\n"
            f"Rerank score: {getattr(c, 'rerank_score', None)}\n"
            f"Mode: {c.retrieval_mode}\n"
            f"{c.content}"
            for c in chunks
        )

        llm_result = self.llm.answer_with_context(query, context)

        if llm_result.enabled and llm_result.answer:
            answer = llm_result.answer
            answer_mode = "chroma_retrieval_rerank_plus_llm"
        else:
            answer = (
                "I found the following relevant information in the knowledge base:\n\n"
                + "\n\n".join(f"- {c.title}: {c.content[:850]}" for c in chunks[:3])
            )
            answer_mode = "chroma_retrieval_rerank_only"

        return {
            "answer": answer,
            "mode": answer_mode,
            "sources": [
                {
                    "title": c.title,
                    "score": round(c.score, 4),
                    "rerank_score": getattr(c, "rerank_score", None),
                    "source": c.source,
                    "chunk_id": c.chunk_id,
                    "retrieval_mode": c.retrieval_mode,
                }
                for c in chunks
            ],
        }
