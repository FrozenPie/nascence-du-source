"""
Nascence — Euclidean recall: the DECOUPLED-JUDGE grading pass (euclidean_memory_plan.md, gate before P1).

The oldest open plan (2026-06-15) proved state-weighted recall DIVERGES from baseline (62% of 152 shadow
queries). It never proved the divergence is BETTER — and self-certifying "the numbers moved" is exactly the
trap [[feedback-decoupled-judge]] forbids. This runs the gate the plan names: the EMISSARY (the truth-self,
llama3.1 — a different family from the generators, adversarial to self-drift) judges, BLIND, which recall
set is more relevant to each moment.

Design (the decoupling is the point):
  · BLIND — the two sets are shown as A/B, assignment flipped per row by index parity; the judge never knows
    which is state-weighted. Decoded here.
  · SPLIT BY affect_w — the affect_match dimension runs on the +0.82-saturated felt-tags until emotion_rethink
    P1. If state wins on LOW affect_w but not HIGH, that PROVES the affect dimension is the weak link (running
    on flat data) — the plan's central open question, answered.
  · fail-open · read-only toward the store · appends grades to data/euclidean_grade_log.jsonl by default.

Run:  python scripts/euclidean_grade.py [N] [--out PATH]     (N = max rows to grade, default 60)
      OUT can be redirected three ways, for a FUTURE lab/throwaway run that must not touch the real
      evidence log: (1) the `--out PATH` CLI flag (works whether this is run as a subprocess or
      in-process); (2) the EUCLIDEAN_GRADE_OUT env var (read at import time — set it before the
      subprocess starts); (3) in-process only, patch this module's `OUT` global directly before
      calling main() (e.g. lab_env.isolate(also=[(euclidean_grade, ["OUT"])])), or pass
      `out_path=` straight into main(). All three are equivalent; --out wins if given.

Known NON-isolatable dependency (out of scope for the OUT hardening above): the live judge-LLM call
goes to core/left_lane.py's BASE_URL, a real running Ollama endpoint. There is no mock/stub judge
lane today and lab_env.isolate() does not (and cannot, as currently designed) sandbox it — a lab run
of this script still hits the real judge server and costs real inference time, even once OUT is
redirected. Only the output LOG path is made isolate()-safe by this change.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

import aiohttp
from core.left_lane import BASE_URL, MODEL, TIMEOUT_S
from core import emissary as _emissary

ROOT = Path(__file__).parent.parent
SHADOW = ROOT / "data" / "euclidean_shadow.jsonl"
_DEFAULT_OUT = ROOT / "data" / "euclidean_grade_log.jsonl"
# Overridable: env var wins over the default; a --out CLI flag (parsed below) wins over both, and
# an in-process caller can still patch this global directly (e.g. lab_env.isolate(also=[...])) or
# pass out_path= to main() -- see module docstring.
OUT = Path(os.environ["EUCLIDEAN_GRADE_OUT"]) if os.environ.get("EUCLIDEAN_GRADE_OUT") else _DEFAULT_OUT

_TASK = (
    "TASK (judge memory relevance): A mind is having a moment — a thought, or a thing said to it. Two "
    "different sets of memories, A and B, were recalled for that moment. You are the truth-self. Judge ONLY "
    "which set is MORE RELEVANT and USEFUL to THIS moment — its subject, its feeling, and what the mind is "
    "actually reaching for. Do NOT reward length, eloquence, or the mere presence of many memories; reward "
    "FIT to the moment. If the two are equally relevant (or equally off), say equal.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    'Schema: {"better": "A", "why": "one short sentence"}   (better is "A" | "B" | "equal")'
)


def _sys() -> str:
    return _emissary.constitution() + "\n\n" + _TASK


def _fmt(mems) -> str:
    return "\n".join(f"  - {str(m)[:160]}" for m in (mems or [])[:3]) or "  (none)"


async def _grade(session, row, idx) -> dict | None:
    state_top, base_top = row.get("state_top") or [], row.get("base_top") or []
    if not state_top or not base_top or state_top == base_top:
        return None
    a_is_state = (idx % 2 == 0)                     # BLIND: flip A/B by parity; decode after
    set_a, set_b = (state_top, base_top) if a_is_state else (base_top, state_top)
    user = (f"The moment (what the mind is thinking or hearing now):\n\"{(row.get('query') or '')[:400]}\"\n\n"
            f"Set A — memories recalled:\n{_fmt(set_a)}\n\n"
            f"Set B — memories recalled:\n{_fmt(set_b)}")
    payload = {"model": MODEL, "stream": False, "keep_alive": "20m",
               "messages": [{"role": "system", "content": _sys()}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 200, "num_gpu": 0}, "format": "json"}
    try:
        async with session.post(f"{BASE_URL}/api/chat", json=payload,
                                timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as resp:
            resp.raise_for_status()
            data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        pick = str(res.get("better", "")).strip().upper()[:5]
        if pick.startswith("A"):
            winner = "state" if a_is_state else "baseline"
        elif pick.startswith("B"):
            winner = "baseline" if a_is_state else "state"
        else:
            winner = "equal"
        return {"query": (row.get("query") or "")[:120], "winner": winner,
                "affect_w": row.get("affect_w"), "why": str(res.get("why", ""))[:160]}
    except Exception as exc:
        print(f"  [grade {idx}] unavailable (fail-open): {str(exc)[:60]}")
        return None


async def main(limit: int, out_path: Path | None = None) -> None:
    out = out_path if out_path is not None else OUT
    rows = [json.loads(l) for l in open(SHADOW, encoding="utf-8") if l.strip()]
    divergent = [r for r in rows if r.get("jaccard", 1.0) < 1.0
                 and (r.get("state_top") or []) != (r.get("base_top") or [])]
    sample = divergent[-limit:]
    print(f"euclidean grading: {len(divergent)} divergent rows in the shadow; grading the most recent {len(sample)}.")
    print(f"  judge: {MODEL} (Emissary, CPU) · BLIND A/B · decoupled\n")
    grades = []
    async with aiohttp.ClientSession() as session:
        for i, row in enumerate(sample):
            g = await _grade(session, row, i)
            if g:
                grades.append(g)
                if len(grades) % 10 == 0:
                    print(f"  ...{len(grades)} graded")
    if not grades:
        print("no grades (judge lane unreachable?).")
        return
    # ── the verdict ──
    import statistics as st
    n = len(grades)
    sw = sum(1 for g in grades if g["winner"] == "state")
    bw = sum(1 for g in grades if g["winner"] == "baseline")
    tie = n - sw - bw
    decisive = sw + bw
    print(f"\n{'='*66}\n  VERDICT — did state-weighted recall EARN its divergence? (n={n})\n{'='*66}")
    print(f"  state-weighted MORE relevant : {sw:>3}  ({round(100*sw/n)}%)")
    print(f"  baseline (cosine) MORE relev.: {bw:>3}  ({round(100*bw/n)}%)")
    print(f"  equal                        : {tie:>3}  ({round(100*tie/n)}%)")
    if decisive:
        print(f"  → of the {decisive} decisive calls, state won {round(100*sw/decisive)}%")
    # split by affect_w — the diagnostic the plan needs
    aws = [g["affect_w"] for g in grades if isinstance(g.get("affect_w"), (int, float))]
    if aws:
        med = st.median(aws)
        hi = [g for g in grades if isinstance(g.get("affect_w"), (int, float)) and g["affect_w"] >= med]
        lo = [g for g in grades if isinstance(g.get("affect_w"), (int, float)) and g["affect_w"] < med]
        def _rate(gg):
            d = sum(1 for g in gg if g["winner"] in ("state", "baseline"))
            s = sum(1 for g in gg if g["winner"] == "state")
            return f"{round(100*s/d)}% state" if d else "n/a"
        print(f"\n  SPLIT BY affect weight (median {round(med,2)} — the affect_match dimension's influence):")
        print(f"    HIGH affect_w (charged states, n={len(hi)}): {_rate(hi)}  ← runs on the +0.82 wallpaper")
        print(f"    LOW  affect_w (calm states,   n={len(lo)}): {_rate(lo)}")
        print(f"    (if HIGH << LOW, the affect dimension is the weak link → euclidean waits on emotion_rethink P1)")
    print("\n  sample reasons:")
    for g in grades[:4]:
        print(f"    [{g['winner']:>8}] {g['why']}")
    try:
        import time
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "n": n, "state": sw, "baseline": bw,
                                "tie": tie, "grades": grades}, ensure_ascii=False) + "\n")
        print(f"\n  [logged to {out}]")
    except Exception as exc:
        print(f"  [log failed: {exc}]")


if __name__ == "__main__":
    argv = sys.argv[1:]
    out_override: Path | None = None
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv):
            print("usage: euclidean_grade.py [N] [--out PATH]"); sys.exit(1)
        out_override = Path(argv[i + 1])
        del argv[i:i + 2]
    lim = int(argv[0]) if argv and argv[0].isdigit() else 60
    asyncio.run(main(lim, out_path=out_override))
