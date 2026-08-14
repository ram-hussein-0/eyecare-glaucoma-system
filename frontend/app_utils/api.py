import os
import json as jsonlib
from pathlib import Path
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _headers() -> dict:
    token = st.session_state.get("token")
    return {"X-Session-Token": token} if token else {}


def _friendly_message(data: Any) -> str:
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, list):
            messages: list[str] = []
            for item in detail:
                if isinstance(item, dict):
                    loc = item.get("loc", [])
                    field = loc[-1] if loc else "field"
                    msg = item.get("msg", "Invalid value")
                    messages.append(f"{field}: {msg}")
                else:
                    messages.append(str(item))
            return "\n".join(messages)
        if detail:
            return str(detail)
        if data.get("message"):
            return str(data["message"])
    return str(data)


def handle_response(response: requests.Response) -> Any:
    try:
        data = response.json()
    except Exception:
        data = response.text

    if response.status_code >= 400:
        raise RuntimeError(_friendly_message(data))
    return data


def api_get(path: str, **params):
    return handle_response(
        requests.get(
            f"{API_BASE_URL}{path}",
            headers=_headers(),
            params={k: v for k, v in params.items() if v is not None},
            timeout=30,
        )
    )


def api_post(path: str, json: dict | None = None, files=None, data=None):
    kwargs: dict[str, Any] = {"headers": _headers(), "timeout": 90}

    if files is not None:
        kwargs["files"] = files
        if data is not None:
            kwargs["data"] = data
    else:
        kwargs["json"] = json
        if data is not None:
            kwargs["data"] = data

    return handle_response(requests.post(f"{API_BASE_URL}{path}", **kwargs))


def api_post_stream(path: str, json: dict | None = None):
    headers = _headers()
    headers["Accept"] = "text/event-stream"

    with requests.post(
        f"{API_BASE_URL}{path}",
        headers=headers,
        json=json,
        stream=True,
        timeout=(10, 120),
    ) as response:
        if response.status_code >= 400:
            return handle_response(response)

        for raw_line in response.iter_lines(
            chunk_size=1,
            decode_unicode=True,
        ):
            if not raw_line:
                continue

            line = raw_line.strip()

            if line.startswith(":"):
                continue

            if not line.startswith("data:"):
                continue

            payload = line[5:].strip()

            if not payload:
                continue

            try:
                yield jsonlib.loads(payload)
            except jsonlib.JSONDecodeError:
                continue


def api_put(path: str, json: dict | None = None):
    return handle_response(
        requests.put(f"{API_BASE_URL}{path}", headers=_headers(), json=json, timeout=30)
    )


def api_patch(path: str, json: dict | None = None):
    return handle_response(
        requests.patch(f"{API_BASE_URL}{path}", headers=_headers(), json=json, timeout=30)
    )


def api_delete(path: str):
    return handle_response(
        requests.delete(f"{API_BASE_URL}{path}", headers=_headers(), timeout=30)
    )


def api_download(path: str) -> bytes:
    response = requests.get(f"{API_BASE_URL}{path}", headers=_headers(), timeout=60)
    if response.status_code >= 400:
        try:
            data = response.json()
        except Exception:
            data = response.text
        raise RuntimeError(_friendly_message(data))
    return response.content
