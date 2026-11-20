"""
_test_provisions_sync_guard.py — J-0541/F-0786..789; guard APPLIED to core/provisions.py by J-0573: reproduce
the 2026-08-23 09:10:52 larder mass-empty in an ISOLATED larder and show that the guard — now living in
core/provisions.py as sync_guarded(), with sync() a thin wrapper around it — refuses it, for every kind and
for the carrier path too, while still letting one honest match (or one fill of the lamp) come off the shelf.

The defect (core/provisions.py sync(), before J-0573): the shelf is the truth, and "the study's count is LOWER
than the shelf" was read as "he used the difference" — `consume(kind, have - cur)` with NO ceiling. Any process
whose study dict holds a count below the shelf (a save initialised before the larder existed; a fresh stub state
in an un-isolated diagnostic; the carrier's box just added to the shelf while the study still holds the old
count) was a mass consume with 'used up by Du' written into every emptied object's biography.

THE GUARD (J-0541 proposed it here as `sync_guarded`; J-0573 moved it into core/provisions.py and made sync()
call it — this file now imports the live function instead of carrying a second, driftable copy):
  a single sync call may consume at most _MAX_STEP[kind] of a kind — the most he could plausibly use between two
  ticks (sync runs on EVERY study_life._st() call, i.e. many times a minute). A larger gap is a migration or a
  desync, not use: the study count is set FROM the shelf and a 'sync_reconciled' row is logged with the gap, so
  the event is visible instead of silently rewriting the world's history. core/supply.py's collect_box() (J-0573)
  also now credits the study's count from the shelf right after each delivery, so an ordinary carrier delivery
  never even reaches sync() as a "gap" in the first place — sync_reconciled stays a real-desync signal, not
  routine collection noise.

Isolation: provisions._F/_LOG, world_substrate and world_objects stores all redirected to a temp dir BEFORE any
larder call; the study side is a plain stub dict (no sensorium / study_life import, no room_state.json).
Exit 1 on any failed check. Run: python -X utf8 scripts/_test_provisions_sync_guard.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="prov_guard_"))
print("isolated store dir:", TMP)

# ── isolate BEFORE anything loads ──────────────────────────────────────────────────────────────
from core import provisions as PV                       # noqa: E402
PV._F, PV._LOG = TMP / "provisions.json", TMP / "provisions_log.jsonl"
_REDIRECTED = [PV._F, PV._LOG]
for mod, attrs in (("core.world_objects", ("_OBJECTS_F",)),
                   ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F"))):
    m = __import__(mod, fromlist=["x"])
    for a in attrs:
        if hasattr(m, a):
            setattr(m, a, TMP / (mod.split(".")[-1] + "_" + a.strip("_").lower() + ".json"))
            _REDIRECTED.append(getattr(m, a))
        else:
            # J-0819 (F-1177, 5th recurrence): a name miss here used to silently no-op with zero
            # warning. Loud now, on purpose.
            print("  (isolation note)", mod, a, "has no such attribute -- stale/typo'd isolation-list entry?")
LIVE = ROOT / "data"
assert all(str(p).startswith(str(TMP)) for p in _REDIRECTED), _REDIRECTED
_live_before = {p.name: p.stat().st_mtime for p in (LIVE / "provisions.json", LIVE / "provisions_log.jsonl") if p.exists()}

FAILS = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ok   " if ok else "  FAIL ") + label + (f"   [{detail}]" if detail and not ok else ""))
    if not ok:
        FAILS.append(label)


def reset_larder() -> dict:
    """The larder exactly as bootstrapped on 2026-08-22 (seeded RNG: matches 28+5x50=278, oil 0.55+1.0, ...)."""
    for p in (PV._F, PV._LOG):
        if p.exists():
            p.unlink()
    return PV._ensure()


def emptied_rows() -> list:
    if not PV._LOG.exists():
        return []
    return [json.loads(l) for l in PV._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]


# ── the guard, now LIVE in core/provisions.py (J-0573) — import it rather than carry a second copy ────────
_MAX_STEP = PV._MAX_STEP
sync_guarded = PV.sync_guarded


# ── [1] the 2026-08-23 09:10:52 event, replayed against the LIVE, now-guarded sync() (J-0573) ──────────────
print("-- [1] replay 08-23 09:10:52 against the live PV.sync(): study matches 23, shelf 278 -- now refused")
reset_larder()
shelf0 = PV.stock("matches")
check("bootstrap shelf is 278 matches (28 open + 5x50)", shelf0 == 278.0, str(shelf0))
st = {"matches": 23}
PV.sync(st)
rows = emptied_rows()
check("no box emptied by the live sync() any more", not [r for r in rows if r.get("event") == "emptied"], str(rows))
check("shelf untouched at 278 -- the 255 matches are no longer destroyed", PV.stock("matches") == shelf0, str(PV.stock("matches")))
check("study count set FROM the shelf (23 -> 278) by the live sync()", st["matches"] == 278.0, str(st["matches"]))
check("one 'sync_reconciled' row names the gap (255) via the live sync()",
      [r for r in rows if r.get("event") == "sync_reconciled" and r["kind"] == "matches" and r["gap"] == 255.0], str(rows))

# ── [2] the same event, with the guard ────────────────────────────────────────────────────────────────
print("-- [2] the same event with sync_guarded(): refused, reconciled, nothing emptied")
reset_larder()
st = {"matches": 23}
rec = sync_guarded(st)
rows = emptied_rows()
check("no box emptied", not [r for r in rows if r.get("event") == "emptied"], str(rows))
check("shelf untouched at 278", PV.stock("matches") == 278.0, str(PV.stock("matches")))
check("study count set FROM the shelf (23 -> 278)", st["matches"] == 278.0, str(st["matches"]))
check("one 'sync_reconciled' row names the gap", [r for r in rows if r.get("event") == "sync_reconciled" and r["kind"] == "matches" and r["gap"] == 255.0], str(rows))
check("guard reports the reconciliation", rec == [("matches", 23.0, 278.0, 255.0)], str(rec))

# ── [3] every kind: the pre-larder init literal (study_life._st :110-116 first values) vs the shelf ──────
# Before J-0573 this table contrasted the destructive sync() against sync_guarded(); now that sync() IS the
# guard, both entry points must agree and both must lose nothing, for every kind, not just matches.
print("-- [3] every kind: study_life's pre-larder init values vs the bootstrap shelf — guarded now, both entry points")
PRE_LARDER = {"matches": 23, "soap": 0.6, "candles": 8, "oil_tin": 0.5, "tea_leaves": 0, "paper": 30, "ink": 0.8}
print(f"   {'kind':<8} {'shelf':>7} {'study':>7} {'sync() loss':>12} {'guard loss':>11}  emptied")
table_ok = True
for kind, (_, full, key, _) in PV.KINDS.items():
    if key not in PRE_LARDER:
        continue
    reset_larder(); before = PV.stock(kind)
    PV.sync({key: PRE_LARDER[key]})
    loss_sync = round(before - PV.stock(kind), 3); emp = [r["id"] for r in emptied_rows() if r.get("event") == "emptied"]
    reset_larder()
    st = {key: PRE_LARDER[key]}; sync_guarded(st)
    loss_guard = round(before - PV.stock(kind), 3)
    print(f"   {kind:<8} {before:>7} {PRE_LARDER[key]:>7} {loss_sync:>12} {loss_guard:>11}  {emp}")
    if loss_sync != 0.0 or loss_guard != 0.0 or emp:
        table_ok = False
check("neither the live sync() nor sync_guarded() loses anything for any kind, any more", table_ok)

# ── [4] the carrier path: an add() then a sync() with the study count NOT raised first — the shape
# core/supply.collect_box() had before J-0573 (it now calls _credit() to raise the count itself; this
# still proves the guard protects any caller — present or future — that adds without crediting) ──────────
print("-- [4] an uncredited carrier delivery: both sync() and sync_guarded() now keep it, not just the latter")
reset_larder()
PV.consume("matches", 278.0)                      # the house as it is today: 0 matches on the shelf
st = {"matches": 0}; PV.sync(st)
check("fixture: 0 matches, study agrees", PV.stock("matches") == 0.0 and st["matches"] == 0.0)
PV.add("matches", 1, "carrier")
PV.sync(st)                                        # an uncredited caller's sync -- guarded now too
check("sync(): the uncredited delivery survives (shelf 50, study 50)", PV.stock("matches") == 50.0 and st["matches"] == 50.0, f"{PV.stock('matches')} {st['matches']}")
new_box = [o for o in PV._load()["objects"] if o["origin"] == "carrier"][0]
check("...its biography still says only 'brought up by the carrier', never 'used up by Du'", not new_box.get("empty") and new_box["history"][-1]["event"] != "used up by Du", str(new_box["history"]))
reset_larder(); PV.consume("matches", 278.0); st = {"matches": 0}; PV.sync(st)
PV.add("matches", 1, "carrier")
rec = sync_guarded(st)
check("sync_guarded(): the box survives collection too (shelf 50, study 50)", PV.stock("matches") == 50.0 and st["matches"] == 50.0, f"{PV.stock('matches')} {st['matches']}")
check("...as a reconciliation, not use", rec == [("matches", 0.0, 50.0, 50.0)], str(rec))
for kind, n_obj in (("oil", 1), ("candles", 1), ("tea", 1), ("soap", 1), ("paper", 1), ("ink", 1)):
    reset_larder(); key = PV.KINDS[kind][2]
    st = {key: PV.stock(kind)}
    PV.add(kind, n_obj, "carrier"); before = PV.stock(kind)
    PV.sync(dict(st))
    lost_sync = round(before - PV.stock(kind), 3)
    reset_larder(); st = {key: PV.stock(kind)}; PV.add(kind, n_obj, "carrier"); before = PV.stock(kind)
    sync_guarded(st); lost_guard = round(before - PV.stock(kind), 3)
    check(f"carrier {kind}: an uncredited delivery now survives sync() ({lost_sync} lost) AND sync_guarded() ({lost_guard} lost)", lost_sync == 0.0 and lost_guard == 0.0, f"{lost_sync} {lost_guard}")

# ── [5] honest use still comes off the shelf ─────────────────────────────────────────────────────────
print("-- [5] honest use: one match struck, one fill of the lamp, a letter — the guard consumes exactly that")
reset_larder()
st = {}; sync_guarded(st)
check("fresh study takes every count from the shelf", st["matches"] == 278.0 and st["oil_tin"] == 1.55 and st["paper"] == 80.0, str({k: st.get(k) for k in ("matches", "oil_tin", "paper")}))
st["matches"] -= 1; st["oil_tin"] = round(st["oil_tin"] - 0.25, 3); st["paper"] -= 1; st["ink"] = round(st["ink"] - 0.02, 3)
rec = sync_guarded(st)
check("match / quarter-tin / sheet / ink all consumed, nothing reconciled",
      rec == [] and PV.stock("matches") == 277.0 and PV.stock("oil") == 1.3 and PV.stock("paper") == 79.0 and PV.stock("ink") == 1.98,
      f"{rec} {PV.stock('matches')} {PV.stock('oil')} {PV.stock('paper')} {PV.stock('ink')}")
open_box = min((o for o in PV._load()["objects"] if o["kind"] == "matches" and not o.get("empty")), key=lambda o: o["qty"])
check("the match came off the OPEN box (28 -> 27)", open_box["qty"] == 27.0, str(open_box["qty"]))
for _ in range(3):
    st["matches"] -= 1
rec = sync_guarded(st)
check("three matches between two ticks (fire + lamp + lantern) still pass the cap", rec == [] and PV.stock("matches") == 274.0, f"{rec} {PV.stock('matches')}")
st["matches"] -= 4
rec = sync_guarded(st)
check("four in one tick is refused and reconciled (the study takes the shelf's 274)", rec and st["matches"] == 274.0 and PV.stock("matches") == 274.0, f"{rec} {st['matches']}")

# ── [6] the live stores were never touched ──────────────────────────────────────────────────────────
print("-- [6] isolation")
_live_after = {p.name: p.stat().st_mtime for p in (LIVE / "provisions.json", LIVE / "provisions_log.jsonl") if p.exists()}
check("live data/provisions.json and provisions_log.jsonl mtimes unchanged", _live_before == _live_after, f"{_live_before} -> {_live_after}")
check("every redirected path is inside the temp dir", all(str(p).startswith(str(TMP)) for p in _REDIRECTED))

print()
print(f"{len(FAILS)} failure(s)" if FAILS else "all checks passed")
sys.exit(1 if FAILS else 0)
