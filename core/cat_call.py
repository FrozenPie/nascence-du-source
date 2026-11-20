"""
core/cat_call.py — HIS CALL: calling her is its own hand, carried to her, her decision, a sound-first answer
=========================================================================================================
2026-10-28 (docs/staged/cat_overhaul.md Part C3 steps 1-5; D-0499 "open D-1..D-4 and build"; D-0505 (c): the
name is a learned sound with range; J-2468; built on J-2465's legs and J-2467's hearing). Until now `call`
sat in the cat action's verbs (core/actions.py) but landed in cat.react() as a TEND verb ("call to") — calling
her was a stroke, and it only ever fired when she was already where he was. Now it is its own hand, cat.call():

  1. THE CALL IS A SELF-SOUND (expression class: a voice, no grade, discharge — core/expression.py's own
     law) with a target and a REACH from his position: what he called ("puss-puss", the kissing noise, or
     her name — the R1 act, cat.react's naming latch), the house wall, the weather (cat_sounds.carry, the
     C1 law run in reverse: his position is the origin, hers the observer). soundscape sees it as the
     "cat_call" point on object "his own voice" for the window it sounds (active_sounds / the census), the
     way his footsteps and the gate latch already are.
  2. CARRY to her, through HER hearing gate: asleep-deep low, dozing some, awake yes, in transit yes,
     hunting far none, storm none, gone none. A call that does not reach her is a call that did not reach
     her — nothing records it anywhere she is.
  3. HER DECISION, hers: bond, hunger (a hungry cat comes fast), satiety (handled for the fifth time this
     hour -> she ignores it; cat.react's own budget), mood (aloof answers with a sound and does not move;
     afraid -> nothing), the tom present (B3's hook, J-2470: cat_state "tom": {"present": true}) -> no.
  4. THE ANSWER COMES BACK AS SOUND FIRST: she stamps call.answered_ts and core/cat_sounds emits cat_trill
     from HER state (the same one-shot law as the greeting) — carried to him by position, so "from the
     garden, a rising chirrup" reaches him before she does. Then she moves on her own legs (cat._depart
     via cat_ears._begin, a reaction with its own hold) and arrives with the greeting (presence_line reads
     call.answered_ts exactly as it reads ears.gate_ts). Or silence, honestly: the line says only what he
     did and what he heard.
  5. THE NAME IS A LEARNED SOUND WITH RANGE (D-0505 (c), D-5): "puss-puss" and the kissing noise are sounds
     she knows (him) and work at short range only. A name, once given, she LEARNS: each time she is called
     by it and comes, or is fed within NAME_FED_WINDOW_S after, name_recognition on cat_state rises; past
     NAME_LEARNED_AT the name reaches her at range (study -> the wood's edge, ~90 m on the chain frame)
     where "puss-puss" never does. NOTHING TELLS HIM ANY OF THIS (D-0434, world answers, never leads): he
     finds that the far call fails and the near one works. No line here carries a number, a band, a
     reason, or the word "recognition".

INSTRUMENT. Every call — heard or not, answered or not — is one row in data/cat_call_ledger.jsonl
(call, what, by_name, heard, answered, came, with the carry and her state), fenced (profile.guard_path),
rotated at _ROTATE_BYTES to one .1 generation. It is the R1 instrument too (how often he uses the name,
and whether the name ever starts to work). Read by the HUD and the read job only.

LIVE by default (D-0499: world content; C2's own reading), hot kill switch data/life_flags.json
{"cat_call_live": false} (scripts/life_flags.py cat_call off). Restart-gated: Du is down since 2026-10-20.

Zero LLM. Read-only toward every store but cat_state.json (through cat.state; cat.call saves) and its own
ledger. Fail-open everywhere: a call that cannot be computed is a call that went unanswered.
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.cat_call")

_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "cat_call_ledger.jsonl"
_FLAGS_F = _DATA / "life_flags.json"

LIVE = True                 # code default; hot override: life_flags.json cat_call_live (false = the hand is off)
_ROTATE_BYTES = 2_000_000   # the ledger rolls to cat_call_ledger.jsonl.1 past this (one generation kept)
_SOUND_WINDOW_S = 20.0      # how long his call counts as "sounding now" for soundscape (its own _ACT_RECENCY_S)

# ── what he can call, and how far each carries (metres, calm air, open ground) — HIS voice, not hers ─────
# "puss-puss" is a call, not a shout; the kissing noise is a near thing; a NAME is the one call he can really
# raise his voice on — it carries. Whether it REACHES her is a different question (KNOWN_REACH, NAME_LEARNED_AT).
CALLS = {
    "puss-puss":         {"reach": 30.0},
    "the kissing noise": {"reach": 10.0},
    "name":              {"reach": 130.0},   # study door -> the wood's edge is ~87 m on the chain frame; x0.7 (door open) still reaches
}
KNOWN_REACH = 30.0        # within this (cut by wall and weather like any sound) any sound of his is HIM to her
NAME_LEARNED_AT = 0.60    # name_recognition past this: the name reaches her at its full range
NAME_LEARN_COME = 0.15    # called by name and she came
NAME_LEARN_FED = 0.10     # called by name and fed within NAME_FED_WINDOW_S after
NAME_FED_WINDOW_S = 20 * 60

# her hearing gate (step 2): the share of calls that physically reach her which she actually HEARS
HEAR_P = {"awake": 1.0, "dozing": 0.75, "asleep": 0.5, "asleep_deep": 0.25, "transit": 1.0,
          "hunting_far": 0.0, "storm": 0.0, "gone": 0.0}
DEEP_SLEEP_ENERGY = 0.5   # asleep with energy below this is asleep-deep

# her decision (step 3)
COME_BASE = 0.20          # a kept cat with no bond to speak of
COME_BOND = 0.60          # + bond * this
COME_HUNGER = 0.30        # + this when hungry (a hungry cat comes, and fast)
HUNGRY_AT = 0.50          # body.hunger at or past this (or the legacy 5 h clock) is hungry
HUNGRY_LEG_FACTOR = 0.7   # her legs, hungry: the first leg shortened by this
SPENT_ENERGY = 0.30       # energy below this: she is less inclined to get up
SATIETY_N = 4             # cat.react's own budget: 4 handlings on record this hour -> the fifth is one too many
_SOUND_ONLY_MOODS = ("aloof", "aloof-but-near", "offhand", "wary")
_AFRAID_MOODS = ("afraid",)
_RESTING = ("sleeping", "dozing")

# the grammar: verbs (word-boundary, clause-scoped, blockers — core/hands.wants) and what counts as her
_CALL_VERBS = ("call out to", "call out for", "call to", "call for", "call out", "call", "whistle for", "whistle up")
_CALL_OBJECTS = ("cat", "kitten", "puss", "puss-puss", "kitty", "moggy", "stray")
_PUSS_RE = re.compile(r"\bpuss(?:[ -]puss)?\b|\bkitty(?:[ -]kitty)?\b")
_KISS_RE = re.compile(r"\bkiss\w*\b|\bclick\w*\b|\btut(?:s|ting)?\b|\btsk\w*\b|\bpss+\b|\bsmack\w*\b|\blips\b")
_BY_NAME_RE = re.compile(r"\b(?:by|her|the) name\b")

_mem: dict = {"last_call_ts": 0.0}
_flags_cache: dict = {"ts": 0.0, "v": {}}


# ── flags / io ────────────────────────────────────────────────────────────────────────────────────────────
def _flags() -> dict:
    now = time.time()
    if now - _flags_cache["ts"] < 10.0:
        return _flags_cache["v"]
    v = {}
    try:
        if _FLAGS_F.exists():
            v = json.loads(_FLAGS_F.read_text(encoding="utf-8")) or {}
    except Exception:
        v = {}
    _flags_cache["ts"], _flags_cache["v"] = now, v
    return v


def live_on() -> bool:
    v = _flags().get("cat_call_live")
    return bool(LIVE if v is None else v)


def _log(row: dict) -> None:
    path = profile.guard_path(_LEDGER)   # J-0733: real data/ only if this process is live; raises before any I/O if not (D-0179)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if path.exists() and path.stat().st_size > _ROTATE_BYTES:
                gen = path.with_name(path.name + ".1")
                if gen.exists():
                    gen.unlink()
                path.rename(gen)
        except Exception:
            pass
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[cat_call] ledger write failed (non-fatal): %s", exc)


# ── the grammar: is this thought a CALL, and what did he call ─────────────────────────────────────────────
def wants_call(txt: str, name: str = "", she_referred: bool = False) -> bool:
    """Does this (lowered) thought WILL a call to her? A call verb with a cat word, her name, or — only when
    she is already the referent of this thought or the one before (cat.react's own anaphora window) — a bare
    'her'. hands.wants applies the clause scope, the word boundaries, the determiner guard ("the morepork's
    call" is a noun) and the volition blockers, the same grammar every other hand reads."""
    try:
        from core import hands as _h
    except Exception:
        return False
    objects = list(_CALL_OBJECTS)
    if name:
        objects.append(name.lower())
    if she_referred:
        objects.append("her")
    return bool(_h.wants(txt, _CALL_VERBS, objects))


def what_called(txt: str, name: str = "") -> tuple[str, bool]:
    """(what, by_name): her name when his own words carry it (or 'by name' / 'her name' and she has one);
    'puss-puss' for puss / kitty; the kissing noise for a kiss, a click, a tut; 'puss-puss' when he does not
    say — the ordinary call. Never invents a name he has not given."""
    n = (name or "").strip().lower()
    if n and re.search(r"(?<![a-z-])" + re.escape(n) + r"(?![a-z-])", txt):
        return "name", True
    if n and _BY_NAME_RE.search(txt):
        return "name", True
    if _PUSS_RE.search(txt):
        return "puss-puss", False
    if _KISS_RE.search(txt):
        return "the kissing noise", False
    return "puss-puss", False


# ── the world around the call (each read fail-open, each replaceable in a test) ─────────────────────────
def _his_pos(his_place: str) -> tuple[str, list[float]]:
    """(standpoint, xyz in cat_sounds' chain frame) for the place he is calling FROM — the place is the
    caller's (sensorium's authority, passed in); the standpoint locomotion's (peek: no write)."""
    sp = "_"
    try:
        from core import locomotion as _loco
        sp = str(_loco.peek().get("standpoint") or "_")
    except Exception:
        sp = "_"
    try:
        from core import cat_sounds as _cs
        table = _cs._HIS.get(his_place) or _cs._HIS["study"]
        return sp, list(table.get(sp) or table["_"])
    except Exception:
        return sp, [0.0, 1.0, 0.0]


def _her_origin(state: dict) -> list[float] | None:
    """Her point in the chain frame: a fixed spot's _POS, or the midpoint of the leg she is on. None = off
    the map (gone) — a call to nowhere."""
    try:
        from core import cat_sounds as _cs
        if str(state.get("location") or "") == "in_transit":
            return _cs._transit_origin(state)
        return _cs._POS.get(str(state.get("location") or ""))
    except Exception:
        return None


def hearing(state: dict) -> str:
    """Her hearing gate label (HEAR_P's keys): what her own state does to a sound that physically reaches
    her. Hunting far: none (she is beyond the wall, in the long grass, on her own business); storm: none
    (pressed to the floor by thunder, nothing but the storm reaches her); gone: none."""
    loc, act = str(state.get("location") or ""), str(state.get("activity") or "")
    if loc == "gone" or act in ("missing", "slipped_away") or state.get("phase") in (None, "absent", "dead"):
        return "gone"   # D-2 (J-2471): a call to a dead cat is a call to nowhere — the silence pool answers, nothing tells him
    if act == "storm_hide":
        return "storm"
    if loc == "away_hunting" or act == "hunting":
        return "hunting_far"
    if loc == "in_transit":
        return "transit"
    if act == "sleeping":
        energy = float((state.get("body") or {}).get("energy", 0.6))
        return "asleep_deep" if energy < DEEP_SLEEP_ENERGY else "asleep"
    if act == "dozing":
        return "dozing"
    return "awake"


def name_learned(state: dict) -> bool:
    return float(state.get("name_recognition") or 0.0) >= NAME_LEARNED_AT


def _hungry(state: dict, now: float) -> bool:
    try:
        if float((state.get("body") or {}).get("hunger", 0.0)) >= HUNGRY_AT:
            return True
    except Exception:
        pass
    return (now - float(state.get("last_fed") or 0.0)) > 5 * 3600


def _handled_this_hour(state: dict, now: float) -> int:
    try:
        return len([t for t in state.get("_handled_ts", []) if now - float(t) < 3600])
    except Exception:
        return 0


def _tom_present(state: dict) -> bool:
    """B3's hook (J-2470): the tom in the garden is cat_state {"tom": {"present": true}} — inert until the
    tom is built; a key that does not exist is a tom that is not there."""
    t = state.get("tom")
    return bool(isinstance(t, dict) and t.get("present"))


# ── her decision (step 3) ─────────────────────────────────────────────────────────────────────────────────
def decide(state: dict, now: float, here: bool) -> tuple[str, str]:
    """('comes' | 'sound' | 'nothing', why). Hers: bond, hunger, satiety, mood, the tom. `here`: she is
    already where he is — then coming is coming over, and an aloof cat still answers in place."""
    if _tom_present(state):
        return "nothing", "the tom is there"
    mood = str(state.get("mood") or "")
    if mood in _AFRAID_MOODS:
        return "nothing", "afraid"
    if _handled_this_hour(state, now) >= SATIETY_N:
        return "nothing", "handled enough this hour"
    if mood in _SOUND_ONLY_MOODS:
        return "sound", "aloof: a sound, no move"
    bond = float(state.get("bond") or 0.0)
    hungry = _hungry(state, now)
    energy = float((state.get("body") or {}).get("energy", 0.6))
    p = COME_BASE + COME_BOND * bond + (COME_HUNGER if hungry else 0.0) - (0.2 if energy < SPENT_ENERGY else 0.0)
    p = max(0.0, min(1.0, p))
    if here:
        p = max(p, 0.6)   # she is in the room: answering him costs her a stretch, not a walk
    if random.random() < p:
        return "comes", ("hungry, comes fast" if hungry else "bond")
    return "sound", "answers, stays put"


# ── the lines (cat_content.CALL; the inline lines are the fail-open floor) ─────────────────────────────────
def _pool(key: str, her: str, name: str = "") -> str:
    try:
        from core import cat as _cat
        line = _cat._pool("CALL", key)
    except Exception:
        line = ""
    if not line:
        line = random.choice(_FLOOR.get(key) or _FLOOR["puss-puss"])
    return line.replace("{her}", her).replace("{name}", name or her)


_FLOOR = {
    "puss-puss": ["You call her — puss-puss, puss-puss — and listen.",
                  "You put your head out and call: puss, puss, puss. Then you wait."],
    "the kissing noise": ["You make the small kissing noise at the air, the one that means come here.",
                          "You make the kissing sound, twice, and look about for {her}."],
    "name": ["You call {name}, properly, out loud, and listen for anything coming back.",
             "You raise your voice and call her by it — {name} — and wait."],
    "answer_here": [" {her} answers with a chirrup from where she is and comes over, tail up.",
                    " From the rug, a short rising chirrup, and {her} comes to be acknowledged."],
    "answer_stays": [" {her} answers from where she is, one short chirrup, and does not move.",
                     " A chirrup back from {her}, and nothing else; she stays exactly where she is."],
    "silence": [" Nothing comes back; the day goes on with itself.",
                " You listen. The house is quiet, and the garden is only the garden."],
}


# ── the hand ──────────────────────────────────────────────────────────────────────────────────────────────
def call(state: dict, his_location: str, thought: str = "", intention: str = "", now: float | None = None) -> str | None:
    """The deed. `state` is cat.state (mutated here, saved by the caller: cat.call). Returns the line he
    perceives — what he did, and what he heard right then — or None when the hand is off / fail-closed.
    Everything about her (did it reach her, did she hear, did she answer, is she coming) goes to the
    ledger and to her state; the line never explains an unanswered call."""
    now = time.time() if now is None else now
    if not live_on() or not his_location:
        return None
    try:
        from core import cat as _cat
        from core import cat_sounds as _cs
    except Exception:
        return None
    txt = f"{thought} {intention}".lower()
    name = str(state.get("name") or "")
    her = name or "the cat"
    what, by_name = what_called(txt, name)
    spec = CALLS["name" if by_name else what]
    his_place = str(his_location)
    sp, his_pos = _his_pos(his_place)
    loc = str(state.get("location") or "")
    origin = _her_origin(state)
    door_open, window_open = _cs._house_open()
    weather, wind = _cs._weather()
    # 1. the self-sound: his voice, this window (soundscape._sec_cat reads sounding_now)
    _mem["last_call_ts"] = now
    c = {"audible": False, "why": "no position", "dist_m": None, "bearing": None, "reach_eff": None}
    known = {"audible": False}
    if origin is not None:
        # 2. the carry, C1's law in reverse: his position is the origin, hers the observer (the same wall, the
        # same weather; distance is symmetric) — once at the reach of what he called, once at KNOWN_REACH
        # (the range at which any sound of his is HIM to her)
        try:
            c = _cs.carry("cat_call", loc, his_place, his_pos, door_open, window_open, weather, wind,
                          origin=origin, reach=float(spec["reach"]))
            known = _cs.carry("cat_call", loc, his_place, his_pos, door_open, window_open, weather, wind,
                              origin=origin, reach=KNOWN_REACH)
        except Exception:
            pass
    reaches = bool(c.get("audible"))
    recognised = bool(known.get("audible")) or (by_name and name_learned(state))
    h = hearing(state)
    heard = reaches and recognised and random.random() < HEAR_P.get(h, 0.0)
    why = c.get("why") if not reaches else ("at range, a voice she does not place" if not recognised else
                                            (h if not heard else "heard"))
    here = False
    try:   # the ACOUSTIC same-room test (cat_sounds._here): a study-side doorstep is here only with the door open
        here = bool(_cs._here(loc, his_place, door_open)) and loc != "in_transit"
    except Exception:
        here = False
    decision, dwhy = ("nothing", why) if not heard else decide(state, now, here)
    answered = decision in ("comes", "sound")
    came = decision == "comes"
    # her state: the answer (sound first — cat_sounds emits cat_trill from this stamp), then the legs
    cs = state.get("call") if isinstance(state.get("call"), dict) else {}
    cs.update({"ts": now, "what": what, "by_name": by_name, "heard": heard, "answered": answered, "came": came,
               "his_place": his_place})
    if by_name:
        cs["by_name_ts"] = now   # the fed-after-a-name-call window (cat.react's feed branch reads it)
    if answered:
        cs["answered_ts"] = now
        cs["answer_here"] = here
        if came and not here:
            _come(state, now, his_place, loc, door_open, weather, wind, hungry=_hungry(state, now))
        elif came and here:
            state["activity"], state["mood"] = "coming to your call", "affectionate"
            state["last_seen"] = now
        if came and by_name:
            state["name_recognition"] = round(min(1.0, float(state.get("name_recognition") or 0.0) + NAME_LEARN_COME), 3)
    state["call"] = cs
    # discharge, not accumulation (expression's own law): a voice costs the world nothing
    try:
        from core import boredom as _b
        _b.discharge("expression", "call")
    except Exception:
        pass
    try:
        from core import activity_memory as _am
        _am.record("called_the_cat", what if not by_name else name)
    except Exception:
        pass
    row = {"ts": round(now, 1), "kind": "call", "what": what, "by_name": by_name, "name_known": name_learned(state),
           "recognition": round(float(state.get("name_recognition") or 0.0), 3),
           "reaches": reaches, "heard": heard, "answered": answered, "came": came, "here": here,
           "decision": decision, "why": dwhy if heard else why, "hearing": h,
           "his": {"place": his_place, "standpoint": sp}, "her": {"loc": loc, "act": state.get("activity"),
                                                                  "mood": state.get("mood"), "bond": round(float(state.get("bond") or 0.0), 3)},
           "dist_m": c.get("dist_m"), "reach_eff": c.get("reach_eff"), "bearing": c.get("bearing"),
           "door_open": door_open, "weather": weather, "wind": wind}
    try:
        _log(row)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    # 4. the line: what he did, and what he heard right then — an answer in the room is a sound here and now;
    # from elsewhere the trill reaches him through cat_sounds (sound first, then her legs); or silence
    line = _pool("name" if by_name else what, her, name)
    if answered and here:
        line += _pool("answer_here" if came else "answer_stays", her, name)
    elif not answered and random.random() < 0.5:
        line += _pool("silence", her, name)
    return line


def _come(state: dict, now: float, his_place: str, loc: str, door_open: bool, weather: str, wind: str,
          hungry: bool = False) -> None:
    """She comes on her own legs: cat_ears._begin walks her (a cross-place move is a journey; a cross-wall
    move with the door shut becomes the honest door-asking state; mid-leg it re-aims her) and holds her
    (HOLD_S["call"]) so the 180 s roll does not send her elsewhere before she arrives. A hungry cat's first
    leg is shorter."""
    dest_loc = {"study": "indoors", "garden": "garden", "wood": "wood", "shore": "shore"}.get(his_place, "garden")
    try:
        from core import cat_ears as _ce
        _ce._begin(state, now, "call", "his call", dest_loc, "coming to your call", "expectant", bout="active")
    except Exception as exc:
        logger.debug("[cat_call] legs failed (non-fatal): %s", exc)
        return
    t = state.get("transit")
    if hungry and isinstance(t, dict) and t.get("leg_ends"):
        try:
            t["leg_ends"] = now + (float(t["leg_ends"]) - now) * HUNGRY_LEG_FACTOR
        except Exception:
            pass


def note_fed(state: dict, now: float | None = None) -> bool:
    """cat.react's feed branch, on a REAL feed: fed within NAME_FED_WINDOW_S of a call by her name ->
    name_recognition rises (step 5). Returns True when it did. One rise per call (the window is consumed)."""
    now = time.time() if now is None else now
    cs = state.get("call") if isinstance(state.get("call"), dict) else {}
    ts = float(cs.get("by_name_ts") or 0.0)
    if not ts or now - ts > NAME_FED_WINDOW_S or not state.get("name"):
        return False
    cs["by_name_ts"] = 0.0
    state["name_recognition"] = round(min(1.0, float(state.get("name_recognition") or 0.0) + NAME_LEARN_FED), 3)
    state["call"] = cs
    try:
        _log({"ts": round(now, 1), "kind": "fed_after_call", "what": cs.get("what"), "by_name": True,
              "recognition": state["name_recognition"], "name_known": name_learned(state)})
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    return True


def sounding_now(now: float | None = None) -> bool:
    """soundscape._sec_cat: his call is in the air this window (a self-sound, known instantly)."""
    now = time.time() if now is None else now
    return (now - float(_mem.get("last_call_ts") or 0.0)) < _SOUND_WINDOW_S


def status() -> dict:
    n = 0
    try:
        with open(_LEDGER, encoding="utf-8") as f:
            n = sum(1 for _ in f)
    except Exception:
        pass
    return {"live": live_on(), "ledger_rows": n, "last_call": _mem.get("last_call_ts")}
