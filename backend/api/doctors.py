from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.api.deps import get_doctor, require_role
from backend.db.database import execute, fetch_all, fetch_one
from backend.services.appointment_service import generate_slots_for_doctor

router = APIRouter(prefix="/doctors", tags=["doctors"])


class DoctorProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2)
    specialization: str = "Ophthalmology"
    bio: str | None = None
    clinic_location: str | None = None
    phone: str | None = None
    experience_years: int = Field(default=0, ge=0, le=80)


class AvailabilityCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    slot_minutes: int = Field(default=30, ge=10, le=180)


@router.get("/approved")
def approved_doctors():
    return fetch_all(
        """SELECT id, full_name, specialization, bio, clinic_location, phone, experience_years
           FROM doctors WHERE status = 'approved' ORDER BY full_name"""
    )


@router.get("/{doctor_id}")
def doctor_details(doctor_id: int):
    doctor = fetch_one(
        """SELECT id, full_name, specialization, bio, clinic_location, phone, experience_years
           FROM doctors WHERE id = ? AND status = 'approved'""",
        (doctor_id,),
    )
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor was not found.")
    doctor["availability"] = fetch_all(
        "SELECT * FROM doctor_availability WHERE doctor_id = ? AND is_active = 1 ORDER BY weekday, start_time",
        (doctor_id,),
    )
    return doctor


@router.get("/{doctor_id}/slots")
def doctor_slots(doctor_id: int, date_from: date | None = None, date_to: date | None = None):
    today = date.today()
    date_from = date_from or today
    date_to = date_to or (date_from + timedelta(days=14))
    return generate_slots_for_doctor(doctor_id, date_from, date_to)


@router.get("/me/profile")
def my_doctor_profile(doctor: dict = Depends(get_doctor)):
    return doctor


@router.put("/me/profile")
def update_my_doctor_profile(payload: DoctorProfileUpdate, doctor: dict = Depends(get_doctor)):
    execute(
        """UPDATE doctors SET full_name=?, specialization=?, bio=?, clinic_location=?, phone=?, experience_years=? WHERE id=?""",
        (payload.full_name, payload.specialization, payload.bio, payload.clinic_location, payload.phone, payload.experience_years, doctor["id"]),
    )
    execute("UPDATE users SET full_name=? WHERE id=?", (payload.full_name, doctor["user_id"]))
    return fetch_one("SELECT * FROM doctors WHERE id = ?", (doctor["id"],))


@router.get("/me/availability")
def my_availability(doctor: dict = Depends(get_doctor)):
    return fetch_all(
        "SELECT * FROM doctor_availability WHERE doctor_id = ? AND is_active = 1 ORDER BY weekday, start_time",
        (doctor["id"],),
    )


@router.post("/me/availability")
def add_availability(payload: AvailabilityCreate, doctor: dict = Depends(get_doctor)):
    if doctor["status"] != "approved":
        raise HTTPException(status_code=403, detail="Only approved doctors can manage public availability.")
    if payload.start_time >= payload.end_time:
        raise HTTPException(status_code=400, detail="Start time must be earlier than end time.")
    av_id = execute(
        "INSERT INTO doctor_availability(doctor_id, weekday, start_time, end_time, slot_minutes) VALUES(?,?,?,?,?)",
        (doctor["id"], payload.weekday, payload.start_time, payload.end_time, payload.slot_minutes),
    )
    return fetch_one("SELECT * FROM doctor_availability WHERE id = ?", (av_id,))


@router.delete("/me/availability/{availability_id}")
def delete_availability(availability_id: int, doctor: dict = Depends(get_doctor)):
    row = fetch_one("SELECT * FROM doctor_availability WHERE id = ? AND doctor_id = ?", (availability_id, doctor["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="Availability rule was not found.")
    execute("UPDATE doctor_availability SET is_active = 0 WHERE id = ?", (availability_id,))
    return {"message": "Availability removed."}
