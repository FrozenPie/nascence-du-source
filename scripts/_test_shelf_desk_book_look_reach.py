"""THE SHELF/DESK/BOOK LOOK GATE (2026-09-23, J-1178 / F-1652). ISOLATED: every store this touches is
redirected into a temp dir before any module writes (the S-0016 / test-isolation rule, mirroring
scripts/_test_letterbox_reach.py's own pattern) -- the live data/ is never written, proven by hash.

What it proves, per phrase 'I want to look at the shelf / the desk / the book / my books / the page /
my tablets / my works':
  1. literal_will.classify() yields a 'look' family reading with verdict DEED
  2. dispatch.dispatch() returns exactly ONE ('look', <text>) tuple, and that text is real (non-empty,
     not the generic room fallback) -- which is also the "lands in _acted exactly once" / no-double-
     perceive proof F-1481's own verification used (its own docstring: "confirms 'look' lands in
     _acted exactly once per thought, which the ... guard now checks")

TODAY (core/actions.py's 'look' row has desk/shelf but not book/books/page/tablets/works): the shelf
and the desk phrases pass both assertions; the other FIVE are expected to FAIL assertion (1) -- classify()
never proposes a 'look' candidate for them at all, so dispatch is never reached. That failure is the
point: it pins the real, current gap F-1652 found, the same way a red test pins a bug before its fix
lands. This file does not fix the gap (out of item (2)'s "no ruling for a table widen" instruction) --
see decide.py D-<n> (opened by J-1178) for the per-word widening question this gap raises.

Run:  python scripts/_test_shelf_desk_book_look_reach.py
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="shelf_desk_book_reach_"))
print("isolated store dir:", TMP)
LIVE_SUPPLY = Path(r"C:\Nascence") / "data" / "supply.json"
_LIVE_SUPPLY_EXISTS = LIVE_SUPPLY.exists()
_live_md5_before = hashlib.md5(LIVE_SUPPLY.read_bytes()).hexdigest() if _LIVE_SUPPLY_EXISTS else ""
_REDIRECTS: list[tuple[object, str]] = []

# ── isolate BEFORE importing anything that might load (mirrors _test_letterbox_reach.py's own list) ──
from core import sensorium as S                         # noqa: E402
S._STATE_F = TMP / "room_state.json"
_REDIRECTS.append((S, "_STATE_F"))
from core import supply as SUP                          # noqa: E402
SUP._F, SUP._LOG = TMP / "supply.json", TMP / "supply_log.jsonl"
_REDIRECTS += [(SUP, "_F"), (SUP, "_LOG")]
for mod, attrs in (("core.life", ("_F", "_LEDGER", "_EVENTS")), ("core.study_life", ("_LEDGER", "_EVENTS")),
                   ("core.provisions", ("_F", "_LOG")), ("core.sound_knowledge", ("_LEDGER_F",)),
                   ("core.locomotion", ("_POS_F",)), ("core.garden", ("_F", "_LEDGER", "_EVENTS")),
                   ("core.garden_life", ("_F",)), ("core.shore_life", ("_F", "_EVENTS")),
                   ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")), ("core.cat", ("_STATE_F",)),
                   ("core.world_objects", ("_OBJECTS_F",)),
                   ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                   ("core.fieldcraft", ("_F",)), ("core.intentions", ("_F", "_LOG")), ("core.hands", ("_TRACE",)),
                   ("core.procedures", ("_F", "_LOG")), ("core.literal_will", ("_LOG", "_STATE")),
                   ("core.night", ("_LOG", "_RECENT")), ("core.boredom", ("_STATE",))):
    try:
        m = __import__(mod, fromlist=["x"])
        for a in attrs:
            if hasattr(m, a):
                setattr(m, a, TMP / f"{mod.split('.')[-1]}_{a.strip('_').lower()}.json")
                _REDIRECTS.append((m, a))
            else:
                print("  (isolation note)", mod, a, "has no such attribute -- stale/typo'd isolation-list entry?")
        if hasattr(m, "_d"):
            m._d = None
    except Exception as exc:
        print("  (isolation note)", mod, exc)

from core import wandering as _WDR                      # noqa: E402
from core import activity_memory as _AM                 # noqa: E402
_WDR.perceive = lambda *a, **k: None
_AM.record = lambda *a, **k: None

# a fresh in-memory study, no book/curriculum fixture set up (see this file's own docstring: assertion
# (2) is scoped to GATE+CUE reachability, not to study_life's own curriculum-content rendering, which
# F-1481's own dedicated fixture already proved works once a real 'look' candidate reaches dispatch).
S.state.clear()
S.state.update({"weather": "clear", "wind": "breeze", "fire": "low", "fire_fuel": 1.0, "last_event": 0,
                "location": "study"})

from core import literal_will as LW, dispatch as D, hands as H  # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


PHRASES = [
    ("the shelf", "I want to look at the shelf."),
    ("the desk", "I want to look at the desk."),
    ("the book", "I want to look at the book."),
    ("my books", "I want to look at my books."),
    ("the page", "I want to look at the page."),
    ("my tablets", "I want to look at my tablets."),
    ("my works", "I want to look at my works."),
]
# ASPIRATIONAL contract, asserted UNIFORMLY (this job's own briefing, verbatim): every one of these 7
# phrases should reach look:DEED at the gate, then dispatch() with a real answer. core/actions.py's
# 'look' row carries desk/shelf but not book/books/page/tablets/works today, so 5 of the 7 are EXPECTED
# to fail assertion [1] right now, and by construction assertion [2] cascades to a no-candidate result
# for those same 5 -- this is not a bug in this script; it is the pinned, current state of the gap
# F-1652 found, a red test the same way a bug reproduction is red before its fix lands. Do not "fix" the
# per-phrase toggle out of this list to make it report ALL OK -- see decide.py's per-word widening
# question (opened by J-1178, not ruled) for what would actually turn these green.

print("\n[1] literal_will.classify() -- every phrase asserted to reach look:DEED (the aspirational gate)")
gate_results = {}
for label, phrase in PHRASES:
    r = {c["family"]: c["verdict"] for c in LW.classify(phrase, "", location="study")}
    got_deed = r.get("look") == "DEED"
    gate_results[label] = got_deed
    check(got_deed, f"{label!r}: classify() -> look:DEED (got look={r.get('look')!r}, book={r.get('book')!r})")

print("\n[2] dispatch.dispatch() end to end -- exactly one real ('look', text) tuple per phrase")
for label, phrase in PHRASES:
    S.state["location"] = "study"
    S.state["last_event"] = 0
    ans = D.dispatch(phrase, "", "", "", cycle_id=f"t-{label.replace(' ', '_')}")
    look_hits = [a for f, a in ans if f == "look"]
    check(len(look_hits) == 1, f"{label!r}: dispatch() returns exactly one look tuple (got {len(look_hits)}: {look_hits})")
    if look_hits:
        text = look_hits[0]
        is_room_fallback = text.startswith("You look around:")
        check(bool(text) and not is_room_fallback,
              f"{label!r}: the look text is real, not the generic room fallback -- {text[:90]!r}")

print("\n[3] isolation proof")
check(_LIVE_SUPPLY_EXISTS, f"live {LIVE_SUPPLY} exists to be checked")
_live_md5_after = hashlib.md5(LIVE_SUPPLY.read_bytes()).hexdigest() if LIVE_SUPPLY.exists() else ""
check(_LIVE_SUPPLY_EXISTS and _live_md5_before == _live_md5_after,
      f"live data/supply.json untouched (md5 {_live_md5_after[:8]})")
escaped = [f"{m.__name__}.{a}" for m, a in _REDIRECTS if not str(getattr(m, a)).startswith(str(TMP))]
check(not escaped, f"every redirected store path still inside TMP ({len(_REDIRECTS)} checked){' ESCAPED: ' + str(escaped) if escaped else ''}")

print(f"\n{'ALL OK' if not fails else str(fails) + ' FAILURE(S)'}  (stores: {TMP})")
gap_words = [label for label, ok in gate_results.items() if not ok]
if gap_words:
    print(f"NOTE: {len(gap_words)} of the failures above ({gap_words}) are the EXPECTED, pinned state of")
    print("the reachability gap F-1652 found -- core/actions.py's 'look' row does not carry these words")
    print("yet. This is not a bug in this script; see docs/decisions.jsonl for the per-word widening")
    print("question this gap raises (opened by J-1178, not ruled). Once/if a word is added to the table,")
    print("its own two checks above should turn green with no change to this file.")
sys.exit(1 if fails else 0)
