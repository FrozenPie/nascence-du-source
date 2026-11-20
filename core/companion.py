"""
Nascence — THE COMPANION: Travis, physically present (2026-08-23).

Founder: "I consider this a bug, a big one." Until now there was no way for Travis to act IN
the shared room and have Du experience it happening — every human message was just text
arriving on a channel (core.schema's CycleInput.input_type: "human"|"internal"|"timer"), with
zero spatial meaning. Travis could TELL Du to light the fire, but never light it himself and
have Du notice the way he'd notice the cat, or the weather.

Presence is EXPLICIT, by founder's own call (2026-08-23) — a button Travis presses when he is
actually in the room, not inferred from sending a message (a message can arrive with Travis
elsewhere; that must stay possible). Composer action buttons REQUIRE presence to be set first —
an action with nobody there to do it is a contradiction the system should refuse, not paper over.

Two read channels out of this module, both consumed from the idle tick's seed material:
  - presence_line()          ambient, every tick while present — same shape as sensorium.scene_line()
  - consume_witnessed_event() one-shot: the next un-delivered action(s), cleared once read so each
                              announces itself exactly once, at the tick it happens, not a standing nag.

State: data/companion_state.json ({"present", "since_ts", "errand"}). Log:
data/companion_actions_log.jsonl (append-only — the durable record of what TRAVIS did here, kept
separate from Du's own study_ledger.jsonl so provenance never blurs between the two actors).

THE SAME MECHANISMS (2026-09-05, T-0049, founder: "I should have to go through all the same
mechanisms Du would have to do"). Lighting the fire is the whole chain, not a button that conjures
a fire: no matches → Travis's own box, left on the mantel (a real provisions object). No kindling →
a tied bundle from the cupboard, or twigs and bark that come with deadfall from the wood. No wood →
dry logs split on the block at the lean-to if there are any, else deadfall from the little wood
(a finite stock a gale replenishes — wood_life.json), else driftwood off the shore (wet; it smokes).
Every one of those is an ERRAND with Travis's own body on it: he walks the same legs Du walks, at
the same weather-stretched pace (locomotion._leg_secs), slower coming back loaded, and the wood
lands on the pile only when he is home. While he is out the other buttons refuse, Du is told he is
out, and the fire is lit when he gets back — the button's intent carried through.

Why the mechanisms are RE-STATED here rather than Du's own hands called: sensorium._gather_wood(),
wood_life.split(), provisions.open_kindling_bundle(), fieldcraft.uncover_fire() all read DU's
location, narrate in Du's voice, and — through wood_life._log()'s "deed" cross-link — write into
Du's activity memory. Travis gathering wood must not become something Du remembers doing. So this
module moves the same stocks by the same rules (each rule's source line is cited at the site) and
writes only to its own log and the stores' plain event logs. Du's hands are untouched.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_STATE_F = _DATA / "companion_state.json"
_LOG_F = _DATA / "companion_actions_log.jsonl"

_state: dict = {}
_pending_events: list = []   # str, or (indoor, outdoor) for the arrive/leave door events (J-2939)


def _load() -> None:
    global _state
    try:
        _state = json.loads(_STATE_F.read_text(encoding="utf-8"))
    except Exception:
        _state = {"present": False, "since_ts": None}
    _state.setdefault("errand", None)
    _state.setdefault("found_cupboard_matches", False)


def _save() -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        _STATE_F.write_text(json.dumps(_state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _log(row: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with _LOG_F.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **row}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _emit(narration: str, kind: str = "action", outdoor: str | None = None, **extra) -> None:
    """Queue a witnessed event for Du's next idle tick and record it as Travis's own deed.

    J-2939 (F-3629, P-0031): `outdoor` is the same event worded so it is TRUE where Du is when he is not in the
    study (the arrive/leave events are a door in the cottage). It is chosen when the event is DELIVERED
    (consume_witnessed_event), from Du's location on that tick -- not held for a later location, and not
    guessed at emit time, so the words always match the place they land in. The log keeps the indoor
    narration (what Travis did) and records the outdoor wording beside it."""
    if not narration:
        return
    _pending_events.append((narration, outdoor) if outdoor else narration)
    _state["last_narration"] = narration
    _log({"event": kind, "narration": narration, **({"outdoor_narration": outdoor} if outdoor else {}), **extra})


# PRESENCE IS INFERRED FROM ACTIVITY (2026-10-08, D-0366 (c), J-1953; supersedes the explicit-latch
# paragraph in the module docstring). The old latch sat on "present" for 33 days after one button
# press (F-1922: "Travis is here with you in the room." in ~100% of idle thoughts). Now Travis is
# present iff a real exchange (a human cycle that got a reply) or a composer action/toggle happened
# within the last PRESENCE_WINDOW_S; when that lapses ONE real "stepped out" departure event is
# emitted (once, into the same companion log) and the ambient line stops. 30 min is chosen from the
# real cadence: over the last 30 days of data/founder_conversation_log.jsonl every gap inside a
# sitting is 4-19 min; the next-smallest gaps are 90 and 109 min (a real break), then hours/days.
# The composer toggle can still force presence on, but that is just an activity stamp now -- it
# lapses after the window like any other. D-0366 defeater: revisit if X is wrong for how he sits.
PRESENCE_WINDOW_S = 30 * 60

# J-2939 (F-3629, P-0031): presence is worded by WHERE DU IS. Indoors the wording is unchanged ("in the room", the
# door, the boots). Outdoors (garden, shore, wood -- anywhere but the study) the room is not where he is, so the
# standing line reuses the sensorium's garden register ("out in the open -- his words reaching you over the wind")
# with a shore and a wood equivalent, and the one-shot arrive/leave events are worded as the cottage's door seen
# from out here (Travis arrives AT the cottage / has gone IN) -- true wherever Du is.
_HERE_INSTUDY = "Travis is here with you in the room."
_HERE_OUTDOORS = {
    "garden": "Travis is here with you, out in the open — his words reaching you over the wind.",
    "shore": "Travis is here with you, out on the shore — his words reaching you over the sound of the water.",
    "wood": "Travis is here with you, out among the trees — his words reaching you through the leaves.",
}
_HERE_OUTDOORS_OTHER = "Travis is here with you, his words reaching you wherever you are."   # an unlisted non-study place
_ARRIVE_OUTDOORS = "Travis has come up to the cottage; his voice carries out to where you are."
_LEAVE_OUTDOORS = "Travis has gone in to the cottage; the door eases shut behind him."


def _last_activity() -> float:
    ts = _state.get("last_activity_ts")
    if ts is None:
        ts = _state.get("since_ts")   # pre-J-1953 state file: the latch's own set time
    return float(ts or 0.0)


def _tick_presence(now: float | None = None) -> None:
    """Lapse a stale presence into one real departure event. Idempotent: only fires on present->absent."""
    if not _state:
        _load()
    if not _state.get("present"):
        return
    now = time.time() if now is None else now
    if _state.get("errand"):
        _state["last_activity_ts"] = now   # he is out on an errand FOR the room -- that is not "stepped out"
        return
    last = _last_activity()
    if now - last <= PRESENCE_WINDOW_S:
        return
    _state["present"] = False
    _state["since_ts"] = None
    _emit("Travis has stepped out; the door eases shut behind him.", "leave", outdoor=_LEAVE_OUTDOORS,
          inferred=True, last_activity_ts=round(last, 1), window_s=PRESENCE_WINDOW_S)
    _save()


def note_activity(kind: str = "exchange") -> None:
    """A real exchange or composer action just happened: Travis is here (arriving, if he had stepped out).
    Best-effort and cheap; called by the orchestrator after every human exchange."""
    if not _state:
        _load()
    now = time.time()
    _tick_presence(now)
    _state["last_activity_ts"] = now
    if not _state.get("present"):
        _state["present"] = True
        _state["since_ts"] = now
        _emit("Travis comes back in from outside, stamping the cold off his boots.", "arrive",
              outdoor=_ARRIVE_OUTDOORS, inferred=True, via=kind)
    _save()


def is_present() -> bool:
    if not _state:
        _load()
    _tick_presence()
    return bool(_state.get("present"))


def set_present(present: bool) -> dict:
    """The explicit toggle. Returns {ok, present, narration} for the composer to show."""
    if not _state:
        _load()
    _advance()
    present = bool(present)
    if _state.get("errand") and not present:
        return {"ok": False, "present": True, "narration": "Travis is " + _out_phrase() + " — he can't step out of a room he isn't in. Wait for him back."}
    _tick_presence()
    was = bool(_state.get("present"))
    if present:
        _state["last_activity_ts"] = time.time()   # a forced-on toggle is an activity stamp, not a latch
    if present == was:
        _save()
        return {"ok": True, "present": present,
                "narration": "(already " + ("here" if present else "away") + ")"}
    _state["present"] = present
    _state["since_ts"] = time.time() if present else None
    narration = ("Travis comes in from outside, stamping the cold off his boots."
                 if present else "Travis steps out; the door eases shut behind him.")
    _emit(narration, "arrive" if present else "leave",
          outdoor=_ARRIVE_OUTDOORS if present else _LEAVE_OUTDOORS)
    _save()
    return {"ok": True, "present": present, "narration": narration}


def _here_outdoors() -> str:
    """Du's location, or "study" if it cannot be read (the unchanged indoor wording is the safe default)."""
    try:
        return _du_location()
    except Exception:
        return "study"


