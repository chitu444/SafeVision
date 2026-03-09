import cv2
import requests
from io import BytesIO
from PIL import Image
from config.settings import ROBoflow_API_KEY, MODEL_ENDPOINT

def detect_ppe(frame):
    img = cv2.resize(frame, (640,480))
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    buf = BytesIO()
    pil_img.save(buf, format="JPEG")
    buf.seek(0)

    response = requests.post(
        MODEL_ENDPOINT,
        params={"api_key": ROBoflow_API_KEY},
        files={"file": buf.getvalue()},
        timeout=10
    )

    return response.json()