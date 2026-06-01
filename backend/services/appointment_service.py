from datetime import date, datetime, timedelta

from fastapi import HTTPException

from backend.db.database import execute, fetch_all, fetch_one

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%H:%M")


def _format_time(value: datetime) -> str:
    return value.strftime("%H:%M")


def generate_slots_for_doctor(doctor_id: int, date_from: date, date_to: date) -> list[dict]:
    doctor = fetch_one("SELECT * FROM doctors WHERE id = ? AND status = 'approved'", (doctor_id,))
    if not doctor:
        raise HTTPException(status_code=404, detail="Approved doctor was not found.")

    availability = fetch_all(
        "SELECT * FROM doctor_availability WHERE doctor_id = ? AND is_active = 1 ORDER BY weekday, start_time",
        (doctor_id,),
    )
    booked = fetch_all(
        """SELECT appointment_date, start_time FROM appointments
           WHERE doctor_id = ? AND status = 'confirmed'
           AND date(appointment_date) BETWEEN date(?) AND date(?)""",
        (doctor_id, date_from.isoformat(), date_to.isoformat()),
    )
    booked_keys = {(b["appointment_date"], b["start_time"]) for b in booked}

    slots = []
    current = date_from
    availability_by_weekday = {}
    for item in availability:
        availability_by_weekday.setdefault(item["weekday"], []).append(item)

    while current <= date_to:
        for av in availability_by_weekday.get(current.weekday(), []):
            start = _parse_time(av["start_time"])
            end = _parse_time(av["end_time"])
            step = timedelta(minutes=int(av["slot_minutes"]))
            cursor = start
            while cursor + step <= end:
                start_str = _format_time(cursor)
                end_str = _format_time(cursor + step)
                key = (current.isoformat(), start_str)
                if key not in booked_keys and current >= date.today():
                    slots.append({
                        "doctor_id": doctor_id,
                        "doctor_name": doctor["full_name"],
                        "date": current.isoformat(),
                        "weekday": WEEKDAYS[current.weekday()],
                        "start_time": start_str,
                        "end_time": end_str,
                    })
                cursor += step
        current += timedelta(days=1)
    return slots


def book_appointment(patient_id: int, doctor_id: int, appointment_date: str, start_time: str, end_time: str, reason: str | None) -> dict:
    doctor = fetch_one("SELECT * FROM doctors WHERE id = ? AND status = 'approved'", (doctor_id,))
    if not doctor:
        raise HTTPException(status_code=404, detail="Approved doctor was not found.")
    # Confirm the requested slot is still available.
    available = generate_slots_for_doctor(doctor_id, date.fromisoformat(appointment_date), date.fromisoformat(appointment_date))
    if not any(s["date"] == appointment_date and s["start_time"] == start_time for s in available):
        raise HTTPException(status_code=409, detail="This appointment slot is no longer available.")
    try:
        appt_id = execute(
            """INSERT INTO appointments(patient_id, doctor_id, appointment_date, start_time, end_time, status, reason)
               VALUES(?,?,?,?,?,'confirmed',?)""",
            (patient_id, doctor_id, appointment_date, start_time, end_time, reason),
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail="This appointment slot is already booked.") from exc
    return get_appointment(appt_id)


def get_appointment(appointment_id: int) -> dict:
    row = fetch_one(
        """
        SELECT a.*, p.full_name AS patient_name, d.full_name AS doctor_name, d.specialization, d.clinic_location
        FROM appointments a
        JOIN patients p ON p.id = a.patient_id
        JOIN doctors d ON d.id = a.doctor_id
        WHERE a.id = ?
        """,
        (appointment_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Appointment was not found.")
    return row


def patient_appointments(patient_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT a.*, d.full_name AS doctor_name, d.specialization, d.clinic_location
        FROM appointments a
        JOIN doctors d ON d.id = a.doctor_id
        WHERE a.patient_id = ?
        ORDER BY date(a.appointment_date) DESC, a.start_time DESC
        """,
        (patient_id,),
    )


def doctor_appointments(doctor_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT a.*, p.full_name AS patient_name, p.phone AS patient_phone, p.age AS patient_age, p.gender AS patient_gender
        FROM appointments a
        JOIN patients p ON p.id = a.patient_id
        WHERE a.doctor_id = ?
        ORDER BY date(a.appointment_date) DESC, a.start_time DESC
        """,
        (doctor_id,),
    )
