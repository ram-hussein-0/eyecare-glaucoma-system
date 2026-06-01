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
from frontend.app_utils.api import api_get, api_patch
from frontend.app_utils.ui import appointment_card, hero, section, setup_page

setup_page("My Appointments", "")
require_role("patient")
hero("My appointments", "Review upcoming and previous ophthalmology visits, and cancel confirmed appointments when needed.", "Patient scheduling")

appointments = api_get("/appointments/mine")
if not appointments:
    st.info("You have no appointments yet.")
    st.page_link("pages/04_Doctors_Booking.py", label="Book an appointment")
    st.stop()

section("Appointment timeline")
for a in appointments:
    appointment_card(
        a['doctor_name'],
        a['appointment_date'],
        f"{a['start_time']} - {a['end_time']}",
        a['status'],
        f"{a.get('clinic_location') or ''} · Reason: {a.get('reason') or '—'}",
    )
    if a["status"] == "confirmed":
        if st.button("Cancel this appointment", key=f"cancel_{a['id']}"):
            try:
                api_patch(f"/appointments/{a['id']}/cancel")
                st.success("Appointment cancelled.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with st.expander("Detailed table"):
    st.dataframe(pd.DataFrame(appointments), use_container_width=True, hide_index=True)
