from pathlib import Path
import json
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
from frontend.app_utils.ui import (
    feature_card,
    hero,
    info_strip,
    risk_badge,
    section,
    setup_page,
    stat_card,
)

setup_page("Screening Center", "")
me = require_role("patient")
profile = me.get("profile") or {}

hero(
    "Screening center",
    "Review fundus-image screening and complete a structured eye-health assessment.",
    "Clinical screening",
)

tab1, tab2 = st.tabs(
    ["Fundus image screening", "Eye health assessment"]
)

with tab1:
    info_strip(
        "Fundus screening",
        "Upload a clear fundus image to receive a preliminary glaucoma-risk "
        "assessment. The result supports screening and does not replace an "
        "ophthalmology examination.",
        "eye",
    )

    left, right = st.columns([1, 1])

    with left:
        uploaded = st.file_uploader(
            "Upload fundus image",
            type=["jpg", "jpeg", "png", "bmp", "webp"],
        )
        notes = st.text_area(
            "Optional notes",
            placeholder=(
                "Example: left eye image, blurred vision, "
                "previous high eye pressure..."
            ),
        )
        analyze = st.button(
            "Analyze image",
            key="fundus_analyze_image",
            use_container_width=True,
            disabled=uploaded is None,
        )

    with right:
        if uploaded:
            st.image(
                uploaded,
                caption="Uploaded fundus image",
                use_container_width=True,
            )
        else:
            feature_card(
                "eye",
                "Image preview",
                "Upload a clear fundus image to preview it before analysis.",
            )

    if analyze:
        try:
            files = {
                "file": (
                    uploaded.name,
                    uploaded.getvalue(),
                    uploaded.type or "application/octet-stream",
                )
            }
            result = api_post(
                "/screening/analyze",
                files=files,
                data={"notes": notes},
            )

            st.success("Analysis completed.")

            rc1, rc2, rc3 = st.columns(3)

            with rc1:
                st.markdown("#### Risk level")
                risk_badge(result.get("risk_level"))

            with rc2:
                stat_card(
                    "Glaucoma risk",
                    "—"
                    if result.get("probability") is None
                    else f"{float(result['probability']) * 100:.1f}%",
                )

            with rc3:
                status = (
                    "Completed"
                    if result.get("model_status") == "configured"
                    else "Unavailable"
                )
                stat_card("Analysis status", status)

            st.markdown("#### Recommendation")
            st.write(result.get("recommendation"))

        except Exception as exc:
            st.error(str(exc))

    section("Previous screening results")
    previous = api_get("/screening/mine")[:5]

    if previous:
        for result in previous:
            with st.container(border=True):
                cols = st.columns([2, 1, 3])
                cols[0].write(f"**{result['created_at']}**")
                with cols[1]:
                    risk_badge(result.get("risk_level"))
                cols[2].write(result.get("recommendation"))
    else:
        st.info("No previous fundus screening results yet.")

