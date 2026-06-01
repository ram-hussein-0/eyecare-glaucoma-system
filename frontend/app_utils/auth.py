import streamlit as st

from frontend.app_utils.api import api_get, api_post


def load_me(force: bool = False):
    if not st.session_state.get("token"):
        return None
    if force or "me" not in st.session_state:
        try:
            st.session_state.me = api_get("/auth/me")
        except Exception:
            st.session_state.pop("token", None)
            st.session_state.pop("me", None)
            return None
    return st.session_state.get("me")


def login(email: str, password: str):
    data = api_post("/auth/login", {"email": email, "password": password})
    st.session_state.token = data["token"]
    st.session_state.me = {"user": data["user"], "profile": None}
    load_me(force=True)
    return data


def logout():
    try:
        api_post("/auth/logout")
    except Exception:
        pass
    st.session_state.clear()


def require_login():
    me = load_me()
    if not me:
        st.warning("Please sign in to continue.")
        st.page_link("pages/01_Login_Register.py", label="Go to Login / Register")
        st.stop()
    return me


def require_role(*roles: str):
    me = require_login()
    role = me["user"]["role"]
    if role not in roles:
        st.error("This page is not available for your account role.")
        st.stop()
    return me
