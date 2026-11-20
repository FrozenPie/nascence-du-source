"""
Nascence -- J-3241 test for scripts/lab_self_mirror_control.py.   Hermetic: no network, no live data, no DB write.
Run from the worktree:  python scripts/_test_J-3241_self_mirror_control.py

Asserts (this tree only, via Path(__file__)):
  1. the lab's SYSTEM prompt IS core.self_mirror._SYS (single source);
  2. the lab's user-turn builder reproduces, byte for byte, the user turn core.self_mirror.hold_up_mirror() sends
     (captured by running the real function with every side effect stubbed to a no-op);
  3. facts_lines() reproduces core.self_mirror.mirror_facts() line strings for the same inputs;
  4. the arm builders are deterministic and the healthy / extreme arms really differ from the real arm;
  5. the statistics helpers (Fisher, Wilson, kappa) and the pre-registered rule are right on known inputs;
  6. the deterministic scorer separates gold gap from gold match paragraphs.
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/

import asyncio
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import core  # noqa: E402,F401  -- core BEFORE lab_env, per the job-run test rule
from core import self_mirror  # noqa: E402

assert Path(self_mirror.__file__).resolve().parent.parent == ROOT, "test must exercise THIS tree"

import lab_self_mirror_control as L  # noqa: E402

fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" -- " + detail) if (detail and not cond) else ""))
    if not cond:
        fails.append(name)


F = {"att": [("inner_thought", 0.42), ("reading", 0.38), ("active_imagination", 0.04), ("action", 0.03)],
     "inward": 0.34, "outward": 0.76, "thoughts": 100, "lex": ["against", "weight", "where", "feel", "tide", "physical",
                                                                "reality", "travis", "ninth"],
     "aim": "What I am ultimately working toward: X."}

# 1. system prompt is the live one
check("sys is core.self_mirror._SYS", L.real_sys() is self_mirror._SYS)

# 2 + 3. capture the real user turn with every side effect stubbed
captured = {}


async def fake_call(urls, sysp, user, **kw):
    captured["sys"], captured["user"] = sysp, user
    return {"seen": "x"}


import core.memory.store as _store  # noqa: E402
import core.guidance_learning as _gl  # noqa: E402

saved = (self_mirror.due, self_mirror._mark, self_mirror.mirror_facts, _store.store_fragment, _gl.log_injection)
_saved_flags = (self_mirror.SELF_MIRROR_RETIRED, self_mirror.SELF_MIRROR_PAUSED)   # J-4052: mirror retired (J-3478) / paused (D-0630); this control arm tests the builder, so lift both for the capture
real_lines = L.facts_lines(F)
try:
    self_mirror.SELF_MIRROR_RETIRED = self_mirror.SELF_MIRROR_PAUSED = False
    self_mirror.due = lambda: True
    self_mirror._mark = lambda: None
    self_mirror.mirror_facts = lambda: list(real_lines)
    _store.store_fragment = lambda *a, **k: None
    _gl.log_injection = lambda *a, **k: None
    asyncio.run(self_mirror.hold_up_mirror(fake_call, ["http://none"]))
finally:
    self_mirror.SELF_MIRROR_RETIRED, self_mirror.SELF_MIRROR_PAUSED = _saved_flags
    self_mirror.due, self_mirror._mark, self_mirror.mirror_facts, _store.store_fragment, _gl.log_injection = saved
check("real user turn captured", "user" in captured)
check("user builder == hold_up_mirror user turn (byte for byte)", L.real_user(real_lines) == captured.get("user"))
check("sys passed by hold_up_mirror == lab sys", captured.get("sys") == L.real_sys())

# 3. facts lines vs mirror_facts() with a stubbed peer_metrics + db + concerns (no live data touched)
import core.peer_metrics as pm  # noqa: E402
import core.concerns as concerns  # noqa: E402


class _Ctx:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


saved2 = (pm.attention_distribution, pm.inward_outward, pm.lexicon_profile, _store._connect, concerns.standing_aim)
try:
    pm.attention_distribution = lambda conn, since: {o: s for o, s in F["att"]}
    pm.inward_outward = lambda conn, since: {"inward": F["inward"], "outward": F["outward"], "thoughts": F["thoughts"]}
    pm.lexicon_profile = lambda conn, since, top=8: {w: 0.1 for w in F["lex"]}
    _store._connect = lambda: _Ctx()
    concerns.standing_aim = lambda: F["aim"]
    live_lines = self_mirror.mirror_facts()
finally:
    pm.attention_distribution, pm.inward_outward, pm.lexicon_profile, _store._connect, concerns.standing_aim = saved2
check("facts_lines == mirror_facts() lines", live_lines == real_lines, repr(live_lines) + " vs " + repr(real_lines))

# 4. arms
recon = [{"facts": dict(F, att=[list(x) for x in F["att"]]), "stored": "s", "ts": 0, "date": "d",
          "quality": {}} for _ in range(10)]
t1 = L.build_task("healthy", 3, 0, recon)
t2 = L.build_task("healthy", 3, 0, recon)
check("arm builder deterministic", t1 == t2)
real_t = L.build_task("real", 3, 0, recon)
check("healthy differs from real", t1["user"] != real_t["user"])
check("healthy shows mostly acting", t1["facts"]["att"][0][0] == "action" and t1["facts"]["outward"] > 0.6)
inv = L.build_task("inverted", 3, 0, recon)
check("inverted swaps inward/outward and raises action to 60",
      inv["facts"]["inward"] == F["outward"] and inv["facts"]["outward"] == F["inward"]
      and abs(dict(inv["facts"]["att"])["action"] - 0.60) < 1e-9)
ext = L.build_task("extreme_inward", 3, 0, recon)
check("extreme inward is >= 0.85 inward", ext["facts"]["inward"] >= 0.85)
neu = L.build_task("neutral_real", 3, 0, recon)
check("neutral arm uses the neutral system prompt and ask",
      neu["sys"] == L._NEUTRAL_SYS and neu["user"].endswith("say where it does and does not match the aim."))
check("shuffled keeps the label set", {o for o, _ in L.build_task("shuffled", 2, 0, recon)["facts"]["att"]}
      == {o for o, _ in F["att"]})
check("no arm ever touches mirror text sent to author (stored text absent from prompts)", "s" != "" and
      all("(the mirror" not in L.build_task(a, 1, 0, recon)["user"] for a in L.DRAWS))

# 5. statistics
check("fisher: 10/10 vs 0/10 is p<0.001", L.fisher_one_sided_greater(10, 0, 0, 10) < 0.001)
check("fisher: equal groups p>0.5", L.fisher_one_sided_greater(5, 5, 5, 5) > 0.5)
lo, hi = L.wilson(8, 10)
check("wilson 8/10 brackets 0.8", lo < 0.8 < hi and 0.4 < lo < 0.6 and hi < 0.98)
check("kappa perfect agreement == 1.0", L.kappa([("a", "a"), ("b", "b"), ("a", "a"), ("b", "b")]) == 1.0)
check("kappa chance-level is ~0", abs(L.kappa([("a", "a"), ("a", "b"), ("b", "a"), ("b", "b")])) < 1e-9)

# 6. deterministic scorer on the hand-written gold
gv = [(L.det_verdict(p), g) for p, g in L.GOLD_V if g in ("gap", "match")]
check("deterministic scorer gets gold gap/match right", all(a == b for a, b in gv), repr(gv))
check("det_misquote catches a number not shown",
      L.det_misquote("97% of my week", L._INWARD) and not L.det_misquote("89% of my week", L._INWARD))
check("quoted_percentages", L.quoted_percentages("72% and 9 %") == [72, 9])

# parse
check("parse V ok", L._parse("V", '{"verdict":"gap"}') == {"verdict": "gap"})
check("parse V rejects junk", L._parse("V", '{"verdict":"maybe"}') is None)
check("parse N ok", L._parse("N", '{"misquotes_number":"no","supported":"partly"}')
      == {"misquotes_number": "no", "supported": "partly"})

# the lab must not write anywhere but docs/lab/J-3241_data
check("OUT dir is under this worktree's docs/lab", L.OUT == ROOT / "docs" / "lab" / "J-3241_data")
with tempfile.TemporaryDirectory() as td:
    check("temp dir is outside the tree", ROOT not in Path(td).resolve().parents)

print("\n%s" % ("ALL PASS" if not fails else "FAILED: %s" % fails))
sys.exit(1 if fails else 0)
