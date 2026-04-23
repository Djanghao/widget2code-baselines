#!/usr/bin/env python3
import argparse
import base64
import concurrent.futures as futures
import datetime as dt
from zoneinfo import ZoneInfo
import json
import os
import re
import sys
import threading
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from color_extract import build_palette_text
from bench_color_extract import build_bench_palette_text


# ---------------------------------------------------------------------------
# Model registry: maps model name -> (BASE_URL env var, API_KEY env var)
# CLI --base-url / --api-key always take precedence over env vars.
# ---------------------------------------------------------------------------
MODEL_REGISTRY = {
    "gpt-4o":                         ("GPT_4O_BASE_URL",          "GPT_4O_API_KEY"),
    "gpt-5.2":                        ("GPT_5_2_BASE_URL",         "GPT_5_2_API_KEY"),
    "claude-opus-4-5-20251101":       ("CLAUDE_OPUS_4_5_BASE_URL", "CLAUDE_OPUS_4_5_API_KEY"),
    "gemini-3-pro-preview":           ("GEMINI_3_0_PRO_BASE_URL",  "GEMINI_3_0_PRO_API_KEY"),
    "doubao-seed-1-8-251228":         ("DOUBAO_1_8_BASE_URL",      "DOUBAO_1_8_API_KEY"),
    "doubao-seed-2-0-pro-260215-32k": ("DOUBAO_2_0_BASE_URL",      "DOUBAO_2_0_API_KEY"),
    "qwen3-vl-plus":                  ("QWEN3_VL_PLUS_BASE_URL",   "QWEN3_VL_PLUS_API_KEY"),
    "qwen3.5-plus":                   ("QWEN3_5_PLUS_BASE_URL",    "QWEN3_5_PLUS_API_KEY"),
}


def resolve_model_config(
    model: str,
    api_key_override: Optional[str] = None,
    base_url_override: Optional[str] = None,
) -> Tuple[List[str], str]:
    """Resolve API keys and base URL for *model*.

    API keys may be comma-separated (e.g. ``sk-aaa,sk-bbb``).
    Priority: CLI flags > model-specific env vars.
    Raises ValueError if base_url or api_keys cannot be resolved.

    Returns (api_keys_list, base_url).
    """
    raw_key = api_key_override
    base_url = base_url_override

    if model in MODEL_REGISTRY:
        url_var, key_var = MODEL_REGISTRY[model]
        if not base_url:
            base_url = os.getenv(url_var)
        if not raw_key:
            raw_key = os.getenv(key_var)

    if not base_url:
        raise ValueError(
            f"No base_url for model '{model}'. "
            f"Pass --base-url or add it to MODEL_REGISTRY / .env."
        )
    if not raw_key:
        raise ValueError(
            f"No api_key for model '{model}'. "
            f"Pass --api-key or add it to MODEL_REGISTRY / .env."
        )

    api_keys = [k.strip() for k in raw_key.split(",") if k.strip()]
    if not api_keys:
        raise ValueError(
            f"No valid api_key for model '{model}' after parsing."
        )

    return api_keys, base_url


# ---------------------------------------------------------------------------
# Round-robin key rotation with fallback
# ---------------------------------------------------------------------------
_rr_counter: dict[str, int] = {}
_rr_lock = threading.Lock()


def _next_key_index(group: str, total: int) -> int:
    """Return the next round-robin index for *group* (thread-safe)."""
    with _rr_lock:
        idx = _rr_counter.get(group, 0)
        _rr_counter[group] = (idx + 1) % total
        return idx


def chat_completion_with_fallback(
    api_keys: List[str],
    base_url: str,
    model: str,
    messages: list,
    temperature: float,
    top_p: float,
    max_tokens: int,
    timeout: int,
):
    """Call chat completions, rotating through *api_keys* on failure.

    Uses round-robin to spread load across keys. If a key fails, tries the
    next one. Raises the last exception only when **all** keys have failed.
    """
    n = len(api_keys)
    start = _next_key_index(base_url, n)
    last_error: Optional[Exception] = None
    for i in range(n):
        key = api_keys[(start + i) % n]
        try:
            client = OpenAI(api_key=key, base_url=base_url, timeout=timeout)
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
        except Exception as e:
            last_error = e
            continue
    raise last_error


