from __future__ import annotations

import html
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT_DIR = Path(__file__).resolve().parents[2]
CSS_PATH = ROOT_DIR / "frontend" / "assets" / "styles.css"


def _safe(value) -> str:
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _svg(name: str = "eye") -> str:
    icons = {
        "eye": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z'/><circle cx='12' cy='12' r='3'/></svg>""",
        "spark": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 3l1.5 5L19 10l-5.5 2L12 17l-1.5-5L5 10l5.5-2L12 3Z'/><path d='M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8Z'/></svg>""",
        "calendar": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='4' width='18' height='17' rx='3'/><path d='M8 2v4M16 2v4M3 10h18'/></svg>""",
        "file": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M14 2H7a3 3 0 0 0-3 3v14a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V8Z'/><path d='M14 2v6h6M8 13h8M8 17h6'/></svg>""",
        "shield": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z'/><path d='M9 12l2 2 4-5'/></svg>""",
        "doctor": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 3v6a6 6 0 0 0 12 0V3'/><path d='M9 3H5M19 3h-4'/><path d='M12 15v2a4 4 0 0 0 8 0v-3'/><circle cx='20' cy='12' r='2'/></svg>""",
        "login": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4'/><path d='M10 17l5-5-5-5M15 12H3'/></svg>""",
        "home": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M3 11.5 12 4l9 7.5'/><path d='M5 10.5V21h14V10.5'/><path d='M9 21v-6h6v6'/></svg>""",
        "chat": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M21 12a8 8 0 0 1-8 8H6l-3 3v-6.5A8 8 0 1 1 21 12Z'/><path d='M8 11h8M8 15h5'/></svg>""",
        "grid": """<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='7' height='7' rx='2'/><rect x='14' y='3' width='7' height='7' rx='2'/><rect x='3' y='14' width='7' height='7' rx='2'/><rect x='14' y='14' width='7' height='7' rx='2'/></svg>""",
    }
    return icons.get(name, icons["eye"])


def _icon_from_input(icon: str | None) -> str:
    mapping = {
        "🧠": "spark", "📅": "calendar", "📄": "file", "🔐": "login", "⚕️": "doctor", "🧬": "spark", "🖼️": "eye", "🛡️": "shield", "✅": "shield", "💬": "chat", "🏥": "grid", "👨‍⚕️": "doctor", "🕒": "calendar", "🩺": "doctor", "👁️": "eye",
        "spark": "spark", "calendar": "calendar", "file": "file", "login": "login", "doctor": "doctor", "shield": "shield", "chat": "chat", "grid": "grid", "home": "home", "eye": "eye",
    }
    return _svg(mapping.get(str(icon), "spark"))


def setup_page(title: str, icon: str = "eye"):
    st.set_page_config(page_title=title, page_icon=None, layout="wide", initial_sidebar_state="expanded")
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    components.html(
        """<script>
        try {
          window.parent.scrollTo(0, 0);
          const doc = window.parent.document;
          [doc.scrollingElement, doc.documentElement, doc.body].forEach(function(el){ if(el){ el.scrollTop = 0; } });
        } catch(e) {}
        </script>""",
        height=0,
        width=0,
    )
    render_sidebar()


def render_sidebar():
    from frontend.app_utils.auth import load_me, logout

    me = load_me()
    user = me.get("user") if me else None
    role = user.get("role") if user else "guest"
    full_name = user.get("full_name") if user else "Guest"

    nav = {
        "guest": [("Home", "Home.py"), ("Login / Register", "pages/01_Login_Register.py")],
        "patient": [
            ("Patient Dashboard", "pages/02_Patient_Dashboard.py"),
            ("Screening Center", "pages/03_Screening_Center.py"),
            ("Doctors & Booking", "pages/04_Doctors_Booking.py"),
            ("My Appointments", "pages/05_My_Appointments.py"),
            ("Reports", "pages/06_Reports.py"),
            ("AI Assistant", "pages/07_AI_Assistant.py"),
        ],
        "doctor": [
            ("Doctor Dashboard", "pages/08_Doctor_Dashboard.py"),
            ("Doctor Schedule", "pages/09_Doctor_Schedule.py"),
            ("Doctor Appointments", "pages/10_Doctor_Appointments.py"),
            ("AI Assistant", "pages/07_AI_Assistant.py"),
        ],
        "admin": [("Admin Panel", "pages/11_Admin_Panel.py"), ("AI Assistant", "pages/07_AI_Assistant.py")],
    }

    with st.sidebar:
        st.markdown(
            f"""
            <div class='brand-box'>
              <div class='brand-logo'>{_svg('eye')}</div>
              <div>
                <div class='brand-title'>OptiCare</div>
                <div class='brand-subtitle'>Glaucoma screening platform</div>
              </div>
            </div>
            <div class='role-pill'>{_safe(role.title())}</div>
            <div class='current-user'>{_safe(full_name)}</div>
            <div class='sidebar-section-label'>Navigation</div>
            """,
            unsafe_allow_html=True,
        )
        for label, target in nav.get(role, nav["guest"]):
            st.page_link(target, label=label)

        st.markdown("<div class='sidebar-section-label account-label'>Account</div>", unsafe_allow_html=True)
        if user:
            if st.button("Sign out", key=f"global_sidebar_sign_out_{role}", use_container_width=True):
                logout()
                try:
                    st.switch_page("Home.py")
                except Exception:
                    st.rerun()
        else:
            st.markdown("<div class='sidebar-login-note'>Sign in to access your secure portal.</div>", unsafe_allow_html=True)

