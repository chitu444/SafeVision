import streamlit as st
from ui.live_detection import live_detection
from ui.incident_history import incident_history

def dashboard():
    st.sidebar.title("Navigation")

    page = st.sidebar.radio(
        "Select page",
        ["Live Detection","Incident History"]
    )

    if page == "Live Detection":
        live_detection()

    elif page == "Incident History":
        incident_history()