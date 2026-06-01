from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import admin, appointments, assistant, auth, doctors, reports, screening, symptoms
from backend.core.config import get_settings
from backend.db.database import init_db

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(screening.router)
app.include_router(symptoms.router)
app.include_router(reports.router)
app.include_router(assistant.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"app": "OptiCare Glaucoma Screening", "status": "running", "docs": "/docs"}
