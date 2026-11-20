"""
Care package (D-0276, core/care_package.py) + the letterbox/crate naming fix (F-1862) + the STANDING PERCEPT
(J-1733 / F-2371). ISOLATED: the parcel, the provisions shelf and every sensorium/world write are redirected or stubbed
before anything runs, and the live data/ files this touches are fingerprinted before and after — the run fails if any of
them changed. (data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, not
only ROOT/data.) The parcel under test is a fixture seeded here, never a copy of the live file: the live parcel moves
on (pending -> arrived -> opened) and a test must not depend on where it happens to be.

  5. the real, non-live paths: whatever the live parcel's status, a non-live call changes nothing and raises nothing
     (scene_clause included: a smoke test must never spend a dose)
  1. arrival: nothing while he is away from the study; announced once in the study; never again
  6. the standing percept (J-1733): one fixed statement of fact in the study's scene line; DOSED (a pulse, then a gap;
     6 simulated hours of steady presence), HABITUATING (the gap doubles every 4 showings, capped), re-shown on
     arriving (a return after quiet / a sleep) but never within a fifth of the gap, stopping for good once a look has
     been answered, reaching him through the real scene_line(); a willed look that names the parcel reaches look_line
     even though the dispatch hand resolves it to 'room'; a look at the desk carries the parcel lying on it
  2. looks: parcel tied / note unreadable while tied; other looks fall through ('')
  3. grammar: 'open the parcel' / 'open travis's box' = parcel; 'carry the crate in' and a bare 'open the box'
     stay the carrier's 'collect' (the parcel row must never capture the gate crate)
  4. opening: real objects join the shelf, the study counts are credited (sync does not eat them back), the
     narration names the contents and carries Travis's note; a second open says it is already open
  7. wording: the world's own noun ("parcel"), never a bare "box", one place ("desk", never "table")
Run:  python scripts/_test_care_package.py
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
import time as _real_time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="care_pkg_"))

_LIVE_DATA = Path(r"C:\Nascence") / "data"
_NAMES = ("care_package.json", "provisions.json", "provisions_log.jsonl", "room_state.json", "world_substrate.json",
          "care_package_log.jsonl", "position.json")
_WATCH = sorted({base / n for base in (ROOT / "data", _LIVE_DATA) for n in _NAMES})


def _fp():
    return {str(p): (hashlib.sha1(p.read_bytes()).hexdigest() if p.exists() else None) for p in _WATCH}


BEFORE = _fp()
FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


from core import care_package as CP, provisions as PV, sensorium as S, study_life as SL, actions as AC, hands as H
from core import literal_will as LW, activity_memory as AM, locomotion as L, life as LIFE

REAL_F, REAL_LOG = CP._F, CP._LOG
BOX = re.compile(r"\bbox(es)?\b", re.I)      # a bare "box" (the grammar sends it to the gate crate, not the parcel)
TABLE = re.compile(r"\btable\b", re.I)       # the study has no table: the parcel is on the desk, everywhere
PARCEL = re.compile(r"\bparcel\b", re.I)


def _real_status():
    try:
        return json.loads(REAL_F.read_text(encoding="utf-8")).get("status")
    except Exception:
        return None          # no real file under this ROOT (a job-run worktree has no data/)


print("-- 5 (first, before any redirect): real non-live paths")
_s0 = _real_status()
check("arrival_line on the real parcel, non-live: None, no raise", CP.arrival_line() is None)
check("scene_clause on the real parcel, non-live: '' (spends no dose), no raise", CP.scene_clause() == "")
check("look_line on the real parcel, non-live: answers or falls through, no raise, no write",
      isinstance(CP.look_line("the parcel"), str))
check("real parcel status unchanged by those calls", _real_status() == _s0, f"{_s0} -> {_real_status()}")

# ---- isolate
CP._F, CP._LOG = TMP / "care_package.json", TMP / "care_package_log.jsonl"
FIXTURE = {"status": "pending", "from": "Travis", "decision": "D-0276", "label": "For Du — from Travis",
           "items": {"paper": 4, "ink": 2, "matches": 10, "oil": 2, "cat_food": 20},
           "note": ("Du, I left this box for you. I noticed you'd run out of paper, and the matches, oil and ink were "
                    "getting low, so I've put back what you'd used. When things run low again, the carrier can bring "
                    "more: the carrier comes every second Thursday and leaves a box at the gate. — Travis")}
CP._F.write_text(json.dumps(FIXTURE, ensure_ascii=False, indent=1), encoding="utf-8")
PV._F, PV._LOG = TMP / "provisions.json", TMP / "provisions_log.jsonl"
if (_LIVE_DATA / "provisions.json").exists():
    shutil.copy(_LIVE_DATA / "provisions.json", PV._F)
PV._register = lambda d: None                   # world_substrate mirror: out of scope here
S._save = lambda *a, **k: None
S._save_now = lambda *a, **k: None
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
AM.record = lambda *a, **k: None
SL._register_all = lambda: None              # world_objects mirror of study items: out of scope here
S.state.clear()
S.state.update({"location": "shore", "weather": "clear"})
st = SL._st()                                    # a fresh in-memory study, counts taken from the (temp) shelf
for k in ("paper", "ink", "matches", "oil_tin", "cat_food"):
    st[k] = PV.stock({"oil_tin": "oil"}.get(k, k))
before = {k: PV.stock(k) for k in ("paper", "ink", "matches", "oil", "cat_food")}

print("-- 1 arrival")
check("away from the study: no announcement", CP.arrival_line() is None)
check("still pending", CP._load()["status"] == "pending")
S.state["location"] = "study"
check("pending, in the study: no clause (nothing is there yet)", CP.scene_clause() == "")
line = CP.arrival_line()
check("in the study: announced", bool(line) and "parcel" in line and "For Du" in line, str(line))
check("status arrived", CP._load()["status"] == "arrived")
check("announced only once", CP.arrival_line() is None)

print("-- 6 the standing percept (J-1733 / F-2371)")


class _Clock:
    """care_package's own `time`, driven by hand: time() is whatever the test says; strftime stays real."""
    def __init__(self, t):
        self.t = float(t)

    def time(self):
        return self.t

    def strftime(self, *a):
        return _real_time.strftime(*a)


