"""
alerts/voice_alert.py
=====================
Two-channel voice alerting:
  1. macOS ``say`` command (desktop deployments).
  2. Browser Web Speech API injected via streamlit.components (may be
     blocked by browser autoplay policies on first load).
"""

import platform
import subprocess

import streamlit.components.v1 as components


def speak(messages: list[str]) -> None:
    """
    Announce each message in *messages* via TTS.

    On macOS the system ``say`` binary is used so the audio plays even
    when the browser tab is not focused.  The browser-side fallback runs
    in parallel for cross-platform deployments.
    """
    text = ". ".join(messages).strip()
    if not text:
        return

    # macOS local TTS
    if platform.system() == "Darwin":
        try:
            subprocess.Popen(["say", text])
        except Exception:
            pass

    # Browser TTS (cross-platform fallback)
    safe_text = text.replace("\\", "\\\\").replace("'", "\\'")
    components.html(
        f"""
        <script>
          try {{
            const synth = window.speechSynthesis;
            if (synth) {{
              synth.cancel();
              const u = new SpeechSynthesisUtterance('{safe_text}');
              u.rate = 1.0; u.pitch = 1.0; u.volume = 1.0;
              synth.speak(u);
            }}
          }} catch (e) {{}}
        </script>
        """,
        height=0,
        width=0,
    )
