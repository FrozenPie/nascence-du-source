"""J-4193 / D-0810 fast-track: replay the second-look `kind` label offline over stands already in the ledger.

Read-only on live data. Uses the production prompt (core.commitment_ledger._SECOND_LOOK_SYS) on the same
cross-family lane. Writes one JSON + one markdown report to --out (default docs/reviews), never to data/.
Usage: python scripts/stand_kind_replay.py [--n 60] [--seed 4193] [--out DIR]
Prints summary only.
"""
import argparse, asyncio, collections, json, random, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import commitment_ledger as cl            # noqa: E402  (import core first, per project rule)
from core.model_client import call_node_json        # noqa: E402
from core.schema import SERVE_CHAINS                # noqa: E402


def load_stands():
    formed, end = {}, {}
    for line in open(cl._LEDGER, encoding="utf-8"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        ev, i = e.get("event"), e.get("id")
        if ev == "formed":
            formed[i] = e
        elif ev in ("achieved", "dissolved") and i in formed:
            end[i] = (ev, e.get("ts", 0) - formed[i].get("ts", 0))
    return formed, end


async def label(sem, lane, s):
    async with sem:
        user = f"SENTENCE: {s['statement'][:300]}\nABOUT: {str(s.get('scope',''))[:120]}"
        try:
            d = await call_node_json(lane, cl._SECOND_LOOK_SYS, user, max_tokens=160, temperature=0.0,
                                     timeout=90, retries=1, tier=3)
            return {"verdict": str(d.get("verdict", "")).lower(), "kind": str(d.get("kind", "")).lower(),
                    "why": str(d.get("why", ""))[:200], "error": None}
        except Exception as exc:
            return {"verdict": None, "kind": None, "why": "", "error": ("timeout" if "TimeoutError" in str(exc) else str(exc)[:100])}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=4193)
    ap.add_argument("--out", default=str(ROOT / "docs" / "reviews"))
    a = ap.parse_args()
    formed, end = load_stands()
    ach = [i for i, (ev, _) in end.items() if ev == "achieved" and formed[i].get("load_bearing")]
    dis = [i for i, (ev, _) in end.items() if ev == "dissolved" and formed[i].get("load_bearing")]
    rnd = random.Random(a.seed)
    pick = rnd.sample(ach, min(a.n, len(ach))) + rnd.sample(dis, min(a.n // 3, len(dis)))
    lane = SERVE_CHAINS["judge_mixtral"]
    sem = asyncio.Semaphore(3)
    res = await asyncio.gather(*[label(sem, lane, formed[i]) for i in pick])
    rows = [{"id": i, "end": end[i][0], "life_s": round(end[i][1]), "statement": formed[i]["statement"][:300],
             "scope": formed[i].get("scope", ""), **r} for i, r in zip(pick, res)]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    (out / f"{stamp}_stand_kind_replay.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    for grp in ("achieved", "dissolved"):
        g = [r for r in rows if r["end"] == grp]
        c = collections.Counter(r["kind"] or ("ERR:" + str(r["error"])) for r in g)
        print(grp, len(g), dict(c))
    ok = [r for r in rows if r["kind"]]
    print("labelled", len(ok), "of", len(rows), "errors", len(rows) - len(ok))
    print("file", out / f"{stamp}_stand_kind_replay.json")


if __name__ == "__main__":
    asyncio.run(main())