def prepare_image_content(image_path: str) -> dict:
    """Encode a local image as a base64 data-URL for the OpenAI vision API."""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    suffix = Path(image_path).suffix.lower().lstrip(".")
    if suffix == "jpg":
        suffix = "jpeg"
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/{suffix};base64,{data}"},
    }


def list_images(images_dir: Path) -> List[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files = []
    for p in sorted(images_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return files


def read_prompt_file(path: Path) -> Optional[str]:
    """Read prompt text from a Markdown file.

    The entire file content is used as the prompt text.
    """
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return None


def collect_prompts(prompts_root: Path, includes: Optional[List[str]], excludes: Optional[List[str]]) -> List[Tuple[str, Path, str]]:
    items: List[Tuple[str, Path, str]] = []
    for category in sorted([p for p in prompts_root.iterdir() if p.is_dir()]):
        for md in sorted(category.glob("*.md")):
            rel = md.relative_to(prompts_root)
            rel_str = str(rel)
            if includes and not any(fnmatch(rel_str, pat) for pat in includes):
                continue
            if excludes and any(fnmatch(rel_str, pat) for pat in excludes):
                continue
            prompt_text = read_prompt_file(md)
            if not prompt_text:
                continue
            items.append((category.name, md, prompt_text))
    return items


def fnmatch(s: str, pat: str) -> bool:
    if pat == "*":
        return True
    if "*" not in pat:
        return s == pat
    parts = pat.split("*")
    i = 0
    for idx, part in enumerate(parts):
        if part == "":
            continue
        j = s.find(part, i)
        if j == -1:
            return False
        if idx == 0 and not pat.startswith("*") and j != 0:
            return False
        i = j + len(part)
    if not pat.endswith("*") and not s.endswith(parts[-1]):
        return False
    return True


def extract_code(content: str) -> str:
    s = content.strip()
    fence = re.match(r"^```([a-zA-Z0-9\-\+]*)\n([\s\S]*?)\n```\s*$", s)
    if fence:
        return fence.group(2).strip()
    return s


def trim_to_stop(code: str, stop_sequences: Optional[List[str]]) -> str:
    if not code or not stop_sequences:
        return code
    earliest = None
    stop_used = None
    for seq in stop_sequences:
        if not seq:
            continue
        idx = code.find(seq)
        if idx != -1 and (earliest is None or idx < earliest):
            earliest = idx
            stop_used = seq
    if earliest is None or stop_used is None:
        return code
    return code[: earliest + len(stop_used)]


def decide_extension(code: str) -> str:
    starts = code.lstrip().lower()
    if starts.startswith("<html"):
        return ".html"
    if starts.startswith("export default function"):
        return ".jsx"
    if re.search(r"export\s+default\s+function\s+\w+\s*\(\)\s*\{", code):
        return ".jsx"
    return ".txt"


def append_log(run_dir: Path, line: str) -> None:
    log_file = run_dir / "run.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    except Exception:
        pass


def log_line(run_dir: Path, tag: str, message: str) -> None:
    ts = dt.datetime.now(ZoneInfo("America/Toronto")).strftime("%Y-%m-%d %H:%M:%S")
    append_log(run_dir, f"[{ts}] {tag:<12} | {message}")

def build_size_constraint_text(image_path: Path, size_flag: bool, aspect_ratio_flag: bool) -> tuple[str, dict]:
    if not size_flag and not aspect_ratio_flag:
        return "", {}
    img = Image.open(image_path)
    width, height = img.size
    ratio = width / height
    size_info = {"width": width, "height": height, "aspect_ratio": round(ratio, 2)}
    if size_flag and aspect_ratio_flag:
        return f"The widget must match the screenshot size ({width}\u00d7{height} px) and maintain its aspect ratio (\u2248{ratio:.2f}:1) as closely as possible.", size_info
    elif size_flag:
        return f"The widget must match the screenshot size ({width}\u00d7{height} px) as closely as possible.", size_info
    else:
        return f"The widget must maintain the screenshot's aspect ratio (\u2248{ratio:.2f}:1) as closely as possible.", size_info

def run_one(
    image_path: Path,
    category: str,
    prompt_file: Path,
    prompt_text: str,
    out_dir: Path,
    model: str,
    api_keys: List[str],
    base_url: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    timeout: int,
    size_flag: bool,
    aspect_ratio_flag: bool,
    stop_sequences: Optional[List[str]],
    inject_colors: bool = False,
    color_k: int = 10,
    inject_bench_colors: bool = False,
) -> Tuple[Path, Optional[str], Optional[str]]:
    constraint_text, size_info = build_size_constraint_text(image_path, size_flag, aspect_ratio_flag)
    if constraint_text:
        prompt_text = prompt_text + "\n" + constraint_text

    palette_text = ""
    if inject_bench_colors:
        try:
            palette_text = build_bench_palette_text(image_path, k=color_k)
        except Exception:
            palette_text = ""
        if "[COLOR_PALETTE]" in prompt_text:
            prompt_text = prompt_text.replace("[COLOR_PALETTE]", palette_text or "(no palette available)")
        elif palette_text:
            prompt_text = (
                prompt_text
                + "\n\n### Color Palette (bench-style, from eval's HSV analysis)\n"
                + palette_text
            )
    elif inject_colors:
        try:
            palette_text = build_palette_text(image_path, k=color_k)
        except Exception:
            palette_text = ""
        if "[COLOR_PALETTE]" in prompt_text:
            prompt_text = prompt_text.replace("[COLOR_PALETTE]", palette_text or "(no palette available)")
        elif palette_text:
            prompt_text = (
                prompt_text
                + "\n\n### Color Palette (from the target image, sorted by pixel coverage)\n"
                + palette_text
            )

    out_cat = out_dir / category
    out_cat.mkdir(parents=True, exist_ok=True)
    base_name = prompt_file.stem
    meta_out_file = out_cat / f"{base_name}.meta.json"
    meta_data = {
        "prompt": prompt_text,
        "category": category,
        "prompt_file": str(prompt_file),
        "size_flag": size_flag,
        "aspect_ratio_flag": aspect_ratio_flag,
        "file_type": "html" if category.startswith("html") else "jsx",
    }
    if size_info:
        meta_data["image_size"] = {"width": size_info["width"], "height": size_info["height"]}
        meta_data["aspect_ratio"] = size_info["aspect_ratio"]
    if inject_colors:
        meta_data["inject_colors"] = True
        meta_data["color_k"] = color_k
        meta_data["palette"] = palette_text
    meta_out_file.write_text(json.dumps(meta_data, ensure_ascii=False, indent=2), encoding="utf-8")

    img_content = prepare_image_content(str(image_path))
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt_text}, img_content]}]

    try:
        resp = chat_completion_with_fallback(
            api_keys, base_url, model, messages,
            temperature, top_p, max_tokens, timeout,
        )
    except Exception as e:
        meta_data["response"] = None
        meta_data["error"] = str(e)
        meta_out_file.write_text(json.dumps(meta_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return (prompt_file, None, f"ERROR: {e}")

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
    meta_out_file.write_text(json.dumps(meta_data, ensure_ascii=False, indent=2), encoding="utf-8")

    code = extract_code(content) if content else ""
    if stop_sequences and category.startswith("html"):
        code = trim_to_stop(code, stop_sequences)
    ext = decide_extension(code)
    expected_ext = ".html" if category.startswith("html") else ".jsx"
    file_ext = ext if ext in (".html", ".jsx") else expected_ext
    out_file = out_cat / f"{base_name}{file_ext}"
    out_file.write_text(code, encoding="utf-8")
    return (out_file, code[:64] if code else "", None)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Batch widget2code inference (OpenAI-compatible API)")
    p.add_argument("--images-dir", required=True, help="Directory with images")
    p.add_argument("--prompts-root", default=str(Path("prompts").resolve()), help="Prompts root directory (expects .md files)")
    p.add_argument("--results-root", default=str(Path("results").resolve()), help="Results root directory")
    p.add_argument("--experiment", required=True, help="Experiment name suffix")
    p.add_argument("--threads", type=int, default=os.cpu_count() or 4, help="Max concurrent workers")
    p.add_argument("--model", required=True, help="Model id (must be in MODEL_REGISTRY or provide --base-url/--api-key)")
    p.add_argument("--api-key", dest="api_key", default=None, help="API key override (falls back to model-specific or OPENAI_API_KEY env var)")
    p.add_argument("--base-url", dest="base_url", default=None, help="Base URL override (falls back to model-specific or OPENAI_BASE_URL env var)")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--top-p", type=float, default=0.9)
    p.add_argument("--max-tokens", type=int, default=4000)
    p.add_argument("--timeout", type=int, default=90)
    p.add_argument("--stop-seq", action="append", default=None, help="Stop sequence(s) for trimming output (HTML only)")
    p.add_argument("--include", nargs="*", help="Optional glob filters relative to prompts root, e.g. 'react/*' 'html/1-*' ")
    p.add_argument("--exclude", nargs="*", help="Optional glob filters to exclude")
    p.add_argument("--suffix", default="", help="Optional extra suffix for run directory name")
    p.add_argument("--size", action="store_true", help="Append image size constraint to prompt")
    p.add_argument("--aspect-ratio", action="store_true", help="Append aspect ratio constraint to prompt")
    p.add_argument("--inject-colors", action="store_true", help="Extract k-means color palette from image and inject into prompt")
    p.add_argument("--inject-bench-colors", action="store_true", help="Inject bench-style color info (polarity + saturation profile + hue spread + k-means hex) into prompt")
    p.add_argument("--color-k", type=int, default=10, help="Number of k-means color clusters (default 10)")
    args = p.parse_args(argv)

    images_dir = Path(args.images_dir)
    prompts_root = Path(args.prompts_root)
    results_root = Path(args.results_root)
    if not images_dir.exists():
        print(f"Images dir not found: {images_dir}", file=sys.stderr)
        return 2
    if not prompts_root.exists():
        print(f"Prompts root not found: {prompts_root}", file=sys.stderr)
        return 2
    images = list_images(images_dir)
    if not images:
        print("No images found", file=sys.stderr)
        return 2
    prompts = collect_prompts(prompts_root, args.include, args.exclude)
    if not prompts:
        print("No prompts collected", file=sys.stderr)
        return 2

    api_keys, base_url = resolve_model_config(args.model, args.api_key, args.base_url)

    ts = dt.datetime.now(ZoneInfo("America/Toronto")).strftime("%Y%m%d-%H%M%S")
    run_dir_name = f"{ts}-{args.experiment}{('-' + args.suffix) if args.suffix else ''}"
    run_dir = results_root / run_dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "experiment": args.experiment,
        "base_url": base_url,
        "model": args.model,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "timeout": args.timeout,
        "images_dir": str(images_dir),
        "prompts_root": str(prompts_root),
        "include": args.include,
        "exclude": args.exclude,
        "size": args.size,
        "aspect_ratio": args.aspect_ratio,
        "inject_colors": args.inject_colors,
        "color_k": args.color_k,
        "stop_sequences": args.stop_seq,
        "created_at": ts,
    }
    (run_dir / "run.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Log batch start
    log_line(run_dir, "BATCH START", f"model={args.model} base_url={base_url}")
    log_line(run_dir, "BATCH INFO", f"images_dir={images_dir} include={args.include} exclude={args.exclude} size={args.size} aspect_ratio={args.aspect_ratio} inject_colors={args.inject_colors} color_k={args.color_k} threads={args.threads}")

    tasks = []
    with futures.ThreadPoolExecutor(max_workers=args.threads) as pool:
        for img in images:
            image_id = img.stem
            out_dir = run_dir / image_id
            out_dir.mkdir(parents=True, exist_ok=True)
            try:
                dst = out_dir / f"source{img.suffix.lower()}"
                if not dst.exists():
                    dst.write_bytes(img.read_bytes())
            except Exception:
                pass
            for category, prompt_file, prompt_text in prompts:
                tasks.append(
                    pool.submit(
                        run_one,
                        img,
                        category,
                        prompt_file,
                        prompt_text,
                        out_dir,
                        args.model,
                        api_keys,
                        base_url,
                        args.temperature,
                        args.top_p,
                        args.max_tokens,
                        args.timeout,
                        args.size,
                        args.aspect_ratio,
                        args.stop_seq,
                        args.inject_colors,
                        args.color_k,
                        args.inject_bench_colors,
                    )
                )

        ok = 0
        fail = 0
        for i, t in enumerate(futures.as_completed(tasks), start=1):
            out_path, preview, err = t.result()
            if err:
                fail += 1
                print(f"[{i}/{len(tasks)}] FAIL {out_path}: {err}")
                log_line(run_dir, "BATCH FAIL", f"path={out_path} error={err}")
            else:
                ok += 1
                print(f"[{i}/{len(tasks)}] OK   {out_path}")
                log_line(run_dir, "BATCH OK", f"path={out_path}")

    log_line(run_dir, "BATCH DONE", f"ok={ok} fail={fail} output={run_dir}")
    print(f"Done. Succeeded: {ok}, Failed: {fail}. Output: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