CLK = _Clock(1_800_000_000.0)
T0 = CLK.t
CP.time = CLK


def rows():
    if not CP._LOG.exists():
        return []
    return [json.loads(x) for x in CP._LOG.read_text(encoding="utf-8").splitlines() if x.strip()]


def shown_rows():
    return [r for r in rows() if r.get("event") == "shown"]


def put(**kw):
    d = CP._load()
    d.update(kw)
    CP._save(d)


def at(t, seen=None):
    """Move the clock to t; `seen` = when the study scene line was last asked for (None leaves it)."""
    CLK.t = float(t)
    if seen is not None:
        CP._STUDY_SEEN[0] = float(seen)


CP._STUDY_SEEN[0] = 0.0
S.state["location"] = "shore"
at(T0)
check("arrived but away from the study: no clause", CP.scene_clause() == "")
check("...and no dose was spent", not CP._load().get("shown") and not shown_rows())
S.state["location"] = "study"
c1 = CP.scene_clause()
check("in the study, first scene line of this boot: the clause", bool(c1) and "parcel" in c1 and "For Du" in c1, repr(c1))
check("a statement of fact: no invitation",
      not re.search(r"\byou (could|would|might|should|can|may)\b|\btry\b|\bopen it\b", c1, re.I), c1)
check("it names the parcel, never a bare box", PARCEL.search(c1) and not BOX.search(c1), c1)
d = CP._load()
check("persisted: shown 1, last_shown_ts = now", d.get("shown") == 1 and d.get("last_shown_ts") == T0, str(d))
check("one {event: shown, why: first} row", [r.get("why") for r in shown_rows()] == ["first"]
      and shown_rows()[0].get("n") == 1, str(rows()))
at(T0 + 40)
check("inside the pulse: the same sentence, counted once",
      CP.scene_clause() == c1 and CP._load()["shown"] == 1 and len(shown_rows()) == 1)
