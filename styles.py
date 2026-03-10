"""
ui/styles.py
============
All CSS for the SafeVision app injected through ``st.markdown``.
Split into two functions so login-page and main-app styles are loaded
independently (avoiding unnecessary CSS bulk on the login screen).
"""

import streamlit as st


def inject_login_styles() -> None:
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] {display: none;}
        div[data-testid="stToolbar"] {display: none;}
        .block-container {padding-top: 0.15rem !important;}
        .sv-topbar { display:none !important; height:0 !important; margin:0 !important;
                     padding:0 !important; border:0 !important; box-shadow:none !important; }
        .login-shell {
            width: min(900px, 95vw); margin: 0 auto;
            padding: 2rem 2.1rem 1.8rem 2.1rem; border-radius: 26px;
            background: linear-gradient(180deg, #fbfdff 0%, #f2f8ff 100%);
            border: 6px solid #1172d8;
            box-shadow: inset 0 0 0 4px #35b44b, 0 18px 40px rgba(15,55,110,0.2);
        }
        .brand-wrap { text-align: center; margin-bottom: 0.55rem; }
        .login-brand-logo { height:140px; width:140px; object-fit:contain; margin-bottom:0.3rem;
                            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.14)); }
        .brand-title { font-size: clamp(2.65rem,5vw,4.5rem); font-weight:900;
                       letter-spacing:0.5px; line-height:1.05; margin-bottom:0.1rem; }
        .safe  { color: #f27a05; }
        .vision { color: #0057b8; }
        .brand-sub { font-size:1.35rem; font-weight:700; color:#3f4b60; letter-spacing:1.4px; }
        .login-caption {
            display:flex; align-items:center; justify-content:center; gap:0.9rem;
            text-align:center; color:#0d376f; font-size:2.05rem; font-weight:800;
            margin: 0.55rem 0 1rem 0;
        }
        .login-caption::before, .login-caption::after {
            content:""; width: min(220px,24vw); height:2px; border-radius:5px;
            background: linear-gradient(90deg,rgba(185,203,225,.25),rgba(165,191,222,.9),rgba(185,203,225,.25));
        }
        .stTextInput > div > div > input {
            border-radius:16px; border:2px solid #8daed5;
            padding:0.86rem 0.95rem; font-size:1.34rem; background:#f9fbff;
        }
        .login-label { color:#143766; font-size:1.02rem; font-weight:600; margin:0.22rem 0; }
        .stButton > button {
            width:100%; border:none; border-radius:16px; font-size:1.55rem; font-weight:800;
            color:#ffffff; background:linear-gradient(135deg,#2fbbff 0%,#005fd0 100%);
            box-shadow:0 8px 18px rgba(0,88,186,.35); padding:0.65rem 1rem;
        }
        .stButton > button:hover { background:linear-gradient(135deg,#4ecbff 0%,#0e73e5 100%); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_app_styles() -> None:
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] {display: none;}
        div[data-testid="stToolbar"] {display: none;}
        .block-container {padding-top: 1rem;}
        .stApp { background: linear-gradient(180deg,#d6e8ff 0%,#c4dcff 100%); color:#10233f; }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg,#0d2a4f 0%,#0a223f 100%); color:#f4f8ff; }
        section[data-testid="stSidebar"] * { color:#eef6ff !important; }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div[role="radiogroup"] label,
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
            color:#ffffff !important; font-weight:600 !important; }
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="base-input"] > div,
        section[data-testid="stSidebar"] [data-baseweb="input"] > div {
            background:#f6fbff !important; border:1px solid #89b4e7 !important; color:#0b1f3a !important; }
        section[data-testid="stSidebar"] [data-baseweb="select"] span,
        section[data-testid="stSidebar"] [data-baseweb="base-input"] input,
        section[data-testid="stSidebar"] [data-baseweb="input"] input {
            color:#0b1f3a !important; font-weight:700 !important; }
        div[role="listbox"] div, div[role="option"] { color:#0b1f3a !important; background:#ffffff !important; }
        .sv-topbar {
            background:#ffffff; border:2px solid #0f4b8f; border-radius:14px;
            padding:0.8rem 1rem; margin-bottom:0.7rem;
            display:flex; justify-content:space-between; align-items:center; }
        .sv-logo { font-size:3rem; font-weight:900; letter-spacing:-0.5px; line-height:1; }
        .sv-safe  { color:#ef7b10; }
        .sv-vision { color:#0a3f82; }
        .sv-chip {
            background:#edf5ff; border:2px solid #0f4b8f; border-radius:12px;
            padding:0.45rem 0.8rem; color:#10233f; font-size:1.05rem; font-weight:700;
            box-shadow:0 3px 10px rgba(6,39,82,.18); }
        .sv-card {
            background:#ffffff; border:2px solid #0f4b8f; border-radius:14px;
            padding:0.85rem 1rem; box-shadow:0 4px 12px rgba(6,39,82,.2); color:#10233f; }
        .sv-banner {
            background:linear-gradient(90deg,#ebfff0 0%,#dcffe9 100%);
            border:2px solid #2a9c4d; border-radius:12px; color:#0e3a1d;
            padding:0.7rem 1rem; margin-bottom:0.65rem; font-size:1.05rem; font-weight:700; }
        </style>
        """,
        unsafe_allow_html=True,
    )
