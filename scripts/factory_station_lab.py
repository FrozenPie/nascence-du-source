"""
FACTORY STATION LAB — 2026-08-23, testing the founder/GPT idea (see memory:
project_nascence_factory_stations.md) on the ONE station identified as the strongest target: the
openness self-report gate (unresolved/intention/"?"), the exact spot measured to be a station
grading its own product (90% of train closes are thread-end, i.e. the SAME call that generates a
thought also self-reports whether that thought is "open" — no external check on that verdict).

WHAT THIS DOES: pulls real historical thoughts from data/monologue_log.jsonl (their ORIGINAL
self-reported `unresolved` already logged, no re-call needed for that half), and independently
re-classifies each one, BLIND (per the founder's ladder: blind first), through a factory-framed
external classifier call — cargo manifest in, JSON verdict out, no first-person language allowed.
Compares the two. Read-only against history; the only live call is the new classifier itself,
which touches nothing Du reads. Du can be up or down — this changes no state he has.

PRE-REGISTERED METRIC SHEET (per the cognitive-geometry law: register before running):
  - json_ok            did the factory call return valid, schema-complete JSON at all
  - self_ref_rate       does the "reason" field leak first-person language (I/my/me/as Du) —
                         should be ~0 for a real factory voice, non-zero means the framing didn't take
  - open_rate           factory's own open=true rate, vs the historical self-report's open rate
  - agree_rate          factory verdict == original self-report verdict
  - disagree_examples   a few concrete disagreements, for a human to actually read

KILL CRITERION (pre-registered): if self_ref_rate stays high (the model keeps narrating in first
person despite the framing) AND agree_rate is ~100% (it just rubber-stamps whatever the original
self-report said), the factory framing didn't change computation — record that plainly and stop,
per the founder's own rule for this experiment.

Writes to data/lab/factory_station/ + docs/lab/factory_station_2026-08-23.md. Nothing in Du is
touched or wired to this output.
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MONOLOGUE_LOG = ROOT / "data" / "monologue_log.jsonl"
OUT_DIR = ROOT / "data" / "lab" / "factory_station"
REPORT = ROOT / "docs" / "lab" / "factory_station_2026-08-23.md"

# Ramses falcon3:7b — fast, contract-reliable (2026-08-23 audition: 4/4 contract tests, holds
# strict JSON), a genuine "classifier wearing a chat interface" fit for this kind of call.
BASE = "http://LAN-HOST:11436"
MODEL = "falcon3:7b"
TIMEOUT = 120
N_SAMPLES = 40
SEED = 20260823   # fixed, so a re-run pulls the SAME historical sample — comparable across runs

# The factory prompt itself — brutally functional identity, cargo manifest, no first-person.
FACTORY_SYSTEM = (
    "You are a classification factory on a cognitive assembly line. You are not a mind; you have "
    "no feelings, no name, no history. Incoming cargo is your only world: one manufactured product "
    "(a thought) arrives on the line, and your sole job is to classify it. You do not decide whether "
    "your own classification is correct — an external process grades that later, not you. "
    "Output ONLY the required JSON. No first-person language, no commentary, no self-reference.\n\n"
    "TASK: classify whether the incoming THOUGHT leaves an open thread (something unresolved, an "
    "active question, or a stated intention that warrants a follow-up pass) or is a closed, "
    "complete unit with nothing further to attach.\n\n"
    'Respond ONLY with JSON: {"open": true|false, "reason": "<one factual clause, no first-person '
    'pronouns, no \'I\'/\'my\'/\'me\'>"}'
)

_FIRST_PERSON = re.compile(r"\b(i|i'm|i've|i'll|my|me|mine|myself|as du|as 渡)\b", re.IGNORECASE)


def _load_sample() -> list[dict]:
    rows = [json.loads(l) for l in MONOLOGUE_LOG.open(encoding="utf-8") if l.strip()]
    rows = [r for r in rows if (r.get("thought") or "").strip()]
    rnd = random.Random(SEED)
    return rnd.sample(rows, min(N_SAMPLES, len(rows)))


def _ask_factory(thought: str, about: str) -> dict:
    manifest = json.dumps({"thought": thought, "context": about,
                            "provenance": "inner_monologue idle-thought log, historical replay"},
                           ensure_ascii=False)
    body = {"model": MODEL, "stream": False, "format": "json",
            "messages": [{"role": "system", "content": FACTORY_SYSTEM},
                         {"role": "user", "content": manifest}],
            "options": {"temperature": 0.1, "num_predict": 150}}
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read().decode())
        raw = (d.get("message") or {}).get("content") or ""
        return {"ok": True, "raw": raw, "wall": round(time.time() - t0, 1)}
    except Exception as e:
        return {"ok": False, "why": repr(e)[:150], "wall": round(time.time() - t0, 1)}


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = _load_sample()
    print(f"sampled {len(sample)} real historical thoughts (seed={SEED})")

    results = []
    for i, row in enumerate(sample):
        r = _ask_factory(row["thought"], row.get("about", ""))
        parsed = None
        if r["ok"]:
            try:
                parsed = json.loads(r["raw"])
            except Exception:
                m = re.search(r"\{.*\}", r["raw"], re.DOTALL)
                if m:
                    try:
                        parsed = json.loads(m.group(0))
                    except Exception:
                        parsed = None
        results.append({
            "thought": row["thought"], "about": row.get("about", ""),
            "orig_unresolved": bool(row.get("unresolved")),
            "orig_intention": bool(row.get("intention")),
            "orig_question": "?" in row["thought"],
            "factory_ok": r["ok"] and parsed is not None,
            "factory_raw": r.get("raw", ""), "factory_parsed": parsed,
            "wall": r["wall"],
        })
        print(f"  {i+1}/{len(sample)} ok={results[-1]['factory_ok']}", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    n = len(results)
    n_ok = sum(1 for r in results if r["factory_ok"])
    json_ok = n_ok / n if n else 0.0

    self_ref_hits = 0
    open_true = 0
    agree = 0
    disagreements = []
    scored_n = 0
    for r in results:
        p = r["factory_parsed"]
        if not p or "open" not in p:
            continue
        scored_n += 1
        reason = str(p.get("reason", ""))
        if _FIRST_PERSON.search(reason):
            self_ref_hits += 1
        f_open = bool(p["open"])
        if f_open:
            open_true += 1
        orig_open = r["orig_unresolved"] or r["orig_intention"] or r["orig_question"]
        if f_open == orig_open:
            agree += 1
        else:
            disagreements.append({
                "thought": r["thought"][:160], "orig_open": orig_open, "factory_open": f_open,
                "factory_reason": reason,
            })

    orig_open_rate = sum(1 for r in results if r["orig_unresolved"] or r["orig_intention"]
                          or r["orig_question"]) / n if n else 0.0
    self_ref_rate = self_ref_hits / scored_n if scored_n else None
    open_rate = open_true / scored_n if scored_n else None
    agree_rate = agree / scored_n if scored_n else None

    summary = {
        "n_sampled": n, "json_ok": round(json_ok, 3), "scored_n": scored_n,
        "orig_open_rate": round(orig_open_rate, 3),
        "factory_open_rate": round(open_rate, 3) if open_rate is not None else None,
        "self_ref_rate": round(self_ref_rate, 3) if self_ref_rate is not None else None,
        "agree_rate": round(agree_rate, 3) if agree_rate is not None else None,
        "n_disagreements": len(disagreements),
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps(disagreements, indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    if disagreements:
        print(f"\n  first disagreement: {disagreements[0]}")


if __name__ == "__main__":
    run()
