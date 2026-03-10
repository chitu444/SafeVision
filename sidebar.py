"""
ui/sidebar.py
=============
Renders the left sidebar and returns all user-configured values as a
``SidebarConfig`` dataclass so the rest of the app receives a single,
typed object rather than scattered ``st.session_state`` keys.
"""

from dataclasses import dataclass, field

import streamlit as st

from config.settings import (
    ROBOFLOW_API_KEY,
    MODEL_ENDPOINT,
    LOGIN_ID,
    ADMIN_EMAIL,
    ADMIN_PASSCODE,
)
from detection.roboflow import test_connection


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------

@dataclass
class SidebarConfig:
    # Auth / navigation
    user_role: str = "Supervisor"
    page: str = "Live Detection"
    is_admin_authorized: bool = True
    can_configure: bool = False
    can_operate_live: bool = True

    # Roboflow
    api_key: str = ROBOFLOW_API_KEY
    model_endpoint: str = MODEL_ENDPOINT

    # Detection thresholds
    detection_enabled: bool = True
    confidence_threshold: float = 0.45
    helmet_threshold: float = 0.35
    vest_threshold: float = 0.45
    goggles_threshold: float = 0.30
    person_threshold: float = 0.45
    no_ppe_threshold: float = 0.45
    overlap_threshold: float = 0.30
    enhance_frame: bool = True
    selected_classes: list = field(default_factory=list)
    show_boxes: bool = True

    # Email
    email_alert_enabled: bool = True
    email_cooldown: int = 60

    # Voice
    voice_alert_enabled: bool = True
    auto_voice_on_unsafe: bool = True
    auto_voice_cooldown: int = 15

    # Video
    auto_video_on_unsafe: bool = True
    safety_video_url: str = "https://youtu.be/PiklWx68dSI?si=1ZCGcCNYlZPTFM2I"
    auto_video_cooldown: int = 120

    # Demo people
    demo_name_alerts_enabled: bool = True
    demo_active_people: list = field(default_factory=lambda: ["Arun", "Aravind"])


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_sidebar(login_user: str) -> SidebarConfig:
    """Render the full sidebar and return a ``SidebarConfig`` instance."""
    cfg = SidebarConfig()

    with st.sidebar:
        st.success(f"Logged in as: {login_user}")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.login_user = ""
            st.rerun()
        st.divider()

        # --- Role & Navigation ---
        st.header("⚙️ Configuration")
        st.divider()
        st.subheader("🔐 Access Role")

        cfg.user_role = st.selectbox("Select role", ["Viewer", "Supervisor", "Admin"], index=1)
        nav_options = (
            ["Incident History"]
            if cfg.user_role == "Viewer"
            else ["Live Detection", "Upload", "Settings", "Incident History"]
        )
        cfg.page = st.radio("Navigation", nav_options)

        admin_pass = ""
        if cfg.user_role == "Admin":
            admin_pass = st.text_input("Admin passcode", type="password")

        cfg.is_admin_authorized = cfg.user_role != "Admin" or admin_pass == ADMIN_PASSCODE
        cfg.can_configure   = cfg.user_role == "Admin" and cfg.is_admin_authorized
        cfg.can_operate_live = cfg.user_role in ("Admin", "Supervisor") and cfg.is_admin_authorized

        if cfg.user_role == "Admin" and not cfg.is_admin_authorized:
            st.error("Admin passcode is incorrect. Configuration and live controls are locked.")

        # --- Detection ---
        st.divider()
        st.subheader("Detection Settings")
        cfg.detection_enabled = st.checkbox("Enable Detection", value=True)
        cfg.api_key = st.text_input(
            "Roboflow API Key", value=ROBOFLOW_API_KEY, type="password",
            disabled=not cfg.can_configure,
        )
        cfg.model_endpoint = st.text_input(
            "Roboflow Model Endpoint", value=MODEL_ENDPOINT,
            disabled=not cfg.can_configure,
        )

        if cfg.can_configure:
            cfg.confidence_threshold = st.slider("Default Confidence Threshold", 0.0, 1.0, 0.45, 0.05)
            cfg.helmet_threshold     = st.slider("Helmet Threshold",              0.0, 1.0, 0.35, 0.05)
            cfg.vest_threshold       = st.slider("Vest/Jacket Threshold",         0.0, 1.0, 0.45, 0.05)
            cfg.goggles_threshold    = st.slider("Goggles Threshold",             0.0, 1.0, 0.30, 0.05)
            cfg.person_threshold     = st.slider("Person Threshold",              0.0, 1.0, 0.40, 0.05)
            cfg.no_ppe_threshold     = st.slider("No-PPE Class Threshold",        0.0, 1.0, 0.35, 0.05)
            cfg.overlap_threshold    = st.slider("NMS Overlap Threshold",         0.0, 1.0, 0.30, 0.05)
            cfg.enhance_frame        = st.checkbox("Enhance Frame Before Detection", value=True)
            raw_classes              = st.text_input("Filter classes (comma-separated)")
            cfg.selected_classes     = [c.strip() for c in raw_classes.split(",") if c.strip()]
            cfg.show_boxes           = st.checkbox("Show Bounding Boxes", value=True)
        else:
            st.caption("Detection settings are editable by Admin only.")

        if st.button("Test Roboflow Connection"):
            ok, msg = test_connection(cfg.api_key, cfg.model_endpoint)
            (st.success if ok else st.error)(msg)

        # --- Email ---
        st.divider()
        st.subheader("📧 Email Alert Settings")
        cfg.email_alert_enabled = st.checkbox("Enable Email Alerts", value=True)
        st.caption("Sender / receiver configured via environment variables.")
        cfg.email_cooldown = st.number_input("Alert Cooldown (seconds)", 0, 3600, 60)

        if st.button("Send Test Email", use_container_width=True):
            st.session_state.send_test_email_requested = True

        # --- Voice ---
        st.divider()
        st.subheader("🔊 Voice Alerts")
        cfg.voice_alert_enabled  = st.checkbox("Enable Voice Alerts", value=True)
        cfg.auto_voice_on_unsafe = st.checkbox("Auto voice alert on unsafe detection", value=True)
        cfg.auto_voice_cooldown  = st.number_input("Auto voice cooldown (seconds)", 1, 3600, 15)
        if st.button("Trigger Voice Alert", use_container_width=True, disabled=not cfg.voice_alert_enabled):
            st.session_state.voice_alert_nonce = st.session_state.get("voice_alert_nonce", 0) + 1

        # --- Video ---
        st.divider()
        st.subheader("🎬 Safety Training Video")
        cfg.auto_video_on_unsafe = st.checkbox("Auto play training video on unsafe detection", value=True)
        cfg.safety_video_url     = st.text_input(
            "YouTube safety video URL",
            value="https://youtu.be/PiklWx68dSI?si=1ZCGcCNYlZPTFM2I",
        )
        cfg.auto_video_cooldown = st.number_input("Auto video cooldown (seconds)", 10, 7200, 120)

        # --- Demo people ---
        st.divider()
        st.subheader("🧑 Demo Person Recognition")
        cfg.demo_name_alerts_enabled = st.checkbox("Enable demo person-name alerts", value=True)
        st.caption("Demo mapping: first refs → Arun, next refs → Aravind")
        cfg.demo_active_people = st.multiselect(
            "People currently in monitored zone (demo)",
            options=["Arun", "Aravind"],
            default=["Arun", "Aravind"],
        )

        if st.button("Add Test Incident", use_container_width=True):
            st.session_state.add_test_incident_requested = True

        st.divider()

    return cfg
