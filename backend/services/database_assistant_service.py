from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from backend.db.database import fetch_all, fetch_one


@dataclass
class DatabaseAssistantResult:
    intent: str
    used_database: bool
    answer: str
    rows: list[dict]
    policy_note: str


def _as_dicts(rows) -> list[dict]:
    return [dict(r) for r in rows]


def _contains_any(text: str, words: list[str]) -> bool:
    text = text.lower()
    return any(w.lower() in text for w in words)


def _profile_for_user(user: dict) -> dict | None:
    role = user.get("role")
    if role == "patient":
        row = fetch_one("SELECT * FROM patients WHERE user_id=?", (user["id"],))
        return dict(row) if row else None
    if role == "doctor":
        row = fetch_one("SELECT * FROM doctors WHERE user_id=?", (user["id"],))
        return dict(row) if row else None
    return None


def _format_rows_for_answer(rows: list[dict], max_rows: int = 6) -> str:
    if not rows:
        return "لا توجد نتائج مطابقة حاليًا."

    lines: list[str] = []
    for idx, row in enumerate(rows[:max_rows], start=1):
        compact = []
        for key, value in row.items():
            if value is None or key in {"user_id", "patient_id", "doctor_id"}:
                continue
            compact.append(f"{key}: {value}")
        lines.append(f"{idx}. " + " · ".join(compact))

    if len(rows) > max_rows:
        lines.append(f"... وهناك {len(rows) - max_rows} نتيجة إضافية.")

    return "\n".join(lines)


