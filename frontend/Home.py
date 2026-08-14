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

from frontend.app_utils.auth import load_me
from frontend.app_utils.api import api_get
from frontend.app_utils.ui import feature_card, hero, info_strip, section, setup_page, stat_card

setup_page("OptiCare Glaucoma Screening", "home")

try:
    api_get("/health")
    backend_ok = True
except Exception:
    backend_ok = False

hero(
    "Modern glaucoma screening and ophthalmology appointments",
    "A secure eye-care platform that combines appointment booking, preliminary fundus-image glaucoma screening, symptom triage, patient reports, and a knowledge-grounded assistant.",
    "Eye-care workflow platform",
)

if not backend_ok:
    st.error("The service is temporarily unavailable. Please try again shortly.")

cols = st.columns(3)
with cols[0]:
    feature_card("eye", "Fundus image screening", "Upload a fundus image and receive a structured preliminary glaucoma-risk assessment.")
with cols[1]:
    feature_card("calendar", "Appointment booking", "Browse approved ophthalmologists, select available slots, and manage confirmed or cancelled appointments.")
with cols[2]:
    feature_card("file", "Reports and assistant", "Generate polished reports and ask the AI assistant about the platform, screening workflow, and booking steps.")

section("Platform flow", "A clear patient journey from preliminary screening to ophthalmology follow-up.")
flow = st.columns(4)
steps = [
    ("1", "Create account", "Secure patient or doctor access."),
    ("2", "Complete screening", "Image workflow and symptom triage."),
    ("3", "Generate report", "Preview and export a structured summary."),
    ("4", "Book follow-up", "Choose an available ophthalmologist slot."),
]
for col, (n, title, body) in zip(flow, steps):
    with col:
        stat_card(f"Step {n}", title, body)

me = load_me()
section("Secure access")
if me:
    role = me.get("user", {}).get("role", "patient")
    destination = {
        "patient": "pages/02_Patient_Dashboard.py",
        "doctor": "pages/08_Doctor_Dashboard.py",
        "admin": "pages/11_Admin_Panel.py",
    }.get(role, "pages/02_Patient_Dashboard.py")
    st.success(f"You are signed in as {me['user']['full_name']} ({role}).")
    st.page_link(destination, label="Open your dashboard")
else:
    info_strip("Sign in required", "Create or access your secure account to use screening, reports, appointments, and role-specific tools.", "shield")
    st.page_link("pages/01_Login_Register.py", label="Login / Register")

info_strip(
    "Clinical scope",
    "The platform provides preliminary screening support and appointment-related guidance. Diagnosis and treatment decisions remain the responsibility of an ophthalmologist.",
    "shield",
)
