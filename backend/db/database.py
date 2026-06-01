import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from backend.core.config import get_settings


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor(commit: bool = False):
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    with get_connection() as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()


def fetch_one(query: str, params: Iterable[Any] = ()) -> dict | None:
    with db_cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchone()


def fetch_all(query: str, params: Iterable[Any] = ()) -> list[dict]:
    with db_cursor() as cur:
        cur.execute(query, tuple(params))
        return cur.fetchall()


def execute(query: str, params: Iterable[Any] = ()) -> int:
    with db_cursor(commit=True) as cur:
        cur.execute(query, tuple(params))
        return int(cur.lastrowid or 0)


def execute_many(query: str, seq: list[Iterable[Any]]) -> None:
    with db_cursor(commit=True) as cur:
        cur.executemany(query, seq)
