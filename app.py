"""
app.py
======
SafeVision – AI Safety Monitoring System
=========================================
Entry point.  Run with:

    streamlit run app.py

Module map
----------
config/
    settings.py         – env vars, paths, constants

database/
    db.py               – SQLite init, schema migration, incident CRUD

detection/
    roboflow.py         – Roboflow REST API wrapper + frame pre-processing
    ppe_logic.py        – class predicates, clustering, stats, drawing

alerts/
    email_alert.py      – SMTP email with optional attachments
    voice_alert.py      – macOS say + browser Web Speech API
    video_alert.py      – auto-playing YouTube safety-training video

utils/
    snapshot.py         – save annotated frame as JPEG
    logo.py             – logo discovery (file → base64) + render helper
    charts.py           – matplotlib pie chart

ui/
    styles.py           – CSS injection (login + app)
    login_page.py       – login form
    sidebar.py          – sidebar config panel → SidebarConfig dataclass
    pages/
        live_detection.py  – WebRTC live PPE detection
        upload.py          – static image upload analysis
        incident_history.py – incident table view
"""

import streamlit as st

from config.settings import LOGIN_ID, LOGIN_PASSWORD, ADMIN_EMAIL
from database.db import init_db, log_incident, get_incident_count
from alerts.email_alert import send_alert
from ui.login_page import render_login_page
from ui.styles import inject_app_styles
from ui.sidebar import render_sidebar
from utils.logo import render_corner_logo

import ui.pages.live_detection as page_live
import ui.pages.upload as page_upload
import ui.pages.incident_history as page_history

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AI Safety Monitoring System", layout="wide")

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "authenticated":                    False,
    "login_user":                       "",
    "last_incident_log_ts":             0.0,
    "last_email_alert_ts":              0.0,
    "live_stats":                       {"total": 0, "safe": 0, "unsafe": 0},
    "voice_alert_nonce":                0,
    "voice_alert_last_handled_nonce":   0,
    "last_auto_voice_ts":               0.0,
    "last_auto_video_ts":               0.0,
    "safety_video_nonce":               0,
    "safety_video_last_handled_nonce":  0,
    "add_test_incident_requested":      False,
    "send_test_email_requested":        False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Authentication gate
# ---------------------------------------------------------------------------
if not st.session_state.authenticated:
    clicked, uid, pwd = render_login_page()
    if clicked:
        allowed = {LOGIN_ID.lower(), ADMIN_EMAIL.lower()}
        if uid.strip().lower() in allowed and pwd == LOGIN_PASSWORD:
            st.session_state.authenticated = True
            st.session_state.login_user    = uid
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid Employee/Admin ID or password.")
    st.stop()

# ---------------------------------------------------------------------------
# Authenticated app
# ---------------------------------------------------------------------------
inject_app_styles()
render_corner_logo()

st.markdown(
    f"""
    <div class='sv-topbar'>
      <div class='sv-logo'><span class='sv-safe'>Safe</span><span class='sv-vision'>Vision</span></div>
      <div class='sv-chip'>🛰️ {st.session_state.login_user}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Database init
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# Sidebar (returns SidebarConfig dataclass)
# ---------------------------------------------------------------------------
cfg = render_sidebar(st.session_state.login_user)

# ---------------------------------------------------------------------------
# Sidebar deferred actions
# ---------------------------------------------------------------------------
if st.session_state.send_test_email_requested:
    ok, err = send_alert(
        subject="SafeVision Test Email",
        body="This is a test email from SafeVision. Email alert configuration is working.",
        enabled=cfg.email_alert_enabled,
    )
    st.sidebar.success("Test email sent.") if ok else st.sidebar.error(f"Test email failed: {err}")
    st.session_state.send_test_email_requested = False

if st.session_state.add_test_incident_requested:
    log_incident("manual_test", total=1, safe=0, unsafe=1, details={"note": "Manual test incident"})
    st.sidebar.success("Test incident added.")
    st.session_state.add_test_incident_requested = False

# Incident count badge
try:
    st.sidebar.info(f"Incidents stored: {get_incident_count()}")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
if cfg.page == "Live Detection":
    page_live.render(cfg)

elif cfg.page == "Upload":
    page_upload.render(cfg)

elif cfg.page == "Settings":
    st.subheader("Settings")
    st.info("Use the left sidebar for advanced configuration and credentials.")

elif cfg.page == "Incident History":
    page_history.render()
