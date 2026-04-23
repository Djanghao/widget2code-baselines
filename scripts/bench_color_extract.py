"""
Bench-style color extraction — mirrors widget_quality/style.py logic.

Produces a structured palette for prompt injection that combines:
  1. K-means dominant hex colors (for direct use in code)
  2. Polarity (light-mode vs dark-mode + contrast strength) — matches compute_polarity_consistency
  3. Saturation profile (low/mid/high bins) — matches compute_vibrancy_consistency
  4. Hue spread summary — matches compute_palette_distance
"""
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from skimage.color import rgb2hsv, rgb2gray

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from color_extract import top_colors_kmeans


def _load_rgb(image_path: str) -> np.ndarray:
    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(image_path)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
        alpha = img[:, :, 3] / 255.0
        # composite onto white for hue/saturation stability where alpha < 1
        rgb = img[:, :, :3].astype(np.float32)
        rgb = rgb * alpha[:, :, None] + 255.0 * (1 - alpha[:, :, None])
        img = np.clip(rgb, 0, 255).astype(np.uint8)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img / 255.0  # [0, 1]


def compute_polarity_summary(rgb_img: np.ndarray, q: float = 0.1) -> dict:
    """Same logic as compute_polarity_consistency, but returns a descriptive dict."""
    L = rgb2gray(rgb_img)
    flat = np.sort(L.ravel())
    k = max(1, int(q * flat.size))
    bg = float(np.median(flat))
    dark = float(np.mean(flat[:k]))
    bright = float(np.mean(flat[-k:]))
    if abs(bg - dark) >= abs(bg - bright):
        fg = dark
    else:
        fg = bright
    contrast = bg - fg   # >0 ⇒ light bg / dark fg
    strength = abs(contrast)
    polarity = "light_on_dark" if contrast < 0 else "dark_on_light"
    label = "dark-themed (light text on dark background)" if polarity == "light_on_dark" else "light-themed (dark text on light background)"
    return {
        "bg_luminance": bg,
        "fg_luminance": fg,
        "contrast_strength": strength,
        "polarity": polarity,
        "label": label,
    }


def compute_saturation_profile(rgb_img: np.ndarray) -> dict:
    """HSV S histogram split into low/mid/high buckets."""
    hsv = rgb2hsv(rgb_img)
    s = hsv[..., 1].ravel()
    low = float((s < 0.2).mean()) * 100
    mid = float(((s >= 0.2) & (s < 0.6)).mean()) * 100
    high = float((s >= 0.6).mean()) * 100
    if high > 40:
        profile = "highly-saturated / vivid"
    elif mid > 40 or high > 20:
        profile = "mixed saturation (neutral + accents)"
    else:
        profile = "desaturated / mostly neutral"
    return {"low_pct": low, "mid_pct": mid, "high_pct": high, "profile": profile}


def compute_hue_spread(rgb_img: np.ndarray, bins: int = 36) -> dict:
    """Active hue bins count (only pixels with meaningful saturation)."""
    hsv = rgb2hsv(rgb_img)
    h = hsv[..., 0].ravel()
    s = hsv[..., 1].ravel()
    # only count pixels with sat > 0.15 to ignore grays
    h_colored = h[s > 0.15]
    if len(h_colored) == 0:
        return {"active_bins": 0, "summary": "essentially grayscale"}
    hist, _ = np.histogram(h_colored, bins=bins, range=(0, 1), density=True)
    # normalize and count bins > 1% density
    hist_norm = hist / (hist.sum() + 1e-6)
    active = int((hist_norm > 0.02).sum())
    if active <= 2:
        summary = "monochromatic / single hue family"
    elif active <= 5:
        summary = "few hues (2-3 accent colors)"
    else:
        summary = "multi-hue / colorful"
    return {"active_bins": active, "total_bins": bins, "summary": summary}


def build_bench_palette_text(image_path: Path, k: int = 10) -> str:
    """Return a structured markdown palette block mirroring eval semantics."""
    rgb = _load_rgb(str(image_path))
    hex_colors = top_colors_kmeans(str(image_path), k=k, n=k)
    pol = compute_polarity_summary(rgb)
    sat = compute_saturation_profile(rgb)
    hue = compute_hue_spread(rgb)

    lines = []
    lines.append(f"**Theme polarity**: {pol['label']}")
    lines.append(f"  (background luminance ≈ {pol['bg_luminance']:.2f}, foreground ≈ {pol['fg_luminance']:.2f}, contrast strength ≈ {pol['contrast_strength']:.2f})")
    lines.append("")
    lines.append(f"**Saturation profile**: {sat['profile']}")
    lines.append(f"  (low-sat pixels: {sat['low_pct']:.0f}%, mid-sat: {sat['mid_pct']:.0f}%, high-sat: {sat['high_pct']:.0f}%)")
    lines.append("")
    lines.append(f"**Hue variety**: {hue['summary']}")
    lines.append(f"  ({hue['active_bins']}/{hue['total_bins']} hue bins active among saturated pixels)")
    lines.append("")
    lines.append("**Dominant colors (k-means, sorted by coverage)**:")
    for hx, pct in hex_colors:
        lines.append(f"- `{hx}` ({pct:.1f}%)")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) < 2:
        print("Usage: python bench_color_extract.py <image>")
        _sys.exit(1)
    print(build_bench_palette_text(Path(_sys.argv[1])))
