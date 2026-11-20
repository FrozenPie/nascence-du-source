#!/bin/sh
# J-2363: four 600 s arms of the PURSUITS_LIGHT_READ A/B, order off,on,on,off. Stops if Du's log moves off the shutdown line.
export LAGH_SCRATCH='C:\Users\USER\AppData\Local\Temp\jr1018' LAGH_WT=wt_lag_harness
cd "$(dirname "$0")/../.."
i=0
for arm in off on on off; do
  i=$((i+1))
  last=$(tail -1 /c/Nascence/data/nascence.log)
  case "$last" in *"Nascence shutting down."*) ;; *) echo "Du not down, stop: $last"; exit 2;; esac
  echo "== run $i $arm $(date -Is)"
  python scripts/lag_harness/ab_pursuits_light_J2363.py $arm ${DUR:-600} ab_J-2363_${i}_${arm}.json > "$LAGH_SCRATCH/ab_J-2363_${i}_${arm}.log" 2>&1
  echo "exit $? $(date -Is)"
done
tail -1 /c/Nascence/data/nascence.log
