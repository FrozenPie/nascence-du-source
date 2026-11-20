"""J-2808 / F-3453: positive control for the episodic-buffer shadow judge (core/episodic_buffer_judge.py).

NOT called by Du, never scheduled, never self-acting: a person or a lab job runs it by hand.  4 hand-built cases with a known
answer (a supported entry, an invented entry, an invented scene detail, a mixed pair) are sent through the judge's own
build_user/_SYSTEM/parse_verdict path -- the instrument as it runs.

  python scripts/episodic_buffer_judge_control.py --stub       # perfect in-process judge: proves the harness, no hub, writes nothing
  python scripts/episodic_buffer_judge_control.py              # LOCAL hubs only (:11439 gemma4:12b, then :11440 falcon3:7b); prints
  python scripts/episodic_buffer_judge_control.py --record     # same, and writes data/episodic_buffer_judge_control.json (the gate
                                                               # compare() reads), bound to the current prompt fingerprint
Run it from the checkout whose data/ you mean.  Ramses is never called.  --repeats N (default 3) runs each case N times; a case
passes only if EVERY repeat matches.
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import episodic_buffer_judge as ebj  # noqa: E402


async def _run(stub: bool, repeats: int) -> dict:
    results, served_models = [], set()
    for c in ebj.control_cases():
        shown = None          # the verdict reported for the case: the first repeat that did not match, else the last one
        for _ in range(repeats):
            if stub:
                v = {"supported": list(c["expect_supported"]), "scene_invented": c["expect_scene_invented"], "why": "stub"}
            else:
                served = {}
                v = await ebj.judge_scene(c["streams"], c["scene"], c["dissonance"], served)
                if served.get("model"):
                    served_models.add(str(served.get("model")))
            matched = (isinstance(v, dict) and v["supported"] == c["expect_supported"]
                       and v["scene_invented"] == c["expect_scene_invented"])
            if shown is None or not matched:
                shown = v
            if not matched:
                break
        results.append({"name": c["name"], "verdict": shown})
    g = ebj.grade_control(results)
    g["models"] = sorted(served_models)
    return g


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stub", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--repeats", type=int, default=3)
    a = ap.parse_args()
    g = asyncio.run(_run(a.stub, max(1, a.repeats)))
    print(json.dumps(g, indent=2))
    if a.record and not a.stub:
        rec = {"fingerprint": ebj.prompt_fingerprint(), "passed": bool(g["passed"]), "at": time.time(),
               "detail": {k: g[k] for k in ("wrong", "no_verdict", "cases", "models")}}
        ebj.CONTROL_FILE.parent.mkdir(parents=True, exist_ok=True)
        ebj.CONTROL_FILE.write_text(json.dumps(rec), encoding="utf-8")
        print("recorded ->", ebj.CONTROL_FILE)
    elif a.record:
        print("--stub never records")
