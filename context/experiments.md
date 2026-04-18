# Experiment Pipeline

Three steps: **Infer → Render → Evaluate**.

---

## 1. Infer

```bash
python scripts/batch_infer.py \
  --images-dir <path-to-images> \
  --experiment <run-name> \
  --model <model-id> \
  --include "<prompt-glob>" \
  --threads 10 \
  [--size]
```

| Flag | Description |
|---|---|
| `--images-dir` | Input images directory |
| `--experiment` | Run name suffix |
| `--model` | Model id from `MODEL_REGISTRY` |
| `--include` | Glob under `prompts/`, e.g. `"html-refined/1-minimal.md"` |
| `--threads` | Concurrent workers (typical: 10) |
| `--size` | Append image size to prompt (optional) |
| `--aspect-ratio` | Append aspect ratio to prompt (optional) |

Other flags (`--temperature`, `--top-p`, `--max-tokens`, `--timeout`, `--api-key`, `--base-url`, etc.) use sensible defaults; run `--help` if needed.

Output: `results/<timestamp>-<run-name>/`.

---

## 2. Render

```bash
# HTML → PNG
node viewer/renderer/bin/render-html-batch.mjs results/<run-dir> [-j N]

# JSX → PNG
node viewer/renderer/bin/render-jsx-batch.mjs  results/<run-dir> [-j N]
```

- `<run-dir>` is the positional results directory.
- `-j / --jobs N` sets browser concurrency (default: cpu_count).
- Re-running skips files that already have a `.png` — rerun to retry browser timeouts.

---

## 3. Evaluate

**Before launching**, pick a free GPU:

```bash
nvidia-smi --query-gpu=index,memory.free --format=csv,noheader
```

Then:

```bash
CUDA_VISIBLE_DEVICES=<gpu-id> widget2code-bench \
  --gt_dir <path-to-gt> \
  --pred_dir results/<run-dir> \
  --pred_name "<category>/1-minimal.png" \
  --cuda --workers 10
```

| Flag | Description |
|---|---|
| `--gt_dir` | GT directory (flat files with 4-digit IDs) |
| `--pred_dir` | Prediction directory (subfolders with 4-digit IDs) |
| `--pred_name` | Prediction filename inside each subfolder |
| `--cuda` | Enable GPU |
| `--workers` | Parallel threads (typical: 10) |

### Concurrency (80GB GPU)

- `--workers 10` → 2–3 concurrent evals per GPU (recommended)
- `--workers 20` → 2 concurrent evals per GPU

### Output

- Per-image: `<pred_subfolder>/evaluation.json`
- Aggregate: `<pred_dir>/.analysis/metrics_stats.json`, `metrics.xlsx`
- Summary: `<pred_dir>/evaluation.xlsx`

All metrics higher-is-better except `lp` (LPIPS, lower-is-better).
