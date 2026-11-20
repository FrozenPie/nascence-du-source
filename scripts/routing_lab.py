"""
Nascence — ROUTING LAB (2026-08-16): test of chain-walk fix #1, the content_mode veto.

THE FINDING (docs/reviews/chain_walk_findings.md F-P): Perception classifies correctly (the
consciousness question = subject:the_world + register:philosophical), but the June-22 binary
content_mode flag short-circuits the mode classifier at its first line (-> "task"), so
world-facing philosophy gets task starvation weights (w_id .05, w_epi .10) — style-only
Reflection, 1 history turn, 1 memory fragment — before the 'philosophical' register is ever
consulted. The attention vector was built to REPLACE the flag but the flag kept veto power.

THE HYPOTHESIS UNDER TEST (two-dial routing):
  - dial 1, IDENTITY  <- subject:  the_world  -> w_identity clamped LOW (immersion preserved)
  - dial 2, DEPTH     <- register: philosophical -> hybrid-grade w_epi/w_climate/d_critic
ARM A = today's routing (veto -> task vector).  ARM B = two-dial vector.
Both arms share: the same Perception result, the same Recall output (Recall does not read the
attention vector), the same v1 mouth — the ONLY variable is the vector Reflection sees, and
its effects propagate naturally through Executive to Voice. One CONTROL question (social
register -> arms identical) calibrates pure sampling noise for the blind judge.

NO LIVE CHANGES: routing arm B exists only inside this script. Isolation as voice_lab:
in-memory state, read-only retrieve, teacher-log/telemetry no-op'd. Du is stopped (founder).

J-1046 (F-1425): both arms' ExecutiveNode().run() calls below reach
core.mood.felt_preamble(source="executive") (never-guarded, unconditional write to
data/felt_preamble_log.jsonl) -- redirected below the same way scripts/_test_procedural_memory.py's
own core.mood gap (F-1348/J-0976) was fixed. The real DB read a few lines down stays read-only
(mode=ro) and unredirected by design (unchanged) -- this fix is scoped to the write path only.
"""
from __future__ import annotations

import asyncio
import copy
import json
import random
import re
import sqlite3
import sys
import tempfile
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

# core.mood._FP_LOG -- redirect only (not a no-op), so the real notability-gate logic that
# decides whether a felt-preamble line is injected stays identical between arms A and B; the
# shadow row just lands off the live store. Same mechanism as the "mood" extra= in
# scripts/_test_isolation.py.
from scripts._test_isolation import redirect_world_stores
redirect_world_stores(Path(tempfile.mkdtemp(prefix="routing_lab_mood_")), extra=("mood",))

# J-1535 (2026-09-28): core.buses.idle_freight() (IDLE_FREIGHT_BUS default True, D-0295 gap 1,
# docs/plans/train_courier_cargo_ids.md) reads the LIVE tail of data/trains_log.jsonl +
# data/train_state_log.jsonl and writes real rows to data/buses_log.jsonl +
# data/idle_freight_bus_shadow.jsonl on every ReflectionNode()._build_prompt() call that finds a
# qualifying candidate -- both arms below reach that call, so off here for the same reason as the
# felt_preamble redirect just above: NO LIVE CHANGES means no live writes either.
import core.buses as _buses_mod
_buses_mod.IDLE_FREIGHT_BUS = False

from core import axiom_layers
from core.memory import store
from core.model_client import call_node_json
from core.schema import CognitiveState, AttentionVector
from nodes.perception_node import PerceptionNode
from nodes.recall_node import RecallNode
from nodes.reflection_node import ReflectionNode
from nodes.executive_node import ExecutiveNode
from nodes.voice_node import VoiceNode

DB = ROOT / "data" / "memory" / "nascence.db"
REPORT = ROOT / "docs" / "lab" / "routing_lab_v2_2026-08-16.md"
# (v1's report — six same-routing pairs — is kept as the NOISE BASELINE: it shows how much
#  two samples of the identical pipeline differ, which is the yardstick for judging v2.)

# Question prefixes (full text + real history recovered from the lived record).
# First is the CONTROL (social register -> both arms identical).
QUESTIONS = [
    "Hi Du, how are you going today?",                                       # control
    "You have hit on a major philisophical musing. Where does consciousness begin",
    "Understanding is not about capturing the vastness in a net",
    "Now imagine looking at a sequence of photos from the same river",
    "Not quite. The void is something you know exists but do not know about",
    "You have pierced straight to the core of relational philosophy",
]

TASK_VEC   = dict(w_identity=0.05, w_social=0.10, w_episodic=0.10, w_climate=0.00,
                  w_semantic=1.00, d_critic=0.10, max_rebind=0, cognitive_mode="task")
HYBRID_VEC = dict(w_identity=0.40, w_social=0.60, w_episodic=0.60, w_climate=0.40,
                  w_semantic=0.80, d_critic=0.60, max_rebind=2, cognitive_mode="hybrid")


