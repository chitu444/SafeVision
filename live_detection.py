import streamlit as st
import cv2
from detection.roboflow_detector import detect_ppe
from database.incident_logger import log_incident

def live_detection():
    st.header("Live PPE Detection")

    cap = cv2.VideoCapture(0)

    frame_window = st.empty()

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break

        predictions = detect_ppe(frame)

        total = len(predictions.get("predictions", []))
        unsafe = sum(1 for p in predictions.get("predictions", []) if "no_" in p["class"])
        safe = max(total - unsafe,0)

        if unsafe > 0:
            log_incident("webcam", total, safe, unsafe)

        frame_window.image(frame, channels="BGR")