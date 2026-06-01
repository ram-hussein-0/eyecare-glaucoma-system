from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.api.deps import require_role
from backend.db.database import execute, fetch_all, fetch_one
from backend.services.document_ingestion_service import extract_knowledge_from_upload

router = APIRouter(prefix="/admin", tags=["admin"])


class DoctorStatusUpdate(BaseModel):
    status: str


class RAGDocumentCreate(BaseModel):
    title: str
    content: str


@router.get("/metrics")
def metrics(admin: dict = Depends(require_role("admin"))):
    items = {}
    for name, query in {
        "patients": "SELECT COUNT(*) AS c FROM patients",
        "doctors": "SELECT COUNT(*) AS c FROM doctors",
        "pending_doctors": "SELECT COUNT(*) AS c FROM doctors WHERE status='pending'",
        "appointments": "SELECT COUNT(*) AS c FROM appointments",
        "screenings": "SELECT COUNT(*) AS c FROM screening_results",
        "reports": "SELECT COUNT(*) AS c FROM patient_reports",
    }.items():
        items[name] = fetch_one(query)["c"]
    return items


@router.get("/doctor-applications")
def doctor_applications(admin: dict = Depends(require_role("admin"))):
    return fetch_all("SELECT * FROM doctors ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, created_at DESC")


@router.patch("/doctors/{doctor_id}/status")
def update_doctor_status(doctor_id: int, payload: DoctorStatusUpdate, admin: dict = Depends(require_role("admin"))):
    if payload.status not in {"pending", "approved", "rejected", "suspended"}:
        raise HTTPException(status_code=400, detail="Invalid doctor status.")
    if not fetch_one("SELECT id FROM doctors WHERE id=?", (doctor_id,)):
        raise HTTPException(status_code=404, detail="Doctor was not found.")
    execute("UPDATE doctors SET status=? WHERE id=?", (payload.status, doctor_id))
    return fetch_one("SELECT * FROM doctors WHERE id=?", (doctor_id,))


@router.get("/users")
def users(admin: dict = Depends(require_role("admin"))):
    return fetch_all("SELECT id, email, role, full_name, is_active, created_at FROM users ORDER BY created_at DESC")


@router.get("/appointments")
def appointments(admin: dict = Depends(require_role("admin"))):
    return fetch_all(
        """
        SELECT a.*, p.full_name AS patient_name, d.full_name AS doctor_name
        FROM appointments a
        JOIN patients p ON p.id = a.patient_id
        JOIN doctors d ON d.id = a.doctor_id
        ORDER BY date(a.appointment_date) DESC, a.start_time DESC
        """
    )


@router.get("/rag-documents")
def list_rag_documents(admin: dict = Depends(require_role("admin"))):
    return fetch_all("SELECT * FROM rag_documents ORDER BY is_active DESC, updated_at DESC, created_at DESC")


@router.post("/rag-documents")
def create_rag_document(payload: RAGDocumentCreate, admin: dict = Depends(require_role("admin"))):
    doc_id = execute("INSERT INTO rag_documents(title, content, is_active) VALUES(?,?,1)", (payload.title, payload.content))
    return fetch_one("SELECT * FROM rag_documents WHERE id=?", (doc_id,))


@router.post("/rag-documents/upload")
async def upload_rag_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    admin: dict = Depends(require_role("admin")),
):
    try:
        doc_title, content, metadata = await extract_knowledge_from_upload(file, title)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    doc_id = execute(
        "INSERT INTO rag_documents (title, content, is_active) VALUES (?, ?, 1)",
        (doc_title, content),
    )
    result = fetch_one("SELECT * FROM rag_documents WHERE id=?", (doc_id,)) or {"title": doc_title, "content": content, "is_active": 1}
    result = dict(result)
    result["upload_metadata"] = metadata
    return result


@router.patch("/rag-documents/{doc_id}/toggle")
def toggle_rag_document(doc_id: int, admin: dict = Depends(require_role("admin"))):
    doc = fetch_one("SELECT * FROM rag_documents WHERE id=?", (doc_id,))
    if not doc:
        raise HTTPException(status_code=404, detail="Document was not found.")
    execute("UPDATE rag_documents SET is_active=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (0 if doc["is_active"] else 1, doc_id))
    return fetch_one("SELECT * FROM rag_documents WHERE id=?", (doc_id,))


@router.delete("/rag-documents/{doc_id}")
def delete_rag_document(doc_id: int, admin: dict = Depends(require_role("admin"))):
    doc = fetch_one("SELECT * FROM rag_documents WHERE id=?", (doc_id,))
    if not doc:
        raise HTTPException(status_code=404, detail="Document was not found.")

    execute("DELETE FROM rag_documents WHERE id=?", (doc_id,))

    # Force the local vector index to rebuild on the next assistant query.
    # We do not import the embedding/vector services here to keep deletion fast
    # and avoid loading the embedding model during a simple admin action.
    try:
        source_hash = Path(__file__).resolve().parents[2] / "data" / "vector_index" / "source_hash.txt"
        if source_hash.exists():
            source_hash.unlink()
    except Exception:
        pass

    return {
        "deleted": True,
        "id": doc_id,
        "title": doc["title"],
        "message": "RAG document deleted. Vector index will rebuild automatically on the next query.",
    }


from backend.services.vector_store_service import RAGVectorStore



def _invalidate_rag_vector_index() -> None:
    """Force Chroma/vector index rebuild on the next query.

    We only delete the source hash marker instead of loading the embedding model
    during every admin toggle/delete action.
    """
    try:
        root = Path(__file__).resolve().parents[2]
        for candidate in [
            root / "data" / "chroma_db" / "source_hash.txt",
            root / "data" / "vector_index" / "source_hash.txt",
        ]:
            if candidate.exists():
                candidate.unlink()
    except Exception:
        pass


@router.get("/vector-store/status")
def vector_store_status(admin: dict = Depends(require_role("admin"))):
    docs = fetch_all("SELECT id, title, is_active FROM rag_documents ORDER BY id DESC")
    active_docs = [d for d in docs if d["is_active"]]

    status = {
        "backend": "chroma",
        "documents_total": len(docs),
        "documents_active": len(active_docs),
        "is_current": False,
        "chunks": 0,
        "collection": None,
        "db_dir": None,
        "error": None,
    }

    try:
        store = RAGVectorStore()
        status["is_current"] = bool(store.is_current())
        status["collection"] = getattr(store, "collection_name", None)
        status["db_dir"] = str(getattr(store, "db_dir", ""))
        try:
            status["chunks"] = int(store._collection().count())
        except Exception:
            status["chunks"] = 0
    except Exception as exc:
        status["error"] = str(exc)

    return status


@router.post("/vector-store/rebuild")
def rebuild_vector_store(admin: dict = Depends(require_role("admin"))):
    result = RAGVectorStore().rebuild()
    return {
        "rebuilt": True,
        **result,
    }


@router.delete("/rag-documents/{doc_id}")
def delete_rag_document(doc_id: int, admin: dict = Depends(require_role("admin"))):
    doc = fetch_one("SELECT * FROM rag_documents WHERE id=?", (doc_id,))
    if not doc:
        raise HTTPException(status_code=404, detail="Document was not found.")

    execute("DELETE FROM rag_documents WHERE id=?", (doc_id,))
    _invalidate_rag_vector_index()

    return {
        "deleted": True,
        "id": doc_id,
        "title": doc["title"],
        "message": "RAG document deleted. Chroma will rebuild on the next query or manual rebuild.",
    }
