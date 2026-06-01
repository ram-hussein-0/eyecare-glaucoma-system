from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.api.deps import get_doctor, get_patient
from backend.db.database import execute, fetch_one
from backend.services.appointment_service import book_appointment, doctor_appointments, get_appointment, patient_appointments

router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: str
    start_time: str
    end_time: str
    reason: str | None = Field(default=None, max_length=500)


@router.post("/book")
def book(payload: AppointmentCreate, patient: dict = Depends(get_patient)):
    return book_appointment(patient["id"], payload.doctor_id, payload.appointment_date, payload.start_time, payload.end_time, payload.reason)


@router.get("/mine")
def mine(patient: dict = Depends(get_patient)):
    return patient_appointments(patient["id"])


@router.get("/doctor/mine")
def mine_doctor(doctor: dict = Depends(get_doctor)):
    return doctor_appointments(doctor["id"])


@router.get("/{appointment_id}")
def detail(appointment_id: int, patient: dict = Depends(get_patient)):
    appt = get_appointment(appointment_id)
    if appt["patient_id"] != patient["id"]:
        raise HTTPException(status_code=403, detail="This appointment does not belong to your account.")
    return appt


@router.patch("/{appointment_id}/cancel")
def cancel(appointment_id: int, patient: dict = Depends(get_patient)):
    appt = get_appointment(appointment_id)
    if appt["patient_id"] != patient["id"]:
        raise HTTPException(status_code=403, detail="This appointment does not belong to your account.")
    if appt["status"] != "confirmed":
        raise HTTPException(status_code=400, detail="Only confirmed appointments can be cancelled.")
    execute("UPDATE appointments SET status='cancelled', cancelled_at=CURRENT_TIMESTAMP WHERE id=?", (appointment_id,))
    return get_appointment(appointment_id)


@router.patch("/{appointment_id}/complete")
def complete(appointment_id: int, doctor: dict = Depends(get_doctor)):
    appt = get_appointment(appointment_id)
    if appt["doctor_id"] != doctor["id"]:
        raise HTTPException(status_code=403, detail="This appointment does not belong to your schedule.")
    execute("UPDATE appointments SET status='completed' WHERE id=?", (appointment_id,))
    return get_appointment(appointment_id)
