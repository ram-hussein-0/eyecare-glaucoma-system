from __future__ import annotations

import json
from typing import Iterator

from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.responses import (
    StreamingResponse,
)
from pydantic import BaseModel

from backend.api.deps import (
    get_current_user,
)
from backend.services.rag_service import (
    RAGService,
)


router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)


class ChatRequest(BaseModel):
    message: str


def _sse(
    payload: dict,
) -> str:
    return (
        "data: "
        + json.dumps(
            payload,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )
        + "\n\n"
    )


@router.post("/chat")
def chat(
    payload: ChatRequest,
    user: dict = Depends(
        get_current_user
    ),
):
    """Compatibility non-streaming RAG endpoint."""

    question = payload.message.strip()

    if not question:
        return {
            "answer":
                "Please write a question first.",
            "mode":
                "empty_question",
            "sources":
                [],
            "database_intent":
                None,
            "database_rows":
                [],
            "policy_note": (
                "The assistant answers from "
                "approved knowledge documents only."
            ),
        }

    result = RAGService().answer(
        question
    )

    result[
        "database_intent"
    ] = None

    result[
        "database_rows"
    ] = []

    result[
        "policy_note"
    ] = (
        "The assistant answers from "
        "approved knowledge documents only."
    )

    return result


@router.post("/chat/stream")
def chat_stream(
    payload: ChatRequest,
    user: dict = Depends(
        get_current_user
    ),
):
    """Stream grounded RAG answers as Server-Sent Events."""

    question = payload.message.strip()

    def events() -> Iterator[str]:
        if not question:
            yield _sse(
                {
                    "type":
                        "delta",
                    "text":
                        "Please write a question first.",
                }
            )

            yield _sse(
                {
                    "type":
                        "done",
                    "mode":
                        "empty_question",
                    "sources":
                        [],
                    "policy_note": (
                        "The assistant answers from "
                        "approved knowledge documents only."
                    ),
                }
            )

            return

        try:
            for event in (
                RAGService()
                .stream_answer(
                    question
                )
            ):
                if (
                    event.get(
                        "type"
                    )
                    == "done"
                ):
                    event[
                        "database_intent"
                    ] = None
                    event[
                        "database_rows"
                    ] = []
                    event[
                        "policy_note"
                    ] = (
                        "The assistant answers from "
                        "approved knowledge documents only."
                    )

                yield _sse(
                    event
                )

        except Exception:
            yield _sse(
                {
                    "type":
                        "error",
                    "message": (
                        "The assistant could not "
                        "complete this request."
                    ),
                }
            )

            yield _sse(
                {
                    "type":
                        "done",
                    "mode":
                        "stream_error",
                    "sources":
                        [],
                    "policy_note": (
                        "The assistant answers from "
                        "approved knowledge documents only."
                    ),
                }
            )

    return StreamingResponse(
        events(),
        media_type=(
            "text/event-stream"
        ),
        headers={
            "Cache-Control":
                "no-cache",
            "X-Accel-Buffering":
                "no",
            "Connection":
                "keep-alive",
        },
    )


@router.get(
    "/booking/suggestions"
)
def booking_suggestions(
    user: dict = Depends(
        get_current_user
    ),
):
    """Compatibility endpoint kept for older UI calls."""

    return []
