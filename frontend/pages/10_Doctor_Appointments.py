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
from frontend.app_utils.ui import appointment_card, hero, section, setup_page, status_badge

setup_page("Doctor Appointments", "")
require_role("doctor")
hero("Doctor appointments", "Review patient appointments and mark visits as completed.", "Patient case review")

appointments = api_get("/appointments/doctor/mine")
if not appointments:
    st.info("No appointments yet.")
    st.stop()

section("Appointment list")
for a in appointments:
    appointment_card(
        a['patient_name'],
        a['appointment_date'],
        f"{a['start_time']} - {a['end_time']}",
        a['status'],
        f"Phone: {a.get('patient_phone') or '—'} · Age/Gender: {a.get('patient_age') or '—'} / {a.get('patient_gender') or '—'} · Reason: {a.get('reason') or '—'}",
    )
    if a["status"] == "confirmed":
        if st.button("Mark completed", key=f"complete_{a['id']}"):
            try:
                api_patch(f"/appointments/{a['id']}/complete")
                st.success("Appointment completed.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with st.expander("Table view"):
    st.dataframe(pd.DataFrame(appointments), use_container_width=True, hide_index=True)
