"""
OCR text extraction for prompt injection (easyocr-backed).

Returns detected text boxes with coordinates **normalized to image dimensions**
so the model can rescale to its own chosen canvas width/height.
"""
import os
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "7")

from pathlib import Path
from typing import List, Tuple
import threading

import easyocr
from PIL import Image

_reader_lock = threading.Lock()
_reader = None


def _get_reader():
    global _reader
    with _reader_lock:
        if _reader is None:
            _reader = easyocr.Reader(["en"], gpu=True, verbose=False)
    return _reader


def extract_text_boxes(image_path: Path) -> Tuple[List[Tuple[str, float, float, float, float, float]], int, int]:
    """
    Returns (boxes, image_width, image_height).
    Each box: (text, x_frac, y_frac, w_frac, h_frac, confidence).
    Fractions are relative to the image's (width, height).
    Filters low-confidence (<0.3) and tiny boxes.
    """
    img_w, img_h = Image.open(image_path).size
    reader = _get_reader()
    results = reader.readtext(str(image_path), detail=1, paragraph=False)
    out = []
    for box, text, conf in results:
        if not text or conf < 0.3:
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        x_px = float(min(xs)); y_px = float(min(ys))
        w_px = float(max(xs) - min(xs)); h_px = float(max(ys) - min(ys))
        if h_px < 8 or w_px < 8:
            continue
        out.append((
            text,
            x_px / img_w, y_px / img_h,
            w_px / img_w, h_px / img_h,
            float(conf),
        ))
    return out, img_w, img_h


def format_ocr(boxes, img_w: int, img_h: int) -> str:
    """
    Format OCR boxes as a markdown list with fractional coordinates.
    The model multiplies fractions by its own canvas W/H to get concrete px.
    """
    if not boxes:
        return "(no text detected in image)"
    lines = []
    for text, xf, yf, wf, hf, _conf in boxes:
        safe = text.replace("`", "'")
        lines.append(
            f'- `"{safe}"` at ({xf*100:.1f}%, {yf*100:.1f}%) of widget, '
            f'font-height ≈ {hf*100:.1f}% of widget height'
        )
    return "\n".join(lines)


def build_ocr_text(image_path: Path) -> str:
    boxes, img_w, img_h = extract_text_boxes(image_path)
    return format_ocr(boxes, img_w, img_h)