def hero(title: str, subtitle: str, kicker: str = "OptiCare Clinical Platform"):
    st.markdown(
        f"""
        <section class="app-hero">
          <div class="app-kicker">{_safe(kicker)}</div>
          <h1>{_safe(title)}</h1>
          <p>{_safe(subtitle)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str | None = None):
    st.markdown(
        f"""
        <div class="section-title">
          <div>
            <h2>{_safe(title)}</h2>
            {f'<p>{_safe(subtitle)}</p>' if subtitle else ''}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(icon: str, title: str, body: str):
    st.markdown(
        f"""
        <div class="feature-card equal-card">
          <div class="feature-icon">{_icon_from_input(icon)}</div>
          <h3>{_safe(title)}</h3>
          <p>{_safe(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, body: str, icon: str = "spark"):
    feature_card(icon, title, body)


def stat_card(label: str, value, note: str | None = None):
    st.markdown(
        f"""
        <div class="stat-card aligned-stat-card">
          <div class="stat-label">{_safe(label)}</div>
          <div class="stat-value">{_safe(value)}</div>
          {f'<div class="stat-note">{_safe(note)}</div>' if note else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_strip(title: str, body: str, icon: str = "spark"):
    st.markdown(
        f"""
        <div class="info-strip">
          <div class="info-icon">{_icon_from_input(icon)}</div>
          <div><strong>{_safe(title)}</strong><br>{_safe(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _badge_html(text: str | None, cls: str) -> str:
    return f"<span class='badge {cls}'>{_safe(text or '—')}</span>"


def badge_markup(text: str | None, kind: str = "info") -> str:
    cls = {"success": "badge-success", "warning": "badge-warning", "danger": "badge-danger", "info": "badge-info", "muted": "badge-muted"}.get(kind, "badge-info")
    return _badge_html(text, cls)


def risk_badge(level: str | None):
    text = level or "—"
    t = text.lower()
    cls = "badge-success"
    if "high" in t or "urgent" in t:
        cls = "badge-danger"
    elif "uncertain" in t or "recommended" in t or "routine" in t or "model" in t:
        cls = "badge-warning"
    st.markdown(_badge_html(text, cls), unsafe_allow_html=True)


def status_badge(status: str | None):
    text = status or "—"
    t = text.lower()
    cls = "badge-info"
    if t in {"approved", "confirmed", "completed", "active"}:
        cls = "badge-success"
    elif t in {"pending"}:
        cls = "badge-warning"
    elif t in {"rejected", "suspended", "cancelled", "inactive"}:
        cls = "badge-danger"
    st.markdown(_badge_html(text, cls), unsafe_allow_html=True)


def doctor_card(doctor: dict):
    st.markdown(
        f"""
        <div class="doctor-card">
          <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start;">
            <div>
              <div class="badge badge-info">Approved ophthalmologist</div>
              <h3 style="font-size:28px;margin:14px 0 8px;">{_safe(doctor.get('full_name'))}</h3>
              <p style="margin:0 0 10px;color:#475569;line-height:1.65;">{_safe(doctor.get('bio') or 'Ophthalmology care provider.')}</p>
            </div>
            <div style="text-align:right;min-width:190px;">
              <div class="badge badge-muted">{_safe(doctor.get('specialization'))}</div>
              <p style="margin-top:12px;color:#64748b;">{_safe(doctor.get('clinic_location'))}</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def appointment_card(title: str, date_text: str, time_text: str, status: str | None, body: str | None = None):
    status_kind = "success" if (status or "").lower() in {"confirmed", "completed"} else "warning"
    if (status or "").lower() in {"cancelled", "rejected"}:
        status_kind = "danger"
    st.markdown(
        f"""
        <div class="appointment-card">
          <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start;">
            <div>
              <h3 style="margin:0 0 8px;">{_safe(title)}</h3>
              <p style="margin:0;color:#475569;line-height:1.6;">{_safe(body or '')}</p>
            </div>
            {badge_markup(status, status_kind)}
          </div>
          <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:16px;">
            <div class="badge badge-info">Date: {_safe(date_text)}</div>
            <div class="badge badge-muted">Time: {_safe(time_text)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def report_summary_card(title: str, summary: str, created_at: str, risk: str | None = None):
    risk_html = ""
    if risk:
        kind = "danger" if "urgent" in risk.lower() or "high" in risk.lower() else "warning"
        risk_html = badge_markup(risk, kind)
    st.markdown(
        f"""
        <div class="report-card">
          <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;">
            <div>
              <div class="preview-label">Clinical Report</div>
              <h3 style="font-size:28px;margin:14px 0 8px;">{_safe(title)}</h3>
              <p>{_safe(summary)}</p>
              <p style="color:#94a3b8;font-size:13px;margin-top:12px;">Generated: {_safe(created_at)}</p>
            </div>
            <div>{risk_html}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
