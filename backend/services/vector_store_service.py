from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from backend.core.config import get_settings
from backend.db.database import fetch_all
from backend.services.embedding_service import EmbeddingService
from backend.services.text_preprocessing_service import chunk_text, clean_for_rag


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)


@dataclass
class VectorSearchResult:
    title: str
    content: str
    score: float
    source: str
    chunk_id: str


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


def _float_env(name: str, default: float, min_value: float, max_value: float) -> float:
    try:
        value = float(_env(name, str(default)))
    except ValueError:
        value = default
    return max(min_value, min(max_value, value))


class RAGVectorStore:
    """Chroma-based local vector database for RAG chunks.

    Responsibilities:
    - Load active RAG documents from markdown files and SQLite rag_documents.
    - Clean and chunk the text.
    - Create local multilingual embeddings through embedding_service.py.
    - Store chunks, embeddings, and metadata in a persistent Chroma collection.
    - Perform semantic search for candidate chunks.

    The embedding model is intentionally external to Chroma so the project has
    one clear embedding_service.py.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

        db_dir_raw = _env("CHROMA_DB_DIR", "data/chroma_db")
        db_dir = Path(db_dir_raw)
        self.db_dir = db_dir if db_dir.is_absolute() else ROOT_DIR / db_dir
        self.db_dir.mkdir(parents=True, exist_ok=True)

        self.collection_name = _env("CHROMA_COLLECTION_NAME", "eyecare_rag_chunks")
        self.hash_path = self.db_dir / "source_hash.txt"

        self.embedding = EmbeddingService()

    def _client(self):
        try:
            import chromadb
        except Exception as exc:
            raise RuntimeError("chromadb is not installed. Run: python3 -m pip install -r requirements.txt") from exc

        return chromadb.PersistentClient(path=str(self.db_dir))

    def _collection(self):
        client = self._client()
        return client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _reset_collection(self):
        client = self._client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass

        return client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _load_documents(self) -> list[dict]:
        docs: list[dict] = []

        for p in sorted(self.settings.rag_docs_path.glob("*.md")):
            raw = p.read_text(encoding="utf-8", errors="replace")
            processed = clean_for_rag(raw)
            if processed.text:
                docs.append({
                    "id": f"file:{p.name}",
                    "title": p.stem.replace("_", " ").title(),
                    "content": processed.text,
                    "source": f"file:{p.name}",
                    "source_type": "markdown_file",
                })

        rows = fetch_all(
            "SELECT id, title, content, updated_at, created_at FROM rag_documents "
            "WHERE is_active = 1 ORDER BY updated_at DESC, created_at DESC"
        )

        for row in rows:
            processed = clean_for_rag(row["content"])
            if processed.text:
                docs.append({
                    "id": f"db:{row['id']}",
                    "title": row["title"],
                    "content": processed.text,
                    "source": f"database:rag_documents:{row['id']}",
                    "source_type": "database",
                })

        return docs

    def _build_chunks(self, docs: list[dict]) -> list[dict]:
        units: list[dict] = []

        for doc in docs:
            chunks = chunk_text(doc["content"])

            for idx, chunk in enumerate(chunks, start=1):
                chunk_id = f"{doc['id']}#chunk:{idx}"
                units.append({
                    "chunk_id": chunk_id,
                    "title": f"{doc['title']} · chunk {idx}",
                    "content": chunk,
                    "source": doc["source"],
                    "source_type": doc["source_type"],
                    "document_id": doc["id"],
                    "document_title": doc["title"],
                    "chunk_index": idx,
                })

        return units

    def _source_hash(self, docs: list[dict]) -> str:
        payload = json.dumps(
            [
                {
                    "id": d["id"],
                    "title": d["title"],
                    "content_sha256": hashlib.sha256(d["content"].encode("utf-8")).hexdigest(),
                }
                for d in docs
            ],
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def is_current(self) -> bool:
        docs = self._load_documents()
        current_hash = self._source_hash(docs)

        if not self.hash_path.exists():
            return False

        try:
            collection = self._collection()
            if collection.count() == 0 and docs:
                return False
        except Exception:
            return False

        return self.hash_path.read_text(encoding="utf-8").strip() == current_hash

    def rebuild(self) -> dict:
        docs = self._load_documents()
        units = self._build_chunks(docs)
        collection = self._reset_collection()

        if not units:
            self.hash_path.write_text(self._source_hash(docs), encoding="utf-8")
            return {
                "backend": "chroma",
                "documents": 0,
                "chunks": 0,
                "collection": self.collection_name,
                "db_dir": str(self.db_dir),
            }

        texts_for_embedding = [u["title"] + "\n" + u["content"] for u in units]
        vectors = self.embedding.encode_documents(texts_for_embedding)

        ids = [u["chunk_id"] for u in units]
        documents = [u["content"] for u in units]
        embeddings = vectors.tolist()
        metadatas = [
            {
                "title": u["title"],
                "source": u["source"],
                "source_type": u["source_type"],
                "document_id": u["document_id"],
                "document_title": u["document_title"],
                "chunk_index": u["chunk_index"],
            }
            for u in units
        ]

        # Chroma can accept batches. This avoids very large single calls later.
        batch_size = 128
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                embeddings=embeddings[start:end],
                metadatas=metadatas[start:end],
            )

        self.hash_path.write_text(self._source_hash(docs), encoding="utf-8")

        return {
            "backend": "chroma",
            "documents": len(docs),
            "chunks": len(units),
            "dimension": int(vectors.shape[1]),
            "collection": self.collection_name,
            "db_dir": str(self.db_dir),
        }

    def _ensure_index(self) -> None:
        if _bool_env("RAG_REBUILD_ON_QUERY", True) and not self.is_current():
            self.rebuild()

    def search(self, query: str, k: int | None = None) -> list[VectorSearchResult]:
        self._ensure_index()

        collection = self._collection()
        if collection.count() == 0:
            return []

        candidate_k = k or _int_env("RAG_CANDIDATE_K", 12, 1, 50)
        min_score = _float_env("RAG_MIN_SCORE", 0.18, -1.0, 1.0)

        query_vec = self.embedding.encode_query(query)[0].tolist()

        result = collection.query(
            query_embeddings=[query_vec],
            n_results=min(candidate_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        out: list[VectorSearchResult] = []

        for chunk_id, doc_text, meta, distance in zip(ids, documents, metadatas, distances):
            # Chroma cosine distance is 0 for identical vectors.
            # Convert to similarity-like score.
            score = 1.0 - float(distance)

            if score < min_score:
                continue

            out.append(
                VectorSearchResult(
                    title=meta.get("title", "Untitled chunk"),
                    content=doc_text,
                    score=score,
                    source=meta.get("source", "chroma"),
                    chunk_id=chunk_id,
                )
            )

        return out
