# Ensure project root is importable when Streamlit executes pages directly.
from pathlib import Path
import sys

_PROJECT_ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "backend").exists() and (p / "frontend").exists()
)
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from frontend.app_utils.auth import load_me, login
from frontend.app_utils.api import api_post
from frontend.app_utils.ui import feature_card, hero, info_strip, setup_page


def _role_home(role: str) -> str:
    return {
        "patient": "pages/02_Patient_Dashboard.py",
        "doctor": "pages/08_Doctor_Dashboard.py",
        "admin": "pages/11_Admin_Panel.py",
    }.get(role, "Home.py")


setup_page("Login / Register", "login")

me = load_me()
if me:
    role = me.get("user", {}).get("role", "patient")
    st.switch_page(_role_home(role))

hero("Secure access", "Sign in, create a patient account, or submit a doctor application for admin approval.", "Authentication")

left, right = st.columns([1.05, 1])
with left:
    feature_card("shield", "Role-based portals", "Patients can access screening, reports, and bookings. Doctors can manage schedules after approval. Admin users supervise applications and knowledge-base content.")
with right:
    info_strip("Secure onboarding", "Patients can create an account immediately. Doctor applications are reviewed before appearing in the public booking list.", "shield")

tabs = st.tabs(["Sign in", "Patient account", "Doctor application"])

with tabs[0]:
    with st.form("login_form"):
        email = st.text_input("Email", value="patient@example.com")
        password = st.text_input("Password", value="Patient@12345", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    if submitted:
        try:
            login(email, password)
            me = load_me(force=True)
            role = me.get("user", {}).get("role", "patient") if me else "patient"
            st.switch_page(_role_home(role))
        except Exception as exc:
            st.error(str(exc))

with tabs[1]:
    with st.form("patient_register"):
        full_name = st.text_input("Full name")
        email = st.text_input("Email", key="patient_email")
        password = st.text_input("Password", type="password", key="patient_password")
        phone = st.text_input("Phone")
        col1, col2 = st.columns(2)
        age = col1.number_input("Age", min_value=0, max_value=120, value=40)
        gender = col2.selectbox("Gender", ["", "Female", "Male", "Other"])
        city = st.text_input("City")
        notes = st.text_area("Medical notes", placeholder="Optional: family history, previous eye pressure, diabetes, hypertension...")
        submitted = st.form_submit_button("Create patient account", use_container_width=True)
    if submitted:
        try:
            api_post("/auth/register/patient", {
                "full_name": full_name, "email": email, "password": password, "phone": phone,
                "age": int(age), "gender": gender or None, "city": city, "medical_notes": notes,
            })
            st.success("Patient account created. You can sign in now.")
        except Exception as exc:
            st.error(str(exc))

with tabs[2]:
    info_strip("Doctor approval required", "Doctor profiles appear to patients only after admin approval.", "shield")
    with st.form("doctor_register"):
        full_name = st.text_input("Doctor full name")
        email = st.text_input("Email", key="doctor_email")
        password = st.text_input("Password", type="password", key="doctor_password")
        phone = st.text_input("Phone", key="doctor_phone")
        specialization = st.text_input("Specialization", value="Ophthalmology")
        clinic_location = st.text_input("Clinic location")
        experience_years = st.number_input("Experience years", min_value=0, max_value=80, value=5)
        bio = st.text_area("Professional bio")
        submitted = st.form_submit_button("Submit doctor application", use_container_width=True)
    if submitted:
        try:
            api_post("/auth/register/doctor", {
                "full_name": full_name, "email": email, "password": password, "phone": phone,
                "specialization": specialization, "clinic_location": clinic_location,
                "experience_years": int(experience_years), "bio": bio,
            })
            st.success("Doctor application submitted. It will appear to patients after approval.")
        except Exception as exc:
            st.error(str(exc))