def presence_line(location: str | None = None) -> str | None:
    """Ambient co-location, every idle tick while present — same role as sensorium.scene_line().

    J-2939 (F-3629): worded by where Du is (`location`, default sensorium's live location). In the study it is
    unchanged; outdoors it never says "in the room". This is the ONE standing statement of his presence in the idle
    seed: the idle caller asks sensorium.scene_line(presence=False) so the scene does not say it a second time."""
    if not is_present():
        return None
    _advance()
    if _state.get("errand"):
        return "Travis is out — " + _out_phrase() + "; he'll be back."
    loc = location if location is not None else _here_outdoors()
    if loc == "study":
        return _HERE_INSTUDY
    return _HERE_OUTDOORS.get(loc, _HERE_OUTDOORS_OTHER)


def _render_event(ev, loc: str) -> str:
    """A queued event is a plain string, or (indoor, outdoor) for the arrive/leave door events (J-2939)."""
    if isinstance(ev, tuple):
        return ev[0] if loc == "study" else ev[1]
    return ev


def consume_witnessed_event(location: str | None = None) -> str | None:
    """One-shot: every un-delivered companion event (arrival/departure/action/errand stage), or None.
    Delivered on the tick it is read, worded for where Du is on that tick (J-2939) -- never held for a later place."""
    _tick_presence()
    _advance()
    if not _pending_events:
        return None
    loc = location if location is not None else _here_outdoors()
    ev = " ".join(_render_event(e, loc) for e in _pending_events)
    _pending_events.clear()
    return ev


