"""Render the node benchmark into a report — from saved raw JSON, nothing re-queried.

Same contract as the lane2 labs: scoring/presentation is revised against fixed evidence so a change of
interpretation is never confounded with a change of sampling.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = ROOT / "data" / "lab" / "node_benchmark"
REPORT = ROOT / "docs" / "lab" / "node_benchmark.md"
Q = chr(96)


def load(name):
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def main() -> int:
    ram, loc = load("raw.json"), load("raw_local.json")
    L, A = [], None
    L = []
    A = L.append
    A("# Node benchmark — can the Ramses i9 carry a CPU tier?\n")
    A(f"*{time.strftime('%Y-%m-%d %H:%M')} · Du stopped, both machines otherwise idle · "
      f"prompt ~400 tok in / 300 max out, JSON requested · 3 runs each*\n")
    A("**The question this exists to answer** (`docs/plans/ramses_second_tier.md` Phase 1a): an 8B "
      "model on Ramses' i9 — 30 seconds or 300? That 10x uncertainty decided whether the CPU tier was "
      "worth standing up, and it had never been measured.\n")
    A("**Method note:** the i9 is reached through the ollama already serving on `:11434` with "
      f"{Q}num_gpu: 0{Q}, which forces full CPU offload — **no Ramses-side setup was needed to measure "
      "it.** In this codebase's history that flag is documented as a trap (it silently sent GPU work to "
      "a CPU); here the same lever is the instrument.\n")
    A("Wall clock is the common denominator: ollama reports internal generation timers, the local "
      f"{Q}nascence_cpu_server.py{Q} hubs report token counts only. Mixing them would compare two "
      "different quantities and favour whichever excludes more overhead.\n")

    if ram:
        A("## Ramses\n")
        A("| node | model | cold wall | warm wall | tok/s | gen tok | valid JSON |")
        A("|---|---|---|---|---|---|---|")
        for r in ram:
            ok = [x for x in r["runs"] if x.get("ok")]
            gt = ok[-1].get("gen_tok") if ok else "—"
            A(f"| {'i9 CPU' if r['cpu'] else '3070 GPU'} | {Q}{r['model']}{Q} | "
              f"{r.get('cold_wall')}s | {r.get('warm_wall_med')}s | {r.get('tok_per_s')} | {gt} | "
              f"{'yes' if r.get('json_ok') else '**no**'} |")
        A("")
    if loc:
        A("## Local (comparison)\n")
        A("| node | model | cold wall | warm wall | gen tok | valid JSON |")
        A("|---|---|---|---|---|---|")
        for r in loc:
            ok = [x for x in r["runs"] if x.get("ok")]
            gt = ok[-1].get("gen_tok") if ok else "—"
            A(f"| {r['label'].split(' · ')[0]} | {Q}{r['model']}{Q} | {r.get('cold_wall')}s | "
              f"{r.get('warm_wall_med')}s | {gt} | {'yes' if r.get('json_ok') else '**no**'} |")
        A("")
    A("*Raw: `data/lab/node_benchmark/raw.json`, `raw_local.json`*")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
