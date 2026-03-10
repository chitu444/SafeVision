"""
utils/logo.py
=============
Logo discovery (file → base-64 data-URI) and Streamlit render helpers.
"""

import base64

import streamlit as st

from config.settings import CORNER_LOGO_URL, LOGO_CANDIDATE_FILES


def resolve_logo_src() -> str:
    """
    Return a URL or base-64 data-URI for the corner logo.

    Priority:
      1. ``CORNER_LOGO_URL`` env var (if non-empty)
      2. First existing file in ``LOGO_CANDIDATE_FILES``
      3. Empty string (caller should render a fallback emoji)
    """
    if CORNER_LOGO_URL.strip():
        return CORNER_LOGO_URL.strip()

    for path in LOGO_CANDIDATE_FILES:
        try:
            with open(path, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        except (FileNotFoundError, OSError):
            continue

    return ""


def render_corner_logo() -> None:
    """Inject the corner logo (or fallback eye emoji) as fixed-position HTML."""
    src = resolve_logo_src()
    if src:
        st.markdown(
            f'<div style="position:fixed;top:8px;left:12px;z-index:9999;">'
            f'<img src="{src}" alt="logo" style="height:86px;width:86px;object-fit:contain;"/>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="position:fixed;top:14px;left:18px;z-index:9999;">'
            '<div style="height:72px;width:72px;border:4px solid #26a643;border-radius:10px;'
            'display:flex;align-items:center;justify-content:center;background:#ffffff;'
            'font-size:40px;box-shadow:0 4px 12px rgba(0,0,0,0.18);">👁️</div></div>',
            unsafe_allow_html=True,
        )
