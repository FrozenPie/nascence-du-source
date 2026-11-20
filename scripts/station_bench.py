"""Run the station suite across many models — the model x station matrix.

Founder, 2026-08-20: *"Each model will have metrics for each task that will be different also is my
guess. We cannot just benchmark one task as we have many tasks."*

This produces one row per (model, station), not a league table. The project already has two proofs
that a single ranking misleads: `deepseek-r1:7b` won the Lane 2 prediction lab and is unusable on CPU;
`phi3:mini` led that same lab until a hedge metric was added and dropped it to 4th.

Writes raw output only. Scoring lives in `station_bench_score.py` so metrics can be revised against
fixed evidence — the discipline that caught both errors above.

SERIAL RESIDENCY is enforced: each model is unloaded before the next loads. On an 11.26 GB card with
5 GB models, co-residency silently corrupts latency and can push calls into timeouts that then look
like format failures. This was measured on 2026-08-20 (phi3 + deepseek co-resident on an 8 GB card)
and is not a hypothetical.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scripts.station_suite import ORDER, TASKS  # noqa: E402

import os
# Default: the 1080 Ti (11.26 GB — everything under ~9.6 GB fits fully). Overridable because
# not every model under test is an ollama model: Bonsai ships as raw GGUFs
# (C:/FreshStart/swarm/models) and is served by `nascence_cpu_server.py` on its own port.
# Fitness metrics are hardware-independent — only `wall` is not comparable across bases.
BASE = os.environ.get("STATION_BASE", "http://127.0.0.1:11433")
# THINK ARM (founder, 2026-08-20: "why should they be think:false? Could we let them think and clean
# up the result after the fact?"). The cleanup half of that is already solved — ollama's native
# /api/chat returns reasoning in a SEPARATE `thinking` field, and `model_client._strip_think_tags`
# handles the inline-<think> case. So nothing needs stripping. The real cost, per model_client's own
# history note, is that thinking BURNS THE TOKEN BUDGET and leaves `content` empty — which reads as a
# format failure and is a budget failure. That makes the question purely empirical: does thinking buy
# enough station fitness to pay for the tokens? Set STATION_THINK=1 with a budget multiplier to find out.
THINK = os.environ.get("STATION_THINK", "") == "1"
BUDGET_MULT = float(os.environ.get("STATION_BUDGET_MULT", "1"))
SUFFIX = os.environ.get("STATION_SUFFIX", "")     # keeps the think arm a SEPARATE row, never overwriting
OUT = ROOT / "data" / "lab" / "station_bench"
RUNS = 3
TIMEOUT = 300


def _post(path: str, payload: dict, timeout: int = TIMEOUT) -> dict:
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def unload(model: str) -> None:
    try:
        _post("/api/generate", {"model": model, "keep_alive": 0, "prompt": ""}, timeout=60)
    except Exception as e:
        print(f"    !! unload {model}: {e!r} — next model's numbers may be contaminated", flush=True)


def ask(model: str, system: str, user: str, budget: int, temp: float) -> dict:
    body = {"model": model, "stream": False, "keep_alive": "10m", "format": "json",
            # think:false MATCHES PRODUCTION and is not optional. `model_client.call_node` sets it
            # hard-off for every ollama lane. Without it, reasoning models (qwen3, qwen3.5, gemma4)
            # spend the whole budget in the `thinking` field and return EMPTY content — which scores
            # as a total format failure and is nothing of the kind. Measured 2026-08-20: all three
            # scored 0.0 across nearly every station until this line existed, purely as an artefact
            # of the harness diverging from how Du actually calls. Third occurrence of this exact
            # confusion in one day; the `had_thinking` field exists to make it self-diagnosing.
            "think": THINK,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "options": {"temperature": temp, "num_predict": max(budget, int(budget * BUDGET_MULT))}}
    t0 = time.time()
    try:
        d = _post("/api/chat", body)
    except Exception as e:
        return {"ok": False, "why": repr(e)[:100], "wall": round(time.time() - t0, 1)}
    msg = d.get("message") or {}
    raw = msg.get("content") or ""
    return {"ok": True, "wall": round(time.time() - t0, 1), "raw": raw,
            "gen_tok": d.get("eval_count"), "prompt_tok": d.get("prompt_eval_count"),
            # A reasoning model puts its work in a separate field and may leave `content` empty.
            # Recording this distinguishes "cannot do the task" from "needed a bigger budget" — a
            # confusion that already caused one model to be wrongly written off in this codebase.
            "had_thinking": bool(msg.get("thinking")),
            "think_chars": len(msg.get("thinking") or "")}


def run_model(model: str) -> dict:
    out: dict = {}
    for tname in ORDER:
        t = TASKS[tname]
        runs = []
        if "cases" in t:                       # judge: one call per labelled case, not repeats
            for text, gold in t["cases"]:
                r = ask(model, t["system"], text, t["budget"], t["temp"])
                r["gold"] = gold
                runs.append(r)
        else:
            for _ in range(RUNS):
                runs.append(ask(model, t["system"], t["user"], t["budget"], t["temp"]))
        ok = sum(1 for r in runs if r.get("ok"))
        med = sorted(r["wall"] for r in runs if r.get("ok"))
        print(f"    {tname:12s} ok={ok}/{len(runs)}  "
              f"median={med[len(med) // 2] if med else '—'}s", flush=True)
        out[tname] = runs
    return out


def main() -> int:
    models = sys.argv[1:]
    if not models:
        print("usage: station_bench.py <model> [<model> ...]")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    raw_path = OUT / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}

    for m in models:
        print(f"\n=== {m} ===", flush=True)
        try:
            raw[m + SUFFIX] = run_model(m)
        except Exception as e:
            print(f"    ABORTED: {e!r}", flush=True)
            raw[m + SUFFIX] = {"_error": repr(e)[:200]}
        unload(m)
        # Written after EVERY model: a 19-model run that dies at model 14 must not lose 13 models
        # of work. Cheap insurance against exactly the kind of long job that gets interrupted.
        # RE-READ before writing (fixed 2026-08-20): loading raw.json once at startup and
        # rewriting the whole dict clobbers any model another process added meanwhile. That
        # is not hypothetical — it silently destroyed the bonsai:8b-q1 and needle2 results,
        # which were written by separate runs while this one was mid-flight. Merge, never
        # overwrite: these runs are deliberately parallel (GPU roster, CPU llama.cpp hub,
        # CPU-only Needle) because they use different hardware.
        on_disk = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
        on_disk.update(raw)
        raw = on_disk
        raw_path.write_text(json.dumps(raw, indent=1), encoding="utf-8")
        print(f"    -- unloaded, {len(raw)} models saved", flush=True)
    print(f"\nwrote {raw_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