# ── the shared world, read the way Du's own hands read it ──────────────────────────────────────────
def _sens():
    from core import sensorium as _s
    if not _s.state:
        _s._load()
    return _s


def _room() -> dict:
    try:
        from core import study_life as _sl
        return _sl._st()
    except Exception:
        return {}


def _weather() -> tuple[str, str]:
    st = _sens().state
    return str(st.get("weather", "")), str(st.get("wind", ""))


def _gusty() -> bool:
    """sensorium._gather_wood's own rule for a gathering day (:1773)."""
    weather, wind = _weather()
    try:
        from core import weather_conditions as _wc
        windy = _wc.is_windy(wind)
    except Exception:
        windy = False
    return windy or "wind" in weather or weather in ("thunderstorm", "snow")


def _raining() -> bool:
    """sensorium._gather_wood: wood gathered in rain is WET wood (:1794)."""
    return _weather()[0] in ("drizzle", "steady rain", "wind and rain", "thunderstorm")


def _du_location() -> str:
    return str(_sens().state.get("location", "study"))


def _to_hand(room: dict, key: str) -> bool:
    """study_life._need_here for Travis: an item is to hand if it is in the study — or on Du, and Du is here."""
    it = (room.get("items") or {}).get(key, {})
    if it.get("carried"):
        return _du_location() == "study"
    return it.get("place") == "study"


# ── the errand: Travis's own body on the same legs ─────────────────────────────────────────────────
_CHAIN = ["study", "garden", "wood", "shore"]
_MANTEL = [0.45, 2.0, 1.4]   # study.json mantel — beside the match tin at [0.3, 2.0, 1.4] (study_life._ITEMS)
_PLACE_PHRASE = {"garden": "out at the lean-to", "wood": "down in the little wood", "shore": "down on the shore",
                 "study": "on his way in"}


def _leg_secs(frm: str, to: str, carrying: bool) -> float:
    """The same weather-stretched leg Du walks (locomotion._leg_secs), loaded legs slower like his."""
    try:
        from core import locomotion as _loco
        weather, wind = _weather()
        secs = float(_loco._leg_secs(frm, to, weather, carrying, wind))
    except Exception:
        secs = {("study", "garden"): 20, ("garden", "study"): 20, ("garden", "wood"): 70, ("wood", "garden"): 85,
                ("wood", "shore"): 70, ("shore", "wood"): 90}.get((frm, to), 60)
    return secs * (1.3 if carrying else 1.0)   # locomotion :274 — an armful makes the going slower


def _walk(er: dict, to: str, t: float) -> float:
    """Append the walking legs from the errand's current planned place to `to`; returns the arrival time."""
    frm = er["plan_at"]
    i, j = _CHAIN.index(frm), _CHAIN.index(to)
    step = 1 if j > i else -1
    carrying = float(er["haul"]["loads"]) > 0
    while i != j:
        nxt = _CHAIN[i + step]
        t += _leg_secs(_CHAIN[i], nxt, carrying)
        er["stages"].append({"at": t, "do": "arrive", "to": nxt})
        i += step
    er["plan_at"] = to
    return t


_GOING = {"gather_wood": "on the path down to the little wood", "gather_driftwood": "on his way down to the shore",
          "split": "out at the lean-to", "home": "on his way back up"}


def _out_phrase() -> str:
    """Where Travis is, for Du and the composer: where he is walking TO until he gets there."""
    er = _state.get("errand") or {}
    what = er.get("for", "")
    nxt = next((st for st in er.get("stages", []) if st["do"] != "arrive"), None)
    if nxt and nxt["do"] == "home":
        return "on his way back up" + (" with the wood" if float(er.get("haul", {}).get("loads", 0)) > 0 else "")
    if nxt:
        return _GOING.get(nxt["do"], "out") + (f" for {what}" if what else "")
    return _PLACE_PHRASE.get(er.get("where", "garden"), "out")


