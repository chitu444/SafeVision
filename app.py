import streamlit as st
from auth.login import login_page
from ui.dashboard import dashboard

st.set_page_config(page_title="SafeVision Industrial", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_page()
    st.stop()

dashboard()