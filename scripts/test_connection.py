#!/usr/bin/env python3
"""Test connectivity for every model and every API key in MODEL_REGISTRY."""
import sys
import os
import time
import concurrent.futures as futures

sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from batch_infer import MODEL_REGISTRY, resolve_model_config
from openai import OpenAI

TIMEOUT = 90


def test_single_key(model: str, base_url: str, api_key: str):
    t0 = time.time()
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=TIMEOUT)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        temperature=0.0,
        top_p=1.0,
        max_tokens=20,
    )
    elapsed = time.time() - t0
    content = resp.choices[0].message.content if resp.choices else "(empty)"
    return content, elapsed


def main():
    models = list(MODEL_REGISTRY.keys())

    total_keys = 0
    ok_keys = 0
    fail_keys = 0
    skip_models = 0
    results = []

    print(f"{'='*70}")
    print(f"  Model Connection Test  ({len(models)} models)")
    print(f"{'='*70}\n")

    for model in models:
        try:
            api_keys, base_url = resolve_model_config(model)
        except ValueError as e:
            skip_models += 1
            results.append((model, "SKIP", str(e)))
            print(f"  SKIP  {model}")
            print(f"        {e}\n")
            continue

        print(f"  [{model}]")
        print(f"  base_url: {base_url}")
        print(f"  keys: {len(api_keys)}")

        model_ok = 0
        model_fail = 0
        for i, key in enumerate(api_keys):
            total_keys += 1
            label = f"{key[:12]}...{key[-4:]}"
            try:
                content, elapsed = test_single_key(model, base_url, key)
                ok_keys += 1
                model_ok += 1
                print(f"    [{i}] {label}  OK   {elapsed:5.1f}s  {content!r:.40}")
            except Exception as e:
                fail_keys += 1
                model_fail += 1
                err_msg = str(e)[:100]
                print(f"    [{i}] {label}  FAIL        {type(e).__name__}: {err_msg}")

        status = "ALL OK" if model_fail == 0 else f"{model_ok}/{model_ok + model_fail} OK"
        results.append((model, status, f"{model_ok} ok, {model_fail} fail"))
        print()

    # Summary
    print(f"{'='*70}")
    print(f"  Summary")
    print(f"{'='*70}")
    for model, status, detail in results:
        icon = "OK" if "OK" in status and "FAIL" not in detail else ("SKIP" if status == "SKIP" else "FAIL")
        print(f"  {icon:4s}  {model:30s}  {detail}")
    print(f"{'='*70}")
    print(f"  Total keys tested: {total_keys}  |  OK: {ok_keys}  |  FAIL: {fail_keys}  |  Models skipped: {skip_models}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