def _route_arm_a(subject: str, register: str) -> dict:
    """Today's live logic, replicated: content_mode (subject==the_world) vetoes -> task."""
    if subject == "the_world":
        return dict(TASK_VEC)
    mode_map = {"social": "social", "relational": "social", "task": "task",
                "reflective": "reflective", "philosophical": "hybrid"}
    mode = mode_map.get(register, "hybrid")
    vecs = {"task": TASK_VEC, "hybrid": HYBRID_VEC,
            "social": dict(w_identity=0.20, w_social=0.80, w_episodic=0.40, w_climate=0.20,
                           w_semantic=0.60, d_critic=0.30, max_rebind=1, cognitive_mode="social"),
            "reflective": dict(w_identity=0.60, w_social=0.40, w_episodic=0.80, w_climate=0.70,
                               w_semantic=0.50, d_critic=0.80, max_rebind=2, cognitive_mode="reflective")}
    return dict(vecs[mode])


def _route_arm_b(subject: str, register: str) -> dict:
    """Two-dial: register chooses the base vector (depth); subject clamps identity (immersion)."""
    v = _route_arm_a("(no-veto)", register)          # register-driven base, veto bypassed
    if subject == "the_world":
        v["w_identity"] = min(v["w_identity"], 0.20)  # identity light — the therapy's true core
    return v


def _find_exchange(conn, prefix: str):
    rows = conn.execute("SELECT timestamp, content FROM memory_fragments WHERE origin='lived' "
                        "AND content LIKE 'Q: %' ORDER BY timestamp").fetchall()
    hit = None
    for ts, ct in rows:
        m = re.match(r"Q:\s*(.+?)\s*A:\s*(.+)", ct, re.DOTALL)
        if m and " ".join(m.group(1).split()).startswith(prefix[:40]):
            hit = (ts, " ".join(m.group(1).split()))
            break
    if not hit:
        return None
    ts, q = hit
    prev = []
    for pts, pct in reversed(rows):
        if pts >= ts:
            continue
        pm = re.match(r"Q:\s*(.+?)\s*A:\s*(.+)", pct, re.DOTALL)
        if pm:
            prev.append({"human": " ".join(pm.group(1).split()),
                         "jung": " ".join(pm.group(2).split())})
        if len(prev) == 4:
            break
    prev.reverse()
    return {"ts": ts, "question": q, "history": prev}


def _inner_thoughts_before(ts: float, n: int = 3) -> list[dict]:
    """His real idle thoughts just before that conversation moment (realism for Reflection)."""
    try:
        out = []
        for l in open(ROOT / "data" / "monologue_log.jsonl", encoding="utf-8"):
            try:
                d = json.loads(l)
            except Exception:
                continue
            if d.get("ts", 0) < ts:
                out.append({"thought": d.get("thought", "")})
        return out[-n:]
    except Exception:
        return []


