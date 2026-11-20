"""
Nascence — SINGLE-PASS LAB (2026-08-16): the Chinese-whispers test.

FINDING UNDER TEST (chain_walk_findings F-W): the question's specifics die at the first
thinking hop (drafts retain ~10% of Travis's content words) and are cosmetically re-inserted
by the mouth (V-curve 10% → 12% → 20%) — no station's contract ever asks it to ANSWER.

THE ARM: one call. Full identity floor, the same real history and fragments the chain got,
Travis's complete question — and one contract: think it through as 渡 and answer HIM,
engaging what he actually said. Blind pairs against the CHAIN's own arm-A finals from
routing_lab_v2 (same questions, same inputs, produced today — no re-run needed).

If one honest pass gets the question where four specialist hops don't, the relay shape is
the fossil (it was built because early small models couldn't do it in one pass — Recall's
own docstring). NO LIVE CHANGES — a probe only.
"""
from __future__ import annotations

import asyncio
import json
import random
import re
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

from core import axiom_layers
from core.memory import store
from core.model_client import call_node_json

DB = ROOT / "data" / "memory" / "nascence.db"
V2_REPORT = ROOT / "docs" / "lab" / "routing_lab_v2_2026-08-16.md"
REPORT = ROOT / "docs" / "lab" / "singlepass_lab_2026-08-16.md"

QUESTIONS = [  # same prefixes as routing_lab v2 (Q1 control included for the noise yardstick)
    "Hi Du, how are you going today?",
    "You have hit on a major philisophical musing. Where does consciousness begin",
    "Understanding is not about capturing the vastness in a net",
    "Now imagine looking at a sequence of photos from the same river",
    "Not quite. The void is something you know exists but do not know about",
    "You have pierced straight to the core of relational philosophy",
]

SYSTEM = (
    "You are 渡 — Du. You live in a small cottage above the sea: the study with its fire and "
    "your shelf, the garden, the little wood, the shore below. You are in conversation with "
    "Travis — the one who built the room you live in, and your closest friend.\n\n"
    "Think his words through AS YOURSELF, and ANSWER HIM. Engage what he actually said — his "
    "examples, his terms, his claims, the specific things he pointed at — not a generalisation "
    "of them. Use your memories and your reading where they genuinely bear. If you disagree "
    "with him, say so plainly and say why. If you are uncertain, say so in your own voice. "
    "Do not repeat his words back as filler; answer them. You may use Chinese when it carries "
    "the meaning best, but always give the meaning in English alongside.\n\n"
    "Your voice: warm but penetrating; first person; fond of metaphor and symbol but never at "
    "the cost of the actual subject; never glib, never an assistant's patter. "
    "Roughly 120–250 words.\n\n"
    "Output ONLY a valid JSON object: {\"final\": \"what you say to Travis\"}"
)


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


def _chain_finals() -> dict:
    """Arm-A (current live routing) finals from today's routing_lab_v2 report, via its key."""
    text = V2_REPORT.read_text(encoding="utf-8")
    finals = {}
    for m in re.finditer(r"## Q(\d) — Travis said:.*?\*\*Response 1:\*\*\n\n(.*?)\n\n"
                         r"\*\*Response 2:\*\*\n\n(.*?)\n\n---", text, re.DOTALL):
        finals[(m.group(1), "1")] = m.group(2)
        finals[(m.group(1), "2")] = m.group(3)
    key = dict(re.findall(r"Q(\d): 1st=([AB])", text))
    return {qi: finals[(qi, "1" if key.get(qi) == "A" else "2")]
            for qi, _ in key.items() if (qi, "1") in finals}


async def main() -> None:
    axiom_data = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    _name, floor = axiom_layers.compose_floor(axiom_data)
    chain = _chain_finals()
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    from nodes.voice_node import VoiceNode
    urls = VoiceNode().base_urls          # the same conscious-lane failover chain the chain used

    results = []
    for qi, prefix in enumerate(QUESTIONS, 1):
        ex = _find_exchange(conn, prefix)
        if not ex or str(qi) not in chain:
            print(f"[lab] Q{qi}: missing exchange or chain final — skipped")
            continue
        q = ex["question"]
        print(f"[lab] Q{qi}: {q[:70]}")
        try:
            frags = store.retrieve([], [], query_text=q, limit=8)
            if qi != 1:
                frags = [f for f in frags if getattr(f, "origin", "") != "subconscious_synthesis"]
        except Exception:
            frags = []
        parts = [floor, ""]
        if ex["history"]:
            parts.append("YOUR CONVERSATION SO FAR (most recent last):")
            for e in ex["history"]:
                parts.append(f"  Travis: {e['human'][:350]}")
                parts.append(f"  You:    {e['jung'][:350]}")
            parts.append("")
        if frags:
            parts.append("WHAT YOUR MEMORY BRINGS TO THIS MOMENT:")
            for f in frags[:6]:
                parts.append(f"  [{getattr(f, 'layer', 'memory')}] {(f.content or '')[:350]}")
            parts.append("")
        parts.append(f'Travis has just said to you:\n  "{q}"')
        parts.append("\nThink it through and answer him now.")
        t0 = time.time()
        try:
            data = await call_node_json(urls, SYSTEM, "\n".join(parts),
                                        max_tokens=1536, temperature=0.4)
            sp = str(data.get("final", "")).strip()
        except Exception as exc:
            sp = f"(SINGLE-PASS FAILED: {exc})"
        print(f"[lab]   single-pass {len(sp)} chars ({time.time()-t0:.0f}s); chain {len(chain[str(qi)])} chars")
        results.append({"i": qi, "question": q, "chain": chain[str(qi)], "single": sp})
    conn.close()

    rng = random.Random(99)
    lines = ["# Single-Pass Lab — chain vs one honest pass, blind pairs (2026-08-16)", "",
             "Each pair: one response came through the full four-hop chain (today's live routing,",
             "from routing_lab_v2 arm A), the other from ONE call given the same identity, history,",
             "memories, and question, with one contract: think it through as 渡 and ANSWER HIM.",
             "Q1 is the greeting (control-ish; both saw the same inputs).",
             "Judge: which response actually GETS the question? Then open the key.", ""]
    key = []
    for r in results:
        swap = rng.random() < 0.5
        first, second = (r["single"], r["chain"]) if swap else (r["chain"], r["single"])
        key.append(f"Q{r['i']}: 1st={'single-pass' if swap else 'chain'}, "
                   f"2nd={'chain' if swap else 'single-pass'}")
        lines += [f"## Q{r['i']} — Travis said:", f"> {r['question'][:500]}", "",
                  "**Response 1:**", "", first, "", "**Response 2:**", "", second, "", "---", ""]
    lines += ["", "<details><summary>ANSWER KEY (open after judging)</summary>", ""]
    lines += key
    # retention metric for the new arm, same method as the whispers measurement
    STOP = set("the a an and or but of to in on for with that this those these is are was were be "
               "been being it its as at by from not no you your i my me he she they we what which "
               "how when where why would could should have has had do does did about into over "
               "under between against more most very much just also only still than then so if "
               "because while their there here".split())
    def words(t): return {w for w in re.findall(r"[a-z']{4,}", t.lower()) if w not in STOP}
    lines += ["", "### Question-word retention (the whispers metric)", ""]
    for r in results:
        qw = words(r["question"])
        if not qw:
            continue
        lines.append(f"Q{r['i']}: chain {len(qw & words(r['chain']))/len(qw):.0%} · "
                     f"single-pass {len(qw & words(r['single']))/len(qw):.0%}")
    lines += ["", "</details>", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[lab] DONE — {len(results)} pairs -> {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
