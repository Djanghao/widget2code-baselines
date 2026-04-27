#!/usr/bin/env python3
"""Strategy 2 (PIL bilinear resize) — take Strategy-1 natural-size PNGs and
resize them to the GT image dimensions using PIL bilinear.

For each *-s1.png under <run-dir>, finds the matching gt_NNNN.png in <gt-dir>,
resizes the prediction to the GT size, and writes <basename>-s2.png next to it.

Usage:
  python render_s2_pil_resize.py <run-dir> --gt-dir <gt-dir>
                                 [-j N] [--in-suffix s1] [--out-suffix s2]
                                 [--filter bilinear|lanczos|bicubic|area]

Notes:
  - Skips outputs that already exist (idempotent).
  - --filter area  uses cv2.INTER_AREA  (matches widget2code-bench's internal
    resize_to_match), the rest are PIL filters.  Default = bilinear.
"""
from __future__ import annotations
import argparse, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image
import numpy as np

PIL_FILTERS = {
    "bilinear": Image.BILINEAR,
    "bicubic":  Image.BICUBIC,
    "lanczos":  Image.LANCZOS,
}
IMAGE_ID_RE = re.compile(r"image_(\d{4,})|gt_(\d{4,})")


def find_gt(gt_dir: Path, sample_id: str) -> Path | None:
    p = gt_dir / f"gt_{sample_id}.png"
    return p if p.exists() else None


def sample_id_for(src: Path) -> str | None:
    for part in src.parts:
        m = IMAGE_ID_RE.match(part)
        if m:
            return m.group(1) or m.group(2)
    return None


def resize_one(src: Path, dst: Path, gt_size: tuple[int, int], filt: str) -> str:
    if dst.exists():
        return "skip"
    im = Image.open(src).convert("RGBA")
    if filt == "area":
        import cv2
        arr = np.array(im)
        out = cv2.resize(arr, gt_size, interpolation=cv2.INTER_AREA)
        Image.fromarray(out).save(dst)
    else:
        im2 = im.resize(gt_size, PIL_FILTERS[filt])
        im2.save(dst)
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--gt-dir", required=True)
    ap.add_argument("-j", "--jobs", type=int, default=16)
    ap.add_argument("--in-suffix", default="s1")
    ap.add_argument("--out-suffix", default="s2")
    ap.add_argument("--filter", choices=list(PIL_FILTERS) + ["area"], default="bilinear")
    args = ap.parse_args()

    run_dir = Path(args.run_dir).resolve()
    gt_dir  = Path(args.gt_dir).resolve()
    in_pat  = re.compile(rf"-{re.escape(args.in_suffix)}\.png$")

    sources = []
    for src in run_dir.rglob(f"*-{args.in_suffix}.png"):
        # skip anything inside a dot-prefixed dir (.analysis-*, .git, etc.)
        if any(p.startswith(".") for p in src.relative_to(run_dir).parts[:-1]):
            continue
        if not in_pat.search(src.name):
            continue
        sample = sample_id_for(src)
        if not sample:
            continue
        gt = find_gt(gt_dir, sample)
        if not gt:
            continue
        dst = src.with_name(in_pat.sub(f"-{args.out_suffix}.png", src.name))
        sources.append((src, dst, gt, sample))

    if not sources:
        print(f"[s2-pil] no inputs found under {run_dir} matching *-{args.in_suffix}.png with GT", file=sys.stderr)
        return

    print(f"[s2-pil] inputs={len(sources)} jobs={args.jobs} filter={args.filter}")

    ok = fail = skip = 0
    futures = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for src, dst, gt, _ in sources:
            with Image.open(gt) as g:
                gtsz = g.size
            futures[ex.submit(resize_one, src, dst, gtsz, args.filter)] = (src, dst)
        done = 0
        for fut in as_completed(futures):
            src, dst = futures[fut]
            try:
                r = fut.result()
                if r == "skip": skip += 1
                else:           ok += 1
            except Exception as e:
                fail += 1
                print(f"FAIL {src}: {e}", file=sys.stderr)
            done += 1
            if done % 200 == 0 or done == len(sources):
                print(f"[s2-pil] [{done}/{len(sources)}] ok={ok} skip={skip} fail={fail}")

    print(f"[s2-pil] Done: ok={ok} skip={skip} fail={fail}")


if __name__ == "__main__":
    main()
