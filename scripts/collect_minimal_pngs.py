#!/usr/bin/env python3
"""Collect per-image PNGs into a flat numbered folder structure."""
import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Tuple


def collect_sources(run_dir: Path, category: str, base_name: str) -> List[Tuple[Path, Path]]:
    sources: List[Tuple[Path, Path]] = []
    for image_dir in sorted([p for p in run_dir.iterdir() if p.is_dir()]):
        png = image_dir / category / f"{base_name}.png"
        if png.exists():
            sources.append((image_dir, png))
    return sources


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Collect <category>/<base>.png from a run into .results/image_XXXX/output.png"
    )
    p.add_argument("--run-dir", required=True, help="Run directory under results/")
    p.add_argument("--category", default="html-no-size", help="Category folder name (default: html-no-size)")
    p.add_argument("--base-name", default="1-minimal", help="Base file name without extension (default: 1-minimal)")
    p.add_argument(
        "--output-root",
        default=None,
        help="Output root (default: <run-dir>/.results)",
    )
    args = p.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Run directory not found: {run_dir}", file=sys.stderr)
        return 2

    output_root = Path(args.output_root) if args.output_root else (run_dir / ".results")
    output_root.mkdir(parents=True, exist_ok=True)

    sources = collect_sources(run_dir, args.category, args.base_name)
    if not sources:
        print("No PNG files found to collect.", file=sys.stderr)
        return 2

    width = 4
    for i, (_, png) in enumerate(sources, start=1):
        out_dir = output_root / f"image_{i:0{width}d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / "output.png"
        shutil.copy2(png, dest)

    print(f"Copied {len(sources)} PNGs into {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
