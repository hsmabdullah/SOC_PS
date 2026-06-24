"""
app.py
───────
Main Streamlit entry point for the SOC Alert Triage Platform.

Run with:
    streamlit run app.py

Architecture:
    - Pages are loaded dynamically from streamlit_pages/
    - Authentication is enforced before any page renders
    - Session state holds the signed auth token (not the user object)
    - Audit log entry is written on every page navigation
"""

from __future__ import annotations

import streamlit as st

from config.logging_config import configure_logging, get_logger
from config.settings import get_settings
from security.auth import Role, get_auth_service
from security.audit_logger import get_audit_logger

# ── Bootstrap ──────────────────────────────────────────────────────────────────
try:
    cfg = get_settings()
    configure_logging(cfg.app.log_level, cfg.app.log_file)
except Exception as e:
    st.error(f"Configuration error: {e}. Please check your .env file.")
    st.stop()

logger = get_logger(__name__)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SOC Alert Triage Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Auth wall ─────────────────────────────────────────────────────────────────
def render_login() -> None:
    """Render the login form."""
    st.title("🛡️ SOC Alert Triage Platform")
    st.subheader("Please log in to continue")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            auth = get_auth_service()
            token = auth.login(username, password)
            if token:
                st.session_state["auth_token"] = token
                st.session_state["username"] = username
                get_audit_logger().log(
                    username=username,
                    role="unknown",
                    module="auth",
                    action="login",
                    result="success",
                )
                st.rerun()
            else:
                st.error("Invalid username or password.")
                get_audit_logger().log(
                    username=username,
                    role="unknown",
                    module="auth",
                    action="login",
                    result="failure",
                )


def get_current_user():
    """Return the validated User object or None."""
    token = st.session_state.get("auth_token")
    if not token:
        return None
    auth = get_auth_service()
    return auth.validate_token(token)


# ── Sidebar navigation ────────────────────────────────────────────────────────
PAGES = {
    "📊 Dashboard":           "streamlit_pages.dashboard",
    "🗄️ Database Explorer":   "streamlit_pages.database_explorer",
    "📋 Data Profiling":      "streamlit_pages.data_profiling",
    "⚙️ AI Preprocessing":    "streamlit_pages.preprocessing",
    "🔍 EDA Agent":           "streamlit_pages.eda_agent",
    "🏗️ Feature Engineering": "streamlit_pages.feature_engineering",
    "🤖 Model Training":      "streamlit_pages.model_training",
    "📈 Evaluation":          "streamlit_pages.evaluation",
    "💡 Explainability":      "streamlit_pages.explainability",
    "🎯 Predictions":         "streamlit_pages.predictions",
    "🤝 Analyst Copilot":     "streamlit_pages.analyst_copilot",
    "📝 Audit Logs":          "streamlit_pages.audit_logs",
}

ROLE_REQUIRED = {
    "🗄️ Database Explorer":   Role.ADMIN,
    "⚙️ AI Preprocessing":    Role.ANALYST,
    "🏗️ Feature Engineering": Role.ANALYST,
    "🤖 Model Training":      Role.ADMIN,
    "📈 Evaluation":          Role.ANALYST,
    "💡 Explainability":      Role.ANALYST,
    "🎯 Predictions":         Role.ANALYST,
    "🤝 Analyst Copilot":     Role.ANALYST,
    "📝 Audit Logs":          Role.ADMIN,
}


def render_sidebar(user) -> str:
    """Render sidebar and return the selected page name."""
    auth = get_auth_service()

    with st.sidebar:
        st.image("https://img.icons8.com/external-flaticons-lineal-color-flat-icons/64/external-shield-security-flaticons-lineal-color-flat-icons.png", width=60)
        st.title("SOC Triage")
        st.caption(f"👤 {user.full_name or user.username}  •  🔑 {user.role.name}")
        st.divider()

        available_pages = [
            name for name in PAGES
            if auth.require_role(user, ROLE_REQUIRED.get(name, Role.VIEWER))
        ]

        selection = st.radio("Navigation", available_pages, label_visibility="collapsed")

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            get_audit_logger().log(
                username=user.username,
                role=user.role.name,
                module="auth",
                action="logout",
                result="success",
            )
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    return selection  # type: ignore[return-value]


# ── Main render loop ──────────────────────────────────────────────────────────
def main() -> None:
    user = get_current_user()

    if user is None:
        render_login()
        return

    page_name = render_sidebar(user)

    # Lazy-import the selected page module and call its render() function
    module_path = PAGES.get(page_name, "streamlit_pages.dashboard")
    try:
        import importlib
        module = importlib.import_module(module_path)
        get_audit_logger().log(
            username=user.username,
            role=user.role.name,
            module=module_path.split(".")[-1],
            action="page_view",
            result="success",
        )
        module.render(user)  # type: ignore[attr-defined]
    except ImportError:
        st.info(f"Page '{page_name}' is under construction.")
    except Exception as exc:
        logger.exception("Page render error on '%s': %s", page_name, exc)
        st.error(f"An error occurred loading this page. Please try again or contact your administrator.")


if __name__ == "__main__":
    main()