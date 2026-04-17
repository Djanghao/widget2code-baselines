#!/bin/bash
# Batch evaluation script - runs 2 jobs in parallel (1 per GPU)
# Usage: bash scripts/run_eval_batch.sh

RESULTS_DIR="/home/houston/workspace/widget-research/widget2code-baselines/results"
GT_DIR="/shared/zhixiang_team/widget_research/Comparison/GT"
GPUS=(5 6)
LOG_DIR="/home/houston/workspace/widget-research/widget2code-baselines/eval_logs"
mkdir -p "$LOG_DIR"

# Extract prompt template from directory name
get_prompt_template() {
    local name="$1"
    # Remove timestamp-model-test-1000- prefix and eval suffix
    # Pattern: DATE-MODEL-test-1000-PROMPT_TEMPLATE-EVAL_SUFFIX
    # Eval suffixes: minimal, minimal-cal-size, minimal-cal-aspect-ratio, minimal-cal-size-cal-aspect-ratio
    local after_1000
    after_1000=$(echo "$name" | sed 's/.*-test-1000-//')
    # Remove eval suffixes from the end
    local template
    template=$(echo "$after_1000" | sed \
        -e 's/-minimal-cal-size-cal-aspect-ratio$//' \
        -e 's/-minimal-cal-aspect-ratio$//' \
        -e 's/-minimal-cal-size$//' \
        -e 's/-minimal$//')
    echo "$template"
}

# Collect TODO runs (skip runs with 0 rendered PNGs)
TODO_RUNS=()
SKIPPED=()
for d in "$RESULTS_DIR"/202604*/; do
    name=$(basename "$d")
    if [ -f "$d/evaluation.xlsx" ]; then
        continue
    fi
    # Check if there are any rendered PNGs (non-source.png)
    template=$(get_prompt_template "$name")
    png_count=$(find "$d" -path "*/${template}/1-minimal.png" | head -1 | wc -l)
    if [ "$png_count" -eq 0 ]; then
        SKIPPED+=("$name")
    else
        TODO_RUNS+=("$name")
    fi
done

if [ ${#SKIPPED[@]} -gt 0 ]; then
    echo "Skipped ${#SKIPPED[@]} runs (no rendered PNGs):"
    for s in "${SKIPPED[@]}"; do
        echo "  - $s"
    done
    echo "---"
fi

echo "Total TODO runs: ${#TODO_RUNS[@]}"
echo "Using GPUs: ${GPUS[*]}"
echo "---"

# Process runs with 2 parallel jobs
idx=0
total=${#TODO_RUNS[@]}

while [ $idx -lt $total ]; do
    pids=()
    for gpu in "${GPUS[@]}"; do
        if [ $idx -ge $total ]; then
            break
        fi
        run="${TODO_RUNS[$idx]}"
        template=$(get_prompt_template "$run")
        pred_name="${template}/1-minimal.png"
        pred_dir="${RESULTS_DIR}/${run}"
        log_file="${LOG_DIR}/${run}.log"

        echo "[$(date +%H:%M:%S)] Starting ($((idx+1))/$total) on GPU $gpu: $run"
        echo "  pred_name: $pred_name"

        CUDA_VISIBLE_DEVICES=$gpu widget2code-bench \
            --gt_dir "$GT_DIR" \
            --pred_dir "$pred_dir" \
            --pred_name "$pred_name" \
            --cuda --workers 4 \
            > "$log_file" 2>&1 &
        pids+=($!)
        idx=$((idx+1))
    done

    # Wait for current batch to finish
    for pid in "${pids[@]}"; do
        wait "$pid"
        status=$?
        if [ $status -ne 0 ]; then
            echo "  WARNING: PID $pid exited with status $status"
        fi
    done
    echo "[$(date +%H:%M:%S)] Batch done."
done

echo "=== All evaluations complete ==="
# Summary
done_count=0
fail_count=0
for run in "${TODO_RUNS[@]}"; do
    if [ -f "${RESULTS_DIR}/${run}/evaluation.xlsx" ]; then
        done_count=$((done_count+1))
    else
        fail_count=$((fail_count+1))
        echo "FAILED: $run"
    fi
done
echo "Success: $done_count / $total"
echo "Failed: $fail_count / $total"
