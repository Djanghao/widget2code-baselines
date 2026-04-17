#!/usr/bin/env python3
import argparse
import concurrent.futures as futures
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import os
import datetime as dt

# Import sibling helpers from batch_infer
try:
    import batch_infer  # type: ignore
except Exception as e:
    print(f"Failed to import batch_infer: {e}", file=sys.stderr)
    raise

from batch_infer import prepare_image_content, resolve_model_config, chat_completion_with_fallback


def find_source_image(image_dir: Path) -> Optional[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    # Prefer saved copy named source.*
    for p in image_dir.iterdir():
        if p.is_file() and p.stem == "source" and p.suffix.lower() in exts:
            return p
    # Fallback: first image file in the folder
    for p in image_dir.iterdir():
        if p.is_file() and p.suffix.lower() in exts:
            return p
    return None


def code_exists(category_dir: Path, base_name: str) -> bool:
    # Accept any of these as a produced result
    for ext in (".html", ".jsx"):
        if (category_dir / f"{base_name}{ext}").exists():
            return True
    return False


def has_error_in_meta(meta_file: Path) -> bool:
    """Check if meta.json contains an error field."""
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        return "error" in meta and meta["error"] is not None
    except Exception:
        return False


def collect_missing(run_dir: Path) -> Tuple[dict, List[Tuple[Path, str, str, Optional[Path]]]]:
    """Return (run_meta, tasks) where tasks are tuples:
    (image_dir, category, base_name, meta_file_path_or_None)

    Includes tasks that need to be (re)run:
    1. Missing output files (has meta.json but no .html/.jsx)
    2. Failed tasks (has error in meta.json, even if output file exists)
    3. Never started tasks (no meta.json at all - need to infer from run.meta.json)
    """
    run_meta_file = run_dir / "run.meta.json"
    if not run_meta_file.exists():
        raise FileNotFoundError(f"run.meta.json not found in {run_dir}")
    run_meta = json.loads(run_meta_file.read_text(encoding="utf-8"))

    # Get expected prompts from run.meta.json
    prompts_root = Path(run_meta.get("prompts_root", "prompts"))
    include_patterns = run_meta.get("include")
    exclude_patterns = run_meta.get("exclude")

    # Collect expected prompt files
    expected_prompts = []
    if prompts_root.exists():
        expected_prompts = batch_infer.collect_prompts(prompts_root, include_patterns, exclude_patterns)

    tasks: List[Tuple[Path, str, str, Optional[Path]]] = []
    for image_dir in sorted([p for p in run_dir.iterdir() if p.is_dir()]):
        if image_dir.name == "run.meta.json":
            continue

        # Check all expected categories/prompts for this image
        for category, prompt_file, _ in expected_prompts:
            category_dir = image_dir / category
            base_name = prompt_file.stem
            meta_file = category_dir / f"{base_name}.meta.json" if category_dir.exists() else None

            # Case 1: meta.json doesn't exist at all (never started)
            if meta_file is None or not meta_file.exists():
                tasks.append((image_dir, category, base_name, None))
                continue

            # Case 2: has error in meta.json (failed)
            if has_error_in_meta(meta_file):
                tasks.append((image_dir, category, base_name, meta_file))
                continue

            # Case 3: missing output file (interrupted before writing output)
            if not code_exists(category_dir, base_name):
                tasks.append((image_dir, category, base_name, meta_file))
                continue

    return run_meta, tasks


def resolve_prompt_text_from_meta(meta_file: Optional[Path]) -> Optional[str]:
    """Get prompt text from meta.json if it exists, otherwise return None."""
    if meta_file is None or not meta_file.exists():
        return None
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        return meta.get("prompt")
    except Exception:
        return None


def expected_extension_from_type(file_type: str) -> str:
    t = (file_type or "").lower()
    if t == "html":
        return ".html"
    if t == "jsx":
        return ".jsx"
    # default safe fallback
    return ".html"


def run_one_snapshot(
    image_path: Path,
    category: str,
    base_name: str,
    file_type: str,
    prompt_text: str,
    out_dir: Path,
    model: str,
    api_keys: List[str],
    base_url: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    timeout: int,
    stop_sequences: Optional[List[str]],
) -> Tuple[Path, Optional[str], Optional[str]]:
    out_cat = out_dir / category
    out_cat.mkdir(parents=True, exist_ok=True)
    meta_out_file = out_cat / f"{base_name}.meta.json"

    # Load or create meta_data
    if meta_out_file.exists():
        try:
            meta_data = json.loads(meta_out_file.read_text(encoding="utf-8"))
        except Exception:
            meta_data = {}
    else:
        meta_data = {
            "prompt": prompt_text,
            "category": category,
            "file_type": file_type,
        }

    img_content = prepare_image_content(str(image_path))
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt_text}, img_content]}]

    try:
        resp = chat_completion_with_fallback(
            api_keys, base_url, model, messages,
            temperature, top_p, max_tokens, timeout,
        )
    except Exception as e:
        # Update meta.json with error
        meta_data["response"] = None
        meta_data["error"] = str(e)
        meta_out_file.write_text(json.dumps(meta_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return (out_cat / f"{base_name}{expected_extension_from_type(file_type)}", None, f"ERROR: {e}")

    content = resp.choices[0].message.content if resp.choices else None
    meta_data["response"] = {
        "content": content,
        "model": resp.model,
        "usage": {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
        } if resp.usage else None,
    }
    # Clear error field if present (from previous failed run)
    if "error" in meta_data:
        del meta_data["error"]
    meta_out_file.write_text(json.dumps(meta_data, ensure_ascii=False, indent=2), encoding="utf-8")

    code = batch_infer.extract_code(content) if content else ""
    if stop_sequences and category.startswith("html"):
        code = batch_infer.trim_to_stop(code, stop_sequences)
    expected_ext = expected_extension_from_type(file_type)
    # Strictly use meta-declared file_type for extension
    file_ext = expected_ext
    out_file = out_cat / f"{base_name}{file_ext}"
    out_file.write_text(code, encoding="utf-8")
    return (out_file, code[:64] if code else "", None)


def append_log(run_dir: Path, line: str) -> None:
    log_file = run_dir / "run.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    except Exception:
        pass


def log_line(run_dir: Path, tag: str, message: str) -> None:
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    append_log(run_dir, f"[{ts}] {tag:<12} | {message}")


def count_missing_all(run_dir: Path) -> int:
    _, tasks = collect_missing(run_dir)
    return len(tasks)


def rerun_missing(run_dir: Path, threads: int = 8, limit: Optional[int] = None, dry_run: bool = False, api_key_opt: Optional[str] = None, base_url_opt: Optional[str] = None) -> int:
    run_meta, tasks = collect_missing(run_dir)

    model = run_meta.get("model")
    base_url = run_meta.get("base_url")
    temperature = float(run_meta.get("temperature", 0.2))
    top_p = float(run_meta.get("top_p", 0.9))
    max_tokens = int(run_meta.get("max_tokens", 1500))
    timeout = int(run_meta.get("timeout", 90))
    size_flag = bool(run_meta.get("size", False))
    aspect_ratio_flag = bool(run_meta.get("aspect_ratio", False))
    stop_sequences = run_meta.get("stop_sequences")
    if isinstance(stop_sequences, str):
        stop_sequences = [stop_sequences]

    # Resolve API keys and base URL: CLI overrides > run.meta.json > env vars
    api_keys, base_url = resolve_model_config(model, api_key_opt or None, base_url_opt or base_url)

    print(f"Loaded run.meta.json from: {run_dir}")
    print(f"- Model: {model}")
    print(f"- Base URL: {base_url}  size={size_flag} aspect_ratio={aspect_ratio_flag}")
    total_missing_before = count_missing_all(run_dir)
    print(f"- Missing items detected: {len(tasks)}")

    if limit is not None and len(tasks) > limit:
        tasks = tasks[:limit]
        print(f"- Limiting to first {limit} tasks")

    if dry_run:
        for image_dir, category, base_name, meta_file in tasks:
            # read file_type for display if present
            status = "never-started"
            if meta_file and meta_file.exists():
                try:
                    md = json.loads(meta_file.read_text(encoding="utf-8"))
                    ft = md.get("file_type")
                    if has_error_in_meta(meta_file):
                        status = "failed"
                    else:
                        status = "incomplete"
                except Exception:
                    ft = None
            else:
                ft = "html" if category.startswith("html") else "jsx"
            suffix = f" ({ft}, {status})" if ft else f" ({status})"
            print(f"DRY-RUN: would run {image_dir.name}/{category}/{base_name}{suffix}")
        return 0

    # Start log
    log_line(run_dir, "RERUN START", f"model={model} base_url={base_url}")
    log_line(run_dir, "RERUN PLAN", f"missing_before={total_missing_before} scheduled={len(tasks)} threads={threads}")
    for image_dir, category, base_name, meta_file in tasks:
        status = "never-started"
        ft = None
        if meta_file and meta_file.exists():
            try:
                md = json.loads(meta_file.read_text(encoding="utf-8"))
                ft = md.get("file_type")
                if has_error_in_meta(meta_file):
                    status = "failed"
                else:
                    status = "incomplete"
            except Exception:
                pass
        else:
            ft = "html" if category.startswith("html") else "jsx"
        log_line(run_dir, "RERUN TASK", f"image={image_dir.name} category={category} name={base_name} file_type={ft} status={status}")

    # If nothing to do, record summary and return early
    if len(tasks) == 0:
        total_missing_after = count_missing_all(run_dir)
        log_line(run_dir, "RERUN DONE", f"ok=0 fail=0 missing_after={total_missing_after}")
        print("Nothing to re-run. Missing=0")
        return 0

    # Get prompts_root and patterns to reload prompts for never-started tasks
    prompts_root = Path(run_meta.get("prompts_root", "prompts"))
    include_patterns = run_meta.get("include")
    exclude_patterns = run_meta.get("exclude")

    # Load all expected prompts
    expected_prompts_dict = {}
    if prompts_root.exists():
        expected_prompts = batch_infer.collect_prompts(prompts_root, include_patterns, exclude_patterns)
        for category, prompt_file, prompt_text in expected_prompts:
            key = (category, prompt_file.stem)
            expected_prompts_dict[key] = (prompt_file, prompt_text)

    ok = 0
    fail = 0
    with futures.ThreadPoolExecutor(max_workers=max(1, threads)) as pool:
        futs = []
        for image_dir, category, base_name, meta_file in tasks:
            img_path = find_source_image(image_dir)
            if not img_path:
                print(f"WARN: No source image found in {image_dir}")
                log_line(run_dir, "RERUN SKIP", f"image={image_dir.name} category={category} name={base_name} reason=no_source_image")
                continue

            # Try to get prompt from meta.json first
            prompt_text = resolve_prompt_text_from_meta(meta_file)

            # If no meta.json or no prompt in meta, load from original prompt file
            if not prompt_text:
                key = (category, base_name)
                if key in expected_prompts_dict:
                    _, prompt_text = expected_prompts_dict[key]
                else:
                    print(f"WARN: Could not find prompt for {category}/{base_name}")
                    log_line(run_dir, "RERUN SKIP", f"image={image_dir.name} category={category} name={base_name} reason=no_prompt_found")
                    continue

            # Determine file_type
            file_type = None
            if meta_file and meta_file.exists():
                try:
                    md = json.loads(meta_file.read_text(encoding="utf-8"))
                    file_type = md.get("file_type")
                except Exception:
                    pass

            # Infer file_type from category if not found
            if not file_type:
                file_type = "html" if category.startswith("html") else "jsx"

            futs.append(
                pool.submit(
                    run_one_snapshot,
                    img_path,
                    category,
                    base_name,
                    file_type,
                    prompt_text,
                    image_dir,
                    model,
                    api_keys,
                    base_url,
                    temperature,
                    top_p,
                    max_tokens,
                    timeout,
                    stop_sequences,
                )
            )

        for i, t in enumerate(futures.as_completed(futs), start=1):
            out_path, preview, err = t.result()
            if err:
                fail += 1
                print(f"[{i}/{len(futs)}] FAIL {out_path}: {err}")
                log_line(run_dir, "RERUN FAIL", f"path={out_path} error={err}")
            else:
                ok += 1
                print(f"[{i}/{len(futs)}] OK   {out_path}")
                log_line(run_dir, "RERUN OK", f"path={out_path}")

    total_missing_after = count_missing_all(run_dir)
    log_line(run_dir, "RERUN DONE", f"ok={ok} fail={fail} missing_after={total_missing_after}")
    print(f"Re-run complete. Succeeded: {ok}, Failed: {fail}.")
    return 0 if fail == 0 else 1


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Re-run missing widget code generations for an existing run directory.")
    p.add_argument("--run-dir", required=True, help="Path to an existing run directory under results/")
    p.add_argument("--threads", type=int, default=8, help="Max concurrent workers")
    p.add_argument("--limit", type=int, default=None, help="Limit number of re-runs (for testing)")
    p.add_argument("--dry-run", action="store_true", help="Only print what would be re-run")
    p.add_argument("--api-key", dest="api_key", default=None, help="API key override")
    p.add_argument("--base-url", dest="base_url", default=None, help="Base URL override")
    args = p.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.exists() or not run_dir.is_dir():
        print(f"Run dir not found: {run_dir}", file=sys.stderr)
        return 2

    return rerun_missing(run_dir, threads=args.threads, limit=args.limit, dry_run=args.dry_run, api_key_opt=args.api_key, base_url_opt=args.base_url)


if __name__ == "__main__":
    raise SystemExit(main())
