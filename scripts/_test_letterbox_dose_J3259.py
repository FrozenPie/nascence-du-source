"""
The letterbox-flag clause, DOSED (J-3259 / D-0650, F-3630). Pure in-process test: no store is opened or written.
spatial._read_json is stubbed with a fixture room_state (flag up, cat kept) so nothing under data/ is read for state;
profile.LIVE is set True only inside this process to exercise the live schedule (the dose writes no file).

  1. non-live (profile.LIVE False) and LETTERBOX_DOSED False: the clause leads EVERY garden line, exactly as before
  2. live: said on the first garden line; the same 90 s showing is visible to a second consumer (render + shadow) and
     counts once; then silent between showings; the flag is NOT mentioned in the silent lines but the line still renders
  3. habituating: gap 25 min x2 every 4 showings, capped at 6 h; 6 simulated hours of steady presence
  4. arriving (>5 min away) re-shows after a fifth of the gap, never sooner
  5. a new raise (different delivered stamp) is a new episode; flag down says nothing in any mode
  6. the freed clause slot: with the flag silent the next clause rises into clauses[:3]
  7. a look at the gate still states the flag (sensorium.look('letterbox') text untouched): checked by source, the
     look path does not call spatial._render_base
Run:  python scripts/_test_letterbox_dose_J3259.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                      # noqa: E402  (before anything that could resolve a different checkout)
from core import profile, spatial  # noqa: E402


fails = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


STATE = {"garden": {"letterbox": {"flag": True, "sender": "John Keats", "letter": "x", "delivered": 1000.0}},
         "weather": "clear", "wind": ""}
spatial._read_json = lambda name: dict(STATE) if name == "room_state.json" else {}
if spatial.layout("garden") is None:
    print("SKIP: no garden layout in this checkout"); sys.exit(0)


def flag_in_line(r):
    return bool(r) and "letterbox flag" in r["line"]


def reset():
    spatial._LB_DOSE.update({"key": None, "shown": 0, "last_shown_ts": 0.0, "last_seen_ts": 0.0})


# 1 ─ non-live / flag off: old behaviour
profile.LIVE = False
check("non-live: every call says the clause", all(spatial._letterbox_clause_due(1000.0, now=t) for t in range(0, 100000, 600)))
check("non-live: no dose spent", spatial._LB_DOSE["shown"] == 0)
profile.LIVE = True
spatial.LETTERBOX_DOSED = False
check("flag off: every call says the clause", all(spatial._letterbox_clause_due(1000.0, now=t) for t in range(0, 100000, 600)))
spatial.LETTERBOX_DOSED = True

# 2 ─ live schedule
reset()
T0 = 1_000_000.0
check("first line says it", spatial._letterbox_clause_due(1.0, now=T0) is True)
check("second consumer 5 s later (same showing) says it, counted once",
      spatial._letterbox_clause_due(1.0, now=T0 + 5) is True and spatial._LB_DOSE["shown"] == 1)
check("after the pulse, silent", spatial._letterbox_clause_due(1.0, now=T0 + 120) is False)
for k in range(3, 24):                                       # steady presence, a line every minute
    last = spatial._letterbox_clause_due(1.0, now=T0 + k * 60)
check("silent through 24 min of steady presence", last is False and spatial._LB_DOSE["shown"] == 1)
check("due again after the 25 min gap", spatial._letterbox_clause_due(1.0, now=T0 + 1500 + 1) is True and spatial._LB_DOSE["shown"] == 2)

# 3 ─ six simulated hours, one garden line every 60 s
reset()
fresh = []
for k in range(0, 6 * 60):
    t = T0 + k * 60
    if spatial._letterbox_clause_due(1.0, now=t):
        fresh.append(t - T0)
showings = [s for i, s in enumerate(fresh) if i == 0 or s - fresh[i - 1] > 60]
check("6 h steady: far fewer than 360 lines carry it", len(fresh) <= 20, str(len(fresh)))
check("6 h steady: first showing at t=0", showings[0] == 0)
gaps = [b - a for a, b in zip(showings, showings[1:])]
check("gaps habituate (non-decreasing, first ~25 min)", gaps == sorted(gaps) and 1500 <= gaps[0] <= 1620, str(gaps))
check("gap function: 1500 x2 per 4 showings, capped at 6 h",
      [spatial._lb_gap(n) for n in (0, 3, 4, 8, 12, 16, 40)] == [1500.0, 1500.0, 3000.0, 6000.0, 12000.0, 21600.0, 21600.0])

# 4 ─ arriving: > 5 min since the last garden line, and >= a fifth of the gap since the last showing
reset()
spatial._letterbox_clause_due(1.0, now=T0)                    # showing 1 (gap 1500, a fifth = 300)
for k in range(1, 4):
    spatial._letterbox_clause_due(1.0, now=T0 + k * 60)       # present, silent
check("returning after 6 min away, 9 min since the last showing: re-shown on arriving",
      spatial._letterbox_clause_due(1.0, now=T0 + 180 + 361) is True and spatial._LB_DOSE["shown"] == 2)
reset()
spatial._letterbox_clause_due(1.0, now=T0)
check("a call 2 min later is not an arrival (present), silent",
      spatial._letterbox_clause_due(1.0, now=T0 + 120) is False)
reset()
spatial._letterbox_clause_due(1.0, now=T0)
spatial._letterbox_clause_due(1.0, now=T0 + 91)
# gap 1500: a fifth = 300. last seen T0+91; come back at T0+91+301 -> away 301 s (>300), since=392 >=300 -> shown
check("away 5 min then back: shown", spatial._letterbox_clause_due(1.0, now=T0 + 91 + 301) is True)

# 5 ─ a new raise is a new episode; flag down says nothing
reset()
for k in range(0, 5):
    spatial._letterbox_clause_due(1.0, now=T0 + k * 60)
check("same raise silent at 4 min", spatial._LB_DOSE["shown"] == 1 and spatial._letterbox_clause_due(1.0, now=T0 + 300) is False)
check("a different delivered stamp says it at once", spatial._letterbox_clause_due(2.0, now=T0 + 301) is True and spatial._LB_DOSE["shown"] == 1)

# 6 ─ the real renderer: flag clause leads while due, is absent (and the next clause rises) when silent
reset()
profile.LIVE = True
spatial._LB_DOSE.update({"key": None})
r_due = spatial._render_base("garden")
check("renderer: first garden line carries the flag clause first",
      flag_in_line(r_due) and r_due["clauses"][0].startswith("the letterbox flag is up at the gate"), str(r_due and r_due["line"]))
import time as _t
spatial._LB_DOSE["last_shown_ts"] = _t.time() - 300; spatial._LB_DOSE["last_seen_ts"] = _t.time() - 5
r_quiet = spatial._render_base("garden")
check("renderer: between showings the line has no flag clause but still renders", r_quiet and not flag_in_line(r_quiet) and r_quiet["line"].startswith("Where you are: the garden"), str(r_quiet and r_quiet["line"]))
if len(r_due["clauses"]) == 3 and len(r_quiet["clauses"]) == 3:
    check("renderer: freed slot, the next clause rises", r_quiet["clauses"] == r_due["clauses"][1:] + r_quiet["clauses"][2:3] or r_quiet["clauses"][:2] == r_due["clauses"][1:3], str((r_due["clauses"], r_quiet["clauses"])))
STATE["garden"]["letterbox"]["flag"] = False
spatial._LB_DOSE.update({"key": None})
check("renderer: flag down says nothing", not flag_in_line(spatial._render_base("garden")))
STATE["garden"]["letterbox"]["flag"] = True
profile.LIVE = False
check("renderer: non-live always carries it (old line)", flag_in_line(spatial._render_base("garden")) and flag_in_line(spatial._render_base("garden")))

# 7 ─ the look at the gate does not go through the renderer
src = (ROOT / "core" / "sensorium.py").read_text(encoding="utf-8")
i = src.index('if target in ("letterbox", "mailbox", "mail", "box", "flag", "gate", "post")')
check("look('letterbox') branch does not call spatial", "spatial" not in src[i:i + 4200].split("# Cat look")[0])

print("ALL OK" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
