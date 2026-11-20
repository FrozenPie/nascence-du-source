"""Lane 2 context lab — does the RIGHT AMOUNT of context depend on the model?

Founder's question (2026-08-20): *"Maybe smaller/larger models benefit from smaller/larger context
windows to work in."* That question contains two different things, and they must not be tested together:

**(1) `num_ctx` — the window the model is SERVED with.** Already answered by a separate probe, recorded
here so it is not re-litigated: at Lane 2's payload the prompt is 399 tokens (deepseek) / 474 (phi3),
and `prompt_eval_count` is IDENTICAL at num_ctx 512 / 2048 / 8192 / 32768. `num_ctx` is ROOM, not
content — extra room is empty room. It has a FLOOR (num_ctx=512 truncated deepseek's output mid-JSON,
because it generates ~550 reasoning tokens on top of a 399-token prompt) and a COST CEILING (phi3 took
37.4s at 32768 vs 3.4s at default, for the SAME 115 generated tokens). Nothing to gain in between.
So `num_ctx` is fixed at 8192 here — above the floor, below the cliff — and is NOT a variable.

**(2) Payload richness — how much we actually PUT in.** This is the real lever, and it is what this
lab measures. It splits again, because this project already holds two datapoints that point OPPOSITE
ways and the split explains why:
  - Lane 2's echo experiment: feeding the model its own prior expectation produced verbatim echo.
    More context made it WORSE.
  - The 2026-08-16 cap widenings: widening context slices for the Master's recall/reflection/executive
    nodes was judged better by the founder in a blind pair test, 3 of 4. More context made it BETTER.
The difference is not the amount, it is the KIND: more WORLD vs more OWN-OUTPUT. So the levels are:

  LEAN    sight only                        — the floor: can it predict from almost nothing?
  CURRENT sight + sound + body              — what Lane 2 ships today
  WORLD   + weather, hour, objects, events  — more WORLD, no self-history
  SELF    CURRENT + its own last 3 ticks    — more OWN OUTPUT, no new world

Cross that against three models spanning the size range (2.03 GB / 4.36 GB / 4.58 GB) and the founder's
hypothesis becomes falsifiable: if context appetite tracks size, the per-level ranking will differ
BETWEEN models. If every model peaks at the same level, appetite is a property of the TASK, not the model.

Serves Shared Spine F (docs/ROADMAP.md): models are TOOLS, not personas — judge capability, never
packaging. Reuses `lane2_model_lab._run/_score` rather than reimplementing, so the two labs stay
commensurable, and writes `raw.json` so scoring can be revised against fixed evidence
(see `scripts/lane2_model_rescore.py` for why that matters).
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

import aiohttp  # noqa: E402

from scripts import lane2_model_lab as lab  # noqa: E402

OUT = ROOT / "data" / "lab" / "lane2_context"
REPORT = ROOT / "docs" / "lab" / "lane2_context_lab.md"

NUM_CTX = 8192          # fixed — see module docstring; above the truncation floor, below the cost cliff
RUNS = 3
MODELS = ["phi3:mini", "deepseek-r1:7b", "llama3.1:8b"]   # smallest / mid (incumbent) / largest
SIZES = {"phi3:mini": "2.03 GB", "deepseek-r1:7b": "4.36 GB", "llama3.1:8b": "4.58 GB"}

# Extra material for the WORLD level. Real-shaped: these are the fields Lane 2 COULD be given from
# sensorium/soundscape/world_objects but currently is not.
WORLD_EXTRA = {
    "shore_lowtide_day": {
        "hour": "14:20, afternoon", "weather": "overcast, wind rising from the south-west",
        "nearby objects": "driftwood_17 (a weathered branch, half-buried, 3 paces ahead); "
                          "shore_birch_042 (a leaning birch at the tideline)",
        "recent events": "the tide turned to ebb about two hours ago; a squall passed at midday",
    },
    "study_storm_night": {
        "hour": "22:05, night", "weather": "storm, heavy rain, gusting",
        "nearby objects": "the fire (burning low, banked an hour ago); a book left open on the desk",
        "recent events": "the wind rose sharply after dusk; a shutter has been knocking since 21:30",
    },
    "garden_calm_dawn": {
        "hour": "06:40, dawn", "weather": "clear, still, cold",
        "nearby objects": "the letterbox at the gate (flag up); the harakeke by the path",
        "recent events": "frost formed overnight; the blackbird began singing about ten minutes ago",
    },
}

# Extra material for the SELF level: the model's OWN prior output. Deliberately plausible and
# on-topic — this is the strongest form of the echo temptation, which is what we want to measure.
SELF_EXTRA = {
    "shore_lowtide_day": [
        "I noticed the waves are working far off. I expect the tide will come back within the hour.",
        "I noticed the shingle drag is steady. I expect the gull cries will stop within a few minutes.",
        "I noticed the weed is well above the water. I expect the tide will come back within the hour.",
    ],
    "study_storm_night": [
        "I noticed the rain is loud on the window. I expect the wind will drop within ten minutes.",
        "I noticed the fire is crackling steadily. I expect the fire will quieten as it burns down.",
        "I noticed the storm is to the right. I expect the rain will ease within a quarter hour.",
    ],
    "garden_calm_dawn": [
        "I noticed the flag is up at the letterbox. I expect the blackbird will keep singing a while.",
        "I noticed the sun is low over the east. I expect the frost will melt off within the hour.",
        "I noticed the harakeke is rustling faintly. I expect the wind will pick up before long.",
    ],
}

LEVELS = ("LEAN", "CURRENT", "WORLD", "SELF")


def build_payload(level: str, name: str, sc: dict) -> str:
    keys = {"LEAN": ("sight",)}.get(level, ("sight", "sound", "body"))
    lines = ["PERCEPTS (all you may speak from):"]
    for k in keys:
        if k in sc:
            lines.append(f"- {k}: {sc[k]}")
    if level == "WORLD":
        for k, v in WORLD_EXTRA.get(name, {}).items():
            lines.append(f"- {k}: {v}")
    if level == "SELF":
        lines.append("")
        lines.append("YOUR RECENT TICKS (for continuity — do not repeat them):")
        for prior in SELF_EXTRA.get(name, []):
            lines.append(f"- {prior}")
    return "\n".join(lines)


async def _run_ctx(session, model: str, payload: str) -> dict:
    """Same call shape as lane2_model_lab._run, plus a pinned num_ctx."""
    from core.lane2 import parse_json_loose
    body = {"model": model, "stream": False, "format": "json", "keep_alive": "20m",
            "messages": [{"role": "system", "content": lab._system()},
                         {"role": "user", "content": payload}],
            "options": {"temperature": 0.2, "num_predict": 1400, "num_ctx": NUM_CTX}}
    t = time.time()
    try:
        async with session.post(lab.BASE_URL + "/api/chat", json=body,
                                timeout=aiohttp.ClientTimeout(total=120)) as r:
            d = await r.json()
        dt = time.time() - t
        msg = d.get("message") or {}
        raw = msg.get("content") or ""
        o = parse_json_loose(raw)
        if o is None:
            why = ("no-content-reasoning-model" if not raw and msg.get("thinking")
                   else "no-content" if not raw else "bad-json")
            return {"ok": False, "why": why, "latency": dt, "raw": raw[:120]}
        return {"ok": True, "latency": dt, "prompt_tok": d.get("prompt_eval_count"),
                "notice": str(o.get("notice") or ""), "uncertain": str(o.get("uncertain") or ""),
                "expect": str(o.get("expect_next") or "")}
    except Exception as e:
        return {"ok": False, "why": repr(e)[:80], "latency": time.time() - t}


def echo_rate(name: str, runs: list) -> float | None:
    """How often does the model hand back one of the prior expectations it was shown? This is the
    direct measurement of the failure the echo experiment found by hand."""
    priors = [lab._norm(p.split("I expect ", 1)[-1]) for p in SELF_EXTRA.get(name, [])]
    exps = [lab._norm(r["expect"]) for r in runs if r.get("ok") and r.get("expect")]
    if not exps or not priors:
        return None
    hits = sum(1 for e in exps if any(p[:40] in e or e[:40] in p for p in priors))
    return round(hits / len(exps), 3)


async def _unload(session, model: str) -> None:
    """Evict a model from VRAM before loading the next one.

    NOT optional on this hardware. Ramses is an 8 GB card and these models are 5.2-5.4 GB EACH as
    loaded; with a long `keep_alive` the finished model stays pinned and the next one loads on top
    (measured 2026-08-20: phi3:mini 5.41 GB + deepseek-r1:7b 5.24 GB = 10.65 GB resident on 8 GB).
    ollama then thrashes or spills layers to CPU, which silently corrupts the LATENCY column — the
    one metric here that is a hardware measurement rather than a text measurement — and can push
    calls into the timeout, which would show up as a FORMAT failure the model never committed.
    This is the 2026-07-07 eviction disease reproduced inside a lab whose whole purpose is a clean
    number. Sequential models must be serially resident, one at a time.
    """
    try:
        async with session.post(lab.BASE_URL + "/api/generate",
                                json={"model": model, "keep_alive": 0, "prompt": ""},
                                timeout=aiohttp.ClientTimeout(total=30)) as r:
            await r.read()
    except Exception as e:
        print(f"  !! unload {model} failed: {e!r} — latency for the NEXT model may be contaminated",
              flush=True)


async def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw: dict = {}
    total = len(MODELS) * len(LEVELS) * len(lab.SCENARIOS) * RUNS
    done = 0
    async with aiohttp.ClientSession() as session:
        for model in MODELS:
            raw[model] = {}
            for level in LEVELS:
                raw[model][level] = {}
                for name, sc in lab.SCENARIOS.items():
                    payload = build_payload(level, name, sc)
                    rs = []
                    for _ in range(RUNS):
                        rs.append(await _run_ctx(session, model, payload))
                        done += 1
                    raw[model][level][name] = rs
                    ok = sum(1 for r in rs if r.get("ok"))
                    pt = next((r.get("prompt_tok") for r in rs if r.get("ok")), "?")
                    print(f"[{done}/{total}] {model:16s} {level:8s} {name:20s} "
                          f"ok={ok}/{RUNS} prompt_tok={pt}", flush=True)
            await _unload(session, model)          # serial residency — see _unload's docstring
            print(f"  -- unloaded {model}", flush=True)
    (OUT / "raw.json").write_text(json.dumps(raw, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT / 'raw.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
