"""scripts/lab_j1752_hub_warm_degenerate.py (J-1752, 2026-10-08) -- plan-driven driver for the warm-state degenerate-generation
characterization of the gemma4:12b hub (:11439). Reuses scripts/lab_j1668_hub_cold_warm_probe.py's machinery unchanged
(production compose_letter path, lab_env.isolate + telemetry lab mode, hub-log cold/warm classification, live-state diff).

Usage:  python scripts/lab_j1752_hub_warm_degenerate.py --plan "C1:shackleton:16,W1:twain:20,W2:twain:20,W3:twain:18" [--dry]
  --plan  comma list of LABEL:persona:rows_upto ; the token UNLOAD waits for the hub's own idle-unload (hub log 'unloading').
  Set J1668_OUT to choose the output dir (default temp/j1668_probe; results.jsonl is APPENDED).
The hub must be idle (Du down). NEVER restarts/signals the hub. Each call holds the hub lock 2-7 min.
"""
import os, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import lab_j1668_hub_cold_warm_probe as p

spec = sys.argv[sys.argv.index("--plan") + 1]
plan = []
for tok in spec.split(","):
    tok = tok.strip()
    if tok == "UNLOAD":
        plan.append(("WAIT_UNLOAD", None, None, None))
    else:
        label, persona, upto = tok.split(":")
        plan.append((label, "?", persona, int(upto)))
if __name__ == "__main__":
    import asyncio
    p.PLAN = plan
    # p.main() reassigns PLAN only for --plan2, which we never pass
    asyncio.run(p.main())
