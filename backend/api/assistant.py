from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.deps import get_current_user
from backend.services.rag_service import RAGService


router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(payload: ChatRequest, user: dict = Depends(get_current_user)):
    """RAG-only assistant.

    The assistant no longer answers questions by reading operational database
    tables such as appointments, patient reports, doctors, or admin metrics.

    It only uses the approved RAG knowledge base:
    documents -> Chroma vector database -> cross-encoder reranking -> optional LLM.

    The user dependency remains only to require authentication.
    """
    question = payload.message.strip()

    if not question:
        return {
            "answer": "Please write a question first.",
            "mode": "empty_question",
            "sources": [],
            "database_intent": None,
            "database_rows": [],
            "policy_note": "RAG-only mode is active. Operational database access is disabled for the assistant.",
        }

    result = RAGService().answer(question)
    result["database_intent"] = None
    result["database_rows"] = []
    result["policy_note"] = "RAG-only mode: the assistant answers from indexed knowledge documents only."
    return result


@router.get("/booking/suggestions")
def booking_suggestions(user: dict = Depends(get_current_user)):
    """Compatibility endpoint kept to avoid breaking older UI calls.

    Booking suggestions through the assistant are disabled in RAG-only mode.
    Users should use the Doctors & Booking page.
    """
    return []
