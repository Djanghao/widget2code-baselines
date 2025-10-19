#!/usr/bin/env python3
"""Rerun tasks where response.content is null (API returned empty response)."""
import argparse
import concurrent.futures as futures
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import os

try:
    import batch_infer
except Exception as e:
    print(f"Failed to import batch_infer: {e}", file=sys.stderr)
    raise

try:
    from provider_hub import LLM, ChatMessage, prepare_image_content
except Exception as e:
    print(f"Failed to import provider_hub: {e}", file=sys.stderr)
    raise


def find_source_image(image_dir: Path) -> Optional[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    for p in image_dir.iterdir():
        if p.is_file() and p.stem == "source" and p.suffix.lower() in exts:
            return p
    for p in image_dir.iterdir():
        if p.is_file() and p.suffix.lower() in exts:
            return p
    return None


def has_null_content(meta_file: Path) -> bool:
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if "response" not in meta:
            return False
        resp = meta["response"]
        if resp is None:
            return False
        return resp.get("content") is None
    except Exception:
        return False


def collect_null_content_tasks(run_dir: Path) -> Tuple[dict, List[Tuple[Path, str, str, Path]]]:
    run_meta_file = run_dir / "run.meta.json"
    if not run_meta_file.exists():
        raise FileNotFoundError(f"run.meta.json not found in {run_dir}")
    run_meta = json.loads(run_meta_file.read_text(encoding="utf-8"))

    tasks: List[Tuple[Path, str, str, Path]] = []

    for image_dir in sorted([p for p in run_dir.iterdir() if p.is_dir()]):
        for category_dir in sorted([p for p in image_dir.iterdir() if p.is_dir()]):
            category = category_dir.name
            for meta_file in sorted(category_dir.glob("*.meta.json")):
                if has_null_content(meta_file):
                    base_name = meta_file.name.replace(".meta.json", "")
                    tasks.append((image_dir, category, base_name, meta_file))

    return run_meta, tasks


def rerun_single_task(
    image_dir: Path,
    category: str,
    base_name: str,
    meta_file: Path,
    run_meta: dict
) -> Tuple[str, bool, Optional[str]]:
    task_id = f"{image_dir.name}/{category}/{base_name}"

    source_image = find_source_image(image_dir)
    if not source_image:
        return (task_id, False, "No source image found")

    try:
        old_meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception as e:
        return (task_id, False, f"Failed to read meta.json: {e}")

    prompt_text = old_meta.get("prompt")
    if not prompt_text:
        return (task_id, False, "No prompt in meta.json")

    provider = run_meta.get("provider")
    model = run_meta.get("model", "gemini-2.5-pro")
    api_key = run_meta.get("api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")
    base_url = run_meta.get("base_url")
    temperature = run_meta.get("temperature", 0.2)
    top_p = run_meta.get("top_p", 0.9)
    max_tokens = run_meta.get("max_tokens", 1500)
    timeout = run_meta.get("timeout", 90)
    thinking = run_meta.get("thinking")

    try:
        llm = LLM(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            timeout=timeout,
            thinking=thinking,
        )

        img = prepare_image_content(str(source_image))
        messages = [ChatMessage(role="user", content=[{"type": "text", "text": prompt_text}, img])]
        resp = llm.chat(messages)

        from dataclasses import asdict
        old_meta["response"] = asdict(resp) if hasattr(resp, "__dataclass_fields__") else {"content": str(resp)}
        meta_file.write_text(json.dumps(old_meta, ensure_ascii=False, indent=2), encoding="utf-8")

        raw = resp.content if hasattr(resp, "content") else str(resp)

        if not raw:
            return (task_id, False, "Response content still empty")

        code = batch_infer.extract_code(raw)
        ext = batch_infer.decide_extension(code)
        expected_ext = ".html" if category.startswith("html") else ".jsx"
        file_ext = ext if ext in (".html", ".jsx") else expected_ext
        out_file = meta_file.parent / f"{base_name}{file_ext}"
        out_file.write_text(code, encoding="utf-8")

        return (task_id, True, None)

    except Exception as e:
        old_meta["error"] = str(e)
        meta_file.write_text(json.dumps(old_meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return (task_id, False, f"Exception: {e}")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Rerun tasks where response.content is null")
    p.add_argument("--run-dir", required=True, help="Run directory to check")
    p.add_argument("--threads", type=int, default=4, help="Number of parallel workers")
    p.add_argument("--dry-run", action="store_true", help="Only list tasks, don't run")
    args = p.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Run directory not found: {run_dir}", file=sys.stderr)
        return 2

    print(f"Scanning {run_dir} for null content tasks...")
    run_meta, tasks = collect_null_content_tasks(run_dir)

    if not tasks:
        print("No tasks with null content found.")
        return 0

    print(f"\nFound {len(tasks)} tasks with null content:")
    for image_dir, category, base_name, meta_file in tasks:
        print(f"  - {image_dir.name}/{category}/{base_name}")

    if args.dry_run:
        print("\n[Dry run mode - not executing]")
        return 0

    print(f"\nRerunning {len(tasks)} tasks with {args.threads} workers...\n")

    success_count = 0
    failure_count = 0

    with futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        future_map = {
            executor.submit(rerun_single_task, img_dir, cat, bn, mf, run_meta): (img_dir, cat, bn)
            for img_dir, cat, bn, mf in tasks
        }

        for future in futures.as_completed(future_map):
            task_id, success, error = future.result()
            if success:
                print(f"✓ {task_id}")
                success_count += 1
            else:
                print(f"✗ {task_id}: {error}")
                failure_count += 1

    print(f"\n{'='*80}")
    print(f"Results: {success_count} succeeded, {failure_count} failed")
    print(f"{'='*80}\n")

    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
