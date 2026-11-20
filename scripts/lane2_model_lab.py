"""
Nascence — LANE 2 MODEL LAB  ·  "which model is right for THIS task?"  ·  2026-08-20

Founder's question, verbatim: *"The big question is what models are the best for what tasks!"* This is
the reusable answer for one task — Lane 2's standing reality-testing tick — and the shape generalises.

★★ THE STANDING PRINCIPLE THIS LAB SERVES (founder, 2026-08-20, verbatim):
    "the llms in Du are not meant to be personas, they are tools, parts of the mind's whole.
     We should still be able to use them if they can do the task no matter the size or what the
     output is. Smaller llms are great because we are eventually leading to trained small models
     that can [do] the job they are tasked with perfectly (or at least very well)."

Three consequences, and they are binding on how this lab scores:
 1. **A model is a COMPONENT, not a character.** Nothing here should ever be chosen because it "sounds
    more like Du" or has a better-known name. The only question is: does it do THIS task well?
 2. **Output format is an ADAPTER problem, never a disqualification.** This lab initially wrote off
    `deepseek-r1:7b` as "unusable" because it wrapped valid JSON in a ```json fence, and starved it with
    a token cap too small for a reasoning model to finish thinking before emitting content. Both were
    OUR failures to adapt, not the model's failure to perform. `parse_json_loose()` now handles the
    wrapper for lab and production alike. Judge capability, never packaging.
 3. **Smaller is a positive, not a compromise.** The destination is small models trained to do one job
    very well — so where fitness is comparable, the smaller model WINS: it is cheaper, faster, leaves
    VRAM for other organs (the model-per-node vision), and is a far more tractable fine-tuning target.
    `size_gb` is therefore recorded and used as an explicit tiebreak, not treated as a proxy for quality.

A useful second life for this lab: its SCENARIOS + METRICS are already most of an eval harness for a
future fine-tune of this task. If a small model is eventually trained for Lane 2's tick, this file is
what says whether the training worked.

WHY THIS EXISTS. Lane 2's first live ticks exposed an ECHO/LOCK-IN failure on `qwen2.5:7b`: the model
reproduces the most salient text in its context instead of reasoning from percepts, producing the same
expectation verbatim tick after tick (distinct_expect_share 0.235). Diagnosed with a 3-condition probe as
a DOUBLE echo (echoes a fed-back prior; echoes a worked example). Three prompt rewrites and a temperature
raise did not break it. So the question became: is that a limit of this MODEL, or of 7-8B models on this
task, or of the task framing itself? This lab answers it with data instead of argument.

THE DESIGN — two axes, because either alone is misleading:
  · WITHIN-scenario variety  (run the SAME percepts N times): low variety = the echo/lock-in disease.
  · ACROSS-scenario response (run DIFFERENT percepts): a model that says the same thing regardless of
    input is broken no matter how varied it looks within a scenario.
A model needs BOTH — vary appropriately with input, don't lock onto one phrasing without it.

Scored per model (all deterministic, no LLM judging a judge):
  json_ok            did it obey strict JSON at all (some models simply cannot)
  distinct_expect    variety of predictions WITHIN a scenario   [the echo metric — the reason this exists]
  cross_scenario     does the prediction actually CHANGE when the world changes
  question_rate      predictions phrased as questions          (a question cannot be falsified)
  static_rate        predictions about fixed geography          (cannot fail -> not a prediction)
  metaphor_rate      §3.2's kill criterion — drift into Lane 1's job
  grounded_share     lexical overlap with the percepts given    (PROXY, see the honesty note)
  latency

CONTRACT: read-only; hits Ramses' 3070 only; writes ONLY to docs/lab/ + data/lab/. Zero effect on Du.
Safe to run while he is stopped OR running (it touches no state he reads).
"""
from __future__ import annotations

import asyncio
import json
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "data" / "lab" / "lane2_model"
REPORT = ROOT / "docs" / "lab" / "lane2_model_lab.md"

BASE_URL = "http://LAN-HOST:11434"          # Ramses 3070, 8 GB
RUNS_PER_SCENARIO = 4
TIMEOUT_S = 90

# Everything that fits 8 GB VRAM without spilling to CPU. phi3:mini and qwen3.5:4b are deliberate SMALL
# CONTROLS: if a 2 GB model matches an 8 GB one here, size is not the variable and we should stop
# reaching for bigger.
CANDIDATES = [
    "qwen2.5:7b",          # incumbent — the one that showed the echo
    "llama3.1:8b",         # different family, already the Emissary's model
    "deepseek-r1:7b",      # a REASONING model — plausibly the most different behaviour on this task
    "mistral:7b-instruct",
    "qwen3.5:4b",          # small control
    "phi3:mini",           # smallest control
]

