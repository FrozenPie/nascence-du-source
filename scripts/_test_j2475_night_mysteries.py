"""
J-2475 (sound_world_expansion §2, D-0500): THE NIGHT MYSTERIES -- possum_rasp, wall_scratch, distant_yowl,
hedgehog_snuffle, dolphin_blow. Hermetic: every store the engine can reach is redirected into a temp dir before
anything can write; a Python audit hook records any write attempt under a live data/ dir; the live files are
md5-hashed before and after. Run from the worktree:  python scripts/_test_j2475_night_mysteries.py   (exit 0 = ALL OK)

  [1] registry: five Sound-Space points, rates, AUDITION entries (unnamed), named percept pools (>= 4, rotating)
  [2] life binding: rows carry the voices (sound / sound_at / sound_days); creature_sound_keys per place; some nights,
      not every night; never by day; the hedgehog silent in hibernation; the dolphins only when the pod is about
  [3] propagation through the REAL soundscape.active_sounds(): place x phase x weather, gating ON and OFF, row LAST
      (out[:4] unchanged), the yowl's nightly bout deterministic and rare
  [4] the percept rail: a mystery reaches him UNNAMED (its features, never its cause), rotates, obeys the shared
      cooldown and the 6 h per-key floor, and renders NAMED only after the name is earned; cat/morepork/tui keep
      first refusal; no digit or readout word in any new line (D-0434)
  [5] earning the name: sight-binding (hedgehog), the un-findable wall (miss, never a reveal), a book (possum)
  [6] the hearing ledger banks occurrences through world_tick at the registered rate
  [7] isolation: no write attempt under any data/, live hashes unchanged
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

TMP = Path(tempfile.mkdtemp(prefix="j2475_night_mysteries_"))
print("isolated store dir:", TMP)
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("room_state.json", "life_state.json", "life_ledger.jsonl", "life_events.jsonl",
                                        "life_flags.json", "sound_knowledge.json", "soundscape_state.json",
                                        "soundscape_felt_shadow.jsonl", "cat_state.json", "position.json")]


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
from core import life, life_mammals                             # noqa: E402
from core import cat_tom as _cat_tom                            # noqa: E402
_cat_tom.live_on = lambda: False   # merge 2026-10-29: when the tom (cat_overhaul B3) is live he owns the far yowl; this harness tests §2's own draw
from core import world_traces as WT                             # noqa: E402
from core import sensorium as S                                 # noqa: E402
from core import locomotion as L                                # noqa: E402
from core import sound_knowledge as SK                          # noqa: E402
from core import soundscape as SC                               # noqa: E402
from core import cat as CAT                                     # noqa: E402

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
SC._DATA, SC._SND_STATE_F, SC._FELT_SHADOW_F = TMP, TMP / "soundscape_state.json", TMP / "soundscape_felt_shadow.jsonl"
CAT._STATE_F = TMP / "cat_state.json"
assert not profile.LIVE, "this test must never run as the live process"

# an in-memory room: soundscape reads room_state/cat_state through _read_json -- no disk, no live file
ROOM: dict = {"location": "garden", "weather": "clear", "wind": "breeze", "fire": "out", "study": {}}
CATST: dict = {"phase": "kept", "mood": "content", "activity": "sleeping", "location": "gone"}
SC._read_json = lambda name: dict(ROOM) if name == "room_state.json" else (dict(CATST) if name == "cat_state.json" else {})
S.state = {"weather": "clear", "wind": "breeze", "frost_last": False}
life.RENDER = False
life.SOUND_GATING = True            # the live flag state since 2026-09-09 (data/life_flags.json gating=true)

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


NEW = ("possum_rasp", "wall_scratch", "distant_yowl", "hedgehog_snuffle", "dolphin_blow")
life._ensure_builtin()

# ═══ [1] registry ════════════════════════════════════════════════════════════════════════════════════════════════
print("[1] registry")
for k in NEW:
    e = SC._SOUNDS.get(k)
    check(bool(e) and set(e["coords"]) == set(SC._AXES) and all(0.0 <= v <= 1.0 for v in e["coords"].values()), f"{k}: a six-axis point in [0,1]")
check(SC._SOUNDS["possum_rasp"]["object"] == "the possum" and SC._SOUNDS["hedgehog_snuffle"]["object"] == "the hedgehog"
      and SC._SOUNDS["wall_scratch"]["object"] == "the mice" and SC._SOUNDS["dolphin_blow"]["object"] == "the dolphins"
      and SC._SOUNDS["distant_yowl"]["object"] == "the distant cat", "objects name the life rows / stick_test's 'the distant cat'")
check(set(SC._EVENT_RATES) <= set(SC._SOUNDS), "set(_EVENT_RATES) <= set(_SOUNDS) still holds")
check(all(0 < SC._EVENT_RATES[k] <= 6.0 for k in NEW) and SC._EVENT_RATES["dolphin_blow"] <= 0.5 and SC._EVENT_RATES["distant_yowl"] <= 2.0,
      "every mystery rated, low (dolphin <= 0.5/h, yowl <= 2/h)")
check(all(k not in SC._BEDS for k in NEW), "all five are EVENT-class (none a bed)")
check(all(k in SK.AUDITION and k not in SK.GRANDFATHERED for k in NEW), "all five have an AUDITION entry and none is grandfathered")
check(all(not SK.is_learned(k) for k in NEW), "with an empty ledger none is learned (arrives unnamed)")
for k in NEW:
    pools = SK.AUDITION[k]["unknown"]
    check(all(isinstance(p, (tuple, list)) and len(p) >= 4 for p in pools.values()), f"{k}: unnamed pool(s) of >= 4 lines per place {sorted(pools)}")
    check(len(SC._PERCEPT_LINES[k]["onset"]) >= 4 and len(SC._PERCEPT_LINES[k]["renotice"]) >= 2, f"{k}: named onset pool >= 4, renotice >= 2")
check(SK.AUDITION["wall_scratch"]["sight_prob"] == 0.0 and SK.AUDITION["wall_scratch"]["reveal"] == "", "wall_scratch can never be sight-bound (no trap authored; may stay a mystery)")
check(SK.AUDITION["distant_yowl"]["day_only"] is False and SK.AUDITION["dolphin_blow"]["day_only"] is True, "yowl binds at night; the dolphins only by day")
# known kind, unknown individual: every unnamed yowl line says 'cat' (the kind) and never 'black' (the individual)
yowl_lines = [ln for pool in SK.AUDITION["distant_yowl"]["unknown"].values() for ln in pool]
check(all("cat" in ln.lower() and "black" not in ln.lower() and "hers" not in ln.lower() for ln in yowl_lines), "distant_yowl unnamed lines: a cat's voice, never whose")
# the other four never name their cause while unnamed
for k, words in (("possum_rasp", ("possum",)), ("wall_scratch", ("mouse", "mice")), ("hedgehog_snuffle", ("hedgehog",)), ("dolphin_blow", ("dolphin",))):
    lines = [ln for pool in SK.AUDITION[k]["unknown"].values() for ln in pool]
    check(all(not any(w in ln.lower() for w in words) for ln in lines), f"{k}: unnamed lines never name the cause")
# no readout (D-0434): no digit, no gauge word, in any new line he could ever receive
all_new_lines = [ln for k in NEW for pool in SK.AUDITION[k]["unknown"].values() for ln in pool]
all_new_lines += [ln for k in NEW for kind in ("onset", "renotice") for ln in SC._PERCEPT_LINES[k][kind]]
all_new_lines += [SK.AUDITION[k]["reveal"] + SK.AUDITION[k]["miss"] for k in NEW]
check(all(not any(ch.isdigit() for ch in ln) and not any(w in ln.lower() for w in ("gauge", "score", "level", "percent", "probability")) for ln in all_new_lines),
      f"no digit / readout word in any of the {len(all_new_lines)} new lines")
_NEARFAR = ("close", "near", "far", "distant", "overhead", "a long way", "right at", "beyond", "above you", "at your feet", "arm's length")
heard_lines = [ln for k in NEW for pool in SK.AUDITION[k]["unknown"].values() for ln in pool]
heard_lines += [ln for k in NEW for kind in ("onset", "renotice") for ln in SC._PERCEPT_LINES[k][kind]]
check(all(any(w in ln.lower() for w in _NEARFAR) for ln in heard_lines), f"every one of the {len(heard_lines)} lines he can hear carries a near/far word")
check(SC._PERCEPT_SOUNDS[:13] == ("cat_purr", "morepork_call", "tui_song", "cat_trill", "cat_meow_at_door", "cat_demand", "cat_chatter",
                                   "cat_yowl_cargo", "cat_thump", "cat_lapping", "cat_storm_rustle", "cat_hiss", "cat_growl") and SC._PERCEPT_SOUNDS[13:18] == NEW,
      "the rail's try-order: the thirteen cat/legacy keys first (cat_hiss/cat_growl merged in from cat_overhaul B3), the five mysteries directly after them (J-2476+: later sections append after)")

# ═══ [2] life binding ════════════════════════════════════════════════════════════════════════════════════════════
print("[2] life binding")
rows = {r["key"]: r for r in life_mammals.rows()}
check(rows["possum"]["sound"] == ("possum_rasp",) and rows["hedgehog"]["sound"] == ("hedgehog_snuffle",) and rows["dolphins"]["sound"] == ("dolphin_blow",),
      "possum / hedgehog / dolphins carry their voice in `sound`")
check(rows["mice"].get("sound_at") == {"study": ("wall_scratch",)} and not rows["mice"].get("sound"), "the mice carry wall_scratch ONLY at the study (sound_at)")
check(0 < rows["possum"]["sound_days"] < 1 and 0 < rows["hedgehog"]["sound_days"] < 1 and 0 < rows["mice"]["sound_days"] < 1, "possum / hedgehog / mice voice some days, not every day")
check(life.row("x")["sound_days"] == 1.0 and life.row("x")["sound_at"] == {}, "row() defaults: sound_days 1.0, sound_at {} (byte-identical for every other row)")
check("wall_scratch" in life.creature_sound_keys("study") and "wall_scratch" not in life.creature_sound_keys("wood") and "wall_scratch" not in life.creature_sound_keys("garden"),
      "creature_sound_keys governs wall_scratch at the study only")
check({"possum_rasp", "hedgehog_snuffle"} <= life.creature_sound_keys("garden") and "possum_rasp" in life.creature_sound_keys("wood")
      and "hedgehog_snuffle" not in life.creature_sound_keys("wood") and "dolphin_blow" in life.creature_sound_keys("shore")
      and "dolphin_blow" not in life.creature_sound_keys("garden"), "creature_sound_keys per place: possum garden+wood, hedgehog garden, dolphins shore")
check(set(NEW) - {"distant_yowl"} <= life.creature_sound_keys(None) and "distant_yowl" not in life.creature_sound_keys(None),
      "the four creature voices are governed; distant_yowl has no row and is NOT governed (legacy keeps its say)")
# _voice_day: 1.0 always True; missing field True; 0 never; a share is one fact per day and varies across days
check(all(life._voice_day("k", {"sound_days": 1.0}, at(11, d, 23)) for d in range(1, 31)) and life._voice_day("k", {}, at(11, 1, 23)), "_voice_day: share 1.0 / absent -> always voices")
check(not any(life._voice_day("k", {"sound_days": 0.0}, at(11, d, 23)) for d in range(1, 31)), "_voice_day: share 0 -> never")
half = [life._voice_day("possum", {"sound_days": 0.5}, at(11, d, 23)) for d in range(1, 31)]
check(5 <= sum(half) <= 25 and (life._voice_day("possum", {"sound_days": 0.5}, at(11, 3, 2)) == life._voice_day("possum", {"sound_days": 0.5}, at(11, 2, 23))),
      f"_voice_day: share 0.5 -> some days not others ({sum(half)}/30), and 02:00 belongs to the evening before")
# sounds_active over 30 summer nights in the garden: the possum rasps some nights, not every night; by day never
nights_possum = [("possum_rasp" in life.sounds_active("garden", at(11, d, 23))) for d in range(1, 31)]
nights_hedge = [("hedgehog_snuffle" in life.sounds_active("garden", at(11, d, 23))) for d in range(1, 31)]
check(3 <= sum(nights_possum) <= 24, f"possum_rasp voices on some November nights, not all ({sum(nights_possum)}/30)")
check(3 <= sum(nights_hedge) <= 27, f"hedgehog_snuffle voices on some November nights, not all ({sum(nights_hedge)}/30)")
check(not any(k in life.sounds_active("garden", at(11, d, 13)) for d in range(1, 31) for k in ("possum_rasp", "hedgehog_snuffle")), "neither sounds in the garden at noon")
check(not any("hedgehog_snuffle" in life.sounds_active("garden", at(7, d, 23)) for d in range(1, 31)), "July: the hedgehog is hibernating -- never snuffles")
check(any("possum_rasp" in life.sounds_active("garden", at(7, d, 23)) for d in range(1, 31)), "July: the resident possum still rasps some nights")
nights_wall = [("wall_scratch" in life.sounds_active("study", at(7, d, 23))) for d in range(1, 31)]
check(3 <= sum(nights_wall) <= 27 and not any("wall_scratch" in life.sounds_active("study", at(7, d, 13)) for d in range(1, 31)),
      f"wall_scratch: some winter nights ({sum(nights_wall)}/30), never by day")
check(not any("wall_scratch" in life.sounds_active(p, at(7, d, 23)) for d in range(1, 31) for p in ("wood", "garden")), "wall_scratch never sounds in the wood or the garden")
days_dolphin = [("dolphin_blow" in life.sounds_active("shore", at(1, d, 13))) for d in range(1, 31)]
check(1 <= sum(days_dolphin) <= 30, f"dolphin_blow: the summer pod is about some calm January days ({sum(days_dolphin)}/30)")
S.state["weather"] = "thunderstorm"
check(not any("dolphin_blow" in life.sounds_active("shore", at(1, d, 13)) for d in range(1, 31)), "dolphin_blow: never in a storm (the row's own weather gate)")
S.state["weather"] = "clear"
check(life.sounds_active("garden", at(11, 5, 23)) == life.sounds_active("garden", at(11, 5, 23)), "sounds_active is deterministic for one moment")

# ═══ [3] propagation through the REAL active_sounds() ═══════════════════════════════════════════════════════════
print("[3] propagation")
try:
    def active_at(loc: str, t: float, weather: str = "clear", wind: str = "breeze", table=None) -> list[str]:
        ROOM.update(location=loc, weather=weather, wind=wind)
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

    # J-2476+: later sections (§3 geophony, ...) append their own rows AFTER this one, so the invariant is "directly after
    # the cat row, nothing of the pre-§2 table moved" -- the suffix checks below truncate the table at the §2 row.
    _IDX2 = [f for _, f in SC._PROPAGATION_TABLE].index(SC._sec_night_mysteries)
    check(SC._PROPAGATION_TABLE[_IDX2 - 1][1] is SC._sec_cat and all(f is not SC._sec_cat for _, f in SC._PROPAGATION_TABLE[_IDX2:]),
          "the §2 row sits directly after the cat row (later sections append after it)")
    # garden, summer nights, gating ON: possum / hedgehog exactly as life says; day: none of them
    agree = 0
    for d in range(1, 31):
        t = at(11, d, 23)
        act = active_at("garden", t)
        mine = set(life.sounds_active("garden", t))
        agree += (("possum_rasp" in act) == ("possum_rasp" in mine)) and (("hedgehog_snuffle" in act) == ("hedgehog_snuffle" in mine))
    check(agree == 30, f"garden nights: possum_rasp / hedgehog_snuffle in active_sounds iff life voices them ({agree}/30)")
    check(not any(k in active_at("garden", at(11, d, 13)) for d in range(1, 31) for k in NEW), "garden days: no night mystery (dolphins are the shore's)")
    check(all(("possum_rasp" in active_at("wood", at(11, d, 23))) == ("possum_rasp" in life.sounds_active("wood", at(11, d, 23))) for d in range(1, 31))
          and not any("hedgehog_snuffle" in active_at("wood", at(11, d, 23)) for d in range(1, 31)), "wood nights: possum as life says; never the hedgehog")
    check(all(("wall_scratch" in active_at("study", at(7, d, 23))) == ("wall_scratch" in life.sounds_active("study", at(7, d, 23))) for d in range(1, 31)),
          "study winter nights: wall_scratch iff the mice voice there")
    check(all(("dolphin_blow" in active_at("shore", at(1, d, 13))) == ("dolphin_blow" in life.sounds_active("shore", at(1, d, 13))) for d in range(1, 31)),
          "shore days: dolphin_blow iff the pod is about")
    # the yowl: rare, nightly-drawn, a two-hour bout, deterministic; dry nights only; garden/wood near, study carried
    yowl_nights = 0
    for d in range(1, 61):
        samples = [SC._night_bout("distant_yowl", at(11, 1, 0) + (d - 1) * 86400 + 12 * 3600 + m * 600, SC._YOWL_NIGHT_SHARE, SC._YOWL_BOUT_H)
                   for m in range(0, 144)]       # noon .. noon next day, every 10 min (a bout may straddle midnight)
        if any(samples):
            yowl_nights += 1
            check(10 <= sum(samples) <= 13, f"night {d}: the yowl's bout lasts ~2 h ({sum(samples)} x 10 min)")
    check(3 <= yowl_nights <= 24, f"the other cat yowls on some nights only ({yowl_nights}/60)")
    tries = [at(11, d, h) for d in range(1, 61) for h in (22, 23, 0, 1, 2, 3)]
    yowl_t = next((t for t in tries if SC._night_bout("distant_yowl", t, SC._YOWL_NIGHT_SHARE, SC._YOWL_BOUT_H)), None)
    check(yowl_t is not None, "found a yowl moment to test with")
    if yowl_t:
        check("distant_yowl" in active_at("garden", yowl_t) and "distant_yowl" in active_at("wood", yowl_t) and "distant_yowl" in active_at("study", yowl_t),
              "in its bout the yowl is active in the garden, the wood, and carried into the study")
        check("distant_yowl" not in active_at("garden", yowl_t, weather="steady rain") and "distant_yowl" not in active_at("study", yowl_t, weather="thunderstorm"),
              "a wet night: no yowl")
        check("distant_yowl" not in active_at("shore", yowl_t), "the shore never hears it")
        check(active_at("garden", yowl_t) == active_at("garden", yowl_t), "deterministic: two reads of one moment agree")
    quiet_t = next((t for t in tries if not SC._night_bout("distant_yowl", t, SC._YOWL_NIGHT_SHARE, SC._YOWL_BOUT_H)), None)
    check(quiet_t is not None and "distant_yowl" not in active_at("garden", quiet_t), "outside its bout: no yowl")
    # row LAST: with the row removed, every pre-existing key is still there in the same relative order (the gate
    # itself re-appends governed keys after the kept legacy ones -- pre-existing behaviour, so the comparison is on
    # the pre-existing keys' own sequence, not on raw positions); gating OFF, the row is a pure suffix.
    without = SC._PROPAGATION_TABLE[:_IDX2]
    with2 = SC._PROPAGATION_TABLE[:_IDX2 + 1]          # J-2476+: the table up to and including the §2 row (later rows excluded)
    moments = (at(11, 7, 23), at(7, 7, 23), at(1, 7, 13), yowl_t or at(11, 1, 23))
    # (with gating ON the gate itself already adds the governed creature voices from life even without the row, so
    #  the new keys are stripped from BOTH sides: the row changes nothing about any pre-existing key)
    ok_order = all([k for k in active_at(loc, t, table=with2) if k not in NEW] == [k for k in active_at(loc, t, table=without) if k not in NEW]
                   for loc in ("garden", "wood", "study", "shore") for t in moments)
    check(ok_order, "gating ON: every pre-existing key present, in its old relative order; only the new keys are added")
    life.SOUND_GATING = False
    try:
        ok_suffix = all(active_at(loc, t, table=with2)[:len(active_at(loc, t, table=without))] == active_at(loc, t, table=without)
                        and all(k in NEW for k in active_at(loc, t, table=with2)[len(active_at(loc, t, table=without)):])
                        for loc in ("garden", "wood", "study", "shore") for t in moments)
        check(ok_suffix, "gating OFF: the row is a pure suffix -- nothing ahead of it moves (out[:4] discipline)")
    finally:
        life.SOUND_GATING = True
    # gating OFF (shadow): the legacy row contributes the same keys (it reads life.sounds_active itself)
    life.SOUND_GATING = False
    try:
        same = all(set(active_at("garden", at(11, d, 23))) & set(NEW) == set(life.sounds_active("garden", at(11, d, 23))) & set(NEW) | ({"distant_yowl"} & set(active_at("garden", at(11, d, 23))))
                   for d in range(1, 31))
        check(same, "gating OFF: the propagation row alone still binds the creature voices to presence")
    finally:
        life.SOUND_GATING = True
finally:
    thaw()

# ═══ [4] the percept rail ═══════════════════════════════════════════════════════════════════════════════════════
print("[4] percept rail")
_REAL_ACTIVE_SOUNDS = SC.active_sounds
try:
    # a night the possum voices in the garden (life must agree, since _audition re-checks the gate)
    pt = next(t for t in (at(11, d, 23) for d in range(1, 61)) if "possum_rasp" in life.sounds_active("garden", t))
    ROOM.update(location="garden", weather="clear", wind="breeze")
    S.state.update(weather="clear", wind="breeze")
    SC.SOUND_PERCEPTS = True
    SC.active_sounds = lambda: ["waves_on_shingle", "possum_rasp"]
    freeze(pt)
    SC._save_snd_state({"was_active": [], "quiet_since": {"possum_rasp": pt - 700}, "last_notice": {}, "last_percept": 0.0})
    line = SC.percept(store=False)
    pools = SK.AUDITION["possum_rasp"]["unknown"]["garden"]
    check(bool(line) and line in pools, "an onset reaches him as the UNNAMED garden rendering (features + 'close', never 'possum')")
    check(bool(line) and "possum" not in line.lower() and ("close" in line.lower() or "near" in line.lower() or "overhead" in line.lower()), "...with a near/far word and no cause named")
    led = SK._load()
    check(any(r.get("key") == "possum_rasp" and r.get("loc") == "garden" for r in led.get("recent", [])), "the hearing is noted in the ledger's recent list (a look within 15 min can bind)")
    st = SC._snd_state()
    check(st.get("last_mystery_percept", {}).get("possum_rasp") == pt and st.get("last_percept") == pt, "state: last_mystery_percept + last_percept stamped")
    check(SC.percept(store=False) is None, "an immediate second call: nothing (the rail's shared cooldown)")
    # past the shared cooldown but inside the 6 h per-key floor: quiet, then active again -> still nothing for THIS key
    t2 = pt + 3000
    freeze(t2)
    SC._save_snd_state({"was_active": [], "quiet_since": {"possum_rasp": t2 - 700}, "last_notice": {}, "last_percept": pt,
                        "last_mystery_percept": {"possum_rasp": pt}})
    check(SC.percept(store=False) is None, "50 min later, a fresh onset: refused by the 6 h per-key floor")
    t3 = pt + SC._MYSTERY_PERCEPT_COOLDOWN_S + 60
    freeze(t3)
    SC._save_snd_state({"was_active": [], "quiet_since": {"possum_rasp": t3 - 700}, "last_notice": {}, "last_percept": pt,
                        "last_mystery_percept": {"possum_rasp": pt}})
    pt3 = next((t for t in (t3 + k * 86400 for k in range(0, 60)) if "possum_rasp" in life.sounds_active("garden", t)), None)
    freeze(pt3)
    SC._save_snd_state({"was_active": [], "quiet_since": {"possum_rasp": pt3 - 700}, "last_notice": {}, "last_percept": pt, "last_mystery_percept": {"possum_rasp": pt}})
    line2 = SC.percept(store=False)
    check(bool(line2) and line2 in pools, "past the floor (and on a night it voices): it fires again")
    # a renotice of a long-running mystery is also unnamed, and the floor applies to it too
    t4 = pt3 + SC._RENOTICE_S + 60
    freeze(t4)
    SC._save_snd_state({"was_active": ["possum_rasp"], "quiet_since": {}, "last_notice": {"possum_rasp": pt3}, "last_percept": pt3, "last_mystery_percept": {"possum_rasp": pt3}})
    line3 = SC.percept(store=False)
    check(line3 is None, "4 h on: a renotice is refused while the 6 h floor holds")
    t5 = pt3 + SC._MYSTERY_PERCEPT_COOLDOWN_S + 60
    pt5 = next((t for t in (t5 + k * 3600 for k in range(0, 24 * 60)) if "possum_rasp" in life.sounds_active("garden", t)), None)
    check(pt5 is not None, "found a later night the possum voices on, past the 6 h floor")
    freeze(pt5)
    SC._save_snd_state({"was_active": ["possum_rasp"], "quiet_since": {}, "last_notice": {"possum_rasp": pt3}, "last_percept": pt3, "last_mystery_percept": {"possum_rasp": pt3}})
    line4 = SC.percept(store=False)
    check(bool(line4) and line4 in pools, "6 h on: the renotice fires, still unnamed (same garden pool)")
    # the rail refuses a mystery whose creature the gate says is NOT voicing (the audition re-check)
    quiet_night = next(t for t in (at(11, d, 23) for d in range(1, 61)) if "possum_rasp" not in life.sounds_active("garden", t))
    freeze(quiet_night)
    SC._save_snd_state({"was_active": [], "quiet_since": {"possum_rasp": quiet_night - 700}, "last_notice": {}, "last_percept": 0.0})
    check(SC.percept(store=False) is None, "a forced 'possum_rasp' on a night life says it is silent: no line, no percept (the gate holds)")
    # rotation: the unnamed pool never repeats back-to-back and uses more than one line
    seq = [SK._unknown_line(SK.AUDITION["possum_rasp"], "possum_rasp", "garden") for _ in range(40)]
    check(len(set(seq)) >= 3 and all(a != b for a, b in zip(seq, seq[1:])), f"unnamed pool rotates ({len(set(seq))} distinct, never twice running)")
    check(SK._unknown_line({"unknown": {"shore": "one fixed string"}}, "k", "shore") == "one fixed string"
          and SK._unknown_line({"unknown": {"shore": "one fixed string"}}, "k", "garden") == "one fixed string", "a plain-string unknown (every older entry) renders exactly as before, with the place fallback")
    # once the name is earned: the NAMED pool, direction and near/far words intact
    led = SK._load(); SK._add_event(led, "possum_rasp", "sighted", 1.0, "test"); SK._save(led)
    check(SK.is_learned("possum_rasp"), "after a sighting the voice is learned")
    freeze(pt)
    SC._save_snd_state({"was_active": [], "quiet_since": {"possum_rasp": pt - 700}, "last_notice": {}, "last_percept": 0.0})
    named = SC.percept(store=False)
    check(bool(named) and named in SC._PERCEPT_LINES["possum_rasp"]["onset"] and "possum" in named.lower(), "learned: the onset renders NAMED from its own pool")
    # the yowl, carried into the study: the study's own unnamed pool ('through the window', far)
    if yowl_t:
        ROOM.update(location="study")
        SC.active_sounds = lambda: ["fire_crackle", "distant_yowl"]
        freeze(yowl_t)
        SC._save_snd_state({"was_active": [], "quiet_since": {"distant_yowl": yowl_t - 700}, "last_notice": {}, "last_percept": 0.0})
        yl = SC.percept(store=False)
        check(bool(yl) and yl in SK.AUDITION["distant_yowl"]["unknown"]["study"] and "cat" in yl.lower() and "black" not in yl.lower(),
              "the yowl in the study: unnamed study pool -- a cat's voice, whose unknown, through the window")
    # first refusal: with the morepork AND a mystery both onsetting, the morepork wins the slot
    ROOM.update(location="garden")
    SC.active_sounds = lambda: ["morepork_call", "hedgehog_snuffle"]
    ht = next(t for t in (at(11, d, 23) for d in range(1, 61)) if "hedgehog_snuffle" in life.sounds_active("garden", t))
    freeze(ht)
    SC._save_snd_state({"was_active": [], "quiet_since": {"morepork_call": ht - 700, "hedgehog_snuffle": ht - 700}, "last_notice": {}, "last_percept": 0.0})
    mp = SC.percept(store=False)
    check(bool(mp) and mp in SC._PERCEPT_LINES["morepork_call"]["onset"], "the morepork keeps first refusal over a mystery onsetting at the same moment")
finally:
    thaw()
    SC.active_sounds = _REAL_ACTIVE_SOUNDS
check(SC.active_sounds is _REAL_ACTIVE_SOUNDS and SC.active_sounds.__module__ == "core.soundscape", "real active_sounds restored")

# ═══ [5] earning the name ═══════════════════════════════════════════════════════════════════════════════════════
print("[5] earning the name")
SK._save({"sounds": {}, "recent": []})
_real_random = random.random
try:
    now = at(11, 9, 23)
    freeze(now)
    led = SK._load(); led["recent"] = [{"key": "hedgehog_snuffle", "ts": now - 60, "loc": "garden"}]; SK._save(led)
    random.random = lambda: 0.0           # the roll succeeds
    out = SK.look_binding("the hedge bottom", "garden", is_day=False)
    check(out.startswith(SK.AUDITION["hedgehog_snuffle"]["reveal"]) and SK.is_learned("hedgehog_snuffle"), "a night look at the hedge binds the snuffle to the hedgehog (reveal + learned)")
    led = SK._load(); led["recent"] = [{"key": "wall_scratch", "ts": now - 60, "loc": "study"}]; SK._save(led)
    out = SK.look_binding("the wall by the skirting", "study", is_day=False)
    check(out == SK.AUDITION["wall_scratch"]["miss"] and not SK.is_learned("wall_scratch") and 0 < SK._weight(SK._load(), "wall_scratch") < 1.0,
          "a look at the wall: the honest miss, a little exposure weight, never a reveal (sight_prob 0)")
    led = SK._load(); led["recent"] = [{"key": "dolphin_blow", "ts": now - 60, "loc": "shore"}]; SK._save(led)
    check(SK.look_binding("the water", "shore", is_day=False) == "" and not SK.is_learned("dolphin_blow"), "the dolphins cannot be bound by night (day_only)")
    check(SK.look_binding("the water out past the surf", "shore", is_day=True).startswith(SK.AUDITION["dolphin_blow"]["reveal"]), "...but a day look at the water binds them")
    random.random = _real_random
    learned = SK.learn_from_text("The brushtail possum is loud at night: a harsh coughing rasp, hisses and screeches from the branches.")
    check("possum_rasp" in learned and SK.is_learned("possum_rasp"), "a book that ties 'possum' to 'rasp' teaches the voice")
    learned2 = SK.learn_from_text("A tomcat yowls at night, they say.")
    check("distant_yowl" in learned2 and SK.is_learned("distant_yowl"), "a book can name the yowl's owner too (tom + yowl)")
finally:
    random.random = _real_random
    thaw()

# ═══ [6] the hearing ledger ═════════════════════════════════════════════════════════════════════════════════════
print("[6] hearing ledger")
SK._save({"sounds": {}, "recent": []})
_real_active = SC.active_sounds
try:
    SC.active_sounds = lambda: ["possum_rasp", "dolphin_blow"]
    for _ in range(60):
        SC.world_tick("garden", 300.0)            # 5 h of possum nights at 2/h -> ~10 rasps; dolphins at 0.5/h -> ~2-3
    h = SK._load().get("hearings", {})
    n_p, n_d = int((h.get("possum_rasp") or {}).get("count", 0)), int((h.get("dolphin_blow") or {}).get("count", 0))
    check(2 <= n_p <= 25, f"world_tick banks possum_rasp occurrences at its rate ({n_p} in 5 h, expected ~10)")
    check(0 <= n_d <= 10 and n_d < n_p, f"dolphin_blow is rarer ({n_d} in 5 h, expected ~2-3)")
    check((h.get("possum_rasp") or {}).get("places", {}).get("garden") == n_p, "...and keyed to his place")
finally:
    SC.active_sounds = _real_active

# ═══ [7] isolation ══════════════════════════════════════════════════════════════════════════════════════════════
print("[7] isolation")
_after = {p: _md5(p) for p in _LIVE_FILES}
check(LIVE_WRITE_ATTEMPTS == [], f"no write attempt under any data/ dir ({LIVE_WRITE_ATTEMPTS[:3]})")
changed = [p.name for p in _LIVE_FILES if _before[p] != _after[p]]
check(not changed, f"live files unchanged ({changed})")
for mod, attr in ((life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (SK, "_LEDGER_F"), (SC, "_SND_STATE_F"), (SC, "_FELT_SHADOW_F"), (S, "_STATE_F"), (CAT, "_STATE_F")):
    check(str(getattr(mod, attr)).startswith(str(TMP)), f"{mod.__name__}.{attr} still inside TMP")

print(f"\n{N - len(FAILS)}/{N} checks passed" + (f" -- FAILS: {FAILS}" if FAILS else " -- ALL OK"))
sys.exit(1 if FAILS else 0)
