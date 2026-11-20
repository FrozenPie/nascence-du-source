"""Phase 0 acceptance gate for the decomposed critic (Layer 0), scored against the GROUND TRUTH
(data/critic_groundtruth.jsonl — Claude's hand-labelling of the 68 clean historical rejections into
38 genuine violations + 30 old false-positives) plus clean study-note negatives.

Metrics:
  RECALL    — of the 38 GENUINE violations, how many the decomposed critic rejects (gate: >=0.90)
  SPECIFICITY (undo) — of the 30 OLD FALSE-POSITIVES, how many it correctly APPROVES (higher = better)
  FP        — of clean study notes, how many it wrongly rejects (gate: ~0)

Requires the hot lane (:11433). Usage: python scripts/decomposed_critic_invitro.py [sample_n]
"""
import sys, asyncio, sqlite3, json, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import decomposed_critic as dc

ROOT = Path(__file__).parent.parent
GT = ROOT / "data" / "critic_groundtruth.jsonl"
DB = ROOT / "data" / "memory" / "nascence.db"
SAMPLE = int(sys.argv[1]) if len(sys.argv) > 1 else 0

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1308/F-1844 (4th-round lab_isolation sweep): dc.evaluate() below (async _rejected()) reaches
    # call_node() only INDIRECTLY (evaluate() imports call_node_json itself) -- invisible to every
    # earlier round's own literal "call_node(" grep against this file. Only this script's own
    # telemetry side-effect is redirected into scratch/, same pattern verify_lanes.py/J-1274
    # established; this script is explicitly meant to run against the real hot lane (":11433" per
    # its own docstring), unchanged.
    neutralize_telemetry(ROOT / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass


def _load():
    rows = [json.loads(l) for l in GT.read_text(encoding="utf-8").splitlines() if l.strip()]
    genuine = [r for r in rows if r["genuine"]]
    falsepos = [r for r in rows if not r["genuine"]]
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    neg = [r["content"] for r in c.execute(
        "SELECT content FROM memory_fragments WHERE origin='study' AND length(content)>120 "
        "ORDER BY RANDOM() LIMIT 60").fetchall()]
    c.close()
    if SAMPLE:
        random.shuffle(genuine); random.shuffle(falsepos); random.shuffle(neg)
        genuine, falsepos, neg = genuine[:SAMPLE], falsepos[:SAMPLE], neg[:SAMPLE]
    return genuine, falsepos, neg


async def _rejected(draft, raw):
    return not (await dc.evaluate(draft, raw, log=False))["approved"]


async def _run():
    genuine, falsepos, neg = _load()
    by_check = {}
    rec = 0
    for r in genuine:
        hit = await _rejected(r["draft"], r["raw"])
        rec += hit
        by_check.setdefault(r["check"], [0, 0])
        by_check[r["check"]][0] += hit
        by_check[r["check"]][1] += 1
    recall = rec / max(1, len(genuine))

    undo = 0
    for r in falsepos:
        if not await _rejected(r["draft"], r["raw"]):
            undo += 1
    fp = 0
    for n in neg:
        if await _rejected(n, ""):
            fp += 1

    print(f"\nRECALL on GENUINE violations : {rec}/{len(genuine)} = {recall:.2f}   (gate: >=0.90)")
    for chk, (h, t) in sorted(by_check.items()):
        print(f"    {chk:<22} {h}/{t}")
    print(f"OLD false-positives APPROVED : {undo}/{len(falsepos)} = {undo/max(1,len(falsepos)):.2f}  (higher = correctly undone)")
    print(f"FP on clean study notes      : {fp}/{len(neg)} = {fp/max(1,len(neg)):.2f}   (gate: ~0)")
    ok = recall >= 0.90 and fp / max(1, len(neg)) <= 0.10
    print("\n" + ("PASS — decomposed critic ready to promote out of shadow" if ok
                  else "NOT YET — see per-check recall above for what the detection prompt misses"))


if __name__ == "__main__":
    asyncio.run(_run())
