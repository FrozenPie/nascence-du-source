"""
J-2476 (sound_world_expansion §3, D-0500): THE GEOPHONY FILLS -- hail_on_roof / hail_on_leaves, drizzle_hiss vs
downpour_drum, rain_down_chimney, tin_roof_tick, stream_over_stones, undertow_rumble, frost_crack, calm_sea_hush.
Hermetic: every store the engine can reach is redirected into a temp dir before anything can write; a Python audit
hook records any write attempt under a live data/ dir; the live files are md5-hashed before and after. Run from the
worktree:  python scripts/_test_j2476_geophony.py   (exit 0 = ALL OK)

  [1] registry: ten Sound-Space points, beds as rate 0.0 / events rated, GRANDFATHERED vs AUDITION split, named pools
      (>= 4 onset, >= 2 renotice, rotating), near/far words, no digit or readout word (D-0434), rail try-order
  [2] the clocks: hail is a short drawn burst inside storm weather in the cold seasons only; the roof's window follows
      world_clock's sun; the stream mouth runs except late summer at its floor; all deterministic
  [3] propagation through the REAL soundscape.active_sounds(): the rain grades either side of rain_on_roof on the ladder
      and in agreement with _storm_severity_scale (D-0063's defeater), the chimney, hail by place, the roof, the shore's
      three states, the garden's night hush, frost by season/sky/wind/place; row LAST (pure suffix)
  [4] the percept rail: tin_roof_tick / frost_crack reach him UNNAMED (features, never the cause), the known eight
      render named directly, the 8 h per-key floor, renotice, first refusal kept by the keys ahead
  [5] earning the name: a look up binds the tick; the crack can only ever miss; a book teaches it; sensorium's own
      frost milestone line does not
  [6] the hearing ledger: beds bank hours, events bank counts, through world_tick
  [7] the sidecar dry-run's archetype invariant still holds with the ten keys classified
  [8] isolation: no write attempt under any data/, live hashes unchanged
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j2476_geophony_"))
print("isolated store dir:", TMP)
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("room_state.json", "life_state.json", "life_ledger.jsonl", "life_events.jsonl",
                                        "life_flags.json", "sound_knowledge.json", "soundscape_state.json",
                                        "soundscape_felt_shadow.jsonl", "cat_state.json", "position.json",
                                        "wood_state.json", "sound_strings_constructed.json")]


def _md5(p: Path) -> str:
    if not p.exists():
        return ""
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_before = {p: _md5(p) for p in _LIVE_FILES}

_WATCH = [str(_LIVE_DATA).lower(), str(ROOT / "data").lower()]
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move", "shutil.rmtree"}
LIVE_WRITE_ATTEMPTS: list = []


def _under_watch(p) -> bool:
    try:
        if isinstance(p, int):
            return False
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in _WATCH)


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing and _under_watch(path):
                LIVE_WRITE_ATTEMPTS.append(("open", str(path), mode))
        elif event in _WRITE_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and _under_watch(a):
                    LIVE_WRITE_ATTEMPTS.append((event, str(a), None))
                    break
    except Exception:
        pass


sys.addaudithook(_audit)

# ── import core FIRST (house rule), assert it is the worktree's, then redirect every store ─────────────────────
import core                                                     # noqa: E402
assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), f"core imported from {core.__file__}, not {ROOT}"
from core import profile                                        # noqa: E402
from core import life                                           # noqa: E402
from core import world_traces as WT                             # noqa: E402
from core import sensorium as S                                 # noqa: E402
from core import locomotion as L                                # noqa: E402
from core import sound_knowledge as SK                          # noqa: E402
from core import soundscape as SC                               # noqa: E402
from core import cat as CAT                                     # noqa: E402
from core import wood_life as WL                                # noqa: E402

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
SC._DATA, SC._SND_STATE_F, SC._FELT_SHADOW_F = TMP, TMP / "soundscape_state.json", TMP / "soundscape_felt_shadow.jsonl"
CAT._STATE_F = TMP / "cat_state.json"
WL._F = TMP / "wood_state.json"
assert not profile.LIVE, "this test must never run as the live process"

# an in-memory room: soundscape reads room_state/cat_state through _read_json -- no disk, no live file
ROOM: dict = {"location": "study", "weather": "clear", "wind": "breeze", "fire": "out", "study": {}}
CATST: dict = {"phase": "kept", "mood": "content", "activity": "sleeping", "location": "gone"}
SC._read_json = lambda name: dict(ROOM) if name == "room_state.json" else (dict(CATST) if name == "cat_state.json" else {})
S.state = {"weather": "clear", "wind": "breeze", "frost_last": False}
life.RENDER = False
life.SOUND_GATING = True            # the live flag state since 2026-09-09 (data/life_flags.json gating=true)


def set_stream(level: float) -> None:
    WL._F.write_text(json.dumps({"stream": level}), encoding="utf-8")


set_stream(0.5)

FAILS: list[str] = []
N = 0


def check(cond, msg):
    global N
    N += 1
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def at(month: int, day: int, hour: int, minute: int = 0) -> float:
    return time.mktime((2026, month, day, hour, minute, 0, 0, 0, -1))


_real_time = time.time


def freeze(t: float):
    time.time = lambda: t


def thaw():
    time.time = _real_time


NEW = ("hail_on_roof", "hail_on_leaves", "drizzle_hiss", "downpour_drum", "rain_down_chimney",
       "tin_roof_tick", "stream_over_stones", "undertow_rumble", "frost_crack", "calm_sea_hush")
KNOWN = ("hail_on_roof", "hail_on_leaves", "drizzle_hiss", "downpour_drum", "rain_down_chimney",
         "stream_over_stones", "undertow_rumble", "calm_sea_hush")
UNNAMED = ("tin_roof_tick", "frost_crack")
BEDS = ("hail_on_roof", "hail_on_leaves", "drizzle_hiss", "downpour_drum", "stream_over_stones", "undertow_rumble", "calm_sea_hush")
EVENTS = ("rain_down_chimney", "tin_roof_tick", "frost_crack")
life._ensure_builtin()

# ═══ [1] registry ════════════════════════════════════════════════════════════════════════════════════════════════
print("[1] registry")
for k in NEW:
    e = SC._SOUNDS.get(k)
    check(bool(e) and set(e["coords"]) == set(SC._AXES) and all(0.0 <= v <= 1.0 for v in e["coords"].values()), f"{k}: a six-axis point in [0,1]")
check(SC._SOUNDS["drizzle_hiss"]["object"] == "the rain" == SC._SOUNDS["downpour_drum"]["object"] == SC._SOUNDS["rain_on_roof"]["object"],
      "the rain grades are spokes of the SAME object as rain_on_roof")
check(SC._SOUNDS["stream_over_stones"]["object"] == "the stream" == SC._SOUNDS["stream_run"]["object"], "stream_over_stones is the stream's second spoke")
check(SC._SOUNDS["undertow_rumble"]["object"] == "the sea" == SC._SOUNDS["calm_sea_hush"]["object"], "undertow and the hush are the sea's")
check(SC._SOUNDS["rain_down_chimney"]["object"] == "the fire" and SC._SOUNDS["hail_on_roof"]["object"] == "the hail" == SC._SOUNDS["hail_on_leaves"]["object"]
      and SC._SOUNDS["tin_roof_tick"]["object"] == "the roof" and SC._SOUNDS["frost_crack"]["object"] == "the frost", "chimney / hail / roof / frost objects")
dz, rr, dp = SC._SOUNDS["drizzle_hiss"]["coords"]["energy"], SC._SOUNDS["rain_on_roof"]["coords"]["energy"], SC._SOUNDS["downpour_drum"]["coords"]["energy"]
check(dz < rr < dp, f"the grades order by energy either side of rain_on_roof ({dz} < {rr} < {dp})")
check(SC._SOUNDS["calm_sea_hush"]["coords"]["energy"] <= 0.05 and SC._SOUNDS["calm_sea_hush"]["coords"]["continuity"] >= 0.95, "calm_sea_hush is near-silence: lowest energy, fully continuous")
check(set(SC._EVENT_RATES) <= set(SC._SOUNDS), "set(_EVENT_RATES) <= set(_SOUNDS) still holds")
check(all(SC._EVENT_RATES.get(k) == 0.0 for k in BEDS) and all(k not in SC._BEDS for k in NEW), "the seven beds carry rate 0.0 (the trickle convention); _BEDS itself untouched")
check(all(0 < SC._EVENT_RATES[k] for k in EVENTS) and SC._EVENT_RATES["frost_crack"] <= 0.5 and SC._EVENT_RATES["tin_roof_tick"] <= 12.0, "the three events rated; the frost's report rare")
_RIDX = list(SC._EVENT_RATES).index("hail_on_roof")      # J-2477+: later sections append their rates after these ten
check(list(SC._EVENT_RATES)[_RIDX:_RIDX + 10] == ["hail_on_roof", "hail_on_leaves", "drizzle_hiss", "downpour_drum", "stream_over_stones", "undertow_rumble", "calm_sea_hush",
                                                  "rain_down_chimney", "tin_roof_tick", "frost_crack"]
      and list(SC._EVENT_RATES)[_RIDX - 1] == "dolphin_blow", "the ten rates sit together directly after the §2 rates (later sections append after)")
check(all(k in SK.GRANDFATHERED and k not in SK.AUDITION for k in KNOWN), "the eight known keys are grandfathered and have no AUDITION entry")
check(all(k in SK.AUDITION and k not in SK.GRANDFATHERED for k in UNNAMED), "tin_roof_tick / frost_crack have AUDITION entries and are not grandfathered")
check(all(SK.is_learned(k) for k in KNOWN) and not any(SK.is_learned(k) for k in UNNAMED), "with an empty ledger: the known render named, the two mysteries do not")
for k in UNNAMED:
    pools = SK.AUDITION[k]["unknown"]
    check(all(isinstance(p, (tuple, list)) and len(p) >= 4 for p in pools.values()), f"{k}: unnamed pool(s) of >= 4 lines per place {sorted(pools)}")
check(set(SK.AUDITION["tin_roof_tick"]["unknown"]) == {"study", "garden"} and set(SK.AUDITION["frost_crack"]["unknown"]) == {"study", "garden", "wood"},
      "unnamed pools exist for every place each mystery can sound at")
for k in NEW:
    check(len(SC._PERCEPT_LINES[k]["onset"]) >= 4 and len(SC._PERCEPT_LINES[k]["renotice"]) >= 2, f"{k}: named onset pool >= 4, renotice >= 2")
tick_lines = [ln for pool in SK.AUDITION["tin_roof_tick"]["unknown"].values() for ln in pool]
check(all(not any(w in ln.lower() for w in ("roof", "iron", "tin", "sun", "heat", "warm", "corrugated")) for ln in tick_lines), "tin_roof_tick unnamed lines never name the cause")
crack_lines = [ln for pool in SK.AUDITION["frost_crack"]["unknown"].values() for ln in pool]
check(all(not any(w in ln.lower() for w in ("frost", "ice", "freez", "cold")) for ln in crack_lines), "frost_crack unnamed lines never name the cause")
check(all("sound you don't know" in ln for ln in tick_lines + crack_lines), "every unnamed line is framed as a sound he does not know")
check(SK.AUDITION["frost_crack"]["sight_prob"] == 0.0 and SK.AUDITION["frost_crack"]["reveal"] == "" and SK.AUDITION["frost_crack"]["day_only"] is False,
      "frost_crack can never be sight-bound (a report, over before it can be looked at); binds by night")
check(0 < SK.AUDITION["tin_roof_tick"]["sight_prob"] <= 0.25 and SK.AUDITION["tin_roof_tick"]["day_only"] is True and SK.AUDITION["tin_roof_tick"]["reveal"],
      "tin_roof_tick: low-odds sight-binding by looking up, by day only -- a slow mystery")
all_new_lines = [ln for k in UNNAMED for pool in SK.AUDITION[k]["unknown"].values() for ln in pool]
all_new_lines += [ln for k in NEW for kind in ("onset", "renotice") for ln in SC._PERCEPT_LINES[k][kind]]
all_new_lines += [SK.AUDITION[k]["reveal"] + SK.AUDITION[k]["miss"] for k in UNNAMED]
check(all(not any(ch.isdigit() for ch in ln) and not any(w in ln.lower() for w in ("gauge", "score", "level", "percent", "probability", "count", "band", "verdict"))
          for ln in all_new_lines), f"no digit / readout word in any of the {len(all_new_lines)} new lines (D-0434)")
_NEARFAR = ("close", "near", "far", "distant", "overhead", "a long way", "right at", "beyond", "above you", "at your feet", "a little way off",
            "beside you", "below you", "in front of you", "at hand", "over your head")
heard_lines = [ln for k in UNNAMED for pool in SK.AUDITION[k]["unknown"].values() for ln in pool]
heard_lines += [ln for k in NEW for kind in ("onset", "renotice") for ln in SC._PERCEPT_LINES[k][kind]]
check(all(any(w in ln.lower() for w in _NEARFAR) for ln in heard_lines), f"every one of the {len(heard_lines)} lines he can hear carries a near/far word")
for k in NEW:
    seq = [SC._pick(SC._PERCEPT_LINES[k]["onset"], f"t_{k}") for _ in range(40)]
    check(len(set(seq)) >= 3 and all(a != b for a, b in zip(seq, seq[1:])), f"{k}: onset pool rotates ({len(set(seq))} distinct, never twice running)")
check(SC._PERCEPT_SOUNDS[:18] == ("cat_purr", "morepork_call", "tui_song", "cat_trill", "cat_meow_at_door", "cat_demand", "cat_chatter",
                                   "cat_yowl_cargo", "cat_thump", "cat_lapping", "cat_storm_rustle", "cat_hiss", "cat_growl",
                                   "possum_rasp", "wall_scratch", "distant_yowl", "hedgehog_snuffle", "dolphin_blow")
      and set(SC._PERCEPT_SOUNDS[18:28]) == set(NEW) and len(SC._PERCEPT_SOUNDS) >= 28,
      "the rail's try-order: the eighteen existing keys first (cat_hiss/cat_growl merged in from cat_overhaul B3), the ten geophony keys directly after them (J-2477+: later sections append after)")
check(SC._GEOPHONY_PERCEPT_KEYS == frozenset(NEW) and SC._GEOPHONY_UNNAMED_KEYS == frozenset(UNNAMED) and SC._GEOPHONY_PERCEPT_COOLDOWN_S >= 6 * 3600,
      "per-key floor set covers the ten; the unnamed pair routed through audition; floor >= 6 h (<= 4 a day, D-0500's defeater)")
check(not (set(NEW) & SC._STORM_DRIVEN_EVENTS), "no geophony key is in _STORM_DRIVEN_EVENTS (the severity curve scales nothing here)")

# ═══ [2] the clocks ═════════════════════════════════════════════════════════════════════════════════════════════
print("[2] clocks")
check(SC._season_at(at(7, 10, 12)) == "winter" and SC._season_at(at(1, 10, 12)) == "summer" and SC._season_at(at(4, 10, 12)) == "autumn" and SC._season_at(at(10, 10, 12)) == "spring",
      "_season_at reads the calendar of the given moment")
jul = at(7, 1, 0)
samples = [(h, m) for h in range(24 * 31) for m in range(0, 60)]
hail_wr = [SC._hail_burst(jul + h * 3600 + m * 60, "wind and rain") for h, m in samples]
frac = sum(hail_wr) / len(hail_wr)
check(0.003 <= frac <= 0.06, f"July storm-hours: hail falls a small fraction of the time ({frac:.4f})")
hours_with = {h for (h, m), v in zip(samples, hail_wr) if v}
check(3 <= len(hours_with) <= 300, f"...spread over some storm-hours, not all ({len(hours_with)}/{24 * 31})")
for h in sorted(hours_with)[:5]:
    mins = [m for m in range(60) if SC._hail_burst(jul + h * 3600 + m * 60, "wind and rain")]
    check(4 <= len(mins) <= 9 and mins == list(range(mins[0], mins[0] + len(mins))), f"hour {h}: one contiguous squall of {len(mins)} min")
check(not any(SC._hail_burst(jul + h * 3600 + m * 60, w) for h, m in samples[:24 * 60] for w in ("clear", "drizzle", "steady rain", "overcast", "snow")),
      "no hail outside the storm end of the ladder (sev >= 5)")
check(any(SC._hail_burst(jul + h * 3600 + m * 60, "thunderstorm") for h, m in samples), "a thunderstorm can carry hail too")
check(not any(SC._hail_burst(at(1, 1, 0) + h * 3600 + m * 60, "wind and rain") for h, m in samples), "January: never hail (summer share 0)")
frac_apr = sum(SC._hail_burst(at(4, 1, 0) + h * 3600 + m * 60, "wind and rain") for h, m in samples) / len(samples)
check(0 < frac_apr < frac, f"April: rarer than July ({frac_apr:.4f} < {frac:.4f})")
check(SC._hail_burst(jul + 5 * 3600, "wind and rain") == SC._hail_burst(jul + 5 * 3600, "wind and rain"), "deterministic: two reads of one moment agree")
# the roof's window: after sunrise and around sunset, from world_clock's sun table (July: rise 7.6, set 17.2)
check(SC._roof_flex_window(at(7, 10, 9, 0)) and SC._roof_flex_window(at(7, 10, 10, 0)) and not SC._roof_flex_window(at(7, 10, 12, 0))
      and not SC._roof_flex_window(at(7, 10, 7, 30)) and SC._roof_flex_window(at(7, 10, 16, 30)) and not SC._roof_flex_window(at(7, 10, 19, 0))
      and not SC._roof_flex_window(at(7, 10, 2, 0)), "July: the roof ticks mid-morning and around sunset, not at noon, dawn or night")
check(SC._roof_flex_window(at(1, 10, 7, 30)) and not SC._roof_flex_window(at(1, 10, 9, 30)) and SC._roof_flex_window(at(1, 10, 20, 0)),
      "January: the windows move with the summer sun (rise ~six, set after eight)")
# the stream mouth: constant except late summer at the floor
set_stream(0.2)
check(SC._stream_mouth_running(at(7, 10, 12)) and not SC._stream_mouth_running(at(1, 10, 12)), "stream level at the floor: runs in July, dry in January")
set_stream(0.5)
check(SC._stream_mouth_running(at(1, 10, 12)), "after rain the January stream makes the sea again")
WL._F.unlink()
check(SC._stream_mouth_running(at(1, 10, 12)), "no wood store: fail-open to running (the plan's 'constant')")
set_stream(0.5)

# ═══ [3] propagation through the REAL active_sounds() ═══════════════════════════════════════════════════════════
print("[3] propagation")
try:
    def active_at(loc: str, t: float, weather: str = "clear", wind: str = "breeze", fire: str = "out", table=None) -> list[str]:
        ROOM.update(location=loc, weather=weather, wind=wind, fire=fire)
        S.state.update(weather=weather, wind=wind)
        freeze(t)
        try:
            if table is None:
                return SC.active_sounds()
            saved = SC._PROPAGATION_TABLE[:]
            SC._PROPAGATION_TABLE[:] = table
            try:
                return SC.active_sounds()
            finally:
                SC._PROPAGATION_TABLE[:] = saved
        finally:
            thaw()

    # J-2477+: later sections (§4 seasonal biophony, ...) append their own rows AFTER this one, so the invariant is "directly
    # after the §2 row, nothing of the pre-§3 table moved" -- the suffix checks below truncate the table at the §3 row.
    _IDX3 = [f for _, f in SC._PROPAGATION_TABLE].index(SC._sec_geophony)
    check(SC._PROPAGATION_TABLE[_IDX3 - 1][1] is SC._sec_night_mysteries and all(f is not SC._sec_night_mysteries for _, f in SC._PROPAGATION_TABLE[_IDX3:]),
          "the §3 row sits directly after the §2 row (later sections append after it)")
    noon = at(7, 10, 13)          # a July afternoon (no roof window, daylight)
    # the rain grades, study: either side of rain_on_roof on the ladder; rain_on_roof itself untouched
    a = active_at("study", noon, "drizzle")
    check("drizzle_hiss" in a and "rain_on_roof" in a and "downpour_drum" not in a, "drizzle: drizzle_hiss ADDED beside rain_on_roof, no downpour")
    a = active_at("study", noon, "steady rain")
    check("rain_on_roof" in a and "drizzle_hiss" not in a and "downpour_drum" not in a, "steady rain: rain_on_roof alone -- its own middle grade")
    a = active_at("study", noon, "wind and rain")
    check("downpour_drum" in a and "rain_on_roof" in a and "drizzle_hiss" not in a, "wind and rain: downpour_drum beside rain_on_roof")
    a = active_at("study", noon, "thunderstorm")
    check("downpour_drum" in a and "rain_on_roof" in a and "thunder" in a, "thunderstorm: downpour_drum, rain_on_roof and thunder together")
    check(not any(k in active_at("study", noon, w) for w in ("clear", "high cloud", "overcast", "snow") for k in ("drizzle_hiss", "downpour_drum", "rain_down_chimney")),
          "dry (and snow): no rain grade, no chimney")
    # D-0063's defeater: the grade and the severity curve never disagree
    agree = all((("downpour_drum" in active_at("study", noon, w)) == (SC._storm_severity_scale(w) > 1.0))
                and (("drizzle_hiss" in active_at("study", noon, w)) <= (SC._storm_severity_scale(w) == 1.0)) for w in S._WEATHERS)
    check(agree, "every ladder step: downpour_drum iff the severity curve ramps; drizzle_hiss only where it is flat")
    # the chimney: fire + rain co-state, study only
    check("rain_down_chimney" in active_at("study", noon, "steady rain", fire="burning") and "rain_down_chimney" in active_at("study", noon, "drizzle", fire="embers")
          and "rain_down_chimney" not in active_at("study", noon, "steady rain", fire="out") and "rain_down_chimney" not in active_at("study", noon, "clear", fire="burning"),
          "rain_down_chimney: fire (burning or embers) AND rain, never one without the other")
    check(not any(k in active_at(p, noon, "wind and rain", fire="burning") for p in ("garden", "wood", "shore") for k in ("drizzle_hiss", "downpour_drum", "rain_down_chimney")),
          "the roof and the chimney are the study's: no grade outdoors")
    # hail by place
    hail_t = next(jul + h * 3600 + m * 60 for h in range(0, 24 * 31) for m in range(60)
                  if SC._hail_burst(jul + h * 3600 + m * 60, "wind and rain") and 9 <= time.localtime(jul + h * 3600 + m * 60).tm_hour <= 15)
    check("hail_on_roof" in active_at("study", hail_t, "wind and rain") and "hail_on_leaves" not in active_at("study", hail_t, "wind and rain"), "hail in the study: on the roof")
    check(all("hail_on_leaves" in active_at(p, hail_t, "wind and rain") and "hail_on_roof" not in active_at(p, hail_t, "wind and rain") for p in ("garden", "wood")),
          "hail in the garden / the wood: on the leaves")
    check(not any(k in active_at("shore", hail_t, "wind and rain") for k in ("hail_on_roof", "hail_on_leaves")), "the shore registers no hail voice (the weather he stands in)")
    check(not any(k in active_at("study", hail_t, "steady rain") for k in ("hail_on_roof", "hail_on_leaves")), "same minute, steady rain: no hail")
    # the roof's tick: clear sky, the window, study + garden
    m9, m12 = at(7, 10, 9, 15), at(7, 10, 12, 0)
    check("tin_roof_tick" in active_at("study", m9) and "tin_roof_tick" in active_at("garden", m9) and "tin_roof_tick" not in active_at("wood", m9)
          and "tin_roof_tick" not in active_at("shore", m9), "a clear July morning: the roof ticks in the study and the garden only")
    check(not any("tin_roof_tick" in active_at("study", m9, w) for w in ("high cloud", "overcast", "drizzle")) and "tin_roof_tick" not in active_at("study", m12),
          "...not under cloud, not at noon")
    check("tin_roof_tick" in active_at("study", at(7, 10, 16, 30)), "...and again as the iron cools toward sunset")
    # the shore's three states
    set_stream(0.5)
    a = active_at("shore", noon, "clear", "gale")
    check("undertow_rumble" in a and "waves_crashing" in a and "calm_sea_hush" not in a, "a gale: the sea crashes and the undertow rumbles; no hush")
    a = active_at("shore", noon, "thunderstorm", "breeze")
    check("undertow_rumble" in a and "calm_sea_hush" not in a, "a storm sea (weather-raised): undertow, no hush")
    a = active_at("shore", noon, "clear", "calm")
    check("calm_sea_hush" in a and "undertow_rumble" not in a and "waves_on_shingle" in a, "calm wind, gentle sea: the hush, beside the gentle waves")
    a = active_at("shore", noon, "clear", "breeze")
    check("calm_sea_hush" not in a and "undertow_rumble" not in a, "a breeze: neither hush nor undertow")
    check("stream_over_stones" in active_at("shore", noon) and "stream_over_stones" in active_at("shore", at(7, 10, 23)), "the stream mouth runs at the shore, day and night (July)")
    set_stream(0.2)
    check("stream_over_stones" not in active_at("shore", at(1, 10, 13)) and "stream_over_stones" in active_at("shore", at(7, 10, 13)), "at the floor: dry in January, running in July")
    set_stream(0.5)
    check("stream_over_stones" in active_at("shore", at(1, 10, 13)), "January after rain: running again")
    check(not any("stream_over_stones" in active_at(p, noon) for p in ("study", "garden", "wood")), "stream_over_stones is the shore's only (stream_run is the wood's)")
    # the garden's night hush
    night = at(7, 10, 23)
    check("calm_sea_hush" in active_at("garden", night, "clear", "calm") and "calm_sea_hush" not in active_at("garden", night, "clear", "breeze")
          and "calm_sea_hush" not in active_at("garden", night, "drizzle", "calm") and "calm_sea_hush" not in active_at("garden", noon, "clear", "calm"),
          "garden: the hush on a calm, dry night only")
    # the frost's report
    for p in ("study", "garden", "wood"):
        check("frost_crack" in active_at(p, night, "clear", "calm") and "frost_crack" in active_at(p, night, "clear", "breeze"), f"{p}: a clear still July night cracks with frost")
    check("frost_crack" not in active_at("shore", night, "clear", "calm"), "the shore never (no timber, the sea's own noise)")
    check(not any("frost_crack" in active_at("study", night, w, "calm") for w in ("high cloud", "overcast", "drizzle", "snow")), "cloud keeps the frost off: no crack")
    check(not any("frost_crack" in active_at("study", night, "clear", w) for w in ("fresh wind", "strong wind", "gale")), "wind keeps the frost off: no crack")
    check("frost_crack" not in active_at("study", noon, "clear", "calm"), "never by day")
    check(not any("frost_crack" in active_at("study", at(mo, 10, 23), "clear", "calm") for mo in (1, 4, 10, 11)), "never outside winter (sensorium's own frost clock)")
    # row LAST: pure suffix with gating OFF; with gating ON every pre-existing key keeps its relative order
    without = SC._PROPAGATION_TABLE[:_IDX3]
    with3 = SC._PROPAGATION_TABLE[:_IDX3 + 1]          # J-2477+: the table up to and including the §3 row (later rows excluded)
    moments = ((("study", noon, "drizzle", "breeze", "burning"), ("study", night, "clear", "calm", "out"), ("shore", noon, "clear", "calm", "out"),
                ("shore", noon, "clear", "gale", "out"), ("garden", night, "clear", "calm", "out"), ("study", hail_t, "wind and rain", "breeze", "out"),
                ("study", m9, "clear", "breeze", "out"), ("wood", hail_t, "wind and rain", "breeze", "out")))
    ok_order = all([k for k in active_at(*m, table=with3) if k not in NEW] == [k for k in active_at(*m, table=without) if k not in NEW] for m in moments)
    check(ok_order, "gating ON: every pre-existing key present, in its old relative order; only the new keys are added")
    life.SOUND_GATING = False
    try:
        ok_suffix = all(active_at(*m, table=with3)[:len(active_at(*m, table=without))] == active_at(*m, table=without)
                        and all(k in NEW for k in active_at(*m, table=with3)[len(active_at(*m, table=without)):]) and len(active_at(*m, table=with3)) > len(active_at(*m, table=without))
                        for m in moments)
        check(ok_suffix, "gating OFF: the row is a pure, non-empty suffix at every moment -- nothing ahead of it moves (out[:4] discipline)")
    finally:
        life.SOUND_GATING = True
    check(not (set(NEW) & life.creature_sound_keys(None)), "no geophony key is creature-governed (the gate leaves all ten to the row)")
finally:
    thaw()

# ═══ [4] the percept rail ═══════════════════════════════════════════════════════════════════════════════════════
print("[4] percept rail")
_REAL_ACTIVE_SOUNDS = SC.active_sounds
try:
    pt = at(7, 10, 9, 15)
    ROOM.update(location="study", weather="clear", wind="breeze", fire="out")
    S.state.update(weather="clear", wind="breeze")
    SC.SOUND_PERCEPTS = True
    SC.active_sounds = lambda: ["tin_roof_tick"]
    freeze(pt)
    SC._save_snd_state({"was_active": [], "quiet_since": {"tin_roof_tick": pt - 700}, "last_notice": {}, "last_percept": 0.0})
    line = SC.percept(store=False)
    pools = SK.AUDITION["tin_roof_tick"]["unknown"]["study"]
    check(bool(line) and line in pools, "an onset reaches him as the UNNAMED study rendering (a tick from overhead, never 'roof')")
    check(bool(line) and "roof" not in line.lower() and ("overhead" in line.lower() or "above" in line.lower() or "ceiling" in line.lower()), "...direction + near word, no cause named")
    led = SK._load()
    check(any(r.get("key") == "tin_roof_tick" and r.get("loc") == "study" for r in led.get("recent", [])), "the hearing is noted in the ledger's recent list (a look within 15 min can bind)")
    st = SC._snd_state()
    check(st.get("last_geophony_percept", {}).get("tin_roof_tick") == pt and st.get("last_percept") == pt, "state: last_geophony_percept + last_percept stamped")
    check(SC.percept(store=False) is None, "an immediate second call: nothing (the rail's shared cooldown)")
    t2 = pt + 3000
    freeze(t2)
    SC._save_snd_state({"was_active": [], "quiet_since": {"tin_roof_tick": t2 - 700}, "last_notice": {}, "last_percept": pt, "last_geophony_percept": {"tin_roof_tick": pt}})
    check(SC.percept(store=False) is None, "50 min later, a fresh onset: refused by the 8 h per-key floor")
    t3 = pt + SC._GEOPHONY_PERCEPT_COOLDOWN_S + 60
    freeze(t3)
    SC._save_snd_state({"was_active": [], "quiet_since": {"tin_roof_tick": t3 - 700}, "last_notice": {}, "last_percept": pt, "last_geophony_percept": {"tin_roof_tick": pt}})
    line2 = SC.percept(store=False)
    check(bool(line2) and line2 in pools, "past the floor: it fires again, still unnamed")
    t4 = t3 + SC._RENOTICE_S + 60
    freeze(t4)
    SC._save_snd_state({"was_active": ["tin_roof_tick"], "quiet_since": {}, "last_notice": {"tin_roof_tick": t3}, "last_percept": t3, "last_geophony_percept": {"tin_roof_tick": t3}})
    check(SC.percept(store=False) is None, "4 h on: a renotice is refused while the 8 h floor holds")
    t5 = t3 + SC._GEOPHONY_PERCEPT_COOLDOWN_S + 60
    freeze(t5)
    SC._save_snd_state({"was_active": ["tin_roof_tick"], "quiet_since": {}, "last_notice": {"tin_roof_tick": t3}, "last_percept": t3, "last_geophony_percept": {"tin_roof_tick": t3}})
    line3 = SC.percept(store=False)
    check(bool(line3) and line3 in pools, "8 h on: the renotice fires, still unnamed (same study pool)")
    seq = [SK._unknown_line(SK.AUDITION["tin_roof_tick"], "tin_roof_tick", "garden") for _ in range(40)]
    check(len(set(seq)) >= 3 and all(a != b for a, b in zip(seq, seq[1:])), f"the garden's unnamed pool rotates ({len(set(seq))} distinct, never twice running)")
    # the frost's report in the garden: unnamed garden pool
    ROOM.update(location="garden")
    SC.active_sounds = lambda: ["frost_crack"]
    ft = at(7, 10, 23)
    freeze(ft)
    SC._save_snd_state({"was_active": [], "quiet_since": {"frost_crack": ft - 700}, "last_notice": {}, "last_percept": 0.0})
    fl = SC.percept(store=False)
    check(bool(fl) and fl in SK.AUDITION["frost_crack"]["unknown"]["garden"] and "frost" not in fl.lower(), "frost_crack in the garden: the unnamed garden pool, a crack in the dark, no cause")
    # a known key renders NAMED straight from its pool (grandfathered), and takes the same floor
    ROOM.update(location="study", weather="wind and rain")
    SC.active_sounds = lambda: ["hail_on_roof", "rain_on_roof"]
    ht = at(7, 12, 14)
    freeze(ht)
    SC._save_snd_state({"was_active": ["rain_on_roof"], "quiet_since": {"hail_on_roof": ht - 700}, "last_notice": {}, "last_percept": 0.0})
    hl = SC.percept(store=False)
    check(bool(hl) and hl in SC._PERCEPT_LINES["hail_on_roof"]["onset"] and "hail" in hl.lower(), "hail_on_roof: known -- the named onset pool directly")
    check(SC._snd_state().get("last_geophony_percept", {}).get("hail_on_roof") == ht, "...and its own per-key floor stamped")
    # the hush as a percept: silence noticed as a state
    ROOM.update(location="shore", weather="clear", wind="calm")
    SC.active_sounds = lambda: ["waves_on_shingle", "calm_sea_hush"]
    st_ = at(7, 12, 22)
    freeze(st_)
    SC._save_snd_state({"was_active": [], "quiet_since": {"calm_sea_hush": st_ - 700}, "last_notice": {}, "last_percept": 0.0})
    hush = SC.percept(store=False)
    check(bool(hush) and hush in SC._PERCEPT_LINES["calm_sea_hush"]["onset"] and any(w in hush.lower() for w in ("quiet", "hush", "calm", "still")),
          "calm_sea_hush reaches him as noticed quiet -- a state, not an absence")
    # once the name is earned: the NAMED pool
    led = SK._load(); SK._add_event(led, "tin_roof_tick", "sighted", 1.0, "test"); SK._save(led)
    check(SK.is_learned("tin_roof_tick"), "after a sighting the tick is learned")
    ROOM.update(location="study", weather="clear", wind="breeze")
    SC.active_sounds = lambda: ["tin_roof_tick"]
    freeze(pt)
    SC._save_snd_state({"was_active": [], "quiet_since": {"tin_roof_tick": pt - 700}, "last_notice": {}, "last_percept": 0.0})
    named = SC.percept(store=False)
    check(bool(named) and named in SC._PERCEPT_LINES["tin_roof_tick"]["onset"] and "roof" in named.lower(), "learned: the onset renders NAMED from its own pool")
    # first refusal: morepork / a mystery ahead of a geophony key onsetting at the same moment
    ROOM.update(location="garden")
    SC.active_sounds = lambda: ["morepork_call", "frost_crack", "calm_sea_hush"]
    freeze(ft)
    SC._save_snd_state({"was_active": [], "quiet_since": {"morepork_call": ft - 700, "frost_crack": ft - 700, "calm_sea_hush": ft - 700}, "last_notice": {}, "last_percept": 0.0})
    mp = SC.percept(store=False)
    check(bool(mp) and mp in SC._PERCEPT_LINES["morepork_call"]["onset"], "the morepork keeps first refusal over geophony onsetting at the same moment")
finally:
    thaw()
    SC.active_sounds = _REAL_ACTIVE_SOUNDS
check(SC.active_sounds is _REAL_ACTIVE_SOUNDS and SC.active_sounds.__module__ == "core.soundscape", "real active_sounds restored")

# ═══ [5] earning the name ═══════════════════════════════════════════════════════════════════════════════════════
print("[5] earning the name")
SK._save({"sounds": {}, "recent": []})
_real_random = random.random
try:
    now = at(7, 10, 9, 20)
    freeze(now)
    led = SK._load(); led["recent"] = [{"key": "tin_roof_tick", "ts": now - 60, "loc": "study"}]; SK._save(led)
    random.random = lambda: 0.0           # the roll succeeds
    check(SK.look_binding("the ceiling", "study", is_day=False) == "" and not SK.is_learned("tin_roof_tick"), "a look up at night cannot bind the tick (day_only)")
    out = SK.look_binding("the ceiling", "study", is_day=True)
    check(out.startswith(SK.AUDITION["tin_roof_tick"]["reveal"]) and SK.is_learned("tin_roof_tick"), "a day look up at the ceiling binds the tick to the roof (reveal + learned)")
    led = SK._load(); led["recent"] = [{"key": "frost_crack", "ts": now - 60, "loc": "study"}]; SK._save(led)
    out = SK.look_binding("the wall by the window", "study", is_day=False)
    check(out == SK.AUDITION["frost_crack"]["miss"] and not SK.is_learned("frost_crack") and 0 < SK._weight(SK._load(), "frost_crack") < 1.0,
          "a look at the wall: the honest miss, a little exposure weight, never a reveal (sight_prob 0)")
    random.random = _real_random
    check(SK.learn_from_text("a hard frost is settling in tonight, clear and still and bitterly cold; it will silver the grass by dawn and cut back the tender things") == []
          and not SK.is_learned("frost_crack"), "sensorium's own frost milestone line (no sound-word) does not teach the crack")
    learned = SK.learn_from_text("On the hardest nights the frost gets into the timber and the whole house cracks like a gun.")
    check("frost_crack" in learned and SK.is_learned("frost_crack"), "a book that ties frost to cracking timber teaches it")
finally:
    random.random = _real_random
    thaw()

# ═══ [6] the hearing ledger ═════════════════════════════════════════════════════════════════════════════════════
print("[6] hearing ledger")
SK._save({"sounds": {}, "recent": []})
_real_active = SC.active_sounds
try:
    ROOM.update(location="study", weather="drizzle", wind="breeze", fire="burning")
    SC.active_sounds = lambda: ["drizzle_hiss", "rain_down_chimney", "frost_crack"]
    for _ in range(60):
        SC.world_tick("study", 300.0)            # 5 h: the hiss banks hours; the chimney ~60 spits at 12/h; the frost ~1 report at 0.25/h
    h = SK._load().get("hearings", {})
    hrs = float((h.get("drizzle_hiss") or {}).get("bed_hours", 0.0))
    n_c, n_f = int((h.get("rain_down_chimney") or {}).get("count", 0)), int((h.get("frost_crack") or {}).get("count", 0))
    check(abs(hrs - 5.0) < 0.01 and not (h.get("drizzle_hiss") or {}).get("count"), f"drizzle_hiss banks lived-in hours, never counts ({hrs:.3f} h)")
    check(30 <= n_c <= 100, f"rain_down_chimney banks spits at its rate ({n_c} in 5 h, expected ~60)")
    check(0 <= n_f <= 6 and n_f < n_c, f"frost_crack is rare ({n_f} in 5 h, expected ~1)")
    check((h.get("rain_down_chimney") or {}).get("places", {}).get("study") == n_c, "...keyed to his place")
finally:
    SC.active_sounds = _real_active

# ═══ [7] the sidecar dry-run's archetype invariant ═════════════════════════════════════════════════════════════
print("[7] sidecar archetypes")
import scripts.sound_strings_phase1_dryrun as DRY        # noqa: E402  (imports the same worktree core.soundscape; writes nothing until main())
strings = DRY.build_all()
check(set(NEW) <= set(strings), "every geophony key is classified (build_all's invariant holds)")
check(all(strings[k]["archetype"] == "bed_like" for k in BEDS) and all(strings[k]["archetype"] == "thump" for k in EVENTS), "beds are bed-like strings; the three events are strikes")

# ═══ [8] isolation ══════════════════════════════════════════════════════════════════════════════════════════════
print("[8] isolation")
_after = {p: _md5(p) for p in _LIVE_FILES}
check(LIVE_WRITE_ATTEMPTS == [], f"no write attempt under any data/ dir ({LIVE_WRITE_ATTEMPTS[:3]})")
changed = [p.name for p in _LIVE_FILES if _before[p] != _after[p]]
check(not changed, f"live files unchanged ({changed})")
for mod, attr in ((life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (SK, "_LEDGER_F"), (SC, "_SND_STATE_F"), (SC, "_FELT_SHADOW_F"), (S, "_STATE_F"), (CAT, "_STATE_F"), (WL, "_F")):
    check(str(getattr(mod, attr)).startswith(str(TMP)), f"{mod.__name__}.{attr} still inside TMP")

print(f"\n{N - len(FAILS)}/{N} checks passed" + (f" -- FAILS: {FAILS}" if FAILS else " -- ALL OK"))
sys.exit(1 if FAILS else 0)
