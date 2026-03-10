"""
ui/pages/incident_history.py
============================
Incident history table page.
"""

import streamlit as st

from database.db import fetch_incidents


def render() -> None:
    st.subheader("Incident History")
    limit = st.number_input("Rows to load", min_value=10, max_value=1000, value=200, step=10)
    df = fetch_incidents(limit=int(limit))
    if df.empty:
        st.info("No incidents logged yet.")
    else:
        st.dataframe(df, use_container_width=True)
