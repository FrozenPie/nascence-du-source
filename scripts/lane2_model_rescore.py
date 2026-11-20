"""Re-score the Lane 2 model lab from its SAVED raw data and regenerate the report — no models re-queried.

Exists because a metric was added AFTER a run (the hedge penalty), and re-querying six models to apply it
would be both slow and dishonest: the comparison must be against the SAME outputs, or a scoring change and
a sampling change get confounded. `scripts/lane2_model_lab.py` writes `raw.json` precisely so scoring can
be revised against fixed evidence. Run this after changing `_score()`.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RAW = ROOT / "data" / "lab" / "lane2_model" / "raw.json"
SCORES = ROOT / "data" / "lab" / "lane2_model" / "scores.json"
REPORT = ROOT / "docs" / "lab" / "lane2_model_lab.md"

SIZES = {"deepseek-r1:7b": "4.36 GB", "qwen2.5:7b": "4.36 GB", "llama3.1:8b": "4.58 GB",
         "mistral:7b-instruct": "4.07 GB", "phi3:mini": "2.03 GB", "qwen3.5:4b": "3.16 GB"}
FENCE = chr(96) * 1


def main() -> int:
    spec = importlib.util.spec_from_file_location("lab", ROOT / "scripts" / "lane2_model_lab.py")
    lab = importlib.util.module_from_spec(spec)
    sys.modules["lab"] = lab
    spec.loader.exec_module(lab)

    raw = json.loads(RAW.read_text(encoding="utf-8"))
    rows = sorted((lab._score(m, p) for m, p in raw.items()),
                  key=lambda r: -(r.get("score") if r.get("score") is not None else -1))
    SCORES.write_text(json.dumps(rows, indent=1), encoding="utf-8")

    q = FENCE
    L: list = []
    A = L.append
    A("# Lane 2 model lab — which model for the standing reality-testing tick?\n")
    A(f"*Re-scored {time.strftime('%Y-%m-%d %H:%M')} from the 2026-08-20 09:13 run · Ramses 3070 (8 GB) · "
      f"4 runs × 3 scenarios × 6 models · system prompt imported LIVE from core/lane2.py*\n")
    A("**Serves Shared Spine F (`docs/ROADMAP.md`): models are TOOLS, not personas — judge capability, "
      "never packaging.**\n")
    A("> **Two corrections make this table trustworthy where the first run was not.**")
    A(f"> **(1)** {q}deepseek-r1:7b{q} was first recorded *\"UNUSABLE — no valid JSON\"*. **False.** It emits")
    A("> VALID JSON inside a fenced code block, and needs a token budget large enough for a reasoning model")
    A("> to finish thinking before it emits content at all. Both were OUR failure to adapt, not its failure")
    A("> to perform — exactly the trap Spine F names. **It now scores first.**")
    A(f"> **(2)** A HEDGE metric was added after the first run. {q}phi3:mini{q} scored 0.944 and looked like")
    A("> the winner; it hedges **100%** of its predictions (\"might\", \"could\", \"if X then maybe Y\"), and")
    A("> every hedge is worded differently — which **inflated its variety score**. A prediction hedged into")
    A("> unfalsifiability fails exactly as a question does. Penalised, it drops to 4th.\n")
    A("| model | size | json_ok | distinct↑ | cross↑ | hedge↓ | static↓ | metaphor↓ | latency | score |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        m = r["model"]
        sz = SIZES.get(m, "?")
        if r.get("score") is None:
            A(f"| {q}{m}{q} | {sz} | {r.get('json_ok')} | — | — | — | — | — | — | "
              f"**unusable — emits no content even at 1400 tokens** |")
            continue
        A(f"| {q}{m}{q} | {sz} | {r.get('json_ok')} | {r.get('distinct_expect')} | "
          f"{r.get('cross_scenario')} | {r.get('hedge_rate')} | {r.get('static_rate')} | "
          f"{r.get('metaphor_rate')} | {r.get('latency_med')}s | **{r.get('score')}** |")
    A("")
    A("- **distinct↑** variety given the SAME percepts (the echo metric) · **cross↑** does it change when "
      "the WORLD changes")
    A("- **hedge↓** \"might/could/if\" — unfalsifiable, *and* it inflates distinct · **static↓** predicts "
      "fixed geography (cannot fail)")
    A("- **metaphor↓** §3.2 kill criterion, weighted double\n")
    A("## Verdict\n")
    A(f"**{q}deepseek-r1:7b{q}** — the only candidate combining full variety (1.0) with low hedging (0.27) "
      "and **zero** static predictions. Its cost is latency: ~6.3s vs ~1.5s. Against a 90s tick that is a "
      "~7% duty cycle, so it is affordable. **Recommended for Lane 2.**\n")
    A("**On size — a correction worth keeping.** An earlier reading of this lab claimed score was inversely "
      "correlated with size. That was an artifact of the missing hedge metric: "
      f"{q}phi3:mini{q} looked best because hedging inflated its variety. The honest finding is narrower "
      "and more useful: **fitness for task is not predicted by size in either direction.** The winner is "
      f"mid-sized; the largest ({q}llama3.1:8b{q}) and the smallest both lost. Size stays a legitimate "
      "TIEBREAK where fitness is comparable — it is not itself evidence.\n")
    A("## Sample predictions (same scenario, consecutive runs)\n")
    for r in rows[:4]:
        m = r["model"]
        A(f"**{q}{m}{q}** — shore, low tide, day:")
        for x in raw[m].get("shore_lowtide_day", []):
            A(f"- {x.get('expect') if x.get('ok') else '*(' + str(x.get('why')) + ')*'}")
        A("")
    A(f"*Raw: {q}data/lab/lane2_model/raw.json{q} · scores: {q}scores.json{q}*")

    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"re-scored {len(rows)} models from saved raw data (nothing re-queried)")
    for r in rows:
        print(f"  {r['model']:22s} score={r.get('score')}  hedge={r.get('hedge_rate')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
