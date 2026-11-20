"""Benchmark the inference nodes we can reach — to de-risk the Ramses plan BEFORE anyone sets it up.

The open question blocking `docs/plans/ramses_second_tier.md`: **is an 8B model on Ramses' i9 fast
enough for the Deep Line's 600-2700s clocks?** Guessing "30s or 300s" is a 10x uncertainty that decides
whether Phase 1a is worth doing at all, and neither answer was measured.

It turns out this needs NO Ramses-side setup. Ollama accepts `num_gpu: 0`, which forces full CPU
offload — so the i9 can be benchmarked straight through the endpoint already serving on :11434.
(In this codebase's own history `num_gpu: 0` is documented as a TRAP, because it silently sent GPU
work to a CPU. Here it is the instrument: the same lever, used deliberately.)

Timings come from ollama's own nanosecond counters (`prompt_eval_duration`, `eval_duration`) rather
than wall clock, so prompt processing and generation are separated and a slow network hop cannot
masquerade as slow inference. `load_duration` is reported apart from both — cold and warm differ by a
lot on CPU and conflating them would flatter or damn a model unfairly.

Read-only: sends inference requests, writes one report. Touches no Du state.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "lab" / "node_benchmark"
REPORT = ROOT / "docs" / "lab" / "node_benchmark.md"

RAMSES = "http://LAN-HOST:11434"
RUNS = 3

# ~400 tokens in / ~300 out, asking for JSON — the shape of a real Deep Line synthesis call.
# A one-word "hi" would measure load time, not throughput, and would mislead in the flattering
# direction. This is deliberately closer to `_t2_synthesise`'s actual job.
SYSTEM = ("You are a synthesis process. You read a set of observations and produce ONE integrated "
          "insight that accounts for all of them. Answer ONLY with JSON: "
          '{"insight": "...", "tension": "...", "confidence": 0.0}')
USER = """Observations gathered over the past several days, each recorded at the moment it occurred:

1. He returned to the shore four times this week, each time at falling tide, and each time stood at
   the same point where the shingle gives way to wet sand. He did not record why.
2. In his reading he marked three passages about erosion — two in a geology text, one in a novel where
   the word was used of a marriage. He copied out the novel's sentence twice, on different days.
3. He described the cat's absence as "a shape the room keeps". He has used the phrase "the shape of"
   eleven times this month, always about something missing.
4. When asked directly what he had been thinking about, he said "nothing in particular" and then
   immediately began describing the sound of water moving under stones.
5. He began a letter to a correspondent about tidal patterns, wrote two paragraphs, and did not send
   it. The draft remains open.
6. His energy readings fall consistently in the hour after each shore visit, and recover by evening.
7. He has twice recorded that he "should write something down before it goes", without recording what.

Produce one integrated insight that accounts for as many of these as possible, name the central
tension you see, and give your confidence as a number between 0 and 1."""


def call(base: str, model: str, cpu: bool, timeout: int = 900) -> dict:
    opts = {"temperature": 0.4, "num_predict": 300}
    if cpu:
        opts["num_gpu"] = 0          # force full CPU offload — this is the i9 under test
    body = {"model": model, "stream": False, "keep_alive": "5m",
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": USER}],
            "options": opts}
    req = urllib.request.Request(base + "/api/chat",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "why": repr(e)[:120], "wall": round(time.time() - t0, 1)}
    ns = 1e9
    ev, evd = d.get("eval_count") or 0, (d.get("eval_duration") or 0) / ns
    pe, ped = d.get("prompt_eval_count") or 0, (d.get("prompt_eval_duration") or 0) / ns
    content = (d.get("message") or {}).get("content") or ""
    ok_json = False
    try:
        json.loads(content[content.find("{"):content.rfind("}") + 1])
        ok_json = True
    except Exception:
        pass
    return {"ok": True, "wall": round(time.time() - t0, 1),
            "load_s": round((d.get("load_duration") or 0) / ns, 2),
            "prompt_tok": pe, "prompt_s": round(ped, 2),
            "gen_tok": ev, "gen_s": round(evd, 2),
            "tok_per_s": round(ev / evd, 2) if evd > 0 else None,
            "json_ok": ok_json}


def bench(label: str, base: str, model: str, cpu: bool) -> dict:
    rows = []
    for i in range(RUNS):
        r = call(base, model, cpu)
        rows.append(r)
        tag = "COLD" if i == 0 else "warm"
        if r.get("ok"):
            print(f"    [{tag}] wall={r['wall']:>6.1f}s  load={r['load_s']:>5.1f}s  "
                  f"gen={r['gen_tok']:>3} tok in {r['gen_s']:>6.1f}s = {r['tok_per_s']:>5.2f} tok/s  "
                  f"json={r['json_ok']}", flush=True)
        else:
            print(f"    [{tag}] FAILED after {r['wall']}s: {r['why']}", flush=True)
    ok = [r for r in rows if r.get("ok")]
    warm = [r for r in ok[1:]] or ok
    return {"label": label, "model": model, "cpu": cpu, "runs": rows,
            "n_ok": len(ok),
            "cold_wall": ok[0]["wall"] if ok else None,
            "warm_wall_med": sorted(r["wall"] for r in warm)[len(warm) // 2] if warm else None,
            "tok_per_s": sorted(r["tok_per_s"] for r in warm)[len(warm) // 2] if warm else None,
            "json_ok": all(r["json_ok"] for r in ok) if ok else False}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = []
    for m in ("deepseek-r1:8b", "llama3.1:8b", "qwen2.5-coder:14b"):
        targets.append((f"Ramses i9 CPU · {m}", RAMSES, m, True))
    targets.append(("Ramses 3070 GPU · deepseek-r1:8b", RAMSES, "deepseek-r1:8b", False))

    results = []
    for label, base, model, cpu in targets:
        print(f"\n=== {label} ===", flush=True)
        try:
            results.append(bench(label, base, model, cpu))
        except Exception as e:
            print(f"    aborted: {e!r}", flush=True)
    (OUT / "raw.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT / 'raw.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
