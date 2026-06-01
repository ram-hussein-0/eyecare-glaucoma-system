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

from frontend.app_utils.auth import require_role, load_me
from frontend.app_utils.api import api_get, api_put
from frontend.app_utils.ui import hero, section, setup_page, stat_card, status_badge

setup_page("Doctor Dashboard", "")
me = require_role("doctor")
profile = me.get("profile") or {}
hero("Doctor dashboard", f"Welcome, {profile.get('full_name') or me['user']['full_name']}. Manage your professional profile and review your appointment workflow.", "Doctor portal")

section("Application status")
status_badge(profile.get("status"))
if profile.get("status") != "approved":
    st.warning("Your profile will appear to patients after admin approval.")

appointments = []
try:
    appointments = api_get("/appointments/doctor/mine")
except Exception:
    pass

c1, c2, c3 = st.columns(3)
with c1: stat_card("Total appointments", len(appointments))
with c2: stat_card("Confirmed", len([a for a in appointments if a["status"] == "confirmed"]))
with c3: stat_card("Completed", len([a for a in appointments if a["status"] == "completed"]))

section("Professional profile")
with st.form("profile_form"):
    full_name = st.text_input("Full name", value=profile.get("full_name") or "")
    specialization = st.text_input("Specialization", value=profile.get("specialization") or "Ophthalmology")
    clinic_location = st.text_input("Clinic location", value=profile.get("clinic_location") or "")
    phone = st.text_input("Phone", value=profile.get("phone") or "")
    experience_years = st.number_input("Experience years", min_value=0, max_value=80, value=int(profile.get("experience_years") or 0))
    bio = st.text_area("Bio", value=profile.get("bio") or "")
    submitted = st.form_submit_button("Save profile", use_container_width=True)
if submitted:
    try:
        api_put("/doctors/me/profile", {
            "full_name": full_name,
            "specialization": specialization,
            "clinic_location": clinic_location,
            "phone": phone,
            "experience_years": int(experience_years),
            "bio": bio,
        })
        load_me(force=True)
        st.success("Profile updated.")
        st.rerun()
    except Exception as exc:
        st.error(str(exc))