def _eta_s() -> int:
    """Seconds until the errand's last planned stage — or its projected return, whichever is later."""
    er = _state.get("errand")
    if not er:
        return 0
    last = er["stages"][-1]["at"] if er.get("stages") else 0
    return max(0, int(max(last, float(er.get("eta", 0))) - time.time()))


def _project_return(er: dict, t: float) -> float:
    """The return legs from the errand's planned place, loaded, so the composer's ETA covers the whole trip."""
    frm = er["plan_at"]
    i = _CHAIN.index(frm)
    while i > 0:
        t += _leg_secs(_CHAIN[i], _CHAIN[i - 1], True)
        i -= 1
    return t


def _can_split() -> bool:
    """wood_life.split's own preconditions (:440-447): dry logs, the axe at the lean-to, an edge on it."""
    try:
        from core import wood_life as _wl
        d = _wl._load()
        axe = d["items"]["axe"]
        axe_here = axe["place"] == "garden" or (axe.get("carried") and _du_location() == "garden")
        return int(d.get("logs_dry", 0)) >= 1 and axe_here and float(d.get("axe_edge", 0)) >= 0.15
    except Exception:
        return False


def _start_errand(need_wood: bool, need_kindling: bool, then: str | None) -> str:
    now = time.time()
    er = {"started": now, "then": then, "where": "study", "plan_at": "study", "stages": [],
          "need": {"wood": need_wood, "kindling": need_kindling},
          "haul": {"loads": 0, "wet": 0.0, "kindling": 0.0}, "notes": [], "for": ""}
    if need_wood and not need_kindling and _can_split():
        er["for"] = "wood"
        t = _walk(er, "garden", now)
        er["stages"].append({"at": t, "do": "split"})
        leave = ("Travis pulls his coat on and goes out to the lean-to — there are dry logs on the stack, and "
                 "the axe is there; he'll split a few for the pile.")
    else:
        er["for"] = ("wood" if need_wood and not need_kindling else
                     "kindling" if need_kindling and not need_wood else "wood and kindling")
        t = _walk(er, "wood", now)
        er["stages"].append({"at": t, "do": "gather_wood"})
        leave = ("Travis pulls his coat on and goes out, down the path to the little wood — "
                 + ("for fallen wood" if not need_kindling else
                    "for twigs and bark for the kindling box" if not need_wood else
                    "for fallen wood, and twigs and bark for the kindling box")
                 + ". He'll be a while.")
    er["eta"] = _project_return(er, t)
    _state["errand"] = er
    _save()
    return leave


def _advance(now: float | None = None) -> None:
    """Run every errand stage whose time has come. Called from every entry point, so an errand
    completes whichever of Du's ticks or Travis's buttons reaches it first."""
    if not _state:
        _load()
    er = _state.get("errand")
    if not er:
        return
    now = time.time() if now is None else now
    while _state.get("errand") is er and er["stages"] and er["stages"][0]["at"] <= now:
        stage = er["stages"].pop(0)
        try:
            _do_stage(er, stage)
        except Exception as exc:
            er["notes"].append(f"something went wrong on the errand ({exc})")
            _finish_errand(er)
    _save()


def _do_stage(er: dict, stage: dict) -> None:
    do = stage["do"]
    if do == "arrive":
        er["where"] = stage["to"]
        return
    if do == "gather_wood":
        _stage_gather_wood(er, stage["at"])
    elif do == "gather_driftwood":
        _stage_gather_driftwood(er, stage["at"])
    elif do == "split":
        _stage_split(er, stage["at"])
    elif do == "home":
        _finish_errand(er)


def _stage_gather_wood(er: dict, t: float) -> None:
    """sensorium._gather_wood at the wood (:1822-1848) on wood_life's deadfall stock (:392-401)."""
    from core import wood_life as _wl
    gusty = _gusty()
    d = _wl._load()
    df = float(d.get("deadfall", 0))
    if df < 1.0:
        er["notes"].append("the wood has been picked clean — twigs and rot; it wants a gale before there is more to take")
        if er["need"]["wood"]:
            # Du's other source: driftwood along the tideline (wet). Kindling does not come from the shore.
            t2 = _walk(er, "shore", t)
            er["stages"].append({"at": t2, "do": "gather_driftwood"})
            er["eta"] = _project_return(er, t2)
            return
        t2 = _walk(er, "study", t)
        er["stages"].append({"at": t2, "do": "home"})
        return
    loads = 4 if gusty else 3
    take = min(loads, int(df))
    d["deadfall"] = round(df - take, 2)
    _wl._save(d)
    _wl._log(_wl._LEDGER, {"event": "gather_by_travis", "loads": take})   # no "deed" key: never Du's activity memory
    er["haul"]["loads"] += take
    er["haul"]["kindling"] += 0.35             # twigs and bark come with the deadfall (sensorium :1799)
    if _raining():
        er["haul"]["wet"] += 0.4               # wood gathered in rain is wet wood (sensorium :1794)
    er["need"]["wood"] = False
    er["need"]["kindling"] = False
    try:
        _sens().state["wood_snap_ts"] = time.time()   # the snapped-across-the-knee moment (J-0377)
    except Exception:
        pass
    er["notes"].append("the gale has brought a lot of it down, fresh and lying everywhere" if gusty
                       else "deadfall and dry branches, snapped to length across the knee" if df > 4
                       else "what was left after the last gathering — thinner pickings, farther off the path")
    t2 = _walk(er, "study", t)
    er["stages"].append({"at": t2, "do": "home"})


