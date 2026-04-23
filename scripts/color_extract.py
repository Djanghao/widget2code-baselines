"""
K-means color extraction for prompt injection.

Adapted from widget2code/libs/python/generator/perception/color/color_picker.py
(self-contained to avoid cross-repo dependency).
"""
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np


def _rgb_to_hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def top_colors_kmeans(
    image_path: str,
    k: int = 10,
    n: int | None = None,
    max_pixels: int = 200_000,
    attempts: int = 3,
) -> List[Tuple[str, float]]:
    if n is None:
        n = k

    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Could not open image: {image_path}")

    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        rgb = img.reshape(-1, 3)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
        alpha = img[:, :, 3]
        mask = alpha > 0
        if not np.any(mask):
            raise ValueError("Image is fully transparent.")
        rgb = img[:, :, :3][mask]
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rgb = img.reshape(-1, 3)

    total_pixels = rgb.shape[0]
    if total_pixels > max_pixels:
        idx = np.random.choice(total_pixels, size=max_pixels, replace=False)
        sample = rgb[idx].astype(np.float32)
    else:
        sample = rgb.astype(np.float32)

    Z = sample.reshape((-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    flags = cv2.KMEANS_PP_CENTERS
    _, _, centers = cv2.kmeans(Z, k, None, criteria, attempts, flags)
    centers = centers.astype(np.uint8)

    pix = rgb.astype(np.int32)
    centers_int = centers.astype(np.int32)
    diffs = pix[:, None, :] - centers_int[None, :, :]
    dists = np.sum(diffs * diffs, axis=2)
    assigned = np.argmin(dists, axis=1)

    unique_centers, counts = np.unique(assigned, return_counts=True)
    center_counts = [
        (tuple(centers[i]), int(c)) for i, c in zip(unique_centers, counts)
    ]
    center_counts.sort(key=lambda x: x[1], reverse=True)

    results: List[Tuple[str, float]] = []
    for i in range(min(n, len(center_counts))):
        center_color, cnt = center_counts[i]
        results.append((_rgb_to_hex(center_color), float(cnt) / total_pixels * 100.0))
    return results


def format_palette(colors: List[Tuple[str, float]]) -> str:
    """Format (hex, pct) list as markdown lines."""
    if not colors:
        return ""
    return "\n".join(f"- `{hx}` ({pct:.1f}%)" for hx, pct in colors)


def build_palette_text(image_path: Path, k: int = 10) -> str:
    """Extract palette from image and return formatted markdown block."""
    colors = top_colors_kmeans(str(image_path), k=k, n=k)
    return format_palette(colors)
