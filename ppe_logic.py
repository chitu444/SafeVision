"""
detection/ppe_logic.py
======================
All PPE-specific business logic:
  * class-name predicates (is_person, is_unsafe, …)
  * bounding-box clustering / person-count estimation
  * per-person safety stats
  * drawing helpers
  * missing-PPE message generation
  * incident-count normalisation
"""

from typing import Optional
import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Class-name predicates
# ---------------------------------------------------------------------------

def is_person_like(cls: str) -> bool:
    c = cls.lower()
    return any(k in c for k in ["person", "worker", "human", "man", "woman", "employee", "staff"])


def is_unsafe(cls: str) -> bool:
    c = cls.lower().replace("-", "_")
    return (
        c.startswith("no_")
        or "without" in c
        or "no helmet" in c
        or "no vest" in c
        or "no jacket" in c
        or "no goggle" in c
    )


def is_ppe_item(cls: str) -> bool:
    c = cls.lower()
    return any(k in c for k in ["helmet", "vest", "jacket", "goggle", "glasses", "ppe"])


def is_goggle_like(cls: str) -> bool:
    c = cls.lower()
    return any(k in c for k in ["goggle", "goggles", "google", "glass"])


def is_person_proxy(cls: str) -> bool:
    """True for any class that implies a human is present (person OR no-PPE marker)."""
    c = cls.lower()
    return is_person_like(c) or is_unsafe(c)


def get_box_color(cls: str) -> tuple:
    c = cls.lower()
    if "no_" in c or "without" in c or c.startswith("no "):
        return (0, 0, 255)       # red  → unsafe
    if "person" in c:
        return (255, 200, 0)     # yellow → person
    return (0, 255, 0)           # green → PPE item


# ---------------------------------------------------------------------------
# Clustering helpers
# ---------------------------------------------------------------------------

def cluster_person_proxies(proxy_preds: list) -> list:
    """
    Group person / no-PPE detections into per-person clusters using
    centre-distance + proportional overlap.  Stricter than
    ``estimate_people_from_boxes`` to avoid merging nearby different people.
    """
    clusters: list = []
    for p in proxy_preds:
        x1, y1, x2, y2 = p["x1"], p["y1"], p["x2"], p["y2"]
        w1, h1 = max(1, x2 - x1), max(1, y2 - y1)
        c1x, c1y = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        placed = False
        for c in clusters:
            bx1, by1, bx2, by2 = c["box"]
            w2, h2 = max(1, bx2 - bx1), max(1, by2 - by1)
            c2x, c2y = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
            if (
                abs(c1x - c2x) <= max(w1, w2) * 0.55
                and abs(c1y - c2y) <= max(h1, h2) * 0.75
            ):
                c["box"] = (min(x1, bx1), min(y1, by1), max(x2, bx2), max(y2, by2))
                c["items"].append(p)
                placed = True
                break
        if not placed:
            clusters.append({"box": (x1, y1, x2, y2), "items": [p]})
    return clusters


def estimate_people_from_boxes(preds_list: list) -> list:
    """
    Looser clustering that merges PPE / no-PPE items belonging to the same
    person even when no explicit person box is present.
    Uses horizontal overlap + vertical proximity + centre distance.
    """
    clusters: list = []
    for p in preds_list:
        x1, y1, x2, y2 = p["x1"], p["y1"], p["x2"], p["y2"]
        if x2 <= x1 or y2 <= y1:
            continue
        w1, h1 = (x2 - x1), (y2 - y1)
        cx1, cy1 = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        placed = False
        for c in clusters:
            bx1, by1, bx2, by2 = c["box"]
            w2, h2 = (bx2 - bx1), (by2 - by1)
            cx2, cy2 = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
            ix1, ix2 = max(x1, bx1), min(x2, bx2)
            horiz_overlap = max(0, ix2 - ix1) / float(max(1.0, min(w1, w2)))
            if (
                (horiz_overlap >= 0.15 and abs(cy1 - cy2) <= max(h1, h2) * 2.8)
                or abs(cx1 - cx2) <= max(w1, w2) * 1.35
            ):
                c["box"] = (min(x1, bx1), min(y1, by1), max(x2, bx2), max(y2, by2))
                c["items"].append(p)
                placed = True
                break
        if not placed:
            clusters.append({"box": (x1, y1, x2, y2), "items": [p]})
    return clusters


# ---------------------------------------------------------------------------
# PPE stats
# ---------------------------------------------------------------------------

def compute_person_ppe_stats(preds_list: list) -> tuple[int, int, int, list]:
    """
    Derive (total, safe, unsafe, per_person_details) from a flat prediction list.

    Falls back to clustering when no explicit person boxes are present.
    Returns ``(total, safe, unsafe, per_person_list)``.
    """
    persons = [p for p in preds_list if is_person_like(p["class"])]
    helmets = [p for p in preds_list if "helmet" in p["class"].lower()]
    vests   = [p for p in preds_list if "vest"   in p["class"].lower() or "jacket" in p["class"].lower()]

    per_person = []
    for person in persons:
        x1, y1, x2, y2 = person["x1"], person["y1"], person["x2"], person["y2"]
        has_helmet = any(x1 <= (h["x1"]+h["x2"])/2 <= x2 and y1 <= (h["y1"]+h["y2"])/2 <= y2 for h in helmets)
        has_vest   = any(x1 <= (v["x1"]+v["x2"])/2 <= x2 and y1 <= (v["y1"]+v["y2"])/2 <= y2 for v in vests)
        per_person.append({"person_box": (x1, y1, x2, y2), "has_helmet": has_helmet, "has_jacket": has_vest})

    total  = len(per_person)
    safe   = sum(1 for p in per_person if p["has_helmet"] and p["has_jacket"])
    unsafe = total - safe

    # Fallback when model emits no explicit person boxes
    if total == 0 and preds_list:
        proxy_preds = [p for p in preds_list if is_person_proxy(p["class"])]
        clusters = cluster_person_proxies(proxy_preds) if proxy_preds else estimate_people_from_boxes(preds_list)
        if clusters:
            total  = len(clusters)
            unsafe = sum(1 for c in clusters if any(is_unsafe(i["class"]) for i in c["items"]))
            safe   = max(total - unsafe, 0)
        else:
            unsafe_n = sum(1 for p in preds_list if is_unsafe(p["class"]))
            ppe_n    = sum(1 for p in preds_list if is_ppe_item(p["class"]) and not is_unsafe(p["class"]))
            est_total = max(unsafe_n, ppe_n)
            if est_total > 0:
                total  = est_total
                unsafe = min(unsafe_n, total)
                safe   = max(total - unsafe, 0)

    return total, safe, unsafe, per_person


