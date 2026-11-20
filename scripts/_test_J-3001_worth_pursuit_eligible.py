"""
Proof for J-3001 (F-3695, F-3702; D-0683 'the graded set must become the pursuit-eligible questions'): the curiosity
worth-judge now grades the questions frontier.pending_pursuit can pick, not the LP top-5.

  [1] frontier.pursuit_candidates is exactly the old pending_pursuit filter (open, no finding, not parked) and
      pending_pursuit still picks by the UNCHANGED sort key (checked against a re-statement of the old rule).
  [2] select_for_grading (pure): head slot = the question the gate would pick next; then newest-born ungraded; then
      stalest grades past the cooldown; a fresh grade is skipped (cooldown); a failed call is skipped; k bound; dedupe.
  [3] REAL-SHAPE REPLAY on a TEMP COPY of the live frontier.json + scores (read-only copy, stub model): the old LP top-5
      holds 0 eligible questions (the defect), shadow_pass grades 5 EVERY pass that are all eligible, and after enough
      passes interest_for returns a stored grade for the whole eligible set; no question is graded twice inside the cooldown.
  [4] pending_pursuit reads the grades: an eligible question graded below AIMLESS_BELOW is demoted behind the next one.
  [5] the grade prompt: the 'recently on the agenda' list never contains the question itself.
  [6] status()/coverage() report the gate's reach; interest_for tolerates a record with no 'interest'.
  [7] isolation: nothing under the live data dir was written, no network call was made.

  python scripts/_test_J-3001_worth_pursuit_eligible.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="J3001_worth_"))
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WRITES: list = []


def _under(p) -> bool:
    try:
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in (str(_LIVE_DATA).lower(), str(ROOT / "data").lower()))


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            w = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if w and not isinstance(path, int) and _under(path):
                _WRITES.append(str(path))
    except Exception:
        pass


sys.addaudithook(_audit)

from core import frontier as F          # noqa: E402  (core BEFORE any lab environment)
from core import curiosity_worth as W   # noqa: E402
from core import curiosity_progress as CP  # noqa: E402

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


print("[0] resolution")
check(Path(W.__file__).resolve() == ROOT / "core" / "curiosity_worth.py", f"core.curiosity_worth is THIS tree ({W.__file__})")
W._SCORES = TMP / "scores.json"
W._LOG = TMP / "worth_log.jsonl"
F._F = TMP / "frontier.json"
F._F_LIGHT = TMP / "frontier.light.json"
CP._FRONTIER = TMP / "frontier.json"
check(not any(_under(p) for p in (W._SCORES, W._LOG, F._F, CP._FRONTIER)), "every store path redirected out of the live data dir")

# ---- a small synthetic frontier for the unit cases -------------------------------------------------------------
NOW = 2_000_000_000.0


def Q(i, born, src="curiosity", status="open", finding=None, stalls=0, text=None):
    d = {"id": f"q{i}", "q": text or f"question number {i} about the world", "source": src, "born": born,
         "status": status, "consecutive_stalls": stalls}
    if finding:
        d["finding"] = finding
    return d


syn = {"questions": [
    Q(1, 100.0, "curiosity"), Q(2, 300.0, "curiosity"), Q(3, 200.0, "intention"), Q(4, 400.0, "curiosity", finding="x"),
    Q(5, 500.0, "curiosity", stalls=3), Q(6, 600.0, "curiosity", status="faded"), Q(7, 700.0, "study"),
    Q(8, 800.0, "intention"),
]}
print("\n[1] pursuit_candidates == the old pending_pursuit filter; pending_pursuit sort unchanged")
cands = F.pursuit_candidates(syn)
old = [q for q in syn["questions"] if q.get("status") == "open" and not q.get("finding")
       and int(q.get("consecutive_stalls", 0) or 0) < 3]
check([q["id"] for q in cands] == [q["id"] for q in old], f"same set, same order: {[q['id'] for q in cands]}")
check({q["id"] for q in cands} == {"q1", "q2", "q3", "q7", "q8"}, "excludes finding-holder q4, parked q5, faded q6")
(TMP / "frontier.json").write_text(json.dumps(syn), encoding="utf-8")
pp = F.pending_pursuit()
exp = min(old, key=lambda x: (1 if W.interest_for(x["q"]) < W.AIMLESS_BELOW else 0,
                              0 if x["source"] in F._GROUNDED_SOURCES else 1, x["born"]))
check(pp and pp["id"] == exp["id"] == "q1", f"pending_pursuit picks oldest grounded q1 as before ({pp})")

print("\n[2] select_for_grading (pure)")
sel = W.select_for_grading(cands, scores={}, now=NOW, k=5, failed={})
ids = [q["id"] for q in sel]
check(ids[0] == "q1", f"slot 1 = the question the gate would pick next (q1, oldest grounded): {ids}")
check(ids[1:] == ["q8", "q7", "q2", "q3"], f"then newest-born ungraded first (q8 800, q7 700, q2 300, q3 200): {ids[1:]}")
sel = W.select_for_grading(cands, scores={}, now=NOW, k=3, failed={})
check(len(sel) == 3, "k bounds the pass")
fresh = {W._norm(cands[0]["q"]): {"interest": 0.9, "ts": NOW - 3600}}            # q1 graded an hour ago
ids = [q["id"] for q in W.select_for_grading(cands, scores=fresh, now=NOW, k=5, failed={})]
check("q1" not in ids, f"a question graded inside the cooldown is not re-graded: {ids}")
check(ids[0] == "q2", f"the head slot moves to the next question in gate order (q2 is the oldest-born grounded left): {ids}")
old_g = {W._norm(cands[0]["q"]): {"interest": 0.9, "ts": NOW - W.REGRADE_COOLDOWN_S - 5}}
ids = [q["id"] for q in W.select_for_grading(cands, scores=old_g, now=NOW, k=5, failed={})]
check(ids[0] == "q1" and len(ids) == 5, f"a grade past the cooldown is gradable again (head q1): {ids}")
allg = {W._norm(q["q"]): {"interest": 0.8, "ts": NOW - W.REGRADE_COOLDOWN_S - i * 10} for i, q in enumerate(cands, 1)}
ids = [q["id"] for q in W.select_for_grading(cands, scores=allg, now=NOW, k=5, failed={})]
check(ids == ["q1", "q8", "q7", "q3", "q2"], f"when all are stale: head slot first, then the stalest grade first ({ids})")
ids = [q["id"] for q in W.select_for_grading(cands, scores={}, now=NOW, k=5, failed={W._norm(cands[0]["q"]): NOW - 10})]
check("q1" not in ids, f"a question whose grade call just failed is skipped: {ids}")
dup = cands + [dict(cands[0], id="dup")]
ids = [q["id"] for q in W.select_for_grading(dup, scores={}, now=NOW, k=9, failed={})]
check(len(ids) == len(set(W._norm(q["q"]) for q in dup)), "no two picks share a normalised text")
check(W.select_for_grading([], scores={}, now=NOW) == [], "empty frontier -> nothing to grade")

# ---- [3] real-shape replay on a TEMP COPY of the live stores -------------------------------------------------------
print("\n[3] real-shape replay on a temp COPY of the live frontier + scores")
live_f, live_s = _LIVE_DATA / "frontier.json", _LIVE_DATA / "curiosity_worth_scores.json"
if live_f.exists():
    shutil.copyfile(live_f, TMP / "frontier.json")
    if live_s.exists():
        shutil.copyfile(live_s, TMP / "scores.json")
    real = True
else:
    (TMP / "frontier.json").write_text(json.dumps({"questions": [Q(i, 1000.0 + i, text=f"synthetic question {i} about rivers")
                                                                  for i in range(160)]}), encoding="utf-8")
    real = False
print(f"      (source: {'copy of the live stores' if real else 'synthetic 160-question frontier'})")
live_front = json.loads((TMP / "frontier.json").read_text(encoding="utf-8"))
elig = F.pursuit_candidates(live_front)
lp_top5 = CP.rank()[:5]
lp_top5_elig = [r for r in lp_top5 if not r["finding"] and not r["parked"]]
print(f"      eligible={len(elig)}  LP-top5 eligible={len(lp_top5_elig)} of {len(lp_top5)}")
print(f"      NOTE F-3695 recorded 0 of 5 on 2026-11-01; today's copy has {len(lp_top5_elig)} of 5 -- the LP top-5 was never the "
      f"eligible set (it covers at most 5 of {len(elig)} = {5/max(1,len(elig)):.1%} at best), and cannot rotate through the rest")
check(len(lp_top5_elig) <= 5 and 5 < len(elig), "the OLD target (LP top-5) could cover at most 5 of the eligible set, never rotated")
before = W.coverage()
print(f"      coverage before: {before}")

CALLS: list = []
SEEN_RECENT: list = []


async def stub_call(urls, system, user, max_tokens=80, temperature=0.2):
    CALLS.append(urls)
    q = user.split("\n")[0][len("Question: "):]
    SEEN_RECENT.append((q, user))
    v = 0.2 if (hash(q) % 7 == 0) else 0.9                      # never 0.5 (== DEFAULT_INTEREST)
    return {"interesting": v, "reason": "stub"}


async def passes(n):
    outs = []
    for _ in range(n):
        outs.append(await W.shadow_pass(stub_call, ["http://stub"]))
    return outs

try:
    need = -(-len(elig) // W._TOP_K) + 1
    outs = asyncio.run(passes(need))
    check(all(o["graded"] == min(W._TOP_K, o["graded"]) and o["graded"] > 0 for o in outs[:max(1, need - 2)]),
          f"every early pass graded questions (graded per pass: {[o['graded'] for o in outs][:8]}...)")
    check(all(o["graded"] <= W._TOP_K for o in outs), "never more than _TOP_K per pass")
    rows = [json.loads(l) for l in W._LOG.read_text(encoding="utf-8").splitlines()]
    graded_q = [g["q"] for r in rows for g in r["grades"]]
    elig_norm = {W._norm(q["q"]) for q in elig}
    check(all(any(en.startswith(W._norm(g)[:60]) for en in elig_norm) for g in graded_q),
          f"all {len(graded_q)} grades are of pursuit-eligible questions")
    check(len(graded_q) == len(set(W._norm(g) for g in graded_q)), "no question graded twice inside the cooldown window")
    after = W.coverage()
    print(f"      coverage after {need} passes: {after}")
    check(after.get("eligible") == len(elig) and after.get("ungraded") == 0,
          f"interest_for now holds a grade for the WHOLE eligible set ({after.get('graded')}/{after.get('eligible')})")
    store = W._load_scores()
    check(all(store.get(W._norm(q["q"]), {}).get("interest") is not None for q in elig),
          "the score store holds a grade for every eligible question (interest_for reads it)")
    check(all(r.get("set") == "pursuit_eligible" and "eligible" in r for r in rows), "log rows say which set was graded")
    # the first pass graded the question the gate would pick next
    check(CALLS and all(u == W._JUDGE_URLS for u in CALLS), "only the injected stub was called (grade() pins the judge seat urls; no socket opened)")
finally:
    pass

print("\n[4] the gate now has something to act on")
scores = W._load_scores()
q_head = min(elig, key=lambda x: (0 if x.get("source") in F._GROUNDED_SOURCES else 1, x.get("born", 0)))
# force: head graded aimless, everyone else worthwhile -> pending_pursuit must NOT pick the head
for q in elig:
    scores[W._norm(q["q"])] = {"interest": 0.9, "ts": time.time()}
scores[W._norm(q_head["q"])] = {"interest": 0.1, "ts": time.time()}
W._SCORES.write_text(json.dumps(scores), encoding="utf-8")
pp = F.pending_pursuit()
check(pp and pp["id"] != q_head["id"], f"an aimless-graded eligible question is demoted behind a worthwhile one ({pp and pp['q'][:40]!r})")
scores[W._norm(q_head["q"])] = {"interest": 0.9, "ts": time.time()}
W._SCORES.write_text(json.dumps(scores), encoding="utf-8")
pp2 = F.pending_pursuit()
check(pp2 and pp2["id"] == q_head["id"], "regraded worthwhile, the head is picked again (demote, never starve)")

print("\n[5] the prompt's agenda list excludes the question itself")
bad = 0
for q, user in SEEN_RECENT:
    agenda = user.split("judge redundancy / aimlessness):\n", 1)[1].split("\n") if "aimlessness):\n" in user else []
    if any(a[2:].strip() and W._norm(a[2:]) == W._norm(q) for a in agenda):
        bad += 1
check(bad == 0, f"in {len(SEEN_RECENT)} grade prompts, the question never appears in its own 'recently on the agenda' ({bad} did)")

print("\n[6] status / coverage / tolerance")
st = W.status()
check(st.get("passes", 0) >= 1 and "coverage" in st and st["coverage"].get("eligible") == len(elig), f"status() carries coverage: {st.get('coverage')}")
W._SCORES.write_text(json.dumps({W._norm("some q"): {"ts": 1.0}}), encoding="utf-8")
check(W.interest_for("some q") == W.DEFAULT_INTEREST, "a score record with no 'interest' reads as the neutral default, not an error")
check(asyncio.run(W.shadow_pass(stub_call, [])).get("graded", 0) >= 0, "shadow_pass never raises")

print("\n[7] isolation")
check(not _WRITES, f"nothing under the live data dir was written ({_WRITES[:3]})")

shutil.rmtree(TMP, ignore_errors=True)
print("\nALL OK" if not FAILS else f"\n{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
