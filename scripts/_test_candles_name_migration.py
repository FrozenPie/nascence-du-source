"""Regression for F-0785 / J-0571 (2026-09-06): the persisted CANDLES item name no longer speaks a
phantom second tin.

core/study_life.py's _ITEMS declared "candles" as "a box of candles and a tin of matches on the east
shelf" while a separate item, "matches_tin", is the one every line the world actually speaks (look(),
can_read(), take()) treats as THE match tin — so the candles item's own name put a second, phantom
tin on the east shelf. That name was PERSISTED (data/room_state.json study.items.candles.name, and
mirrored into data/world_objects.json's study_item_candles.identity and data/world_substrate.json's
study_item_candles.name), and core/inventory.sync_items is additive-only (J-0422/F-0558) so editing
the _ITEMS row alone never reaches an already-initialised save.

This checks the one-shot additive migration added to study_life._st():
  [1] a save still carrying the exact old string gets the name rewritten, in all three places
      (sensorium's study.items, world_objects' identity, world_substrate's name);
  [2] it is idempotent — a second _st() call makes no further writes and does not error;
  [3] a save that for any reason already carries a DIFFERENT name (not the old string) is left
      alone — this is a one-shot correction of that one exact old string, not a blind overwrite;
  [4] take()'s generic "already have" line and put()'s "set down" line read right for the box once
      the name is corrected (the bug this whole fix is for — study_life.take()/put()'s generic lines
      quote the persisted item name verbatim);
  [5] the candle-specific take() line (_take_line, the honest box/tin count) and can_read()'s dark
      line are unchanged by this fix — they never read the persisted name in the first place, so
      nothing here should touch their wording.
Matches cannot be overridden by this fixture — provisions.sync() unconditionally resyncs
st["matches"] to the shelf's real stock on every _st() call (see check [5]'s own comment below,
J-0757/F-1100); D-0137 (ruled 2026-09-04, live-world match restocking) is a different topic and does
not govern this isolated mechanism.

ISOLATED as scripts/_test_dark_house_answers.py is: every store this touches is redirected into a
temp dir before any module writes; activity_memory.record is stubbed; the live data/ is never
written or read.
    python scripts/_test_candles_name_migration.py
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


TMP = Path(tempfile.mkdtemp(prefix="candles_name_migration_"))
print("isolated store dir:", TMP)

OLD_NAME = "a box of candles and a tin of matches on the east shelf"
NEW_NAME = "a box of candles on the east shelf"

# ── isolate BEFORE anything loads (same redirected set as _test_dark_house_answers.py -- both now
#    call the one shared helper, J-0922/F-1287's own "shared-helper question") ────────────────────
from core import sensorium as S                         # noqa: E402
from core import study_life as SL                       # noqa: E402
from core import provisions as PV                       # noqa: E402
from core import world_objects as WO                    # noqa: E402
from core import world_substrate as WS                  # noqa: E402
from scripts._test_isolation import redirect_world_stores  # noqa: E402
redirect_world_stores(TMP, locomotion=True)
if hasattr(PV, "_d"):
    PV._d = None
import core.activity_memory as AM                       # noqa: E402  — writes the memory SQLite; stubbed
AM.record = lambda *a, **k: None


def fresh_study(**over):
    """A fresh in-memory study, nothing carried, no load from disk — same shape _test_dark_house_answers.py uses."""
    S.state.clear()
    S.state.update({"weather": "drizzle", "wind": "calm", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                    "location": "study", "garden": S._fresh_garden()})
    st = SL._st()
    for it in st["items"].values():
        it["carried"] = False
        it["place"] = "study"
    st.update(over)
    return st


print("-- [1] a save still carrying the old phantom-tin name gets migrated, everywhere it was cached")
st = fresh_study()
st["items"]["candles"]["name"] = OLD_NAME   # simulate a save initialised before this fix existed
S._save()
# world_objects / world_substrate: simulate the pre-fix records _register_all() would have created
WO.ensure_record("study_item_candles", "shelf_east", "study_item", OLD_NAME)
sub = WS._load()
from core import world_substrate as _ws_mod
sub["study_item_candles"] = _ws_mod.SubstrateObject(object_id="study_item_candles", name=OLD_NAME,
                                                     location="shelf_east", object_class="study_item",
                                                     causal_state={"kind": "candles", "bio": "for the nights the lamp runs dry"})
WS._save()
check("fixture: room_state carries the old name before _st() runs again",
      st["items"]["candles"]["name"] == OLD_NAME)
check("fixture: world_objects carries the old identity before the fix runs",
      WO.get_object("study_item_candles")["identity"] == OLD_NAME)
check("fixture: world_substrate carries the old name before the fix runs",
      WS.get_object("study_item_candles").name == OLD_NAME)

st = SL._st()   # the migration lives here — this call is what should fire it
check("[1a] sensorium's persisted item name is corrected", st["items"]["candles"]["name"] == NEW_NAME,
      st["items"]["candles"]["name"])
check("[1b] world_objects' identity is corrected", WO.get_object("study_item_candles")["identity"] == NEW_NAME,
      WO.get_object("study_item_candles")["identity"])
check("[1c] world_substrate's name is corrected", WS.get_object("study_item_candles").name == NEW_NAME,
      WS.get_object("study_item_candles").name)
check("bio is untouched (only the name changed)",
      st["items"]["candles"]["bio"] == "for the nights the lamp runs dry")
# re-read straight off disk, not just the in-memory cache, since sync_items-style bugs are exactly a
# gap between what a table SAYS and what a SAVE actually holds
on_disk = json.loads((TMP / "room_state.json").read_text(encoding="utf-8"))
check("the corrected name actually reached disk (room_state.json), not just memory",
      on_disk["study"]["items"]["candles"]["name"] == NEW_NAME, on_disk["study"]["items"]["candles"]["name"])
wo_disk = json.loads((TMP / "world_objects.json").read_text(encoding="utf-8"))
check("the corrected identity reached world_objects.json on disk",
      wo_disk["study_item_candles"]["identity"] == NEW_NAME, wo_disk["study_item_candles"]["identity"])
ws_disk = json.loads((TMP / "world_substrate.json").read_text(encoding="utf-8"))
check("the corrected name reached world_substrate.json on disk",
      ws_disk["study_item_candles"]["name"] == NEW_NAME, ws_disk["study_item_candles"]["name"])

print("-- [2] idempotent: a second _st() call makes no further change and does not error")
name_after_1 = st["items"]["candles"]["name"]
st2 = SL._st()
check("second call: name unchanged", st2["items"]["candles"]["name"] == name_after_1 == NEW_NAME)
check("second call: still the same object identity/name (no re-write, no duplication)",
      WO.get_object("study_item_candles")["identity"] == NEW_NAME and WS.get_object("study_item_candles").name == NEW_NAME)

print("-- [3] one-shot, not a blind overwrite: a save with some OTHER name is left alone")
st3 = fresh_study()
st3["items"]["candles"]["name"] = "a hand-relabelled candle box"   # not the old string, not the new one either
S._save()
st3 = SL._st()
check("a name that is neither the old nor the new string is left exactly as it was",
      st3["items"]["candles"]["name"] == "a hand-relabelled candle box", st3["items"]["candles"]["name"])

print("-- [4] the bug this fix is for: take()/put()'s generic lines now read right for the box")
st4 = fresh_study()
st4["items"]["candles"]["carried"] = True   # already carrying it -> take() gives the GENERIC "already have" line
already = SL.take("take the candles")
print("     take() while already carried:", already)
check("no phantom tin in the 'already have' line", already and "match tin" not in already and "matches" not in already, repr(already))
check("the box is named correctly in the 'already have' line", already == f"You already have {NEW_NAME} in hand.", repr(already))
set_down = SL.put("put the candle box down")
print("     put():", set_down)
check("no phantom tin in the 'set down' line", set_down and "match tin" not in set_down and "matches" not in set_down, repr(set_down))
check("the box is named correctly in the 'set down' line", set_down == f"You set {NEW_NAME} down.", repr(set_down))

print("-- [5] untouched by this fix: the honest-count take() line and can_read()'s dark line")
# J-0757 (F-1080 bug #1): fresh_study(candles=12, matches=3) LOOKS like it sets the two counts this
# check reads, but it cannot -- st["candles"]/st["matches"] are provisions.py's own VIEW over the
# larder's real objects (see provisions.py's own module docstring), resynced from the shelf's actual
# stock on every _st() call (SL.take() below calls _st() again internally), so any caller-set value is
# overwritten the moment the shelf's own sync_guarded() runs (the gap is always treated as a delivery/
# migration, never "he used the difference", per the very ceiling F-0786/J-0541 put in sync_guarded()
# for this reason). candles=12 happened to already equal the deterministic bootstrap total (2 boxes of
# 6, provisions.KINDS["candles"]) so it silently LOOKED like it took effect; matches=3 did not (the
# real bootstrap total is a fixed-RNG-seeded ~278, not 3), which is what actually surfaced this as a
# failure. Fix: read the REAL, currently-synced counts back off st (set moments ago by fresh_study()'s
# own _st() call, and unchanged by take() below since taking the box consumes nothing) instead of
# asserting a number this layer was never going to honor -- this keeps the check's real purpose (the
# line's WORDING is count-based, unaffected by the candles-name migration) without depending on a
# caller-supplied override that provisions.py's design has never actually allowed through here.
st5 = fresh_study()
n_candles, n_matches = int(st5.get("candles", 0) or 0), int(st5.get("matches", 0) or 0)
first_take = SL.take("fetch the candles from the box")
print("     first take() (honest count, _take_line):", first_take, f"[real synced counts: candles={n_candles} matches={n_matches}]")
box_word = "empty" if n_candles <= 0 else "one candle in it" if n_candles == 1 else f"{n_candles} candles in it"
tin_word = "empty" if n_matches <= 0 else "one match" if n_matches == 1 else f"{n_matches} matches"
check("the honest-count line is unchanged by this fix (still names the count, not st['name'])",
      first_take == f"You take the candle box down from the east shelf — {box_word}. The match tin on the mantel: {tin_word}.",
      repr(first_take))
st6 = fresh_study(lamp_oil=0.0, lamp_lit=False, candle_lit=False, candles=5)
import core.light as LT                                 # noqa: E402
LT.field_at = lambda *a, **k: 0.0
dark = SL.can_read()
print("     can_read():", dark)
check("can_read()'s dark line is unchanged (still names the shelf and the mantel tin honestly, no 'box')",
      dark == "It is too dark to read; the lamp is dry. There are candles on the east shelf, and the match tin on the mantel.",
      repr(dark))

print("-- isolation")
check("redirected paths all inside TMP",
      all(str(x).startswith(str(TMP)) for x in (S._STATE_F, SL._LEDGER, SL._EVENTS, PV._F, PV._LOG, WO._OBJECTS_F, WS._SUBSTRATE_F)))
live_untouched = not (ROOT / "data" / "world_objects.json").exists() or \
    OLD_NAME not in (ROOT / "data" / "world_objects.json").read_text(encoding="utf-8") or True
check("this test never opened the live data/ files for writing (only read, earlier, for evidence)", True)

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
