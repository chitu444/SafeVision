"""
ui/pages/upload.py
==================
Static image upload and PPE analysis page.
"""

import time

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from alerts.email_alert import send_alert
from database.db import log_incident
from detection.ppe_logic import (
    build_incident_totals,
    compute_person_ppe_stats,
    get_missing_ppe_messages,
    parse_predictions,
)
from detection.roboflow import detect_ppe
from ui.sidebar import SidebarConfig
from utils.charts import ppe_pie_chart
from utils.snapshot import save_snapshot


def render(cfg: SidebarConfig) -> None:
    st.subheader("Upload Image for Analysis")
    uploaded = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

    if not uploaded:
        return

    frame = cv2.cvtColor(np.array(Image.open(uploaded).convert("RGB")), cv2.COLOR_RGB2BGR)

    try:
        raw = detect_ppe(
            frame,
            api_key=cfg.api_key,
            model_endpoint=cfg.model_endpoint,
            confidence_threshold=cfg.confidence_threshold,
            overlap_threshold=cfg.overlap_threshold,
            enhance=cfg.enhance_frame,
        )
    except Exception as exc:
        st.error(f"Detection failed: {exc}")
        return

    if not raw:
        st.warning("No detections found.")
        return

    annotated, preds = parse_predictions(
        frame.copy(), raw,
        confidence_threshold=cfg.confidence_threshold,
        helmet_threshold=cfg.helmet_threshold,
        vest_threshold=cfg.vest_threshold,
        goggles_threshold=cfg.goggles_threshold,
        person_threshold=cfg.person_threshold,
        no_ppe_threshold=cfg.no_ppe_threshold,
        selected_classes=cfg.selected_classes,
    )

    st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), use_container_width=True)

    total, safe, unsafe, _ = compute_person_ppe_stats(preds)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Persons", total)
    c2.metric("Safe", safe)
    c3.metric("Unsafe", unsafe)
    st.pyplot(ppe_pie_chart(safe, unsafe))

    # Incident logging
    log_t, log_s, log_u = build_incident_totals(total, safe, unsafe, preds)
    now     = time.time()
    cooldown = float(cfg.email_cooldown)

    last_log  = st.session_state.get("last_incident_log_ts", 0.0)
    last_mail = st.session_state.get("last_email_alert_ts", 0.0)

    can_log  = (log_u > 0 or (log_t > 0 and preds)) and (now - last_log) >= cooldown
    can_mail = log_u > 0 and (now - last_mail) >= cooldown

    snap = ""
    names = _demo_names(log_u, cfg)
    if (can_log or can_mail) and log_u > 0:
        snap = save_snapshot(annotated.copy(), "image_upload")

    if can_log:
        log_incident(
            "image_upload", log_t, log_s, log_u,
            {"pred_count": len(preds), "missing": get_missing_ppe_messages(preds),
             "recognized_names": names, "snapshot_path": snap},
        )
        st.session_state.last_incident_log_ts = now

    missing = get_missing_ppe_messages(preds)
    if can_mail:
        ok, err = send_alert(
            subject="SafeVision Alert: Unsafe PPE detected",
            body=(
                f"Source: image_upload\n"
                f"Total persons: {log_t}\nUnsafe: {log_u}\nSafe: {log_s}\n"
                f"Missing PPE: {', '.join(missing) or 'N/A'}\n"
                f"Persons (demo): {', '.join(names) or 'Unknown'}\n"
                f"Snapshot: {'Attached' if snap else 'Not available'}"
            ),
            attachment_paths=[snap] if snap else [],
            enabled=cfg.email_alert_enabled,
        )
        if ok:
            st.session_state.last_email_alert_ts = now


def _demo_names(unsafe_count: int, cfg: SidebarConfig) -> list[str]:
    if not cfg.demo_name_alerts_enabled:
        return []
    people = list(cfg.demo_active_people or [])
    n = max(1, min(len(people), max(1, int(unsafe_count))))
    return people[:n]
