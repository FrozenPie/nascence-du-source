#!/usr/bin/env bash
# scripts/lag_harness/run_contention_sweep_J1927.sh (J-1927): one condition = start the stand-in busy hub processes
# (busy_standin_J1927.py, OUTSIDE the audited harness process), wait for them to warm, run cpu_contention_J1927.py,
# then stop them through the stop file. Du must be DOWN (the stand-ins take the whole CPU).
# usage: run_contention_sweep_J1927.sh <label> <busy_threads_csv e.g. 14,20 or 0> <membw|compute> [harness args...]
# env: LAGH_SCRATCH, LAGH_WT (as the harness), HARNESS_DIR (dir holding the scripts; default: this script's dir)
set -u
LABEL="$1"; BUSY="$2"; MODE="$3"; shift 3
HD="${HARNESS_DIR:-$(cd "$(dirname "$0")" && pwd)}"
STOP="$LAGH_SCRATCH/busy_stop_J-1927"
rm -f "$STOP"
pids=()
if [ "$BUSY" != "0" ]; then
  IFS=, read -ra parts <<< "$BUSY"
  for t in "${parts[@]}"; do
    python "$HD/busy_standin_J1927.py" --threads "$t" --mode "$MODE" --secs 1200 --stopfile "$STOP" \
      >> "$LAGH_SCRATCH/busy_${LABEL}_J-1927.log" 2>&1 &
    pids+=($!)
  done
  sleep 10
fi
echo "== condition $LABEL busy=$BUSY mode=$MODE pids=${pids[*]:-none} $*"
python "$HD/cpu_contention_J1927.py" --label "$LABEL" "$@" 2>&1 | grep -v "FutureWarning\|import pynvml"
rc=${PIPESTATUS[0]}
touch "$STOP"
for p in "${pids[@]:-}"; do [ -n "$p" ] && wait "$p" 2>/dev/null; done
rm -f "$STOP"
exit $rc
