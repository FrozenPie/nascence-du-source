"""
Nascence — VOICE LAB (2026-08-16): offline A/B of the mouth prompt, v1 (pre-Nascence skeleton)
vs v2 (the diegetic mouth). Founder-designed test: replay REAL past questions from Travis,
produce ONE fresh synthesis per question through the real reflection→executive stages, then
render that same synthesis through BOTH voice prompts. Blind-randomized pairs; answer key at
the bottom of the report. Travis is the judge.

ISOLATION (the law): no live-store writes. All stages used here write only to in-memory state;
retrieve() is read-only; the teacher-example log and telemetry are no-op'd for this process.
The live Du process is untouched (this script shares only the gemma serving lane).

J-1046 (F-1425): this script constructs a real ExecutiveNode() and calls .run() on it (line
~117 below), which reaches core.mood.felt_preamble(source="executive") via
nodes/executive_node.py's own unconditional call inside _build_prompt() -- a never-guarded
write to data/felt_preamble_log.jsonl that the "no live-store writes" law above did not
originally account for. Redirected below the same way scripts/_test_procedural_memory.py's
own core.mood gap (F-1348/J-0976) was fixed.
"""
from __future__ import annotations

import asyncio
import json
import random
import re
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")   # the charmap law
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── neutralise the two write paths before any node import is USED ────────────────────────────
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

# core.mood._FP_LOG (felt_preamble_log.jsonl) -- never-guarded, reached by ExecutiveNode().run()
# below (J-1046/F-1425). Redirect only, not a no-op: preserves the real notability-gate logic
# (which line, if any, gets injected into the executive prompt) while keeping the shadow row
# off the live store, same mechanism _test_procedural_memory.py uses via the "mood" extra=.
from scripts._test_isolation import redirect_world_stores
redirect_world_stores(Path(tempfile.mkdtemp(prefix="voice_lab_mood_")), extra=("mood",))

from core import axiom_layers
from core.memory import store
from core.model_client import call_node_json
from core.schema import CognitiveState
from nodes.reflection_node import ReflectionNode
from nodes.executive_node import ExecutiveNode
from nodes.voice_node import VoiceNode

DB = ROOT / "data" / "memory" / "nascence.db"
REPORT = ROOT / "docs" / "lab" / "voice_lab_2026-08-16.md"

# The eight questions: (distinctive prefix to find the full text, cognitive mode for the facet)
QUESTIONS = [
    ("Hi Du, how are you going today?",                          "social"),
    ("How are you feeling today Du? Any concerns",               "reflective"),
    ("The self is not the body. If I lost an arm",               "existential"),
    ("You have hit on a major philisophical musing. Where does consciousness begin", "task"),
    ("Now imagine looking at a sequence of photos from the same river", "task"),
    ("We have added two books to your library Du",               "social"),
    ("Du, you have swung from one extreme to the other",         "task"),
    ("Understanding is not about capturing the vastness in a net", "task"),
]


def _find_exchange(conn, prefix: str):
    """The full Q/A lived fragment matching the prefix, + the two exchanges before it."""
    rows = conn.execute(
        "SELECT timestamp, content FROM memory_fragments WHERE origin='lived' "
        "AND content LIKE 'Q: %' ORDER BY timestamp").fetchall()
    hit = None
    for ts, ct in rows:
        m = re.match(r"Q:\s*(.+?)\s*A:\s*(.+)", ct, re.DOTALL)
        if m and " ".join(m.group(1).split()).startswith(prefix[:40]):
            hit = (ts, " ".join(m.group(1).split()), " ".join(m.group(2).split()))
            break
    if not hit:
        return None
    ts, q, a = hit
    prev = []
    for pts, pct in reversed(rows):
        if pts >= ts:
            continue
        pm = re.match(r"Q:\s*(.+?)\s*A:\s*(.+)", pct, re.DOTALL)
        if pm:
            prev.append({"human": " ".join(pm.group(1).split()),
                         "jung": " ".join(pm.group(2).split())})
        if len(prev) == 2:
            break
    prev.reverse()
    return {"ts": ts, "question": q, "history": prev,
            "recent_replies": [p["jung"] for p in prev]}


