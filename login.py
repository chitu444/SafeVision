import streamlit as st
from config.settings import LOGIN_ID, LOGIN_PASSWORD

def login_page():
    st.title("SafeVision Login")

    user = st.text_input("User ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == LOGIN_ID and password == LOGIN_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials")