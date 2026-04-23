# Run commands

Pipeline: **infer → render → eval**. Each step reads the previous step's output from `results/<experiment>/...`.

## Prompt variants

Two prompt families were validated on 1000 images with gpt-4o. Both inject **color palette + OCR text positions**; the difference is how the widget size is conveyed to the model:

| variant | flag | what model receives | prompt dir |
|---|---|---|---|
| **`svgonly-color-ocr`** (SOTA) | `--size` | exact pixel `W×H` of source image | `prompts/react-gemini-svgonly-color-ocr/` |
| `aspect-color-ocr` | `--aspect-ratio` | aspect ratio only, model picks W/H | `prompts/react-gemini-aspect-color-ocr/` |

Head-to-head on gpt-4o / 1000 images: **svgonly-color-ocr wins 7-3-1** (notably ContrastDiff +3.08, PolarityConsistency +3.31). Use `svgonly-color-ocr` unless you explicitly want model-chosen dimensions.

---

## 1. Infer (image → JSX)

### gpt-4o — svgonly + color + OCR (SOTA, 1000 images)

```bash
python3 /home/houston/workspace/widget-research/widget2code-baselines/scripts/batch_infer.py \
  --model gpt-4o \
  --images-dir /home/houston/workspace/widget-research/widget2code2.0/data/widget2code-benchmark/test \
  --prompts-root /home/houston/workspace/widget-research/widget2code-baselines/prompts \
  --results-root /home/houston/workspace/widget-research/widget2code-baselines/results \
  --include "react-gemini-svgonly-color-ocr/*" \
  --experiment "gpt-4o-test-1000-svgonly-color-ocr" \
  --size --inject-colors --inject-ocr \
  --threads 300 --timeout 180
```

Reference run: `results/20260423-034243-gpt-4o-test-1000-svgonly-color-ocr`.

### qwen3-vl-plus — aspect + color + OCR (1000 images)

```bash
python3 /home/houston/workspace/widget-research/widget2code-baselines/scripts/batch_infer.py \
  --model qwen3-vl-plus \
  --images-dir /home/houston/workspace/widget-research/widget2code2.0/data/widget2code-benchmark/test \
  --prompts-root /home/houston/workspace/widget-research/widget2code-baselines/prompts \
  --results-root /home/houston/workspace/widget-research/widget2code-baselines/results \
  --include "react-gemini-aspect-color-ocr/*" \
  --experiment "qwen3vl-plus-test-1000-aspect-color-ocr-v1" \
  --aspect-ratio --inject-colors --inject-ocr \
  --threads 100 --timeout 180
```

### gpt-4o — aspect + color + OCR (1000 images)

```bash
python3 /home/houston/workspace/widget-research/widget2code-baselines/scripts/batch_infer.py \
  --model gpt-4o \
  --images-dir /home/houston/workspace/widget-research/widget2code2.0/data/widget2code-benchmark/test \
  --prompts-root /home/houston/workspace/widget-research/widget2code-baselines/prompts \
  --results-root /home/houston/workspace/widget-research/widget2code-baselines/results \
  --include "react-gemini-aspect-color-ocr/*" \
  --experiment "gpt-4o-test-1000-aspect-color-ocr-run2" \
  --aspect-ratio --inject-colors --inject-ocr \
  --threads 100 --timeout 180
```

The experiment dir is prefixed with a timestamp by `batch_infer.py`, e.g. `20260423-023146-gpt-4o-test-1000-aspect-color-ocr-run2`.

---

## 2. Render (JSX → PNG)

Scale-based renderer: reads GT image size, applies CSS `transform: scale()` so layout renders at the model's chosen canvas then is scaled to GT dims (sharp text, no Lanczos blur). This is the **only** renderer that was used for the validated runs above — `renderer/bin/render-jsx-batch.mjs` does not have target-size-from-GT logic and must not be used here.

```bash
cd /home/houston/workspace/widget-research/widget2code-baselines/viewer
node renderer/test_scale_poc.mjs \
  /home/houston/workspace/widget-research/widget2code-baselines/results/20260423-034243-gpt-4o-test-1000-svgonly-color-ocr \
  /shared/zhixiang_team/widget_research/Comparison/GT \
  -j 8
```

Positional args: `<results_dir> <gt_dir>`. `cd viewer/` first or the relative deps won't resolve. Expand the timestamp prefix with a glob (`20260423-*-...`) if you don't remember it.

---

## 3. Eval (widget2code-bench-exp 0.2.9)

```bash
source /home/houston/miniconda3/etc/profile.d/conda.sh && conda activate widget2code-bench-exp-0.2.9 && \
CUDA_VISIBLE_DEVICES=5 widget2code-bench-exp \
  --gt_dir /shared/zhixiang_team/widget_research/Comparison/GT \
  --pred_dir /home/houston/workspace/widget-research/widget2code-baselines/results/20260423-034243-gpt-4o-test-1000-svgonly-color-ocr \
  --pred_name "react-gemini-svgonly-color-ocr/1-minimal.png" \
  --cuda --workers 35
```

`--pred_name` is the path **inside each sample dir** to the rendered PNG. Match the prompt folder name used during infer (`react-gemini-svgonly-color-ocr` or `react-gemini-aspect-color-ocr`).
