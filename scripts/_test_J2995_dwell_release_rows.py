"""
J-2995 / F-3698: core/sitting.py judge_dwell_release logs the FULL thought the judge saw (thought_full, [:600]),
the prior namings list (priors) and the felt text (felt_seen) as NEW fields on the dwell_release row; every
existing field and the release rule are unchanged. Hermetic: _STATE and _RELEASE_LOG point at a temp dir, the
judge call is a stub, no live data is touched.

  python scripts/_test_J2995_dwell_release_rows.py        # exit 0 = ALL OK
"""
from __future__ import annotations
import asyncio, hashlib, json, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    if not c:
        FAILS += 1


def snap(p):
    return None if not p.exists() else hashlib.sha256(p.read_bytes()).hexdigest()


LIVE = [Path(r"C:\Nascence\data\dwell_release.jsonl"), Path(r"C:\Nascence\data\raw_difficulty.json"),
        ROOT / "data" / "dwell_release.jsonl", ROOT / "data" / "raw_difficulty.json"]
before = {p: snap(p) for p in LIVE}

import core                                       # noqa: E402  (BEFORE anything else -- F-2423)
from core import sitting as S                     # noqa: E402
check(Path(core.__file__).resolve().is_relative_to(ROOT), "core imported from the tree under test")

TMP = Path(tempfile.mkdtemp(prefix="j2995_"))
S._STATE = TMP / "raw_difficulty.json"
S._RELEASE_LOG = TMP / "dwell_release.jsonl"

LONG = "I am frustrated. " + ("x" * 700)
PRIORS = ["I am frustrated.", "It is still here, tighter."]
seen = {}


def make_stub(verdict):
    async def stub(urls, sys_p, user_p, **kw):
        seen["user"] = user_p
        return dict(verdict)
    return stub


def run(verdict, thought, felt="tense"):
    return asyncio.run(S.judge_dwell_release(make_stub(verdict), ["http://stub"], thought, felt, "cyc-1"))


VER = {"shift": True, "clean_clause": True, "concrete": True, "under_arousal": False, "willingness": False,
       "naming": "I am frustrated."}

# [1] a sit with priors, a long thought
S._save({"active": True, "text": "you let go of a stand you had held: X", "kind": "loss", "ts": 1.0, "dwelt": 3,
         "integrable": False, "namings": list(PRIORS)})
rec = run(VER, LONG, "tense: valence low")
rows = [json.loads(l) for l in S._RELEASE_LOG.read_text(encoding="utf-8").splitlines()]
check(len(rows) == 1 and rec is not None, "one row logged")
r = rows[0]
check(r["thought"] == LONG.strip()[:220] and len(r["thought"]) == 220, "existing `thought` is still the 220 cut")
check(r["thought_full"] == LONG.strip()[:600] and len(r["thought_full"]) == 600, "thought_full is the 600 chars the judge read")
check(LONG.strip()[:600] in seen["user"] and LONG.strip()[:601] not in seen["user"], "thought_full == what the judge prompt held")
check(r["priors"] == PRIORS and r["n_priors"] == 2, "priors logged, n_priors unchanged")
for i, n in enumerate(PRIORS, 1):
    check(f"  {i}. {n}" in seen["user"], f"prior {i} in the judge prompt matches the logged list")
check(r["felt_seen"] == "tense: valence low", "felt_seen logged")
for k in ("ts", "cycle_id", "difficulty", "dwelt", "thought", "shift", "clean_clause", "concrete", "under_arousal",
          "willingness", "naming", "n_priors", "released", "reason"):
    check(k in r, f"existing field kept: {k}")
check(r["released"] is True and r["reason"] == "felt_shift", "release rule unchanged (shift+concrete+clean+priors -> released)")

# [2] first naming: no priors -> shift cannot release; priors == []
S._save({"active": True, "text": "d", "kind": "loss", "ts": 2.0, "dwelt": 0, "integrable": False, "namings": []})
run(VER, "I am frustrated, plainly.", "")
r2 = [json.loads(l) for l in S._RELEASE_LOG.read_text(encoding="utf-8").splitlines()][-1]
check(r2["priors"] == [] and r2["n_priors"] == 0 and r2["released"] is False, "first naming: priors [] and not released")
check(r2["felt_seen"] == "unknown", "empty felt logged as the 'unknown' the judge saw")

# [3] a judge that fails writes no row (unchanged)
n = len(S._RELEASE_LOG.read_text(encoding="utf-8").splitlines())
S._save({"active": True, "text": "d", "kind": "loss", "ts": 3.0, "dwelt": 1, "integrable": False, "namings": ["a"]})
asyncio.run(S.judge_dwell_release(make_stub({}), ["http://stub"], "a thought long enough here", "", "c"))
check(len(S._RELEASE_LOG.read_text(encoding="utf-8").splitlines()) == n, "empty judge verdict: no row, no release")

check(all(snap(p) == before[p] for p in LIVE), "live/tree data files byte-identical")
print("ALL OK" if FAILS == 0 else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