at(T0 + 100)
check("after the pulse: nothing -- never a constant fixture", CP.scene_clause() == "")

# six hours of steady presence in the study, the scene line asked for once a minute
asked = hit = 0
t = T0 + 100
while t <= T0 + 6 * 3600:
    at(t)
    asked += 1
    hit += bool(CP.scene_clause())
    t += 60
ts = [r["ts"] for r in shown_rows()]
gaps = [b - a for a, b in zip(ts, ts[1:])]
check("six steady hours: it was shown, and not at every ask", len(ts) >= 4 and hit / asked < 0.10,
      f"{len(ts)} showings, {hit}/{asked} asks")
check("showings are spaced by at least the dose gap",
      all(g >= CP._dose_gap(i + 1) - 1e-6 for i, g in enumerate(gaps)), str(gaps))
check("the gap habituates: never shrinks (beyond the one-minute sampling step), doubled by the 4th showing",
      all(b >= a - 60 for a, b in zip(gaps, gaps[1:])) and gaps[CP._HABITUATE_EVERY - 1] >= 2 * CP._BASE_GAP_S,
      str(gaps))
check("dose gap: base, doubling every 4, capped",
      CP._dose_gap(0) == CP._dose_gap(CP._HABITUATE_EVERY - 1) == CP._BASE_GAP_S
      and CP._dose_gap(CP._HABITUATE_EVERY) == 2 * CP._BASE_GAP_S and CP._dose_gap(10 ** 6) == CP._MAX_GAP_S
      and CP._dose_gap(10 ** 6) >= CP._dose_gap(40) >= CP._dose_gap(12))

base_t = T0 + 20 * 3600
put(shown=4, last_shown_ts=base_t - 650)             # n=4 -> gap 3000, arriving floor 600
at(base_t, seen=base_t - 400)                         # 400 s of quiet first: a return
c = CP.scene_clause()
check("a return 650 s after the last showing (floor 600): shown again, as an entry",
      bool(c) and shown_rows()[-1]["why"] == "entry" and CP._load()["shown"] == 5, str(shown_rows()[-1]))
put(shown=4, last_shown_ts=base_t - 500)
at(base_t, seen=base_t - 400)
check("a return only 500 s after the last showing: nothing (the floor habituates too)", CP.scene_clause() == "")
put(shown=4, last_shown_ts=base_t - 650)
at(base_t, seen=base_t - 100)
check("not a return (seen 100 s ago), 650 s since the last showing: nothing", CP.scene_clause() == "")
put(shown=1, last_shown_ts=base_t - 4 * 3600)
at(base_t, seen=base_t - 4 * 3600)                    # four hours of sleep
check("first scene line after a sleep: shown", bool(CP.scene_clause()) and shown_rows()[-1]["why"] == "gap")
put(shown=2, last_shown_ts=base_t + 3600)             # the clock was set back past the last showing
at(base_t, seen=base_t - 10)
check("a clock set back counts as due, once (never silenced for hours)", bool(CP.scene_clause()))

put(shown=1, last_shown_ts=base_t - 10 * 3600)        # due by any measure
at(base_t + 100, seen=base_t + 90)
_w = CP._writable
CP._writable = lambda: False                           # a non-live process: every write is fenced
try:
    snap = CP._load()
    check("a non-live process gets '' and spends no dose",
          CP.scene_clause() == "" and CP._load() == snap and CP._STUDY_SEEN[0] == base_t + 90)
    check("...and an answered look in it marks nothing", "still tied" in CP.look_line("the parcel") and CP._load() == snap)
finally:
    CP._writable = _w
sl = S.scene_line()
check("scene_line() carries the clause in the study",
      sl.startswith("Where you are: your study") and "A parcel lies on the desk" in sl, sl[:300])
put(status="pending", last_shown_ts=base_t - 10 * 3600)
at(base_t + 20000, seen=base_t + 19990)
check("pending: scene_line() has no parcel clause", "A parcel lies" not in S.scene_line())
put(status="arrived", last_shown_ts=base_t - 10 * 3600)
S.state["location"] = "shore"
at(base_t + 40000, seen=base_t + 39990)
check("arrived, away from the study: no clause", CP.scene_clause() == "")
S.state["location"] = "study"