with tab2:
    info_strip(
        "Eye-health assessment",
        "Rate each symptom from 0 (none) to 10 (severe), then add relevant "
        "risk factors. The assessment is preliminary and is not a medical diagnosis.",
        "shield",
    )

    default_age = profile.get("age")
    try:
        default_age = int(default_age)
    except (TypeError, ValueError):
        default_age = 30
    default_age = max(0, min(100, default_age))

    with st.form("eye_health_assessment"):
        age = st.slider("Age", 0, 100, default_age)

        st.markdown("### Symptoms")
        left, right = st.columns(2)

        with left:
            pain = st.slider("Eye pain", 0, 10, 0)
            redness = st.slider("Eye redness", 0, 10, 0)
            vision_blur = st.slider("Blurred vision", 0, 10, 0)
            dryness = st.slider("Eye dryness", 0, 10, 0)
            itching = st.slider("Eye itching", 0, 10, 0)
            tearing = st.slider("Excessive tearing", 0, 10, 0)
            discharge = st.slider("Eye discharge", 0, 10, 0)
            photophobia = st.slider("Light sensitivity", 0, 10, 0)
            eye_fatigue = st.slider("Eye fatigue", 0, 10, 0)

        with right:
            halos = st.slider("Halos around lights", 0, 10, 0)
            headache = st.slider("Headache", 0, 10, 0)
            nausea = st.slider("Nausea", 0, 10, 0)
            floaters = st.slider("Floaters", 0, 10, 0)
            vision_loss = st.slider("Vision loss", 0, 10, 0)
            peripheral_loss = st.slider(
                "Peripheral vision loss",
                0,
                10,
                0,
            )
            burning = st.slider("Eye burning", 0, 10, 0)
            foreign_body = st.slider(
                "Foreign-body sensation",
                0,
                10,
                0,
            )
            screen_time = st.slider(
                "Daily screen time (hours)",
                0,
                12,
                4,
            )

        st.markdown("### Risk factors")
        r1, r2 = st.columns(2)

        with r1:
            contact_lens = st.checkbox("Contact lens use")
            diabetes = st.checkbox("Diabetes")
            hypertension = st.checkbox("Hypertension")
            family_glaucoma = st.checkbox(
                "Family history of glaucoma"
            )

        with r2:
            previous_surgery = st.checkbox(
                "Previous eye surgery"
            )
            eye_trauma = st.checkbox(
                "Previous eye trauma"
            )
            smoking = st.checkbox("Smoking")

        submitted = st.form_submit_button(
            "Complete assessment",
            use_container_width=True,
        )

    if submitted:
        answers = {
            "age": age,
            "pain": pain,
            "redness": redness,
            "vision_blur": vision_blur,
            "dryness": dryness,
            "itching": itching,
            "tearing": tearing,
            "discharge": discharge,
            "photophobia": photophobia,
            "halos": halos,
            "headache": headache,
            "nausea": nausea,
            "floaters": floaters,
            "vision_loss": vision_loss,
            "peripheral_loss": peripheral_loss,
            "burning": burning,
            "foreign_body": foreign_body,
            "eye_fatigue": eye_fatigue,
            "screen_time": screen_time,
            "contact_lens": int(contact_lens),
            "diabetes": int(diabetes),
            "hypertension": int(hypertension),
            "family_glaucoma": int(family_glaucoma),
            "previous_surgery": int(previous_surgery),
            "eye_trauma": int(eye_trauma),
            "smoking": int(smoking),
        }

        try:
            result = api_post(
                "/symptoms/assess",
                {"answers": answers},
            )

            st.success("Assessment completed.")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("#### Overall assessment")
                risk_badge(result.get("risk_level"))

            with c2:
                stat_card(
                    "Assessment score",
                    f"{float(result.get('score') or 0):.1f}%",
                )

            with c3:
                stat_card(
                    "Leading pattern",
                    result.get("primary_finding") or "—",
                )

            if result.get("confidence") is not None:
                stat_card(
                    "Leading pattern score",
                    f"{float(result['confidence']):.1f}%",
                    "Rule-based symptom-pattern score",
                )

            details = {}
            raw_details = result.get("details_json")
            if raw_details:
                try:
                    details = json.loads(raw_details)
                except Exception:
                    details = {}

            scores = details.get("assessment_scores") or {}
            if scores:
                st.markdown("#### Strongest assessment indicators")
                for name, value in list(scores.items())[:3]:
                    st.write(f"**{name}:** {float(value):.1f}%")

            st.markdown("#### Recommendation")
            st.write(result.get("recommendation"))

            st.page_link(
                "pages/04_Doctors_Booking.py",
                label="Book ophthalmology appointment",
            )

        except Exception as exc:
            st.error(str(exc))

    section("Previous eye-health assessments")
    assessments = api_get("/symptoms/mine")[:5]

    if assessments:
        for item in assessments:
            with st.container(border=True):
                cols = st.columns([2, 1, 2, 3])
                cols[0].write(f"**{item['created_at']}**")
                with cols[1]:
                    risk_badge(item.get("risk_level"))
                cols[2].write(
                    item.get("primary_finding") or "—"
                )
                cols[3].write(item.get("recommendation"))
    else:
        st.info("No previous eye-health assessments yet.")
