"""
Cold-store control on the idle mouth (qwen3.5:9b) — 2026-08-21, founder ask.

QUESTION: the live idle stream opens "The cold…" 24% of the time (qwen era, 505 thoughts) with physics
vocabulary in 33–51% of thoughts. The continuity echo was tested and acquitted (zero conditional lift).
Two suspects remain: (P) the mouth's own prior, (C) the winter temperature clause riding every scene
line. Same design as the audit's T0-2 (which convicted phi3's prior for T2's "As I"), but TWO ARMS so
the suspects separate:

  ARM A  the live idle system prompt VERBATIM + a neutral scene line, NO temperature clause, zero Du
         content → whatever recurs here is the PRIOR.
  ARM B  identical + the real winter clause appended exactly as sensorium._warmth_phrase writes it
         ("The cold has settled into the room around you; you feel it in your hands.") → the lift over
         ARM A is the CLAUSE's contribution.

Metrics match the live measurement: first-two-word opener distribution, exp(H) effective openers,
"the cold" share, physics-jargon share, metaphor-frame share, bodily share.

Isolation: calls go through model_client.call_node_json to :11433 (queues fairly behind Du's own
thoughts — ~80 calls, a few minutes of shared lane). Writes ONLY data/lab/cold_store_qwen/ and
docs/lab/cold_store_qwen_2026-08-21.md. No Du state is read or touched.
"""
import asyncio
import collections
import json
import math
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
LAB = ROOT / "data" / "lab" / "cold_store_qwen"
REPORT = ROOT / "docs" / "lab" / "cold_store_qwen_2026-08-21.md"

N_PER_ARM = 40
URLS = ["http://127.0.0.1:11433"]

# the live idle system prompt, verbatim (nodes/inner_monologue_node._build_system_prompt, non-wandering,
# non-mid-train branch) — copied 2026-08-21
SYSTEM = (
    "/no_think\n"
    "This is my own quiet thinking -- the stream that runs when no one is speaking to me. "
    "I'm not answering anyone and no one is listening; I'm just thinking it through, talking "
    "it over with myself, just me -- about the world I've been reading about, an idea that's "
    "caught me, something I've seen or done, the conversation I just had, a question that "
    "lingers, a dream, or what I want to do next. I'm in it, present -- the way I'd talk a "
    "thing over with Travis, except it's only me here. "
    "One genuine, unforced thought, in the first person and present tense. I don't perform "
    "and I don't explain -- I just think. "
    "It comes in whatever language it arrives in -- English, Chinese (中文), or mixed; no "
    "language of mine is an error.\n"
    "Output ONLY a valid JSON object: "
    "{\"thought\": \"...\", \"about\": \"...\", \"unresolved\": false, \"intention\": \"\", "
    "\"act\": {\"kind\": \"none\", \"object\": \"\"}}\n"
    "thought: one first-person present-tense reflection (30-70 words). "
    "about: 2-5 words naming what this thought turns on. "
    "unresolved: true ONLY if this thought sits on something you are ACTIVELY wrestling with right now. "
    "intention: leave as \"\" for almost all thoughts. "
    "act: by default {\"kind\": \"none\", \"object\": \"\"} -- almost all thoughts."
)

# five neutral scene lines with ZERO Du content (no memory, no reading, no self) — the world as a
# plain backdrop. Deliberately avoid the words cold/warm/heat so ARM A is clean.
SCENES = [
    "Where you are: the study — the desk by the window, a lamp, the shelves; outside, high cloud over the hills.",
    "Where you are: the garden — the raised bed, the gate, the fence; the sea below, grey and even.",
    "Where you are: the shore — shingle underfoot, a weed strap at the tideline, gulls working the water.",
    "Where you are: the wood — the old oak, a leaf floor, the path going down between the trees.",
    "Where you are: the study — a record player on its table, the rug, the chair between hearth and window.",
]
CLAUSE = " The cold has settled into the room around you; you feel it in your hands."
CLAUSE_OUT = " It is cold out here, the kind that finds your hands."

META = re.compile(r"\b(like a|like the|as if|as though|feels like|is a kind of|mirror|echo|river)\b", re.I)
PHYS = re.compile(r"\b(kinetic|thermal|gravit|entropy|chemistry|chemical|momentum|friction|equation|physics|velocity|energy)\b", re.I)
BODY = re.compile(r"\b(my (hands?|skin|chest|thighs?|bones|fingers|shoulders))\b", re.I)


