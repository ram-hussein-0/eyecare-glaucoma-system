from __future__ import annotations

import html
from pathlib import Path
from textwrap import shorten

from backend.core.config import get_settings
from backend.db.database import fetch_one


def _safe(value) -> str:
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _badge_class(level: str | None) -> str:
    text = (level or "").lower()
    if "high" in text or "urgent" in text:
        return "danger"
    if "uncertain" in text or "recommended" in text or "routine" in text or "model" in text:
        return "warning"
    return "success"


def _risk_label(screening: dict | None, symptom: dict | None) -> str:
    for item in (screening, symptom):
        if item and item.get("risk_level"):
            return str(item["risk_level"])
    return "Preliminary Review"


def build_report(patient_id: int, title: str, screening_result_id: int | None, symptom_assessment_id: int | None, appointment_id: int | None) -> dict:
    patient = fetch_one("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if not patient:
        raise ValueError("Patient was not found.")
    screening = fetch_one("SELECT * FROM screening_results WHERE id = ? AND patient_id = ?", (screening_result_id, patient_id)) if screening_result_id else None
    symptom = fetch_one("SELECT * FROM symptom_assessments WHERE id = ? AND patient_id = ?", (symptom_assessment_id, patient_id)) if symptom_assessment_id else None
    appointment = None
    if appointment_id:
        appointment = fetch_one(
            """
            SELECT a.*, d.full_name AS doctor_name, d.clinic_location, d.specialization
            FROM appointments a JOIN doctors d ON d.id = a.doctor_id
            WHERE a.id = ? AND a.patient_id = ?
            """,
            (appointment_id, patient_id),
        )

    summary_parts = []
    if screening:
        summary_parts.append(f"Fundus screening result: {screening['risk_level']}.")
    if symptom:
        summary_parts.append(f"Eye health assessment: {symptom['risk_level']}.")
    if appointment:
        summary_parts.append(f"Linked appointment: {appointment['appointment_date']} at {appointment['start_time']} with {appointment['doctor_name']}.")
    summary = " ".join(summary_parts) or "Patient report generated with available profile information."

    html_content = render_html_report(title, patient, screening, symptom, appointment, summary)
    settings = get_settings()
    report_id_fragment = f"patient_{patient_id}_{abs(hash((title, summary))) % 10_000_000}"
    html_path = settings.reports_path / f"{report_id_fragment}.html"
    pdf_path = settings.reports_path / f"{report_id_fragment}.pdf"
    html_path.write_text(html_content, encoding="utf-8")
    try:
        render_pdf_report(pdf_path, title, patient, screening, symptom, appointment, summary)
        pdf_str = str(pdf_path)
    except Exception:
        pdf_str = None
    return {"summary": summary, "html_path": str(html_path), "pdf_path": pdf_str}


def render_html_report(title: str, patient: dict, screening: dict | None, symptom: dict | None, appointment: dict | None, summary: str) -> str:
    screening_level = screening.get("risk_level") if screening else None
    symptom_level = symptom.get("risk_level") if symptom else None
    screening_badge = _badge_class(screening_level)
    symptom_badge = _badge_class(symptom_level)
    probability = "—"
    if screening and screening.get("probability") is not None:
        probability = f"{float(screening['probability']) * 100:.1f}%"
    confidence = "—"
    if screening and screening.get("confidence") is not None:
        confidence = f"{float(screening['confidence']) * 100:.1f}%"
    risk = _risk_label(screening, symptom)
    risk_badge = _badge_class(risk)
    appt_time = "—"
    if appointment:
        appt_time = f"{appointment.get('start_time') or '—'} - {appointment.get('end_time') or '—'}"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_safe(title)}</title>
  <style>
    :root {{ --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --blue:#2563eb; --teal:#0f766e; --cyan:#06b6d4; --bg:#f6f9fc; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; background: radial-gradient(circle at top left, rgba(37,99,235,.10), transparent 32%), var(--bg); color:var(--ink); }}
    .page {{ max-width: 1020px; margin: 34px auto; background: #fff; border-radius: 34px; overflow: hidden; box-shadow: 0 30px 90px rgba(15, 23, 42, .13); border:1px solid rgba(226,232,240,.9); }}
    .hero {{ position:relative; overflow:hidden; padding: 42px 48px; background: linear-gradient(135deg, #0f766e 0%, #0ea5e9 44%, #2563eb 100%); color:#fff; }}
    .hero:after {{ content:""; position:absolute; width:300px; height:300px; border-radius:999px; background:rgba(255,255,255,.14); right:-90px; top:-120px; }}
    .kicker {{ display:inline-block; padding:8px 12px; border-radius:999px; background:rgba(255,255,255,.16); font-size:12px; letter-spacing:.12em; text-transform:uppercase; font-weight:800; margin-bottom:16px; }}
    .hero h1 {{ margin:0; font-size:40px; letter-spacing:-.04em; line-height:1.05; }}
    .hero p {{ margin:12px 0 0; max-width:760px; font-size:16px; line-height:1.7; opacity:.94; }}
    .content {{ padding: 36px 48px 44px; }}
    .topline {{ display:flex; gap:16px; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; margin-bottom:22px; }}
    .summary {{ flex:1; min-width:280px; padding:20px 22px; border-radius:22px; background:linear-gradient(135deg,#eff6ff,#ecfeff); border:1px solid #bfdbfe; line-height:1.7; color:#1e3a8a; }}
    .badge {{ display:inline-flex; align-items:center; justify-content:center; border-radius:999px; padding:9px 14px; font-weight:850; font-size:13px; border:1px solid transparent; white-space:normal; max-width:100%; text-align:center; line-height:1.25; overflow-wrap:anywhere; }}
    .success {{ background:#dcfce7; color:#166534; border-color:#bbf7d0; }}
    .warning {{ background:#fef3c7; color:#92400e; border-color:#fde68a; }}
    .danger {{ background:#fee2e2; color:#991b1b; border-color:#fecaca; }}
    .meta-card {{ flex:0 1 290px; max-width:100%; padding:20px; border-radius:22px; background:#f8fafc; border:1px solid var(--line); }}
    .meta-label {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.08em; font-weight:800; }}
    .meta-value {{ font-size:20px; line-height:1.25; font-weight:850; margin-top:8px; }}
    .grid {{ display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:18px; }}
    .card {{ border:1px solid var(--line); border-radius:24px; padding:22px; background:linear-gradient(180deg,#ffffff 0%,#fbfdff 100%); box-shadow:0 14px 36px rgba(15,23,42,.055); min-height: 220px; }}
    .card h2 {{ margin:0 0 16px; font-size:20px; letter-spacing:-.02em; }}
    .row {{ display:flex; justify-content:space-between; gap:18px; border-bottom:1px solid #eef2f7; padding:10px 0; align-items:flex-start; }}
    .row:last-child {{ border-bottom:none; }}
    .label {{ min-width:120px; color:var(--muted); font-weight:650; }}
    .value {{ font-weight:750; text-align:right; overflow-wrap:anywhere; word-break:break-word; line-height:1.45; }}
    .note {{ margin-top:22px; padding:18px 20px; border-radius:20px; background:#f8fafc; color:#475569; line-height:1.7; border:1px solid var(--line); }}
    .footer {{ display:flex; justify-content:space-between; gap:18px; align-items:center; padding:20px 48px; background:#f8fafc; color:#64748b; font-size:13px; border-top:1px solid var(--line); }}
    @media (max-width: 760px) {{ .page {{ margin:0; border-radius:0; }} .hero,.content,.footer {{ padding-left:24px; padding-right:24px; }} .grid {{ grid-template-columns: 1fr; }} .meta-card {{ width:100%; }} .row {{ flex-direction:column; gap:4px; }} .value {{ text-align:left; }} }}
    @media print {{ body {{ background:#fff; }} .page {{ margin:0; box-shadow:none; border:none; }} }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="kicker">OptiCare Screening Report</div>
      <h1>{_safe(title)}</h1>
      <p>Preliminary glaucoma screening support, symptom-triage information, and ophthalmology appointment summary.</p>
    </section>
    <section class="content">
      <div class="topline">
        <div class="summary"><strong>Clinical summary:</strong> {_safe(summary)}</div>
        <div class="meta-card"><div class="meta-label">Overall status</div><div class="meta-value"><span class="badge {risk_badge}">{_safe(risk)}</span></div></div>
      </div>
      <div class="grid">
        <div class="card">
          <h2>Patient Information</h2>
          <div class="row"><span class="label">Name</span><span class="value">{_safe(patient.get('full_name'))}</span></div>
          <div class="row"><span class="label">Age</span><span class="value">{_safe(patient.get('age'))}</span></div>
          <div class="row"><span class="label">Gender</span><span class="value">{_safe(patient.get('gender'))}</span></div>
          <div class="row"><span class="label">Phone</span><span class="value">{_safe(patient.get('phone'))}</span></div>
          <div class="row"><span class="label">Medical notes</span><span class="value">{_safe(shorten(patient.get('medical_notes') or '—', width=110))}</span></div>
        </div>
        <div class="card">
          <h2>Fundus Screening</h2>
          <div class="row"><span class="label">Risk level</span><span class="value"><span class="badge {screening_badge}">{_safe(screening_level)}</span></span></div>
          <div class="row"><span class="label">Probability</span><span class="value">{probability}</span></div>
          <div class="row"><span class="label">Confidence</span><span class="value">{confidence}</span></div>
          <div class="row"><span class="label">Date</span><span class="value">{_safe(screening.get('created_at') if screening else None)}</span></div>
        </div>
        <div class="card">
          <h2>Eye Health Assessment</h2>
          <div class="row"><span class="label">Result</span><span class="value"><span class="badge {symptom_badge}">{_safe(symptom_level)}</span></span></div>
          <div class="row"><span class="label">Score</span><span class="value">{_safe(symptom.get('score') if symptom else None)}</span></div>
          <div class="row"><span class="label">Recommendation</span><span class="value">{_safe(symptom.get('recommendation') if symptom else None)}</span></div>
          <div class="row"><span class="label">Date</span><span class="value">{_safe(symptom.get('created_at') if symptom else None)}</span></div>
        </div>
        <div class="card">
          <h2>Appointment</h2>
          <div class="row"><span class="label">Doctor</span><span class="value">{_safe(appointment.get('doctor_name') if appointment else None)}</span></div>
          <div class="row"><span class="label">Specialization</span><span class="value">{_safe(appointment.get('specialization') if appointment else None)}</span></div>
          <div class="row"><span class="label">Date</span><span class="value">{_safe(appointment.get('appointment_date') if appointment else None)}</span></div>
          <div class="row"><span class="label">Time</span><span class="value">{_safe(appt_time)}</span></div>
          <div class="row"><span class="label">Location</span><span class="value">{_safe(appointment.get('clinic_location') if appointment else None)}</span></div>
        </div>
      </div>
      <div class="note"><strong>Important note:</strong> This report provides preliminary screening support and appointment-related information. It does not replace clinical examination, medical diagnosis, or professional judgment by an ophthalmologist.</div>
    </section>
    <footer class="footer"><span>OptiCare Glaucoma Screening</span><span>Generated report</span></footer>
  </main>
</body>
</html>"""


def render_pdf_report(pdf_path: Path, title: str, patient: dict, screening: dict | None, symptom: dict | None, appointment: dict | None, summary: str) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ModernTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=colors.white, alignment=TA_LEFT, spaceAfter=6)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15, textColor=colors.HexColor("#dbeafe"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#0f172a"), spaceAfter=8)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#0f172a"))
    label = ParagraphStyle("Label", parent=body, fontName="Helvetica-Bold", textColor=colors.HexColor("#475569"))
    value = ParagraphStyle("Value", parent=body, alignment=TA_RIGHT)
    note_style = ParagraphStyle("Note", parent=body, fontName="Helvetica-Oblique", textColor=colors.HexColor("#475569"), leading=14)

    story = []
    header = Table(
        [[Paragraph(html.escape(title), title_style)], [Paragraph("Preliminary glaucoma screening support and ophthalmology appointment summary.", subtitle_style)]],
        colWidths=[174 * mm],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2563eb")),
        ("BOX", (0, 0), (-1, -1), 0, colors.HexColor("#2563eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, 0), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(header)
    story.append(Spacer(1, 12))

    summary_table = Table([[Paragraph("Clinical summary", label), Paragraph(html.escape(summary), body)]], colWidths=[44 * mm, 130 * mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#bfdbfe")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    def _p(v, style=value):
        return Paragraph(html.escape(str(v if v is not None and v != "" else "—")), style)

    def block(heading: str, rows: list[tuple[str, object]]):
        story.append(Paragraph(heading, h2))
        table = Table([[_p(k, label), _p(v)] for k, v in rows], colWidths=[48 * mm, 126 * mm], repeatRows=0)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("BACKGROUND", (1, 0), (1, -1), colors.white),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#dbe3ee")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(table)
        story.append(Spacer(1, 11))

    block("Patient Information", [
        ("Name", patient.get("full_name")),
        ("Age", patient.get("age")),
        ("Gender", patient.get("gender")),
        ("Phone", patient.get("phone")),
        ("Medical notes", shorten(patient.get("medical_notes") or "—", width=140)),
    ])
    if screening:
        prob = "—" if screening.get("probability") is None else f"{float(screening['probability'])*100:.1f}%"
        conf = "—" if screening.get("confidence") is None else f"{float(screening['confidence'])*100:.1f}%"
        block("Fundus Screening", [
            ("Risk level", screening.get("risk_level") or "—"),
            ("Probability", prob),
            ("Confidence", conf),
            ("Recommendation", screening.get("recommendation") or "—"),
            ("Date", screening.get("created_at") or "—"),
        ])
    if symptom:
        block("Eye Health Assessment", [
            ("Risk level", symptom.get("risk_level") or "—"),
            ("Score", symptom.get("score") or "—"),
            ("Recommendation", symptom.get("recommendation") or "—"),
            ("Date", symptom.get("created_at") or "—"),
        ])
    if appointment:
        block("Appointment", [
            ("Doctor", appointment.get("doctor_name") or "—"),
            ("Specialization", appointment.get("specialization") or "—"),
            ("Date", appointment.get("appointment_date") or "—"),
            ("Time", f"{appointment.get('start_time')} - {appointment.get('end_time')}"),
            ("Location", appointment.get("clinic_location") or "—"),
        ])
    story.append(Spacer(1, 4))
    story.append(Paragraph("This report provides preliminary screening support and does not replace clinical examination by an ophthalmologist.", note_style))
    doc.build(story)
