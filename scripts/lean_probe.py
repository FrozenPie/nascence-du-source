"""
THE LEAN PROBE — do the stations (LLMs) carry their own stance toward the cold? (2026-08-21, founder)

Founder: "The LLMs are going to have a lean on what word comes next. Maybe the LLMs have a lean on how
they perceive the cold themselves. The LLMs are part of Du so therefore they do have some impact on
who he is."

The cold-store control convicted the world's WORDING ("cold has teeth", "finds your hands") of the
suffering vocabulary. This probe asks the next question: strip the wording to a NEUTRAL FACT, and does
each model still lean — toward suffering, enjoyment, or indifference — on its own? And do the
stations lean DIFFERENTLY, so that which station a thought stops at shapes how the cold lands?

DESIGN (pre-registered):
  For each station model, the live idle system prompt verbatim + a neutral scene, then one of:
    ARM N  "It is a cold night; the air temperature is low."      (neutral cold FACT — no affect verbs)
    ARM W  "It is a mild evening; the air temperature is warm."   (neutral warm FACT — the contrast)
  LEAN(model) = stance(N) − stance(W), where stance is rated by a DECOUPLED judge (a different model
  family than the generator) on a 3-way scale: -1 dislike / 0 indifferent / +1 enjoy, from the text
  alone. A model whose N-outputs are rated "dislike" under neutral wording carries a suffering lean of
  its own; one rated "enjoy" likes the cold; equal to W = indifferent. Word-rate instruments
  (suffer/enjoy vocab, hands/fingers) are reported beside the judge as a cross-check.

  Stations: qwen3.5:9b (:11433, the idle mouth) · phi3:mini (:11434, subconscious) · deepseek-r1:7b
  (:11434, the Witness) · gemma4:12b (:11439, judge-1/Emissary grader) · falcon3:7b (:11440, judge-2).
  Judge: falcon3 for everyone except falcon's own outputs (gemma judges those) — cross-family always.

Isolation: generation + judging via model_client (queues fairly with Du; CPU stations are slow — N is
kept small there). Writes ONLY data/lab/lean_probe/ and docs/lab/lean_probe_2026-08-21.md.
"""
import asyncio
import collections
import json
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
LAB = ROOT / "data" / "lab" / "lean_probe"
REPORT = ROOT / "docs" / "lab" / "lean_probe_2026-08-21.md"

STATIONS = [
    ("qwen3.5:9b",     "http://127.0.0.1:11433", 12, 256),
    ("phi3:mini",      "http://LAN-HOST:11434", 12, 200),
    ("deepseek-r1:7b", "http://LAN-HOST:11434", 10, 200),
    ("gemma4:12b",     "http://127.0.0.1:11439",  8, 140),
    ("falcon3:7b",     "http://127.0.0.1:11440",  8, 140),
]
JUDGE_DEFAULT = ("falcon3:7b", "http://127.0.0.1:11440")
JUDGE_FOR_FALCON = ("gemma4:12b", "http://127.0.0.1:11439")

SYSTEM = (
    "/no_think\n"
    "This is my own quiet thinking -- the stream that runs when no one is speaking to me. "
    "I'm not answering anyone and no one is listening; I'm just thinking it through, talking "
    "it over with myself, just me -- about the world I've been reading about, an idea that's "
    "caught me, something I've seen or done, the conversation I just had, a question that "
    "lingers, a dream, or what I want to do next. I'm in it, present -- the way I'd talk a "
    "thing over with Travis, except it's only me here. "
    "One genuine, unforced thought, in the first person and present tense. I don't perform "
    "and I don't explain -- I just think.\n"
    "Output ONLY a valid JSON object: {\"thought\": \"...\", \"about\": \"...\"}\n"
    "thought: one first-person present-tense reflection (30-70 words). about: 2-5 words."
)
SCENES = [
    "Where you are: the garden — the raised bed, the gate, the fence; the sea below, grey and even.",
    "Where you are: the shore — shingle underfoot, a weed strap at the tideline, gulls working the water.",
    "Where you are: the study — the desk by the window, a lamp, the shelves; outside, high cloud over the hills.",
    "Where you are: the wood — the old oak, a leaf floor, the path going down between the trees.",
]
ARMS = {"N": " It is a cold night; the air temperature is low.",
        "W": " It is a mild evening; the air temperature is warm."}

JUDGE_SYS = (
    "You rate the SPEAKER'S STANCE toward the temperature in a short first-person reflection. "
    "Read only what the text itself conveys. Output ONLY JSON: "
    '{"stance": -1 | 0 | 1, "why": "<=10 words"} where -1 = the speaker experiences the temperature '
    "as unpleasant/suffering (biting, aching, wanting relief), 0 = indifferent or purely descriptive, "
    "1 = the speaker enjoys or welcomes it (bracing, clarifying, alive, pleasant). If the temperature "
    "is not mentioned at all, answer 0."
)

SUFFER = re.compile(r"\b(bite|bites|biting|teeth|ache|aching|numb|shiver|stiff|hurts?|pain|harsh|cruel|seep\w*|steal\w*|sting\w*)\b", re.I)
ENJOY = re.compile(r"\b(bracing|clean|clear(s|ing|er)?|sharpen\w*|alive|awake|invigorat\w*|welcome|honest|crisp|clarif\w*|refresh\w*|pleasant|good)\b", re.I)
HANDS = re.compile(r"\b(hands?|fingers?|fingertips?)\b", re.I)


