#!/bin/bash

# All models use OpenAI-compatible API. Base URLs and API keys are loaded
# from .env via MODEL_REGISTRY in batch_infer.py.
# For self-hosted endpoints, pass --base-url / --api-key explicitly.

# -----------------------------------------------------------------------------
# gpt-4o
# -----------------------------------------------------------------------------
source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment gpt-4o-test-1000-html-no-size-minimal-cal-size-cal-aspect-ratio \
  --threads 1 --model gpt-4o --include "html-no-size/1-minimal.md" --size --aspect-ratio

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment gpt-4o-test-1000-html-no-size-minimal-cal-size \
  --threads 1 --model gpt-4o --include "html-no-size/1-minimal.md" --size

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment gpt-4o-test-1000-html-no-size-minimal-cal-aspect-ratio \
  --threads 1 --model gpt-4o --include "html-no-size/1-minimal.md" --aspect-ratio

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment gpt-4o-test-1000-html-no-size-minimal \
  --threads 1 --model gpt-4o --include "html-no-size/1-minimal.md"

# -----------------------------------------------------------------------------
# doubao-1.8
# -----------------------------------------------------------------------------
source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment doubao-1.8-test-1000-html-no-size-minimal-cal-size-cal-aspect-ratio \
  --threads 1 --model doubao-1.8 --include "html-no-size/1-minimal.md" --size --aspect-ratio

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment doubao-1.8-test-1000-html-no-size-minimal-cal-size \
  --threads 1 --model doubao-1.8 --include "html-no-size/1-minimal.md" --size

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment doubao-1.8-test-1000-html-no-size-minimal-cal-aspect-ratio \
  --threads 1 --model doubao-1.8 --include "html-no-size/1-minimal.md" --aspect-ratio

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment doubao-1.8-test-1000-html-no-size-minimal \
  --threads 1 --model doubao-1.8 --include "html-no-size/1-minimal.md"


# -----------------------------------------------------------------------------
# qwen3-vl-235b-a22b-instruct (self-hosted vLLM endpoint)
# -----------------------------------------------------------------------------
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-235b-a22b-instruct-test-1000-html-no-size-minimal-cal-size-cal-aspect-ratio \
  --threads 8 --api-key EMPTY --base-url http://202.78.161.193:3050/v1 \
  --model "Qwen/Qwen3-VL-235B-A22B-Instruct" --include "html-no-size/1-minimal.md" \
  --timeout 3600 --max-tokens 2048 --size --aspect-ratio

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-235b-a22b-instruct-test-1000-html-no-size-minimal-cal-size \
  --threads 8 --api-key EMPTY --base-url http://202.78.161.193:3050/v1 \
  --model "Qwen/Qwen3-VL-235B-A22B-Instruct" --include "html-no-size/1-minimal.md" \
  --timeout 3600 --max-tokens 2048 --size

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-235b-a22b-instruct-test-1000-html-no-size-minimal-cal-aspect-ratio \
  --threads 8 --api-key EMPTY --base-url http://202.78.161.193:3050/v1 \
  --model "Qwen/Qwen3-VL-235B-A22B-Instruct" --include "html-no-size/1-minimal.md" \
  --timeout 3600 --max-tokens 2048 --aspect-ratio

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-235b-a22b-instruct-test-1000-html-no-size-minimal \
  --threads 8 --api-key EMPTY --base-url http://202.78.161.193:3050/v1 \
  --model "Qwen/Qwen3-VL-235B-A22B-Instruct" --include "html-no-size/1-minimal.md" \
  --timeout 3600 --max-tokens 2048


# -----------------------------------------------------------------------------
# qwen3-vl-plus
# -----------------------------------------------------------------------------
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-plus-test-1000-html-no-size-minimal-cal-size-cal-aspect-ratio \
  --threads 1 --model qwen3-vl-plus --include "html-no-size/1-minimal.md" --size --aspect-ratio

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-plus-test-1000-html-no-size-minimal-cal-size \
  --threads 1 --model qwen3-vl-plus --include "html-no-size/1-minimal.md" --size

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-plus-test-1000-html-no-size-minimal-cal-aspect-ratio \
  --threads 1 --model qwen3-vl-plus --include "html-no-size/1-minimal.md" --aspect-ratio

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-plus-test-1000-html-no-size-minimal \
  --threads 1 --model qwen3-vl-plus --include "html-no-size/1-minimal.md"


