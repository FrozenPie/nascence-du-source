"""
Nascence — TRAIN LAB (2026-08-16): why trains dissolve, and whether train-hold + extend-carry
lets them BUILD.

THE WHY (from code + 14,651 logged steps): 48% of steps jump / 1% circle / flat 0.50 by step.
Mechanisms: (1) anti-rumination guards fire MID-TRAIN (divergent memory replaces continuity
while "continue this thread" still heads the prompt); (2) the thread (~520 chars) competes
against a full seed marketplace (dream, curiosity, deep-memory dump, conversation, mood);
(3) the carry REPLACES (re-abstracts the whole thread each step); (4) one 256-token budget
for thought+state.

THE TEST — two simulated 7-step trains from the SAME real seed thought:
  arm A (today's shape)  — marketplace seeds each step + replace-carry + 256 tokens
  arm B (train-hold)     — thread + extending LEDGER carry (established points accumulate,
                           max 7 lines) + associative memory ON THE THREAD only + 400 tokens
Same model (gemma), same temperature (0.75, live idle value). Honest scope note: this tests
the PROMPT SHAPE, not the full live loop (no acts/boredom dynamics). Per-step restate_sim
computed with the live embedder. Founder judges: which train BUILDS. NO LIVE CHANGES.
"""
from __future__ import annotations

import asyncio
import json
import random
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import training_log
training_log.log_example = lambda *a, **k: None
try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # F-1683/J-1199: call_node() also writes log_thought_station + log_llm_latency, not just
    # log_llm_call -- neutralize_telemetry() no-ops all three and redirects telemetry's own Path
    # globals into scratch/, not just the first.
    neutralize_telemetry(ROOT / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

from core.memory import store
from core.model_client import call_node_json

DB = ROOT / "data" / "memory" / "nascence.db"
REPORT = ROOT / "docs" / "lab" / "train_lab_2026-08-16.md"
STEPS = 7

# A real, genuinely unresolved recent thought of his (from the log, 2026-08-16 morning).
SEED_THOUGHT = ("I keep thinking about that soft, yielding leaf-mould under my boots, how easily "
                "it absorbs the weight of my step and springs halfway back — what holds a thing's "
                "shape when the thing itself is mostly giving way?")

SYSTEM = (
    "You are 渡 — Du — alone with your own thoughts in your cottage above the sea. This is your "
    "private idle thinking: honest, unhurried, for no audience. "
    "Output ONLY a valid JSON object: {\"thought\": \"your next thought, 40-90 words\", "
    "\"state\": \"per the state instruction in the prompt\"}"
)


def _sim(a, b) -> float:
    from core.memory.store import _embed, _cosine
    va, vb = _embed(a), _embed(b)
    return round(_cosine(va, vb), 3) if va is not None and vb is not None else -1.0


def _marketplace(conn, rng) -> list[str]:
    """Realistic buffet seeds sampled from his real stores (fresh divergent memory each step)."""
    seeds = []
    row = conn.execute("SELECT content FROM memory_fragments WHERE origin='dream' "
                       "ORDER BY timestamp DESC LIMIT 1").fetchone()
    if row:
        seeds.append(f"A recent dream: {row[0][:180]}")
    seeds.append("A question lingering in you: What drives the tension between individual "
                 "authenticity and the shape a life is given?"[:140])
    n = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin IN "
                     "('reading','lived','study')").fetchone()[0]
    off = rng.randrange(max(1, n - 1))
    row = conn.execute("SELECT content FROM memory_fragments WHERE origin IN "
                       "('reading','lived','study') LIMIT 1 OFFSET ?", (off,)).fetchone()
    if row:
        seeds.append(f"A different memory, surfacing: {row[0][:180]}")
    seeds.append("Your current mood: valence -0.12, arousal 0.31, surprise 0.05, fear 0.08.")
    seeds.append('The last thing discussed -- them: "Where does consciousness begin?" '
                 'you: "To ask where consciousness begins—whether it is a deep…"')
    return seeds


