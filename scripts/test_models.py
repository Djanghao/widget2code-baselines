#!/usr/bin/env python3
"""Smoke test: try every individual API key for every configured model."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from batch_infer import MODEL_REGISTRY, resolve_model_config
from openai import OpenAI


def test_single_key(model: str, base_url: str, api_key: str, timeout: int = 30):
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        temperature=0.0,
        top_p=1.0,
        max_tokens=20,
    )
    return resp.choices[0].message.content if resp.choices else "(empty)"


def main():
    models = list(MODEL_REGISTRY.keys())
    print(f"Testing {len(models)} models, all keys individually...\n")

    for model in models:
        try:
            api_keys, base_url = resolve_model_config(model)
        except ValueError as e:
            print(f"[SKIP] {model}")
            print(f"       not configured: {e}\n")
            continue

        print(f"[{model}]  base_url={base_url}  keys={len(api_keys)}")
        for i, key in enumerate(api_keys):
            label = f"{key[:12]}...{key[-4:]}"
            try:
                content = test_single_key(model, base_url, key)
                print(f"  key[{i}] {label}  =>  OK  response: {content!r:.60}")
            except Exception as e:
                print(f"  key[{i}] {label}  =>  FAIL  {type(e).__name__}: {str(e)[:120]}")
        print()


if __name__ == "__main__":
    main()