class DatabaseAssistantService:
    """Protected, rule-based database assistant.

    This service is intentionally NOT text-to-SQL.

    Security model:
    - No user-provided SQL.
    - No LLM-generated SQL.
    - Only fixed read-only SELECT queries.
    - Role-aware visibility:
        patient: only own appointments/reports/screening + public approved doctors.
        doctor: only own schedule/appointments + public approved doctors.
        admin: operational summaries, no passwords/session tokens.
    - No INSERT/UPDATE/DELETE.
    """

    def answer(self, question: str, user: dict) -> DatabaseAssistantResult:
        role = user.get("role")
        q = (question or "").strip().lower()

        if not q:
            return self._empty()

        if self._asks_available_slots(q):
            if role not in {"patient", "admin"}:
                return self._forbidden("available_slots", "يمكن للمرضى أو المدير فقط استعراض مواعيد الحجز العامة.")
            return self.available_slots()

        if self._asks_doctors(q):
            return self.approved_doctors()

        if role == "patient":
            return self._patient_answer(q, user)

        if role == "doctor":
            return self._doctor_answer(q, user)

        if role == "admin":
            return self._admin_answer(q)

        return self._empty()

    def _empty(self) -> DatabaseAssistantResult:
        return DatabaseAssistantResult(
            intent="no_database_intent",
            used_database=False,
            answer="",
            rows=[],
            policy_note="No database intent matched.",
        )

    def _forbidden(self, intent: str, message: str) -> DatabaseAssistantResult:
        return DatabaseAssistantResult(
            intent=intent,
            used_database=True,
            answer=message,
            rows=[],
            policy_note="Role-based access denied.",
        )

    def _asks_available_slots(self, q: str) -> bool:
        return _contains_any(q, [
            "available", "slot", "slots", "appointment available", "nearest appointment",
            "موعد", "مواعيد", "متاح", "متاحة", "اقرب موعد", "أقرب موعد", "حجز",
        ])

    def _asks_doctors(self, q: str) -> bool:
        return _contains_any(q, [
            "doctor", "doctors", "ophthalmologist", "clinic",
            "طبيب", "دكتور", "أطباء", "اطباء", "عيادة",
        ])

    def _patient_answer(self, q: str, user: dict) -> DatabaseAssistantResult:
        patient = _profile_for_user(user)
        if not patient:
            return self._forbidden("patient_profile_missing", "لا يوجد ملف مريض مرتبط بهذا الحساب.")

        if _contains_any(q, ["my appointment", "appointments", "حجوزاتي", "مواعيدي", "موعدي"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT a.id, d.full_name AS doctor_name, d.specialization, d.clinic_location,
                       a.appointment_date, a.start_time, a.end_time, a.status, a.reason
                FROM appointments a
                JOIN doctors d ON d.id = a.doctor_id
                WHERE a.patient_id=?
                ORDER BY a.appointment_date DESC, a.start_time DESC
                LIMIT 10
                """,
                (patient["id"],),
            ))
            return DatabaseAssistantResult(
                intent="patient_my_appointments",
                used_database=True,
                answer="هذه آخر المواعيد المسجلة على حسابك:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Patient can only see own appointments.",
            )

        if _contains_any(q, ["screening", "image result", "fundus", "model result", "فحص الصورة", "نتيجة الصورة", "نتيجة الموديل", "تصوير"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT id, risk_level, probability, confidence, recommendation, model_name, model_status, created_at
                FROM screening_results
                WHERE patient_id=?
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (patient["id"],),
            ))
            return DatabaseAssistantResult(
                intent="patient_screening_results",
                used_database=True,
                answer="هذه آخر نتائج فحص الصورة الخاصة بك:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Patient can only see own screening results.",
            )

        if _contains_any(q, ["symptom", "triage", "form", "أعراض", "اعراض", "استمارة", "النموذج", "الفورم"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT id, score, risk_level, recommendation, created_at
                FROM symptom_assessments
                WHERE patient_id=?
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (patient["id"],),
            ))
            return DatabaseAssistantResult(
                intent="patient_symptom_assessments",
                used_database=True,
                answer="هذه آخر تقييمات الأعراض الخاصة بك:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Patient can only see own symptom assessments.",
            )

        if _contains_any(q, ["report", "reports", "تقرير", "تقارير"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT id, title, summary, created_at
                FROM patient_reports
                WHERE patient_id=?
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (patient["id"],),
            ))
            return DatabaseAssistantResult(
                intent="patient_reports",
                used_database=True,
                answer="هذه آخر التقارير الخاصة بك:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Patient can only see own reports.",
            )

        return self._empty()

    def _doctor_answer(self, q: str, user: dict) -> DatabaseAssistantResult:
        doctor = _profile_for_user(user)
        if not doctor:
            return self._forbidden("doctor_profile_missing", "لا يوجد ملف طبيب مرتبط بهذا الحساب.")

        if _contains_any(q, ["schedule", "availability", "دوام", "جدول", "تواجدي", "مواعيد الدوام"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT id, weekday, start_time, end_time, slot_minutes, is_active
                FROM doctor_availability
                WHERE doctor_id=?
                ORDER BY weekday, start_time
                """,
                (doctor["id"],),
            ))
            return DatabaseAssistantResult(
                intent="doctor_schedule",
                used_database=True,
                answer="هذا جدول التوفر الخاص بك:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Doctor can only see own availability rules.",
            )

        if _contains_any(q, ["appointment", "appointments", "patients", "مواعيدي", "مرضاي", "الحجوزات", "الحجوزات القادمة"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT a.id, p.full_name AS patient_name, a.appointment_date,
                       a.start_time, a.end_time, a.status, a.reason
                FROM appointments a
                JOIN patients p ON p.id = a.patient_id
                WHERE a.doctor_id=?
                ORDER BY a.appointment_date DESC, a.start_time DESC
                LIMIT 12
                """,
                (doctor["id"],),
            ))
            return DatabaseAssistantResult(
                intent="doctor_appointments",
                used_database=True,
                answer="هذه آخر المواعيد المرتبطة بك كطبيب:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Doctor can only see own appointments.",
            )

        return self._empty()

    def _admin_answer(self, q: str) -> DatabaseAssistantResult:
        if _contains_any(q, ["metrics", "summary", "dashboard", "statistics", "إحصائيات", "احصائيات", "ملخص", "لوحة"]):
            metrics = {}
            for name, query in {
                "patients": "SELECT COUNT(*) AS c FROM patients",
                "doctors": "SELECT COUNT(*) AS c FROM doctors",
                "pending_doctors": "SELECT COUNT(*) AS c FROM doctors WHERE status='pending'",
                "appointments": "SELECT COUNT(*) AS c FROM appointments",
                "confirmed_appointments": "SELECT COUNT(*) AS c FROM appointments WHERE status='confirmed'",
                "screenings": "SELECT COUNT(*) AS c FROM screening_results",
                "reports": "SELECT COUNT(*) AS c FROM patient_reports",
                "rag_documents": "SELECT COUNT(*) AS c FROM rag_documents",
                "active_rag_documents": "SELECT COUNT(*) AS c FROM rag_documents WHERE is_active=1",
            }.items():
                metrics[name] = fetch_one(query)["c"]

            rows = [metrics]
            return DatabaseAssistantResult(
                intent="admin_metrics",
                used_database=True,
                answer="هذا ملخص تشغيلي آمن للنظام:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Admin receives aggregate metrics only.",
            )

        if _contains_any(q, ["pending doctors", "doctor applications", "طلبات الأطباء", "الأطباء المعلقين", "اطباء معلقين"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT id, full_name, specialization, clinic_location, experience_years, status, created_at
                FROM doctors
                WHERE status='pending'
                ORDER BY created_at DESC
                LIMIT 12
                """
            ))
            return DatabaseAssistantResult(
                intent="admin_pending_doctors",
                used_database=True,
                answer="هذه طلبات الأطباء المعلقة:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Admin can view doctor applications without exposing credentials.",
            )

        if _contains_any(q, ["rag", "knowledge", "documents", "vector", "chroma", "معرفة", "ملفات الراج", "فيكتور"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT id, title, is_active, created_at, updated_at, length(content) AS content_length
                FROM rag_documents
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 20
                """
            ))
            return DatabaseAssistantResult(
                intent="admin_rag_documents",
                used_database=True,
                answer="هذه حالة مستندات المعرفة المستخدمة في RAG:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Admin can inspect RAG document metadata and content length.",
            )

        if _contains_any(q, ["appointments", "حجوزات", "مواعيد"]):
            rows = _as_dicts(fetch_all(
                """
                SELECT a.id, p.full_name AS patient_name, d.full_name AS doctor_name,
                       a.appointment_date, a.start_time, a.end_time, a.status
                FROM appointments a
                JOIN patients p ON p.id = a.patient_id
                JOIN doctors d ON d.id = a.doctor_id
                ORDER BY a.appointment_date DESC, a.start_time DESC
                LIMIT 20
                """
            ))
            return DatabaseAssistantResult(
                intent="admin_appointments_overview",
                used_database=True,
                answer="هذه آخر الحجوزات في النظام:\n" + _format_rows_for_answer(rows),
                rows=rows,
                policy_note="Admin can view operational appointment overview.",
            )

        return self._empty()

    def approved_doctors(self) -> DatabaseAssistantResult:
        rows = _as_dicts(fetch_all(
            """
            SELECT id, full_name, specialization, clinic_location, experience_years, bio
            FROM doctors
            WHERE status='approved'
            ORDER BY full_name
            LIMIT 12
            """
        ))
        return DatabaseAssistantResult(
            intent="approved_doctors",
            used_database=True,
            answer="الأطباء المعتمدون الظاهرون للحجز:\n" + _format_rows_for_answer(rows),
            rows=rows,
            policy_note="Approved doctor list is public within the authenticated system.",
        )

    def available_slots(self, days: int = 14, limit: int = 12) -> DatabaseAssistantResult:
        today = date.today()
        end = today + timedelta(days=days)

        doctors = _as_dicts(fetch_all(
            """
            SELECT id, full_name, specialization, clinic_location
            FROM doctors
            WHERE status='approved'
            ORDER BY full_name
            """
        ))

        availability = _as_dicts(fetch_all(
            """
            SELECT da.*, d.full_name AS doctor_name, d.specialization, d.clinic_location
            FROM doctor_availability da
            JOIN doctors d ON d.id = da.doctor_id
            WHERE da.is_active=1 AND d.status='approved'
            ORDER BY da.weekday, da.start_time
            """
        ))

        booked = {
            (r["doctor_id"], r["appointment_date"], r["start_time"])
            for r in fetch_all(
                """
                SELECT doctor_id, appointment_date, start_time
                FROM appointments
                WHERE status='confirmed'
                  AND date(appointment_date) BETWEEN date(?) AND date(?)
                """,
                (today.isoformat(), end.isoformat()),
            )
        }

        slots: list[dict] = []
        day = today
        while day <= end and len(slots) < limit:
            weekday = day.weekday()
            for av in availability:
                if int(av["weekday"]) != weekday:
                    continue

                key = (av["doctor_id"], day.isoformat(), av["start_time"])
                if key in booked:
                    continue

                slots.append({
                    "doctor_id": av["doctor_id"],
                    "doctor_name": av["doctor_name"],
                    "specialization": av["specialization"],
                    "clinic_location": av["clinic_location"],
                    "date": day.isoformat(),
                    "start_time": av["start_time"],
                    "end_time": av["end_time"],
                    "slot_minutes": av["slot_minutes"],
                })

                if len(slots) >= limit:
                    break
            day += timedelta(days=1)

        return DatabaseAssistantResult(
            intent="available_slots",
            used_database=True,
            answer="هذه أقرب المواعيد المتاحة حاليًا:\n" + _format_rows_for_answer(slots),
            rows=slots,
            policy_note="Only approved doctors and unbooked public slots are returned.",
        )
