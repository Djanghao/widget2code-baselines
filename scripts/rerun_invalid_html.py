#!/usr/bin/env python3
"""Rerun tasks that produced code but are missing PNG renders."""
import argparse
import concurrent.futures as futures
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Import helpers from sibling script.
sys.path.append(str(Path(__file__).resolve().parent))
try:
    import rerun_missing  # type: ignore
except Exception as e:
    print(f"Failed to import rerun_missing: {e}", file=sys.stderr)
    raise


def resolve_output_path(category_dir: Path, base_name: str) -> Optional[Path]:
    for ext in (".html", ".jsx"):
        p = category_dir / f"{base_name}{ext}"
        if p.exists():
            return p
    return None


def read_prompt_from_meta(meta: dict) -> Optional[str]:
    prompt = meta.get("prompt")
    if prompt:
        return str(prompt)
    prompt_file = meta.get("prompt_file")
    if not prompt_file:
        return None
    try:
        return Path(prompt_file).read_text(encoding="utf-8").strip()
    except Exception:
        return None


def infer_file_type(category: str, meta: dict) -> str:
    file_type = (meta.get("file_type") or "").lower()
    if file_type in ("html", "jsx"):
        return file_type
    return "html" if category.startswith("html") else "jsx"


def collect_invalid_html_tasks(
    run_dir: Path,
) -> Tuple[dict, List[Tuple[Path, str, str, str, str, Path]]]:
    """Return (run_meta, tasks) where tasks are:
    (image_dir, category, base_name, file_type, prompt_text, source_image)
    """
    run_meta_file = run_dir / "run.meta.json"
    if not run_meta_file.exists():
        raise FileNotFoundError(f"run.meta.json not found in {run_dir}")
    run_meta = json.loads(run_meta_file.read_text(encoding="utf-8"))

    tasks: List[Tuple[Path, str, str, str, str, Path]] = []

    for image_dir in sorted([p for p in run_dir.iterdir() if p.is_dir()]):
        source = rerun_missing.find_source_image(image_dir)
        if not source:
            print(f"WARN: No source image found in {image_dir}", file=sys.stderr)
            continue

        for category_dir in sorted([p for p in image_dir.iterdir() if p.is_dir()]):
            category = category_dir.name
            for meta_file in sorted(category_dir.glob("*.meta.json")):
                base_name = meta_file.name[: -len(".meta.json")]
                output = resolve_output_path(category_dir, base_name)
                if output is None:
                    continue
                png_path = output.with_suffix(".png")
                if png_path.exists():
                    continue

                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                except Exception:
                    print(f"WARN: Failed to read {meta_file}", file=sys.stderr)
                    continue

                prompt = read_prompt_from_meta(meta)
                if not prompt:
                    print(f"WARN: Missing prompt in {meta_file}", file=sys.stderr)
                    continue

                file_type = infer_file_type(category, meta)
                tasks.append((image_dir, category, base_name, file_type, prompt, source))

    return run_meta, tasks


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Rerun tasks missing PNG renders (invalid_html)")
    p.add_argument("--run-dir", required=True, help="Run directory to check")
    p.add_argument("--threads", type=int, default=4, help="Number of parallel workers")
    p.add_argument("--limit", type=int, default=None, help="Limit number of tasks to rerun")
    p.add_argument("--dry-run", action="store_true", help="Only list tasks, don't run")
    p.add_argument("--model", default=None, help="Model override")
    p.add_argument("--api-key", dest="api_key", default=None, help="API key override")
    p.add_argument("--base-url", dest="base_url", default=None, help="Base URL override")
    p.add_argument("--temperature", type=float, default=None, help="Temperature override")
    p.add_argument("--top-p", type=float, default=None, help="Top-p override")
    p.add_argument("--max-tokens", type=int, default=None, help="Max tokens override")
    p.add_argument("--timeout", type=int, default=None, help="Timeout override (seconds)")
    args = p.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Run directory not found: {run_dir}", file=sys.stderr)
        return 2

    run_meta, tasks = collect_invalid_html_tasks(run_dir)
    print(f"Found {len(tasks)} invalid_html tasks (missing PNG).")

    if args.limit is not None and len(tasks) > args.limit:
        tasks = tasks[: args.limit]
        print(f"Limiting to first {args.limit} tasks.")

    if args.dry_run:
        for image_dir, category, base_name, _, _, _ in tasks:
            print(f"- {image_dir.name}/{category}/{base_name}")
        return 0

    model = args.model if args.model is not None else run_meta.get("model")
    base_url_override = args.base_url if args.base_url is not None else run_meta.get("base_url")
    temperature = args.temperature if args.temperature is not None else float(run_meta.get("temperature", 0.2))
    top_p = args.top_p if args.top_p is not None else float(run_meta.get("top_p", 0.9))
    max_tokens = args.max_tokens if args.max_tokens is not None else int(run_meta.get("max_tokens", 1500))
    timeout = args.timeout if args.timeout is not None else int(run_meta.get("timeout", 90))
    stop_sequences = run_meta.get("stop_sequences")
    if isinstance(stop_sequences, str):
        stop_sequences = [stop_sequences]

    from batch_infer import resolve_model_config
    api_keys, base_url = resolve_model_config(model, args.api_key, base_url_override)

    print(f"Model={model} Base URL={base_url} Keys={len(api_keys)}")
    print(f"temperature={temperature} top_p={top_p} max_tokens={max_tokens} timeout={timeout}")

    ok = 0
    fail = 0

    with futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        future_map = {
            executor.submit(
                rerun_missing.run_one_snapshot,
                image_path=source,
                category=category,
                base_name=base_name,
                file_type=file_type,
                prompt_text=prompt_text,
                out_dir=image_dir,
                model=model,
                api_keys=api_keys,
                base_url=base_url,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                timeout=timeout,
                stop_sequences=stop_sequences,
            ): (image_dir, category, base_name)
            for image_dir, category, base_name, file_type, prompt_text, source in tasks
        }

        for i, future in enumerate(futures.as_completed(future_map), start=1):
            out_path, _, err = future.result()
            if err:
                fail += 1
                print(f"[{i}/{len(future_map)}] FAIL {out_path}: {err}")
            else:
                ok += 1
                print(f"[{i}/{len(future_map)}] OK   {out_path}")

    print(f"Done. ok={ok} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
