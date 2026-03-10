"""
detection/roboflow.py
=====================
Thin wrapper around the Roboflow inference REST API.
Handles frame pre-processing (CLAHE + sharpening), JPEG encoding,
and the HTTP request/response cycle.

All threshold / config values are passed in as arguments so this module
has no Streamlit state dependency and can be called from background threads.
"""

from io import BytesIO
from typing import Optional

import cv2
import numpy as np
import requests
from PIL import Image

from config.settings import FRAME_WIDTH, FRAME_HEIGHT


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_ppe(
    frame: np.ndarray,
    *,
    api_key: str,
    model_endpoint: str,
    confidence_threshold: float = 0.45,
    overlap_threshold: float = 0.30,
    enhance: bool = True,
    jpeg_quality: int = 70,
    timeout: int = 10,
) -> Optional[dict]:
    """
    Send *frame* to the Roboflow model and return the parsed JSON response,
    or ``None`` if the request fails or detection is disabled.

    Parameters
    ----------
    frame:               BGR numpy array (any size — resized internally).
    api_key:             Roboflow API key.
    model_endpoint:      Full Roboflow inference URL.
    confidence_threshold: Minimum confidence sent to the API (0–1 scale).
    overlap_threshold:   NMS overlap threshold sent to the API (0–1 scale).
    enhance:             Apply CLAHE + sharpening before encoding.
    jpeg_quality:        JPEG compression quality (lower → smaller payload).
    timeout:             HTTP request timeout in seconds.
    """
    try:
        img = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        if enhance:
            img = _enhance_frame(img)

        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        buf = BytesIO()
        pil_img.save(buf, format="JPEG", quality=jpeg_quality)
        buf.seek(0)

        params = {
            "api_key":    api_key,
            "confidence": int(max(0, min(100, round(confidence_threshold * 100)))),
            "overlap":    int(max(0, min(100, round(overlap_threshold * 100)))),
        }
        response = requests.post(
            model_endpoint,
            params=params,
            files={"file": buf.getvalue()},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    except Exception as exc:
        # Callers decide whether to surface this error to the UI.
        raise RuntimeError(f"Roboflow detection failed: {exc}") from exc


def test_connection(api_key: str, model_endpoint: str, timeout: int = 10) -> tuple[bool, str]:
    """
    Send a blank frame to verify credentials and reachability.

    Returns ``(True, success_message)`` or ``(False, error_message)``.
    """
    try:
        blank = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        detect_ppe(
            blank,
            api_key=api_key,
            model_endpoint=model_endpoint,
            enhance=False,
            timeout=timeout,
        )
        return True, "Connected to Roboflow successfully."
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _enhance_frame(img: np.ndarray) -> np.ndarray:
    """Apply mild CLAHE equalisation and an unsharp-mask sharpening pass."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    img = cv2.cvtColor(cv2.merge((l_ch, a_ch, b_ch)), cv2.COLOR_LAB2BGR)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    return cv2.filter2D(img, -1, kernel)
