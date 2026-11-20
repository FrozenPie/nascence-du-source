"""Hermetic test for core/world_displacement.py (J-2195 / D-0439). Touches nothing under data/:
the shadow log, curiosity-log seed, balance_world channel, current book and last percept are all stubbed."""
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402  -- must resolve to THIS checkout, never the live tree

assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__

from core import profile, world_displacement as wd  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="j2195_"))
wd._SHADOW = tmp / "world_displacement_shadow.jsonl"
wd._CURIOSITY_LOG = tmp / "curiosity_log.jsonl"          # absent -> empty seed
profile.guard_path = lambda p: Path(p)                   # temp path only (asserted below)
REALITY = {"raw": 0.15}
wd._reality_raw = lambda: REALITY["raw"]
import core.reading as _rd, core.world_substrate as _ws  # noqa: E402
_rd.current_book = lambda: Path("The_Art_of_Rhetoric.txt")
_ws.last_looked_object = lambda: "driftwood_17"

MOT = [f"How does 'mottainai' shape attitude {i} toward waste?" for i in range(20)]
VARIED = [f"What is the history of topic{i} and its rival{i}?" for i in range(20)]
Q0 = "How does the 'mottainai' mindset change how I perceive time?"
ALT_WORLD = "How does the art of rhetoric shape persuasion in public speech?"
ALT_PLAIN = "What drives the migration of eels across oceans?"


def reset(hist):
    wd._history.clear()
    wd._history.extend(hist)
    wd._seeded = True


def last_row():
    import json
    return json.loads(wd._SHADOW.read_text(encoding="utf-8").splitlines()[-1])


ok = True


def check(name, cond):
    global ok
    print(("ok   " if cond else "FAIL ") + name)
    ok = ok and cond


# 1. shadow (switch False): would displace, but q0 still fires
wd.WORLD_DISPLACEMENT_LIVE = False
reset(MOT)
got = wd.choose([Q0, ALT_WORLD], study_subjects=["rhetoric"], rng=lambda: 0.0)
r = last_row()
check("shadow: q0 fires", got == Q0)
check("shadow: row would_displace, not displaced", r["would_displace"] and not r["displaced"])
check("shadow: modal share 1.0, dose 0 < p < W_MAX", r["modal_share"] == 1.0 and 0 < r["p"] <= wd.W_MAX)
check("shadow: world anchor hit on rhetoric", "rhetoric" in r["alt_hits"])

# 2. live (lab only): alternative fires
wd.WORLD_DISPLACEMENT_LIVE = True
reset(MOT)
got = wd.choose([Q0, ALT_WORLD], study_subjects=["rhetoric"], rng=lambda: 0.0)
check("live: world alternative displaces", got == ALT_WORLD and last_row()["displaced"])
check("live: displaced question enters the window", wd._history[-1] == ALT_WORLD)

# 3. never forced: coin above p keeps the topic
reset(MOT)
got = wd.choose([Q0, ALT_WORLD], study_subjects=["rhetoric"], rng=lambda: 0.99)
check("live: coin above p -> he keeps the topic", got == Q0 and not last_row()["would_displace"])

# 4. dwell floor: a varied window gets zero dose
reset(VARIED[:12] + MOT[:8])
got = wd.choose([Q0, ALT_WORLD], study_subjects=["rhetoric"], rng=lambda: 0.0)
r = last_row()
check("floor: share <= SHARE_FLOOR -> p 0, q0", got == Q0 and r["p"] == 0.0 and r["modal_share"] <= wd.SHARE_FLOOR)

# 5. balance_world not in deficit -> no dose
REALITY["raw"] = None
reset(MOT)
got = wd.choose([Q0, ALT_WORLD], study_subjects=["rhetoric"], rng=lambda: 0.0)
check("no reality deficit -> p 0, q0", got == Q0 and last_row()["p"] == 0.0)
REALITY["raw"] = 0.15

# 6. off-topic alternative that touches nothing in the world is NOT used (no topic anti-relock)
reset(MOT)
got = wd.choose([Q0, ALT_PLAIN], study_subjects=["rhetoric"], rng=lambda: 0.0)
r = last_row()
check("no world anchor -> q0, world_alt False, off_topic_alts 1",
      got == Q0 and not r["world_alt"] and r["off_topic_alts"] == 1)

# 7. cold window (< MIN_N) -> no dose
reset(MOT[:5])
got = wd.choose([Q0, ALT_WORLD], study_subjects=["rhetoric"], rng=lambda: 0.0)
check("cold window -> p 0", got == Q0 and last_row()["p"] == 0.0)

# 8. fail-open: a broken clusterer returns q0
import core.topic_perseveration as _tp  # noqa: E402
_orig = _tp.cluster
_tp.cluster = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
reset(MOT)
check("fail-open -> q0", wd.choose([Q0, ALT_WORLD], study_subjects=["rhetoric"], rng=lambda: 0.0) == Q0)
_tp.cluster = _orig

st = wd.status()
check("status counts rows", st["rows"] >= 7 and st["displaced"] == 1)
check("shadow file is under the temp dir", str(wd._SHADOW).startswith(str(tmp)))
wd.WORLD_DISPLACEMENT_LIVE = False
print("ALL OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
