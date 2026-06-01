# Ensure project root is importable when Streamlit executes pages directly.
from pathlib import Path
import sys

_PROJECT_ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "backend").exists() and (p / "frontend").exists()
)
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from frontend.app_utils.auth import require_role
from frontend.app_utils.api import api_get, api_post
from frontend.app_utils.ui import doctor_card, hero, info_strip, section, setup_page, stat_card

setup_page("Doctors & Booking", "")
require_role("patient")
hero("Doctors and booking", "Choose an approved ophthalmologist, review availability, and confirm a visit from one clean booking workflow.", "Appointment scheduling")

doctors = api_get("/doctors/approved")
if not doctors:
    st.info("No approved doctors are available yet.")
    st.stop()

selected_label = st.selectbox("Select doctor", [f"{d['full_name']} — {d['specialization']}" for d in doctors])
doctor = doctors[[f"{d['full_name']} — {d['specialization']}" for d in doctors].index(selected_label)]
doctor_card(doctor)

section("Find available slots")
c1, c2 = st.columns(2)
date_from = c1.date_input("From", value=date.today())
date_to = c2.date_input("To", value=date.today() + timedelta(days=14))

try:
    slots = api_get(f"/doctors/{doctor['id']}/slots", date_from=date_from.isoformat(), date_to=date_to.isoformat())
except Exception as exc:
    st.error(str(exc))
    st.stop()

if not slots:
    st.info("No available slots in the selected date range.")
    st.stop()

def slot_label(s: dict) -> str:
    return f"{s['date']} ({s['weekday']}) · {s['start_time']}–{s['end_time']}"

labels = [slot_label(s) for s in slots]
selected_slot_label = st.selectbox("Choose an available slot", labels, index=0)
slot = slots[labels.index(selected_slot_label)]

m1, m2, m3 = st.columns(3)
with m1: stat_card("Selected date", slot["date"])
with m2: stat_card("Start", slot["start_time"])
with m3: stat_card("End", slot["end_time"])

reason = st.text_area("Reason for visit", placeholder="Example: glaucoma screening review, blurred vision, routine eye check...")
info_strip("Booking confirmation", "The selected slot will be reserved immediately after confirmation if it is still available.", "")
if st.button("Confirm appointment", key="auto_frontend_pages_04_doctors_booking_py_63_confirm_appointment", use_container_width=True):
    try:
        api_post("/appointments/book", {
            "doctor_id": slot["doctor_id"],
            "appointment_date": slot["date"],
            "start_time": slot["start_time"],
            "end_time": slot["end_time"],
            "reason": reason,
        })
        st.success("Appointment confirmed.")
        st.page_link("pages/05_My_Appointments.py", label="Open my appointments")
    except Exception as exc:
        st.error(str(exc))

with st.expander("View all available slots as a table"):
    st.dataframe(pd.DataFrame(slots), use_container_width=True, hide_index=True)
