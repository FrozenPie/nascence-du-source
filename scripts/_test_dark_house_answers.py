"""Regression for J-0540 / F-0733 (2026-09-04): truthful dark-house answers.

  (a) the lamp and lantern hands check the match tin BEFORE the oil, so with matches 0 he is never told he struck a
      match he does not have; when both the tin and the reservoir are empty, both facts are said.
  (b) can_read()'s dark line no longer says "box" (which dispatch read as the carrier's box at the gate), and a new
      study family 'candles' takes the candle box / the match tin with an honest count — the two real 09-03
      hands_trace rows ("I will fetch candles from the box", 08:35; "I want to fetch the candles from the box",
      09:47) replay through dispatch.dispatch() and are answered in the study, with the 'collect' reading DROPPED
      as the same clause's compound noun (Action.claims), not STAGED at the garden gate.

ISOLATED as scripts/life_smoke.py is: every store this touches is redirected into a temp dir before any module
writes, activity_memory.record (the memory SQLite) is stubbed, and the live data/ is never written. No matches are
added (D-0137 is open): the tin stays at 0 throughout.
    python scripts/_test_dark_house_answers.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


TMP = Path(tempfile.mkdtemp(prefix="dark_house_"))
print("isolated store dir:", TMP)

# ── isolate BEFORE anything loads ──────────────────────────────────────────────────────────────
from core import sensorium as S                         # noqa: E402
from core import study_life as SL                       # noqa: E402
from core import provisions as PV                       # noqa: E402
# sensorium/study_life/provisions (formerly direct assignment) + world_objects/world_substrate/
# locomotion (formerly 3 entries in the generic loop just below) now go through the one shared
# helper both this script and _test_candles_name_migration.py use (J-0922, F-1287's own
# "shared-helper question") -- see scripts/_test_isolation.py's own docstring for the full
# redirect-set provenance and its fail-loud-on-a-stale-name convention.
from scripts._test_isolation import redirect_world_stores  # noqa: E402
redirect_world_stores(TMP, locomotion=True)
if hasattr(PV, "_d"):
    PV._d = None
# J-0743 (2026-09-08, F-1063's wider sweep): every (module, attrs) pair below was re-verified
# directly against the real module source this pass. core.garden_life was missing its own "_EVENTS"
# (shared filename with core.garden's, per core/profile.py's own comment, but a DIFFERENT Python
# attribute -- garden's own redirect never covers it); core.shore_life was missing "_LEDGER";
# core.fieldcraft was missing "_LEDGER" -- all three are real guard_path()-protected write targets
# (core/garden_life.py:72, core/shore_life.py, core/fieldcraft.py:72), caught only by that separate,
# later-built fence until now, not by this script's own isolation claim. core.cat was missing
# "_HUNT_LEDGER_F" (J-0733's self-feed hunting fallback, added after this script's own cat entry —
# the same module-drift class J-0725 already named). core.garden_soil/core.life_traces/core.inventory
# carry NO redirectable path of their own at all (all three operate on core.garden's/core.life's own
# state, already covered above) -- their entries were always dead no-ops; dropped rather than left to
# mislead the next copy. core.hands' own "_F" was likewise dead (real store is "_TRACE" alone).
# core.world_objects/core.world_substrate/core.locomotion moved to the shared helper call above
# (J-0922) -- dropped from this table so nothing double-redirects them.
for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")),
                   ("core.supply", ("_F", "_LOG")), ("core.fieldcraft", ("_F", "_LEDGER")), ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")),
                   ("core.shore_life", ("_F", "_EVENTS", "_LEDGER")), ("core.life", ("_F", "_LEDGER", "_EVENTS", "_FLAGS_F")),  # J-0743: _FLAGS_F read-only, see life_smoke.py's own comment
                   ("core.hands", ("_TRACE",)),
                   ("core.intentions", ("_F", "_LOG")), ("core.procedures", ("_F", "_LOG")), ("core.night", ("_LOG", "_RECENT")),
                   ("core.light", ("_SHADOW",)), ("core.cat", ("_STATE_F", "_HUNT_LEDGER_F")), ("core.sound_knowledge", ("_LEDGER_F",))):
    try:
        m = __import__(mod, fromlist=["x"])
        for a in attrs:
            if hasattr(m, a):
                setattr(m, a, TMP / f"{mod.split('.')[-1]}_{a.strip('_').lower()}.json")
            else:
                # J-0819 (F-1177, 5th recurrence): a name miss here used to silently no-op with zero
                # warning. Loud now, on purpose.
                print("   (redirect skipped:", mod, a, "-- no such attribute, stale/typo'd isolation-list entry? )")
    except Exception as exc:
        print("   (redirect skipped:", mod, exc, ")")
import core.activity_memory as AM                       # noqa: E402  — writes the memory SQLite; stubbed
AM.record = lambda *a, **k: None
# J-0743: core.wandering was never stubbed here at all (unlike activity_memory just above) -- the
# same un-redirectable module F-1063 found in scripts/_test_letterbox_reach.py (no per-module path
# attribute exists; core.wandering.perceive() is the only neutralization option). Not confirmed
# reached by this script specifically (its own exercised surface is narrower than life_smoke.py's),
# but the fix is one line and the module IS transitively importable from core/sensorium.py's own
# substrate tick, which this script's redirected S._STATE_F does not gate against.
import core.wandering as WDR                            # noqa: E402
WDR.perceive = lambda *a, **k: None
import core.light as LT                                 # noqa: E402  — the dark, forced, so can_read() answers
LT.field_at = lambda *a, **k: 0.0


def fresh_study(**over):
    """A fresh in-memory study: matches 0, lamp dry, 12 candles, nothing carried. No load from disk."""
    S.state.clear()
    S.state.update({"weather": "drizzle", "wind": "calm", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                    "location": "study", "garden": S._fresh_garden()})
    st = SL._st()
    # J-0573: provisions.sync() is now guarded (a per-tick ceiling — see core/provisions.py sync_guarded)
    # and will no longer wipe the whole larder from a hand-set 0; a gap that large is reconciled (the
    # study count set FROM the shelf) instead of consumed. Drain the ISOLATED larder for real, through
    # consume() (uncapped, unchanged by J-0573 — only sync()'s automatic reconciliation was capped), then
    # set the study's count to match so the next sync() sees no gap at all.
    PV.consume("matches", PV.stock("matches"))
    st["matches"] = 0
    st = SL._st()
    st.update({"lamp_oil": 0.0, "lamp_lit": False, "candle_lit": False, "lantern_oil": 0.6, "lantern_lit": False,
               "oil_tin": 0.3, "can_oil": 0.0})
    st["candles"] = 12
    st = SL._st()
    for it in st["items"].values():
        it["carried"] = False; it["place"] = "study"
    st.update(over)
    return st


print("-- [1] the lamp: the tin before the oil")
st = fresh_study()
check("state as briefed: matches 0 / lamp_oil 0 / candles 12", st["matches"] == 0 and st["lamp_oil"] == 0.0 and st["candles"] == 12,
      f"matches={st['matches']} lamp_oil={st['lamp_oil']} candles={st['candles']}")
a1 = SL.act("light the lamp")
print("     lamp, tin empty + dry :", a1)
check("no phantom match: 'strike a match' is gone", a1 and "strike a match" not in a1, repr(a1))
check("both facts said: the tin is empty AND the lamp is dry", a1 and "match tin" in a1 and "empty" in a1 and "dry" in a1, repr(a1))
st["lamp_oil"] = 0.7
a2 = SL.act("light the lamp")
print("     lamp, tin empty + oil :", a2)
check("oil in, tin empty: the tin line, no lighting", a2 and "match tin" in a2 and "empty" in a2 and not st["lamp_lit"], repr(a2))
st["lamp_oil"] = 0.0
# the larder is the truth of the count (provisions.sync would put a hand-set 5 straight back to the shelf's 0),
# so five matches go into the ISOLATED larder's open box — the temp-dir copy, never the live one
_d = PV._ensure(); _box = next(o for o in _d["objects"] if o["kind"] == "matches")
_box["qty"], _box["empty"] = 5, False; PV._save(_d)
st["matches"] = 5                   # shelf and study agree, else sync reads the gap as five struck and consumes them
st = SL._st()
check("fixture: five matches in the isolated larder's open box", st["matches"] == 5 and str(PV._F).startswith(str(TMP)), f"{st['matches']} {PV._F}")
a3 = SL.act("light the lamp")
print("     lamp, matches + dry   :", a3)
check("matches present, lamp dry: today's oil line unchanged", a3 == "You turn up the wick and strike a match — nothing. The lamp is dry; it wants oil before it will burn.", repr(a3))
check("no matches were added by the test path (5 set, 5 remain: a dry lamp strikes none)", st["matches"] == 5, str(st["matches"]))

print("-- [2] the lantern: the same order")
st = fresh_study(lantern_oil=0.0)
b1 = SL.act("light the lantern")
print("     lantern, tin empty + dry:", b1)
check("lantern: no phantom match, both facts", b1 and "strike a match" not in b1 and "match tin" in b1 and "dry" in b1, repr(b1))
st["lantern_oil"] = 0.6
b2 = SL.act("light the lantern")
print("     lantern, tin empty + oil:", b2)
check("lantern: oil in, tin empty -> the tin line", b2 and "match tin" in b2 and "empty" in b2 and not st["lantern_lit"], repr(b2))

print("-- [3] the candle: box first, then the tin (the order that was already right)")
st = fresh_study()
c1 = SL.act("light a candle")
print("     candle:", c1)
check("12 candles, 0 matches -> 'No matches left'", c1 == "No matches left to light it with.", repr(c1))
check("the candle count is untouched", st["candles"] == 12 and st["matches"] == 0)

print("-- [4] the dark line no longer says 'box'")
st = fresh_study()
d1 = SL.can_read()
print("     can_read:", d1)
check("too dark, lamp dry, candles present -> the reworded line", d1 and "candles" in d1 and "east shelf" in d1 and "match tin" in d1, repr(d1))
check("'box' is gone from the line", d1 and "box" not in d1, repr(d1))
check("can_write mirrors it", "write" in SL.can_write() and "box" not in SL.can_write(), repr(SL.can_write()))

print("-- [5] the grammar: 'candles' family, and the claim over 'collect'")
from core import literal_will as lw, actions as ac, hands as h   # noqa: E402
R1 = ("The lamp sputters; ink runs dry. I will fetch candles from the box. The fire banks itself well enough for now, "
      "but the room needs its own light to think clearly about John Smith's letter.")
R2_T = ("The arithmetic sums wait on my paper, but the room feels too still. The lamp is dry, and the light is failing "
        "as the drizzle grows heavier outside. I feel a pull to tend the fire or fetch the candles ")
R2_I = "I want to fetch the candles from the box to warm the room."


def deeds(t, i="", loc="study"):
    return [(c["family"], c["object"]) for c in lw.classify(t, i, location=loc) if c.get("verdict") == "DEED"]


d_r1 = deeds(R1)
check("08:35 row: 'candles' is a DEED (and 'collect' still reads 'box')", ("candles", "candles") in d_r1 and ("collect", "box") in d_r1, str(d_r1))
d_r2 = deeds(R2_T, R2_I)
check("09:47 row: 'candles' is a DEED", any(f == "candles" for f, _ in d_r2), str(d_r2))
cl = ac.claimed_by((c["family"], c["object"], c["clause"]) for c in lw.classify(R1, "", location="study") if c["verdict"] == "DEED")
check("claimed_by: collect's 'box' is the candle box (same clause)", cl == {"collect": "candles"}, str(cl))
TWO = "I will fetch the candles from the shelf. Then I will collect the box from the gate."
cl2 = ac.claimed_by((c["family"], c["object"], c["clause"]) for c in lw.classify(TWO, "", location="study") if c["verdict"] == "DEED")
check("two sentences, two deeds: the gate's box is NOT claimed", cl2 == {}, str(cl2))
_gate = deeds("I will fetch the box from the gate.")
check("'fetch the box from the gate' alone: collect reads it, no candles reading (move's 'gate' is J-0539's, untouched)",
      ("collect", "box") in _gate and not any(f == "candles" for f, _ in _gate), str(_gate))
check("'light a candle' is the lamp family's, not a take", ("lamp", "candle") in deeds("I will light a candle.") and not any(f == "candles" for f, _ in deeds("I will light a candle.")),
      str(deeds("I will light a candle.")))
check("the family order: 'candles' sits before 'collect' and 'tool'",
      [a.family for a in ac.ACTIONS].index("candles") < [a.family for a in ac.ACTIONS].index("collect") < [a.family for a in ac.ACTIONS].index("tool"))

print("-- [6] the two 09-03 rows through dispatch.dispatch() in the study")
from core import dispatch as dp, intentions as it_, hands as H   # noqa: E402
st = fresh_study()
out1 = dp.dispatch(R1, "", "light", "candles", cycle_id="t-0835")
dec1 = list(H._decided["rows"])
print("     08:35 ->", out1)
print("           decisions:", dec1)
check("08:35: the candles hand FIRES", any(f == "candles" for f, _ in out1), str(out1))
check("08:35: the answer is the candle box in his hands, with the tin's honest count",
      any("candle box" in a and "match tin" in a and "empty" in a and "12 candles" in a for _, a in out1), str(out1))
check("08:35: the box is CARRIED now", st["items"]["candles"].get("carried") is True)
check("08:35: 'collect' is DROP-claimed:candles, not STAGE-place", any(r["family"] == "collect" and r["decision"] == "DROP-claimed:candles" for r in dec1)
      and not any(r["family"] == "collect" and r["decision"].startswith("STAGE") for r in dec1), str(dec1))
st = fresh_study()
out2 = dp.dispatch(R2_T, R2_I, "move", "to the candlebox", cycle_id="t-0947")
dec2 = list(H._decided["rows"])
print("     09:47 ->", out2)
print("           decisions:", dec2)
check("09:47: the candles hand FIRES with the honest line", any(f == "candles" and "candle box" in a and "empty" in a for f, a in out2), str(out2))
check("09:47: 'collect' is DROP-claimed:candles", any(r["family"] == "collect" and r["decision"] == "DROP-claimed:candles" for r in dec2), str(dec2))
try:
    staged = json.loads((it_._F).read_text(encoding="utf-8")) if it_._F.exists() else {}
except Exception:
    staged = {}
opened = [i for i in (staged.get("open") or []) if i.get("family") == "collect"]
check("nothing was staged at the garden gate for 'collect' in either row", not opened, str(opened)[:200])
check("no matches appeared anywhere along the way", st["matches"] == 0 and PV.stock("matches") == 0, f"{st['matches']} / {PV.stock('matches')}")

print("-- [7] the same reach out in the garden: staged for the study, the box still claimed")
st = fresh_study(); S.state["location"] = "garden"
out3 = dp.dispatch(R1, "", "light", "candles", cycle_id="t-garden")
dec3 = list(H._decided["rows"])
print("     garden ->", out3, dec3)
check("garden: candles STAGE-place (the study), collect DROP-claimed", any(r["family"] == "candles" and r["decision"] == "STAGE-place" for r in dec3)
      and any(r["family"] == "collect" and r["decision"] == "DROP-claimed:candles" for r in dec3), str(dec3))

print("-- [8] the tin itself, and the item-naming fix")
st = fresh_study()
e1 = SL.act("I will fetch the matches from the mantel", family="candles")
print("     fetch the matches:", e1)
check("'fetch the matches' reaches the TIN (not the candle box), honestly empty", e1 and "match tin" in e1 and "mpty" in e1 and st["items"]["matches_tin"].get("carried") is True
      and not st["items"]["candles"].get("carried"), repr(e1))
st = fresh_study()
e2 = SL.take("i take the lantern from its hook; the hard blue sea outside matches the clarity of the day")
print("     take the lantern ... matches:", e2)
check("'matches' as a verb elsewhere no longer hides the lantern from take()", e2 and "lantern" in e2 and st["items"]["lantern"].get("carried") is True, repr(e2))
st = fresh_study()
e3 = SL.act("I will fetch the candles from the box", family="candles")
e4 = SL.act("I set the candle box down on the desk", family="candles")
check("put(): the box is set down again", e4 and "set" in e4 and st["items"]["candles"].get("carried") is False, repr(e4))
check("an unscoped call (no family) still walks the old chain: 'light the lamp' answers as the lamp", "match tin" in (SL.act("light the lamp") or ""))

print("-- [9] D-0271 / J-1755: bare 'candles'/'candle' are back, but ONLY as the direct object of the row's own verbs")
# The 2026-09-30 07:57:41 live miss (F-2266): the study's own lack text says "There are candles on the east shelf" and
# the will it invites was dropped by D-0267 PART 1, so the 'book' row (fetch ... "see the book clearly") took the thought.
R3 = ("The darkness presses against my eyes; the dry lamp offers no light. I must fetch the candles from the shelf to see the "
      "book clearly. The rain hisses on, but I need the fire within the room to answer t")
d_r3 = deeds(R3, "", "study")
check("09-30 07:57 row: 'candles' is a DEED again, ahead of 'book' in the table",
      ("candles", "candles") in d_r3 and ("book", "book") in d_r3 and [f for f, _ in d_r3].index("candles") < [f for f, _ in d_r3].index("book"), str(d_r3))
for label, t in (("a determiner-less plural (the 09-03 08:35 shape)", "I will fetch candles from the box."),
                 ("a modifier before the noun", "I will bring the spare candles to the desk."),
                 ("a singular after a quantifier", "I want to carry a candle to the desk."),
                 ("a separated particle verb", "I pick the candles up and set them on the desk."),
                 ("put down, singular", "I put the candle down on the desk.")):
    check(f"guarded noun READ: {label}", any(f == "candles" for f, _ in deeds(t)), str(deeds(t)))
for label, t in (("a card that LISTS candles", "I pick up the card listing oil and candles, feeling the weight of survival pressing against my desire for simple presence."),
                 ("a list of necessities", "I read the list of necessities -- oil, seed, candles -- and feel the weight of scarcity lift slightly."),
                 ("lifting the gaze to them", "I lift my gaze to the candles on the east shelf."),
                 ("carrying their weight", "I carry the weight of the candles with me through the evening."),
                 ("carrying a question about them", "I carry the question of the candles into sleep."),
                 ("setting down something else, then watching them", "I set down my pen and watch the candles gutter."),
                 ("scenery, the candle's own flame", "The candle drips wax while the rain hisses; the candle's blue bead steadies my hand."),
                 ("the bare word as a subject before a verb", "The candles on the east shelf wait for the dark, and I take a long breath."),
                 ("'matches' stays dropped (D-0271: unless the replay shows it costs genuine wills -- it costs none)", "I will fetch the matches from the mantel.")):
    check(f"guard holds, NO candles reading: {label}", not any(f == "candles" for f, _ in deeds(t)), str(deeds(t)))
st = fresh_study()
out4 = dp.dispatch(R3, "", "world", "light the candles", cycle_id="t-0930")
dec4 = list(H._decided["rows"])
print("     09-30 07:57 ->", out4)
print("           decisions:", dec4)
check("09-30: the candles hand FIRES (the candle box in his hands)", any(f == "candles" and "candle box" in a for f, a in out4) and st["items"]["candles"].get("carried") is True, str(out4))
check("09-30: 'book' is only STAGE-busy:candles -- not fired, so no take_book rides on this thought (F-2266)",
      any(r["family"] == "book" and r["decision"] == "STAGE-busy:candles" for r in dec4) and not any(f == "book" for f, _ in out4), str(dec4))
st = fresh_study()
out5 = dp.dispatch("I could fetch a candle, but the book feels heavy with its question about rain data silencing local voices.", "", "observe", "the book", cycle_id="t-hedge")
dec5 = list(H._decided["rows"])
check("a hedged 'I could fetch a candle' is read but DROPPED as weak intent: nothing fires, nothing stages",
      not out5 and any(r["family"] == "candles" and r["decision"] == "DROP-weak-intent" for r in dec5)
      and not any(r["decision"].startswith(("FIRE", "STAGE")) for r in dec5), str((out5, dec5)))

print("-- isolation")
live = [p for p in (ROOT / "data" / "room_state.json", ROOT / "data" / "intentions.json") if p.exists()]
check("redirected paths all inside TMP", all(str(x).startswith(str(TMP)) for x in (S._STATE_F, SL._LEDGER, SL._EVENTS, PV._F, PV._LOG, it_._F, H._TRACE)))

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