async def run_one(i: int, spec, axiom_data, floor: str, conn) -> dict | None:
    prefix, mode = spec
    ex = _find_exchange(conn, prefix)
    if not ex:
        print(f"[lab] Q{i}: NOT FOUND for prefix {prefix[:40]!r} — skipped")
        return None
    q = ex["question"]
    print(f"[lab] Q{i}: {q[:70]}")

    state = CognitiveState(spirit_name="渡", axiom=floor)
    state.raw_input = q
    state.input_type = "human"
    state.cycle_id = f"lab-{i}"
    state.conversation_history = ex["history"]
    state.facet_note = axiom_layers.facet_for_mode(axiom_data, mode)
    state.recent_voice_replies = ex["recent_replies"]
    try:
        state.memory_fragments = store.retrieve([], [], query_text=q, limit=8)
    except Exception as exc:
        print(f"[lab]   retrieve failed ({exc}) — continuing without fragments")
        state.memory_fragments = []

    t0 = time.time()
    refl = ReflectionNode()
    if not await refl.run(state):
        print(f"[lab]   reflection FAILED — skipped")
        return None
    execu = ExecutiveNode()
    if not await execu.run(state):
        print(f"[lab]   executive FAILED — skipped")
        return None
    synthesis = state.executive.synthesis if state.executive else ""
    print(f"[lab]   synthesis ready ({len(synthesis)} chars, {time.time()-t0:.0f}s)")

    voice = VoiceNode()
    temp = 0.4                      # same fixed temperature for both mouths — fair race
    outs = {}
    # v1 referenced EXPLICITLY since the 2026-08-21 promotion: `voice.system_prompt` now IS v2, so
    # the old tuple would silently compare v2 against itself.
    for tag, sysm, user in (("v1", voice.system_prompt_v1, voice._build_prompt_v1(state)),
                            ("v2", voice.system_prompt_v2, voice._build_prompt_v2(state))):
        try:
            data = await call_node_json(voice.base_urls, sysm, user,
                                        max_tokens=1536, temperature=temp)
            outs[tag] = str(data.get("final", "")).strip()
        except Exception as exc:
            outs[tag] = f"(GENERATION FAILED: {exc})"
        print(f"[lab]   {tag}: {len(outs[tag])} chars")
    return {"i": i, "question": q, "synthesis": synthesis, **outs}


async def main() -> None:
    axiom_data = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    _name, floor = axiom_layers.compose_floor(axiom_data)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    results = []
    for i, spec in enumerate(QUESTIONS, 1):
        r = await run_one(i, spec, axiom_data, floor, conn)
        if r:
            results.append(r)
    conn.close()

    rng = random.Random(42)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Voice Lab — blind pairs (2026-08-16)",
             "",
             "Same question, same freshly-produced synthesis, two mouths. For each pair: which",
             "response sounds more like 渡 speaking to you? Judge before reading the key at the bottom.",
             ""]
    key = []
    for r in results:
        first_is_v2 = rng.random() < 0.5
        A = r["v2"] if first_is_v2 else r["v1"]
        B = r["v1"] if first_is_v2 else r["v2"]
        key.append(f"Q{r['i']}: A={'v2' if first_is_v2 else 'v1'}, B={'v2' if not first_is_v2 else 'v1'}")
        lines += [f"## Q{r['i']} — Travis said:",
                  f"> {r['question']}",
                  "",
                  f"**Response A:**",
                  "", A, "",
                  f"**Response B:**",
                  "", B, "",
                  "---", ""]
    lines += ["", "<details><summary>ANSWER KEY (open after judging)</summary>", ""]
    lines += key
    lines += ["", "</details>", ""]
    lines += ["## The syntheses (for fidelity checking — both mouths had to render exactly this)", ""]
    for r in results:
        lines += [f"**Q{r['i']} synthesis:** {r['synthesis'][:900]}", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[lab] DONE — {len(results)} pairs -> {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
