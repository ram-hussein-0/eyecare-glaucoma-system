from datetime import date, timedelta

from backend.db.database import fetch_all
from backend.services.appointment_service import generate_slots_for_doctor


def booking_intent_detected(message: str) -> bool:
    text = message.lower()
    keywords = ["book", "appointment", "doctor", "available", "slot", "موعد", "حجز", "طبيب"]
    return any(k in text for k in keywords)


def suggest_nearest_slots(days: int = 14, limit: int = 5) -> list[dict]:
    doctors = fetch_all("SELECT id, full_name, specialization FROM doctors WHERE status='approved' ORDER BY full_name")
    all_slots: list[dict] = []
    start = date.today()
    end = start + timedelta(days=days)
    for doctor in doctors:
        all_slots.extend(generate_slots_for_doctor(doctor["id"], start, end))
    return sorted(all_slots, key=lambda s: (s["date"], s["start_time"]))[:limit]
