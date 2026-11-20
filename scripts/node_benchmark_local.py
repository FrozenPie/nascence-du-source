"""Local-side companion to `node_benchmark.py` — the comparison point that makes the Ramses numbers mean something.

An absolute "8B on the i9 takes N seconds" is hard to judge. A RELATIVE number against the CPU tier Du
already runs in production is not: `llama3.1:8b` serves on the local Threadripper hub (:11439) today,
and the same model can be forced onto Ramses' i9. Same model, same prompt, two CPUs — that ratio is
what tells us whether the i9 tier is viable or a downgrade dressed as capacity.

**Wall clock only, deliberately.** `nascence_cpu_server.py` returns `prompt_eval_count`/`eval_count`
but not `eval_duration` or `load_duration` (ollama does). Mixing ollama's internal generation timer
with the local hub's wall clock would compare two different quantities and quietly favour whichever
excludes more overhead. Wall clock is the one number both stacks report the same way.

Caveat kept in view: local hubs are llama.cpp via `nascence_cpu_server.py`; Ramses is ollama with
`num_gpu: 0`. Both are llama.cpp underneath, but the serving wrappers differ, so treat the ratio as a
solid go/no-go signal rather than a precise coefficient.
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scripts.node_benchmark import RUNS, SYSTEM, USER, call  # noqa: E402

OUT = ROOT / "data" / "lab" / "node_benchmark"

TARGETS = [
    # label,                                    base,                      model
    ("Local Threadripper CPU · llama3.1:8b",    "http://127.0.0.1:11439",  "llama3.1:8b"),
    ("Local Threadripper CPU · qwen2.5:7b",     "http://127.0.0.1:11440",  "qwen2.5:7b"),
    ("Local 1080 Ti GPU · phi3:mini",           "http://127.0.0.1:11433",  "phi3:mini"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for label, base, model in TARGETS:
        print(f"\n=== {label} ===", flush=True)
        rows = []
        for i in range(RUNS):
            r = call(base, model, cpu=False)      # these hubs are already CPU-pinned by construction
            rows.append(r)
            tag = "COLD" if i == 0 else "warm"
            if r.get("ok"):
                print(f"    [{tag}] wall={r['wall']:>6.1f}s  gen_tok={r['gen_tok']:>3}  "
                      f"json={r['json_ok']}", flush=True)
            else:
                print(f"    [{tag}] FAILED after {r['wall']}s: {r['why']}", flush=True)
        ok = [r for r in rows if r.get("ok")]
        warm = ok[1:] or ok
        results.append({"label": label, "model": model, "runs": rows, "n_ok": len(ok),
                        "cold_wall": ok[0]["wall"] if ok else None,
                        "warm_wall_med": st.median([r["wall"] for r in warm]) if warm else None,
                        "json_ok": all(r["json_ok"] for r in ok) if ok else False})
    (OUT / "raw_local.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT / 'raw_local.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
