"""
J-2478 (sound_world_expansion §5, D-0500): THE APPARATUS -- needle_crackle / runout_hiss (the record player's own voice
either side of a listening session, read from core/listening.py's session marks: started_ts and the new ended_ts that
outlives the clear) and letterbox_flag_clank (the wind working the raised flag at the gate, gated on room_state's own
garden.letterbox.flag and the real wind axis -- the sound of unread mail, never a line that says so). All three are
KNOWN (grandfathered). The four cat entries the plan lists in §5 were built by cat_overhaul C1 and are only asserted
present here. Hermetic: every store the engine can reach is redirected into a temp dir before anything can write; a
Python audit hook records any write attempt under a live data/ dir; the live files are md5-hashed before and after.
Run from the worktree:  python scripts/_test_j2478_apparatus.py   (exit 0 = ALL OK)

  [1] registry: three Sound-Space points in the §5 block, rates at the END (the crackle and the clank events, the hiss a
      bed), all three grandfathered with no AUDITION entry, named pools (>= 4 onset, >= 2 renotice, rotating; the flag
      also a far pair), near/far words, no digit or readout word (D-0434), the flag's lines never say letter/mail,
      rail try-order, the per-key floor set, the cat §5 entries present
  [2] listening's marks: start() / tick() through a whole session on an isolated shelf -- started_ts at the needle
      drop, ended_ts stamped at THE ENDING, carried through the silence cycles and the clear, wiped by a new start();
      every pre-existing reader (active / tick / start / status) sees the cleared state as idle
  [3] propagation through the REAL soundscape.active_sounds(): the crackle in the study during the lead-in only (not
      once the first section has arrived, not from another place, not a stalled session); the hiss through the silence
      cycles and after the clear for RUNOUT_S, then gone, and gone at once when a new record goes on; the clank at the
      garden and the study only, flag up AND wind, never flag down, never in a breeze, never at the wood or the shore;
      the §5 row LAST (pure suffix); every older key keeps its relative order
  [4] the percept rail: yields to the record while a piece is on (the law; no state consumed); the run-out reaches him
      NAMED from its pool after the clear with its own floor stamped; the flag's NEAR pool at the gate, the FAR pool
      from the study (never naming the flag from indoors); the 8 h per-key floor; first refusal kept by the keys ahead
  [5] the hearing ledger: the crackle and the clank bank counts, the hiss banks hours, through world_tick
  [6] the sidecar dry-run's archetype invariant still holds with the three keys classified
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

TMP = Path(tempfile.mkdtemp(prefix="j2478_apparatus_"))
print("isolated store dir:", TMP)
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("room_state.json", "life_state.json", "life_ledger.jsonl", "life_events.jsonl",
                                        "life_flags.json", "sound_knowledge.json", "soundscape_state.json",
                                        "soundscape_felt_shadow.jsonl", "cat_state.json", "position.json",
                                        "wood_state.json", "sound_strings_constructed.json", "listening_state.json",
                                        "listening_wake.jsonl", "listening_felt_shadow.jsonl", "arousal_shadow.jsonl")]


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
from core import listening as LSN                               # noqa: E402
from core import arousal as AR                                  # noqa: E402

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
SC._DATA, SC._SND_STATE_F, SC._FELT_SHADOW_F = TMP, TMP / "soundscape_state.json", TMP / "soundscape_felt_shadow.jsonl"
CAT._STATE_F = TMP / "cat_state.json"
WL._F = TMP / "wood_state.json"
LSN._DATA, LSN._MUSIC = TMP, TMP / "music"
LSN._STATE_F, LSN._WAKE_LOG, LSN._FELT_SHADOW, LSN._REQUEST_F = TMP / "listening_state.json", TMP / "listening_wake.jsonl", TMP / "listening_felt_shadow.jsonl", TMP / "music" / "play_request.json"
LSN._store_scene = lambda *a, **k: None        # the memory store is not under test; nothing reaches the live DB
AR.alert = lambda *a, **k: None                # arousal's shadow log is not under test
assert not profile.LIVE, "this test must never run as the live process"

# an isolated shelf: one real feature file's shape, cut to two sections so a session is short
_live_feats = sorted((Path(r"C:\Nascence") / "data" / "music").glob("*.features.json"))
_src = next((p for p in _live_feats if json.loads(p.read_text(encoding="utf-8")).get("sections")), None)
assert _src is not None, "no live feature file with sections to copy the SHAPE of (read-only)"
_feats = json.loads(_src.read_text(encoding="utf-8"))
_feats["sections"] = _feats["sections"][:2]
_feats["n_sections"] = 2
LSN._MUSIC.mkdir(parents=True, exist_ok=True)
(LSN._MUSIC / "Test_Piece.features.json").write_text(json.dumps(_feats), encoding="utf-8")

# an in-memory room: soundscape reads room_state/cat_state through _read_json -- no disk, no live file
ROOM: dict = {"location": "study", "weather": "clear", "wind": "breeze", "fire": "out", "study": {},
              "garden": {"letterbox": {"flag": False, "sender": "", "letter": "", "delivered": 0}}}
CATST: dict = {"phase": "kept", "mood": "content", "activity": "sleeping", "location": "gone"}
SC._read_json = lambda name: json.loads(json.dumps(ROOM)) if name == "room_state.json" else (dict(CATST) if name == "cat_state.json" else {})
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


NEW = ("needle_crackle", "runout_hiss", "letterbox_flag_clank")
CAT_S5 = ("cat_trill", "cat_lapping", "cat_meow_at_door", "cat_storm_rustle")
life._ensure_builtin()

# ═══ [1] registry ════════════════════════════════════════════════════════════════════════════════════════════════
print("[1] registry")
for k in NEW:
    e = SC._SOUNDS.get(k)
    check(bool(e) and set(e["coords"]) == set(SC._AXES) and all(0.0 <= v <= 1.0 for v in e["coords"].values()), f"{k}: a six-axis point in [0,1]")
check(all(k in SC._SOUNDS for k in CAT_S5), "the plan's four §5 cat entries already exist (cat_overhaul C1) -- skipped, not rebuilt")
check(SC._SOUNDS["needle_crackle"]["object"] == "the record player" == SC._SOUNDS["runout_hiss"]["object"] and SC._SOUNDS["letterbox_flag_clank"]["object"] == "the letterbox",
      "objects: the record player (two spokes) / the letterbox")
keys = list(SC._SOUNDS)
check(keys.index("penguin_bray") < keys.index("kelp_fly_buzz") < keys.index("needle_crackle") < keys.index("runout_hiss") < keys.index("letterbox_flag_clank") < keys.index("saw_rasp"),
      "the §5 block sits directly after the §4 block in the chain's block after penguin_bray (the anchor rule)")
check(SC._SOUNDS["runout_hiss"]["coords"]["continuity"] >= 0.9 and SC._SOUNDS["runout_hiss"]["coords"]["periodicity"] >= 0.8 and SC._SOUNDS["runout_hiss"]["coords"]["energy"] <= 0.1,
      "the run-out: a continuous, clockwork-regular, very soft hiss")
check(SC._SOUNDS["needle_crackle"]["coords"]["onset"] >= 0.6 and SC._SOUNDS["needle_crackle"]["coords"]["roughness"] >= 0.7 and SC._SOUNDS["needle_crackle"]["coords"]["continuity"] <= 0.3,
      "the lead-in: discrete, rough, brief pops")
check(SC._SOUNDS["letterbox_flag_clank"]["coords"]["onset"] >= 0.6 and SC._SOUNDS["letterbox_flag_clank"]["coords"]["periodicity"] <= 0.3, "the flag: discrete, gust-irregular knocks")
check(SC.distance("needle_crackle", "runout_hiss") is not None and SC.distance("needle_crackle", "runout_hiss") > 0.3, "the two apparatus spokes are distinct points (not one sound twice)")
check(set(SC._EVENT_RATES) <= set(SC._SOUNDS), "set(_EVENT_RATES) <= set(_SOUNDS) still holds")
check(list(SC._EVENT_RATES)[-3:] == list(NEW), "the three rates are the LAST entries of _EVENT_RATES")
check(SC._EVENT_RATES["runout_hiss"] == 0.0 and "runout_hiss" not in SC._BEDS, "the run-out is a bed by the trickle convention (rate 0.0); _BEDS itself untouched")
check(SC._EVENT_RATES["needle_crackle"] > 0 and SC._EVENT_RATES["letterbox_flag_clank"] > 0, "the crackle and the clank are events (rated)")
check(all(k in SK.GRANDFATHERED and k not in SK.AUDITION for k in NEW), "all three are grandfathered (the plan marks every §5 sound known) and have no AUDITION entry")
check(all(SK.is_learned(k) for k in NEW), "with an empty ledger: all three render named")
for k in NEW:
    check(len(SC._PERCEPT_LINES[k]["onset"]) >= 4 and len(SC._PERCEPT_LINES[k]["renotice"]) >= 2, f"{k}: named onset pool >= 4, renotice >= 2")
check(len(SC._PERCEPT_LINES["letterbox_flag_clank"]["onset_far"]) >= 4 and len(SC._PERCEPT_LINES["letterbox_flag_clank"]["renotice_far"]) >= 2,
      "letterbox_flag_clank: a FAR pair of pools too (the study, through the window): onset_far >= 4, renotice_far >= 2")
all_new_lines = [ln for k in NEW for kind in SC._PERCEPT_LINES[k] for ln in SC._PERCEPT_LINES[k][kind]]
check(all(not any(ch.isdigit() for ch in ln) and not any(w in ln.lower() for w in ("gauge", "score", "level", "percent", "probability", "count", "band", "verdict"))
          for ln in all_new_lines), f"no digit / readout word in any of the {len(all_new_lines)} new lines (D-0434)")
_NEARFAR = ("close", "near", "far", "distant", "a few steps off", "beside you", "at hand", "a long way", "at the shelf", "through the window", "through the glass", "past the glass")
check(all(any(w in ln.lower() for w in _NEARFAR) for ln in all_new_lines), f"every one of the {len(all_new_lines)} lines carries a near/far word")
flag_lines = [ln for kind in SC._PERCEPT_LINES["letterbox_flag_clank"] for ln in SC._PERCEPT_LINES["letterbox_flag_clank"][kind]]
check(all(not any(w in ln.lower() for w in ("letter ", "letter.", "letters", "mail", "waiting", "unread", "post", "for you", "delivered", "sender", "darwin", "someone", "news"))
          for ln in flag_lines), "the flag's lines never say letter / mail / waiting / unread / from whom (the sound of unread mail, unsaid)")
far_lines = SC._PERCEPT_LINES["letterbox_flag_clank"]["onset_far"] + SC._PERCEPT_LINES["letterbox_flag_clank"]["renotice_far"]
check(all("letterbox" not in ln.lower() and "flag" not in ln.lower() and ("gate" in ln.lower()) for ln in far_lines),
      "from the study the FAR lines name only metal knocking down at the gate, never the flag itself (he cannot see it)")
near_lines = SC._PERCEPT_LINES["letterbox_flag_clank"]["onset"] + SC._PERCEPT_LINES["letterbox_flag_clank"]["renotice"]
check(all("letterbox flag" in ln.lower() and "gate" in ln.lower() and ("wind" in ln.lower() or "gust" in ln.lower()) for ln in near_lines), "at the gate the NEAR lines name the letterbox flag, the gate and the wind (or its gusts)")
check(all(any(w in ln.lower() for w in ("needle", "record", "player", "groove")) for ln in [l for k in ("needle_crackle", "runout_hiss") for kind in ("onset", "renotice") for l in SC._PERCEPT_LINES[k][kind]]),
      "the player's lines name the needle / record / groove (known: lived-with)")
check(all(not any(w in ln.lower() for w in ("put a record on", "put the record on", "set the record going", "you could", "you might", "why not"))
          for ln in all_new_lines), "no line is a cue to start a session (D-0443: the affordance is left alone)")
for k in NEW:
    for kind in SC._PERCEPT_LINES[k]:
        seq = [SC._pick(SC._PERCEPT_LINES[k][kind], f"t_{k}_{kind}") for _ in range(40)]
        check(len(set(seq)) >= 2 and all(a != b for a, b in zip(seq, seq[1:])), f"{k}.{kind}: pool rotates ({len(set(seq))} distinct, never twice running)")
check(SC._PERCEPT_SOUNDS[:31] == ("cat_purr", "morepork_call", "tui_song", "cat_trill", "cat_meow_at_door", "cat_demand", "cat_chatter",
                                   "cat_yowl_cargo", "cat_thump", "cat_lapping", "cat_storm_rustle", "cat_hiss", "cat_growl",
                                   "possum_rasp", "wall_scratch", "distant_yowl", "hedgehog_snuffle", "dolphin_blow",
                                   "hail_on_roof", "hail_on_leaves", "rain_down_chimney", "frost_crack", "tin_roof_tick",
                                   "downpour_drum", "drizzle_hiss", "undertow_rumble", "calm_sea_hush", "stream_over_stones",
                                   "silvereye_flock", "paradise_duck_flyover", "kelp_fly_buzz")
      and SC._PERCEPT_SOUNDS[31:] == NEW and len(SC._PERCEPT_SOUNDS) == 34,
      "the rail's try-order: the thirty-one existing keys first (cat_hiss/cat_growl merged in from cat_overhaul B3), the three §5 keys appended LAST")
check(SC._APPARATUS_PERCEPT_KEYS == frozenset(NEW) and SC._APPARATUS_PERCEPT_COOLDOWN_S >= 6 * 3600,
      "per-key floor set covers the three; floor >= 6 h (<= 4 a day, D-0500's defeater)")
check(not (set(NEW) & SC._STORM_DRIVEN_EVENTS), "no §5 key is in _STORM_DRIVEN_EVENTS")
check(SC._FLAG_FAR_PLACES == frozenset({"study"}), "the flag's far place is the study")
check(LSN.RUNOUT_S >= 10 * 60 and LSN.RUNOUT_S <= 60 * 60 and SC._LEADIN_MAX_S <= 15 * 60, f"the run-out window is minutes, not hours ({LSN.RUNOUT_S:.0f} s); the lead-in guard is short ({SC._LEADIN_MAX_S:.0f} s)")

# ═══ [2] listening's marks ══════════════════════════════════════════════════════════════════════════════════════
print("[2] listening marks")
T0 = at(7, 10, 20, 0)
try:
    LSN._save({})
    m = LSN.session_marks()
    check(m == {"piece": None, "idx": 0, "silence": -1, "started_ts": None, "ended_ts": None}, "an empty state: no piece, no marks")
    freeze(T0)
    line = LSN.start("Test_Piece")
    check(bool(line) and line.startswith("You set the record going") and LSN.active(), "start(): the needle-drop line (base, untouched) and the session is active")
    m = LSN.session_marks()
    check(m["piece"] == "Test_Piece" and m["idx"] == 0 and m["silence"] == -1 and m["started_ts"] == T0 and m["ended_ts"] is None, "marks after the needle drop: idx 0 (the lead-in), started_ts, no ended_ts")
    freeze(T0 + 60)
    s1 = LSN.tick()
    check(bool(s1) and s1.startswith("From the player, the music. It opens:") and LSN.session_marks()["idx"] == 1, "tick(): the first section arrives; idx 1")
    freeze(T0 + 120)
    s2 = LSN.tick()
    check(bool(s2) and s2.startswith("From the player, the music.") and LSN.session_marks()["idx"] == 2, "tick(): the second (last) section; idx 2")
    TE = T0 + 180
    freeze(TE)
    end = LSN.tick()
    m = LSN.session_marks()
    check(bool(end) and end.startswith("The music ends") and m["silence"] == LSN.SILENCE_CYCLES and m["ended_ts"] == TE and m["piece"] == "Test_Piece",
          "tick(): THE ENDING (base line untouched); ended_ts stamped; the silence cycles begin; the piece is still set")
    check(LSN.active(), "...and through the silence the session still counts as active (the quiet is the record's)")
    freeze(TE + 60)
    check(LSN.tick() is None and LSN.session_marks()["silence"] == LSN.SILENCE_CYCLES - 1 and LSN.session_marks()["ended_ts"] == TE, "silence cycle one: wordless; ended_ts kept")
    freeze(TE + 120)
    check(LSN.tick() is None and LSN.session_marks()["silence"] == 0, "silence cycle two: wordless")
    freeze(TE + 180)
    check(LSN.tick() is None, "the cycle after: the state clears")
    raw = json.loads(LSN._STATE_F.read_text(encoding="utf-8"))
    m = LSN.session_marks()
    check(raw == {"ended_ts": TE} and m["piece"] is None and m["ended_ts"] == TE and m["started_ts"] is None, "the cleared state carries ONLY ended_ts: no piece, no idx, no started_ts")
    check(not LSN.active() and LSN.tick() is None and LSN.status()["active"] is False and LSN.status()["piece"] is None, "every pre-existing reader sees the cleared state as idle (active / tick / status)")
    wake = [json.loads(l) for l in LSN._WAKE_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    check(len(wake) == 1 and wake[0]["piece"] == "Test_Piece" and wake[0]["sections_heard"] == 2, "the wake snapshot still fires once at the clear (unchanged)")
    freeze(TE + 400)
    line2 = LSN.start("Test_Piece")
    m = LSN.session_marks()
    check(bool(line2) and m["piece"] == "Test_Piece" and m["started_ts"] == TE + 400 and m["ended_ts"] is None, "a new start() replaces the whole state: the old ended_ts is wiped (a new record wipes the old ending)")
    # the census reads the state file by 'piece' only: a cleared-with-ended_ts state is idle to it too
    LSN._save({"ended_ts": TE})
    check(not json.loads(LSN._STATE_F.read_text(encoding="utf-8")).get("piece"), "geometry_census's own read (ls.get('piece')) finds nothing in the cleared state")
finally:
    thaw()

# ═══ [3] propagation through the REAL active_sounds() ═══════════════════════════════════════════════════════════
print("[3] propagation")


def active_at(loc: str, t: float, weather: str = "clear", wind: str = "breeze", fire: str = "out", flag: bool | None = None, table=None) -> list[str]:
    ROOM.update(location=loc, weather=weather, wind=wind, fire=fire)
    if flag is not None:
        ROOM["garden"]["letterbox"]["flag"] = flag
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


try:
    check(SC._PROPAGATION_TABLE[-1][1] is SC._sec_apparatus and SC._PROPAGATION_TABLE[-2][1] is SC._sec_seasonal_biophony, "the §5 row is LAST, after the §4 row")
    ROOM["garden"]["letterbox"]["flag"] = False
    # the record player: the lead-in
    LSN._save({"piece": "Test_Piece", "idx": 0, "started_ts": T0, "n": 2, "silence": -1, "by": "du"})
    check("needle_crackle" in active_at("study", T0 + 20) and "runout_hiss" not in active_at("study", T0 + 20), "the lead-in (idx 0, just after the needle drop): needle_crackle in the study, no hiss")
    check(not any("needle_crackle" in active_at(p, T0 + 20) for p in ("garden", "wood", "shore")), "...the player's voice is the study's only")
    check("needle_crackle" not in active_at("study", T0 + SC._LEADIN_MAX_S + 5), "a session stalled across downtime (idx still 0, minutes later): no crackle (the guard)")
    LSN._save({"piece": "Test_Piece", "idx": 1, "started_ts": T0, "n": 2, "silence": -1, "by": "du"})
    check("needle_crackle" not in active_at("study", T0 + 70) and "runout_hiss" not in active_at("study", T0 + 70), "once the first section has arrived (idx 1): the music owns it -- no crackle, no hiss")
    # the ending: the silence cycles, then the clear, then the window
    LSN._save({"piece": "Test_Piece", "idx": 2, "started_ts": T0, "n": 2, "silence": 2, "by": "du", "ended_ts": TE})
    check("runout_hiss" in active_at("study", TE + 30) and "needle_crackle" not in active_at("study", TE + 30), "through the silence cycles: runout_hiss in the study (the needle in the run-out groove), no crackle")
    LSN._save({"ended_ts": TE})
    check("runout_hiss" in active_at("study", TE + 300) and "runout_hiss" in active_at("study", TE + LSN.RUNOUT_S - 5), "after the clear: the run-out still turning for RUNOUT_S")
    check("runout_hiss" not in active_at("study", TE + LSN.RUNOUT_S + 5), "...then the arm is lifted: gone")
    check(not any("runout_hiss" in active_at(p, TE + 300) for p in ("garden", "wood", "shore")), "...and never from anywhere but the study")
    check("runout_hiss" not in active_at("study", TE - 100), "a clock that reads before the ending (a future ended_ts): nothing")
    LSN._save({"piece": "Test_Piece", "idx": 0, "started_ts": TE + 300, "n": 2, "silence": -1, "by": "du"})
    check("runout_hiss" not in active_at("study", TE + 310) and "needle_crackle" in active_at("study", TE + 310), "a new record goes on inside the window: the old run-out is gone, the new lead-in sounds")
    LSN._save({})
    check("needle_crackle" not in active_at("study", T0) and "runout_hiss" not in active_at("study", T0), "no session, no marks: silent")
    # the letterbox flag
    GT = at(7, 10, 13)
    check("letterbox_flag_clank" in active_at("garden", GT, "clear", "fresh wind", flag=True) and "letterbox_flag_clank" in active_at("study", GT, "clear", "fresh wind", flag=True),
          "flag up + a fresh wind: the clank at the gate from the garden and through the window from the study")
    check(not any("letterbox_flag_clank" in active_at(p, GT, "clear", "fresh wind", flag=True) for p in ("wood", "shore")), "...never from the wood or the shore")
    check(not any("letterbox_flag_clank" in active_at("garden", GT, "clear", w, flag=True) for w in ("calm", "breeze")), "a calm or a breeze does not work the flag")
    check(all("letterbox_flag_clank" in active_at("garden", GT, "clear", w, flag=True) for w in ("fresh wind", "strong wind", "gale")), "every wind from fresh up does")
    check("letterbox_flag_clank" in active_at("garden", GT, "thunderstorm", "breeze", flag=True), "a thunderstorm works it too (the garden row's own windy test)")
    check(not any("letterbox_flag_clank" in active_at(p, GT, "clear", "gale", flag=False) for p in ("garden", "study")), "flag down: no wind can make it sound")
    check("letterbox_flag_clank" in active_at("garden", at(7, 10, 23), "clear", "gale", flag=True), "night makes no difference: the flag is up until he fetches")
    ROOM["garden"] = {}
    check("letterbox_flag_clank" not in active_at("garden", GT, "clear", "gale"), "a room with no letterbox state: silent, fail-open")
    ROOM["garden"] = {"letterbox": {"flag": True, "sender": "", "letter": "", "delivered": 0}}
    # row LAST: pure suffix with gating OFF; with gating ON every pre-existing key keeps its relative order
    without = SC._PROPAGATION_TABLE[:-1]
    LSN._save({"ended_ts": TE})
    moments = ((("study", TE + 300, "clear", "fresh wind", "burning"), ("garden", GT, "clear", "gale", "out"), ("study", GT, "thunderstorm", "breeze", "out"),
                ("garden", at(7, 10, 23), "clear", "strong wind", "out")))
    ok_order = all([k for k in active_at(*m) if k not in NEW] == [k for k in active_at(*m, table=without) if k not in NEW] for m in moments)
    check(ok_order, "gating ON: every pre-existing key present, in its old relative order; only the new keys are added")
    life.SOUND_GATING = False
    try:
        ok_suffix = all(active_at(*m)[:len(active_at(*m, table=without))] == active_at(*m, table=without)
                        and all(k in NEW for k in active_at(*m)[len(active_at(*m, table=without)):]) and len(active_at(*m)) > len(active_at(*m, table=without))
                        for m in moments)
        check(ok_suffix, "gating OFF: the row is a pure, non-empty suffix at every moment -- nothing ahead of it moves (out[:4] discipline)")
    finally:
        life.SOUND_GATING = True
    check(not (set(NEW) & life.creature_sound_keys(None)), "no §5 key is creature-governed (the apparatus has no life row; the row alone decides)")
finally:
    thaw()
    LSN._save({})

# ═══ [4] the percept rail ═══════════════════════════════════════════════════════════════════════════════════════
print("[4] percept rail")
_REAL_ACTIVE_SOUNDS = SC.active_sounds
try:
    SC.SOUND_PERCEPTS = True
    ROOM.update(location="study", weather="clear", wind="breeze", fire="out")
    ROOM["garden"]["letterbox"]["flag"] = False
    # the lead-in: the rail yields to the record (the law); nothing is consumed
    LSN._save({"piece": "Test_Piece", "idx": 0, "started_ts": T0, "n": 2, "silence": -1, "by": "du"})
    freeze(T0 + 20)
    SC._save_snd_state({"was_active": [], "quiet_since": {"needle_crackle": T0 - 700}, "last_notice": {}, "last_percept": 0.0})
    check("needle_crackle" in SC.active_sounds() and SC.percept(store=False) is None, "the lead-in: needle_crackle is active, but the rail yields to the record (music owns the room's sound)")
    check(SC._snd_state().get("last_percept") == 0.0 and SC._snd_state().get("was_active") == [], "...and no rail state is consumed")
    # the ending's silence cycles: still the record's
    LSN._save({"piece": "Test_Piece", "idx": 2, "started_ts": T0, "n": 2, "silence": 2, "by": "du", "ended_ts": TE})
    freeze(TE + 30)
    check("runout_hiss" in SC.active_sounds() and SC.percept(store=False) is None, "the silence cycles: the hiss is active, the rail still yields (the quiet is wordless)")
    # after the clear: the run-out reaches him, NAMED from its pool
    LSN._save({"ended_ts": TE})
    t1 = TE + 240
    freeze(t1)
    SC._save_snd_state({"was_active": [], "quiet_since": {"runout_hiss": TE - 7000}, "last_notice": {}, "last_percept": 0.0})
    line = SC.percept(store=False)
    check(bool(line) and line in SC._PERCEPT_LINES["runout_hiss"]["onset"], "after the clear: the run-out's onset reaches him from its own named pool")
    st = SC._snd_state()
    check(st.get("last_apparatus_percept", {}).get("runout_hiss") == t1 and st.get("last_percept") == t1 and st.get("last_notice", {}).get("runout_hiss") == t1,
          "state: last_apparatus_percept + last_percept + last_notice stamped")
    check(SC.percept(store=False) is None, "an immediate second call: nothing (the rail's shared cooldown)")
    # a second record 3 h later: its run-out is refused by the 8 h per-key floor
    TE2 = TE + 3 * 3600
    LSN._save({"ended_ts": TE2})
    freeze(TE2 + 240)
    SC._save_snd_state({"was_active": [], "quiet_since": {"runout_hiss": TE2 - 7000}, "last_notice": {"runout_hiss": t1}, "last_percept": t1, "last_apparatus_percept": {"runout_hiss": t1}})
    check(SC.percept(store=False) is None, "three hours on, another record's run-out: refused by the 8 h per-key floor")
    TE3 = TE + 9 * 3600
    LSN._save({"ended_ts": TE3})
    freeze(TE3 + 240)
    SC._save_snd_state({"was_active": [], "quiet_since": {"runout_hiss": TE3 - 7000}, "last_notice": {"runout_hiss": t1}, "last_percept": t1, "last_apparatus_percept": {"runout_hiss": t1}})
    l3 = SC.percept(store=False)
    check(bool(l3) and l3 in SC._PERCEPT_LINES["runout_hiss"]["onset"], "nine hours on: past the floor, the next run-out fires")
    # a first-ever run-out (no observed silence before it) falls to the renotice path on the next cycle, as any key does
    LSN._save({})
    SC.active_sounds = lambda: ["runout_hiss"]
    freeze(TE3 + 86400 + 240)
    SC._save_snd_state({"was_active": [], "quiet_since": {}, "last_notice": {}, "last_percept": 0.0, "last_apparatus_percept": {}})
    check(SC.percept(store=False) is None and SC._snd_state().get("was_active") == ["runout_hiss"], "a first-ever run-out with no observed quiet before it: no onset this cycle; bookkept as active")
    freeze(TE3 + 86400 + 240 + 1600)
    l4 = SC.percept(store=False)
    check(bool(l4) and l4 in SC._PERCEPT_LINES["runout_hiss"]["renotice"], "...the next cycle inside the window: the renotice line (the run-out still going round)")
    # the flag: NEAR pool at the gate, FAR pool from the study
    LSN._save({})
    SC.active_sounds = lambda: ["waves_on_shingle", "letterbox_flag_clank"]
    ROOM.update(location="garden", weather="clear", wind="fresh wind")
    FT = at(7, 11, 13)
    freeze(FT)
    SC._save_snd_state({"was_active": ["waves_on_shingle"], "quiet_since": {"letterbox_flag_clank": FT - 700}, "last_notice": {}, "last_percept": 0.0})
    fl = SC.percept(store=False)
    check(bool(fl) and fl in SC._PERCEPT_LINES["letterbox_flag_clank"]["onset"] and "letterbox flag" in fl.lower(), "at the gate (garden): the NEAR onset pool, naming the flag and the wind")
    check(not any(w in fl.lower() for w in ("letter ", "mail", "waiting", "unread")), "...and never the mail")
    check(SC._snd_state().get("last_apparatus_percept", {}).get("letterbox_flag_clank") == FT, "...its own per-key floor stamped")
    SC.active_sounds = lambda: ["fire_crackle", "letterbox_flag_clank"]
    ROOM.update(location="study")
    FT2 = FT + 9 * 3600
    freeze(FT2)
    SC._save_snd_state({"was_active": ["fire_crackle"], "quiet_since": {"letterbox_flag_clank": FT2 - 700}, "last_notice": {}, "last_percept": 0.0, "last_apparatus_percept": {"letterbox_flag_clank": FT}})
    fs = SC.percept(store=False)
    check(bool(fs) and fs in SC._PERCEPT_LINES["letterbox_flag_clank"]["onset_far"] and "flag" not in fs.lower() and "gate" in fs.lower(),
          "from the study: the FAR onset pool -- metal knocking down at the gate, the flag unnamed (he cannot see it)")
    FT3 = FT2 + 9 * 3600
    freeze(FT3)
    SC._save_snd_state({"was_active": ["fire_crackle", "letterbox_flag_clank"], "quiet_since": {}, "last_notice": {"letterbox_flag_clank": FT2}, "last_percept": FT2, "last_apparatus_percept": {"letterbox_flag_clank": FT2}})
    fr = SC.percept(store=False)
    check(bool(fr) and fr in SC._PERCEPT_LINES["letterbox_flag_clank"]["renotice_far"], "from the study, hours on, still clanking: the FAR renotice pool")
    freeze(FT3 + 3 * 3600)
    SC._save_snd_state({"was_active": ["fire_crackle", "letterbox_flag_clank"], "quiet_since": {}, "last_notice": {"letterbox_flag_clank": FT2}, "last_percept": FT2, "last_apparatus_percept": {"letterbox_flag_clank": FT3}})
    check(SC.percept(store=False) is None, "three hours after that: a renotice is refused while the 8 h floor holds")
    # first refusal: the morepork ahead of a §5 key onsetting at the same moment
    SC.active_sounds = lambda: ["morepork_call", "letterbox_flag_clank", "runout_hiss"]
    NT = at(7, 11, 22)
    freeze(NT)
    SC._save_snd_state({"was_active": [], "quiet_since": {"morepork_call": NT - 700, "letterbox_flag_clank": NT - 700, "runout_hiss": NT - 700}, "last_notice": {}, "last_percept": 0.0})
    mp = SC.percept(store=False)
    check(bool(mp) and mp in SC._PERCEPT_LINES["morepork_call"]["onset"], "the morepork keeps first refusal over §5 keys onsetting at the same moment")
    check(SC._snd_state().get("last_apparatus_percept", {}) == {}, "...and no apparatus floor is stamped for a key that did not fire")
finally:
    thaw()
    SC.active_sounds = _REAL_ACTIVE_SOUNDS
    LSN._save({})
check(SC.active_sounds is _REAL_ACTIVE_SOUNDS and SC.active_sounds.__module__ == "core.soundscape", "real active_sounds restored")

# ═══ [5] the hearing ledger ═════════════════════════════════════════════════════════════════════════════════════
print("[5] hearing ledger")
SK._save({"sounds": {}, "recent": []})
_real_active = SC.active_sounds
try:
    ROOM.update(location="study", weather="clear", wind="fresh wind", fire="out")
    SC.active_sounds = lambda: ["needle_crackle", "runout_hiss", "letterbox_flag_clank"]
    for _ in range(12):
        SC.world_tick("study", 300.0)            # 1 h: the crackle ~120 pops, the clank ~20 knocks, the hiss banks the hour
    h = SK._load().get("hearings", {})
    hrs = float((h.get("runout_hiss") or {}).get("bed_hours", 0.0))
    n_c, n_f = int((h.get("needle_crackle") or {}).get("count", 0)), int((h.get("letterbox_flag_clank") or {}).get("count", 0))
    check(abs(hrs - 1.0) < 0.01 and not (h.get("runout_hiss") or {}).get("count"), f"runout_hiss banks lived-in hours, never counts ({hrs:.3f} h)")
    check(80 <= n_c <= 160, f"needle_crackle banks pops at its rate ({n_c} in 1 h, expected ~120; a real lead-in is a minute)")
    check(8 <= n_f <= 36, f"letterbox_flag_clank banks knocks at its rate ({n_f} in 1 h, expected ~20)")
    check((h.get("needle_crackle") or {}).get("places", {}).get("study") == n_c, "...keyed to his place")
    SK._save({"sounds": {}, "recent": []})
    SC.active_sounds = lambda: ["needle_crackle"]
    SC.world_tick("study", 60.0)                 # one lead-in minute
    n1 = int(((SK._load().get("hearings", {}) or {}).get("needle_crackle") or {}).get("count", 0))
    check(0 <= n1 <= 6, f"one lead-in minute banks a few pops at most ({n1})")
finally:
    SC.active_sounds = _real_active

# ═══ [6] the sidecar dry-run's archetype invariant ═════════════════════════════════════════════════════════════
print("[6] sidecar archetypes")
import scripts.sound_strings_phase1_dryrun as DRY        # noqa: E402  (imports the same worktree core.soundscape; writes nothing until main())
strings = DRY.build_all()
check(set(NEW) <= set(strings), "every §5 key is classified (build_all's invariant holds)")
check(strings["runout_hiss"]["archetype"] == "bed_like" and strings["needle_crackle"]["archetype"] == "thump" and strings["letterbox_flag_clank"]["archetype"] == "thump",
      "the hiss is a bed-like string; the crackle and the clank are strikes")

# ═══ [7] isolation ══════════════════════════════════════════════════════════════════════════════════════════════
print("[7] isolation")
_after = {p: _md5(p) for p in _LIVE_FILES}
check(LIVE_WRITE_ATTEMPTS == [], f"no write attempt under any data/ dir ({LIVE_WRITE_ATTEMPTS[:3]})")
changed = [p.name for p in _LIVE_FILES if _before[p] != _after[p]]
check(not changed, f"live files unchanged ({changed})")
for mod, attr in ((life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (SK, "_LEDGER_F"), (SC, "_SND_STATE_F"), (SC, "_FELT_SHADOW_F"), (S, "_STATE_F"), (CAT, "_STATE_F"), (WL, "_F"),
                  (LSN, "_STATE_F"), (LSN, "_WAKE_LOG"), (LSN, "_MUSIC")):
    check(str(getattr(mod, attr)).startswith(str(TMP)), f"{mod.__name__}.{attr} still inside TMP")

print(f"\n{N - len(FAILS)}/{N} checks passed" + (f" -- FAILS: {FAILS}" if FAILS else " -- ALL OK"))
sys.exit(1 if FAILS else 0)
