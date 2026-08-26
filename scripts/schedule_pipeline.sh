#!/bin/bash

set -u

ROOT="$HOME/Projects/AI_Job_Hunter"
LOG="$HOME/Library/Logs/AI_Job_Hunter/pipeline.log"
LOCK="$HOME/Library/Logs/AI_Job_Hunter/pipeline.lock"

exec >> "$LOG" 2>&1

echo ""
echo "============================================================"
echo "AI JOB HUNTER SCHEDULED RUN"
date
echo "============================================================"

if [ -f "$LOCK" ]; then
    echo "⚠ Previous pipeline is still running. Skipping this run."
    exit 0
fi

touch "$LOCK"
trap 'rm -f "$LOCK"' EXIT

cd "$ROOT" || exit 1

/usr/bin/caffeinate -dimsu \
    "$ROOT/.venv/bin/python3" \
    "$ROOT/scripts/run_pipeline.py"

STATUS=$?

echo "Pipeline exit code: $STATUS"
date

exit "$STATUS"
