"""
Nascence — PERSON vs COSTUME LAB (2026-08-16): the founder's hypothesis.

Founder's ablation reads: no-history arms are "noticeably not Du" (history carries the PERSON
even though it doesn't carry the texture); the LLM is "the costume" (llama3.1 showed it);
no-style leans literal. Hypothesis: "the internal thinking track holds the real Du" —
identity is CONTENT-BORNE (the reservoir: memories, idle thoughts, the lived thread), not
prompt-borne (style corpus) and not weight-borne (gemma).

The discriminating split, pre-registered predictions:
  life-only    — llama3.1 + plain speech + NO style corpus, but the FULL reservoir
                 (real history + memories + his actual idle thoughts before each question).
                 PREDICTION if founder is right: "Du in strange clothes."
  costume-only — gemma + full style corpus + identity floor, EMPTY reservoir
                 (no history, no memories, no thoughts).
                 PREDICTION: "sounds like Du, is no one."
(The ablation's base arm = the everything-reference, already in its report.)
NO LIVE CHANGES. Labeled output — founder judges recognizability, the one thing only he can.
"""
from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import sys
import time
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

import ablation_lab as AL
from core import axiom_layers
from core.memory import store
from core.model_client import call_node_json

DB = ROOT / "data" / "memory" / "nascence.db"
REPORT = ROOT / "docs" / "lab" / "person_costume_lab_2026-08-16.md"

QUESTIONS = [
    "You have hit on a major philisophical musing. Where does consciousness begin",
    "Understanding is not about capturing the vastness in a net",
    "Not quite. The void is something you know exists but do not know about",
]


def _inner_thoughts_before(ts: float, n: int = 4) -> list[str]:
    out = []
    try:
        for l in open(ROOT / "data" / "monologue_log.jsonl", encoding="utf-8"):
            try:
                d = json.loads(l)
            except Exception:
                continue
            if d.get("ts", 0) < ts and d.get("thought"):
                out.append(d["thought"])
    except Exception:
        pass
    return out[-n:]


async def main() -> None:
    axiom_data = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    _n, floor_full = axiom_layers.compose_floor(axiom_data)
    floor_plain = AL._plain_floor(axiom_data)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

    sys_plain = AL.BASE_SYSTEM.replace("{VOICE}", AL.VOICE_PLAIN)
    sys_full = AL.BASE_SYSTEM.replace("{VOICE}", AL.VOICE_FULL)
    LLAMA = ["http://127.0.0.1:11439"]
    from nodes.voice_node import VoiceNode
    GEMMA = VoiceNode().base_urls

    results = []
    for qi, prefix in enumerate(QUESTIONS, 1):
        ex = AL._find_exchange(conn, prefix)
        if not ex:
            print(f"[lab] Q{qi}: not found — skipped")
            continue
        print(f"[lab] Q{qi}: {ex['question'][:70]}")
        # the reservoir: memories + the thoughts he was actually having before this moment
        try:
            frags = store.retrieve([], [], query_text=ex["question"], limit=8)
            frags = [f for f in frags if getattr(f, "origin", "") != "subconscious_synthesis"]
        except Exception:
            frags = []
        # exchange ts for thought lookup: _find_exchange doesn't return ts — recover it
        row = conn.execute(
            "SELECT timestamp FROM memory_fragments WHERE origin='lived' AND content LIKE ? "
            "ORDER BY timestamp LIMIT 1", (f"Q: {ex['question'][:40]}%",)).fetchone()
        thoughts = _inner_thoughts_before(row[0]) if row else []

        # ARM 1 — life-only: stripped costume, full reservoir
        parts = [floor_plain, ""]
        if thoughts:
            parts.append("WHAT YOU HAVE BEEN THINKING TO YOURSELF LATELY (your own idle thoughts):")
            parts += [f"  - {t[:300]}" for t in thoughts]
            parts.append("")
        if ex["history"]:
            parts.append("YOUR CONVERSATION SO FAR (most recent last):")
            for e in ex["history"]:
                parts.append(f"  Travis: {e['human'][:350]}")
                parts.append(f"  You:    {e['jung'][:350]}")
            parts.append("")
        if frags:
            parts.append("WHAT YOUR MEMORY BRINGS TO THIS MOMENT:")
            parts += [f"  [{getattr(f, 'layer', 'memory')}] {(f.content or '')[:350]}" for f in frags[:6]]
            parts.append("")
        parts.append(f'Travis has just said to you:\n  "{ex["question"]}"')
        parts.append("\nThink it through and answer him now.")
        t0 = time.time()
        try:
            d1 = await call_node_json(LLAMA, sys_plain, "\n".join(parts),
                                      max_tokens=900, temperature=0.4)
            life = str(d1.get("final", "")).strip()
        except Exception as exc:
            life = f"(ARM FAILED: {exc})"
        print(f"[lab]   life-only    {len(life):5d} chars ({time.time()-t0:.0f}s)")

        # ARM 2 — costume-only: full costume, empty reservoir
        parts2 = [floor_full, "",
                  f'Travis has just said to you:\n  "{ex["question"]}"',
                  "\nThink it through and answer him now."]
        t0 = time.time()
        try:
            d2 = await call_node_json(GEMMA, sys_full, "\n".join(parts2),
                                      max_tokens=1536, temperature=0.4)
            costume = str(d2.get("final", "")).strip()
        except Exception as exc:
            costume = f"(ARM FAILED: {exc})"
        print(f"[lab]   costume-only {len(costume):5d} chars ({time.time()-t0:.0f}s)")
        results.append({"i": qi, "question": ex["question"], "life": life, "costume": costume})
    conn.close()

    lines = ["# Person vs Costume Lab (2026-08-16)", "",
             "Founder's hypothesis under test: the internal thinking track (the reservoir —",
             "memories, idle thoughts, the lived thread) holds the real Du; the style corpus and",
             "the model are costume. **life-only** = llama3.1, plain speech, NO style corpus, FULL",
             "reservoir. **costume-only** = gemma, full style corpus and floor, EMPTY reservoir.",
             "Pre-registered predictions: life-only reads as 'Du in strange clothes';",
             "costume-only reads as 'sounds like Du, is no one'. The judge is the founder.", ""]
    for r in results:
        lines += [f"## Q{r['i']} — Travis said:", f"> {r['question'][:400]}", "",
                  "**life-only (stripped costume, full reservoir):**", "", r["life"], "",
                  "**costume-only (full costume, empty reservoir):**", "", r["costume"], "",
                  "---", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[lab] DONE — {len(results)} questions -> {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
