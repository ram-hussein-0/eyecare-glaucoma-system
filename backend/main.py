from __future__ import annotations

import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from backend.api import (
    admin,
    appointments,
    assistant,
    auth,
    doctors,
    reports,
    screening,
    symptoms,
)
from backend.core.config import (
    get_settings,
)
from backend.db.database import (
    init_db,
)
from backend.services.rag_service import (
    RAGService,
)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.on_event("startup")
def startup() -> None:
    init_db()

    if not _bool_env(
        "RAG_WARMUP_ON_STARTUP",
        True,
    ):
        print(
            "RAG startup warm-up: disabled"
        )
        return

    started = time.perf_counter()

    try:
        status = (
            RAGService()
            .warm_up()
        )

        elapsed = (
            time.perf_counter()
            - started
        )

        print(
            "RAG startup warm-up: "
            f"ready in {elapsed:.2f}s | "
            f"{status}"
        )

    except Exception as exc:
        elapsed = (
            time.perf_counter()
            - started
        )

        # Do not prevent the rest of the site from starting.
        # Retrieval already has local fallback behavior.
        print(
            "RAG startup warm-up: "
            f"degraded after {elapsed:.2f}s | "
            f"{type(exc).__name__}: {exc}"
        )


@app.get("/health")
def health():
    return {
        "status":
            "ok",
        "app":
            settings.app_name,
    }


app.include_router(
    auth.router
)
app.include_router(
    doctors.router
)
app.include_router(
    appointments.router
)
app.include_router(
    screening.router
)
app.include_router(
    symptoms.router
)
app.include_router(
    reports.router
)
app.include_router(
    assistant.router
)
app.include_router(
    admin.router
)


@app.get("/")
def root():
    return {
        "app":
            "OptiCare Glaucoma Screening",
        "status":
            "running",
        "docs":
            "/docs",
    }
