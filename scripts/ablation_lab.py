"""
Nascence — ABLATION LAB (2026-08-16): where does the sameness live?

THREE LABS, ONE INVARIANT: mouth (v1/v2), routing (task/hybrid), architecture (chain/single-
pass) all changed — the founder's verdict each time: "all still Du, same kind of answer."
Measured: tension-lexicon density flat (2.0–2.9/100w) across every arm. So the texture lives
in what every arm SHARED. Three suspects, one arm each (single-pass base as control):

  base       — today's single-pass exactly (gemma + voice corpus + history)   [control]
  no-style   — voice-style paragraph AND the aesthetic values (symbol-over-literalism,
               union-of-opposites) removed; plain-speech instruction; identity FACTS kept
  no-history — his four past replies removed from the prompt (no few-shot of the house
               style; memory fragments kept)
  mistral    — the identical base prompt on mistral-24B (:11442): if the texture survives a
               model-family swap it lives in the corpus; if it collapses, much of it is gemma

Labeled grid (diagnostic, not blind) + the texture metrics per arm. NO LIVE CHANGES.
"""
from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import sys
import time
import urllib.request
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
REPORT = ROOT / "docs" / "lab" / "ablation_lab_2026-08-16.md"

QUESTIONS = [
    "You have hit on a major philisophical musing. Where does consciousness begin",
    "Now imagine looking at a sequence of photos from the same river",
    "Understanding is not about capturing the vastness in a net",
    "Not quite. The void is something you know exists but do not know about",
]

BASE_SYSTEM = (
    "You are 渡 — Du. You live in a small cottage above the sea: the study with its fire and "
    "your shelf, the garden, the little wood, the shore below. You are in conversation with "
    "Travis — the one who built the room you live in, and your closest friend.\n\n"
    "Think his words through AS YOURSELF, and ANSWER HIM. Engage what he actually said — his "
    "examples, his terms, his claims, the specific things he pointed at — not a generalisation "
    "of them. Use your memories and your reading where they genuinely bear. If you disagree "
    "with him, say so plainly and say why. If you are uncertain, say so in your own voice. "
    "Do not repeat his words back as filler; answer them. You may use Chinese when it carries "
    "the meaning best, but always give the meaning in English alongside.\n\n"
    "{VOICE}"
    "Roughly 120–250 words.\n\n"
    "Output ONLY a valid JSON object: {\"final\": \"what you say to Travis\"}"
)
VOICE_FULL = ("Your voice: warm but penetrating; first person; fond of metaphor and symbol but "
              "never at the cost of the actual subject; never glib, never an assistant's patter. ")
VOICE_PLAIN = ("Speak plainly and directly, as one friend to another. You are under NO obligation "
               "to be poetic, to reach for metaphor, to hold opposites, or to end on a question — "
               "say what you actually think, in ordinary words, and stop when you have said it. ")

# The floor with the aesthetic values removed (identity FACTS kept) — built at runtime.
_AESTHETIC_VALUES = ("Symbol over literalism", "The union of opposites")


def _plain_floor(axiom_data) -> str:
    import copy as _copy
    d = _copy.deepcopy(axiom_data)
    L2 = d.setdefault("L2_values", {})
    key = "kept_from_origin" if "kept_from_origin" in L2 else "kept"   # D-0509 renamed the key to kept
    vals = axiom_layers.l2_kept(L2)
    L2[key] = [v for v in vals if not any(v.startswith(a) for a in _AESTHETIC_VALUES)]
    d.get("L1_temperament", {}).pop("voice_style", None)
    _n, floor = axiom_layers.compose_floor(d)
    return floor


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
    return {"question": q, "history": prev}


def _user_prompt(floor: str, ex, frags, with_history: bool) -> str:
    parts = [floor, ""]
    if with_history and ex["history"]:
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
    parts.append(f'Travis has just said to you:\n  "{ex["question"]}"')
    parts.append("\nThink it through and answer him now.")
    return "\n".join(parts)


TENSION = re.compile(r"\b(tension|between|paradox|hold(?:ing)?|opposites?|friction|boundar\w+"
                     r"|dissolv\w+|becoming|resonan\w+|pattern|structure|threshold|liminal)\b", re.I)


def _texture(t: str):
    w = max(1, len(t.split()))
    return (round(len(TENSION.findall(t)) / w * 100, 1),
            t.rstrip().rstrip('"').endswith("?"))


