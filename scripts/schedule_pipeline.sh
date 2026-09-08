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
    LOCK_PID="$(cat "$LOCK" 2>/dev/null || true)"

    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "⚠ Previous pipeline is still running (PID $LOCK_PID). Skipping this run."
        exit 0
    fi

    echo "⚠ Removing stale pipeline lock (PID ${LOCK_PID:-unknown})."
    rm -f "$LOCK"
fi

printf '%s\n' "$$" > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

cd "$ROOT" || exit 1

/usr/bin/caffeinate -dimsu \
    "$ROOT/.venv/bin/python3" \
    "$ROOT/scripts/run_pipeline.py"

STATUS=$?

echo "Pipeline exit code: $STATUS"
date

exit "$STATUS"
