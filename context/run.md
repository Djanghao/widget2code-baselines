# Run commands

Pipeline: **infer → render → eval**. Each step reads the previous step's output from `results/<experiment>/...`.

---

## 1. Infer (image → JSX)

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

Scale-based renderer: reads GT image size, applies CSS `transform: scale()` so layout renders at the model's chosen canvas then is scaled to GT dims (sharp text, no Lanczos blur).

```bash
cd /home/houston/workspace/widget-research/widget2code-baselines/viewer
node renderer/test_scale_poc.mjs \
  /home/houston/workspace/widget-research/widget2code-baselines/results/20260423-023146-gpt-4o-test-1000-aspect-color-ocr-run2 \
  /shared/zhixiang_team/widget_research/Comparison/GT \
  -j 8
```

Positional args: `<results_dir> <gt_dir>`. Expand the timestamp prefix with a glob (`20260423-*-...`) if you don't remember it.

---

## 3. Eval (widget2code-bench-exp 0.2.9)

```bash
source /home/houston/miniconda3/etc/profile.d/conda.sh && conda activate widget2code-bench-exp-0.2.9 && \
CUDA_VISIBLE_DEVICES=5 widget2code-bench-exp \
  --gt_dir /shared/zhixiang_team/widget_research/Comparison/GT \
  --pred_dir /home/houston/workspace/widget-research/widget2code-baselines/results/20260423-023146-gpt-4o-test-1000-aspect-color-ocr-run2 \
  --pred_name "react-gemini-aspect-color-ocr/1-minimal.png" \
  --cuda --workers 35
```

`--pred_name` is the path **inside each sample dir** to the rendered PNG. Match the prompt folder name used during infer.
