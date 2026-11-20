"""J-2996: offline test of the pursuits-'advances' gold-set tooling. Temp dir only, no model call, no live data write.
Asserts its own tree, stubs judge_panel._ask, and checks the prompts, the gold set and the scorer."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402,F401  (import core before anything that patches it)
from core import judge_panel as jp  # noqa: E402
import j2996_pursuit_gold_build as build  # noqa: E402
import j2996_pursuit_gold_replay as rp  # noqa: E402
import j2996_pursuit_gold_report as rep  # noqa: E402

assert (ROOT / "core" / "pursuits.py").exists() and ROOT.name != "Nascence"

# 1. V0 is byte-identical to the live prompt in core/pursuits.py
src = (ROOT / "core" / "pursuits.py").read_text(encoding="utf-8")
live_words = ["You are a strict judge of intellectual progress", "Restating the theme in fresh words, circling it, or merely",
              "When uncertain, answer false."]
assert all(w in src for w in live_words)
assert rp.sys_for("V0") == rp.SYS_LIVE
assert "NOT an advance either" in rp.sys_for("V1") and "NOT an advance either" not in rp.sys_for("V2")
assert "ANY of them" in rp.sys_for("V2") and "ANY of them" not in rp.sys_for("V1")
assert "NOT an advance either" in rp.sys_for("V3") and "ANY of them" in rp.sys_for("V3")
for v in rp.VARIANTS:
    assert rp.sys_for(v).endswith('{"advances": true|false, "why": "<one short clause>"}'), v
    assert rp.sys_for(v).startswith("You are a strict judge")

# 2. user blocks
r = {"question": "Q", "prior": "P3", "new": "N", "recent3": ["P1", "P2", "P3"]}
u0, u2 = rp.user_for("V0", r), rp.user_for("V2", r)
assert "ITS PRIOR POSITION: P3" in u0 and "P1" not in u0
assert u2.index("- P1") < u2.index("- P2") < u2.index("- P3") < u2.index("NEW THOUGHT: N")
r2 = {"question": "Q", "prior": "FULLPRIOR", "new": "N", "recent3": ["A", "B", "TRUNC"]}          # pending: last replaced by real prior
assert "- FULLPRIOR" in rp.user_for("V3", r2) and "TRUNC" not in rp.user_for("V3", r2)

# 3. gold set is well-formed (built from the committed files, not live data)
gold = rp.load_gold()
assert len(gold) == 81 and {g["source"] for g in gold} == {"confirmed", "pending"}
assert len({g["pursuit"] for g in gold if g["source"] == "confirmed"}) >= 20
assert {g["gold"] for g in gold} <= {"A", "R", "T"}

# 4. builder: consecutive pairs only, deterministic
items = [{"id": "p1", "status": "dormant", "question": "q", "thoughts": ["a", "b", "c"], "pending": []},
         {"id": "p2", "status": "active", "question": "q2", "thoughts": ["x"], "pending": [
             {"thought": "t", "prior_standing": "ps", "restate_sim": 0.5, "coherent": False, "cycle_id": "c"}]}]
cp = build.confirmed_pairs(items)
assert [(c["prior"], c["new"]) for c in cp] == [("a", "b"), ("b", "c")] and cp[1]["recent3"] == ["a", "b"]
assert build.pending_pairs(items)[0]["prior"] == "ps"
assert build.sample_confirmed(cp, 2, 1) == build.sample_confirmed(cp, 2, 1)

# 5. replay with a stubbed _ask, scratch dir, nothing live written
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    calls = []

    async def fake_ask(session, url, system, user, key, timeout=1, num_predict=200):
        calls.append(url)
        return (url.endswith("11439"), "stub", None, 0.0)       # judge 1 says yes, judge 2 says no -> tiebreak (yi stub says False)

    live_log = jp._LOG
    jp_ = rp._redirect(d)
    assert jp_._LOG.parent == d and jp_.JUDGE_1.startswith("http://127.0.0.1") and jp_.TIEBREAK.endswith("11442")
    assert "LAN-HOST" not in jp_.JUDGE_1 + jp_.JUDGE_2 + jp_.TIEBREAK                 # never Ramses
    jp_._ask = fake_ask
    res = asyncio.run(rp.rule_one(jp_, rp.sys_for("V0"), "u", "t"))
    assert res["how"] == "tiebreak" and res["verdict"] is False and len(calls) == 3, (res, calls)
    assert (d / "judge_panel_log.scratch.jsonl").exists()
    assert str(jp_._LOG) != str(live_log)

    # 6. scorer on synthetic results
    g = {"G1": {"gold": "A", "unsure": False, "source": "confirmed"}, "G2": {"gold": "R", "unsure": False, "source": "confirmed"},
         "G3": {"gold": "T", "unsure": True, "source": "pending"}, "G4": {"gold": "A", "unsure": False, "source": "pending"}}
    mk = lambda gid, v, vd: {"gid": gid, "variant": v, "verdict": vd, "how": "agreed", "v1": vd, "v2": vd}
    resd = {"V0": {"G1": mk("G1", "V0", True), "G2": mk("G2", "V0", True), "G3": mk("G3", "V0", True), "G4": mk("G4", "V0", False)},
            "V1": {"G1": mk("G1", "V1", True), "G2": mk("G2", "V1", False), "G3": mk("G3", "V1", False), "G4": mk("G4", "V1", None)}}
    text = rep.score(g, resd)
    assert "FALSE-KEEP (gold non-advance passed): 2/2" in text and "FALSE-KEEP (gold non-advance passed): 0/2" in text
    assert "FALSE-REJECT (gold advance refused): 1/2" in text
    assert "KEEP RATE on the panel-confirmed sample: 2/2" in text and "KEEP RATE on the panel-confirmed sample: 1/2" in text
    assert "pass->fail 2 (of which correct, gold non-advance: 2" in text
    assert rep.kappa([(True, True), (False, False)]) == 1.0
    lo, hi = rep.wilson(5, 10)
    assert 0.23 < lo < 0.25 and 0.75 < hi < 0.77
print("J-2996 pursuits gold tooling test OK")
