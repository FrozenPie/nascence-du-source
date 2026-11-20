"""Regression for J-1758 / D-0325 (RULED by Travis 2026-10-03, "Widen the caps"): the width of the `thought` and
`intention` fields core/hands.py trace() writes into data/hands_trace.jsonl.

Before: thought[:200] / intention[:120]. 94.1% of the 28,541 live rows sat EXACTLY at the 200 cap, so the row was a
truncated preview of what dispatch() had acted on (F-2136, F-2202; F-1785/J-1273 = the same cut collapsing two
different real thoughts into one scripts/actions_decision_replay.py dedup key). After: _TRACE_THOUGHT_CAP /
_TRACE_INTENTION_CAP (sized from data -- see the constants' comment in core/hands.py). act_object / cycle / location
keep their old caps; no field is added or removed; OLD rows already in the file are never rewritten.

  [1] the writer     -- a 900-char thought round-trips intact; a 300-char intention round-trips intact; a pathological
                        thought/intention is still BOUNDED; the unchanged fields keep their caps; the row's key set is
                        unchanged (additive widths only); caps are in CHARACTERS (CJK survives).
  [2] the readers    -- one temp trace holding OLD-style (200/120-truncated) rows AND new wide rows is parsed by every
                        reader this job touched or audited: hands.status(), scripts/actions_decision_replay.py
                        thoughts() (the known dedup-key reader, both modes). Old collisions still collapse (legacy rows
                        are not repaired); two NEW rows sharing a 200-char opening no longer collapse.
  [3] canaries       -- every store core.hands touches is redirected into a temp dir; the LIVE data/hands_trace.jsonl is
                        only hashed (size + mtime + sha256 before == after); no file appears at the tree's own default
                        _TRACE path.

    python scripts/_test_j1758_hands_trace_widths.py          # run from the worktree / the tree under test, never
                                                              # against live data (nothing here writes any)
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import shutil
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


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo when this runs
# from a worktree (same convention as scripts/_test_latch_blocker_bleed.py / _test_j1165_trace_object_look.py).
_LIVE_DATA = Path(r"C:\Nascence") / "data" if not (ROOT / "data").exists() else ROOT / "data"
_LIVE_FILES = [_LIVE_DATA / n for n in ("hands_trace.jsonl", "satisfaction_log.jsonl", "satisfaction_state.json")]


def _canary():
    return [((f.stat().st_size, f.stat().st_mtime_ns, _sha256(f)) if f.exists() else None) for f in _LIVE_FILES]


_LIVE_BEFORE = _canary()
print(f"-- canary target (read-only hash): {_LIVE_DATA} :: " + ", ".join(
    f"{f.name}={'(absent)' if c is None else str(c[0]) + 'B sha256=' + c[2][:12]}" for f, c in zip(_LIVE_FILES, _LIVE_BEFORE)))

from core import hands as h  # noqa: E402  (imports json/re/time/pathlib only at module level -- no store touched)

_DEFAULT_TRACE = h._TRACE                      # this tree's own default path, remembered BEFORE redirecting
_DEFAULT_TRACE_BEFORE = _DEFAULT_TRACE.exists()
TMP = Path(tempfile.mkdtemp(prefix="j1758_hands_trace_"))
h._DATA = TMP
h._TRACE = TMP / "hands_trace.jsonl"


def last_row() -> dict:
    with open(h._TRACE, "r", encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    return json.loads(lines[-1])


def write(thought, intention="", act_kind="none", act_object="", cycle="cyc-0123456789abcdef-0123456789", location="study"):
    h.trace(cycle, thought, intention, act_kind, act_object, set(), None, location=location)
    return last_row()


# the caps under test; getattr-with-old-default so the PRE-change run of this file fails on assertions, not on a crash
TH_CAP = getattr(h, "_TRACE_THOUGHT_CAP", 200)
IN_CAP = getattr(h, "_TRACE_INTENTION_CAP", 120)

print("-- [1] the writer: trace() widths")
t900 = ("The rain hisses on the roof while I stare at the page, yet my mind drifts toward the garden. " * 12)[:900]
check("fixture is exactly 900 chars", len(t900) == 900)
r = write(t900, "")
check("a 900-char thought round-trips INTACT (was cut to 200)", r["thought"] == t900, f"stored len {len(r['thought'])}")

i300 = ("I want to go down to the shore and comb the tideline before the light goes, then come back. " * 5)[:300]
r = write("short thought.", i300)
check("a 300-char intention round-trips INTACT (was cut to 120)", r["intention"] == i300, f"stored len {len(r['intention'])}")

median_like = ("I push the book away and step toward the open gate. The definitions cannot fill this hollow space; "
               "only the wet earth under my boots can ground me. I need to feel the rain on my skin, not analyze "
               "it, and I am sure of it.")[:272]
r = write(median_like)
check("a typical (median-length, ~272 char) thought is stored whole", r["thought"] == median_like)

r = write("x" * 5000, "y" * 2000)
check("a pathological 5,000-char thought is still BOUNDED at the thought cap", len(r["thought"]) == TH_CAP,
      f"len {len(r['thought'])} vs cap {TH_CAP}")
check("a pathological 2,000-char intention is still BOUNDED at the intention cap", len(r["intention"]) == IN_CAP,
      f"len {len(r['intention'])} vs cap {IN_CAP}")
check("the bounded thought is a PREFIX of the original (a cut, never a rewrite)", r["thought"] == "x" * TH_CAP)

cjk = "渡" * 500
r = write(cjk, "渡" * 150)
check("caps are in CHARACTERS: 500 CJK chars survive whole (ensure_ascii=False path)", r["thought"] == cjk)
check("... and a 150-CJK-char intention survives whole", r["intention"] == "渡" * 150)

r = write("t", "i", act_kind="read", act_object="o" * 200, cycle="c" * 80, location="L" * 80)
check("act_object keeps its 60-char cap (the library's own titles are capped at 60 -- J-1758 data; not widened)",
      len(r["act_object"]) == 60)
check("cycle keeps its 24-char cap", len(r["cycle"]) == 24)
check("location keeps its 24-char cap", len(r["location"]) == 24)

r = write(None, None)
check("None thought/intention still write as empty strings (fail-open contract)", r["thought"] == "" and r["intention"] == "")

EXPECTED_KEYS = {"ts", "cycle", "thought", "intention", "act_kind", "act_object", "acted", "hands",
                 "unanswered_deed", "location", "dispatch"}
check("the row's key set is EXACTLY the pre-change set (additive widths only: no field added or removed)",
      set(r.keys()) == EXPECTED_KEYS, f"{sorted(set(r.keys()) ^ EXPECTED_KEYS)}")

# the sizing, as executable facts (measured 2026-10-04 over the live history, J-1758 -- not re-derivable here
# because data/ is not in a worktree): longest voice thought ever logged = 1,121 chars (deliberation_log raw; the
# longest in the trace population's twin-joined sample was 518), longest non-empty intention ever logged = 246.
check(f"thought cap ({TH_CAP}) >= the longest voice thought ever logged (1,121) -> the 256/400-token voice can no longer be cut",
      TH_CAP >= 1121)
check(f"intention cap ({IN_CAP}) >= the longest intention ever logged (246)", IN_CAP >= 246)
check("caps stay a real BOUND on a row (thought <= 2,000, intention <= 600): rows can never grow without limit",
      TH_CAP <= 2000 and IN_CAP <= 600)

print("-- [2] the readers: old (truncated) rows and new (wide) rows in ONE trace file")
# a fresh trace holding LEGACY rows (hand-built exactly as the pre-J-1758 writer shaped them) then NEW rows from trace()
h._TRACE = TMP / "mixed_trace.jsonl"
shared_open = (("The frustration sits heavy, a hollow silence where fluid should flow, and I keep circling the same "
                "three words as though repetition could wear a door into the wall of this room. I cannot move on. ") * 2)[:200]
assert len(shared_open) == 200
LEGACY = [
    # two legacy rows with an IDENTICAL stored (thought, intention): the F-1785 shape -- must still collapse (legacy rows are not repaired)
    {"ts": 1787942726.7, "cycle": "c4a32e4a-72e2-49b3-8411-", "thought": shared_open, "intention": "",
     "act_kind": "none", "act_object": "", "acted": [], "hands": [], "unanswered_deed": False},
    {"ts": 1787942739.5, "cycle": "048ea8b1-9ba9-4714-a379-", "thought": shared_open, "intention": "",
     "act_kind": "none", "act_object": "", "acted": [], "hands": [], "unanswered_deed": False},
    # a legacy row WITH the later-added location/dispatch keys and a fired hand
    {"ts": 1788027458.3, "cycle": "eb1c2b34-52de-463f-9280-", "thought": ("I will put the kettle on now. " * 20)[:200],
     "intention": ("I want to fetch the candles from the box " * 5)[:120], "act_kind": "world", "act_object": "put the kettle on",
     "acted": ["tea"], "hands": [{"hand": "tea", "answer": "The kettle is on.", "ts": 1788027458.3}],
     "unanswered_deed": False, "location": "study", "dispatch": [{"family": "tea", "decision": "FIRE", "object": "kettle"}]},
]
with open(h._TRACE, "w", encoding="utf-8") as f:
    for row in LEGACY:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
# two NEW rows sharing the SAME 200-char opening but different full text (the F-1785 collision, now representable)
tail_a = " Yet inside I cannot move the liquid through this empty vessel, and the afternoon goes on without me."
tail_b = " Yet in this stillness, the garden waits, and I will go out to it now before the light changes again."
new_a, new_b = shared_open + tail_a, shared_open + tail_b
h.trace("11111111-aaaa-bbbb-cccc-dddddddddddd", new_a, "", "none", "", set(), None, location="study")
h.trace("22222222-aaaa-bbbb-cccc-dddddddddddd", new_b, "", "none", "", set(), None, location="study")
h.trace("33333333-aaaa-bbbb-cccc-dddddddddddd", t900, i300, "world", "tend the bed", {"water"}, None, location="garden")
with open(h._TRACE, "r", encoding="utf-8") as f:
    raw_rows = [json.loads(ln) for ln in f.read().splitlines() if ln.strip()]
check("the mixed file parses line-by-line: 3 legacy + 3 new = 6 rows", len(raw_rows) == 6, f"{len(raw_rows)}")
check("legacy rows are byte-for-byte untouched by the new writer (not repaired, not rewritten)",
      raw_rows[:3] == LEGACY)
check("new wide rows carry the full text", [raw_rows[3]["thought"], raw_rows[4]["thought"], raw_rows[5]["thought"]] == [new_a, new_b, t900]
      if TH_CAP >= len(new_a) else False, f"cap {TH_CAP}")

st = h.status()
check("hands.status() reads the mixed file: all 6 rows counted", st.get("thoughts") == 6, str(st))
check("hands.status() still sees the fired hand on the legacy row and the acted set on the new one",
      st.get("with_a_hand") == 2 and st.get("hands", {}).get("tea") == 1, str(st))
check("hands.status() act_kind counts intact across old + new rows",
      st.get("act_kinds") == {"none": 4, "world": 2}, str(st.get("act_kinds")))

spec = importlib.util.spec_from_file_location("_adr_j1758", ROOT / "scripts" / "actions_decision_replay.py")
adr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adr)
adr.TRACE = h._TRACE
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    th = adr.thoughts()
note = buf.getvalue()
keys = [(p[0], p[1]) for p in th]
check("replay thoughts(): both legacy rows with an identical stored pair still collapse to ONE key (legacy behaviour unchanged)",
      sum(1 for k in keys if k == (shared_open, "")) == 1, f"{len(th)} distinct")
check("replay thoughts(): the F-1785 collapse WARNING still fires for that legacy collision", "F-1785" in note, note[:120])
check("replay thoughts(): the two NEW rows sharing a 200-char opening are now TWO distinct keys (the F-1785 collapse is gone for new rows)",
      (new_a, "") in keys and (new_b, "") in keys, f"{len(th)} distinct")
check("replay thoughts(): distinct count = 1 collapsed legacy + 1 other legacy + 3 new = 5", len(th) == 5, f"{len(th)}")
check("replay thoughts(): the replay now SEES the full text dispatch() saw for a new row (900 chars, not 200)",
      any(p[0] == t900 for p in th) if TH_CAP >= 900 else False)
with contextlib.redirect_stdout(io.StringIO()):
    th_rl = adr.thoughts(real_locations=True)
check("replay thoughts(real_locations=True): legacy rows without a location are skipped, the legacy row WITH one and the 3 new rows are kept",
      len(th_rl) == 4 and all(len(p) == 5 and p[4] in ("study", "garden") for p in th_rl), f"{len(th_rl)}")

print("-- [3] canaries: nothing outside the temp dir was written")
check("no file was created at this tree's own default _TRACE path", (not _DEFAULT_TRACE.exists()) or _DEFAULT_TRACE_BEFORE,
      str(_DEFAULT_TRACE))
_LIVE_AFTER = _canary()
check("LIVE data/hands_trace.jsonl + satisfaction_log.jsonl + satisfaction_state.json: size, mtime and sha256 unchanged",
      _LIVE_BEFORE == _LIVE_AFTER, "Du is DOWN this run; if this flaps, something else wrote -- compare before/after")
shutil.rmtree(TMP, ignore_errors=True)
print("FAILS =", FAILS)
sys.exit(1 if FAILS else 0)