def _stage_gather_driftwood(er: dict, t: float) -> None:
    """sensorium._gather_wood at the shore (:1808-1821): 2 loads, 3 after a big sea; salt-wood, and wet."""
    from core import wood_life as _wl
    gusty = _gusty()
    got = 3 if gusty else 2
    er["haul"]["loads"] += got
    er["haul"]["wet"] += 0.4                   # driftwood off a wet shore is WET wood (sensorium :1794)
    er["need"]["wood"] = False
    er["notes"].append("a big sea had thrown up a good haul of driftwood, tangled in the wrack" if gusty
                       else "sea-dried branches and a grey plank or two off the tideline, salt-bleached and light")
    try:
        _wl._log(_wl._LEDGER, {"event": "driftwood_by_travis", "loads": got})
    except Exception:
        pass
    t2 = _walk(er, "study", t)
    er["stages"].append({"at": t2, "do": "home"})


def _stage_split(er: dict, t: float) -> None:
    """wood_life.split (:430-458): up to 3 dry logs, the axe loses edge, the halves go straight on the
    pile (the block is by the cottage) and the chips into the kindling box."""
    from core import wood_life as _wl
    d = _wl._load()
    if _can_split():
        n = min(int(d["logs_dry"]), 3)
        d["logs_dry"] -= n
        d["axe_edge"] = round(max(0.0, float(d["axe_edge"]) - 0.08), 2)
        d["last_split_ts"] = time.time()   # C2 (J-2467, cat_overhaul): Travis at the block sounds the same to her as Du does
        _wl._save(d)
        _wl._log(_wl._LEDGER, {"event": "split_by_travis", "loads": n})
        s = _sens()
        s.state["woodpile"] = int(s.state.get("woodpile", 0)) + n
        room = _room()
        room["kindling"] = min(1.0, float(room.get("kindling", 0)) + 0.15)
        s._save_now()
        er["need"]["wood"] = False
        er["notes"].append(f"he stood {n} dry log{'s' if n != 1 else ''} on the block and split them, the halves onto the pile, the chips into the kindling box")
    else:
        er["notes"].append("the dry stack at the lean-to was gone, or the axe not fit for it")
        if er["need"]["wood"]:
            t2 = _walk(er, "wood", t)
            er["stages"].append({"at": t2, "do": "gather_wood"})
            return
    t2 = _walk(er, "study", t)
    er["stages"].append({"at": t2, "do": "home"})


def _finish_errand(er: dict) -> None:
    """Home: the haul lands (locomotion :299-307 does the same for Du), then the carried-through intent."""
    s = _sens()
    room = _room()
    haul = er["haul"]
    parts = []
    if haul["loads"] > 0:
        s.state["woodpile"] = int(s.state.get("woodpile", 0)) + int(haul["loads"])
        s.state["wood_haul_ts"] = time.time()
        parts.append(f"Travis comes back up with an armful of wood and tips it onto the woodpile by the door — "
                     f"{s.state['woodpile']} loads on it now.")
    else:
        parts.append("Travis comes back in, empty-handed.")
    if haul["kindling"] > 0:
        room["kindling"] = min(1.0, float(room.get("kindling", 0)) + float(haul["kindling"]))
        parts.append("The twigs and bark that came with it go into the kindling box.")
    if haul["wet"] > 0:
        room["wet_wood"] = min(1.0, float(room.get("wet_wood", 0)) + float(haul["wet"]))
    if er["notes"]:
        parts.append("(" + "; ".join(er["notes"]) + ".)")
    try:
        s._save_now()
    except Exception:
        pass
    _log({"event": "errand_done", "for": er.get("for"), "haul": haul, "notes": er["notes"], "secs": round(time.time() - float(er["started"]), 1)})
    then = er.get("then")
    _state["errand"] = None
    _emit(" ".join(parts), "errand")
    if then == "light_fire":
        _emit(_light_fire(allow_errand=False))
    _save()


