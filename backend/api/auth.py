from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from backend.api.deps import get_current_user
from backend.core.security import generate_session_token, hash_password, session_expiry, verify_password
from backend.db.database import execute, fetch_one

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PatientRegisterRequest(BaseModel):
    full_name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=8)
    phone: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = None
    city: str | None = None
    medical_notes: str | None = None


class DoctorRegisterRequest(BaseModel):
    full_name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=8)
    phone: str | None = None
    specialization: str = "Ophthalmology"
    clinic_location: str | None = None
    experience_years: int = Field(default=0, ge=0, le=80)
    bio: str | None = None


@router.post("/login")
def login(payload: LoginRequest):
    user = fetch_one("SELECT * FROM users WHERE email = ? AND is_active = 1", (payload.email.lower(),))
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = generate_session_token()
    execute("INSERT INTO sessions(user_id, token, expires_at) VALUES(?,?,?)", (user["id"], token, session_expiry()))
    user.pop("password_hash", None)
    return {"token": token, "user": user}


@router.post("/register/patient")
def register_patient(payload: PatientRegisterRequest):
    email = payload.email.lower()
    if fetch_one("SELECT id FROM users WHERE email = ?", (email,)):
        raise HTTPException(status_code=409, detail="Email is already registered.")
    user_id = execute(
        "INSERT INTO users(email, password_hash, role, full_name) VALUES(?,?,?,?)",
        (email, hash_password(payload.password), "patient", payload.full_name),
    )
    execute(
        """INSERT INTO patients(user_id, full_name, phone, age, gender, city, medical_notes)
           VALUES(?,?,?,?,?,?,?)""",
        (user_id, payload.full_name, payload.phone, payload.age, payload.gender, payload.city, payload.medical_notes),
    )
    return {"message": "Patient account created successfully."}


@router.post("/register/doctor")
def register_doctor(payload: DoctorRegisterRequest):
    email = payload.email.lower()
    if fetch_one("SELECT id FROM users WHERE email = ?", (email,)):
        raise HTTPException(status_code=409, detail="Email is already registered.")
    user_id = execute(
        "INSERT INTO users(email, password_hash, role, full_name) VALUES(?,?,?,?)",
        (email, hash_password(payload.password), "doctor", payload.full_name),
    )
    execute(
        """INSERT INTO doctors(user_id, full_name, specialization, bio, clinic_location, phone, experience_years, status)
           VALUES(?,?,?,?,?,?,?, 'pending')""",
        (user_id, payload.full_name, payload.specialization, payload.bio, payload.clinic_location, payload.phone, payload.experience_years),
    )
    return {"message": "Doctor application submitted. The account will appear to patients after admin approval."}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    user = dict(user)
    user.pop("password_hash", None)
    profile = None
    if user["role"] == "patient":
        profile = fetch_one("SELECT * FROM patients WHERE user_id = ?", (user["id"],))
    elif user["role"] == "doctor":
        profile = fetch_one("SELECT * FROM doctors WHERE user_id = ?", (user["id"],))
    return {"user": user, "profile": profile}


@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
    return {"message": "Logged out."}
