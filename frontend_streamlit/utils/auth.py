"""Streamlit-side authentication: login form, session state, and per-page guards.

Session mechanism: the backend issues a JWT on login; it's kept only in
st.session_state (in-memory, cleared on logout or when the browser tab/session ends)
and sent as an Authorization: Bearer header on every API call -- see
frontend_streamlit/utils/api.py.
"""
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

ROLE_LABELS = {"admin": "Admin", "recruiter": "Recruiter", "student": "Student"}


def is_authenticated() -> bool:
    return bool(st.session_state.get("access_token"))


def current_role() -> str:
    return st.session_state.get("role", "")


def get_auth_header() -> dict:
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def login(email: str, password: str) -> bool:
    """Returns True on success. On failure, shows a clean error message and returns False."""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            data={"username": email.strip(), "password": password},
            timeout=10,
        )
    except requests.exceptions.RequestException:
        st.error("Could not reach the server. Make sure the backend is running.")
        return False

    if response.status_code == 401:
        st.error("Invalid email or password.")
        return False
    if not response.ok:
        st.error("Login failed. Please try again.")
        return False

    data = response.json()
    st.session_state["access_token"] = data["access_token"]
    st.session_state["role"] = data["role"]
    st.session_state["name"] = data["name"]
    st.session_state["email"] = data["email"]
    return True


def logout():
    for key in ("access_token", "role", "name", "email"):
        st.session_state.pop(key, None)


def render_login_form():
    """Renders a branded login form. Call this instead of the main app content when
    the viewer isn't authenticated."""
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size: 2.5rem; color: #1f77b4; margin-bottom: 0.25rem;'>📊 Resume Grader</h1>
            <p style='font-size: 1.05rem; color: #666;'>Sign in to continue</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)

        if submitted:
            if not email.strip() or not password:
                st.error("Please enter both email and password.")
            else:
                with st.spinner("Signing in..."):
                    if login(email, password):
                        st.rerun()


def require_login():
    """Guard for the top of every protected page. Stops the script if unauthenticated."""
    if not is_authenticated():
        render_login_form()
        st.stop()


def require_role(*roles: str):
    """Guard for pages/sections restricted to specific roles. Call after require_login()."""
    if current_role() not in roles:
        st.error("🚫 You don't have permission to view this page.")
        st.stop()


def render_session_sidebar():
    """Shows who's logged in + a logout button. Call on every authenticated page."""
    with st.sidebar:
        st.divider()
        name = st.session_state.get("name", "")
        role_label = ROLE_LABELS.get(current_role(), current_role())
        st.caption(f"Logged in as **{name}** ({role_label})")
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()