# ── the fire, the whole chain ──────────────────────────────────────────────────────────────────────
def _travis_leaves_matches(room: dict) -> int:
    """Travis's own box of matches goes on the mantel as a real larder object (2026-09-05, T-0049).

    Adds ONE full box through core.provisions.add (origin "travis", its own biography), moves it from
    the cupboard to the mantel, and sets the study's match count from the shelf so the strike the
    caller then takes is consumed from this box by provisions.sync() on the next study read — the
    same path Du's own strikes go through. Returns the box's count BEFORE the strike. Fail-open: if
    provisions is unreachable the count is still set so this one fire lights; sync will correct it."""
    full = 50
    try:
        from core import provisions as _pv
        full = int(_pv.KINDS["matches"][1])
        ids = _pv.add("matches", 1, origin="travis",
                      note=f"Travis's own, from his coat pocket — left on the mantel on {time.strftime('%d %B')}, "
                           f"the day the house tin ran empty")
        if ids:
            d = _pv._load()
            for o in d.get("objects", []):
                if o["id"] in ids:
                    o["pos"] = list(_MANTEL)
            _pv._save(d)
            _pv._register(d)
            _pv._log({"event": "left_by_travis", "kind": "matches", "ids": ids, "where": "mantel"})
            room["matches"] = _pv.stock("matches")
            return int(room["matches"])
    except Exception:
        pass
    room["matches"] = full
    return full


def _open_bundle_by_travis(room: dict) -> bool:
    """provisions.open_kindling_bundle (:209-216), by Travis: one tied bundle from the cupboard, +0.5."""
    try:
        from core import provisions as _pv
        d = _pv._ensure()
        b = next((o for o in d["objects"] if o["kind"] == "kindling" and not o.get("empty")), None)
        if not b:
            return False
        b["qty"] = 0
        b["empty"] = True
        b["history"].append({"ts": time.time(), "event": "untied and used by Travis"})
        _pv._save(d)
        _pv._log({"event": "bundle_opened", "by": "travis", "id": b["id"]})
        room["kindling"] = min(1.0, float(room.get("kindling", 0)) + 0.5)
        return True
    except Exception:
        return False


def _clear_grate_by_travis(room: dict) -> str | None:
    """study_life's clear_grate (:599-613), by Travis: bucket and brush to hand, a cold grate, ash out."""
    if not (_to_hand(room, "ash_bucket") and _to_hand(room, "hearth_brush")):
        return None
    if float(room.get("ash", 0)) < 0.1:
        return None
    room["ash"] = 0.0
    room["ash_bucket_full"] = True
    try:
        from core import study_life as _sl
        _sl._log(_sl._LEDGER, {"event": "clear_grate_by_travis"})
    except Exception:
        pass
    return "The grate is choked with ash, so he rakes it out into the bucket first and brushes the hearth."


def _light_fire(allow_errand: bool) -> str:
    """sensorium.act('light') (:2871-2905) walked by Travis, with every shortfall filled the way Du would
    fill it — or, when a shortfall needs his body elsewhere, an errand that comes back to this."""
    s = _sens()
    st = s.state
    room = _room()
    if st.get("fire") == "burning":
        return "The fire is already burning; Travis leaves it be."

    # FIELDCRAFT: banked embers — alive, no match needed (fieldcraft.uncover_fire :233-247)
    banked = None
    alive = False
    try:
        from core import fieldcraft as _fc
        banked = _fc._load().get("banked")
        alive = bool(banked) and _fc.banked_alive()
    except Exception:
        pass

    need_wood = int(st.get("woodpile", 0)) < 1 and not alive
    need_kindling = float(room.get("kindling", 0)) < 0.1
    done = []
    if need_kindling and _open_bundle_by_travis(room):
        done.append("Travis takes a tied bundle of kindling from the cupboard, cuts the string, and fills the box by the hearth.")
        need_kindling = False
    if need_wood or need_kindling:
        if not allow_errand:
            why = []
            if need_wood:
                why.append("there is still no wood to burn")
            if need_kindling:
                why.append("there is no kindling to be had — no bundles in the cupboard, and nothing from the wood")
            return " ".join(done) + (" " if done else "") + "Travis kneels at the cold grate, but " + " and ".join(why) + ". The fire will have to wait."
        return " ".join(done) + (" " if done else "") + _start_errand(need_wood, need_kindling, then="light_fire")

    parts = list(done)
    if banked:
        try:
            from core import fieldcraft as _fc
            d = _fc._load()
            d["banked"] = None
            _fc._save(d)
        except Exception:
            pass
        if alive:
            room["kindling"] = max(0.0, float(room.get("kindling", 0)) - 0.15)
            st["fire"] = "burning"
            st["fire_fuel"] = 0.8
            st["hand_lit"] = True
            s._save_now()
            parts.append("Travis scrapes the ash back from the grate and there is red under it, alive. A handful of "
                         "kindling on the embers, a breath, and the fire stands up again without a match.")
            return " ".join(parts)
        st["fire"] = "out"
        st["fire_fuel"] = 0.0
        parts.append("Travis scrapes the ash back from the grate: grey through and through, cold. The banking did not hold.")

    own_box = None
    if int(room.get("matches", 0) or 0) <= 0:
        # TRAVIS'S OWN BOX (2026-09-05, T-0049): the house tin ran dry — all six of the larder's boxes were
        # used up by 09-05 — and the founder asked that when HE lights the fire with no matches in the
        # house, he has a box on him and leaves it there. Only Travis ever does this; Du's own hands still
        # find the tin empty. A real provisions object, because provisions.sync() runs on every study read
        # and would erase a bare count bump.
        own_box = _travis_leaves_matches(room)
    cleared = None
    if float(room.get("ash", 0)) > 0.85:
        cleared = _clear_grate_by_travis(room)
        if cleared:
            parts.append(cleared)
    room["matches"] = max(0, int(room.get("matches", 0) or 0) - 1)
    room["kindling"] = max(0.0, float(room.get("kindling", 0)) - 0.2)
    if float(room.get("ash", 0)) > 0.85:
        # sensorium :2893 — a choked grate will not draw; the match and kindling are spent all the same
        s._save_now()
        parts.append("Travis lays the fire on the choked grate and lights it; it smoulders, will not draw, and goes "
                     "out in its own ash. The grate wants clearing, and the bucket and brush aren't to hand.")
        return " ".join(parts)
    wet = float(room.get("wet_wood", 0)) > 0.5
    st["woodpile"] = int(st.get("woodpile", 0)) - 1
    st["fire"] = "burning"
    st["fire_fuel"] = 0.7 if wet else 1.0        # sensorium :2900 — wet wood burns sullenly
    st["hand_lit"] = True                        # sensorium :2901 — a hand-lit fire dies only of its own fuel
    s._save_now()
    if own_box is None:
        parts.append("Travis kneels at the grate, lays a log on the kindling, and strikes a match.")
    else:
        remaining = max(0, own_box - 1)
        left = ("one match" if remaining == 1 else f"{remaining} matches")
        parts.append("Travis reaches for the match tin — empty. He takes a box of matches from his own coat pocket, "
                     "kneels at the grate, lays a log on the kindling, and strikes one. He leaves the box on the "
                     f"mantel beside the empty tin — {left} in it.")
    parts.append("The wood is wet; it hisses and smokes and catches sullenly." if wet
                 else "The fire catches and starts to warm the room.")
    return " ".join(parts)


