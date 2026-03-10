"""
ui/pages/live_detection.py
==========================
Live webcam PPE detection page.
Uses streamlit-webrtc for in-browser video streaming and a background
inference thread to keep the UI responsive.
"""

import threading
import time

import av
import streamlit as st
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer

from alerts.email_alert import send_alert
from alerts.video_alert import autoplay_video
from alerts.voice_alert import speak
from database.db import fetch_incidents, log_incident
from detection.ppe_logic import (
    build_incident_totals,
    compute_person_ppe_stats,
    draw_boxes,
    get_missing_ppe_messages,
    parse_predictions,
)
from detection.roboflow import detect_ppe
from ui.sidebar import SidebarConfig
from utils.charts import ppe_pie_chart
from utils.snapshot import save_snapshot

# Shared state written by the background thread, read by the Streamlit fragment.
_SHARED_LOCK = threading.Lock()
_SHARED: dict = {"total": 0, "safe": 0, "unsafe": 0, "missing": [], "updated_at": 0.0}


def _get_demo_names(unsafe_count: int, cfg: SidebarConfig) -> list[str]:
    if not cfg.demo_name_alerts_enabled:
        return []
    people = list(cfg.demo_active_people or [])
    n = max(1, min(len(people), max(1, int(unsafe_count))))
    return people[:n]


