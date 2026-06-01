import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.deps import get_patient
from backend.db.database import execute, fetch_all, fetch_one
from backend.services.symptom_service import assess_symptoms

router = APIRouter(prefix="/symptoms", tags=["symptoms"])


class SymptomAssessmentRequest(BaseModel):
    answers: dict


@router.post("/assess")
def assess(payload: SymptomAssessmentRequest, patient: dict = Depends(get_patient)):
    result = assess_symptoms(payload.answers)
    assessment_id = execute(
        """INSERT INTO symptom_assessments(patient_id, answers_json, score, risk_level, recommendation)
           VALUES(?,?,?,?,?)""",
        (patient["id"], json.dumps(payload.answers), result.score, result.risk_level, result.recommendation),
    )
    return fetch_one("SELECT * FROM symptom_assessments WHERE id = ?", (assessment_id,))


@router.get("/mine")
def mine(patient: dict = Depends(get_patient)):
    return fetch_all(
        "SELECT * FROM symptom_assessments WHERE patient_id = ? ORDER BY datetime(created_at) DESC",
        (patient["id"],),
    )
