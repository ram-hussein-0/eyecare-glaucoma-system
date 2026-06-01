import shutil
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.api.deps import get_patient
from backend.core.config import get_settings
from backend.db.database import execute, fetch_all, fetch_one
from backend.services.model_service import GlaucomaModelService, ModelNotConfiguredError, ScreeningPrediction

router = APIRouter(prefix="/screening", tags=["screening"])


@router.post("/analyze")
def analyze(
    file: UploadFile = File(...),
    notes: str | None = Form(default=None),
    patient: dict = Depends(get_patient),
):
    settings = get_settings()
    suffix = Path(file.filename or "fundus_image.jpg").suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image format. Please upload JPG, PNG, BMP, or WEBP.")
    filename = f"patient_{patient['id']}_{int(time.time())}{suffix}"
    destination = settings.uploads_path / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    service = GlaucomaModelService()
    try:
        prediction = service.predict(destination)
    except ModelNotConfiguredError as exc:
        prediction = ScreeningPrediction(
            probability=None,
            confidence=None,
            risk_level="Model Not Configured",
            recommendation=f"The image was uploaded successfully, but the glaucoma model is not configured yet: {exc}",
            model_name="not-configured",
            model_status="not_configured",
            threshold_uncertain=settings.model_threshold_uncertain,
            threshold_high=settings.model_threshold_high,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model service error: {exc}") from exc

    result_id = execute(
        """INSERT INTO screening_results(
            patient_id, image_path, probability, confidence, risk_level,
            threshold_uncertain, threshold_high, recommendation, model_name, model_status, notes
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (
            patient["id"],
            str(destination.relative_to(settings.db_path.parent.parent) if destination.is_relative_to(settings.db_path.parent.parent) else destination),
            prediction.probability,
            prediction.confidence,
            prediction.risk_level,
            prediction.threshold_uncertain,
            prediction.threshold_high,
            prediction.recommendation,
            prediction.model_name,
            prediction.model_status,
            notes,
        ),
    )
    return fetch_one("SELECT * FROM screening_results WHERE id = ?", (result_id,))


@router.get("/mine")
def mine(patient: dict = Depends(get_patient)):
    return fetch_all(
        "SELECT * FROM screening_results WHERE patient_id = ? ORDER BY datetime(created_at) DESC",
        (patient["id"],),
    )


@router.get("/{result_id}")
def detail(result_id: int, patient: dict = Depends(get_patient)):
    result = fetch_one("SELECT * FROM screening_results WHERE id = ? AND patient_id = ?", (result_id, patient["id"]))
    if not result:
        raise HTTPException(status_code=404, detail="Screening result was not found.")
    return result
