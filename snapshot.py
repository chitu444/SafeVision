"""
utils/snapshot.py
=================
Saves annotated video frames as JPEG snapshots for incident records
and email attachments.
"""

import os
import time

import cv2
import numpy as np

from config.settings import INCIDENT_SNAPSHOT_DIR


def save_snapshot(frame: np.ndarray, source: str) -> str:
    """
    Write *frame* to ``INCIDENT_SNAPSHOT_DIR`` and return the full path.
    Returns an empty string if writing fails.

    The filename is ``{source}_{YYYYMMDD_HHMMSS}_{millis:03d}.jpg``.
    """
    try:
        os.makedirs(INCIDENT_SNAPSHOT_DIR, exist_ok=True)
        ts     = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        millis = int((time.time() % 1) * 1000)
        path   = os.path.join(INCIDENT_SNAPSHOT_DIR, f"{source}_{ts}_{millis:03d}.jpg")
        ok, enc = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ok:
            return ""
        with open(path, "wb") as fh:
            fh.write(enc.tobytes())
        return path
    except Exception:
        return ""