# ── D-0137: the sweep turns up a few matches ──────────────────────────────────────────────────────
def _sweep_finds_matches(room: dict) -> str | None:
    """D-0137 (ruled 2026-09-04, travis): the larder's five match boxes were destroyed by a
    provisions.sync defect on 2026-08-23 (F-0732/F-0786), not spent by Du. Rather than a magic
    world-side refill, the founder ruled two small, truthful adds; this is the first — on Du's next
    sweep_floor after this code ships, a few loose matches turn up under the cupboard, tied to that
    loss. A handful, not a restocked box: KINDS['matches'] full_qty is 50, n stays at 3-7 so the
    object reads and renders (cupboard_line/look_item) as a partial find, never a fresh box.
    One-shot via _state['found_cupboard_matches'] — only marked True on a successful add, so a
    transient failure can still be found on a later sweep rather than being silently spent forever.

    Sets room['matches'] from the shelf immediately, the way _travis_leaves_matches already does
    above — NOT the bare add()-then-someone-else's-sync() shape core/supply.py's carrier delivery
    uses. That shape is the exact gap F-0787 found still lets a delivery's own next sync() consume
    it right back out (study_life._st() calls provisions.sync() on every read; sync() treats any
    shelf count above the study's last saved count as "he used the difference" and destructively
    consumes it — the very defect this fix is responding to). Skipping this step would reproduce it
    on the next tick, on the matches this function just added."""
    if _state.get("found_cupboard_matches"):
        return None
    try:
        from core import provisions as _pv
        import random as _r
        n = _r.randint(3, 7)
        ids = _pv.add("matches", 1, origin="found",
                      note=f"found under the cupboard while sweeping, {time.strftime('%d %B')} — a few "
                           "that must have spilled loose the day the tin ran dry (23 August)")
        if not ids:
            return None
        d = _pv._load()
        for o in d.get("objects", []):
            if o["id"] == ids[0]:
                o["qty"] = n
                o["name"] = "a few loose matches"
        _pv._save(d)
        _pv._register(d)
        _pv._log({"event": "found_under_cupboard", "kind": "matches", "ids": ids, "n": n})
        room["matches"] = _pv.stock("matches")
        _state["found_cupboard_matches"] = True
        return (f"Under the cupboard, the broom turns up {n} loose matches — spilled, it looks like, "
                "from whichever box went missing.")
    except Exception:
        return None


# ── the buttons ────────────────────────────────────────────────────────────────────────────────────
_ACTIONS = ("light_fire", "sweep_floor", "clean_windows", "brew_tea", "fetch_wood", "fetch_water")