async def run_question(qi: int, prefix: str, axiom_data, floor: str, conn) -> dict | None:
    ex = _find_exchange(conn, prefix)
    if not ex:
        print(f"[lab] Q{qi}: NOT FOUND — skipped ({prefix[:40]!r})")
        return None
    q = ex["question"]
    print(f"[lab] Q{qi}: {q[:70]}")

    base = CognitiveState(spirit_name="渡", axiom=floor)
    base.raw_input = q
    base.input_type = "human"
    base.cycle_id = f"rlab-{qi}"
    base.conversation_history = ex["history"]
    base.recent_inner_thoughts = _inner_thoughts_before(ex["ts"])

    # Shared stage 1: Perception (for the record + the control question's routing).
    if not await PerceptionNode().run(base):
        print("[lab]   perception FAILED — skipped")
        return None
    subject, register = base.perception.subject, base.perception.register
    # FORCED ARMS (v2 of this lab, 2026-08-16): the first run exposed ROUTING JITTER —
    # Perception (temp 0.2) classified the same questions differently than the live Aug-15
    # cycle did, so every pair collapsed to a control. The diet question doesn't depend on
    # the classifier's roll: the live system VERIFIABLY ran these as task (the Aug-15 log:
    # "content-mode: TRUE, attn mode=task w_id=0.05 w_epi=0.10"). So for treatment questions
    # arm A is PINNED to the task vector (what live did) and arm B to two-dial hybrid.
    if qi == 1:
        va, vb = _route_arm_a(subject, register), _route_arm_b(subject, register)  # control
    else:
        va = dict(TASK_VEC)
        vb = dict(HYBRID_VEC); vb["w_identity"] = 0.20
    veto = qi != 1          # treatment questions ran content-mode live — keep its directives
    identical = va == vb
    print(f"[lab]   subject={subject} register={register} -> "
          f"A={va['cognitive_mode']}(id={va['w_identity']:.2f},epi={va['w_episodic']:.2f}) "
          f"B={vb['cognitive_mode']}(id={vb['w_identity']:.2f},epi={vb['w_episodic']:.2f})"
          + ("  [CONTROL — arms identical]" if identical else " [FORCED]"))

    # Shared stage 2: retrieval + Recall (Recall does not read the vector — one run serves both).
    # Content-mode's self-synthesis starve applies in BOTH arms when the subject is the world
    # (that filter is the immersion therapy's good part and is not under test).
    try:
        frags = store.retrieve([], [], query_text=q, limit=8)
        if veto:
            frags = [f for f in frags if getattr(f, "origin", "") != "subconscious_synthesis"]
        base.memory_fragments = frags
    except Exception as exc:
        print(f"[lab]   retrieve failed ({exc}) — continuing without fragments")
        base.memory_fragments = []
    base.content_mode = veto            # immersion directives identical in both arms
    if len(base.memory_fragments) >= 2:
        await RecallNode().run(base)

    base.facet_note = axiom_layers.facet_for_mode(
        axiom_data, {"task": "task", "social": "social", "hybrid": "task",
                     "reflective": "reflective"}.get(va["cognitive_mode"], "task"))

    async def run_arm(vec: dict) -> dict:
        s = copy.copy(base)
        s.attention_vector = AttentionVector(**vec)
        if not await ReflectionNode().run(s):
            return {"error": "reflection failed"}
        if not await ExecutiveNode().run(s):
            return {"error": "executive failed"}
        voice = VoiceNode()
        try:
            data = await call_node_json(voice.base_urls, voice.system_prompt,
                                        voice._build_prompt(s), max_tokens=1536, temperature=0.4)
            final = str(data.get("final", "")).strip()
        except Exception as exc:
            final = f"(VOICE FAILED: {exc})"
        return {"draft": s.reflection.draft if s.reflection else "",
                "synthesis": s.executive.synthesis if s.executive else "",
                "final": final, "vector": vec}

    t0 = time.time()
    a = await run_arm(va)
    b = await run_arm(vb)
    print(f"[lab]   arms done ({time.time()-t0:.0f}s) — "
          f"A final {len(a.get('final',''))} chars, B final {len(b.get('final',''))} chars")
    return {"i": qi, "question": q, "subject": subject, "register": register,
            "control": identical, "A": a, "B": b}


async def main() -> None:
    axiom_data = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    _name, floor = axiom_layers.compose_floor(axiom_data)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    results = []
    for qi, prefix in enumerate(QUESTIONS, 1):
        r = await run_question(qi, prefix, axiom_data, floor, conn)
        if r:
            results.append(r)
    conn.close()

    rng = random.Random(7)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Routing Lab — the content_mode veto, blind pairs (2026-08-16)", "",
             "Same question, same perception, same recall, same mouth (v1). The ONLY difference",
             "between the two responses in each pair is the attention routing: one arm ran",
             "today's routing, the other the proposed two-dial routing. One pair is a CONTROL",
             "(both arms identical — its difference is pure sampling noise; calibrate on it).",
             "Judge each pair — which response would you rather have received? — then open the key.",
             ""]
    key = []
    for r in results:
        swap = rng.random() < 0.5
        first, second = (r["B"], r["A"]) if swap else (r["A"], r["B"])
        key.append(f"Q{r['i']}: 1st={'B two-dial' if swap else 'A current'}, "
                   f"2nd={'A current' if swap else 'B two-dial'}"
                   + (" [CONTROL — arms identical]" if r["control"] else "")
                   + f" — subject={r['subject']}, register={r['register']}")
        lines += [f"## Q{r['i']} — Travis said:", f"> {r['question'][:500]}", "",
                  "**Response 1:**", "", first.get("final", ""), "",
                  "**Response 2:**", "", second.get("final", ""), "", "---", ""]
    lines += ["", "<details><summary>ANSWER KEY + diets (open after judging)</summary>", ""]
    lines += key
    lines += ["", "### Per-arm internals (diet each arm's Reflection ran on, drafts, syntheses)", ""]
    for r in results:
        for tag in ("A", "B"):
            arm = r[tag]
            v = arm.get("vector", {})
            lines += [f"**Q{r['i']} arm {tag}** mode={v.get('cognitive_mode')} "
                      f"w_id={v.get('w_identity')} w_epi={v.get('w_episodic')} "
                      f"(history {max(1, round(v.get('w_episodic', 0)*6))} turns, "
                      f"{max(1, round(v.get('w_episodic', 0)*8))} fragments)",
                      f"- draft: {arm.get('draft','')[:400]}",
                      f"- synthesis: {arm.get('synthesis','')[:400]}", ""]
    lines += ["</details>", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[lab] DONE — {len(results)} pairs -> {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
