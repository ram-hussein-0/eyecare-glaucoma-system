# Ensure project root is importable when Streamlit executes pages directly.
from pathlib import Path
import sys

_PROJECT_ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "backend").exists() and (p / "frontend").exists()
)
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from datetime import time

import pandas as pd
import streamlit as st

from frontend.app_utils.auth import require_role
from frontend.app_utils.api import api_delete, api_get, api_post
from frontend.app_utils.ui import hero, section, setup_page

setup_page("Doctor Schedule", "")
me = require_role("doctor")
profile = me.get("profile") or {}
hero("Schedule and availability", "Define your weekly availability. Patients can only book slots generated from these rules.", "Doctor scheduling")

if profile.get("status") != "approved":
    st.warning("Availability becomes public after admin approval.")

weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
section("Add availability rule")
with st.form("availability"):
    weekday_label = st.selectbox("Weekday", weekdays)
    c1, c2, c3 = st.columns(3)
    start_time = c1.time_input("Start time", value=time(9, 0))
    end_time = c2.time_input("End time", value=time(13, 0))
    slot_minutes = c3.number_input("Slot duration", min_value=10, max_value=180, value=30)
    submitted = st.form_submit_button("Add availability", use_container_width=True)
if submitted:
    try:
        api_post("/doctors/me/availability", {
            "weekday": weekdays.index(weekday_label),
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "slot_minutes": int(slot_minutes),
        })
        st.success("Availability added.")
        st.rerun()
    except Exception as exc:
        st.error(str(exc))

availability = api_get("/doctors/me/availability")
section("Current availability")
if availability:
    df = pd.DataFrame(availability)
    df["weekday_name"] = df["weekday"].apply(lambda x: weekdays[int(x)])
    st.dataframe(df[["id", "weekday_name", "start_time", "end_time", "slot_minutes"]], use_container_width=True, hide_index=True)
    to_delete = st.selectbox("Remove availability rule", [f"#{a['id']} · {weekdays[a['weekday']]} {a['start_time']} - {a['end_time']}" for a in availability])
    if st.button("Remove selected rule", key="auto_frontend_pages_09_doctor_schedule_py_58_remove_selected_rule"):
        av_id = int(to_delete.split(" · ")[0].replace("#", ""))
        try:
            api_delete(f"/doctors/me/availability/{av_id}")
            st.success("Availability removed.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
else:
    st.info("No availability rules yet.")