def render(cfg: SidebarConfig) -> None:
    st.markdown(
        "<div class='sv-banner'>🟢 Webcam PPE monitoring is active. Roboflow API connected.</div>",
        unsafe_allow_html=True,
    )

    if not cfg.can_operate_live:
        st.warning("Live feed access is available for Supervisor/Admin.")
        return

    detect_every_n = st.slider("Detect every N frames", 1, 15, 2, 1)
    min_interval   = st.slider("Minimum detect interval (seconds)", 0.2, 3.0, 0.4, 0.1)

    lc, rc = st.columns([2.35, 1], gap="medium")

    # ------------------------------------------------------------------
    # WebRTC video processor
    # ------------------------------------------------------------------
    class PPEProcessor:
        def __init__(self):
            self.frame_count  = 0
            self.last_preds   = []
            self.latest_stats = {"total": 0, "safe": 0, "unsafe": 0}
            self.last_incident_ts = 0.0
            self.last_email_ts    = 0.0
            self.last_detect_ts   = 0.0
            self.lock             = threading.Lock()
            self._latest_frame    = None
            self._stop            = threading.Event()
            threading.Thread(target=self._worker, daemon=True).start()

        def _worker(self):
            while not self._stop.is_set():
                frame = None
                with self.lock:
                    if self._latest_frame is not None:
                        frame = self._latest_frame.copy()
                        self._latest_frame = None

                if frame is None or (time.time() - self.last_detect_ts) < float(min_interval):
                    time.sleep(0.01)
                    continue

                self.last_detect_ts = time.time()
                try:
                    raw = detect_ppe(
                        frame,
                        api_key=cfg.api_key,
                        model_endpoint=cfg.model_endpoint,
                        confidence_threshold=cfg.confidence_threshold,
                        overlap_threshold=cfg.overlap_threshold,
                        enhance=cfg.enhance_frame,
                        jpeg_quality=55,
                        timeout=4,
                    )
                except Exception:
                    raw = None

                if raw and "predictions" in raw:
                    _, preds = parse_predictions(
                        frame.copy(), raw,
                        confidence_threshold=cfg.confidence_threshold,
                        helmet_threshold=cfg.helmet_threshold,
                        vest_threshold=cfg.vest_threshold,
                        goggles_threshold=cfg.goggles_threshold,
                        person_threshold=cfg.person_threshold,
                        no_ppe_threshold=cfg.no_ppe_threshold,
                        selected_classes=cfg.selected_classes,
                    )
                    total, safe, unsafe, _ = compute_person_ppe_stats(preds)
                    missing = get_missing_ppe_messages(preds)

                    with self.lock:
                        self.last_preds   = preds
                        self.latest_stats = {"total": total, "safe": safe, "unsafe": unsafe}
                    with _SHARED_LOCK:
                        _SHARED.update({"total": total, "safe": safe, "unsafe": unsafe,
                                        "missing": missing, "updated_at": time.time()})

                    log_t, log_s, log_u = build_incident_totals(total, safe, unsafe, preds)
                    now   = time.time()
                    names = _get_demo_names(log_u, cfg)

                    if (log_u > 0 or (log_t > 0 and preds)) and (now - self.last_incident_ts) >= cfg.email_cooldown:
                        snap = save_snapshot(draw_boxes(frame.copy(), preds), "live_cctv") if log_u > 0 else ""
                        log_incident("live_cctv", log_t, log_s, log_u,
                                     {"pred_count": len(preds), "missing": missing,
                                      "recognized_names": names, "snapshot_path": snap})
                        self.last_incident_ts = now

                    if log_u > 0 and (now - self.last_email_ts) >= cfg.email_cooldown:
                        snap = save_snapshot(draw_boxes(frame.copy(), preds), "live_cctv")
                        send_alert(
                            subject="SafeVision Alert: Unsafe PPE detected",
                            body=(
                                f"Source: live_cctv\n"
                                f"Total persons: {log_t}\nUnsafe: {log_u}\nSafe: {log_s}\n"
                                f"Missing PPE: {', '.join(missing) or 'N/A'}\n"
                                f"Persons (demo): {', '.join(names) or 'Unknown'}\n"
                                f"Snapshot: {'Attached' if snap else 'Not available'}"
                            ),
                            attachment_paths=[snap] if snap else [],
                            enabled=cfg.email_alert_enabled,
                        )
                        self.last_email_ts = now
                else:
                    with _SHARED_LOCK:
                        stale = time.time() - float(_SHARED.get("updated_at", 0))
                    if stale > 2.5:
                        with self.lock:
                            self.last_preds   = []
                            self.latest_stats = {"total": 0, "safe": 0, "unsafe": 0}
                        with _SHARED_LOCK:
                            _SHARED.update({"total": 0, "safe": 0, "unsafe": 0, "missing": []})

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            self.frame_count += 1
            if self.frame_count % detect_every_n == 0:
                with self.lock:
                    self._latest_frame = img.copy()
            with self.lock:
                preds = list(self.last_preds)
            if preds:
                img = draw_boxes(img, preds)
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        def __del__(self):
            self._stop.set()

    # ------------------------------------------------------------------
    # Streamlit layout
    # ------------------------------------------------------------------
    with lc:
        st.subheader("Live Detection")
        ctx = webrtc_streamer(
            key="ppe-live-cctv",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=PPEProcessor,
            media_stream_constraints={"video": True, "audio": False},
            rtc_configuration=RTCConfiguration(
                {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
            ),
            async_processing=True,
        )

    metrics_ph = st.empty()
    with rc:
        pie_ph     = st.empty()
        history_ph = st.empty()
    alert_ph = st.empty()

    @st.fragment(run_every="0.5s")
    def _refresh():
        # Pull stats from processor if available, else shared state
        stats = {}
        if ctx and ctx.video_processor:
            try:
                with ctx.video_processor.lock:
                    stats = dict(ctx.video_processor.latest_stats)
            except Exception:
                pass
        if not stats:
            with _SHARED_LOCK:
                stats = dict(_SHARED)

        # Voice alert (manual trigger)
        if (
            cfg.voice_alert_enabled
            and st.session_state.get("voice_alert_nonce", 0)
               > st.session_state.get("voice_alert_last_handled_nonce", 0)
        ):
            speak(["Wear ur PPE"])
            st.session_state.voice_alert_last_handled_nonce = st.session_state.voice_alert_nonce

        unsafe_now = int(stats.get("unsafe", 0))
        now_ts     = time.time()

        if unsafe_now >= 2:
            if cfg.voice_alert_enabled and cfg.auto_voice_on_unsafe:
                if (now_ts - float(st.session_state.get("last_auto_voice_ts", 0))) >= cfg.auto_voice_cooldown:
                    speak(["Wear ur PPE"])
                    st.session_state.last_auto_voice_ts = now_ts
            if cfg.auto_video_on_unsafe:
                if (now_ts - float(st.session_state.get("last_auto_video_ts", 0))) >= cfg.auto_video_cooldown:
                    st.session_state.safety_video_nonce = st.session_state.get("safety_video_nonce", 0) + 1
                    st.session_state.last_auto_video_ts = now_ts

        with metrics_ph.container():
            k1, k2, k3 = st.columns(3)
            with k1:
                st.markdown("<div class='sv-card'><b>Total Persons</b></div>", unsafe_allow_html=True)
                st.metric("", int(stats.get("total", 0)))
            with k2:
                st.markdown("<div class='sv-card'><b>Safe</b></div>", unsafe_allow_html=True)
                st.metric("", int(stats.get("safe", 0)))
            with k3:
                st.markdown("<div class='sv-card'><b>Unsafe</b></div>", unsafe_allow_html=True)
                st.metric("", int(stats.get("unsafe", 0)))

        with pie_ph.container():
            st.subheader("PPE Compliance")
            st.pyplot(ppe_pie_chart(stats.get("safe", 0), stats.get("unsafe", 0)), clear_figure=True)

        with history_ph.container():
            st.subheader("Incident History")
            df = fetch_incidents(limit=8)
            if df.empty:
                st.info("No incidents yet.")
            else:
                st.dataframe(df[["ts", "unsafe_count"]], use_container_width=True, hide_index=True)

        with alert_ph.container():
            if stats.get("unsafe", 0) > 0:
                st.warning(f"ALERT: {stats.get('unsafe')} unsafe person(s) detected.")

        if (
            cfg.auto_video_on_unsafe
            and st.session_state.get("safety_video_nonce", 0)
               > st.session_state.get("safety_video_last_handled_nonce", 0)
        ):
            st.info("Safety training video triggered due to unsafe detection.")
            autoplay_video(cfg.safety_video_url)
            st.session_state.safety_video_last_handled_nonce = st.session_state.safety_video_nonce

    _refresh()