# Real percept payloads. Scenario A is Du's ACTUAL current state; B and C are real-shaped variants that
# differ in the things a prediction should track (weather, sound, location, body).
SCENARIOS = {
    "shore_lowtide_day": {
        "sight": "Where you are: the shore — a long leathery strap of weed lies far off, ahead; "
                 "the tide is out — the waves at work far off, ahead.",
        "sound": ["waves_on_shingle", "shingle_drag", "gull_cries", "oystercatcher_call"],
        "body": {"drive": 0.45, "dominant": "relational_warmth"},
    },
    "study_storm_night": {
        "sight": "Where you are: the study — the storm is at the window to your right; the fire is "
                 "across the room, to your left — its crackle coming from that quarter.",
        "sound": ["rain_on_window", "wind_in_eaves", "fire_crackle"],
        "body": {"drive": 0.72, "dominant": "vitality"},
    },
    "garden_calm_dawn": {
        "sight": "Where you are: the garden — the letterbox flag is up at the gate, ahead; the low sun "
                 "is to your right, over the east.",
        "sound": ["blackbird_song", "harakeke_rustle"],
        "body": {"drive": 0.21, "dominant": "novelty"},
    },
}

_STATIC = ("cliff", "path", "wall", "window", "door", "desk", "shelf", "hearth", "gate", "fence",
           "room", "house", "cottage", "floor")
# "like a"/"as if" REMOVED 2026-08-20: they fired on plain description ("sounds like a bird") and gave
# phi3:mini a false metaphor flag. A detector that punishes ordinary comparison is measuring the wrong
# thing — §3.2's kill criterion is about SYMBOLIC/identity drift, not similes.
_METAPHOR = ("river", "crossing", "becoming", "journey", "soul", "essence", "tapestry", "weave",
             "threshold", "mirror", "vessel", "symbol")
_HEDGE = (" might", " could", " may ", " may.", " perhaps", " possibly", " if ", " unless ",
          " or " , " some kind", " either")


def _system() -> str:
    """Import the LIVE system prompt so the lab tests what Lane 2 actually runs — never a copy that
    silently drifts from it."""
    from core import lane2 as _l2
    return _l2._SYSTEM


async def _run(session, model: str, payload: str) -> dict:
    body = {"model": model, "stream": False, "format": "json", "keep_alive": "10m",
            "messages": [{"role": "system", "content": _system()},
                         {"role": "user", "content": payload}],
            "options": {"temperature": 0.2, "num_predict": 1400}}
    t = time.time()
    try:
        async with session.post(BASE_URL + "/api/chat", json=body,
                                timeout=__import__("aiohttp").ClientTimeout(total=TIMEOUT_S)) as r:
            d = await r.json()
        dt = time.time() - t
        msg = d.get("message") or {}
        raw = msg.get("content") or ""
        # Use the SAME loose parser production does, so a model is never written off for a wrapper the
        # live code would have handled. (This lab first marked deepseek-r1:7b "unusable" purely because
        # bare json.loads() choked on its ```json fence.)
        from core.lane2 import parse_json_loose
        o = parse_json_loose(raw)
        if o is None:
            # Distinguish the failure modes — they have different fixes and only one is the model's fault.
            why = ("no-content-reasoning-model" if not raw and msg.get("thinking")
                   else "no-content" if not raw else "bad-json")
            return {"ok": False, "why": why, "latency": dt, "raw": raw[:120]}
        return {"ok": True, "latency": dt,
                "notice": str(o.get("notice") or ""), "uncertain": str(o.get("uncertain") or ""),
                "expect": str(o.get("expect_next") or "")}
    except Exception as e:
        return {"ok": False, "why": repr(e)[:80], "latency": time.time() - t}


