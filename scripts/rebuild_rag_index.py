from __future__ import annotations

from backend.services.vector_store_service import RAGVectorStore


if __name__ == "__main__":
    result = RAGVectorStore().rebuild()
    print("RAG vector database rebuilt successfully.")
    for key, value in result.items():
        print(f"{key}: {value}")
