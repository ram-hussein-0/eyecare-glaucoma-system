from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.api.deps import get_patient
from backend.db.database import execute, fetch_all, fetch_one
from backend.services.report_service import build_report

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportCreate(BaseModel):
    title: str = "Eye Screening Report"
    screening_result_id: int | None = None
    symptom_assessment_id: int | None = None
    appointment_id: int | None = None


@router.post("/create")
def create_report(payload: ReportCreate, patient: dict = Depends(get_patient)):
    built = build_report(patient["id"], payload.title, payload.screening_result_id, payload.symptom_assessment_id, payload.appointment_id)
    report_id = execute(
        """INSERT INTO patient_reports(patient_id, title, screening_result_id, symptom_assessment_id, appointment_id, summary, html_path, pdf_path)
           VALUES(?,?,?,?,?,?,?,?)""",
        (patient["id"], payload.title, payload.screening_result_id, payload.symptom_assessment_id, payload.appointment_id, built["summary"], built["html_path"], built["pdf_path"]),
    )
    return fetch_one("SELECT * FROM patient_reports WHERE id = ?", (report_id,))


@router.get("/mine")
def mine(patient: dict = Depends(get_patient)):
    return fetch_all("SELECT * FROM patient_reports WHERE patient_id = ? ORDER BY datetime(created_at) DESC", (patient["id"],))


@router.get("/{report_id}")
def detail(report_id: int, patient: dict = Depends(get_patient)):
    report = fetch_one("SELECT * FROM patient_reports WHERE id = ? AND patient_id = ?", (report_id, patient["id"]))
    if not report:
        raise HTTPException(status_code=404, detail="Report was not found.")
    return report


@router.get("/{report_id}/download/{kind}")
def download(report_id: int, kind: str, patient: dict = Depends(get_patient)):
    if kind not in {"html", "pdf"}:
        raise HTTPException(status_code=400, detail="Unsupported report format.")
    report = fetch_one("SELECT * FROM patient_reports WHERE id = ? AND patient_id = ?", (report_id, patient["id"]))
    if not report:
        raise HTTPException(status_code=404, detail="Report was not found.")
    path_value = report["pdf_path"] if kind == "pdf" else report["html_path"]
    if not path_value:
        raise HTTPException(status_code=404, detail="Report file was not found.")
    path = Path(path_value)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file was not found.")
    media_type = "application/pdf" if kind == "pdf" else "text/html"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.delete("/{report_id}")
def delete_report(report_id: int, patient: dict = Depends(get_patient)):
    report = fetch_one("SELECT * FROM patient_reports WHERE id = ? AND patient_id = ?", (report_id, patient["id"]))
    if not report:
        raise HTTPException(status_code=404, detail="Report was not found.")

    for key in ("html_path", "pdf_path"):
        value = report.get(key)
        if value:
            try:
                path = Path(value)
                if path.exists() and path.is_file():
                    path.unlink()
            except Exception:
                pass

    execute("DELETE FROM patient_reports WHERE id = ? AND patient_id = ?", (report_id, patient["id"]))
    return {"deleted": True, "id": report_id}