def build_incident_totals(
    total: int, safe: int, unsafe: int, preds_list: list
) -> tuple[int, int, int]:
    """
    Ensure incident history records real unsafe detections even when the
    person-count inference is uncertain.  Falls back to clustering / box counts.
    """
    t, s, u = int(total), int(safe), int(unsafe)
    if t <= 0 and preds_list:
        proxy_preds = [p for p in preds_list if is_person_proxy(p["class"])]
        clusters = cluster_person_proxies(proxy_preds) if proxy_preds else estimate_people_from_boxes(preds_list)
        if clusters:
            t = len(clusters)
            u = sum(1 for c in clusters if any(is_unsafe(i["class"]) for i in c["items"]))
            s = max(t - u, 0)
        else:
            unsafe_boxes = sum(1 for p in preds_list if is_unsafe(p["class"]))
            ppe_boxes    = sum(1 for p in preds_list if is_ppe_item(p["class"]))
            t = max(unsafe_boxes, ppe_boxes, 1)
            u = max(u, unsafe_boxes)
            s = max(t - u, 0)
    return t, s, u


def get_missing_ppe_messages(preds_list: list) -> list[str]:
    """Return human-readable messages for each missing PPE category detected."""
    classes = [str(p.get("class", "")).lower() for p in preds_list]
    missing: list[str] = []
    if any("no_helmet" in c or "without helmet" in c or "no helmet" in c for c in classes):
        missing.append("Wear helmet")
    if any("no_vest" in c or "no jacket" in c or "without vest" in c or "without jacket" in c or "no-vest" in c for c in classes):
        missing.append("Wear safety vest")
    if any("no_goggle" in c or "without goggles" in c or "no goggles" in c or "no-goggles" in c for c in classes):
        missing.append("Wear goggles")
    return missing


# ---------------------------------------------------------------------------
# Prediction parsing + drawing
# ---------------------------------------------------------------------------

def parse_predictions(
    frame: np.ndarray,
    predictions: dict,
    *,
    confidence_threshold: float,
    helmet_threshold: float,
    vest_threshold: float,
    goggles_threshold: float,
    person_threshold: float,
    no_ppe_threshold: float,
    selected_classes: Optional[list] = None,
) -> tuple[np.ndarray, list]:
    """
    Filter raw Roboflow predictions by per-class thresholds, draw bounding
    boxes on *frame*, and return ``(annotated_frame, preds_list)``.
    """
    preds_list: list = []
    if not predictions or "predictions" not in predictions:
        return frame, preds_list

    for pred in predictions["predictions"]:
        cls  = str(pred.get("class", "unknown"))
        conf = float(pred.get("confidence", 0.0))
        cls_l = cls.lower()

        # Per-class confidence gating
        if "person" in cls_l:
            threshold = person_threshold
        elif "helmet" in cls_l and not is_unsafe(cls_l):
            threshold = helmet_threshold
        elif ("vest" in cls_l or "jacket" in cls_l) and not is_unsafe(cls_l):
            threshold = vest_threshold
        elif is_goggle_like(cls_l) and not is_unsafe(cls_l):
            threshold = goggles_threshold
        elif is_unsafe(cls_l):
            threshold = no_ppe_threshold
        else:
            threshold = confidence_threshold

        if conf < threshold:
            continue
        if selected_classes and cls not in selected_classes:
            continue

        x_c, y_c = float(pred.get("x", 0)), float(pred.get("y", 0))
        w, h     = float(pred.get("width", 0)), float(pred.get("height", 0))
        if w <= 0 or h <= 0:
            continue

        x1 = max(0, int(x_c - w / 2))
        y1 = max(0, int(y_c - h / 2))
        x2 = min(frame.shape[1] - 1, int(x_c + w / 2))
        y2 = min(frame.shape[0] - 1, int(y_c + h / 2))
        preds_list.append({"class": cls, "confidence": conf, "x1": x1, "y1": y1, "x2": x2, "y2": y2})

    frame = draw_boxes(frame, preds_list)
    return frame, preds_list


def draw_boxes(frame: np.ndarray, preds_list: list) -> np.ndarray:
    """Draw labelled bounding boxes on *frame* in-place and return it."""
    for p in preds_list:
        color = get_box_color(p["class"])
        cv2.rectangle(frame, (p["x1"], p["y1"]), (p["x2"], p["y2"]), color, 2)
        label = f'{p["class"]} {float(p.get("confidence", 0.0)):.2f}'
        cv2.putText(
            frame, label,
            (p["x1"], max(20, p["y1"] - 8)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA,
        )
    return frame
