"""
ui/login_page.py
================
Renders the SafeVision login screen and returns the submitted credentials.
"""

import streamlit as st

from ui.styles import inject_login_styles
from utils.logo import resolve_logo_src


def render_login_page() -> tuple[bool, str, str]:
    """
    Render the full login page.

    Returns
    -------
    ``(login_clicked, user_id, password)``
    """
    inject_login_styles()

    logo_src = resolve_logo_src()
    if logo_src:
        st.markdown(
            f"<div class='brand-wrap'>"
            f"<img src='{logo_src}' class='login-brand-logo' alt='SafeVision logo'/>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class='brand-wrap'>
          <div class='brand-title'><span class='safe'>Safe</span><span class='vision'>Vision</span></div>
          <div class='brand-sub'>AI SAFETY MONITORING SYSTEM</div>
          <div class='login-caption'>Login</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        st.markdown("<div class='login-label'>Employee ID / Admin ID</div>", unsafe_allow_html=True)
        user_id = st.text_input("Employee ID / Admin ID", placeholder="Enter your ID")
        st.markdown("<div class='login-label'>Password</div>", unsafe_allow_html=True)
        password = st.text_input("Password", type="password", placeholder="Enter password")
        login_clicked = st.form_submit_button("✅ Login")

    return login_clicked, user_id, password
