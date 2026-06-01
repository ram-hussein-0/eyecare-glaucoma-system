# Ensure project root is importable when Streamlit executes pages directly.
from pathlib import Path
import sys

_PROJECT_ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "backend").exists() and (p / "frontend").exists()
)
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import streamlit as st

from frontend.app_utils.auth import require_role
from frontend.app_utils.api import api_get
from frontend.app_utils.ui import appointment_card, feature_card, hero, risk_badge, section, setup_page, stat_card, status_badge

setup_page("Patient Dashboard", "")
me = require_role("patient")
profile = me.get("profile") or {}
hero("Patient dashboard", f"Welcome, {profile.get('full_name') or me['user']['full_name']}. Track your screening, appointments, and reports from one clinical workspace.", "Patient portal")

appointments = api_get("/appointments/mine")
screenings = api_get("/screening/mine")
symptoms = api_get("/symptoms/mine")
reports = api_get("/reports/mine")

c1, c2, c3, c4 = st.columns(4)
with c1: stat_card("Appointments", len(appointments), "Confirmed, completed, or cancelled")
with c2: stat_card("Screening results", len(screenings), "Fundus image workflow")
with c3: stat_card("Symptom triage", len(symptoms), "Warning-sign assessments")
with c4: stat_card("Reports", len(reports), "Generated summaries")

section("Clinical overview", "Your latest activity and next actions.")
col1, col2 = st.columns(2)
with col1:
    if screenings:
        latest = screenings[0]
        with st.container(border=True):
            st.markdown("### Latest fundus screening")
            risk_badge(latest.get("risk_level"))
            if latest.get("probability") is not None:
                st.metric("Glaucoma risk probability", f"{float(latest['probability'])*100:.1f}%")
            st.write(latest.get("recommendation"))
    else:
        feature_card("", "No fundus screening yet", "Start the screening workflow when you have a suitable fundus image.")
        st.page_link("pages/03_Screening_Center.py", label="Open Screening Center")

with col2:
    upcoming = [a for a in appointments if a["status"] == "confirmed"]
    if upcoming:
        for a in upcoming[:2]:
            appointment_card(a['doctor_name'], a['appointment_date'], f"{a['start_time']} - {a['end_time']}", a['status'], a.get('clinic_location') or '')
    else:
        feature_card("", "No upcoming appointment", "Book an ophthalmology visit to review screening information and clinical concerns.")
        st.page_link("pages/04_Doctors_Booking.py", label="Book an appointment")

section("Quick actions")
qa1, qa2, qa3, qa4 = st.columns(4)
with qa1: st.page_link("pages/03_Screening_Center.py", label=" Start screening")
with qa2: st.page_link("pages/04_Doctors_Booking.py", label=" Book appointment")
with qa3: st.page_link("pages/06_Reports.py", label=" Generate report")
with qa4: st.page_link("pages/07_AI_Assistant.py", label=" Ask assistant")

section("Recent appointment activity")
if appointments:
    st.dataframe(pd.DataFrame(appointments).head(8), use_container_width=True, hide_index=True)
else:
    st.info("Your appointment activity will appear here.")