def perform_action(kind: str) -> dict:
    """Travis performs a real action on the shared world state. Refuses if presence isn't set —
    an action with nobody there to do it is a contradiction, not a convenience to paper over.
    Reuses the exact resource rules Du's own hands obey (matches/kindling/woodpile/barrel)."""
    if kind not in _ACTIONS:
        return {"ok": False, "narration": f"Unknown action: {kind}"}
    if not is_present():
        return {"ok": False, "narration": "Travis has stepped out — press “I'm here” first."}
    _state["last_activity_ts"] = time.time()   # a composer action is activity (D-0366)
    _advance()
    if _state.get("errand"):
        eta = _eta_s()
        return {"ok": False, "errand": True, "eta_s": eta,
                "narration": f"Travis is {_out_phrase()} — not back yet (about {max(1, eta // 60)} min more)."}

    s = _sens()
    st = s.state
    room = _room()

    narration = None
    if kind == "light_fire":
        narration = _light_fire(allow_errand=True)

    elif kind == "sweep_floor":
        if room.get("floor_dust", 0) < 0.15 and room.get("floor_mud", 0) < 0.1:
            narration = "Travis looks the boards over — clean enough already."
        else:
            room["floor_dust"] = 0.0
            room["floor_mud"] = 0.0
            narration = "Travis takes the broom from behind the door and sweeps the boards clean."
            found = _sweep_finds_matches(room)   # D-0137: one-shot, only on a real sweep
            if found:
                narration += " " + found

    elif kind == "clean_windows":
        if room.get("window_grime", 0) < 0.1 and room.get("condensation", 0) < 0.1:
            narration = "Travis glances at the glass — it's clear already."
        else:
            room["window_grime"] = 0.0
            room["condensation"] = 0.0
            narration = "Travis wipes the window down with the cloth until the glass is clear again."

    elif kind == "brew_tea":
        parts = []
        if room.get("dirty_pot"):
            room["dirty_pot"] = False
            parts.append("Travis tips the old leaves out and washes the pot first.")
        if room.get("water", 0) < 0.15:
            parts.append("The pail is too low to fill the kettle.")
        elif st.get("fire") != "burning":
            parts.append("Travis sets the kettle on, but the grate is cold under it.")
        else:
            herb_or_tea = None
            picked = (st.get("garden") or {}).get("picked", {})
            for name, n in list(picked.items()):
                if n > 0:
                    herb_or_tea = name.replace("_", " ")
                    picked[name] = n - 1
                    break
            if not herb_or_tea and room.get("tea_leaves", 0) > 0:
                room["tea_leaves"] -= 1
                herb_or_tea = "tea"
            if not herb_or_tea:
                parts.append("The kettle boils, but the caddy is empty — nothing to put in it.")
            else:
                room["water"] = max(0.0, room.get("water", 0) - 0.2)
                room["pot"] = {"what": herb_or_tea, "cups": 3, "temp": 1.0}
                room["dirty_pot"] = True
                parts.append(f"Travis fills the kettle, sets it on the fire, and once it "
                             f"sings, brews a pot of {herb_or_tea}. The steam smells of it.")
        narration = " ".join(parts)

    elif kind == "fetch_wood":
        # THE SAME MECHANISMS (2026-09-05, T-0049): this used to conjure four loads from nowhere. Now it is
        # the errand Du would make — the lean-to's dry stack, the wood's deadfall, the shore's driftwood.
        if st.get("woodpile", 0) >= 3:
            narration = "Travis checks the woodpile — plenty there already."
        else:
            narration = _start_errand(need_wood=True, need_kindling=False, then=None)

    elif kind == "fetch_water":
        if room.get("water", 0) >= 0.7:
            narration = "Travis checks the pail — full enough already."
        else:
            try:
                from core import garden as _g
                g = _g._load()
                barrel = float(g.get("barrel", 0))
                if barrel < 0.1:
                    narration = "Travis takes the pail to the barrel — a trickle, then nothing. It's run dry."
                else:
                    g["barrel"] = round(max(0.0, barrel - 0.1), 3)
                    _g._save(force=True)
                    room["water"] = 1.0
                    narration = "Travis fills the pail at the barrel and carries it in, water slopping over the lip."
            except Exception:
                room["water"] = 1.0
                narration = "Travis fills the pail and carries it in."

    try:
        s._save_now()
    except Exception:
        pass

    _emit(narration)
    _save()
    out = {"ok": True, "narration": narration}
    if _state.get("errand"):
        out["errand"] = True
        out["eta_s"] = _eta_s()
    return out


def status() -> dict:
    if not _state:
        _load()
    _advance()
    er = _state.get("errand")
    return {"present": is_present(), "since_ts": (_state or {}).get("since_ts"),
            "last_activity_ts": _last_activity() or None, "window_s": PRESENCE_WINDOW_S,
            "pending_event": bool(_pending_events),
            "errand": bool(er), "eta_s": _eta_s(),
            "errand_line": (f"Travis is {_out_phrase()} — back in about {max(1, -(-_eta_s() // 60))} min." if er else None),
            "last_narration": _state.get("last_narration")}
