from pathlib import Path

from backend.core.config import get_settings
from backend.core.security import hash_password
from backend.db.database import execute, fetch_one, init_db


def upsert_user(email: str, password: str, role: str, full_name: str) -> int:
    existing = fetch_one("SELECT id FROM users WHERE email = ?", (email,))
    if existing:
        return existing["id"]
    return execute(
        "INSERT INTO users(email, password_hash, role, full_name) VALUES(?,?,?,?)",
        (email, hash_password(password), role, full_name),
    )


def seed() -> None:
    init_db()
    settings = get_settings()

    
    # Older local-only addresses such as admin@opticcare.local are rejected by strict
    # email validators. Keep the seeded admin on a normal domain so login works.
    execute("UPDATE users SET email = ? WHERE email = ?", ("admin@opticcare.com", "admin@opticcare.local"))
    admin_id = upsert_user("admin@opticcare.com", "Admin@12345", "admin", "System Administrator")

    patient_user_id = upsert_user("patient@example.com", "Patient@12345", "patient", "Nour Haddad")
    if not fetch_one("SELECT id FROM patients WHERE user_id = ?", (patient_user_id,)):
        execute(
            "INSERT INTO patients(user_id, full_name, phone, age, gender, city, medical_notes) VALUES(?,?,?,?,?,?,?)",
            (patient_user_id, "Nour Haddad", "+963-900-000-001", 44, "Female", "Damascus", "Family history of glaucoma."),
        )

    doctor_user_id = upsert_user("doctor@example.com", "Doctor@12345", "doctor", "Dr. Kareem Mansour")
    if not fetch_one("SELECT id FROM doctors WHERE user_id = ?", (doctor_user_id,)):
        doctor_id = execute(
            """INSERT INTO doctors(user_id, full_name, specialization, bio, clinic_location, phone, experience_years, status)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                doctor_user_id,
                "Dr. Kareem Mansour",
                "Ophthalmology",
                "Ophthalmologist focused on glaucoma screening, optic nerve assessment, and preventive eye care.",
                "EyeCare Center - Main Clinic",
                "+963-900-000-002",
                10,
                "approved",
            ),
        )
        for weekday, start, end in [(0, "09:00", "13:00"), (2, "12:00", "17:00"), (4, "09:00", "14:00")]:
            execute(
                "INSERT INTO doctor_availability(doctor_id, weekday, start_time, end_time, slot_minutes) VALUES(?,?,?,?,?)",
                (doctor_id, weekday, start, end, 30),
            )

    pending_user_id = upsert_user("pending.doctor@example.com", "Doctor@12345", "doctor", "Dr. Lina Farah")
    if not fetch_one("SELECT id FROM doctors WHERE user_id = ?", (pending_user_id,)):
        execute(
            """INSERT INTO doctors(user_id, full_name, specialization, bio, clinic_location, phone, experience_years, status)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                pending_user_id,
                "Dr. Lina Farah",
                "Ophthalmology",
                "Ophthalmologist application awaiting review.",
                "EyeCare Center - North Branch",
                "+963-900-000-003",
                5,
                "pending",
            ),
        )

    docs = {
        "About preliminary glaucoma screening": """
Glaucoma is an eye condition that can damage the optic nerve. Early identification of suspicious findings is important because the disease may progress without obvious symptoms. This system provides preliminary screening support from fundus images and encourages ophthalmology review when risk indicators are high.
""".strip(),
        "How appointment booking works": """
Patients can view approved ophthalmologists, choose an available appointment slot, and track the appointment status. Doctors manage their weekly availability and can review appointment-related screening reports.
""".strip(),
        "Understanding screening results": """
The result is presented as Low Risk, Uncertain, or High Risk. It is not a final medical diagnosis. A high-risk result means the patient should book an appointment with an ophthalmologist for clinical examination and confirmation.
""".strip(),
        "Image upload guidance": """
Upload a clear fundus image when available. Blurry, poorly illuminated, or cropped images may reduce screening quality. If symptoms are urgent, the patient should seek medical review regardless of the automated screening result.
""".strip(),
    }
    for title, content in docs.items():
        if not fetch_one("SELECT id FROM rag_documents WHERE title = ?", (title,)):
            execute("INSERT INTO rag_documents(title, content, is_active) VALUES(?,?,1)", (title, content))

    # Ensure file-based RAG docs exist too.
    settings.rag_docs_path.mkdir(parents=True, exist_ok=True)
    for title, content in docs.items():
        safe = title.lower().replace(" ", "_").replace("/", "_") + ".md"
        p = settings.rag_docs_path / safe
        if not p.exists():
            p.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")

    print("Database initialized and seeded successfully.")
    print(f"Database: {settings.db_path}")


if __name__ == "__main__":
    seed()
