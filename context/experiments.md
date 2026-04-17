# Experiment Pipeline: Generation -> Rendering -> Evaluation

## Prerequisites

- **Conda env**: `widget2code-bench` (has `openai`, `python-dotenv`, `Pillow`, `widget2code-bench`, `torch`, `torchvision`)
- **Node packages**: `viewer/` directory needs `npm install`. For React experiments using external libs, also install them (e.g., `npm install react-icons recharts`).
- **Playwright**: `npx playwright install chromium`
- **PyTorch CUDA**: Must match driver version. Current system has CUDA 12.9 driver; use `torch+cu126` (NOT cu130). Install with:
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
  ```
- **API keys**: Stored in `.env`, loaded by `batch_infer.py` via `python-dotenv`.
- **GT images**: `/shared/zhixiang_team/widget_research/Comparison/GT` (1000 ground-truth PNGs).
- **Source images**: `/home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000`

## Step 1: Generation (Inference)

Run `batch_infer.py` for each (prompt, size/aspect-ratio) combination.

```bash
eval "$(conda shell.bash hook)" && conda activate widget2code-bench

IMGS=/home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000

python scripts/batch_infer.py \
  --images-dir $IMGS \
  --experiment <experiment-name> \
  --threads 10 \
  --model <model-name> \
  --include "<prompt-category>/1-minimal.md" \
  [--size] [--aspect-ratio]
```

### Experiment naming convention

`<model>-test-1000-<prompt-category>-minimal[-cal-size][-cal-aspect-ratio]`

### Available prompt categories (no-size variants)

| Category | Output type | Notes |
|----------|-------------|-------|
| `html-no-size` | `.html` | Plain HTML/CSS |
| `react-no-size` | `.jsx` | React with inline CSS |
| `react-tailwind-no-size` | `.jsx` | React with Tailwind |
| `react-no-size-recharts-reacticons` | `.jsx` | React, only `react-icons` and `recharts` allowed |
| `react-tailwind-no-size-recharts-reacticons` | `.jsx` | React+Tailwind, only `react-icons` and `recharts` allowed |

### Size/aspect-ratio combinations (4 per prompt)

1. `--size --aspect-ratio` (suffix: `-cal-size-cal-aspect-ratio`)
2. `--size` (suffix: `-cal-size`)
3. `--aspect-ratio` (suffix: `-cal-aspect-ratio`)
4. (none) (no suffix beyond `-minimal`)

### Parallelism

All experiments for a model can run in parallel (they only use CPU + network). Use 10 threads per experiment.

### Verification

- Check `run.log` in each result dir: count `OK` and `ERROR` lines.
- All 1000 images should have `OK`. If any `ERROR`, use `scripts/rerun_missing.py` or `scripts/rerun_null_content.py` to retry.

## Step 2: Rendering

Convert generated HTML/JSX to PNG screenshots using Playwright.

```bash
cd /home/houston/workspace/widget-research/widget2code-baselines

# For HTML experiments:
node viewer/renderer/bin/render-html-batch.mjs results/<experiment-dir>

# For React/JSX experiments:
node viewer/renderer/bin/render-jsx-batch.mjs results/<experiment-dir>
```

### Timeout retry policy

- **Code errors** (build fail, missing `.widget`, `useContext` null, etc.): Skip. These are valid failures (model produced broken code).
- **Browser timeouts** (`Timeout XXXXms exceeded`): Must retry. Re-run the same render command; it skips files that already have a `.png`.
- Repeat until either (a) zero new timeouts, or (b) the same images keep timing out across rounds (= code causes browser hang, treat as code error).

### Parallelism

All render jobs can run in parallel. Each uses Playwright with concurrency = CPU count by default. Override with `-j N`.

### Verification

Count PNGs vs total images:
```bash
find results/<experiment-dir> -name "1-minimal.png" | wc -l
```

## Step 3: Evaluation

Use `widget2code-bench` to compare rendered PNGs against ground truth.

```bash
eval "$(conda shell.bash hook)" && conda activate widget2code-bench

