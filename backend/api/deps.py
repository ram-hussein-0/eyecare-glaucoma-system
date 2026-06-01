from fastapi import Depends, Header, HTTPException, status

from backend.db.database import fetch_one


def get_current_user(x_session_token: str | None = Header(default=None, alias="X-Session-Token")) -> dict:
    if not x_session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token is required.")
    row = fetch_one(
        """
        SELECT u.*
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND datetime(s.expires_at) > datetime('now') AND u.is_active = 1
        """,
        (x_session_token,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session.")
    return row


def require_role(*roles: str):
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this resource.")
        return user
    return checker


def get_patient(user: dict = Depends(require_role("patient"))) -> dict:
    patient = fetch_one("SELECT * FROM patients WHERE user_id = ?", (user["id"],))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile was not found.")
    return patient


def get_doctor(user: dict = Depends(require_role("doctor"))) -> dict:
    doctor = fetch_one("SELECT * FROM doctors WHERE user_id = ?", (user["id"],))
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile was not found.")
    return doctor
