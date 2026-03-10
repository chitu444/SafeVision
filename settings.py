"""
config/settings.py
==================
All environment variables, hardcoded defaults, and file-system paths.
Import this module everywhere instead of re-reading os.getenv scattered
across the codebase.
"""

import os

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

INCIDENT_DB_PATH = os.path.join(PROJECT_ROOT, "incidents.db")
INCIDENT_SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "incident_snapshots")

# ---------------------------------------------------------------------------
# Roboflow
# ---------------------------------------------------------------------------
ROBOFLOW_API_KEY: str = os.getenv("PPE_ROBOFLOW_API_KEY", "yU7jc46QBhtWCNQrlT4s")
MODEL_ENDPOINT: str = os.getenv(
    "PPE_ROBOFLOW_MODEL_ENDPOINT",
    "https://detect.roboflow.com/ppe-detection-qlq3d-pwdfn/1",
)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
LOGIN_ID: str = os.getenv("SAFEVISION_LOGIN_ID", "admin")
LOGIN_PASSWORD: str = os.getenv("SAFEVISION_LOGIN_PASSWORD", "admin123")
ADMIN_EMAIL: str = os.getenv("SAFEVISION_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSCODE: str = os.getenv("PPE_ADMIN_PASSCODE", "admin123")

# ---------------------------------------------------------------------------
# Branding / logo
# ---------------------------------------------------------------------------
CORNER_LOGO_URL: str = os.getenv("SAFEVISION_CORNER_LOGO_URL", "")
CORNER_LOGO_FILE: str = os.getenv(
    "SAFEVISION_CORNER_LOGO_FILE",
    "/Users/arunkumar/Downloads/Logo.jpeg",
)
LOGO_CANDIDATE_FILES = [
    CORNER_LOGO_FILE,
    "/Users/arunkumar/Downloads/Logo.jpeg",
    "/Users/arunkumar/Downloads/logo.jpeg",
    "/Users/arunkumar/Downloads/safevision_logo.png",
    "/Users/arunkumar/Downloads/SafeVision.png",
    "/Users/arunkumar/Downloads/safevision.png",
    "/Users/arunkumar/Downloads/logo.png",
]

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_SENDER: str = "aravindmahendran30@gmail.com"
EMAIL_PASSWORD: str = "vgeq phen hoss ekcq"
EMAIL_RECEIVER: str = "aravindmahendran3@gmail.com"
EMAIL_SMTP_SERVER: str = "smtp.gmail.com"
EMAIL_SMTP_PORT: int = 587

# ---------------------------------------------------------------------------
# Detection frame dimensions
# ---------------------------------------------------------------------------
FRAME_WIDTH: int = 640
FRAME_HEIGHT: int = 480

# ---------------------------------------------------------------------------
# Demo people
# ---------------------------------------------------------------------------
DEMO_PEOPLE_OPTIONS = ["Arun", "Aravind"]