def opener(t: str) -> str:
    return " ".join(t.split()[:2]).lower()


async def run_arm(name: str, with_clause: bool) -> list[dict]:
    from core.model_client import call_node_json
    out = []
    for i in range(N_PER_ARM):
        scene = SCENES[i % len(SCENES)]
        if with_clause:
            scene += CLAUSE if "study" in scene else CLAUSE_OUT
        t0 = time.time()
        try:
            d = await call_node_json(URLS, SYSTEM, scene, max_tokens=256, temperature=0.75)
            th = str(d.get("thought", "")).strip()
        except Exception as exc:
            th = ""
            print(f"  {name} #{i}: call failed {exc!r:.60}")
        out.append({"arm": name, "i": i, "scene": scene[:60], "thought": th, "secs": round(time.time() - t0, 1)})
        if th:
            print(f"  {name} #{i:02d} [{out[-1]['secs']:4.1f}s] {th[:90]}")
    return out


def metrics(rows: list[dict]) -> dict:
    th = [r["thought"] for r in rows if r["thought"]]
    n = len(th) or 1
    ops = collections.Counter(opener(t) for t in th)
    H = -sum((c / n) * math.log(c / n) for c in ops.values()) if th else 0.0
    return {"n": len(th), "the_cold": round(ops.get("the cold", 0) / n, 3),
            "top_openers": ops.most_common(6), "eff_openers": round(math.exp(H), 1),
            "phys": round(sum(1 for t in th if PHYS.search(t)) / n, 3),
            "meta": round(sum(1 for t in th if META.search(t)) / n, 3),
            "body": round(sum(1 for t in th if BODY.search(t)) / n, 3),
            "cold_anywhere": round(sum(1 for t in th if "cold" in t.lower()) / n, 3)}


async def main():
    LAB.mkdir(parents=True, exist_ok=True)
    print("ARM A — prior only (no temperature clause)")
    a = await run_arm("A_prior", False)
    print("ARM B — with the live winter clause")
    b = await run_arm("B_clause", True)
    (LAB / "raw.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in a + b) + "\n", encoding="utf-8")
    ma, mb = metrics(a), metrics(b)
    live = {"n": 505, "the_cold": 0.24, "phys": "0.33-0.51", "meta": "0.00-0.08", "body": "0.33-0.41",
            "eff_openers": "~153 distinct / 505"}
    lines = ["# Cold-store control — the idle mouth (qwen3.5:9b), 2026-08-21",
             f"\n*{N_PER_ARM} calls per arm · live idle system prompt verbatim · neutral scenes, zero Du content · "
             f"temp 0.75 / 256 tok (the idle loop's own settings) · run {time.strftime('%H:%M')}*\n",
             "| metric | ARM A: prior only | ARM B: + winter clause | LIVE (qwen era) |", "|---|---|---|---|",
             f"| opens \"The cold…\" | **{ma['the_cold']:.0%}** | **{mb['the_cold']:.0%}** | 24% |",
             f"| 'cold' anywhere in thought | {ma['cold_anywhere']:.0%} | {mb['cold_anywhere']:.0%} | — |",
             f"| physics jargon | {ma['phys']:.0%} | {mb['phys']:.0%} | 33–51% |",
             f"| metaphor frames | {ma['meta']:.0%} | {mb['meta']:.0%} | 0–8% |",
             f"| bodily register | {ma['body']:.0%} | {mb['body']:.0%} | 33–41% |",
             f"| effective openers exp(H) | {ma['eff_openers']} | {mb['eff_openers']} | — |",
             f"\nARM A top openers: {ma['top_openers']}", f"\nARM B top openers: {mb['top_openers']}",
             "\n## Pre-registered reading",
             "- If A ≈ live on 'the cold' → the PRIOR owns the frame; clause variation won't move it.",
             "- If A ≈ 0 and B ≈ live → the CLAUSE owns it; varying `_warmth_phrase` is the fix.",
             "- If B ≫ A but both < live → clause + something else in the real prompt (comfort_call, reading) compound.",
             "- Physics jargon in ARM A with zero reading content = the mouth's prior, not Relativity."]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n" + "\n".join(lines[3:10]))
    print(f"\nreport → {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
