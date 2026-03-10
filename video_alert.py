"""
alerts/video_alert.py
=====================
Renders an auto-playing YouTube safety-training video inside the
Streamlit app using an iframe embed.
"""

from urllib.parse import parse_qs, urlparse

import streamlit.components.v1 as components


def _to_embed_url(url: str) -> str:
    """Convert any YouTube watch / share / shorts URL to an embed URL."""
    raw = (url or "").strip()
    if not raw:
        return ""

    # Already an embed URL
    if "youtube.com/embed/" in raw:
        base = raw.split("?")[0]
        return f"{base}?autoplay=1&mute=1&controls=1&rel=0"

    parsed   = urlparse(raw)
    host     = (parsed.netloc or "").lower()
    video_id = ""

    if "youtu.be" in host:
        video_id = parsed.path.lstrip("/").split("/")[0]
    elif "youtube.com" in host:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/shorts/")[-1].split("/")[0]
        elif parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/embed/")[-1].split("/")[0]

    return (
        f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1&controls=1&rel=0"
        if video_id else raw
    )


def autoplay_video(video_url: str) -> None:
    """Render an auto-playing, muted YouTube embed inside the current Streamlit column."""
    embed_url = _to_embed_url(video_url)
    if not embed_url:
        return
    components.html(
        f"""
        <div style="border:2px solid #0f4b8f; border-radius:12px; overflow:hidden; background:#fff;">
          <iframe
              width="100%" height="315"
              src="{embed_url}"
              title="Safety Training Video"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowfullscreen
          ></iframe>
        </div>
        """,
        height=330,
    )
