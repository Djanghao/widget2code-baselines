#!/usr/bin/env python3
"""Retry failed inferences in-place for an existing run_dir.

Scans run_dir for image subdirs where a category folder's meta.json shows an
error or where the output file (1-minimal.html/.jsx) is missing. Re-invokes
the inference for just those cases, writing results into the same location.
"""
import argparse
import concurrent.futures as futures
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from batch_infer import (  # type: ignore
    resolve_model_config,
    run_one,
    collect_prompts,
    log_line,
)


def find_failed(run_dir: Path, prompts_root: Path) -> list[tuple[Path, str, Path, str]]:
    """Return list of (image_path, category, prompt_file, prompt_text)."""
    run_meta = json.loads((run_dir / "run.meta.json").read_text())
    images_dir = Path(run_meta["images_dir"])
    includes = run_meta.get("include")
    excludes = run_meta.get("exclude")

    prompts = collect_prompts(prompts_root, includes, excludes)

    failed = []
    for img_dir in sorted(run_dir.iterdir()):
        if not img_dir.is_dir() or not img_dir.name.startswith("image_"):
            continue
        image_id = img_dir.name
        src = images_dir / f"{image_id}.png"
        if not src.exists():
            continue
        for category, prompt_file, prompt_text in prompts:
            out_cat = img_dir / category
            base = prompt_file.stem
            meta_p = out_cat / f"{base}.meta.json"
            html_p = out_cat / f"{base}.html"
            jsx_p = out_cat / f"{base}.jsx"
            has_output = html_p.exists() or jsx_p.exists()
            if has_output:
                continue
            if not meta_p.exists():
                continue
            try:
                meta = json.loads(meta_p.read_text())
            except Exception:
                continue
            err = meta.get("error")
            resp = meta.get("response")
            if err or resp is None:
                failed.append((src, category, prompt_file, prompt_text))
    return failed


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True)
    p.add_argument("--prompts-root", default=str(Path("prompts").resolve()))
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--max-tokens", type=int, default=4000)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--top-p", type=float, default=0.9)
    args = p.parse_args()

    run_dir = Path(args.run_dir).resolve()
    prompts_root = Path(args.prompts_root).resolve()
    run_meta = json.loads((run_dir / "run.meta.json").read_text())
    model = run_meta["model"]
    size_flag = run_meta.get("size", False)
    aspect_ratio_flag = run_meta.get("aspect_ratio", False)
    stop_sequences = run_meta.get("stop_sequences")

    api_keys, base_url = resolve_model_config(model)
    failed = find_failed(run_dir, prompts_root)
    total = len(failed)
    print(f"Found {total} failed items in {run_dir}")
    if total == 0:
        return 0

    ok = fail = 0
    log_line(run_dir, "RETRY START", f"count={total}")
    with futures.ThreadPoolExecutor(max_workers=args.threads) as pool:
        tasks = []
        for src, category, prompt_file, prompt_text in failed:
            image_id = src.stem
            out_dir = run_dir / image_id
            tasks.append(pool.submit(
                run_one,
                src, category, prompt_file, prompt_text, out_dir,
                model, api_keys, base_url,
                args.temperature, args.top_p, args.max_tokens, args.timeout,
                size_flag, aspect_ratio_flag, stop_sequences,
            ))
        for i, t in enumerate(futures.as_completed(tasks), start=1):
            out_path, preview, err = t.result()
            if err:
                fail += 1
                print(f"[{i}/{total}] FAIL {out_path}: {err}")
                log_line(run_dir, "RETRY FAIL", f"path={out_path} error={err}")
            else:
                ok += 1
                print(f"[{i}/{total}] OK   {out_path}")
                log_line(run_dir, "RETRY OK", f"path={out_path}")
    log_line(run_dir, "RETRY DONE", f"ok={ok} fail={fail}")
    print(f"Done. ok={ok} fail={fail}")


if __name__ == "__main__":
    raise SystemExit(main())
