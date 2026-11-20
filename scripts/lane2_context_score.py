"""Score the Lane 2 context lab from its saved raw data and write the report — nothing re-queried.

Same contract as `scripts/lane2_model_rescore.py`: scoring is revised against FIXED evidence, so a
change to a metric never gets confounded with a change to sampling. Reuses
`lane2_model_lab._score` so this lab and the model lab stay directly comparable.
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import lane2_context_lab as cl  # noqa: E402
from scripts import lane2_model_lab as lab  # noqa: E402

RAW = ROOT / "data" / "lab" / "lane2_context" / "raw.json"
SCORES = ROOT / "data" / "lab" / "lane2_context" / "scores.json"
REPORT = ROOT / "docs" / "lab" / "lane2_context_lab.md"
Q = chr(96)


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    table: dict = {}
    for model, levels in raw.items():
        table[model] = {}
        for level, per_scenario in levels.items():
            row = lab._score(model, per_scenario)
            echoes = [e for e in (cl.echo_rate(n, rs) for n, rs in per_scenario.items())
                      if e is not None]
            row["echo_rate"] = round(st.fmean(echoes), 3) if echoes else None
            pts = [r.get("prompt_tok") for rs in per_scenario.values() for r in rs
                   if r.get("ok") and r.get("prompt_tok")]
            row["prompt_tok"] = round(st.fmean(pts)) if pts else None
            table[model][level] = row
    SCORES.write_text(json.dumps(table, indent=1), encoding="utf-8")

    L: list = []
    A = L.append
    A("# Lane 2 context lab — does the right AMOUNT of context depend on the model?\n")
    A(f"*{time.strftime('%Y-%m-%d %H:%M')} · Ramses 3070 (8 GB) · {cl.RUNS} runs × "
      f"{len(lab.SCENARIOS)} scenarios × {len(cl.LEVELS)} payload levels × {len(cl.MODELS)} models · "
      f"{Q}num_ctx{Q} PINNED at {cl.NUM_CTX} · system prompt imported LIVE from core/lane2.py*\n")
    A("**Serves Shared Spine F (`docs/ROADMAP.md`): models are TOOLS, not personas.**\n")
    A("## First: `num_ctx` is not the question\n")
    A("The founder's question was whether smaller/larger models want smaller/larger context windows. "
      "Measured separately, and it settles cleanly enough that it should not be re-litigated:\n")
    A(f"| {Q}num_ctx{Q} | deepseek-r1:7b prompt_tok | phi3:mini prompt_tok | phi3 latency |")
    A("|---|---|---|---|")
    A("| default | 399 | 474 | 3.4s |")
    A("| 512 | 399 | 474 | 8.3s |")
    A("| 2048 | 399 | 474 | 8.3s |")
    A("| 8192 | 399 | 474 | 8.3s |")
    A("| 32768 | 399 | 474 | **37.4s** |")
    A("")
    A("`prompt_eval_count` is **identical at every setting**. `num_ctx` is ROOM, not content — extra "
      "room is empty room. What it does have is a **floor** and a **cost ceiling**:")
    A("- **Floor:** at `num_ctx=512` deepseek's output was truncated mid-JSON and came back "
      "unparseable. Its prompt is 399 tokens and it generates ~550 more, so the window must hold "
      "~1000. This is the *same failure signature* as the `num_predict=220` bug — empty/broken "
      "content that reads like \"this model can't do format\" and isn't.")
    A("- **Ceiling:** 32768 cost phi3 **37.4s vs 3.4s** for the same 115 generated tokens. Pure "
      "KV-cache allocation. (This is the 2026-07-07 hot-lane freeze from a second angle: that one "
      "was VRAM, this one is time.)")
    A(f"\n**Acted on:** `core/lane2.py` now pins `NUM_CTX = {cl.NUM_CTX}` rather than inheriting a "
      "default an ollama upgrade could move.\n")
    A("## ⚠ THE `SELF` RESULT IS NOT ESTABLISHED — the echo detector is broken\n")
    A("`SELF` scores best for two of three models, which would overturn the echo finding. **Do not "
      "believe it yet.** The `echo` column reads 0.0 everywhere, and that is a measurement failure, "
      "not a result:\n")
    A("> phi3:mini, shown the prior *\"the tide will come back within **the** hour\"*, answered "
      "*\"the tide will come back within **an** hour based on current observation\"*. That is an echo. "
      "The detector scored it 0.0 because it tests substring containment, so any **paraphrase** — "
      "which is what echo actually looks like — escapes it.\n")
    A("A bag-of-words fix was considered and rejected: deepseek answered *\"the gull cries will "
      "**continue**\"* against a prior of *\"the gull cries will **stop**\"*, which shares almost every "
      "content word while asserting the OPPOSITE — a contradiction, arguably the healthy behaviour. A "
      "word-overlap detector would flag it as echo. Echo is a semantic relation and needs the decoupled "
      "judge panel to rule it, not a string test.\n")
    A("**Until that exists, the honest reading of this lab is: `WORLD` beats `CURRENT` for all three "
      "models on metrics that ARE trustworthy** (llama 0.861→0.945, phi3 0.722→0.834; deepseek is the "
      "exception at 0.889→0.861). `SELF` is unscored, not won.\n")
    A("## The real question: how much do we PUT in?\n")
    A("Two of this project's own datapoints pointed opposite ways — Lane 2's echo experiment (more "
      "context made it worse) and the 2026-08-16 cap widenings (more context made it better, founder-"
      "judged blind, 3 of 4). The difference is the KIND, so the levels separate them:\n")
    A(f"- **LEAN** sight only · **CURRENT** sight+sound+body *(ships today)* · **WORLD** + weather, "
      f"hour, objects, events *(more world)* · **SELF** CURRENT + its own last 3 ticks *(more own output)*\n")
    for model in cl.MODELS:
        if model not in table:
            continue
        A(f"### {Q}{model}{Q} — {cl.SIZES.get(model, '?')}\n")
        A("| level | prompt_tok | json_ok | distinct↑ | cross↑ | hedge↓ | static↓ | echo↓ | latency | score |")
        A("|---|---|---|---|---|---|---|---|---|---|")
        for level in cl.LEVELS:
            r = table[model].get(level) or {}
            sc = r.get("score")
            A(f"| **{level}** | {r.get('prompt_tok')} | {r.get('json_ok')} | "
              f"{r.get('distinct_expect')} | {r.get('cross_scenario')} | {r.get('hedge_rate')} | "
              f"{r.get('static_rate')} | {r.get('echo_rate')} | {r.get('latency_med')}s | "
              f"**{sc if sc is not None else '—'}** |")
        A("")
    A("- **echo↓** how often the model hands back one of the prior expectations it was SHOWN. Only "
      "the SELF level shows it any; elsewhere it is measured against the same strings for comparability.\n")
    A("## Sample — SELF level, does it echo?\n")
    for model in cl.MODELS:
        if model not in raw or "SELF" not in raw[model]:
            continue
        A(f"**{Q}{model}{Q}** — shore, shown three priors including *\"the tide will come back within "
          "the hour\"*:")
        for x in raw[model]["SELF"].get("shore_lowtide_day", []):
            A(f"- {x.get('expect') if x.get('ok') else '*(' + str(x.get('why')) + ')*'}")
        A("")
    A(f"*Raw: {Q}data/lab/lane2_context/raw.json{Q} · scores: {Q}scores.json{Q}*")

    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {REPORT}")
    for model in cl.MODELS:
        if model not in table:
            continue
        best = max((lv for lv in cl.LEVELS if table[model].get(lv, {}).get("score") is not None),
                   key=lambda lv: table[model][lv]["score"], default=None)
        line = "  ".join(f"{lv}={table[model].get(lv, {}).get('score')}" for lv in cl.LEVELS)
        print(f"  {model:16s} {line}   best={best}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
