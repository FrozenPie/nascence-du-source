"""
J-2477 (sound_world_expansion §4, D-0500): THE SEASONAL BIOPHONY -- silvereye_flock (bound to the tauhou's life row),
paradise_duck_flyover (a sound-only event, no life row, a short look-up bind window), kelp_fly_buzz (a summer bed at the
wrack-line, known). bellbird_chime is NOT built (a duplicate of bellbird_song) and this test asserts it is absent.
Hermetic: every store the engine can reach is redirected into a temp dir before anything can write; a Python audit
hook records any write attempt under a live data/ dir; the live files are md5-hashed before and after. Run from the
worktree:  python scripts/_test_j2477_seasonal_biophony.py   (exit 0 = ALL OK)

  [1] registry: three Sound-Space points, rates at the END (the flyover an event, the flock an event, the flies a bed),
      GRANDFATHERED vs AUDITION split, named pools (>= 4 onset, >= 2 renotice, rotating), near/far words, no digit or
      readout word (D-0434), rail try-order, the flyover's short bind window, no bellbird_chime
  [2] the clocks: the flyover is a seeded per-day draw of minutes-long passes inside the sun table, most in autumn and
      spring, rare in summer; deterministic; the window is a tiny fraction of daylight
  [3] life binding: the tauhou row carries silvereye_flock; sounds_active voices it by day in winter at the garden only,
      never at night, never in a storm, rarely in summer; the flyover and the flies are not creature-governed
  [4] propagation through the REAL soundscape.active_sounds(): the flock at the garden with the row; the flyover at the
      garden and the shore inside its window only, grounded by storm or gale; the flies on dry still summer daylight at
      the shore only; row LAST (pure suffix); the legacy row agrees with life.sounds_active with gating off
  [5] the percept rail: the flock and the flyover reach him UNNAMED (features, never the cause), the flies named directly,
      the 8 h per-key floor, renotice, first refusal kept by the keys ahead, the named pool once the name is earned
  [6] earning the name: a day look at the hedge binds the flock; a look UP inside the pass binds the pair, the same look
      ten minutes on does not (bind_window_s) while an entry without one still binds at ten minutes; a book teaches both
  [7] the hearing ledger: the flock and the flyover bank counts, the flies bank hours, through world_tick
  [8] the sidecar dry-run's archetype invariant still holds with the three keys classified
  [9] isolation: no write attempt under any data/, live hashes unchanged
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

TMP = Path(tempfile.mkdtemp(prefix="j2477_biophony_"))
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
ROOM: dict = {"location": "garden", "weather": "clear", "wind": "breeze", "fire": "out", "study": {}}
CATST: dict = {"phase": "kept", "mood": "content", "activity": "sleeping", "location": "gone"}
SC._read_json = lambda name: dict(ROOM) if name == "room_state.json" else (dict(CATST) if name == "cat_state.json" else {})
S.state = {"weather": "clear", "wind": "breeze", "frost_last": False}
life.RENDER = False
life.SOUND_GATING = True            # the live flag state since 2026-09-09 (data/life_flags.json gating=true)
WL._F.write_text(json.dumps({"stream": 0.5}), encoding="utf-8")

FAILS: list[str] = []
N = 0


def check(cond, msg):
    global N
    N += 1
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def at(month: int, day: int, hour: int, minute: int = 0, second: int = 0) -> float:
    return time.mktime((2026, month, day, hour, minute, second, 0, 0, -1))


_real_time = time.time


def freeze(t: float):
    time.time = lambda: t


def thaw():
    time.time = _real_time


NEW = ("silvereye_flock", "paradise_duck_flyover", "kelp_fly_buzz")
UNNAMED = ("silvereye_flock", "paradise_duck_flyover")
KNOWN = ("kelp_fly_buzz",)
life._ensure_builtin()

# ═══ [1] registry ════════════════════════════════════════════════════════════════════════════════════════════════
print("[1] registry")
for k in NEW:
    e = SC._SOUNDS.get(k)
    check(bool(e) and set(e["coords"]) == set(SC._AXES) and all(0.0 <= v <= 1.0 for v in e["coords"].values()), f"{k}: a six-axis point in [0,1]")
check("bellbird_chime" not in SC._SOUNDS and "bellbird_chime" not in SC._EVENT_RATES and "bellbird_chime" not in SK.AUDITION and "bellbird_song" in SC._SOUNDS,
      "bellbird_chime NOT added (a duplicate of the existing bellbird_song)")
check(SC._SOUNDS["silvereye_flock"]["object"] == "the tauhou" and SC._SOUNDS["paradise_duck_flyover"]["object"] == "the paradise ducks"
      and SC._SOUNDS["kelp_fly_buzz"]["object"] == "the kelp", "objects: the tauhou / the paradise ducks / the kelp")
keys = list(SC._SOUNDS)
check(keys.index("penguin_bray") < keys.index("silvereye_flock") < keys.index("saw_rasp"), "the §4 block sits in the chain's block after penguin_bray (the anchor rule)")
check(SC._SOUNDS["silvereye_flock"]["coords"]["onset"] >= 0.7 and SC._SOUNDS["silvereye_flock"]["coords"]["energy"] <= 0.3, "the flock: many small events, soft")
check(SC._SOUNDS["kelp_fly_buzz"]["coords"]["continuity"] >= 0.8 and SC._SOUNDS["kelp_fly_buzz"]["coords"]["periodicity"] >= 0.6, "the flies: a continuous periodic drone")
check(SC._SOUNDS["paradise_duck_flyover"]["coords"]["roughness"] >= 0.6, "the flyover: a hoarse honk in it")
check(set(SC._EVENT_RATES) <= set(SC._SOUNDS), "set(_EVENT_RATES) <= set(_SOUNDS) still holds")
_rk = list(SC._EVENT_RATES)
check(_rk[_rk.index("frost_crack") + 1:_rk.index("frost_crack") + 4] == list(NEW), "the three rates come directly after the §3 rates (J-2478's §5 rates may follow; chain-tolerant)")
check(SC._EVENT_RATES["kelp_fly_buzz"] == 0.0 and "kelp_fly_buzz" not in SC._BEDS, "the flies are a bed by the trickle convention (rate 0.0); _BEDS itself untouched")
check(SC._EVENT_RATES["silvereye_flock"] > 0 and SC._EVENT_RATES["paradise_duck_flyover"] > 0, "the flock and the flyover are events (rated)")
check(all(k in SK.GRANDFATHERED and k not in SK.AUDITION for k in KNOWN), "kelp_fly_buzz is grandfathered and has no AUDITION entry")
check(all(k in SK.AUDITION and k not in SK.GRANDFATHERED for k in UNNAMED), "silvereye_flock / paradise_duck_flyover have AUDITION entries and are not grandfathered")
check(all(SK.is_learned(k) for k in KNOWN) and not any(SK.is_learned(k) for k in UNNAMED), "with an empty ledger: the flies render named, the two do not")
for k in UNNAMED:
    pools = SK.AUDITION[k]["unknown"]
    check(all(isinstance(p, (tuple, list)) and len(p) >= 4 for p in pools.values()), f"{k}: unnamed pool(s) of >= 4 lines per place {sorted(pools)}")
check(set(SK.AUDITION["silvereye_flock"]["unknown"]) == {"garden"} and set(SK.AUDITION["paradise_duck_flyover"]["unknown"]) == {"garden", "shore"},
      "unnamed pools exist for every place each can sound at (the flock: the garden; the flyover: the open sky of the garden and the shore)")
for k in NEW:
    check(len(SC._PERCEPT_LINES[k]["onset"]) >= 4 and len(SC._PERCEPT_LINES[k]["renotice"]) >= 2, f"{k}: named onset pool >= 4, renotice >= 2")
flock_lines = [ln for pool in SK.AUDITION["silvereye_flock"]["unknown"].values() for ln in pool]
check(all(not any(w in ln.lower() for w in ("tauhou", "silvereye", "waxeye", "eye-ring", "grey-green")) for ln in flock_lines), "silvereye_flock unnamed lines never name the cause")
fly_lines = [ln for pool in SK.AUDITION["paradise_duck_flyover"]["unknown"].values() for ln in pool]
check(all(not any(w in ln.lower() for w in ("duck", "goose", "geese", "paradise", "shelduck", "putangitangi")) for ln in fly_lines), "paradise_duck_flyover unnamed lines never name the cause")
check(all("sound you don't know" in ln for ln in flock_lines + fly_lines), "every unnamed line is framed as a sound he does not know")
check(SK.AUDITION["silvereye_flock"]["sight_prob"] >= 0.7 and SK.AUDITION["silvereye_flock"]["day_only"] is True and SK.AUDITION["silvereye_flock"]["reveal"],
      "the flock is EASILY sighted (they swarm visibly), by day")
check(0.3 <= SK.AUDITION["paradise_duck_flyover"]["sight_prob"] <= 0.7 and SK.AUDITION["paradise_duck_flyover"]["day_only"] is True and SK.AUDITION["paradise_duck_flyover"]["reveal"],
      "the flyover is sightable by looking up at the right moment, by day")
bw = SK.AUDITION["paradise_duck_flyover"].get("bind_window_s")
check(bw is not None and SC._FLYOVER_PASS_MIN[0] * 60 <= bw <= 6 * 60 < SK._RECENT_WINDOW_S, f"the flyover's bind window is short: {bw} s, about a pass, well under the module's 15 min")
check(all("bind_window_s" not in SK.AUDITION[k] for k in ("godwits_overhead", "cuckoo_call", "penguin_bray", "tin_roof_tick")), "older entries carry no bind window (the 15 min default, unchanged)")
all_new_lines = [ln for k in UNNAMED for pool in SK.AUDITION[k]["unknown"].values() for ln in pool]
all_new_lines += [ln for k in NEW for kind in ("onset", "renotice") for ln in SC._PERCEPT_LINES[k][kind]]
all_new_lines += [SK.AUDITION[k]["reveal"] + SK.AUDITION[k]["miss"] for k in UNNAMED]
check(all(not any(ch.isdigit() for ch in ln) and not any(w in ln.lower() for w in ("gauge", "score", "level", "percent", "probability", "count", "band", "verdict"))
          for ln in all_new_lines), f"no digit / readout word in any of the {len(all_new_lines)} new lines (D-0434)")
_NEARFAR = ("close", "near", "far", "distant", "overhead", "a long way", "right at", "beyond", "above you", "at your feet", "a little way off",
            "beside you", "below you", "in front of you", "at hand", "over your head", "high up", "high above", "far up", "a few steps off")
heard_lines = [ln for k in UNNAMED for pool in SK.AUDITION[k]["unknown"].values() for ln in pool]
heard_lines += [ln for k in NEW for kind in ("onset", "renotice") for ln in SC._PERCEPT_LINES[k][kind]]
check(all(any(w in ln.lower() for w in _NEARFAR) for ln in heard_lines), f"every one of the {len(heard_lines)} lines he can hear carries a near/far word")
for k in NEW:
    seq = [SC._pick(SC._PERCEPT_LINES[k]["onset"], f"t_{k}") for _ in range(40)]
    check(len(set(seq)) >= 3 and all(a != b for a, b in zip(seq, seq[1:])), f"{k}: onset pool rotates ({len(set(seq))} distinct, never twice running)")
for k, place in (("silvereye_flock", "garden"), ("paradise_duck_flyover", "shore")):
    seq = [SK._unknown_line(SK.AUDITION[k], k, place) for _ in range(40)]
    check(len(set(seq)) >= 3 and all(a != b for a, b in zip(seq, seq[1:])), f"{k}@{place}: unnamed pool rotates ({len(set(seq))} distinct, never twice running)")
check(SC._PERCEPT_SOUNDS[:28] == ("cat_purr", "morepork_call", "tui_song", "cat_trill", "cat_meow_at_door", "cat_demand", "cat_chatter",
                                   "cat_yowl_cargo", "cat_thump", "cat_lapping", "cat_storm_rustle", "cat_hiss", "cat_growl",
                                   "possum_rasp", "wall_scratch", "distant_yowl", "hedgehog_snuffle", "dolphin_blow",
                                   "hail_on_roof", "hail_on_leaves", "rain_down_chimney", "frost_crack", "tin_roof_tick",
                                   "downpour_drum", "drizzle_hiss", "undertow_rumble", "calm_sea_hush", "stream_over_stones")
      and SC._PERCEPT_SOUNDS[28:31] == NEW and all(k not in SC._PERCEPT_SOUNDS[:28] for k in NEW),
      "the rail's try-order: the twenty-eight existing keys first (cat_hiss/cat_growl merged in from cat_overhaul B3), then the three §4 keys (J-2478's §5 keys may follow; chain-tolerant)")
check(SC._BIOPHONY_PERCEPT_KEYS == frozenset(NEW) and SC._BIOPHONY_UNNAMED_KEYS == frozenset(UNNAMED) and SC._BIOPHONY_PERCEPT_COOLDOWN_S >= 6 * 3600,
      "per-key floor set covers the three; the unnamed pair routed through audition; floor >= 6 h (<= 4 a day, D-0500's defeater)")
check(not (set(NEW) & SC._STORM_DRIVEN_EVENTS), "no §4 key is in _STORM_DRIVEN_EVENTS")

# ═══ [2] the clocks ═════════════════════════════════════════════════════════════════════════════════════════════
print("[2] clocks")
from core import world_clock as WC                                # noqa: E402


def passes_in(month: int) -> list[list[tuple[float, float]]]:
    return [SC._flyover_passes(at(month, d, 12)) for d in range(1, 29)]


apr, jan, jul, oct_ = passes_in(4), passes_in(1), passes_in(7), passes_in(10)
days_apr, days_jan = sum(1 for p in apr if p), sum(1 for p in jan if p)
check(0 < days_apr <= 16 and days_jan < days_apr, f"April: a pair goes over on some days ({days_apr}/28), fewer in January ({days_jan}/28)")
check(any(len(p) == 2 for p in apr + jul + oct_), "now and then a second pair on the same day")
ok_shape = True
for month, plist in ((4, apr), (1, jan), (7, jul), (10, oct_)):
    rise, sett = WC._SUN[month]
    for p in plist:
        for s, e in p:
            dur = (e - s) * 60.0
            if not (SC._FLYOVER_PASS_MIN[0] - 1e-6 <= dur <= SC._FLYOVER_PASS_MIN[1] + 1e-6 and s >= rise + SC._FLYOVER_SKY_MARGIN_H - 1e-6 and e <= sett - SC._FLYOVER_SKY_MARGIN_H + 1e-6):
                ok_shape = False
check(ok_shape, "every pass is minutes long and inside the month's own daylight (world_clock's sun table, a margin off sunrise/sunset)")
check(SC._flyover_passes(at(4, 20, 9)) == SC._flyover_passes(at(4, 20, 16)), "deterministic: one day, one draw, whatever the hour")
# the window: a tiny fraction of daylight minutes across a year of days
mins = [SC._flyover_window(at(m, d, h, mi)) for m in (1, 4, 7, 10) for d in (3, 11, 19, 27) for h in range(6, 21) for mi in range(0, 60, 2)]
frac = sum(mins) / len(mins)
check(0.0 < frac < 0.01, f"the pair is overhead a tiny fraction of daylight minutes ({frac:.4f})")
check(not any(SC._flyover_window(at(4, d, 2)) for d in range(1, 29)), "never in the night")


def first_pass(month: int, day_from: int = 10) -> float:
    for d in range(day_from, 29):
        p = SC._flyover_passes(at(month, d, 12))
        if p:
            s, e = p[0]
            h = int(s)
            mi = int((s - h) * 60) + 1
            return at(month, d, h, mi, 10)
    raise AssertionError(f"no pass found in month {month}")


PT = first_pass(4)
check(SC._flyover_window(PT) and not SC._flyover_window(PT + 3600) and not SC._flyover_window(PT - 3600), "inside a pass: overhead; an hour either side: gone")

# ═══ [3] life binding ═══════════════════════════════════════════════════════════════════════════════════════════
print("[3] life binding")
tauhou = life._ROWS.get("tauhou")
check(bool(tauhou) and "silvereye_flock" in (tauhou.get("sound") or ()) and "small_birds" in (tauhou.get("sound") or ()), "the tauhou row carries silvereye_flock beside its small_birds (additive)")
check("silvereye_flock" in life.creature_sound_keys("garden") and "silvereye_flock" in life.creature_sound_keys(None), "silvereye_flock is creature-governed at the garden (D-0133 gating)")
check(not ({"paradise_duck_flyover", "kelp_fly_buzz"} & life.creature_sound_keys(None)), "the flyover and the flies are not creature-governed (no life row; the row alone decides)")
S.state.update(weather="clear", wind="breeze")
july_days = [("silvereye_flock" in life.sounds_active("garden", at(7, d, 13))) for d in range(1, 32)]
check(sum(july_days) >= 24, f"July: the flock is in the hedge most days by day ({sum(july_days)}/31)")
check(not any("silvereye_flock" in life.sounds_active("garden", at(7, d, 23)) for d in range(1, 32)), "July: never at night (DIURNAL)")
jan_days = [("silvereye_flock" in life.sounds_active("garden", at(1, d, 13))) for d in range(1, 32)]
# WINTER_FLOCK's January value (0.2) still clears PRESENT_AT on the row's higher day-factor days -- the row's OWN calendar
# (D-0133: the curves ARE the calendar; base system untouched), so summer is rarer, not silent: "a few" tauhou some days.
check(sum(jan_days) < sum(july_days), f"January: fewer flock days than July (WINTER_FLOCK: {sum(jan_days)}/31 vs {sum(july_days)}/31)")
S.state.update(weather="drizzle", wind="breeze")
jan_wet = [("silvereye_flock" in life.sounds_active("garden", at(1, d, 13))) for d in range(1, 32)]
check(sum(jan_wet) < sum(jan_days), f"...and rarer still in rain (the row's weather gate: {sum(jan_wet)}/31)")
check(not any("silvereye_flock" in life.sounds_active(p, at(7, d, 13)) for d in range(1, 32) for p in ("study", "shore", "wood")), "the garden's only (the row's place)")
S.state.update(weather="thunderstorm", wind="gale")
check(not any("silvereye_flock" in life.sounds_active("garden", at(7, d, 13)) for d in range(1, 32)), "a storm grounds the small birds: no flock voice")
S.state.update(weather="clear", wind="breeze")
check(life.sounds_active("garden", at(7, 10, 13)) == life.sounds_active("garden", at(7, 10, 13)), "sounds_active is deterministic for one moment")
FT = next(at(7, d, 13) for d in range(1, 32) if "silvereye_flock" in life.sounds_active("garden", at(7, d, 13)))
QT = next((at(7, d, 13) for d in range(1, 32) if "silvereye_flock" not in life.sounds_active("garden", at(7, d, 13))), None)

# ═══ [4] propagation through the REAL active_sounds() ═══════════════════════════════════════════════════════════
print("[4] propagation")
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

    _secs = [f for _, f in SC._PROPAGATION_TABLE]
    _i4 = _secs.index(SC._sec_seasonal_biophony)
    check(_secs[_i4 - 1] is SC._sec_geophony and all(getattr(f, "__name__", "") == "_sec_apparatus" for f in _secs[_i4 + 1:]),
          "the §4 row comes directly after the §3 row; only J-2478's §5 apparatus row may follow (chain-tolerant)")
    _TABLE_TO_4 = SC._PROPAGATION_TABLE[:_i4 + 1]
    # the flock
    check("silvereye_flock" in active_at("garden", FT), "a July day the flock is about: silvereye_flock is active in the garden")
    check(not any("silvereye_flock" in active_at(p, FT) for p in ("study", "shore", "wood")), "...and nowhere else")
    check("silvereye_flock" not in active_at("garden", at(7, 10, 23)), "never at night")
    check("silvereye_flock" not in active_at("garden", FT, "thunderstorm", "gale"), "a storm: silent")
    check(all(("silvereye_flock" in active_at("garden", at(7, d, 13))) == ("silvereye_flock" in life.sounds_active("garden", at(7, d, 13))) for d in range(1, 32)),
          "every July day: active_sounds agrees with life.sounds_active on the flock (the row reads the same function)")
    # the flyover
    check("paradise_duck_flyover" in active_at("garden", PT) and "paradise_duck_flyover" in active_at("shore", PT), "inside a pass: the pair is heard from the garden and the shore")
    check(not any("paradise_duck_flyover" in active_at(p, PT) for p in ("study", "wood")), "...not from under the roof or the canopy")
    check("paradise_duck_flyover" not in active_at("garden", PT + 3600) and "paradise_duck_flyover" not in active_at("shore", PT - 3600), "an hour either side: gone")
    check("paradise_duck_flyover" not in active_at("garden", PT, "thunderstorm", "breeze") and "paradise_duck_flyover" not in active_at("garden", PT, "wind and rain", "breeze")
          and "paradise_duck_flyover" not in active_at("garden", PT, "clear", "gale"), "storm weather or a gale grounds the pair")
    check("paradise_duck_flyover" in active_at("garden", PT, "steady rain", "fresh wind"), "plain rain and a fresh wind do not")
    # the flies
    jan_noon = at(1, 10, 13)
    check("kelp_fly_buzz" in active_at("shore", jan_noon, "clear", "calm") and "kelp_fly_buzz" in active_at("shore", jan_noon, "high cloud", "breeze"),
          "a dry still summer day at the shore: the flies are up")
    check(not any("kelp_fly_buzz" in active_at("shore", jan_noon, "clear", w) for w in ("fresh wind", "strong wind", "gale")), "wind keeps them down in the lee of the heap")
    check(not any("kelp_fly_buzz" in active_at("shore", jan_noon, w, "calm") for w in ("drizzle", "steady rain", "thunderstorm")), "rain: no flies")
    check("kelp_fly_buzz" not in active_at("shore", at(1, 10, 23), "clear", "calm"), "never at night")
    check(not any("kelp_fly_buzz" in active_at("shore", at(mo, 10, 13), "clear", "calm") for mo in (4, 7, 10)), "never outside summer")
    check(not any("kelp_fly_buzz" in active_at(p, jan_noon, "clear", "calm") for p in ("garden", "study", "wood")), "the wrack-line's only")
    # row LAST: pure suffix with gating OFF; with gating ON every pre-existing key keeps its relative order
    without = _TABLE_TO_4[:-1]
    moments = ((("garden", FT, "clear", "breeze", "out"), ("garden", PT, "clear", "breeze", "out"), ("shore", PT, "clear", "calm", "out"),
                ("shore", jan_noon, "clear", "calm", "out"), ("shore", jan_noon, "high cloud", "breeze", "out")))
    ok_order = all([k for k in active_at(*m, table=_TABLE_TO_4) if k not in NEW] == [k for k in active_at(*m, table=without) if k not in NEW] for m in moments)
    check(ok_order, "gating ON: every pre-existing key present, in its old relative order; only the new keys are added")
    life.SOUND_GATING = False
    try:
        ok_suffix = all(active_at(*m, table=_TABLE_TO_4)[:len(active_at(*m, table=without))] == active_at(*m, table=without)
                        and all(k in NEW for k in active_at(*m, table=_TABLE_TO_4)[len(active_at(*m, table=without)):])
                        and len(active_at(*m, table=_TABLE_TO_4)) > len(active_at(*m, table=without))
                        for m in moments)
        check(ok_suffix, "gating OFF: the row is a pure, non-empty suffix at every moment -- nothing ahead of it moves (out[:4] discipline)")
        check(all(("silvereye_flock" in active_at("garden", at(7, d, 13))) == ("silvereye_flock" in life.sounds_active("garden", at(7, d, 13))) for d in range(1, 32)),
              "gating OFF (shadow): the legacy row still agrees with life.sounds_active on the flock")
    finally:
        life.SOUND_GATING = True
finally:
    thaw()

# ═══ [5] the percept rail ═══════════════════════════════════════════════════════════════════════════════════════
print("[5] percept rail")
_REAL_ACTIVE_SOUNDS = SC.active_sounds
try:
    ROOM.update(location="garden", weather="clear", wind="breeze", fire="out")
    S.state.update(weather="clear", wind="breeze")
    SC.SOUND_PERCEPTS = True
    SC.active_sounds = lambda: ["silvereye_flock"]
    freeze(FT)
    SC._save_snd_state({"was_active": [], "quiet_since": {"silvereye_flock": FT - 700}, "last_notice": {}, "last_percept": 0.0})
    line = SC.percept(store=False)
    pools = SK.AUDITION["silvereye_flock"]["unknown"]["garden"]
    check(bool(line) and line in pools, "an onset reaches him as the UNNAMED garden rendering (cheeps in the hedge, never 'tauhou')")
    check(bool(line) and "tauhou" not in line.lower() and "silvereye" not in line.lower() and "hedge" in line.lower(), "...direction + near word, no cause named")
    led = SK._load()
    check(any(r.get("key") == "silvereye_flock" and r.get("loc") == "garden" for r in led.get("recent", [])), "the hearing is noted in the ledger's recent list (a look can bind)")
    st = SC._snd_state()
    check(st.get("last_biophony_percept", {}).get("silvereye_flock") == FT and st.get("last_percept") == FT, "state: last_biophony_percept + last_percept stamped")
    check(SC.percept(store=False) is None, "an immediate second call: nothing (the rail's shared cooldown)")
    t2 = FT + 3000
    freeze(t2)
    SC._save_snd_state({"was_active": [], "quiet_since": {"silvereye_flock": t2 - 700}, "last_notice": {}, "last_percept": FT, "last_biophony_percept": {"silvereye_flock": FT}})
    check(SC.percept(store=False) is None, "50 min later, a fresh onset: refused by the 8 h per-key floor")
    t3 = FT + SC._BIOPHONY_PERCEPT_COOLDOWN_S + 60       # the same July day, nine in the evening: the row is quiet but the stub keeps it active
    freeze(t3)
    SC._save_snd_state({"was_active": [], "quiet_since": {"silvereye_flock": t3 - 700}, "last_notice": {}, "last_percept": FT, "last_biophony_percept": {"silvereye_flock": FT}})
    line2 = SC.percept(store=False)
    # at t3 the gate's own audition check (life.sounds_active at night) silences it: a creature that is not awake cannot sound
    check(line2 is None, "past the floor but at night: _audition's life check gives no line (a sleeping flock cannot sound), no cooldown consumed")
    check(SC._snd_state().get("last_percept") == FT, "...and last_percept untouched")
    FT2 = next((t for t in (FT + k * 86400 for k in range(1, 40)) if "silvereye_flock" in life.sounds_active("garden", t)), None)
    check(FT2 is not None, "a later July/August day the flock is about")
    freeze(FT2)
    SC._save_snd_state({"was_active": [], "quiet_since": {"silvereye_flock": FT2 - 700}, "last_notice": {}, "last_percept": FT, "last_biophony_percept": {"silvereye_flock": FT}})
    line3 = SC.percept(store=False)
    check(bool(line3) and line3 in pools, "past the floor, by day, the flock present: it fires again, still unnamed")
    t5 = FT2 + SC._RENOTICE_S + 60
    freeze(t5)
    SC._save_snd_state({"was_active": ["silvereye_flock"], "quiet_since": {}, "last_notice": {"silvereye_flock": FT2}, "last_percept": FT2, "last_biophony_percept": {"silvereye_flock": FT2}})
    check(SC.percept(store=False) is None, "4 h on: a renotice is refused while the 8 h floor holds")
    FT3 = next((t for t in (FT2 + k * 86400 for k in range(1, 40)) if "silvereye_flock" in life.sounds_active("garden", t)), None)
    freeze(FT3)
    SC._save_snd_state({"was_active": ["silvereye_flock"], "quiet_since": {}, "last_notice": {"silvereye_flock": FT2}, "last_percept": FT2, "last_biophony_percept": {"silvereye_flock": FT2}})
    line4 = SC.percept(store=False)
    check(bool(line4) and line4 in pools, "a day on: the renotice fires, still unnamed (same garden pool)")
    # the flyover at the shore: the unnamed shore pool; the pass is in the ledger for a look to catch
    ROOM.update(location="shore")
    SC.active_sounds = lambda: ["waves_on_shingle", "paradise_duck_flyover"]
    freeze(PT)
    SC._save_snd_state({"was_active": ["waves_on_shingle"], "quiet_since": {"paradise_duck_flyover": PT - 700}, "last_notice": {}, "last_percept": 0.0})
    fl = SC.percept(store=False)
    check(bool(fl) and fl in SK.AUDITION["paradise_duck_flyover"]["unknown"]["shore"] and "duck" not in fl.lower() and "overhead" in fl.lower() or (bool(fl) and "high" in fl.lower()),
          "the flyover at the shore: the unnamed shore pool, voices going over high, no cause")
    check(SC._snd_state().get("last_biophony_percept", {}).get("paradise_duck_flyover") == PT, "...and its own per-key floor stamped")
    # the flies: known -- the named onset pool directly
    ROOM.update(location="shore", weather="clear", wind="calm")
    SC.active_sounds = lambda: ["waves_on_shingle", "kelp_fly_buzz"]
    kt = at(1, 10, 13)
    freeze(kt)
    SC._save_snd_state({"was_active": ["waves_on_shingle"], "quiet_since": {"kelp_fly_buzz": kt - 700}, "last_notice": {}, "last_percept": 0.0})
    kl = SC.percept(store=False)
    check(bool(kl) and kl in SC._PERCEPT_LINES["kelp_fly_buzz"]["onset"] and "kelp" in kl.lower(), "kelp_fly_buzz: known -- the named onset pool directly")
    check(SC._snd_state().get("last_biophony_percept", {}).get("kelp_fly_buzz") == kt, "...with its own per-key floor stamped")
    # once the name is earned: the NAMED pool
    led = SK._load(); SK._add_event(led, "silvereye_flock", "sighted", 1.0, "test"); SK._save(led)
    check(SK.is_learned("silvereye_flock"), "after a sighting the flock is learned")
    ROOM.update(location="garden", weather="clear", wind="breeze")
    SC.active_sounds = lambda: ["silvereye_flock"]
    freeze(FT)
    SC._save_snd_state({"was_active": [], "quiet_since": {"silvereye_flock": FT - 700}, "last_notice": {}, "last_percept": 0.0})
    named = SC.percept(store=False)
    check(bool(named) and named in SC._PERCEPT_LINES["silvereye_flock"]["onset"] and "tauhou" in named.lower(), "learned: the onset renders NAMED from its own pool")
    # first refusal: the tui ahead of a §4 key onsetting at the same moment
    SC.active_sounds = lambda: ["tui_song", "silvereye_flock", "paradise_duck_flyover"]
    freeze(FT)
    SC._save_snd_state({"was_active": [], "quiet_since": {"tui_song": FT - 700, "silvereye_flock": FT - 700, "paradise_duck_flyover": FT - 700}, "last_notice": {}, "last_percept": 0.0})
    tp = SC.percept(store=False)
    check(bool(tp) and tp in SC._PERCEPT_LINES["tui_song"]["onset"], "the tui keeps first refusal over §4 keys onsetting at the same moment")
finally:
    thaw()
    SC.active_sounds = _REAL_ACTIVE_SOUNDS
check(SC.active_sounds is _REAL_ACTIVE_SOUNDS and SC.active_sounds.__module__ == "core.soundscape", "real active_sounds restored")

# ═══ [6] earning the name ═══════════════════════════════════════════════════════════════════════════════════════
print("[6] earning the name")
SK._save({"sounds": {}, "recent": []})
_real_random = random.random
try:
    now = FT
    freeze(now)
    led = SK._load(); led["recent"] = [{"key": "silvereye_flock", "ts": now - 60, "loc": "garden"}]; SK._save(led)
    random.random = lambda: 0.0           # the roll succeeds
    check(SK.look_binding("the hedge", "garden", is_day=False) == "" and not SK.is_learned("silvereye_flock"), "a look at the hedge at night cannot bind the flock (day_only)")
    check(SK.look_binding("the hedge", "study", is_day=True) == "" and not SK.is_learned("silvereye_flock"), "a look from another place does not bind")
    out = SK.look_binding("the hedge", "garden", is_day=True)
    check(out.startswith(SK.AUDITION["silvereye_flock"]["reveal"]) and SK.is_learned("silvereye_flock"), "a day look at the hedge binds the cheeping to the tauhou (reveal + learned)")
    # the flyover: a look UP inside the pass binds; the same look ten minutes on does not (bind_window_s), though the
    # hearing is still inside the module's 15-minute recent list
    led = SK._load(); led["recent"] = [{"key": "paradise_duck_flyover", "ts": now - 600, "loc": "garden"}]; SK._save(led)
    check(SK.look_binding("up at the sky", "garden", is_day=True) == "" and not SK.is_learned("paradise_duck_flyover") and SK._weight(SK._load(), "paradise_duck_flyover") == 0.0,
          "ten minutes after the pass: a look up finds nothing to bind and earns nothing (the pair is gone)")
    led = SK._load(); led["recent"] = [{"key": "paradise_duck_flyover", "ts": now - 120, "loc": "garden"}]; SK._save(led)
    out = SK.look_binding("up at the sky", "garden", is_day=True)
    check(out.startswith(SK.AUDITION["paradise_duck_flyover"]["reveal"]) and SK.is_learned("paradise_duck_flyover"), "two minutes in: a look up catches the pair (reveal + learned)")
    # an entry WITHOUT a bind window keeps the module's 15 min exactly as before
    led = SK._load(); led["recent"] = [{"key": "godwits_overhead", "ts": now - 600, "loc": "garden"}]; SK._save(led)
    out = SK.look_binding("up at the sky", "garden", is_day=True)
    check(out.startswith(SK.AUDITION["godwits_overhead"]["reveal"]) and SK.is_learned("godwits_overhead"), "godwits_overhead (no bind window): ten minutes on, a look up still binds (unchanged)")
    led = SK._load(); led["recent"] = [{"key": "cuckoo_call", "ts": now - 1000, "loc": "garden"}]; SK._save(led)
    check(SK.look_binding("the kowhai", "garden", is_day=True) == "", "...and past 15 min nothing binds, as before")
    random.random = lambda: 0.99          # the roll fails: a miss, with exposure weight
    SK._save({"sounds": {}, "recent": [{"key": "paradise_duck_flyover", "ts": now - 60, "loc": "shore"}]})
    out = SK.look_binding("the sky over the bay", "shore", is_day=True)
    check(out == SK.AUDITION["paradise_duck_flyover"]["miss"] and 0 < SK._weight(SK._load(), "paradise_duck_flyover") < 1.0, "a look up that misses: the honest miss line, a little exposure weight")
    random.random = _real_random
    SK._save({"sounds": {}, "recent": []})
    check(SK.learn_from_text("the tauhou are about again this winter") == [] and not SK.is_learned("silvereye_flock"), "a line that names the bird without its sound does not teach the flock")
    learned = SK.learn_from_text("In winter the silvereyes move through the hedges in loose flocks, cheeping softly to one another as they go.")
    check("silvereye_flock" in learned and SK.is_learned("silvereye_flock"), "a book that ties the silvereyes to their flock cheeping teaches it")
    learned = SK.learn_from_text("Paradise ducks pair for life; you will hear them honking as a pair goes over, the female high and the male low.")
    check("paradise_duck_flyover" in learned and SK.is_learned("paradise_duck_flyover"), "a book that ties paradise ducks to honking overhead teaches the flyover")
finally:
    random.random = _real_random
    thaw()

# ═══ [7] the hearing ledger ═════════════════════════════════════════════════════════════════════════════════════
print("[7] hearing ledger")
SK._save({"sounds": {}, "recent": []})
_real_active = SC.active_sounds
try:
    ROOM.update(location="shore", weather="clear", wind="calm", fire="out")
    SC.active_sounds = lambda: ["silvereye_flock", "paradise_duck_flyover", "kelp_fly_buzz"]
    for _ in range(12):
        SC.world_tick("shore", 300.0)            # 1 h: the flock ~24 cheeps, the flyover ~60 honks, the flies bank the hour
    h = SK._load().get("hearings", {})
    hrs = float((h.get("kelp_fly_buzz") or {}).get("bed_hours", 0.0))
    n_f, n_p = int((h.get("silvereye_flock") or {}).get("count", 0)), int((h.get("paradise_duck_flyover") or {}).get("count", 0))
    check(abs(hrs - 1.0) < 0.01 and not (h.get("kelp_fly_buzz") or {}).get("count"), f"kelp_fly_buzz banks lived-in hours, never counts ({hrs:.3f} h)")
    check(10 <= n_f <= 40, f"silvereye_flock banks cheeps at its rate ({n_f} in 1 h, expected ~24)")
    check(35 <= n_p <= 90, f"paradise_duck_flyover banks at its per-hour rate while active ({n_p} in 1 h, expected ~60; a real pass is minutes)")
    check((h.get("silvereye_flock") or {}).get("places", {}).get("shore") == n_f, "...keyed to his place")
finally:
    SC.active_sounds = _real_active

# ═══ [8] the sidecar dry-run's archetype invariant ═════════════════════════════════════════════════════════════
print("[8] sidecar archetypes")
import scripts.sound_strings_phase1_dryrun as DRY        # noqa: E402  (imports the same worktree core.soundscape; writes nothing until main())
strings = DRY.build_all()
check(set(NEW) <= set(strings), "every §4 key is classified (build_all's invariant holds)")
check(strings["kelp_fly_buzz"]["archetype"] == "bed_like" and strings["silvereye_flock"]["archetype"] == "call" and strings["paradise_duck_flyover"]["archetype"] == "call",
      "the flies are a bed-like string; the flock and the flyover are calls")

# ═══ [9] isolation ══════════════════════════════════════════════════════════════════════════════════════════════
print("[9] isolation")
_after = {p: _md5(p) for p in _LIVE_FILES}
check(LIVE_WRITE_ATTEMPTS == [], f"no write attempt under any data/ dir ({LIVE_WRITE_ATTEMPTS[:3]})")
changed = [p.name for p in _LIVE_FILES if _before[p] != _after[p]]
check(not changed, f"live files unchanged ({changed})")
for mod, attr in ((life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (SK, "_LEDGER_F"), (SC, "_SND_STATE_F"), (SC, "_FELT_SHADOW_F"), (S, "_STATE_F"), (CAT, "_STATE_F"), (WL, "_F")):
    check(str(getattr(mod, attr)).startswith(str(TMP)), f"{mod.__name__}.{attr} still inside TMP")

print(f"\n{N - len(FAILS)}/{N} checks passed" + (f" -- FAILS: {FAILS}" if FAILS else " -- ALL OK"))
sys.exit(1 if FAILS else 0)