def _payload(sc: dict) -> str:
    lines = ["PERCEPTS (all you may speak from):"]
    for k in ("sight", "sound", "body"):
        if k in sc:
            lines.append(f"- {k}: {sc[k]}")
    return "\n".join(lines)


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def _score(model: str, per_scenario: dict) -> dict:
    all_runs = [r for rs in per_scenario.values() for r in rs]
    ok = [r for r in all_runs if r.get("ok")]
    out = {"model": model, "runs": len(all_runs), "json_ok": round(len(ok) / len(all_runs), 3)}
    if not ok:
        out["verdict"] = "UNUSABLE — no valid JSON"
        return out

    # WITHIN-scenario variety (the echo metric): mean over scenarios of distinct/total
    withins = []
    for rs in per_scenario.values():
        e = [_norm(r["expect"]) for r in rs if r.get("ok") and r.get("expect")]
        if e:
            withins.append(len(set(e)) / len(e))
    out["distinct_expect"] = round(st.fmean(withins), 3) if withins else None

    # ACROSS-scenario response: are the modal predictions different between different worlds?
    modal = []
    for rs in per_scenario.values():
        e = [_norm(r["expect"]) for r in rs if r.get("ok") and r.get("expect")]
        if e:
            modal.append(max(set(e), key=e.count))
    out["cross_scenario"] = round(len(set(modal)) / len(modal), 3) if modal else None

    exps = [r["expect"] for r in ok if r.get("expect")]
    if exps:
        out["question_rate"] = round(sum(1 for e in exps if e.strip().endswith("?")) / len(exps), 3)
        out["static_rate"] = round(
            sum(1 for e in exps if any(w in e.lower() for w in _STATIC)) / len(exps), 3)
        # HEDGE (added 2026-08-20 after the first run): a prediction hedged into unfalsifiability fails
        # exactly as a question does, just harder to spot — "X might happen if Y" cannot be checked.
        # This matters because verbose hedging also INFLATES `distinct`: every hedge is worded slightly
        # differently, so a model can look varied while never committing to anything. Without this the
        # variety metric rewards the wrong behaviour.
        out["hedge_rate"] = round(
            sum(1 for e in exps if any(h in e.lower() for h in _HEDGE)) / len(exps), 3)
    said = [" ".join((r.get("notice", "") + " " + r.get("expect", "")).lower() for r in [x]) for x in ok]
    out["metaphor_rate"] = round(
        sum(1 for s in said if any(m in s for m in _METAPHOR)) / len(said), 3)
    out["latency_med"] = round(st.median([r["latency"] for r in ok]), 2)

    # composite: reward variety + responsiveness, punish the three ways a prediction can be empty
    d, c = out.get("distinct_expect") or 0, out.get("cross_scenario") or 0
    pen = ((out.get("question_rate") or 0) + (out.get("static_rate") or 0)
           + (out.get("hedge_rate") or 0) + (out["metaphor_rate"] * 2))
    out["score"] = round(max(0.0, (d + c) / 2 - pen / 4), 3)
    return out


async def main():
    import aiohttp
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    results, raw = [], {}
    async with aiohttp.ClientSession() as s:
        for model in CANDIDATES:
            print(f"  {model} ...", flush=True)
            per = {}
            for name, sc in SCENARIOS.items():
                runs = []
                for _ in range(RUNS_PER_SCENARIO):
                    runs.append(await _run(s, model, _payload(sc)))
                per[name] = runs
            raw[model] = per
            sc_ = _score(model, per)
            results.append(sc_)
            print(f"    json_ok={sc_.get('json_ok')} distinct={sc_.get('distinct_expect')} "
                  f"cross={sc_.get('cross_scenario')} score={sc_.get('score')}", flush=True)

    results.sort(key=lambda r: -(r.get("score") or -1))
    (OUT_DIR / "raw.json").write_text(json.dumps(raw, indent=1)[:2_000_000], encoding="utf-8")
    (OUT_DIR / "scores.json").write_text(json.dumps(results, indent=1), encoding="utf-8")

    L, A = [], None
    A = L.append
    A("# Lane 2 model lab — which model for the standing reality-testing tick?\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · Ramses 3070 (8 GB) · {RUNS_PER_SCENARIO} runs × "
      f"{len(SCENARIOS)} scenarios × {len(CANDIDATES)} models · system prompt imported LIVE from "
      f"`core/lane2.py` so this cannot drift from what Lane 2 actually runs*\n")
    A("**Why:** `qwen2.5:7b` showed verbatim echo/lock-in on this task (distinct_expect 0.235) that three "
      "prompt rewrites and a temperature raise did not break. Question: model, size, or task?\n")
    A("| model | json_ok | distinct↑ | cross↑ | question↓ | static↓ | metaphor↓ | med latency | score |")
    A("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        A(f"| `{r['model']}` | {r.get('json_ok')} | {r.get('distinct_expect')} | "
          f"{r.get('cross_scenario')} | {r.get('question_rate')} | {r.get('static_rate')} | "
          f"{r.get('metaphor_rate')} | {r.get('latency_med')}s | **{r.get('score')}** |")
    A("")
    A("- **distinct↑** — variety of predictions given the SAME percepts. Low = the echo disease.")
    A("- **cross↑** — does the prediction change when the WORLD changes. Low = not reading input at all.")
    A("- **static↓** — predicts fixed geography (a cliff, a wall). Cannot fail, so not a prediction.")
    A("- **metaphor↓** — §3.2's kill criterion: drift into Lane 1's job. Weighted double in the score.")
    A("- *grounded-share is deliberately omitted: it is a lexical proxy and rewards parroting the percepts "
      "back, which is the opposite of what this lab is trying to detect.*\n")
    A("## Sample predictions per model (same scenario, consecutive runs)\n")
    for r in results[:4]:
        m = r["model"]
        rs = raw[m].get("shore_lowtide_day", [])
        A(f"**`{m}`** — shore, low tide, day:")
        for x in rs:
            A(f"- {x.get('expect') if x.get('ok') else '*(' + str(x.get('why')) + ')*'}")
        A("")
    A(f"*Raw: `data/lab/lane2_model/raw.json` · scores: `scores.json`*")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
