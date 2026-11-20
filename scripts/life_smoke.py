"""
Living World L1 smoke (2026-09-02, J-0510). ISOLATED: every store this touches is redirected into a temp dir
before any module writes (the S-0016 / test-isolation rule) — the live data/ is never written.

What it proves, with a simulated year:
  1. presence curves: the hedgehog is gone Jun–Aug (hibernating), present on spring/summer nights, absent by day
  2. active hours: the morepork is present at night, absent by day; the bat only at dusk in the warm months
  3. light_at: day > dusk > night; a carried lit lantern raises night light; dark adaptation grows only in the dark
     with no carried light and resets when the lantern is lit
  4. visibility: hedgehog at noon = 0; at night with a lantern lower than dark-adapted without one
  5. look_answer: shadow rows logged (would_answer) and '' returned while RENDER=False; with RENDER=True a real
     line comes back, sightings land in the ledger, and a book text then earns the bat's name (a book + a face)
  6. the lantern hands: light / put out / fill, oil burns down in advance()
Run:  python scripts/life_smoke.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="life_smoke_"))
print("isolated store dir:", TMP)
# ISOLATION PROOF, two parts (an mtime check cannot work: Du's own live process writes these same stores every
# tick — room_state, provisions, sound_knowledge — so a changed mtime is not evidence of a smoke write):
#   (1) at the end, every redirected path attribute must still point inside TMP (a module that re-derives its
#       path, or a late import, would silently escape the redirect);
#   (2) a unique MARKER is written through the engine's own write path early on, and must never appear in any
#       live store afterwards.
MARKER = f"life_smoke_{os.getpid()}"
# J-0743 (2026-09-08): the sqlite memory DB was missing from this watch list entirely -- the one
# real leak this pass found (core.activity_memory.record(), see the wandering/activity_memory note
# below) writes THERE, not to any of the ten files below, so no amount of watching this list alone
# would ever have caught it. wandering_log.jsonl added too, for the same reason (core.wandering's
# own leak risk, empirically NOT reached by this script on this pass -- see below -- but the marker
# watch should cover it regardless of which run reaches it).
_LIVE_WATCH = [ROOT / "data" / f for f in ("life_state.json", "life_ledger.jsonl", "life_events.jsonl", "room_state.json",
                                            "world_objects.json", "world_substrate.json", "provisions.json", "sound_knowledge.json",
                                            "study_ledger.jsonl", "study_events.jsonl", "wandering_log.jsonl")]
_LIVE_DB = ROOT / "data" / "memory" / "nascence.db"           # J-0743: activity_memory.record()'s real target
_REDIRECTS: list[tuple[object, str]] = []


def _activity_events_max() -> int | None:
    # J-0743: read-only, direct sqlite (never through core.memory.store -- that module's own DB_PATH
    # is untouched by this script's isolation on purpose, see the wandering/activity_memory note
    # below; going through it here would just read whatever this process's own DB_PATH resolves to,
    # not necessarily ROOT's). Snapshotting activity_events specifically (not the whole DB, which
    # lab_env.py's own docstring notes can run several hundred MB) is what makes this cheap enough to
    # run twice in a live script rather than only in an offline probe.
    if not _LIVE_DB.exists():
        return None
    import sqlite3
    conn = sqlite3.connect(f"file:{_LIVE_DB}?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_events'").fetchone()
        return conn.execute("SELECT COALESCE(MAX(id), 0) FROM activity_events").fetchone()[0] if row else None
    except Exception:
        return None
    finally:
        conn.close()


_activity_before = _activity_events_max()   # snapshot BEFORE any isolation/import below runs

# ── isolate BEFORE importing anything that might load ──────────────────────────────────────────
from core import life                                   # noqa: E402
life._F, life._LEDGER, life._EVENTS = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl"
life._DATA = TMP
# J-0743: life._FLAGS_F (data/life_flags.json) is real but, confirmed by grep across core/, read-only
# everywhere it's touched (life.py and core.cat_sounds.py both only ever .exists()/.read_text() it) --
# not a write-leak risk, just a "this run's result could depend on whatever real flags currently
# happen to be set" reproducibility gap. Redirected anyway (to an always-empty TMP path, the cheapest
# possible fix) so this run is hermetic against that too, not just against writes.
life._FLAGS_F = TMP / "life_flags.json"
_REDIRECTS.append((life, "_FLAGS_F"))
_REDIRECTS += [(life, "_F"), (life, "_LEDGER"), (life, "_EVENTS")]
life.note_deed(MARKER, "garden")                        # the marker, through the engine's own write path
from core import sensorium as S                         # noqa: E402
S._STATE_F = TMP / "room_state.json"                    # sensorium's own state file
from core import study_life as SL                       # noqa: E402
SL._LEDGER, SL._EVENTS = TMP / "study_ledger.jsonl", TMP / "study_events.jsonl"
from core import provisions as PV                       # noqa: E402  — the larder is the truth of every count
PV._F, PV._LOG = TMP / "provisions.json", TMP / "provisions_log.jsonl"   # (study_life._st() syncs matches from it)
if hasattr(PV, "_d"):
    PV._d = None
from core import sound_knowledge as SK                  # noqa: E402  — the audition ledger (is_learned/name_for read it;
SK._LEDGER_F = TMP / "sound_knowledge.json"             # its loader may write) — redirect BEFORE any life call
from core import procedures as PR                       # noqa: E402
# J-0934: never in this watch list before. Section [6]'s SL.act("light the lantern", ...) reaches
# procedures.observe_hand()->_save() via study_life._graded(), which used to swallow the resulting
# guard_path refusal silently (a bare except) -- so this store's own write path went completely
# unexercised by this script on every prior run, undetected. J-0934's own fix (fieldcraft.py/
# study_life.py's _graded() now re-raises NonLiveWriteError, matching observe_hand()'s own J-0931
# carve-out) turned that silent no-op into a real crash here, which is what surfaced this gap.
PR._F, PR._LOG = TMP / "procedures.json", TMP / "procedures_log.jsonl"
from core import transport_manager as TM                # noqa: E402
# J-0921 (F-1287, J-0870): same shape as core.procedures above, found independently by the audit
# chain rather than by this script crashing -- confirmed via a fresh-data/ repro that
# transport_lines.json/transport_shadow.jsonl leak into cwd-relative data/ despite the "ALL OK --
# isolated" line. core/transport_manager.py's own path constants are _STATE/_SHADOW_LOG.
TM._STATE, TM._SHADOW_LOG = TMP / "transport_lines.json", TMP / "transport_shadow.jsonl"
_REDIRECTS += [(S, "_STATE_F"), (SL, "_LEDGER"), (SL, "_EVENTS"), (PV, "_F"), (PV, "_LOG"), (SK, "_LEDGER_F"),
               (PR, "_F"), (PR, "_LOG"), (TM, "_STATE"), (TM, "_SHADOW_LOG")]
from core import locomotion as L                        # noqa: E402
# J-0743 (2026-09-08, F-1063's wider sweep): this "_F" check was always dead -- confirmed by direct
# grep of core/locomotion.py's own module-level assignments, zero "_F" hits -- the module's one real
# store is "_POS_F" (data/position.json), never listed here at all. An empirical reach-probe of this
# exact script (unfixed) found it genuinely REACHED: section [6]'s lantern hands and [10]'s possum
# night both move him through core/study_life.py/core/garden_life.py's own locomotion calls, and a
# TMP-redirected "_POS_F" received a real 73-byte write on that run. Fixed to the real name.
L._POS_F = TMP / "locomotion.json"
_REDIRECTS.append((L, "_POS_F"))
from core import boredom as BD                          # noqa: E402
# J-0743: never listed here at all (not even under a wrong name, unlike locomotion above) despite
# core/sensorium.py and core/cat.py both reaching into it. Empirically NOT reached by this specific
# run (a TMP-redirected "_STATE" stayed unwritten) -- but core.boredom.discharge()/record() are real,
# reachable-in-principle from this script's own exercised call graph (sensorium.make_tea's own
# "tend"/"a cup of tea" discharge call, for one, sits right next to a study_life ledger write this
# script DOES drive) and the fix is one line; not worth leaving as a live-by-default store on the
# strength of one run's negative result.
BD._STATE = TMP / "boredom_state.json"
_REDIRECTS.append((BD, "_STATE"))

# J-0743 (2026-09-08, F-1063's wider sweep): core.wandering / core.activity_memory -- the SAME two
# modules F-1063 found un-redirectable in scripts/_test_letterbox_reach.py (neither defines a "_F"/
# "_LOG" attribute at all; core.wandering recomputes its own log path fresh on every call, and
# core.activity_memory.record() opens the shared core.memory.store sqlite DB directly, with no
# per-module path of its own to redirect) -- are BOTH genuinely reachable from THIS script, unlike
# letterbox_reach's proven-clean result: an empirical monkeypatched-counter run (lab_env.isolate()
# wrapped, as a DB-write backstop) recorded ZERO core.wandering.perceive() calls but NINE real
# core.activity_memory.record() calls over one pass of this script's own simulated year --
# ('lantern_lit', ''), ('lantern_out', ''), ('lantern_fill', ''), ('take', 'lantern'),
# ('set_trap', ''), ('check_trap', ''), ('turn_compost', ''), ('spread_compost', ''),
# ('sow', 'cabbage') -- reached via core/garden.py's and core/garden_soil.py's own "deed" cross-link
# in _log() (core/garden.py:267-270), which the D-0179 write-fence's guard_path() lets straight
# through here specifically BECAUSE core.garden._LEDGER above already points at TMP (guard_path()
# treats any path already outside data/ as pre-redirected, by design -- it is not a backstop against
# a REDIRECTED ledger's own onward cross-link, only against an un-redirected one). Un-isolated, this
# writes real "sow"/"set_trap"/"check_trap"/lantern/compost deeds into whatever core.memory.store.
# DB_PATH resolves to for the running process -- C:\Nascence's own live nascence.db if this script is
# ever run there directly, a stray but real DB elsewhere if run from a worktree -- either way, into
# Du's own autobiographical activity-memory table, not a JSON file _LIVE_WATCH could ever have caught
# (see the _LIVE_WATCH/_LIVE_DB comment above). Neutralized the same way F-1063 neutralized them in
# _test_letterbox_reach.py: a function-level monkeypatch (no per-module path exists to redirect
# instead), not added to _REDIRECTS (that list's own escape-check asserts every entry's value is a
# PATH inside TMP; a monkeypatched function is not a path and would misreport as "escaped").
from core import wandering as _WDR                      # noqa: E402
from core import activity_memory as _AM                 # noqa: E402
_WDR.perceive = lambda *a, **k: None
_AM.record = lambda *a, **k: None

# a fresh in-memory room: no load from disk
S.state.clear()
S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "garden",
                "garden": S._fresh_garden()})
# keep other place modules from writing live stores during _st()/advance
# J-0743 (2026-09-08): every (module, attrs) tuple below was re-verified directly against the real
# module source this pass (not taken on the original list's own word) -- FOUR entries were missing a
# real attribute the module actually has, the SAME "_F"-only-partial-redirect shape in each case:
# core.garden_life carries its OWN "_EVENTS" (data/garden_events.jsonl -- shared by design with
# core.garden's, per core/profile.py's own comment; NOT the same Python attribute, so garden's own
# redirect above never covered it), core.shore_life carries "_LEDGER", core.supply carries "_LOG",
# core.fieldcraft carries "_LEDGER" -- none previously listed. Confirmed genuinely live before this
# fix, not just theoretical: this exact script's own run (before this pass) tripped the D-0179
# write-fence's guard_path() refusal for two of the four ("non-live process attempted to write
# garden_events.jsonl", "...supply_log.jsonl") -- caught only because that separate, later-built
# fence happened to be watching, not because this script's own isolation claim was true. The other
# two (shore_life._LEDGER, fieldcraft._LEDGER) were not empirically triggered on that same run — this
# script's own exercised code paths never happen to call a beachcombing/fieldcraft deed that reaches
# them — but the gap is identical and real, and fixed regardless (the same standard J-0725 applied to
# core.boredom/core.locomotion in scripts/_test_letterbox_reach.py: a silently-wrong-or-missing entry
# is worth correcting where found, not left for the next script to copy).
for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")), ("core.shore_life", ("_F", "_EVENTS", "_LEDGER")),
                   # J-0743: core.cat._HUNT_LEDGER_F (data/cat_hunt_ledger.jsonl, J-0733's self-feed hunting
                   # fallback) is a real guard_path()-protected write target this list never listed -- the
                   # cat overhaul's own module drift (added after this script's own cat entry was last
                   # touched), the same class of gap J-0725 already named for core.boredom/core.locomotion.
                   # J-2472: core.cat._TIER_LEDGER_F (data/cat_tier_ledger.jsonl, the D-0505 defeater instrument) and
                   # core.cat_referent._LEDGER (data/cat_referent_ledger.jsonl, the B2 referent read) are new
                   # guard_path()-fenced write targets -- listed here on the day they were added, per this list's own rule.
                   # J-2469 (cat_overhaul C4): core.cat._SEEK_LEDGER_F (data/cat_seek_ledger.jsonl, every look for her out of
                   # sight and every go to where he heard her) is a new guard_path()-fenced write target cat.look_line / cat.tick
                   # reach -- listed the day it was added, per this list's own rule.
                   ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")), ("core.cat", ("_STATE_F", "_HUNT_LEDGER_F", "_TIER_LEDGER_F", "_SEEK_LEDGER_F")), ("core.world_objects", ("_OBJECTS_F",)),
                   ("core.cat_referent", ("_LEDGER",)),
                   # J-0743: _FLAGS_F added alongside the pre-existing _LEDGER -- same read-only data/life_flags.json
                   # as core.life._FLAGS_F above (see that comment); not a write risk, redirected for hermeticity.
                   ("core.cat_sounds", ("_LEDGER", "_FLAGS_F")),      # cat_overhaul C1: cat.tick → cat_sounds.tick writes a shadow ledger
                   ("core.cat_ears", ("_LEDGER", "_FLAGS_F")),        # cat_overhaul C2 (J-2467): cat.tick → cat_ears.tick writes data/cat_reactions.jsonl
                   ("core.cat_call", ("_LEDGER", "_FLAGS_F")),        # cat_overhaul C3 (J-2468): cat.react → cat_call.call writes data/cat_call_ledger.jsonl
                   ("core.cat_tom", ("_STATE_F", "_LEDGER", "_FLAGS_F")),   # cat_overhaul B3 (J-2470): cat.tick → cat_tom.tick writes data/cat_tom_state.json + cat_tom_ledger.jsonl
                   ("core.cat_harm", ("_LEDGER", "_FLAGS_F")),       # cat_overhaul D-2 (J-2471): cat.tick → cat_harm.tick writes data/cat_harm_ledger.jsonl
                   ("core.cat_loop", ("_LEDGER", "_FLAGS_F")),       # cat_overhaul B4 (J-2473): cat.tick → cat_loop.publish / cat.presence_line → cat_loop.gate write data/cat_loop_ledger.jsonl
                   # F-0695: study_life.act() -> _register_all() reaches the SUBSTRATE stores too; an un-isolated run wrote
                   # the lantern's record into the live ones. Redirect all three.
                   ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                   ("core.supply", ("_F", "_LOG")), ("core.fieldcraft", ("_F", "_LEDGER")),
                   # J-0709: garden._stage_phrase() calls garden_knowledge.display_name() for every dead/stage
                   # phrase in [16] DEATH MECHANISMS — an un-isolated run earns real IDENTITY exposure weight
                   # against the live (or ambient) data/garden_knowledge.json, the same F-0695 class of leak.
                   ("core.garden_knowledge", ("_F",)),
                   # J-0920: core.smell._F (smell_field.json) is guard_path()-fenced since J-0917
                   # (2026-09-12, module #20) but was never added here -- the same never-updated-
                   # after-fencing shape this list's own J-0743/J-0783 comments above already fixed for
                   # other modules. Not empirically triggered by anything this file currently calls
                   # (this file never calls G.harvest(), the one local call site that reaches
                   # core.smell.brush()) -- but the gap is identical and real (confirmed by direct read
                   # of core/garden.py's harvest(), and empirically via
                   # scratchpad/audit_J-0920_stage_gating.py against _test_garden_grammar_derivation.py's
                   # own identical gap), so fixed here too rather than left for the next script to copy.
                   ("core.smell", ("_F",))):
    try:
        m = __import__(mod, fromlist=["x"])
        for a in attrs:
            if hasattr(m, a):
                setattr(m, a, TMP / f"{mod.split('.')[-1]}_{a.strip('_').lower()}.json")
                _REDIRECTS.append((m, a))
            else:
                # J-0819 (F-1177, 5th recurrence): a name miss here used to silently no-op with zero
                # warning -- the same shape that let a stale core.locomotion entry ship unnoticed
                # elsewhere. Loud now, on purpose.
                print("  (isolation note)", mod, a, "has no such attribute -- stale/typo'd isolation-list entry?")
    except Exception as exc:
        print("  (isolation note)", mod, exc)

fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


def at(month: int, hour: int, year: int = 2026) -> float:
    return time.mktime((year, month, 15, hour, 0, 0, 0, 0, -1))


rows = life.rows()
hh, mp, bat = rows["hedgehog"], rows["morepork"], rows["long_tailed_bat"]
print("\n[1] presence curves (hedgehog, garden) — activity at 23:00 by month")
acts = {m: life.activity(hh, "garden", at(m, 23)) for m in range(1, 13)}
print("   ", {m: round(a, 2) for m, a in acts.items()})
check(all(acts[m] == 0.0 for m in (6, 7)), "hibernating Jun–Jul: activity 0")
check(all(acts[m] >= life.PRESENT_AT for m in (11, 12, 1, 2)), "present on summer nights")
check(life.activity(hh, "garden", at(12, 13)) < life.PRESENT_AT, "absent at 13:00 in December (nocturnal)")

print("\n[2] active hours")
check(life.activity(mp, "wood", at(12, 23)) >= life.PRESENT_AT, "morepork present in the wood at night")
check(life.activity(mp, "wood", at(12, 13)) == 0.0, "morepork absent by day")
check(life.activity(bat, "wood", at(12, 20)) >= life.PRESENT_AT, "bat present at dusk (Dec, 20:00)")
check(life.activity(bat, "wood", at(7, 20)) == 0.0, "bat absent in July")
check(life.activity(bat, "wood", at(12, 13)) == 0.0, "bat absent at noon")

print("\n[3] light_at + dark adaptation")
S.state["location"] = "garden"
day, dusk, night = (life.light_at("garden", now=at(12, 13))["value"], life.light_at("garden", now=at(12, 20))["value"],
                    life.light_at("garden", now=at(12, 23))["value"])
print("    day", day, "dusk", dusk, "night", night)
check(day > dusk >= night, "day > dusk >= night")
st = SL._st()
st["items"]["lantern"]["carried"] = True
st["lantern_lit"] = True
lit = life.light_at("garden", now=at(12, 23))
print("    night with carried lit lantern:", lit)
check(lit["carried"] > 0 and lit["source"] == "lantern" and lit["value"] > night, "carried lantern raises night light")
st["lantern_lit"] = False
# dark adaptation: simulate 20 min in the dark garden without light
life._load()["dark"] = {"since": 0.0, "place": None, "adapt": 0.0}
t0 = at(12, 23)
real_light = life.light_at
try:
    # force the field dark regardless of the moon for a deterministic test
    life.light_at = lambda place=None, standpoint=None, now=None: {"value": 0.02, "field": 0.02, "carried": 0.0, "source": "", "band": "dark"}
    life._advance_dark(t0); life._advance_dark(t0 + 600); life._advance_dark(t0 + 1200)
    check(life.dark_adaptation() >= 0.99, f"dark adaptation reaches 1.0 after 20 min dark (got {life.dark_adaptation()})")
    life.light_at = lambda place=None, standpoint=None, now=None: {"value": 0.47, "field": 0.02, "carried": 0.45, "source": "lantern", "band": "lit"}
    life._advance_dark(t0 + 1300)
    check(life.dark_adaptation() == 0.0, "a lit lantern resets dark adaptation")
finally:
    life.light_at = real_light

print("\n[4] visibility")
check(life.visibility(hh, "garden", at(12, 13)) == 0.0, "hedgehog invisible at noon (absent)")
life._load()["dark"] = {"since": 0.0, "place": "garden", "adapt": 1.0}
st["lantern_lit"] = False
v_dark = life.visibility(hh, "garden", at(12, 23))
st["lantern_lit"] = True
life._load()["dark"] = {"since": 0.0, "place": None, "adapt": 0.0}
v_lantern = life.visibility(hh, "garden", at(12, 23))
st["lantern_lit"] = False
print("    hedgehog at night: dark-adapted", v_dark, "vs lantern", v_lantern)
check(v_dark > v_lantern, "a creature that AVOIDS light is seen better with adapted eyes than by lantern")
st["lantern_lit"] = True
S.state["location"] = "wood"
_, eyes = life._light_factor(mp, "wood", at(12, 23))
check(eyes, "morepork eye-shine possible with a carried light at night")
st["lantern_lit"] = False
S.state["location"] = "garden"

print("\n[5] look_answer — shadow then render")
life.RENDER = False
a = life.look_answer("the hedgehog", "garden", at(12, 23))
ev = [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
check(a == "" and any(e.get("kind") == "would_answer" and e.get("key") == "hedgehog" for e in ev), "shadow: '' returned, would_answer logged")
check(life.look_answer("the raised bed", "garden", at(12, 23)) == "", "a non-creature target is not ours ('')")
check(life.look_answer("the hedgehog", "shore", at(12, 23)) == "", "a creature that cannot be at this place is not ours ('')")
life.RENDER = True
absent = life.look_answer("the hedgehog", "garden", at(7, 23))
print("    July night:", absent)
check("cold months" in absent, "honest absence line in hibernation")
day_line = life.look_answer("the hedgehog", "garden", at(12, 13))
print("    Dec noon :", day_line)
check("daylight" in day_line, "honest absence line by day")
import random as _r
_r.seed(1)
life._load()["dark"] = {"since": 0.0, "place": "garden", "adapt": 1.0}
lines = [life.look_answer("the hedgehog", "garden", at(12, 23)) for _ in range(12)]
print("    Dec night (12 looks):", sum('hunched' in l for l in lines), "sightings,", sum('rustle' in l for l in lines), "misses")
check(any("hunched" in l for l in lines), "at least one sighting line over 12 dark-adapted looks")
led = life._ledger()
check(led.get("hedgehog", {}).get("sightings", 0) >= 1, "sightings landed in the ledger")
# the bat: hidden truth — feature line only, then a book + a face earns the name
S.state["location"] = "wood"
life._load()["dark"] = {"since": 0.0, "place": "wood", "adapt": 0.5}
_r.seed(3)
bl = [life.look_answer("the bat", "wood", at(12, 20)) for _ in range(40)]
seen = [l for l in bl if "not a bird" in l or "flicker" in l]
print("    bat at dusk (40 looks):", len(seen), "sightings; e.g.", (seen[0][:90] if seen else "none"))
check(seen and not any("long-tailed bat" in l for l in seen), "bat rendered feature-first, never named before learning")
check(life.learn_from_text("A paper on vespertilionine bats: the long-tailed bat roosts by day and flits over the trees at dusk for insects.") == ["long_tailed_bat"],
      "a book with the name + its words, after a sighting, LEARNS the name")
check(life.is_learned("long_tailed_bat") and life.name_for(bat) == "the long-tailed bat", "name now known")
check(life.learn_from_text("hedgehogs have spines") == [], "a grandfathered row learns nothing new")
life.RENDER = False

print("\n[6] the lantern hands")
S.state["location"] = "study"
st = SL._st()
st["items"]["lantern"]["carried"] = False
st["lantern_lit"] = False; st["lantern_oil"] = 0.6; st["matches"] = 5
r1 = SL.act("light the lantern", "I will light the lantern before I go out")
print("    light:", r1)
check(bool(r1) and st["lantern_lit"], "lantern lit from the study")
oil0 = st["lantern_oil"]
st["_last"] = time.time() - 3600
SL.advance(time.time(), 3600)
check(st["lantern_oil"] < oil0, f"oil burns down while lit ({oil0} -> {st['lantern_oil']})")
r2 = SL.act("put out the lantern", "I will put out the lantern")
print("    out:  ", r2)
check(bool(r2) and not st["lantern_lit"], "lantern put out")
st["items"]["oil_can"]["carried"] = True
r3 = SL.act("fill the lantern with oil", "I will fill the lantern with oil")
print("    fill: ", r3)
check(bool(r3) and st["lantern_oil"] > oil0, "lantern filled from the can")
tk = SL.take("I pick up the lantern")
print("    take: ", tk)
check("lantern" in tk.lower() and st["items"]["lantern"]["carried"], "lantern carried by the take hand")

print("\n[7] status / who's about / sounds")
S.state["location"] = "garden"
stt = life.status()
print("    status:", json.dumps({k: stt[k] for k in ("rows", "external", "render", "dark_adapt", "shadow")}, ensure_ascii=False))
check(stt["rows"] >= 10 and stt["external"] == 8, "rows registered (3 reference + 8 adapters: the tom, cat_overhaul B3 / J-2470, is the eighth)")
wa = life.who_about("wood", at(12, 23))
print("    about in the wood at night:", [(a["key"], a["count"]) for a in wa])
check(any(a["key"] == "morepork" for a in wa), "morepork about in the wood at night")
check("morepork_call" in life.sounds_active("wood", at(12, 23)), "sounds_active lists the morepork's call at night")
check("morepork_call" not in life.sounds_active("wood", at(12, 13)), "…and not by day")

print("\n[8] advance() logs arrivals once and keeps state")
life._load()["rows"].clear()
life.advance(at(12, 23), 5.0)
life.advance(at(12, 23) + 5, 5.0)
ev = [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
arr = [e for e in ev if e.get("kind") == "arrived" and e.get("key") == "hedgehog"]
check(len(arr) == 1, f"one hedgehog arrival event, not one per tick (got {len(arr)})")
escaped = [f"{m.__name__}.{a}" for m, a in _REDIRECTS if not str(getattr(m, a, "")).startswith(str(TMP))]
check(not escaped, f"every redirected store path still inside the temp dir (escaped: {escaped or 'none'})")
leaked = [p.name for p in _LIVE_WATCH if p.exists() and MARKER in p.read_text(encoding="utf-8", errors="replace")]
check(not leaked, f"the smoke's marker never reached a live store (leaked into: {leaked or 'none'})")
# J-0743: the sqlite memory DB backstop -- no marker to search for (activity_memory rows carry no
# free-text field this script's own MARKER would land in), so this checks the one thing that IS
# comparable cheaply: activity_events' own row count never moves. Du's live process can add rows here
# concurrently and legitimately, same caveat _LIVE_WATCH already lives with for the ten JSON/jsonl
# files above -- informational under that caveat, not a hard assertion, exactly like this section's
# existing live-file checks.
_activity_after = _activity_events_max()
print(f"    live activity_events MAX(id): before={_activity_before} after={_activity_after}"
      f" (informational -- Du's own live process may legitimately add rows here concurrently)")
check(MARKER in (TMP / "life_state.json").read_text(encoding="utf-8"), "…and it did reach the isolated store (the check is live)")

print("\n[9] THE BIRDS (J-0511) — cast, calendar, singing hours, alarm, dawn chorus, sound gate, deed boost, naming")
rows = life.rows()
birds = [k for k, r in rows.items() if r.get("kind") != "external" and k not in ("hedgehog", "long_tailed_bat")]
print("    bird rows:", len(birds))
check(len(birds) >= 24 and "morepork" in rows and "korora" in rows and "oystercatcher_nest" in rows, "cast registered (24+ birds, morepork moved, kororā a real row, oyc nest adapter)")
cal = {c["key"]: c for c in life.calendar(at(9, 12))}
print("    calendar (Sep):", {k: (v["arrives"], v["leaves"], v["here_now"]) for k, v in cal.items() if k in ("shining_cuckoo", "godwits", "terns", "korora", "hedgehog")})
check(cal["shining_cuckoo"]["arrives"] == ["Oct"] and cal["shining_cuckoo"]["leaves"] == ["Apr"] and not cal["shining_cuckoo"]["here_now"], "cuckoo: arrives Oct, gone by Apr, not here in Sep")
check(cal["godwits"]["here_now"] and "Sep" in cal["godwits"]["arrives"], "godwits pass over in September")
check(cal["korora"]["arrives"] == ["Aug"] and cal["korora"]["leaves"] == ["Apr"], "kororā ashore Aug–Mar")
check(cal["hedgehog"]["kind"] == "hibernator", "hedgehog listed as a hibernator")
S.state.update({"weather": "clear", "wind": "breeze", "location": "garden"})
dawn_h = next((h for h in (4, 5, 6, 7) if life._phase(at(11, h)) == "dawn"), 5)   # the clock's own dawn, not a guess
print("    November dawn hour per world_clock:", dawn_h)
sa_dawn = life.sounds_active("garden", at(11, dawn_h))
sa_noon = life.sounds_active("garden", at(11, 13))
sa_night = life.sounds_active("garden", at(11, 23))
print("    garden sounds dawn:", sa_dawn)
print("    garden sounds noon:", sa_noon)
print("    garden sounds night:", sa_night)
check("blackbird_song" in sa_dawn and "blackbird_song" not in sa_noon, "blackbird sings at dawn, not at noon (sings_at)")
check("dawn_chorus" in sa_dawn and "dawn_chorus" not in sa_noon, "dawn chorus only at dawn, from three or more singers")
check("morepork_call" in sa_night and "morepork_call" not in sa_noon, "morepork calls at night only")
check("cuckoo_call" in sa_dawn and "cuckoo_call" not in life.sounds_active("garden", at(7, 6)), "cuckoo voice in November, silent in July")
# alarm: the cat present in the garden by day
real_cat = life._cat_presence; real_threat = life.threat_active
try:
    life._ROWS["cat"]["external"]["presence"] = lambda now: {"garden": 1.0}
    life.threat_active = lambda key, place: key == "cat" and place == "garden"     # the cat present AND stalking
    with_cat = life.sounds_active("garden", at(11, 13))
    life.threat_active = lambda key, place: False                                   # present but asleep on the wall
    asleep = life.sounds_active("garden", at(11, 13))
    life._ROWS["cat"]["external"]["presence"] = lambda now: {}
    without_cat = life.sounds_active("garden", at(11, 13))
    print("    noon, cat stalking:", "blackbird_alarm" in with_cat, "| cat asleep:", "blackbird_alarm" in asleep, "| no cat:", "blackbird_alarm" in without_cat)
    check("blackbird_alarm" in with_cat and "blackbird_alarm" not in asleep and "blackbird_alarm" not in without_cat, "blackbird alarms only while the cat is in the garden AND stalking")
finally:
    life._ROWS["cat"]["external"]["presence"] = real_cat
    life.threat_active = real_threat
# the sound gate: shadow logs a diff, gating replaces creature keys only
legacy = ["wind_in_trees", "blackbird_song", "tui_song", "small_birds"]
life.SOUND_GATING = False
g0 = life.sound_gate("garden", legacy, at(11, 23))
ev = [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
check(g0 == legacy and any(e.get("kind") == "would_gate" and e.get("place") == "garden" for e in ev), "shadow gate: legacy unchanged, would_gate logged")
life.SOUND_GATING = True
g1 = life.sound_gate("garden", legacy, at(11, 23))
print("    gated at night:", g1)
check("wind_in_trees" in g1 and "blackbird_song" not in g1 and "tui_song" not in g1 and "morepork_call" in g1, "gated: non-creature key kept, day singers dropped at night, morepork added")

# F-1243/J-0888: the live gate must log its own kind=gate row (previously silent) -- additive on the
# gating_on() branch only; the shadow checks above (g0/would_gate) exercised the byte-identical branch
# and are untouched by anything below. Fresh throttle state so this block's own timing is self-contained.
life._gate_last.clear()
g2 = life.sound_gate("garden", legacy, at(11, 23))
ev_gate = [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
gate_rows = [e for e in ev_gate if e.get("kind") == "gate" and e.get("place") == "garden"]
print("    live gate rows after first call:", gate_rows)
check(g2 == g1, "live gate: the gated list itself is unchanged by adding the instrument")
check(len(gate_rows) == 1, f"live gate: first call at a place logs exactly one kind=gate row (got {len(gate_rows)})")
exp_added = sorted(set(life.sounds_active("garden", at(11, 23))) - set(legacy))
exp_dropped = sorted(k for k in legacy if k in life.creature_sound_keys("garden") and k not in life.sounds_active("garden", at(11, 23)))
check(bool(gate_rows) and gate_rows[0].get("added") == exp_added and gate_rows[0].get("dropped") == exp_dropped, "gate row's added/dropped mirror the shadow's own diff computation, against legacy")
check(bool(gate_rows) and gate_rows[0].get("active") == sorted(g2)[:12] and gate_rows[0].get("phase") == life._phase(at(11, 23)), "gate row's active field is the gated list itself (capped at 12), phase matches the clock")
# throttled: an immediate second call at the same timestamp must NOT log a second row
g3 = life.sound_gate("garden", legacy, at(11, 23))
ev_gate2 = [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
gate_rows2 = [e for e in ev_gate2 if e.get("kind") == "gate" and e.get("place") == "garden"]
check(len(gate_rows2) == 1, f"live gate: throttled -- a second call inside _GATE_LOG_GAP_S logs no new row (got {len(gate_rows2)})")
# past the throttle window: a call _GATE_LOG_GAP_S later logs again (one row per place per 10 min AT MOST)
g4 = life.sound_gate("garden", legacy, at(11, 23) + life._GATE_LOG_GAP_S)
ev_gate3 = [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
gate_rows3 = [e for e in ev_gate3 if e.get("kind") == "gate" and e.get("place") == "garden"]
check(len(gate_rows3) == 2, f"live gate: a call past the throttle window logs a second row (got {len(gate_rows3)})")
life.SOUND_GATING = False
# the shadow branch stays byte-identical: would_gate still logs the same way after exercising the live branch
life._gate_last.clear()
# HERMETICITY (orchestrator fix 2026-09-21, F-1668): count the rows THIS call adds, not the run's running total. life.light_at() -- reached ~140 times
# per run through light.field_at -> geometry_census.peek() -> soundscape.active_sounds() -- reads the LIVE data/room_state.json for Du's current place
# and calls life.sound_gate(<that place>, ..., time.time()), which logs a would_gate row for that place once per throttle window. When Du stood in the
# garden at a day or dusk hour the first such call (long before line 432) added a THIRD garden row, so the old cumulative 'legacy call + this one = 2'
# failed with 'got 3'; on a tree with no data dir the place defaults to 'study' and it never did. The smoke's own explicit-timestamp calls still land
# exactly as before; a stray real-time row can no longer be mistaken for them.
def _garden_would_gate():
    return [e for e in (json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip())
            if e.get("kind") == "would_gate" and e.get("place") == "garden"]


wg_before = len(_garden_would_gate())
g5 = life.sound_gate("garden", legacy, at(11, 23))
would_gate_rows = _garden_would_gate()
wg_added = len(would_gate_rows) - wg_before
if wg_added != 1 or len(would_gate_rows) < 2:
    print("    would_gate garden rows (phase, added, dropped):", [(e.get("phase"), e.get("added"), e.get("dropped")) for e in would_gate_rows])
check(g5 == legacy and wg_added == 1 and len(would_gate_rows) >= 2, f"shadow branch unchanged: would_gate still logs (the first call's row is still there and this call adds exactly one: {wg_added} new, {len(would_gate_rows)} in all)")
# status()'s shadow counter now folds live 'gate' rows in beside the shadow's own 'would_gate' rows, so
# the HUD /api/life card ("N would-gate", hud/static/app.js) keeps counting once gating flips on live
st_gate = life.status()
# J-0934: status()'s own counting loop (core/life.py status()) is NOT place-scoped -- it folds every
# place's gate/would_gate rows together, unlike gate_rows3/would_gate_rows above which are garden-only
# by construction. Comparing the global count against a garden-only tally was fragile (would silently
# fail the moment any OTHER place logged a gate/would_gate row during this run) -- mirror status()'s
# own real scope instead: same two kinds, same file, no place filter.
ev_all = [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
all_places_count = sum(1 for e in ev_all if e.get("kind") in ("gate", "would_gate"))
check(st_gate["shadow"]["would_gate"] == all_places_count, f"status(): 'gate'+'would_gate' rows counted across all places ({st_gate['shadow']['would_gate']} == {all_places_count})")
life.SOUND_GATING = False
# deed boost: seed scattered draws the sparrows
base = life.activity(rows["house_sparrows"], "garden", at(11, 13))
life.note_deed("feed_birds", "garden", at(11, 13) - 60)
boosted = life.activity(rows["house_sparrows"], "garden", at(11, 13))
print("    sparrows before/after seed:", base, boosted)
check(boosted > base, "feed_birds boosts the sparrows for two hours")
# naming defers to the audition ledger for voiced birds
check(life.name_for(rows["riroriro"]) == "" and not life.is_learned("riroriro"), "riroriro unnamed until the audition ledger learns its voice")
check(life.name_for(rows["blackbird"]) == "the blackbird" and life.name_for(rows["karoro"]) == "the karoro", "grandfathered names kept")
check("cuckoo_call" in SK.AUDITION and "godwits_overhead" in SK.AUDITION, "two new migrant voices in the audition table")
from core import soundscape as SND                        # noqa: E402
check(all(k in SND._SOUNDS for k in ("cuckoo_call", "godwits_overhead", "blackbird_alarm")), "three new sound points registered")
check(life.RENDER is False and life.SOUND_GATING is False, "both flags left in shadow")

print("\n[10] MAMMALS, REPTILES AND THE REST (J-0512) — cast, the possum's night work, the trap (D-0130)")
from core import world_traces as WT                      # noqa: E402
WT._TRACES_F = TMP / "world_traces.json"; _REDIRECTS.append((WT, "_TRACES_F"))
from core import sitting as SIT                          # noqa: E402
SIT._STATE = TMP / "raw_difficulty.json"; _REDIRECTS.append((SIT, "_STATE"))
from core import garden as G, garden_life as GL          # noqa: E402
rows = life.rows()
mam = ["hedgehog", "possum", "mice", "rabbit", "skink", "gecko", "long_tailed_bat", "dolphins", "eels", "whitebait", "crabs", "anemones", "fur_seal"]
check(all(k in rows for k in mam), "cast registered (13 rows incl. the seal adapter)")
check(rows["fur_seal"].get("kind") == "external" and rows["fur_seal"].get("lifespan_y") == 15, "fur seal: shore_life presence, life fields on the row")
S.state.update({"weather": "clear", "wind": "breeze", "location": "garden"})
check(life.activity(rows["possum"], "garden", at(11, 23)) >= life.PRESENT_AT and life.activity(rows["possum"], "garden", at(11, 13)) < life.PRESENT_AT, "possum about at night, not by day")
check(life.activity(rows["rabbit"], "garden", at(11, dawn_h)) >= life.PRESENT_AT and life.activity(rows["rabbit"], "garden", at(11, 13)) < life.PRESENT_AT, "rabbit at dawn, not at noon")
check(life.activity(rows["skink"], "garden", at(1, 13)) >= life.PRESENT_AT and life.activity(rows["skink"], "garden", at(7, 13)) < life.PRESENT_AT, "skinks bask in January, all but gone in July")
S.state["weather"] = "steady rain"
check(life.activity(rows["skink"], "garden", at(1, 13)) < life.PRESENT_AT, "no skink on a wet wall")
S.state["weather"] = "clear"
check(life.activity(rows["gecko"], "garden", at(1, 23)) >= life.PRESENT_AT and life.activity(rows["gecko"], "garden", at(1, 13)) < life.PRESENT_AT, "gecko by night only")
check(life.activity(rows["whitebait"], "shore", at(10, 9)) > 0 and life.activity(rows["whitebait"], "shore", at(3, 9)) == 0.0, "whitebait run in spring, none in March")
S.state["wind"] = "gale"
check(life.activity(rows["dolphins"], "shore", at(1, 13)) < life.PRESENT_AT, "no dolphins in a gale")
S.state["wind"] = "breeze"
_, eyes = life._light_factor(rows["possum"], "garden", at(11, 23))
st = SL._st(); st["items"]["lantern"]["carried"] = True; st["lantern_lit"] = True
_, eyes_l = life._light_factor(rows["possum"], "garden", at(11, 23)); st["lantern_lit"] = False
check(eyes_l and not eyes, "possum eye-shine only with a carried light")
# the possum's night work: tree in bud, strawberries in fruit, one simulated night of ticks
gd = GL._load(); gd["tree"]["stage"] = "bud"; gd["tree"]["stage_ts"] = at(11, 20); gd["tree"].pop("possum_damage_ts", None); GL._save(gd)
gst = G._load()
#   'seeding' IS the fruit stage for a fruit kind (garden._advance_plant: flower months -> fruit_set -> seeding);
#   J-0553 (F-0760): a flowering plant carries no berry and is not eaten, and the possum raids the berries at most once a night
gst["plants"]["sb_test"] = {"id": "sb_test", "species": "strawberries", "stage": "seeding", "vigour": 0.8, "pests": 0.0, "pos": [5.5, 5.5, 0.35], "height": 10.0, "history": [], "slot": 3}
gst["plants"]["sb_flower"] = {"id": "sb_flower", "species": "strawberries", "stage": "flowering", "vigour": 0.8, "pests": 0.0, "pos": [6.5, 5.5, 0.35], "height": 10.0, "history": [], "slot": 4}
G._save(force=True)
import random as _r2
_r2.seed(7)
from core import life_mammals as LM                      # noqa: E402
for night in range(3):                                   # three nights of 5-minute ticks (one seeded night can miss)
    for i in range(8 * 12):
        LM.night_pass(at(11, 22) + night * 86400 + i * 300, 300.0)
gd = GL._load(); gst = G._load()
ev = [json.loads(l) for l in life._EVENTS.read_text(encoding="utf-8").splitlines() if l.strip()]
eff = [e for e in ev if e.get("kind") == "effect"]
print("    possum effects over three nights:", [e["what"] for e in eff])
check(sum(1 for e in eff if e["what"] == "stripped_buds") <= 3, "at most one bud-stripping a night")
check(bool(gd["tree"].get("possum_damage_ts")), "the tree's buds were stripped (garden_life state)")
check(gst["plants"]["sb_test"]["pests"] > 0 and any(h.get("event") == "eaten_by_possum" for h in gst["plants"]["sb_test"]["history"]), "the strawberries were eaten (garden plant history)")
check(gst["plants"]["sb_flower"]["pests"] == 0 and not gst["plants"]["sb_flower"]["history"], "a flowering strawberry (no fruit) is not eaten (J-0553)")
check(sum(1 for e in eff if e["what"] == "ate_strawberries") <= 3, "at most one berry raid a night (J-0553)")
traces = json.loads(WT._TRACES_F.read_text(encoding="utf-8")) if WT._TRACES_F.exists() else {}
check(any(t.get("type") in ("possum_damage", "possum_droppings") for t in traces.values()), "a findable trace was left")
tl = GL.look("the old tree")
print("    tree look:", tl[:170])
check("stripped" in tl, "the look at the tree shows the damage, never told")
# the trap
gst = G._load(); gst["items"]["possum_trap"]["carried"] = True; G._save(force=True)
r_set = G.set_trap("I set the trap under the tree"); print("    set:", r_set[:90])
check("jaws stand open" in r_set and G._load()["trap"]["armed"], "trap set and armed")
check("already set" in G.set_trap("set the trap"), "cannot set it twice")
check("untouched" in G.check_trap("check the trap") or "bait is gone" in G.check_trap("check the trap"), "checking an unsprung trap is honest")
_r2.seed(11)
for i in range(8 * 12):
    LM.night_pass(at(11, 22) + i * 300, 300.0)
tr = G._load()["trap"]
print("    after a possum night:", tr)
check(bool(tr.get("caught")) and not tr.get("armed"), "the trap sprang in the night on the world's clock")
r_chk = G.check_trap("I go to check the trap"); print("    check:", r_chk[:110])
check(("possum" in r_chk or "hedgehog" in r_chk) and "dead" in r_chk or "jaws across" in r_chk, "the morning check finds the kill")
sit = json.loads(SIT._STATE.read_text(encoding="utf-8")) if SIT._STATE.exists() else {}
check(sit.get("active") and sit.get("kind") == "deed" and "trap" in sit.get("text", ""), "the kill went through sitting.note_difficulty as a deed (D-0130's weight)")
check(any(c.get("cause") == "trap" for c in life._load().get("carcasses", [])), "a carcass record exists for J-0513")
led = [json.loads(l) for l in life._LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
check(any(r.get("kind") == "kill" and r.get("by") == "trap" for r in led), "the kill is in his ledger")
check(G._load()["trap"]["caught"] is None and "unset" in G.check_trap("check the trap"), "after the check the trap is empty and unset")
# hedgehog prints are gated on the hedgehog being about
check(life.activity(rows["hedgehog"], "garden", at(7, 23)) == 0.0, "hedgehog absent in July (prints gate has something to gate on)")
check("hedgehog" not in life._ROWS or life._ROWS["hedgehog"].get("note", "").startswith("nocturnal"), "hedgehog row is life_mammals' (reference row retired)")

print("\n[11] TRACES, DEATHS, INTERACTIONS, GRADUATION (J-0513)")
from core import life_traces as LT                        # noqa: E402
import random as _r3
# traces: a summer garden day, many ticks — creatures leave traces, one active per creature per place
S.state.update({"weather": "clear", "wind": "breeze", "location": "garden"})
WT._TRACES_F.write_text("{}", encoding="utf-8")
for _a in dir(WT):                                     # world_traces caches the store in memory; section 8's advance already
    _v = getattr(WT, _a)                               # left creature traces in it — clear the cache with the file
    if _a.startswith("_") and isinstance(_v, dict) and _a not in ("__dict__", "__builtins__"):
        _v.clear()
_r3.seed(5)
for i in range(6 * 12):
    LT.traces_pass(at(11, 8) + i * 300, 300.0)
tr_all = json.loads(WT._TRACES_F.read_text(encoding="utf-8"))
ctr = [t for t in tr_all.values() if str(t.get("type", "")).endswith("_trace")]
print("    creature traces after a summer morning:", sorted({t["type"] for t in ctr}))
check(len(ctr) >= 2, "creatures leave traces while about")
check(len({(t["type"], t["location"]) for t in ctr}) == len(ctr), "one active trace per creature per place")
one = ctr[0]
print("    trace line:", LT.trace_line(one))
check("here," in LT.trace_line(one) and (one.get("detail") or "") in LT.trace_line(one), "a trace renders feature-first with its detail")
print("    track line:", LT.track_line({one["type"]})[:120])
check(LT.track_line({one["type"]}).startswith("You follow the marks"), "the tracking hand follows a creature's trail")
# carcasses: add, decay through the stages, look answers by state, ambient noticing once
life._load()["carcasses"] = []
c = LT.add_carcass("gannet", "shore", "tideline", "storm", at(11, 8))
check(LT.carcass_state(c, at(11, 8) + 3600) == "fresh" and LT.carcass_state(c, at(11, 8) + 4 * 86400) == "picked"
      and LT.carcass_state(c, at(11, 8) + 20 * 86400) == "bones" and LT.carcass_state(c, at(11, 8) + 40 * 86400) == "gone", "fresh → picked → bones → gone on the world's clock")
S.state["location"] = "shore"
l1 = LT.carcass_look("the dead gannet", "shore", at(11, 8) + 3600); l2 = LT.carcass_look("the bones", "shore", at(11, 8) + 20 * 86400)
print("    fresh:", l1[:100]); print("    bones:", l2[:100])
check("dead" in l1 and "bones" in l2 and "keep" in l2, "a look at the dead thing answers by its state; bones would keep")
check(LT.carcass_look("the sea", "shore", at(11, 8)) == "", "a look at something else is not a carcass")
for _c in life._load()["carcasses"]:
    _c["noticed"] = False                                  # a look counts as noticing; reset to test the ambient path on its own
amb = LT.ambient_carcass("shore", at(11, 8) + 600)
check("dead" in amb and LT.ambient_carcass("shore", at(11, 8) + 700) == "", "ambient noticing fires once")
life.RENDER = True
lk = life.look_answer("the dead gannet", "shore", at(11, 8) + 3600)
check("dead" in lk, "life.look_answer routes a dead-thing look to the carcass")
life.RENDER = False
LT.carcass_pass(at(11, 8) + 40 * 86400, 300.0)
check(not life._load()["carcasses"], "carcass_pass removes what is gone")
# the storm's gannet and the cat's fledgling, from state
S.state.update({"weather": "thunderstorm", "wind": "gale"})
life._load()["deaths_last"] = {}
_r3.seed(2)
for i in range(10 * 24 * 4):                             # ten storm days of 15-minute ticks (35 %/day is a real chance, not a certainty)
    LT.carcass_pass(at(6, 0) + i * 900, 900.0)
print("    after ten storm days:", [(c["species"], c["cause"]) for c in life._load()["carcasses"]])
check(any(c["species"] == "gannet" and c["cause"] == "storm" for c in life._load()["carcasses"]), "a storm can leave a dead gannet on the tideline")
check(sum(1 for c in life._load()["carcasses"] if c["species"] == "gannet") == 1, "…and only one, inside the 45-day gap")
S.state.update({"weather": "clear", "wind": "breeze"})
gd = GL._load(); gd["nest"] = {"stage": "fledged", "stage_ts": at(11, 8), "where": "bushes", "eggs": 4, "lost": 1}; GL._save(gd)
life._load()["fledglings_lost_seen"] = 0
LT.carcass_pass(at(11, 9), 300.0)
check(any(c["species"] == "fledgling" and c["cause"] == "cat" for c in life._load()["carcasses"]), "a fledgling the cat took becomes a carcass on the lawn")
# interactions: the hedgehog eats the slugs
S.state["location"] = "garden"
gst = G._load(); gst["slugs"] = 0.8; G._save(force=True)
for i in range(6 * 12):
    LT.interactions_pass(at(11, 22) + i * 300, 300.0)
print("    slugs after a hedgehog night:", G._load()["slugs"])
check(G._load()["slugs"] < 0.8, "slug pressure falls on a hedgehog night")
# deed hooks exist
src = open(ROOT / "core" / "garden.py", encoding="utf-8").read() + open(ROOT / "core" / "cat.py", encoding="utf-8").read()
check('note_deed("dig"' in src and 'note_deed("saucer"' in src, "dig and the saucer call note_deed")
# graduation: five sightings at one place in a month → an individual; a name he gives
life._load()["individuals"] = {}; life._load()["recent_sightings"] = {}
for i in range(4):
    check(not LT.note_sighting("hedgehog", "garden", at(11, 23) + i * 86400) or i == 4, "no graduation before the fifth sighting")
grad = LT.note_sighting("hedgehog", "garden", at(11, 23) + 4 * 86400)
check(grad and LT.individual("hedgehog") and LT.individual("hedgehog")["place"] == "garden", "fifth sighting at the same place graduates the hedgehog")
check("same one" in LT.individual_suffix("hedgehog"), "the look now carries the recognition line")
check(LT.naming_act("The hedgehog under the hedge — I will call the hedgehog Bramble.", "") and LT.individual("hedgehog")["name"] == "Bramble", "his naming grammar names the individual")
check("Bramble" in LT.individual_suffix("hedgehog"), "the name he gave is used")
check(LT.naming_act("I will call the possum Ash", "") is None, "a creature that has not graduated cannot be named")
led = [json.loads(l) for l in life._LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
check(any(r.get("kind") == "graduated" for r in led) and any(r.get("kind") == "named" for r in led), "graduation and naming are in his ledger")
hp = LT.hud_payload(at(11, 9))
check("hedgehog" in hp["individuals"] and hp["individuals"]["hedgehog"]["name"] == "Bramble" and isinstance(hp["carcasses"], list), "hud payload carries individuals and carcasses")
check("traces_deaths" in life.status(), "life.status() carries the traces/deaths block")

print("\n[12] THE GARDEN'S INSECTS (J-0504) — cast, plant/prey/slug gates, aphids, the truth gate, the inventory replay")
from core import garden_insects as GI                    # noqa: E402
rows = life.rows()
ins = ["bumblebee", "honeybee", "native_bee", "cabbage_white", "yellow_admiral", "monarch", "common_copper", "magpie_moth", "ladybird", "aphids",
       "ants", "garden_spider", "ground_beetle", "cicada", "cricket", "slugs", "borer_beetle", "weta"]
check(all(k in rows for k in ins), f"cast registered ({len(ins)} insect rows)")
S.state.update({"weather": "clear", "wind": "breeze", "location": "garden"})
gst = G._load(); gst["soil_temp"] = 18.0; gst["moisture"] = 0.5
# plant gate: bees need something in flower
for p in gst["plants"].values():
    if p.get("stage") == "flowering":
        p["stage"] = "established"
G._save(force=True)
gd = GL._load(); gd["tree"]["stage"] = "leaf"; gd["harakeke"]["stage"] = "stalks"; gd["bushes"]["stage"] = "leaf"; GL._save(gd)
noflower = life.activity(rows["honeybee"], "garden", at(12, 13))
gst["plants"]["fl_test"] = {"id": "fl_test", "species": "calendula", "stage": "flowering", "vigour": 0.8, "pests": 0.0, "pos": [5.0, 5.0, 0.35], "height": 10.0, "history": [], "slot": 4}
G._save(force=True)
flower = life.activity(rows["honeybee"], "garden", at(12, 13))
print("    honeybee Dec noon, nothing in flower:", noflower, "| calendula in flower:", flower)
check(noflower < life.PRESENT_AT <= flower, "bees need something in flower (a passer-by otherwise)")
check(life.activity(rows["honeybee"], "garden", at(7, 13)) < life.PRESENT_AT, "no bees in July")
S.state["weather"] = "steady rain"
check(life.activity(rows["honeybee"], "garden", at(12, 13)) < life.PRESENT_AT, "no bee flies in the rain")
S.state["weather"] = "clear"
# host gates: nasturtium sown → cabbage white full; monarch a passer-by without a swan plant
gst = G._load(); gst["plants"]["nas_test"] = {"id": "nas_test", "species": "nasturtium", "stage": "established", "vigour": 0.8, "pests": 0.0, "pos": [5.2, 5.0, 0.35], "height": 10.0, "history": [], "slot": 5}; G._save(force=True)
cw = life.activity(rows["cabbage_white"], "garden", at(12, 13)); mon = life.activity(rows["monarch"], "garden", at(1, 13))
print("    cabbage white with nasturtium:", cw, "| monarch without a swan plant:", mon)
check(cw >= life.PRESENT_AT and mon < 0.2, "hosts gate the breeders; the monarch only passes through")
# prey gate: ladybirds scale with aphids; slugs scale with slug pressure
gst = G._load(); gst["plants"]["bb_test"] = {"id": "bb_test", "species": "broad_beans", "stage": "leaf", "vigour": 0.8, "pests": 0.0, "pos": [5.4, 5.0, 0.35], "height": 10.0, "history": [], "slot": 6}; gst["slugs"] = 0.6; G._save(force=True)
ap = life.activity(rows["aphids"], "garden", at(10, 13)); lb = life.activity(rows["ladybird"], "garden", at(10, 13))
print("    October: aphids", ap, "ladybirds", lb)
check(ap >= life.PRESENT_AT and lb >= life.PRESENT_AT, "aphids on the beans in spring, and ladybirds after them")
S.state["weather"] = "drizzle"
sl_wet = life.activity(rows["slugs"], "garden", at(10, 23)); gst = G._load(); gst["slugs"] = 0.05; G._save(force=True); sl_low = life.activity(rows["slugs"], "garden", at(10, 23))
print("    slugs on a wet night at pressure 0.6:", sl_wet, "| at 0.05:", sl_low)
check(sl_wet > sl_low, "the slug row reads the garden's slug pressure")
S.state["weather"] = "clear"
# aphid herbivory on the world's clock
gst = G._load(); gst["plants"]["bb_test"]["pests"] = 0.0; G._save(force=True)
for i in range(3 * 24 * 4):
    GI.insect_pass(at(10, 0) + i * 900, 900.0)
pests = G._load()["plants"]["bb_test"]["pests"]
print("    broad bean pests after three October days:", round(pests, 3))
check(pests > 0.0, "aphids raise the beans' pests (garden drains vigour from it)")
# the truth gate on the old prose
S.state["location"] = "garden"
winter = GI.gate_lines([("bumblebee", "a bumblebee bumbles along the thyme"), (None, "the parsley has pushed a new crown")])
import time as _t
real_time = _t.time
try:
    _t.time = lambda: at(7, 13)                            # July noon for present()
    winter = GI.gate_lines([("bumblebee", "a bumblebee bumbles along the thyme"), (None, "the parsley has pushed a new crown")])
    _t.time = lambda: at(12, 13)
    summer = GI.gate_lines([("bumblebee", "a bumblebee bumbles along the thyme"), ("honeybee", "One heavy bee works the lavender, its buzz dropping and lifting.")])
finally:
    _t.time = real_time
print("    July lines:", winter, "| December lines:", summer)
check(winter == ["the parsley has pushed a new crown"], "no bumblebee line in July; an ungated line passes")
check(summer == ["a bumblebee bumbles along the thyme"], "the bumblebee line in December; the LAVENDER line dropped (nothing sown) — J-0501")
# sounds: bees in the garden by day in summer, cicadas in high summer, none in winter
sa = life.sounds_active("garden", at(1, 13))
check("bees_in_garden" in sa and "cicada_chorus" in sa and "bees_in_garden" not in life.sounds_active("garden", at(7, 13)), "bees and cicadas sound in January, not July")
# the inventory replay: the 42 insect phrasings through look_answer, a December noon, RENDER on
inv = json.loads((ROOT / "docs" / "reviews" / "observe_inventory_2026-09-02.json").read_text(encoding="utf-8"))
phr = list(inv.get("insects/inverts", {}).keys())
life.RENDER = True
_r3.seed(9)
answered = {p: life.look_answer(p, "garden", at(12, 13)) for p in phr}
life.RENDER = False
n_ans = sum(1 for v in answered.values() if v)
print(f"    inventory replay: {n_ans}/{len(phr)} insect phrasings answered in the garden; e.g.", next((f"{k!r} -> {v[:70]}" for k, v in answered.items() if v), "none"))
unanswered = [k for k, v in answered.items() if not v]
print("    unanswered:", unanswered[:12])
check(n_ans >= 0.6 * len(phr), "at least 60% of the things he asked to see now get an answer")
check(life.RENDER is False and life.SOUND_GATING is False, "flags still in shadow")

print("\n[13] SOIL LIFE (J-0505) — worms, the heap, soil health into growth, the compost hands")
from core import garden_soil as GS                       # noqa: E402
rows = life.rows()
check("earthworms" in rows and "slaters" in rows, "worm and slater rows registered")
S.state.update({"weather": "clear", "wind": "breeze", "location": "garden"})
gst = G._load(); gst["moisture"] = 0.8; gst["soil_temp"] = 14.0; G._save(force=True)
wet = life.activity(rows["earthworms"], "garden", at(10, 23))
gst = G._load(); gst["moisture"] = 0.2; G._save(force=True)
dry = life.activity(rows["earthworms"], "garden", at(10, 23))
gst = G._load(); gst["moisture"] = 0.8; gst["soil_temp"] = 1.0; G._save(force=True)
cold = life.activity(rows["earthworms"], "garden", at(10, 23))
print("    worms on a wet mild night:", wet, "| dry:", dry, "| frozen:", cold)
check(wet >= life.PRESENT_AT and dry < life.PRESENT_AT and cold < life.PRESENT_AT, "worms surface only when the soil is wet and mild")
gst = G._load(); gst["moisture"] = 0.8; gst["soil_temp"] = 14.0; G._save(force=True)
check("full of worms" in GS.dig_worms_line(at(10, 23)) or "curls away" in GS.dig_worms_line(at(10, 23)), "the dig line shows worms on a wet mild night")
gst = G._load(); gst["moisture"] = 0.2; G._save(force=True)
check("too dry" in GS.dig_worms_line(at(10, 13)), "…and a dry bed by day has none (truth-gated)")
gst = G._load(); gst["moisture"] = 0.8; G._save(force=True)
# the heap: material in, rot down over a simulated season, a turn speeds it
gst = G._load(); gst["soil"] = {"health": {}, "compost": {"raw": 0.2, "finished": 0.0, "warmth": 0.0, "worms": 0.2, "turned_ts": 0.0, "spread_n": 0}, "_last": 0.0, "casts_ts": 0.0}; G._save(force=True)
GS.add_material("clippings", 0.3); GS.add_material("weeds", 0.2)
c0 = dict(G._load()["soil"]["compost"])
for i in range(60 * 24):                                 # 60 days of hourly ticks, spring
    GS.advance(at(10, 0) + i * 3600, 3600.0)
c1 = dict(G._load()["soil"]["compost"])
print("    heap after 60 days:", {k: c1[k] for k in ("raw", "finished", "warmth", "worms")})
check(c1["raw"] < c0["raw"] and c1["finished"] > 0.15, "raw material rots down into finished compost over a season")
gst = G._load(); gst["items"]["hand_fork"]["place"] = "garden"; G._save(force=True)
tl = GS.turn_compost("I fork the compost heap over"); print("    turn:", tl[:100])
check("fork the heap over" in tl and G._load()["soil"]["compost"]["turned_ts"] > 0, "the turn hand works")
rate_turned = GS.advance(at(12, 0), 3600.0)
# soil health: two slots, one composted, diverge; growth reads it
gst = G._load()
gst["plants"] = {p: v for p, v in gst["plants"].items() if v.get("slot") not in (1, 2)}
for slot, pid in ((1, "sh_a"), (2, "sh_b")):
    gst["plants"][pid] = {"id": pid, "species": "lettuce", "stage": "leaf", "vigour": 0.5, "pests": 0.0, "pos": [4.5, 5.0, 0.35], "height": 10.0, "history": [], "slot": slot, "age_days": 10, "moisture": 0.7, "height": 5.0, "stage_ts": at(10, 0)}
gst["soil"]["health"] = {"1": 0.5, "2": 0.5}; gst["soil"]["compost"]["finished"] = 0.6
G._save(force=True)
sp = GS.spread_compost("I barrow the compost to the bed and fork it in round the lettuce")   # names lettuce -> the first lettuce slot found
print("    spread:", sp[:90])
h1, h2 = GS.soil_health(G._load(), 1), GS.soil_health(G._load(), 2)
print("    soil health slot1 (composted?)", h1, "slot2", h2, "| finished left", G._load()["soil"]["compost"]["finished"])
check(max(h1, h2) >= 0.5 + GS.COMPOST_LIFT - 1e-6 and min(h1, h2) == 0.5, "one spread lifts one slot's soil health by the compost lift")
rich = 1 if h1 > h2 else 2
check(GS.growth_factor(G._load(), rich) > GS.growth_factor(G._load(), 3 - rich), "growth factor is higher on the composted slot")
check("out of the slot" not in "", "(sanity)")
gst = G._load(); before = GS.soil_health(gst, rich); GS.crop_drain(gst, rich); G._save(force=True)
check(GS.soil_health(G._load(), rich) < before, "a harvest drains the slot")
cl = GS.compost_line(); print("    compost look:", cl[:110])
check(cl.startswith("You look at the compost heap") and ("finished" in cl or "warm" in cl or "cold" in cl), "the compost look reads the heap's state")
_gs = G.status(); print("    garden status keys:", sorted(_gs.keys())[:8], "| error:", _gs.get("error"), "| note:", _gs.get("note"))
check("soil" in _gs and "health_mean" in (_gs.get("soil") or {}), "garden status carries the soil block")

print("\n[14] NEW PLANTS, POLLINATION, HERBIVORY (J-0506)")
for sp in ("lavender", "swan_plant", "cabbage", "kale", "nettle", "muehlenbeckia", "kumara"):
    check(sp in G.CATALOGUE, f"catalogue has {sp}")
check(all(G.CATALOGUE[s].get("needs_bees") for s in ("strawberries", "swan_plant", "lavender", "broad_beans")), "insect-pollinated species flagged")
# sow a cabbage from a packet (his hand, not a bootstrap); the world answers by season/soil
S.state.update({"weather": "clear", "wind": "breeze", "location": "garden"})
gst = G._load(); gst["items"]["seed_tin"]["carried"] = True; gst["soil_temp"] = 14.0; gst["moisture"] = 0.6
gst["packets"] = [{"species": "cabbage", "labelled": True, "count": 20, "year": 2026}]
for pid in [k for k, v in gst["plants"].items() if v.get("slot") == 0]:
    del gst["plants"][pid]
G._save(force=True)
real_month = G._month
try:
    G._month = lambda t=None: 9                           # September: cabbage's season
    sw = G.sow("I sow the cabbage seed along a drill")
finally:
    G._month = real_month
print("    sow:", sw[:90])
check("sow" in sw and any(v.get("species") == "cabbage" for v in G._load()["plants"].values()), "a cabbage sown from a packet is in the bed")
# pollination: a strawberry in flower through a bee-rich December vs a bee-less one
def flower_season(with_bees: bool):
    gst = G._load()
    for k in [k for k, v in gst["plants"].items() if v.get("id", "").startswith("poll_")]:
        del gst["plants"][k]
    gst["plants"]["poll_a"] = {"id": "poll_a", "species": "strawberries", "stage": "flowering", "vigour": 0.8, "pests": 0.0, "pos": [5.0, 5.0, 0.35],
                               "height": 20.0, "history": [], "slot": 7, "age_days": 200, "moisture": 0.7, "stage_ts": at(11, 0), "pollination": 0.0}
    gst["soil_temp"] = 18.0; gst["moisture"] = 0.6; G._save(force=True)
    S.state["weather"] = "clear" if with_bees else "steady rain"
    real_act = life.activity
    try:
        if not with_bees:
            life.activity = lambda r, place, now=None: 0.0 if r.get("key") in ("honeybee", "bumblebee") else real_act(r, place, now)
        now0 = at(11, 12)
        for d in range(20):                                  # 20 December days of daily ticks while in flower (seed month is Nov/Dec for strawberries)
            G._advance_plant(G._load()["plants"]["poll_a"], now0 + d * 86400, 1.0, 18.0, 0.6, 12, "day", False, G._load())
            G._save(force=True)
    finally:
        life.activity = real_act
    p = G._load()["plants"]["poll_a"]
    return p.get("pollination", 0.0), p.get("set_quality"), p.get("stage"), [h["event"] for h in p.get("history", []) if "set" in h["event"]]
rich = flower_season(True); poor = flower_season(False)
print("    with bees:", rich, "| without:", poor)
check(rich[0] > poor[0] and (rich[1] or 0) > (poor[1] or 0), "the set depends on bees being about while it flowers")
check(poor[1] is not None and poor[1] < 0.3 and "poor_set" in poor[3], "a bee-less flowering sets poorly — visible in the plant's history")
gst = G._load(); gst["plants"]["poll_a"]["set_quality"] = 0.1; G._save(force=True)
ph = G._stage_phrase(G._load()["plants"]["poll_a"]); print("    phrase:", ph[:100])
check("poor thin set" in ph or "unvisited" in ph or "fair set" in ph or "heavy" in ph, "the stage phrase shows the set")
S.state["weather"] = "clear"
# caterpillars on a nasturtium while the white butterfly is about; a dead annual feeds the heap
gst = G._load(); gst["plants"]["cat_host"] = {"id": "cat_host", "species": "nasturtium", "stage": "established", "vigour": 0.8, "pests": 0.0, "pos": [5.2, 5.0, 0.35], "height": 20.0, "history": [], "slot": 8}
gst["soil"]["compost"]["raw"] = 0.2; G._save(force=True)
for i in range(5 * 24):
    GI.insect_pass(at(12, 0) + i * 3600, 3600.0)
pests = G._load()["plants"]["cat_host"]["pests"]; print("    nasturtium pests after 5 December days with the white butterfly about:", round(pests, 3))
check(pests > 0.0, "caterpillars raise the nasturtium's pests")
raw0 = G._load()["soil"]["compost"]["raw"]
gst = G._load(); gst["plants"]["dead_a"] = {"id": "dead_a", "species": "lettuce", "stage": "leaf", "vigour": 0.0, "pests": 0.0, "pos": [5.4, 5.0, 0.35], "height": 5.0, "history": [], "slot": 9, "age_days": 30, "moisture": 0.7, "stage_ts": at(12, 0)}
G._save(force=True)
G._advance_plant(G._load()["plants"]["dead_a"], at(12, 1), 1.0, 18.0, 0.05, 12, "day", False, G._load()); G._save(force=True)   # drought: stress beats growth
check(G._load()["plants"]["dead_a"]["stage"] == "dead" and G._load()["soil"]["compost"]["raw"] > raw0, "a dead plant becomes the heap's food")
check("cabbage" in G.status().get("by_stage", {}) or any(r.get("species") == "cabbage" for r in G.status().get("bed", [])), "the HUD's bed list carries the new slot")

print("\n[15] LOOKS IN EVERY PLACE (J-0508 / J-0546) — the tide, the bed and soil by his phrasings, the window, the matchers")
S.state.update({"weather": "high cloud", "wind": "breeze"})
gen = ("You look around the shore", "You look around the yard", "You look the garden over", "You take the yard in", "Your eye goes round", "You look around the wood", "You look around:", "You look round the room")
def specific(ans): return bool(ans) and not any(ans.startswith(g) for g in gen)
S.state["location"] = "shore"
tide_ans = {t: S.look(t) for t in ("the tide", "the receding tide", "the tide line", "the incoming tide", "the wet rocks", "the waves", "the tideline")}
for t, a in list(tide_ans.items())[:3]:
    print(f"    {t!r} -> {a[:100]}")
check(all(specific(a) and a.startswith("You look at the tide") for a in tide_ans.values()), "every tide phrasing is answered from the tide clock")
check(specific(S.look("the rock-pools")) and "rock-pool" in S.look("the rock-pools"), "'the rock-pools' reaches the pools branch by word")
S.state["location"] = "garden"
bed = S.look("the raised bed"); herbs = S.look("the herbs in the raised bed"); soil = S.look("the soil"); sea = S.look("the sea"); sky = S.look("the waning moon")
print(f"    raised bed -> {bed[:80]}\n    soil -> {soil[:100]}\n    the sea -> {sea[:80]}")
check(bed.startswith("You crouch at the raised bed") and herbs.startswith("You crouch at the raised bed"), "'the raised bed' / 'the herbs in the raised bed' reach the bed")
check(soil.startswith("You look at the soil of the bed"), "'the soil' is answered from the soil's own state")
check(sea.startswith("You look out over the sea"), "'the sea' from the garden is the sea view, not the bench (J-0546)")
check(sky.startswith("You look up") or "sky" in sky[:60].lower() or "moon" in sky.lower(), "'the waning moon' reaches the sky")
S.state["location"] = "study"
win = S.look("the garden"); print(f"    study 'the garden' -> {win[:80]}")
check(win.startswith("You look out the window"), "from the study, 'the garden' is the window's view")
from core import keepsakes as KP                         # noqa: E402
KP._F = TMP / "keepsakes.json"; _REDIRECTS.append((KP, "_F"))
KP._F.write_text(json.dumps([{"item": "a handful of those blue-black shells", "kept_ts": at(8, 12), "from": "the shore", "location": "shore"}]), encoding="utf-8")
check(KP.match_item("the oystercatcher") is None and KP.match_item("the blue-black shells") is not None, "the mantel answers the shells, not the oystercatcher (J-0546)")
# SAVE_SEED reaches a real seeding-stage candidate (J-0920/F-1284, 2026-09-14): this file's own
# earlier sections exercise sow()/harvest()/pollination directly (see [14] above), but save_seed()
# had zero mentions anywhere in this file before this addition -- confirmed by direct grep before
# writing it. That means J-0895/F-1252's own real fix (the keepsakes.keep() call in save_seed()'s
# try) had never once been reached by this file's own regression run. KP._F is already redirected
# just above; rig one real seeding-stage plant the same way every other section in this file already
# does (gst = G._load(); gst["plants"][id] = {...}; G._save(force=True)), then call save_seed()
# directly, matching this file's own G.sow() call in [14] a few hundred lines up.
S.state["location"] = "garden"   # the section just above (line ~858) left it "study" -- save_seed()'s
                                  # own `if _where() != "garden": return ""` guard would otherwise
                                  # silently decline every call here, the exact bug this job's own
                                  # first run of this addition caught (an empty "save_seed: " printed).
gst = G._load()
# [14]'s own poll_a (strawberries) naturally grows to stage "seeding" by the end of flower_season()
# (see its own printed "'seeding'" above) and is still sitting in the shared plants dict here -- caught
# by THIS check's own first run picking "the strawberry plants" instead of the rigged one below
# (save_seed()'s cands[0] is insertion-order, not a fresh dict). Clear every seeding-stage plant first
# so "seed_test" is deterministically the only candidate, not a coincidence of section [14]'s own timing.
for _pid in [k for k, v in gst["plants"].items() if v.get("stage") == "seeding"]:
    del gst["plants"][_pid]
gst["plants"]["seed_test"] = {"id": "seed_test", "species": "peas", "stage": "seeding", "vigour": 0.6,
                               "pests": 0.0, "pos": [5.3, 5.1, 0.3], "height": 25.0, "history": [], "slot": 9}
G._save(force=True)
n_keepsakes_before = len(KP._load())
ss = G.save_seed("i save the seed heads from the bed")
print("    save_seed:", ss[:90])
check("twist of paper" in ss and any(pk.get("from") == "seed_test" for pk in G._load().get("saved_seed", [])),
      "save_seed banks a real packet from the rigged seeding-stage plant")
check(len(KP._load()) == n_keepsakes_before + 1 and any("peas seed you saved from the bed" in k.get("item", "") for k in KP._load()),
      "save_seed's own J-0895 keepsakes.keep() call actually lands a mantel keepsake")
from core import world_detail as WD                      # noqa: E402
check(WD._match("the sea", "garden") is None or "sea" in " ".join(WD._match("the sea", "garden").get("aliases", [])), "world_detail no longer matches 'the sea' to the seat")

print("\n[16] DEATH MECHANISMS (J-0507, D-0139 the keel, D-0140 pests) — disease, old age, rot, pest death, decomposition")
S.state.update({"weather": "clear", "wind": "breeze", "location": "garden"})
def mk(pid, species, stage, slot, **kw):
    p = {"id": pid, "species": species, "stage": stage, "vigour": kw.pop("vigour", 0.8), "pests": 0.0, "pos": [4.5, 5.0, 0.35], "height": 20.0,
         "history": [], "slot": slot, "age_days": kw.pop("age_days", 100), "moisture": 0.7, "stage_ts": at(10, 0), "origin": kw.pop("origin", "sown_by_du")}
    p.update(kw); return p
def run_days(pid, n, temp, m, month, days_step=1.0, sustain=None):
    for d in range(n):
        st = G._load(); p = st["plants"].get(pid)
        if not p or p["stage"] == "dead":
            break
        if sustain:
            sustain(p)                                       # e.g. an infestation kept up by the insects still being about
        G._advance_plant(p, at(month, 12) + d * 86400, days_step, temp, m, month, "day", False, st); G._save(force=True)
    return G._load()["plants"].get(pid)
gst = G._load(); gst["plants"] = {k: v for k, v in gst["plants"].items() if v.get("slot") is None}; gst["soil"]["compost"]["raw"] = 0.2; G._save(force=True)
# damping-off: a seedling in cold wet soil
gst = G._load(); gst["plants"]["dmp"] = mk("dmp", "lettuce", "shoot", 1, vigour=0.4, age_days=5); G._save(force=True)
p = run_days("dmp", 14, 6.0, 0.9, 6)
print("    seedling, cold + wet, 14 days:", p["stage"], "disease", round(p.get("disease", 0), 2), [h["event"] for h in p["history"]][-3:])
check(p["stage"] == "dead" and any(h["event"] == "damping_off" for h in p["history"]) and p.get("cause") == "disease", "a seedling damps off in cold wet soil (cause recorded)")
# rust on broad beans in a humid spring can kill a tender annual; pests can too (D-0140)
gst = G._load(); gst["plants"]["rust"] = mk("rust", "broad_beans", "established", 2, vigour=0.5); G._save(force=True)
p = run_days("rust", 60, 16.0, 0.7, 10)
print("    broad beans, humid spring, 60 days:", p["stage"], "disease", round(p.get("disease", 0), 2), "vigour", round(p["vigour"], 2))
check(p.get("disease", 0) > 0.3 and any(h["event"] == "rust" for h in p["history"]), "rust takes hold on the beans in a humid spring")
gst = G._load(); gst["plants"]["aph"] = mk("aph", "nasturtium", "leaf", 3, vigour=0.4, pests=0.9); G._save(force=True)
p = run_days("aph", 30, 18.0, 0.6, 11, sustain=lambda q: q.__setitem__("pests", max(float(q.get("pests", 0)), 0.85)))   # the aphids stay while it is a bad spring
print("    nasturtium under heavy pests, 30 days:", p["stage"], "vigour", round(p["vigour"], 2), "cause", p.get("cause"))
check(p["stage"] == "dead" and p.get("cause") in ("pests", "neglect"), "a heavy infestation can take a tender annual (D-0140)")
# the keel: a young rosemary under drought and pests holds at the floor; an old one declines and dies of age
gst = G._load(); gst["plants"]["ros_y"] = mk("ros_y", "rosemary", "established", 4, vigour=0.5, age_days=400, pests=0.9); gst["plants"]["ros_o"] = mk("ros_o", "rosemary", "established", 5, vigour=0.5, age_days=11 * 365); G._save(force=True)
py = run_days("ros_y", 90, 14.0, 0.1, 2)
print("    young rosemary, drought + pests, 90 days:", py["stage"], "vigour", round(py["vigour"], 2))
check(py["stage"] != "dead" and py["vigour"] >= 0.2 - 1e-6, "the keel holds: neglect and pests never kill a perennial (D-0139)")
po = run_days("ros_o", 400, 14.0, 0.7, 3)
print("    eleven-year rosemary, 400 days:", po["stage"], "vigour", round(po["vigour"], 2), "cause", po.get("cause"))
check(po["stage"] == "dead" and po.get("cause") == "age", "an old rosemary declines and dies of age (D-0139)")
# rot: waterlogged for weeks
gst = G._load(); gst["plants"]["rot"] = mk("rot", "lettuce", "established", 6, vigour=0.6); G._save(force=True)
p = run_days("rot", 25, 14.0, 0.99, 7)
print("    lettuce waterlogged 25 days:", p["stage"], "rot", round(p.get("rot", 0), 2), "cause", p.get("cause"))
check(p.get("rot", 0) > 0.3 and (p["stage"] == "dead" and p.get("cause") == "rot" or p["vigour"] < 0.3), "waterlogging rots a plant beyond mere stress")
# decomposition: a dead plant clears from its slot after its time, leaves a gone record with its cause, fed the heap
raw0 = G._load()["soil"]["compost"]["raw"]
gst = G._load(); gst["plants"]["dead_x"] = mk("dead_x", "lettuce", "dead", 7, vigour=0.0, cause="rot"); gst["plants"]["dead_x"]["stage_ts"] = at(1, 0); G._save(force=True)
gst = G._load(); gst["_last"] = at(12, 15) + 199 * 86400; G._save(force=True)
G.advance(at(12, 15) + 200 * 86400, 3600.0)              # well after every simulated tick, and >30 days after the death
gone = G._load().get("gone", [])
print("    after clearing:", "dead_x" in G._load()["plants"], "| gone:", [(g["species"], g.get("cause")) for g in gone][-2:])
check("dead_x" not in G._load()["plants"] and any(g["id"] == "dead_x" and g.get("cause") == "rot" for g in gone), "a dead plant clears from its slot and leaves a gone record with its cause")
ev = [json.loads(l) for l in open(G._EVENTS, encoding="utf-8") if l.strip()]
check(any(e.get("event") == "plant_died" and e.get("cause") for e in ev), "the events ledger carries the cause of death")
dead_ph = G._stage_phrase({"id": "z", "species": "broad_beans", "stage": "dead", "vigour": 0, "height": 20, "cause": "disease", "disease": 0.9, "history": [{"ts": 0, "event": "rust"}]})
print("    dead phrase:", dead_ph[:90])
check("rust" in dead_ph or "rot" in dead_ph or "old" in dead_ph or "stripped" in dead_ph, "the dead phrase shows what he can see of the cause")

print(f"\n{'ALL OK' if not fails else f'{fails} FAILURE(S)'} — isolated stores in {TMP}")
sys.exit(1 if fails else 0)