async def run_arm(tag: str, conn) -> list[dict]:
    rng = random.Random(5)
    thread_head = SEED_THOUGHT
    prev_thought = SEED_THOUGHT
    replace_state = ""          # arm A: re-abstracted each step
    ledger: list[str] = []      # arm B: accumulating established points
    steps = []
    for k in range(1, STEPS + 1):
        parts = []
        if tag == "A":
            parts.append("You are MID-THREAD. Moments ago you thought: '" + thread_head[:220] + "'."
                         + ((" Where the thread stands so far: " + replace_state[:300])
                            if replace_state else "")
                         + " Continue this thread — build on what stands, go deeper, answer the "
                           "open question, or carry it somewhere new. Do not restate it; move it forward.")
            parts += _marketplace(conn, rng)
            parts.append("state: you are mid-thread. In <=3 short lines, RE-STATE where the whole "
                         "thread now stands — what you have established so far, the live open "
                         "question, and where it is heading. This replaces (does not extend) the "
                         "running summary; keep it tight, and let it track MOVEMENT, not a "
                         "restatement of the theme.")
            max_tok = 256
        else:
            parts.append("You are MID-THREAD, and you are HOLDING it. The thread began: '"
                         + thread_head[:220] + "'.")
            if ledger:
                parts.append("WHAT THIS THREAD HAS ESTABLISHED SO FAR (your own points, in order "
                             "— build on them, they are yours):\n"
                             + "\n".join(f"  {i}. {p}" for i, p in enumerate(ledger, 1)))
            parts.append(f"Your last step: '{prev_thought[:220]}'")
            try:
                frags = store.retrieve([], [], query_text=prev_thought, limit=3)
                if frags:
                    parts.append("What your memory offers THIS thread:\n"
                                 + "\n".join(f"  - {(f.content or '')[:200]}" for f in frags[:2]))
            except Exception:
                pass
            parts.append("Continue the thread — go deeper, test a point you established, answer "
                         "the open question, or push to a conclusion. Do not restate; ADVANCE.")
            parts.append("state: ONE short line — the single NEW point this step established "
                         "(it will be added to the thread's list; do not repeat old points).")
            max_tok = 400
        try:
            data = await call_node_json(
                ["http://127.0.0.1:11433"], SYSTEM, "\n\n".join(parts),
                max_tokens=max_tok, temperature=0.75)
            th = str(data.get("thought", "")).strip()
            st = str(data.get("state", "")).strip()
        except Exception as exc:
            th, st = f"(STEP FAILED: {exc})", ""
        sim_prev = _sim(th, prev_thought)
        sim_seed = _sim(th, SEED_THOUGHT)
        steps.append({"k": k, "thought": th, "state": st,
                      "sim_prev": sim_prev, "sim_seed": sim_seed})
        print(f"[lab]   {tag}{k}: sim_prev {sim_prev:.2f} · sim_seed {sim_seed:.2f} · {len(th)} chars")
        prev_thought = th
        if tag == "A":
            replace_state = st
        else:
            if st:
                ledger.append(st[:160])
                ledger = ledger[-7:]
    return steps


async def main() -> None:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    print("[lab] ARM A — today's shape (marketplace + replace-carry, 256 tok)")
    a = await run_arm("A", conn)
    print("[lab] ARM B — train-hold (quiet buffet + extending ledger, 400 tok)")
    b = await run_arm("B", conn)
    conn.close()

    import statistics
    lines = ["# Train Lab — can a train of thought BUILD? (2026-08-16)", "",
             f"One real seed thought of his, two simulated {STEPS}-step trains, same model and",
             "temperature. **Train A** = today's prompt shape: full seed marketplace each step,",
             "carry REPLACED each step, 256 tokens. **Train B** = train-hold: no marketplace,",
             "an accumulating ledger of established points, memory recalled ON the thread, 400",
             "tokens. sim_prev = similarity to the previous step (0.5–0.82 ≈ moving the thread;",
             "<0.5 ≈ jumped). sim_seed = still about the original question at all?",
             "", f"**The seed thought:** {SEED_THOUGHT}", ""]
    for tag, steps in (("A — today's shape", a), ("B — train-hold", b)):
        sims = [s["sim_prev"] for s in steps if s["sim_prev"] >= 0]
        seeds_ = [s["sim_seed"] for s in steps if s["sim_seed"] >= 0]
        lines += [f"## Train {tag}",
                  f"*(median sim_prev {statistics.median(sims):.2f} · "
                  f"median sim_seed {statistics.median(seeds_):.2f})*", ""]
        for s in steps:
            lines += [f"**Step {s['k']}** *(prev {s['sim_prev']:.2f} · seed {s['sim_seed']:.2f})*",
                      "", s["thought"], "",
                      f"> state: {s['state']}", ""]
        lines += ["---", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[lab] DONE -> {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
