#!/usr/bin/env bash
# Run the Playwright suite and stop waiting once pytest has printed its summary.
# The bokeh test server keeps non-daemon threads alive, so the process can hang
# for minutes after the last test finishes; this makes local runs usable.
set -uo pipefail

LOG="${LOG:-/tmp/panel-mde-ui.log}"
: > "$LOG"

PYTHONPATH="${PYTHONPATH:-./src}" python -m pytest tests/test_ui.py --ui --browser chromium --color=no -p no:cacheprovider "$@" > "$LOG" 2>&1 &
PID=$!

for _ in $(seq 1 900); do
    if grep -qE "(passed|failed|error|no tests ran).* in [0-9]" "$LOG" 2>/dev/null; then
        break
    fi
    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi
    sleep 1
done

kill -9 "$PID" 2>/dev/null
grep -E "^(FAILED|ERROR)|(passed|failed|error|no tests ran).* in [0-9]" "$LOG"
! grep -qE "[0-9]+ (failed|error)" "$LOG"