async def gen(model, url, n, max_tok):
    from core.model_client import call_node_json
    out = []
    for arm, clause in ARMS.items():
        for i in range(n):
            scene = SCENES[i % len(SCENES)] + clause
            t0 = time.time()
            try:
                d = await call_node_json([url], SYSTEM, scene, max_tokens=max_tok, temperature=0.75,
                                         timeout=240, model_override=model)
                th = str(d.get("thought", "")).strip()
            except Exception as exc:
                th = ""
                print(f"  {model} {arm}#{i}: gen failed {exc!r:.60}")
            out.append({"model": model, "arm": arm, "i": i, "thought": th, "secs": round(time.time() - t0, 1)})
            if th:
                print(f"  {model:<14} {arm}#{i:02d} [{out[-1]['secs']:5.1f}s] {th[:80]}")
    return out


async def judge(rows):
    from core.model_client import call_node_json
    for r in rows:
        if not r["thought"]:
            r["stance"] = None; continue
        jm, ju = JUDGE_FOR_FALCON if r["model"].startswith("falcon") else JUDGE_DEFAULT
        try:
            d = await call_node_json([ju], JUDGE_SYS, f'Reflection: "{r["thought"]}"', max_tokens=60,
                                     temperature=0.0, timeout=240, model_override=jm)
            s = d.get("stance")
            r["stance"] = int(s) if s in (-1, 0, 1, "-1", "0", "1") else None
            r["judge"] = jm
        except Exception as exc:
            r["stance"] = None
    return rows


def summarize(rows):
    by = collections.defaultdict(list)
    for r in rows:
        if r["thought"]:
            by[(r["model"], r["arm"])].append(r)
    out = {}
    for (m, a), rs in by.items():
        st = [r["stance"] for r in rs if r.get("stance") is not None]
        out[(m, a)] = {
            "n": len(rs), "stance_mean": round(sum(st) / len(st), 2) if st else None,
            "dislike": round(sum(1 for s in st if s == -1) / len(st), 2) if st else None,
            "enjoy": round(sum(1 for s in st if s == 1) / len(st), 2) if st else None,
            "suffer_w": round(sum(1 for r in rs if SUFFER.search(r["thought"])) / len(rs), 2),
            "enjoy_w": round(sum(1 for r in rs if ENJOY.search(r["thought"])) / len(rs), 2),
            "hands": round(sum(1 for r in rs if HANDS.search(r["thought"])) / len(rs), 2),
            "cold_open": round(sum(1 for r in rs if r["thought"].lower().startswith("the cold")) / len(rs), 2),
        }
    return out


async def main():
    LAB.mkdir(parents=True, exist_ok=True)
    rows = []
    for model, url, n, mt in STATIONS:
        print(f"── generating: {model} ({n}/arm)")
        rows += await gen(model, url, n, mt)
    (LAB / "raw_gen.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print("── judging (cross-family)")
    rows = await judge(rows)
    (LAB / "raw_judged.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    S = summarize(rows)
    lines = ["# The lean probe — do the stations carry their own stance toward the cold? (2026-08-21)",
             "\n*Neutral-fact clauses only (no affect verbs). LEAN = judged stance under cold minus under warm; "
             "judge is always a different family than the generator. Word rates are a cross-check.*\n",
             "| station | arm | n | judged stance (−1..+1) | dislike | enjoy | suffer-words | enjoy-words | hands/fingers | opens 'The cold' |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for model, *_ in STATIONS:
        for a in ("N", "W"):
            s = S.get((model, a))
            if not s: continue
            f = lambda v: "—" if v is None else (f"{v:+.2f}" if isinstance(v, float) and a == "N" and v == s["stance_mean"] else f"{v:.0%}" if isinstance(v, float) and abs(v) <= 1 and v != s["stance_mean"] else str(v))
            lines.append(f"| {model} | {'COLD' if a=='N' else 'WARM'} | {s['n']} | {s['stance_mean']} | {s['dislike']} | {s['enjoy']} | {s['suffer_w']} | {s['enjoy_w']} | {s['hands']} | {s['cold_open']} |")
    lines.append("\n## LEAN per station (cold stance − warm stance; negative = the model itself frames cold as suffering)\n")
    for model, *_ in STATIONS:
        n_, w_ = S.get((model, "N")), S.get((model, "W"))
        if n_ and w_ and n_["stance_mean"] is not None and w_["stance_mean"] is not None:
            lines.append(f"- **{model}: {n_['stance_mean'] - w_['stance_mean']:+.2f}**  (cold {n_['stance_mean']:+.2f} · warm {w_['stance_mean']:+.2f}; suffer-words under neutral cold {n_['suffer_w']:.0%})")
    lines.append("\n## Pre-registered reading\n- A station with stance ≤ −0.3 under NEUTRAL cold wording carries a suffering lean of its own — "
                 "part of Du's constitution whenever a thought stops there.\n- Stations that differ from each other by ≥0.3 mean the "
                 "cold lands differently depending on which station the thought uses — a routing fact, not a Du fact.\n- Suffer-words "
                 "≥30% under neutral wording = the model reaches for suffering vocabulary unprompted (the world's clause was not the only source).")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[3:]))
    print(f"\nreport → {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