CUDA_VISIBLE_DEVICES=<gpu-id> widget2code-bench \
  --gt_dir /shared/zhixiang_team/widget_research/Comparison/GT \
  --pred_dir results/<experiment-dir> \
  --pred_name "<prompt-category>/1-minimal.png" \
  --cuda \
  --workers 20
```

### GPU parallelism

Use `CUDA_VISIBLE_DEVICES` to assign each eval to a specific GPU. Available GPUs: 0-3 (80GB each). Run up to 4 evals in parallel (one per GPU). Do NOT run eval concurrently with GPU-heavy inference to avoid OOM.

### Verification

Every image with a PNG must have an `evaluation.json`:
```bash
# Must output 0
pngs=$(find results/<dir> -name "1-minimal.png" | wc -l)
evals=$(find results/<dir> -name "evaluation.json" | wc -l)
echo "missing=$((pngs - evals))"
```

### Output

- Per-image: `<image_dir>/evaluation.json`
- Aggregate: `<experiment-dir>/.analysis/metrics_stats.json` and `metrics.xlsx`

## Step 4: Collect Results

Combine all experiments' mean metrics into a single XLSX.

### Metric columns (in order)

| Group | Metrics |
|-------|---------|
| Layout | MarginAsymmetry, ContentAspectDiff, AreaRatioDiff |
| Legibility | TextJaccard, ContrastDiff, ContrastLocalDiff |
| Style | PaletteDistance, Vibrancy, PolarityConsistency |
| Perceptual | ssim, lp |
| Geometry | geo_score (display as "geometry") |

### Script

```python
import json, openpyxl
from pathlib import Path

results_root = Path("results")
metrics_config = [
    ("MarginAsymmetry", "MarginAsymmetry"),
    ("ContentAspectDiff", "ContentAspectDiff"),
    ("AreaRatioDiff", "AreaRatioDiff"),
    ("TextJaccard", "TextJaccard"),
    ("ContrastDiff", "ContrastDiff"),
    ("ContrastLocalDiff", "ContrastLocalDiff"),
    ("PaletteDistance", "PaletteDistance"),
    ("Vibrancy", "Vibrancy"),
    ("PolarityConsistency", "PolarityConsistency"),
    ("ssim", "ssim"),
    ("lp", "lp"),
    ("geo_score", "geometry"),
]

wb = openpyxl.Workbook()
ws = wb.active
headers = ["experiment", "total_images"] + [d for _, d in metrics_config]
for col, h in enumerate(headers, 1):
    ws.cell(row=1, column=col, value=h)

row_idx = 2
for exp_dir in sorted(results_root.glob("*")):
    stats = exp_dir / ".analysis" / "metrics_stats.json"
    if not stats.exists():
        continue
    data = json.loads(stats.read_text())
    exp_name = exp_dir.name.split("-test-1000-", 1)[-1] if "-test-1000-" in exp_dir.name else exp_dir.name
    ws.cell(row=row_idx, column=1, value=exp_name)
    ws.cell(row=row_idx, column=2, value=data["total_images"])
    for i, (key, _) in enumerate(metrics_config):
        val = data["metrics"].get(key, {}).get("mean")
        if val is not None:
            ws.cell(row=row_idx, column=3 + i, value=round(val, 3))
    row_idx += 1

wb.save(results_root / "all-experiments-evaluation.xlsx")
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'httpx'` | Missing pip deps in conda env | `pip install httpx distro sniffio python-dotenv` |
| `cuDNN error: CUDNN_STATUS_NOT_INITIALIZED` | torch cu130 vs CUDA 12.9 driver | `pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu126` |
| `CUDA out of memory` during eval | Eval competing with other GPU processes | Run eval alone, use `CUDA_VISIBLE_DEVICES` to isolate GPUs |
| HTML render fails with `waitForSelector: Timeout` | GPT output truncated (base64 images ate tokens) or missing `.widget` class | Code error, skip |
| JSX render `Build failed` | Model imported unavailable npm packages | Code error, skip. Or add allowed libs to prompt and install in `viewer/` |
| `extract_code` doesn't strip markdown fences | Output truncated, no closing ` ``` ` | Code error (token limit reached) |