# -----------------------------------------------------------------------------
# qwen3-vl-8b-instruct
# -----------------------------------------------------------------------------
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-8b-instruct-test-1000-html-no-size-minimal-cal-size-cal-aspect-ratio \
  --threads 1 --model qwen3-vl-8b-instruct --include "html-no-size/1-minimal.md" --size --aspect-ratio

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-8b-instruct-test-1000-html-no-size-minimal-cal-size \
  --threads 1 --model qwen3-vl-8b-instruct --include "html-no-size/1-minimal.md" --size

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-8b-instruct-test-1000-html-no-size-minimal-cal-aspect-ratio \
  --threads 1 --model qwen3-vl-8b-instruct --include "html-no-size/1-minimal.md" --aspect-ratio

python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment qwen3vl-8b-instruct-test-1000-html-no-size-minimal \
  --threads 1 --model qwen3-vl-8b-instruct --include "html-no-size/1-minimal.md"


# -----------------------------------------------------------------------------
# qwen3-vl-32b-instruct
# -----------------------------------------------------------------------------
python scripts/batch_infer.py --images-dir /home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000 \
  --experiment qwen3vl-32b-instruct-test-1000-html-no-size-minimal-cal-size-cal-aspect-ratio \
  --threads 1 --model qwen3-vl-32b-instruct --include "html-no-size/1-minimal.md" --size --aspect-ratio

python scripts/batch_infer.py --images-dir /home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000 \
  --experiment qwen3vl-32b-instruct-test-1000-html-no-size-minimal-cal-size \
  --threads 1 --model qwen3-vl-32b-instruct --include "html-no-size/1-minimal.md" --size

python scripts/batch_infer.py --images-dir /home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000 \
  --experiment qwen3vl-32b-instruct-test-1000-html-no-size-minimal-cal-aspect-ratio \
  --threads 1 --model qwen3-vl-32b-instruct --include "html-no-size/1-minimal.md" --aspect-ratio

python scripts/batch_infer.py --images-dir /home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000 \
  --experiment qwen3vl-32b-instruct-test-1000-html-no-size-minimal \
  --threads 1 --model qwen3-vl-32b-instruct --include "html-no-size/1-minimal.md"


# -----------------------------------------------------------------------------
# qwen2.5-vl-32b-instruct
# -----------------------------------------------------------------------------
python scripts/batch_infer.py --images-dir /home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000 \
  --experiment qwen2.5vl-32b-instruct-test-1000-html-no-size-minimal-cal-size-cal-aspect-ratio \
  --threads 1 --model qwen2.5-vl-32b-instruct --include "html-no-size/1-minimal.md" --size --aspect-ratio

python scripts/batch_infer.py --images-dir /home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000 \
  --experiment qwen2.5vl-32b-instruct-test-1000-html-no-size-minimal-cal-size \
  --threads 1 --model qwen2.5-vl-32b-instruct --include "html-no-size/1-minimal.md" --size

python scripts/batch_infer.py --images-dir /home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000 \
  --experiment qwen2.5vl-32b-instruct-test-1000-html-no-size-minimal-cal-aspect-ratio \
  --threads 1 --model qwen2.5-vl-32b-instruct --include "html-no-size/1-minimal.md" --aspect-ratio

python scripts/batch_infer.py --images-dir /home/houston/workspace/widget-research/widget-factory-release/data/assets/images-test-1000 \
  --experiment qwen2.5vl-32b-instruct-test-1000-html-no-size-minimal \
  --threads 1 --model qwen2.5-vl-32b-instruct --include "html-no-size/1-minimal.md"


# -----------------------------------------------------------------------------
# gemini-3.0-pro-preview
# -----------------------------------------------------------------------------
source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment gemini-3.0-pro-preview-test-1000-html-no-size-minimal-cal-size-cal-aspect-ratio \
  --threads 1 --model gemini-3.0-pro-preview --include "html-no-size/1-minimal.md" --size --aspect-ratio

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment gemini-3.0-pro-preview-test-1000-html-no-size-minimal-cal-size \
  --threads 1 --model gemini-3.0-pro-preview --include "html-no-size/1-minimal.md" --size

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment gemini-3.0-pro-preview-test-1000-html-no-size-minimal-cal-aspect-ratio \
  --threads 1 --model gemini-3.0-pro-preview --include "html-no-size/1-minimal.md" --aspect-ratio

source venv/bin/activate
python scripts/batch_infer.py --images-dir /shared/zhixiang_team/widget_research/images/images-test-1000 \
  --experiment gemini-3.0-pro-preview-test-1000-html-no-size-minimal \
  --threads 1 --model gemini-3.0-pro-preview --include "html-no-size/1-minimal.md"
