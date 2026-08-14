import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.deps import get_patient
from backend.db.database import execute, fetch_all, fetch_one
from backend.services.fuzzy_assessment_service import FuzzyAssessmentError
from backend.services.symptom_service import assess_symptoms

router = APIRouter(prefix="/symptoms", tags=["eye-health-assessment"])


class SymptomAssessmentRequest(BaseModel):
    answers: dict


@router.post("/assess")
def assess(
    payload: SymptomAssessmentRequest,
    patient: dict = Depends(get_patient),
):
    try:
        result = assess_symptoms(payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FuzzyAssessmentError as exc:
        raise HTTPException(
            status_code=422,
            detail="The eye-health assessment could not be completed.",
        ) from exc

    assessment_id = execute(
        """
        INSERT INTO symptom_assessments(
            patient_id,
            answers_json,
            score,
            risk_level,
            recommendation,
            primary_finding,
            confidence,
            details_json
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            patient["id"],
            json.dumps(payload.answers, ensure_ascii=False),
            result.score,
            result.risk_level,
            result.recommendation,
            result.primary_finding,
            result.confidence,
            result.details_json,
        ),
    )

    return fetch_one(
        "SELECT * FROM symptom_assessments WHERE id = ?",
        (assessment_id,),
    )


@router.get("/mine")
def mine(patient: dict = Depends(get_patient)):
    return fetch_all(
        """
        SELECT *
        FROM symptom_assessments
        WHERE patient_id = ?
        ORDER BY datetime(created_at) DESC
        """,
        (patient["id"],),
    )
