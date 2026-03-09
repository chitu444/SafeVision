import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROBoflow_API_KEY = os.getenv("PPE_ROBOFLOW_API_KEY", "CHANGE_ME")
MODEL_ENDPOINT = os.getenv("PPE_ROBOFLOW_MODEL_ENDPOINT", "https://detect.roboflow.com/model")

LOGIN_ID = os.getenv("SAFEVISION_LOGIN_ID", "admin")
LOGIN_PASSWORD = os.getenv("SAFEVISION_LOGIN_PASSWORD", "admin123")

INCIDENT_DB_PATH = os.path.join(APP_DIR, "incidents.db")