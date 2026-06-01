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

from frontend.app_utils.auth import require_role
from frontend.app_utils.api import api_get, api_post
from frontend.app_utils.ui import feature_card, hero, info_strip, risk_badge, section, setup_page, stat_card

setup_page("Screening Center", "")
require_role("patient")
hero("Screening center", "Complete the fundus-image glaucoma screening workflow and a symptom-based eye triage assessment.", "Clinical screening")

tab1, tab2 = st.tabs(["Fundus image screening", "Eye symptom triage"])

with tab1:
    info_strip("Model integration ready", "The backend exposes a stable model-service adapter. When your trained Vision Transformer or another model is ready, connect it without changing this interface.", "")
    left, right = st.columns([1, 1])
    with left:
        uploaded = st.file_uploader("Upload fundus image", type=["jpg", "jpeg", "png", "bmp", "webp"])
        notes = st.text_area("Optional notes", placeholder="Example: left eye image, blurry vision, previous high eye pressure...")
        analyze = st.button("Analyze image", key="auto_frontend_pages_03_screening_center_py_30_analyze_image", use_container_width=True, disabled=uploaded is None)
    with right:
        if uploaded:
            st.image(uploaded, caption="Uploaded fundus image", use_container_width=True)
        else:
            feature_card("", "Image preview", "Upload a clear fundus image to preview it here before analysis.")

    if analyze:
        try:
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
            data = {"notes": notes}
            result = api_post("/screening/analyze", files=files, data=data)
            st.success("Image submitted successfully.")
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                st.markdown("#### Risk level")
                risk_badge(result.get("risk_level"))
            with rc2:
                stat_card("Probability", "—" if result.get("probability") is None else f"{float(result['probability'])*100:.1f}%")
            with rc3:
                stat_card("Model status", result.get("model_status") or "—")
            st.markdown("#### Recommendation")
            st.write(result.get("recommendation"))
        except Exception as exc:
            st.error(str(exc))

    section("Previous screening results")
    previous = api_get("/screening/mine")[:5]
    if previous:
        for r in previous:
            with st.container(border=True):
                cols = st.columns([2, 1, 3])
                cols[0].write(f"**{r['created_at']}**")
                with cols[1]:
                    risk_badge(r.get("risk_level"))
                cols[2].write(r.get("recommendation"))
    else:
        st.info("No previous image screening results yet.")

with tab2:
    info_strip("Triage purpose", "This questionnaire does not diagnose eye disease. It estimates whether an ophthalmology visit is recommended based on warning signs and risk factors.", "")
    with st.form("symptoms"):
        st.markdown("### Warning signs")
        c1, c2 = st.columns(2)
        sudden_vision_loss = c1.checkbox("Sudden vision loss")
        severe_eye_pain = c2.checkbox("Severe eye pain")
        nausea_with_eye_pain = c1.checkbox("Nausea or vomiting with eye pain")
        halos_with_pain = c2.checkbox("Halos around lights with pain")
        st.markdown("### Current symptoms")
        c3, c4 = st.columns(2)
        blurred_vision = c3.checkbox("Blurred vision")
        halos_around_lights = c4.checkbox("Halos around lights")
        eye_redness = c3.checkbox("Eye redness")
        headache = c4.checkbox("Headache")
        high_eye_pressure_history = c3.checkbox("Previous high eye pressure")
        st.markdown("### Risk factors")
        c5, c6 = st.columns(2)
        family_history_glaucoma = c5.checkbox("Family history of glaucoma")
        diabetes = c6.checkbox("Diabetes")
        hypertension = c5.checkbox("Hypertension")
        age_over_40 = c6.checkbox("Age over 40")
        uses_steroids = c5.checkbox("Long-term steroid use")
        submitted = st.form_submit_button("Assess symptoms", use_container_width=True)
    if submitted:
        answers = {k: v for k, v in locals().items() if k in {
            "sudden_vision_loss", "severe_eye_pain", "nausea_with_eye_pain", "halos_with_pain",
            "blurred_vision", "halos_around_lights", "eye_redness", "headache", "high_eye_pressure_history",
            "family_history_glaucoma", "diabetes", "hypertension", "age_over_40", "uses_steroids"
        }}
        try:
            result = api_post("/symptoms/assess", {"answers": answers})
            st.success("Assessment completed.")
            r1, r2 = st.columns([1, 2])
            with r1:
                st.markdown("#### Triage result")
                risk_badge(result.get("risk_level"))
                stat_card("Score", result.get("score"))
            with r2:
                st.markdown("#### Recommendation")
                st.write(result.get("recommendation"))
                st.page_link("pages/04_Doctors_Booking.py", label="Book ophthalmology appointment")
        except Exception as exc:
            st.error(str(exc))
