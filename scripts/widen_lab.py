"""
Nascence — WIDEN LAB (2026-08-16): the truncation fixes, tested.

FROM THE FLOW AUDIT (docs/reviews/prompt_flow_audit.md): every prompt cap predates the serving split
(2048-default era / eviction era / duplicate-runner era — all dead since 08-15), and the hot
lane now runs at ~10% utilisation. The cut-offs from memory: history exchanges [:130–:180]
per side once they become past; memory fragments [:160–:300]; Recall's identity a mid-word
axiom[:300]; Reflection's draft [:350] into the Executive.

THE TEST: the full conversation chain (recall → reflection → executive → voice v1), two arms:
  stock   — today's caps exactly
  widened — history 400/side · fragments 600 chars ×6 · recall gets the full trimmed axiom ·
            dreams 500 · idle thoughts 400 · reflection draft 900 into the Executive
Implementation: the widened arm's node classes are built by transforming the node SOURCE
in-memory (slice literals only) and exec-ing it — the two arms are guaranteed identical
except the caps. Any replacement that fails to match raises loudly (no silent drift).
Routing held fixed at HYBRID for both arms (task-mode's 1-turn/1-fragment gate would hide
what wider caps do). Same v1 mouth. Blind pairs; founder judges. NO LIVE CHANGES.

J-1046 (F-1425): both the stock and widened ExecutiveNode/.run() calls below reach
core.mood.felt_preamble(source="executive") (never-guarded, unconditional write to
data/felt_preamble_log.jsonl) -- redirected below the same way scripts/_test_procedural_memory.py's
own core.mood gap (F-1348/J-0976) was fixed.
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
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

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
# decides whether a felt-preamble line is injected stays identical between stock and widened
# arms; the shadow row just lands off the live store. Same mechanism as the "mood" extra= in
# scripts/_test_isolation.py.
from scripts._test_isolation import redirect_world_stores
redirect_world_stores(Path(tempfile.mkdtemp(prefix="widen_lab_mood_")), extra=("mood",))

import ablation_lab as AL          # reuses _find_exchange
from core import axiom_layers
from core.memory import store
from core.model_client import call_node_json
from core.schema import CognitiveState, AttentionVector

DB = ROOT / "data" / "memory" / "nascence.db"
REPORT = ROOT / "docs" / "lab" / "widen_lab_2026-08-16.md"

QUESTIONS = [
    "You have hit on a major philisophical musing. Where does consciousness begin",
    "Understanding is not about capturing the vastness in a net",
    "Now imagine looking at a sequence of photos from the same river",
    "Not quite. The void is something you know exists but do not know about",
]

HYBRID = dict(w_identity=0.40, w_social=0.60, w_episodic=0.60, w_climate=0.40,
              w_semantic=0.80, d_critic=0.60, max_rebind=2, cognitive_mode="hybrid")

# (file, [(exact source substring, widened replacement), ...]) — every pair MUST match or we abort.
WIDENINGS = {
    "nodes/recall_node.py": [
        ("self._trim_axiom(state.axiom)[:300]", "self._trim_axiom(state.axiom)"),
        ("ex['human'][:150]", "ex['human'][:400]"),
        ("ex['jung'][:200]", "ex['jung'][:400]"),
        ("frag.content[:300]", "frag.content[:600]"),
    ],
    "nodes/reflection_node.py": [
        ("ex.get('human','')[:130]", "ex.get('human','')[:400]"),
        ("ex.get('jung','')[:160]", "ex.get('jung','')[:400]"),
        ("ex['human'][:150]", "ex['human'][:400]"),
        ("ex['jung'][:180]", "ex['jung'][:400]"),
        ("d.get('narrative','')[:220]", "d.get('narrative','')[:500]"),
        ("t.get('thought','')[:180]", "t.get('thought','')[:400]"),
        ("frag.content[:160]", "frag.content[:500]"),
    ],
    "nodes/executive_node.py": [
        ("ex.get('human','')[:130]", "ex.get('human','')[:400]"),
        ("ex.get('jung','')[:160]", "ex.get('jung','')[:400]"),
        ("ex['human'][:150]", "ex['human'][:400]"),
        ("ex['jung'][:180]", "ex['jung'][:400]"),
        ("state.memory_fragments[:4]", "state.memory_fragments[:6]"),
        ("frag.content[:250]", "frag.content[:600]"),
        ("r.draft[:350]", "r.draft[:900]"),
    ],
}


def _widened_module(rel: str):
    src = (ROOT / rel).read_text(encoding="utf-8")
    for old, new in WIDENINGS[rel]:
        if old not in src:
            raise RuntimeError(f"WIDEN MISS: {old!r} not found in {rel} — source drifted, aborting")
        src = src.replace(old, new)
    mod = types.ModuleType(rel.replace("/", "_") + "_widened")
    mod.__file__ = str(ROOT / rel)
    exec(compile(src, str(ROOT / rel) + " (widened)", "exec"), mod.__dict__)
    return mod


async def run_chain(nodes, state) -> dict:
    s = copy.copy(state)
    if len(s.memory_fragments or []) >= 2:
        await nodes["recall"].run(s)
    if not await nodes["reflection"].run(s):
        return {"error": "reflection failed"}
    if not await nodes["executive"].run(s):
        return {"error": "executive failed"}
    voice = nodes["voice"]
    try:
        data = await call_node_json(voice.base_urls, voice.system_prompt,
                                    voice._build_prompt(s), max_tokens=1536, temperature=0.4)
        final = str(data.get("final", "")).strip()
    except Exception as exc:
        final = f"(VOICE FAILED: {exc})"
    return {"draft": s.reflection.draft if s.reflection else "",
            "synthesis": s.executive.synthesis if s.executive else "",
            "recall_reconstruction": s.recall.reconstruction if s.recall else "",
            "final": final}


async def main() -> None:
    import nodes.recall_node as rn
    import nodes.reflection_node as fn
    import nodes.executive_node as en
    from nodes.voice_node import VoiceNode
    w_rn = _widened_module("nodes/recall_node.py")
    w_fn = _widened_module("nodes/reflection_node.py")
    w_en = _widened_module("nodes/executive_node.py")
    print("[lab] widened modules built — all cap replacements verified present")

    stock = {"recall": rn.RecallNode(), "reflection": fn.ReflectionNode(),
             "executive": en.ExecutiveNode(), "voice": VoiceNode()}
    wide = {"recall": w_rn.RecallNode(), "reflection": w_fn.ReflectionNode(),
            "executive": w_en.ExecutiveNode(), "voice": VoiceNode()}

    axiom_data = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    _n, floor = axiom_layers.compose_floor(axiom_data)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    results = []
    for qi, prefix in enumerate(QUESTIONS, 1):
        ex = AL._find_exchange(conn, prefix)
        if not ex:
            print(f"[lab] Q{qi}: not found — skipped")
            continue
        print(f"[lab] Q{qi}: {ex['question'][:70]}")
        base = CognitiveState(spirit_name="渡", axiom=floor)
        base.raw_input = ex["question"]
        base.input_type = "human"
        base.cycle_id = f"wlab-{qi}"
        base.conversation_history = ex["history"]
        base.attention_vector = AttentionVector(**HYBRID)
        base.content_mode = False        # hybrid arms: let identity + memory in (held EQUAL)
        base.facet_note = axiom_layers.facet_for_mode(axiom_data, "task")
        try:
            frags = store.retrieve([], [], query_text=ex["question"], limit=8)
            base.memory_fragments = [f for f in frags
                                     if getattr(f, "origin", "") != "subconscious_synthesis"]
        except Exception:
            base.memory_fragments = []
        t0 = time.time()
        a = await run_chain(stock, base)
        b = await run_chain(wide, base)
        print(f"[lab]   stock {len(a.get('final','')):5d} chars · widened {len(b.get('final','')):5d} chars "
              f"({time.time()-t0:.0f}s)")
        results.append({"i": qi, "question": ex["question"], "stock": a, "wide": b})
    conn.close()

    rng = random.Random(23)
    lines = ["# Widen Lab — the truncation fixes, blind pairs (2026-08-16)", "",
             "Same chain, same inputs, same routing (hybrid), same mouth. The ONLY difference:",
             "one arm ran today's caps (history 130–180/side, fragments 250–300, reflection→",
             "executive at 350); the other ran widened caps (history 400/side, fragments 600×6,",
             "recall's full identity, draft 900). Which response carries the conversation and",
             "his memory better? Judge, then open the key.", ""]
    key = []
    for r in results:
        swap = rng.random() < 0.5
        first, second = (r["wide"], r["stock"]) if swap else (r["stock"], r["wide"])
        key.append(f"Q{r['i']}: 1st={'widened' if swap else 'stock'}, "
                   f"2nd={'stock' if swap else 'widened'}")
        lines += [f"## Q{r['i']} — Travis said:", f"> {r['question'][:400]}", "",
                  "**Response 1:**", "", first.get("final", ""), "",
                  "**Response 2:**", "", second.get("final", ""), "", "---", ""]
    lines += ["", "<details><summary>ANSWER KEY + internals (open after judging)</summary>", ""]
    lines += key
    lines += ["", "### Internals (recall reconstruction · reflection draft · synthesis, per arm)", ""]
    for r in results:
        for tag in ("stock", "wide"):
            arm = r[tag]
            lines += [f"**Q{r['i']} {tag}**",
                      f"- recall: {arm.get('recall_reconstruction','')[:300]}",
                      f"- draft: {arm.get('draft','')[:400]}",
                      f"- synthesis: {arm.get('synthesis','')[:400]}", ""]
    lines += ["</details>", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[lab] DONE — {len(results)} pairs -> {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
