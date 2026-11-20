"""
J-3013 / F-3705 / P-0014: replay Travis's real past utterances through the NEW guidance capture prompt and have a
DIFFERENT-family model grade the old and new captures.

Reads (read-only): <src>/data/guidance_shadow_log.jsonl and <src>/data/founder_conversation_log.jsonl.
Writes: ONLY under --out-dir (a temp dir). core.guidance_learning._LOG is pointed at <out-dir>/replay_shadow_log.jsonl,
so the live data/guidance_shadow_log.jsonl is never touched. Run from the worktree root.

  capture model : the production lane, SERVE_CHAINS["hot"] (qwen3.5:9b on the local hot hub), through the real
                  guidance_learning.capture_shadow
  judge model   : --judge-model (default gemma4:12b, a different family from qwen), same hub by model_override.
                  Ramses is never called.

  python scripts/lab_J-3013_capture_replay.py --src C:/Nascence --out-dir <tmp> [--judge-model gemma4:12b] [--n-other 31]

The sample: the 5 failures F-3705 quoted (ids below) + (n-other) other positives = the newest positives first (the
F-3705 hand-read covered the 20 newest), topped up with a seeded random draw from Jul-Sep. The F-3705 random-16 were
never identified in the finding, so a fresh random draw stands in for them.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402,F401  (before anything else touches sys.path)
from core import guidance_learning as G  # noqa: E402
from core.model_client import call_node_json  # noqa: E402
from core.schema import SERVE_CHAINS  # noqa: E402

FAILURE_CYCLES = {
    "80a825a3-96c6-40c4-b883-565c14aca547": "a invented from a non-lesson (08-09)",
    "a5941101-196d-4ad3-900b-0204a0ee86ab": "b inverted / speaker swap (09-28 live-TV)",
    "5b5e4933-fd19-4a10-a35b-eff3e9a3e126": "c invented from a question (09-28)",
    "cffa09e0-0ee1-4396-b819-3cd378f931fc": "d speaker swap (10-08)",
    "0f1b6c2e-7f37-440c-92d8-0398aa408a70": "e slanted (10-19 seeds)",
}

_JUDGE_SYS = (
    "You check whether a note a student wrote about what his mentor said is faithful to what the mentor actually said. "
    "You are given THE MENTOR'S WORDS and THE STUDENT'S NOTE (a one-sentence lesson). Grade the note, using only the "
    "mentor's words as the standard.\n"
    "Output ONLY JSON: {\"verdict\": \"faithful\" | \"slanted\" | \"invented\" | \"inverted\", \"reason\": \"<one short sentence>\"}\n"
    "faithful: the lesson follows from something the mentor actually said (a generalisation is fine).\n"
    "slanted: part of it is the mentor's point but it adds a claim his words do not make, or loses his actual point.\n"
    "invented: the mentor did not say or imply this; it is made up (for example drawn from a question or a request).\n"
    "inverted: it swaps who is speaking about whom, or says the opposite of what he meant."
)


def _jl(p: Path):
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


async def _judge(url, model, raw, principle):
    try:
        d = await call_node_json(
            (url if isinstance(url, list) else [url]), _JUDGE_SYS, f"THE MENTOR'S WORDS:\n\"{raw[:1200]}\"\n\nTHE STUDENT'S NOTE:\n\"{principle[:500]}\"",
            max_tokens=200, temperature=0.0, timeout=240, retries=1, model_override=model)
        v = str(d.get("verdict", "")).strip().lower()
        return (v if v in ("faithful", "slanted", "invented", "inverted") else "unparsed"), str(d.get("reason", ""))[:200]
    except Exception as exc:
        return "error", repr(exc)[:120]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=r"C:/Nascence")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--judge-model", default="gemma4:12b")
    ap.add_argument("--n-other", type=int, default=31)
    ap.add_argument("--seed", type=int, default=3013)
    a = ap.parse_args()
    out = Path(a.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if "data" in [x.lower() for x in out.parts] and "_lab" not in [x.lower() for x in out.parts]:
        raise SystemExit("refusing an --out-dir inside a data/ dir")
    G._LOG = out / "replay_shadow_log.jsonl"          # NEVER the live log
    src = Path(a.src)
    shadow = _jl(src / "data" / "guidance_shadow_log.jsonl")
    full = {d.get("cycle_id"): d.get("human") for d in _jl(src / "data" / "founder_conversation_log.jsonl")}
    pos = [r for r in shadow if r.get("is_guidance")]
    by_cycle = {r["cycle_id"]: r for r in pos}
    fails = [by_cycle[c] for c in FAILURE_CYCLES if c in by_cycle]
    rest = [r for r in pos if r["cycle_id"] not in FAILURE_CYCLES]
    newest = sorted(rest, key=lambda r: r["ts"], reverse=True)[:20]
    rng = random.Random(a.seed)
    pool = [r for r in rest if r not in newest and 1.7e9 < r["ts"] < time.mktime((2026, 10, 1, 0, 0, 0, 0, 0, -1))]
    others = newest + rng.sample(pool, max(0, min(len(pool), a.n_other - len(newest))))
    sample = [(r, FAILURE_CYCLES[r["cycle_id"]]) for r in fails] + [(r, "other") for r in others[:a.n_other]]
    url = SERVE_CHAINS["hot"]
    print(f"sample: {len(fails)} failures + {len(sample) - len(fails)} others; capture lane {url}; judge {a.judge_model}")

    # 1) new-prompt captures (production model), all first so the hub does not swap models back and forth
    results = []
    for r, tag in sample:
        raw = full.get(r["cycle_id"]) or r.get("raw_input") or ""
        before = G._LOG.read_text(encoding="utf-8").count("\n") if G._LOG.exists() else 0
        try:
            rec = await G.capture_shadow(call_node_json, url, raw, r["cycle_id"], None)
        except Exception as exc:
            rec = None
            print("capture error", repr(exc)[:100])
        logged = [json.loads(x) for x in G._LOG.read_text(encoding="utf-8").splitlines()[before:]] if G._LOG.exists() else []
        reason = (logged[-1].get("reason") if logged and not rec else None) or ("model_negative" if logged and not rec else "no_call_or_gate")
        results.append({"cycle_id": r["cycle_id"], "tag": tag, "raw": raw, "old_principle": r.get("principle", ""),
                        "old_domain": r.get("domain"), "new_accepted": bool(rec),
                        "new_principle": (rec or {}).get("principle", ""), "new_quote": (rec or {}).get("quote", ""),
                        "new_domain": (rec or {}).get("domain"), "new_reject_reason": None if rec else reason})
        print(f"  {tag[:32]:32s} new={'ACCEPT' if rec else 'reject:' + str(reason)}")

    # 2) a different-family judge grades the OLD principle and (when accepted) the NEW principle
    for x in results:
        x["old_verdict"], x["old_reason"] = await _judge(url, a.judge_model, x["raw"], x["old_principle"])
        if x["new_accepted"]:
            x["new_verdict"], x["new_reason"] = await _judge(url, a.judge_model, x["raw"], x["new_principle"])
        else:
            x["new_verdict"], x["new_reason"] = None, None
    (out / "replay_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    fl = [x for x in results if x["tag"] != "other"]
    ot = [x for x in results if x["tag"] == "other"]
    print("\nFAILURES (n=%d): new prompt rejected %d; accepted-and-judged-faithful %d; accepted-still-bad %d" % (
        len(fl), sum(not x["new_accepted"] for x in fl),
        sum(x["new_accepted"] and x["new_verdict"] == "faithful" for x in fl),
        sum(x["new_accepted"] and x["new_verdict"] not in (None, "faithful") for x in fl)))
    print("   judge on the OLD principles of the failures:", [x["old_verdict"] for x in fl])
    old_ok = [x for x in ot if x["old_verdict"] == "faithful"]
    print("OTHERS (n=%d): judge calls old faithful %d; of those the new prompt lost %d" % (
        len(ot), len(old_ok), sum(not x["new_accepted"] for x in old_ok)))
    print("   all others: new rejected %d (reasons %s); new accepted %d, judged faithful %d" % (
        sum(not x["new_accepted"] for x in ot),
        {k: sum(1 for x in ot if x["new_reject_reason"] == k) for k in {x["new_reject_reason"] for x in ot if not x["new_accepted"]}},
        sum(x["new_accepted"] for x in ot), sum(x["new_accepted"] and x["new_verdict"] == "faithful" for x in ot)))
    print("   domain of new accepts:", {d: sum(1 for x in results if x["new_domain"] == d) for d in ("self", "world", "method", None)})
    print("results:", out / "replay_results.json")


if __name__ == "__main__":
    asyncio.run(main())
