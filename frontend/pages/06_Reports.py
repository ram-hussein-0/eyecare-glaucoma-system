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
import streamlit.components.v1 as components

from frontend.app_utils.auth import require_role
from frontend.app_utils.api import api_delete, api_download, api_get, api_post
from frontend.app_utils.ui import hero, info_strip, report_summary_card, section, setup_page

setup_page("Reports", "file")
require_role("patient")
hero("Patient reports", "Create a polished clinical-style summary, preview it inside the platform, and export it as HTML or PDF.", "Report center")

screenings = api_get("/screening/mine")
symptoms = api_get("/symptoms/mine")
appointments = api_get("/appointments/mine")
reports = api_get("/reports/mine")

info_strip("Two-stage report workflow", "First generate a structured report, then preview it inside the website before downloading HTML or PDF.", "file")


def _options(items: list[dict], labeler):
    result = {"None": None}
    for index, item in enumerate(items, start=1):
        result[labeler(index, item)] = item["id"]
    return result


screening_options = _options(screenings, lambda i, r: f"Screening {i} · {r.get('created_at', '—')} · {r.get('risk_level', '—')}")
symptom_options = _options(symptoms, lambda i, r: f"Eye health assessment {i} · {r.get('created_at', '—')} · {r.get('risk_level', '—')}")
appointment_options = _options(appointments, lambda i, a: f"Appointment {i} · {a.get('appointment_date', '—')} · {a.get('doctor_name', '—')}")

with st.expander("Create new report", expanded=True):
    title = st.text_input("Report title", value="Eye Screening Report")
    c1, c2, c3 = st.columns(3)
    s_label = c1.selectbox("Screening result", list(screening_options.keys()))
    sy_label = c2.selectbox("Eye health assessment", list(symptom_options.keys()))
    a_label = c3.selectbox("Linked appointment", list(appointment_options.keys()))
    if st.button("Generate report", key="generate_patient_report", use_container_width=True):
        try:
            report = api_post("/reports/create", {
                "title": title,
                "screening_result_id": screening_options[s_label],
                "symptom_assessment_id": symptom_options[sy_label],
                "appointment_id": appointment_options[a_label],
            })
            st.session_state["preview_report_id"] = report["id"]
            st.success("Report generated.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

section("Generated reports", "Preview, export, or delete reports generated from this account.")
if not reports:
    st.info("No reports yet.")
else:
    for index, r in enumerate(reports, start=1):
        report_summary_card(f"Report {index}: {r['title']}", r["summary"], r["created_at"])
        b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
        if b1.button("Preview", key=f"preview_{r['id']}", use_container_width=True):
            st.session_state["preview_report_id"] = r["id"]
        try:
            html_bytes = api_download(f"/reports/{r['id']}/download/html")
            b2.download_button("Download HTML", data=html_bytes, file_name=f"report_{index}.html", mime="text/html", key=f"html_{r['id']}", use_container_width=True)
        except Exception:
            b2.warning("HTML unavailable")
        if r.get("pdf_path"):
            try:
                pdf_bytes = api_download(f"/reports/{r['id']}/download/pdf")
                b3.download_button("Download PDF", data=pdf_bytes, file_name=f"report_{index}.pdf", mime="application/pdf", key=f"pdf_{r['id']}", use_container_width=True)
            except Exception:
                b3.warning("PDF unavailable")
        if b4.button("Delete", key=f"delete_report_{r['id']}", use_container_width=True):
            try:
                api_delete(f"/reports/{r['id']}")
                if st.session_state.get("preview_report_id") == r["id"]:
                    st.session_state.pop("preview_report_id", None)
                st.success("Report deleted.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

preview_id = st.session_state.get("preview_report_id")
if preview_id:
    section("Report preview", "This is the same designed HTML report that can be exported or sent.")
    try:
        html_bytes = api_download(f"/reports/{preview_id}/download/html")
        html_text = html_bytes.decode("utf-8", errors="replace")
        st.markdown('<div class="report-preview-shell">', unsafe_allow_html=True)
        components.html(html_text, height=900, scrolling=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Preview unavailable: {exc}")