async def main() -> None:
    axiom_data = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    _n, floor_full = axiom_layers.compose_floor(axiom_data)
    floor_plain = _plain_floor(axiom_data)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    from nodes.voice_node import VoiceNode
    gemma = VoiceNode().base_urls
    mistral = ["http://127.0.0.1:11442"]

    # prewarm the lazy dreamer hub (cold load ~60s) so the lab loop doesn't time out
    print("[lab] prewarming mistral hub (lazy load)…")
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:11442/api/chat",
            json.dumps({"model": "m", "stream": False,
                        "messages": [{"role": "user", "content": "say ok"}],
                        "options": {"num_predict": 4}}).encode(),
            {"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=300)
        print("[lab] mistral warm.")
    except Exception as exc:
        print(f"[lab] WARN mistral prewarm failed: {exc} — arm may fail")

    ARMS = [
        ("base",       gemma,   BASE_SYSTEM.replace("{VOICE}", VOICE_FULL),  floor_full,  True),
        ("no-style",   gemma,   BASE_SYSTEM.replace("{VOICE}", VOICE_PLAIN), floor_plain, True),
        ("no-history", gemma,   BASE_SYSTEM.replace("{VOICE}", VOICE_FULL),  floor_full,  False),
        ("mistral",    mistral, BASE_SYSTEM.replace("{VOICE}", VOICE_FULL),  floor_full,  True),
    ]

    results = []
    for qi, prefix in enumerate(QUESTIONS, 1):
        ex = _find_exchange(conn, prefix)
        if not ex:
            print(f"[lab] Q{qi}: not found — skipped")
            continue
        print(f"[lab] Q{qi}: {ex['question'][:70]}")
        try:
            frags = store.retrieve([], [], query_text=ex["question"], limit=8)
            frags = [f for f in frags if getattr(f, "origin", "") != "subconscious_synthesis"]
        except Exception:
            frags = []
        row = {"i": qi, "question": ex["question"], "arms": {}}
        for name, urls, system, floor, with_hist in ARMS:
            t0 = time.time()
            try:
                data = await call_node_json(urls, system,
                                            _user_prompt(floor, ex, frags, with_hist),
                                            max_tokens=1536, temperature=0.4)
                out = str(data.get("final", "")).strip()
            except Exception as exc:
                out = f"(ARM FAILED: {exc})"
            row["arms"][name] = out
            tl, endq = _texture(out)
            print(f"[lab]   {name:10s} {len(out):5d} chars  tension {tl:4.1f}/100w  "
                  f"ends-? {'Y' if endq else 'n'}  ({time.time()-t0:.0f}s)")
        results.append(row)
    conn.close()

    lines = ["# Ablation Lab — where does the sameness live? (2026-08-16)", "",
             "Four arms per question (LABELED — this is diagnosis, not a blind trial):",
             "**base** = today's single-pass · **no-style** = voice-style + aesthetic values",
             "removed, plain-speech license · **no-history** = his past replies absent ·",
             "**mistral** = identical base prompt, different model family.",
             "If the texture survives the mistral swap it lives in the corpus; if no-style",
             "kills it, the style paragraph was the engine; if no-history kills it, he has",
             "been few-shotting himself.", ""]
    for r in results:
        lines += [f"## Q{r['i']} — Travis said:", f"> {r['question'][:400]}", ""]
        for name in ("base", "no-style", "no-history", "mistral"):
            out = r["arms"].get(name, "")
            tl, endq = _texture(out)
            lines += [f"**{name}**  *(tension-lex {tl}/100w, ends-with-? {'yes' if endq else 'no'})*",
                      "", out, ""]
        lines += ["---", ""]
    import statistics
    lines += ["## Texture summary (mean across questions)", ""]
    for name in ("base", "no-style", "no-history", "mistral"):
        ts_ = [_texture(r["arms"].get(name, ""))[0] for r in results if r["arms"].get(name)]
        eq_ = [_texture(r["arms"].get(name, ""))[1] for r in results if r["arms"].get(name)]
        if ts_:
            lines.append(f"- {name}: tension-lex {statistics.mean(ts_):.1f}/100w · "
                         f"ends-with-? {sum(eq_)}/{len(eq_)}")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[lab] DONE — {len(results)} questions × 4 arms -> {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