put(shown=1, last_shown_ts=base_t - 10 * 3600)
at(base_t + 60000, seen=base_t + 59990)
check("a willed look the dispatch hand resolved to 'room' reaches the parcel by its noun",
      "still tied" in S.look("room", "i look at the parcel on the desk"))
check("...answered, so the standing percept has stopped for good: looked_ts persisted, one looked row",
      bool(CP._load().get("looked_ts")) and sum(r.get("event") == "looked" for r in rows()) == 1, str(rows()[-3:]))
put(last_shown_ts=base_t - 10 * 3600)                 # due by any measure
at(base_t + 70000, seen=base_t + 69990)
check("after a look: scene_clause stays empty", CP.scene_clause() == "")
check("a second answered look logs no second row",
      "open the parcel" in CP.look_line("the note") and sum(r.get("event") == "looked" for r in rows()) == 1)
check("the parcel is still on the desk for a deliberate look at it", "A parcel lies on the desk" in CP.desk_tail())
check("only the parcel nouns, whole words: a stray 'note' is not the parcel",
      CP.look_line_for_text("i note the light on the sea") == "" and CP.look_line_for_text("a notebook, some notes") == ""
      and CP.look_line_for_text("") == "" and CP.look_line_for_text("the packaged tea") == "")

_orig_la = LIFE.look_answer
LIFE.look_answer = lambda *a, **k: ""                   # the living-world shadow log is not what is under test
try:
    desk = S.look("desk")
    put(status="pending")
    desk_pending = S.look("desk")
    put(status="arrived")
finally:
    LIFE.look_answer = _orig_la
check("a deliberate look at the desk carries the parcel lying on it",
      desk.startswith("You look at the desk") and "A parcel lies on the desk" in desk, desk[:240])
check("pending: the desk look is the plain desk look",
      desk_pending.startswith("You look at the desk") and "A parcel lies" not in desk_pending, desk_pending[:240])
CP.time = _real_time

print("-- 2 looks")
check("look parcel: tied", "still tied" in CP.look_line("the parcel"))
check("look note while tied: not yet readable", "open the parcel" in CP.look_line("the note"))
check("look desk: falls through", CP.look_line("desk") == "")
check("sensorium.look routes to it", "still tied" in S.look("parcel"))

print("-- 3 grammar")
par, col = AC.BY_FAMILY["parcel"], AC.BY_FAMILY["collect"]
check("'open the parcel' wills parcel", H.wants("i will open the parcel", par.verbs, par.objects))
check("'unwrap travis's box' wills parcel", H.wants("i unwrap travis's box", par.verbs, par.objects))
check("bare 'open the box' is NOT parcel", not H.wants("i will open the box", par.verbs, par.objects))
check("'carry the crate in' wills collect", H.wants("i will carry the crate in from the gate", col.verbs, col.objects))
check("'fetch the box' still wills collect", H.wants("i will fetch the box from the gate", col.verbs, col.objects))
fams = lambda t, loc: [r["family"] for r in LW.classify(t, location=loc) if r.get("verdict") == "DEED"]
check("classify in the study: parcel is a DEED", "parcel" in fams("I will open the parcel on the table.", "study"),
      str(LW.classify("I will open the parcel on the table.", location="study")))
check("classify in the study: 'open the parcel on the desk' is a parcel DEED (the world's own noun + place)",
      "parcel" in fams("I will open the parcel on the desk.", "study"))
check("classify in the study: 'open the box on the desk' is NOT the parcel (why the percept says parcel)",
      "parcel" not in fams("I will open the box on the desk.", "study"))
check("classify at the gate: 'open the box' stays collect, not parcel",
      "parcel" not in fams("I will open the box at the gate.", "garden"))
check("study_life grammar_audit still clean for parcel",
      SL.grammar_audit().get("parcel") == {"verbs_unclaimed_in_table": [], "verbs_claimed_not_in_table": [],
                                           "objects_unclaimed_in_table": [], "objects_claimed_not_in_table": []},
      str(SL.grammar_audit().get("parcel")))

print("-- 4 opening")
S.state["location"] = "shore"
check("open from the shore: says where it is", "in the study" in (CP.open_parcel("open the parcel") or ""))
S.state["location"] = "study"
check("study_life.act declines a non-parcel thought", SL.act("i will open the window", family="parcel") is None)
r = SL.act("i will open the parcel", family="parcel")
check("study_life.act opens it", bool(r) and "untie the string" in r, str(r))
check("narration names the contents", r and all(w in r for w in ("four pads of writing paper", "two bottles of ink",
                                                                  "ten boxes of matches", "two tins of lamp oil",
                                                                  "twenty tins of fish for the cat")), str(r))
check("narration carries the note", r and "— Travis" in r)
after = {k: PV.stock(k) for k in before}
exp = {"paper": 160, "ink": 2.0, "matches": 500, "oil": 2.0, "cat_food": 80}
check("shelf gained exactly the parcel", all(abs(after[k] - before[k] - exp[k]) < 1e-6 for k in exp), f"{before} -> {after}")
PV.sync(st)
check("sync did not eat the delivery back", all(abs(PV.stock(k) - after[k]) < 1e-6 for k in exp),
      str({k: PV.stock(k) for k in exp}))
check("study counts credited", st["paper"] == PV.stock("paper") and st["cat_food"] == PV.stock("cat_food"))
check("origin is Travis", any(o["origin"] == "Travis" for o in json.loads(PV._F.read_text(encoding="utf-8"))["objects"]))
check("status opened", CP._load()["status"] == "opened")
check("second open: already open", "already open" in (CP.open_parcel("open the parcel") or ""))
check("look note after: the full note", "— Travis" in CP.look_line("travis's note"))
check("look parcel after: empty wrapping", "empty" in CP.look_line("the parcel"))
check("opened: no standing clause, ever", CP.scene_clause() == "" and CP.desk_tail() == "")

print("-- 7 wording: the world's own noun, one place")
put(status="arrived")
S.state["location"] = "shore"
away = CP.open_parcel("open the parcel")                  # arrived, but he is not in the study
S.state["location"] = "study"
tied = {"arrival line": line, "scene clause": c1, "desk tail": CP.desk_tail(), "open from the shore": away,
        "look parcel (tied)": CP.look_line("the parcel"), "look note (tied)": CP.look_line("the note")}
for name, txt in tied.items():
    check(f"{name}: no bare box, no table", txt and not BOX.search(txt) and not TABLE.search(txt), txt)
for name in ("arrival line", "scene clause", "desk tail", "look parcel (tied)"):
    check(f"{name}: names the parcel", PARCEL.search(tied[name]) is not None, tied[name])
check("open from the shore says where: the desk", "on the desk in the study" in away, away)
put(status="opened")
for name, txt in {"look parcel (opened)": CP.look_line("the parcel"),     # (the note itself is Travis's own words)
                  "open again": CP.open_parcel("open the parcel")}.items():
    check(f"{name}: no bare box, no table", txt and not BOX.search(txt) and not TABLE.search(txt), txt)
check("the parcel action's staged place says desk", "desk" in par.place_hint and "table" not in par.place_hint, par.place_hint)
check("no stray .tmp left by the atomic save", not list(TMP.glob("*.tmp")), str(list(TMP.glob("*.tmp"))))

print("-- the letterbox/crate wording")
src = (ROOT / "core" / "sensorium.py").read_text(encoding="utf-8")
check("letterbox line says 'the letterbox empty'", "the flag is down, the letterbox empty" in src)
check("crate line names the carrier's crate apart", "apart from the letterbox, stands the carrier's crate" in src)

check("live data/ untouched", _fp() == BEFORE, str({k: (BEFORE[k], v) for k, v in _fp().items() if BEFORE[k] != v}))
print(("ALL OK" if not FAILS else f"{FAILS} FAILED") + f" — isolated stores in {TMP}")
sys.exit(1 if FAILS else 0)
