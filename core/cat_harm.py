"""
core/cat_harm.py — HER MORTALITY: injury, illness, ageing, death on the world's clock, findable not told
=====================================================================================================
2026-10-28 (docs/staged/cat_overhaul.md §B1 "Age and mortality", §4 D-2; D-0506 (Travis): "Yes, all of it";
J-2471; built on J-2465's body, J-2470's fight hook, J-2472's bond-unlocked missing arc). D-0130 made the world
harsh for everything except her — the cat may kill, but nothing could happen TO the cat. Now it can:

  INJURY   a fight with the tom (cat_tom leaves the hook, cat_state "tom": {"fight_hook"}; this file consumes it
           and writes back `her_injury`), a fall (a raised spot: the wall top, the sill, a branch), a possum (out
           at night, beyond the wall). An injury is {kind, where, severity, since, heals_by}: her legs are slower,
           she hunts less, a bad one keeps her from the hunt bout; a look or a presence line may carry the honest
           clause (she favours a foreleg; a torn ear; a scab across the nose) — never the word "injured", never a
           number. Healed, it may leave a scar on her for good.
  ILLNESS  a week off her food: hunger stays high (she refuses the saucer — the food he puts down stays there,
           which is how he finds out), condition falls, she hides (under the desk with the door open, the hedge
           bottom without) in the "lying low" state. Then it passes, and she is ravenous.
  AGEING   from born_ts (J-2465: she arrived adult, 2-3 y, rolled once). Past OLD_AGE_Y her condition drifts
           down, her legs slow, she hunts less, she sleeps more (energy recovers slower), and a look may notice
           the grey about her muzzle. LIFESPAN_Y 14 (LIFE_ROW) is the shape of the hazard, not a date.
  DEATH    on the world's clock: a per-live-day hazard from age (piecewise, rising past OLD_AGE_Y so that about
           half of cats see 14), illness, an unhealed bad injury and starvation. Two modes, both findable and
           neither told: FOUND — she dies where she lay (indoors, the doorstep, the garden by day) and a carcass
           goes through core/life_traces like every other creature's (fresh -> picked -> bones -> gone;
           ambient_carcass / carcass_look / her own found-lines here); AWAY — she goes off to die as cats do
           (out hunting, prowling, mid-missing-arc, or old), and the path is ABSENCE: the saucer untouched,
           the six-hour line that becomes days, the house a quieter house, and never a return.
  BURIAL   his hand: with her body found, "bury her" / "dig her a grave" carries her out to the garden (or buries
           her where she lies at the shore or the wood); the carcass leaves life state (a burial row in
           life_events), the grave is a fact in cat_state, found by a look at her in the garden and, rarely, an
           ambient line about the turned earth settling.

THE CLOCK (the D-0296 fallen-tree caveat, D-0506's own defeater): every roll here happens INSIDE cat.tick, the
one live writer of cat_state.json, on the 180 s movement tick with dt capped at MAX_DT_H (a stopped stretch is
never caught up on, like the body's budgets) — there is no second writer and no lost update. Nothing here is a
background job. The ONE offline path, apply_offline(), exists for a deliberate founder act while Du is stopped
(J-1444's felling pattern: fell_tree() refuses to clobber, writes through the fence's maintenance path, is called
ONCE from a lab-mode script): it REFUSES while scripts/run_nascence.py is running, refuses to stack a second
injury or illness on one in progress, and records applied_by "offline" in the ledger so the defeater can be read.

NO READOUT (D-0434; world answers, never leads): nothing here reaches his prompt as a gauge, a number, a band or
a verdict. He finds her limping, or off her food, or cold under his hand, or not at all. Every line pool rotates
(cat._pick_fresh). The ledger data/cat_harm_ledger.jsonl and status() are read by the HUD only.

Kill switch: data/life_flags.json cat_harm_live (scripts/life_flags.py cat_harm on|off); off = no roll, no harm
applied, but a cat already dead stays dead (state is truth). Zero LLM. Writes only cat.state (saved by cat.tick /
the hands) and its own ledger; life state through life_traces' own functions.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.cat_harm")

_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "cat_harm_ledger.jsonl"
_FLAGS_F = _DATA / "life_flags.json"

LIVE = True                      # code default; hot override: life_flags.json cat_harm_live
_ROTATE_BYTES = 2_000_000
MAX_DT_H = 6.0                   # the body's own cap: a stopped stretch is not caught up on
YEAR_S = 365.25 * 86400.0
DAY_S = 86400.0

# ── ageing ─────────────────────────────────────────────────────────────────────────────────────────────────
OLD_AGE_Y = 10.0                 # from here her condition drifts, her legs slow, she sleeps more
CONDITION_AGE_PER_DAY_PER_Y = 0.004   # x (age - OLD_AGE_Y): at 14 y, -0.016/day against the fed drift's +0.02
AGE_LEG_FACTOR_MAX = 1.35        # her leg seconds at the far end of old age
AGE_HUNT_FACTOR_MIN = 0.5        # her catch odds at the far end of old age
AGE_RECOVER_FACTOR = 0.85        # energy recovery once old (she sleeps longer to get the same back)
# yearly death hazard by age band (lower bound of the band -> hazard per year). Survival to 14 from 2 y =
# exp(-(6*0.01 + 3*0.05 + 3*0.12)) ~ 0.55: about half of cats see fourteen, few see eighteen.
AGE_HAZARD_PER_Y = ((0.0, 0.01), (8.0, 0.05), (11.0, 0.12), (14.0, 0.25), (17.0, 0.50))

# ── injury ─────────────────────────────────────────────────────────────────────────────────────────────────
INJURY_P_FIGHT_WON = 0.15        # she won the fight: a torn ear, a scratched face, sometimes
INJURY_P_FIGHT_LOST = 0.50       # she lost: usually something to show for it
FALL_PER_YEAR = 1.5              # per live year ON a raised spot (the wall top, the sill, the mantel, a branch)
POSSUM_PER_YEAR = 0.8            # per live year OUT at night beyond the wall (away_hunting, prowling, the wood)
_RAISED = frozenset({"garden_wall", "windowsill", "mantel", "on_the_desk"})
_OUT_AT_NIGHT = frozenset({"away_hunting", "garden_wall", "wood", "garden"})
INJURY_SEVERITY = {"fight": (0.15, 0.65), "fall": (0.10, 0.50), "possum": (0.30, 0.80)}
HEAL_DAYS = (4.0, 14.0)          # x severity-weighted: a scratch is days, a bad bite a fortnight
NO_HUNT_SEVERITY = 0.45          # above this she does not hunt at all while it heals
SCAR_P = {"fight": 0.5, "fall": 0.1, "possum": 0.7}
_INJURY_WHERE = {"fight": ("a torn ear", "a bitten shoulder", "a scratched face", "a bitten foreleg"),
                 "fall": ("a wrenched foreleg", "a wrenched hind leg", "a bruised shoulder"),
                 "possum": ("a torn face", "a bitten foreleg", "a ripped ear", "a bitten flank")}
_SCAR_OF = {"a torn ear": "a nick out of the other ear", "a scratched face": "a pale seam across the nose",
            "a torn face": "a pale seam down the cheek", "a ripped ear": "a ragged edge to one ear",
            "a bitten shoulder": "a bare patch on the shoulder where the fur never came back",
            "a bitten foreleg": "a bare line on the foreleg", "a bitten flank": "a bare patch on the flank"}

# ── illness ────────────────────────────────────────────────────────────────────────────────────────────────
ILLNESS_PER_YEAR = 1.2           # per live year, base: a cat is off her food about once a year
ILLNESS_COLD_FACTOR = 2.0        # x when she has been cold a long while (body cold_hours)
ILLNESS_POOR_FACTOR = 2.0        # x when her condition is poor
ILLNESS_OLD_FACTOR = 2.0         # x once old
ILLNESS_DAYS = (4.0, 10.0)       # "a week off her food"
ILLNESS_SEVERITY = (0.3, 1.0)
CONDITION_ILL_PER_DAY = 0.03     # on top of the body's own hungry drift (she is not eating)
ILLNESS_GAP_S = 60 * DAY_S       # at most one bout every two months (a second one that soon reads as the same)

# ── death ──────────────────────────────────────────────────────────────────────────────────────────────────
ILL_DEATH_PER_DAY = 0.002        # x severity (x3 once old): about one bad week in a hundred kills a young cat
INJURY_DEATH_PER_DAY = 0.006     # x max(0, severity - 0.5) x 2 while unhealed
STARVED_BELOW = 0.15             # condition: starvation's own hazard
STARVED_DEATH_PER_DAY = 0.01
POOR_CONDITION_BELOW = 0.20      # condition: an illness / injury hazard doubles here
AWAY_OLD_Y = 12.0                # an old cat goes off to die unless she is indoors
_INDOORS = frozenset({"by_the_fire", "windowsill", "on_the_desk", "on_your_lap", "under_desk", "mantel", "indoors",
                      "under_the_bed", "cupboard_top"})   # C4 (J-2469): her hidden spots in the house are in the house
_DIES_WHERE = {   # where she is -> (life place, the carcass's `where` as carcass_look renders it: "at the {where}")
    "by_the_fire": ("study", "hearth"), "mantel": ("study", "hearth"), "on_your_lap": ("study", "hearth"),
    "under_desk": ("study", "foot of the desk"), "on_the_desk": ("study", "foot of the desk"),
    "windowsill": ("study", "sill"), "indoors": ("study", "skirting"),
    "doorstep": ("garden", "doorstep"), "garden": ("garden", "hedge bottom"), "garden_wall": ("garden", "foot of the wall"),
    "wood": ("wood", "leaf litter"), "shore": ("shore", "tideline"),
    # C4 (J-2469): the reachable hidden spots -- found where she lay; the roof and the far side of the wall stay
    # unlisted, so a death there is a death away (she went off, as cats do)
    "under_the_bed": ("study", "foot of the bed"), "cupboard_top": ("study", "foot of the cupboard"),
    "lean_to": ("garden", "lean-to"), "wood_shed": ("garden", "wood shed"), "hedge_bottom": ("garden", "hedge bottom"),
    "water_butt_lid": ("garden", "water-butt"),
}
_GRAVE_WHERE = {"garden": ("under the kowhai", "by the hedge bottom", "at the foot of the wall", "by the compost"),
                "wood": ("under the oak", "in the leaf litter off the path"), "shore": ("above the tideline, under the flax")}
ABSENCE_GAP_S = 6 * 3600.0       # the absence lines, dosed: at most one per six hours
ABSENCE_P = 0.3                  # ... and then not every render
ABSENCE_LONG_AFTER_D = 21.0      # after three weeks the lines thin (one a day)
GRAVE_GAP_S = DAY_S              # the grave's ambient line: at most daily
GRAVE_P = 0.15
CLAUSE_P = 0.35                  # a look / presence line carries the honest clause this often
AGE_CLAUSE_P = 0.2
SCAR_CLAUSE_P = 0.1

_HAND_BURY = ("bury", "buried", "burial", "grave", "dig her", "dig a", "lay her", "spade")
_HAND_TEND = ("stroke", "touch", "pick up", "pick her up", "hold", "lift", "put a hand", "put my hand", "go to her", "kneel")
_CAT_WORDS = ("cat", "kitten", "stray", "moggy", "her body", "the body")   # + her name: the hand must name her (cat.react's own rule)

_rng = random.Random()           # ITS OWN RNG: the harnesses patch random.random to drive the cat's own rolls;
                                 # a hazard must not fire because a sibling test wanted a stroke to land
_flags_cache: dict = {"ts": 0.0, "v": {}}


def _roll() -> float:
    return _rng.random()


def _uniform(a: float, b: float) -> float:
    return _rng.uniform(a, b)


def _choice(seq):
    return _rng.choice(list(seq))


# ── flags / io ─────────────────────────────────────────────────────────────────────────────────────────────
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
    v = _flags().get("cat_harm_live")
    return bool(LIVE if v is None else v)


def _log(row: dict) -> None:
    path = profile.guard_path(_LEDGER)   # real data/ only if this process is live; raises before any I/O if not (D-0179)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if path.exists() and path.stat().st_size > _ROTATE_BYTES:
                path.replace(path.with_suffix(path.suffix + ".1"))
        except Exception:
            pass
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[cat_harm] ledger write failed (non-fatal): %s", exc)


# ── state ──────────────────────────────────────────────────────────────────────────────────────────────────
def fresh() -> dict:
    return {"injury": None, "illness": None, "scars": [], "injuries": 0, "illnesses": 0,
            "last_injury_ts": 0.0, "last_illness_ts": 0.0, "fight_hook_seen": 0.0,
            "death": None, "grave": None, "last_ts": 0.0,
            "last_absence_line_ts": 0.0, "last_grave_line_ts": 0.0}


def _h(state: dict) -> dict:
    h = state.get("harm")
    if not isinstance(h, dict):
        h = fresh()
        state["harm"] = h
    for k, v in fresh().items():
        h.setdefault(k, v)
    return h


def _age_y(state: dict, now: float) -> float:
    try:
        from core import cat as _cat
        born = float(state.get("born_ts") or 0.0)
        if not born:
            born = float(state.get("appeared_ts") or now) - _cat.ARRIVED_AGE_Y[0] * YEAR_S
        return max(0.0, (now - born) / YEAR_S)
    except Exception:
        return 0.0


def _cat_pick(key: str, lines) -> str:
    """One rotating line through cat._pick_fresh (its ring lives in cat.state, persisted)."""
    try:
        from core import cat as _cat
        return _cat._pick_fresh(f"HARM:{key}", list(lines))
    except Exception:
        return _choice(lines) if lines else ""


def _pool(section: str, key: str) -> str:
    """A rotating line from cat_content.HARM[key] (a flat list) or cat_content.<section>[key]; {her} rendered."""
    try:
        from core import cat as _cat
        from core import cat_content as cc
        sec = getattr(cc, section, None) or {}
        spec = sec.get(key)
        if spec is None:
            return ""
        if isinstance(spec, dict):
            conds = _cat._conds()
            lines = [l for cond, ls in spec.items() if cond in conds for l in ls]
        else:
            lines = list(spec)
        if not lines:
            return ""
        line = _cat_pick(f"{section}:{key}", lines).replace("{her}", _cat._her())
        return line[:1].upper() + line[1:]
    except Exception:
        return ""


# ── reads (cat.py's hooks; HUD) ────────────────────────────────────────────────────────────────────────────
def is_dead(state: dict) -> bool:
    return str((state or {}).get("phase") or "") == "dead"


def is_ill(state: dict) -> bool:
    return bool((((state or {}).get("harm") or {}).get("illness")))


def injury(state: dict) -> dict | None:
    i = ((state or {}).get("harm") or {}).get("injury")
    return i if isinstance(i, dict) else None


def is_old(state: dict, now: float | None = None) -> bool:
    return _age_y(state, now or time.time()) >= OLD_AGE_Y


def off_her_food(state: dict) -> bool:
    """She will not eat: ill. The saucer he fills stays full (cat._maybe_empty_saucer waits), eat() is not called."""
    return is_ill(state)


def legs_factor(state: dict, now: float | None = None) -> float:
    """x on her leg seconds: an injury slows her by its severity, old age by up to AGE_LEG_FACTOR_MAX."""
    f = 1.0
    i = injury(state)
    if i:
        f += float(i.get("severity") or 0.0)
    age = _age_y(state, now or time.time())
    if age >= OLD_AGE_Y:
        f *= 1.0 + (AGE_LEG_FACTOR_MAX - 1.0) * min(1.0, (age - OLD_AGE_Y) / 5.0)
    return f


def hunt_factor(state: dict, now: float | None = None) -> float:
    """x on her catch odds (cat._maybe_self_feed): 0 while ill (she does not hunt), down with an injury and age."""
    if is_ill(state):
        return 0.0
    f = 1.0
    i = injury(state)
    if i:
        f *= max(0.0, 1.0 - 0.7 * float(i.get("severity") or 0.0))
    age = _age_y(state, now or time.time())
    if age >= OLD_AGE_Y:
        f *= 1.0 - (1.0 - AGE_HUNT_FACTOR_MIN) * min(1.0, (age - OLD_AGE_Y) / 5.0)
    return f


def no_hunt_bout(state: dict) -> bool:
    """A hunt bout becomes a doze: ill, or a bad injury healing."""
    if is_ill(state):
        return True
    i = injury(state)
    return bool(i and float(i.get("severity") or 0.0) > NO_HUNT_SEVERITY)


def recover_factor(state: dict, now: float | None = None) -> float:
    return AGE_RECOVER_FACTOR if is_old(state, now) else 1.0


def condition_drift(state: dict, dt_d: float, now: float | None = None) -> float:
    """The extra condition drift per `dt_d` days (negative): illness, and age past OLD_AGE_Y."""
    d = 0.0
    if is_ill(state):
        d -= CONDITION_ILL_PER_DAY * dt_d
    age = _age_y(state, now or time.time())
    if age >= OLD_AGE_Y:
        d -= CONDITION_AGE_PER_DAY_PER_Y * (age - OLD_AGE_Y) * dt_d
    return d


def hide_spot(door_open: bool, location: str) -> str:
    """Where an ill cat lies low: under the desk when she can get in (indoors already, or the door open), the
    hedge bottom (garden) when she cannot."""
    if location in _INDOORS or door_open:
        return "under_desk"
    return "garden"


# ── the roll (from cat.tick, on the 180 s movement tick, after the body) ───────────────────────────────────
def tick(state: dict, now: float, phase: str, door_open: bool) -> str | None:
    """Advance her harm over the live time since the last pass. Returns "died" when she died this tick (cat.tick
    saves and returns), else None. Mutates `state` only (cat.tick's own _save covers it); logs its own rows."""
    if not state or state.get("phase") not in ("kept", "companion"):
        return None
    h = _h(state)
    last = float(h.get("last_ts") or 0.0)
    dt_h = max(0.0, min(MAX_DT_H, (now - last) / 3600.0)) if last else 0.0
    h["last_ts"] = now
    if not live_on():
        return None
    dt_d = dt_h / 24.0
    age = _age_y(state, now)
    b = state.get("body") or {}
    cond = float(b.get("condition", 0.7))
    loc, act = str(state.get("location") or ""), str(state.get("activity") or "")
    # 1. the fight hook (cat_tom._fight leaves it; consumed once, by its ts)
    try:
        hook = (state.get("tom") or {}).get("fight_hook")
        if isinstance(hook, dict) and float(hook.get("ts") or 0.0) > float(h.get("fight_hook_seen") or 0.0):
            h["fight_hook_seen"] = float(hook.get("ts") or now)
            if not h.get("injury"):
                p = INJURY_P_FIGHT_WON if hook.get("outcome") == "she_wins" else INJURY_P_FIGHT_LOST
                if _roll() < p:
                    inj = _begin_injury(state, h, "fight", now, "tick", age, cond)
                    hook["her_injury"] = {"where": inj["where"], "severity": inj["severity"], "heals_by": inj["heals_by"]}
                else:
                    hook["her_injury"] = {"none": True}
    except Exception as exc:
        logger.debug("[cat_harm] fight hook failed (non-fatal): %s", exc)
    # 2. a fall, a possum — hazards per live year in the states where they can happen
    if not h.get("injury") and dt_d > 0.0:
        hz = 0.0
        if loc in _RAISED or "branch" in act:
            hz += FALL_PER_YEAR * (1.0 + (0.5 if age >= OLD_AGE_Y else 0.0))
        if phase == "night" and (loc in _OUT_AT_NIGHT or act in ("prowling", "hunting")) and loc not in _INDOORS:
            hz += POSSUM_PER_YEAR * _possum_factor()
        if hz > 0.0 and _roll() < hz * dt_d / 365.25:
            kind = "fall" if (loc in _RAISED or "branch" in act) and (phase != "night" or _roll() < 0.5) else "possum"
            _begin_injury(state, h, kind, now, "tick", age, cond)
    # 3. healing
    inj = h.get("injury")
    if inj and now >= float(inj.get("heals_by") or 0.0):
        _heal(state, h, now, age, cond)
    # 4. illness: begins; ends
    ill = h.get("illness")
    if ill:
        if now >= float(ill.get("until") or 0.0):
            h["illness"] = None
            h["last_illness_ts"] = now
            _log({"ts": round(now, 1), "kind": "recovered", "days": round((now - float(ill.get("since") or now)) / DAY_S, 1),
                  "age_y": round(age, 2), "condition": round(cond, 3), "applied_by": "tick"})
    elif dt_d > 0.0 and now - float(h.get("last_illness_ts") or 0.0) >= ILLNESS_GAP_S:
        rate = ILLNESS_PER_YEAR
        if float(b.get("cold_hours", 0.0)) > 48.0:
            rate *= ILLNESS_COLD_FACTOR
        if cond < 0.4:
            rate *= ILLNESS_POOR_FACTOR
        if age >= OLD_AGE_Y:
            rate *= ILLNESS_OLD_FACTOR
        if _roll() < rate * dt_d / 365.25:
            _begin_illness(state, h, now, "tick", age, cond)
    # 5. death
    if dt_d > 0.0:
        hz = _death_hazard_per_day(h, age, cond)
        if hz > 0.0 and _roll() < hz * dt_d:
            _die(state, h, now, door_open, age, cond)
            return "died"
    return None


def _possum_factor() -> float:
    """The possum is about (life's own row, present in the garden) -> 1.0; absent -> 0.3 (she is beyond the wall,
    where the rows do not reach); no row -> 1.0."""
    try:
        from core import life as _life
        r = _life.rows().get("possum")
        if not r:
            return 1.0
        return 1.0 if _life.activity(r, "garden") >= _life.PRESENT_AT else 0.3
    except Exception:
        return 1.0


def _begin_injury(state: dict, h: dict, kind: str, now: float, by: str, age: float, cond: float,
                  severity: float | None = None) -> dict:
    lo, hi = INJURY_SEVERITY.get(kind, (0.2, 0.6))
    sev = round(float(severity) if severity is not None else _uniform(lo, hi), 3)
    where = _choice(_INJURY_WHERE.get(kind) or ("a hurt foreleg",))
    d_lo, d_hi = HEAL_DAYS
    days = d_lo + (d_hi - d_lo) * sev
    inj = {"kind": kind, "where": where, "severity": sev, "since": now, "heals_by": now + days * DAY_S}
    h["injury"] = inj
    h["injuries"] = int(h.get("injuries", 0)) + 1
    h["last_injury_ts"] = now
    _log({"ts": round(now, 1), "kind": "injury", "cause": kind, "where": where, "severity": sev, "heal_days": round(days, 1),
          "age_y": round(age, 2), "condition": round(cond, 3), "her": {"loc": state.get("location"), "act": state.get("activity")},
          "applied_by": by})
    return inj


def _heal(state: dict, h: dict, now: float, age: float, cond: float) -> None:
    inj = h.get("injury") or {}
    scar = None
    if _roll() < SCAR_P.get(str(inj.get("kind")), 0.2):
        scar = _SCAR_OF.get(str(inj.get("where")))
        if scar and scar not in h.setdefault("scars", []):
            h["scars"].append(scar)
    h["injury"] = None
    _log({"ts": round(now, 1), "kind": "healed", "cause": inj.get("kind"), "where": inj.get("where"), "scar": scar,
          "age_y": round(age, 2), "condition": round(cond, 3), "applied_by": "tick"})


def _begin_illness(state: dict, h: dict, now: float, by: str, age: float, cond: float,
                   severity: float | None = None, days: float | None = None) -> dict:
    sev = round(float(severity) if severity is not None else _uniform(*ILLNESS_SEVERITY), 3)
    d = float(days) if days is not None else _uniform(*ILLNESS_DAYS)
    ill = {"kind": "off_her_food", "severity": sev, "since": now, "until": now + d * DAY_S}
    h["illness"] = ill
    h["illnesses"] = int(h.get("illnesses", 0)) + 1
    _log({"ts": round(now, 1), "kind": "illness", "severity": sev, "days": round(d, 1), "age_y": round(age, 2),
          "condition": round(cond, 3), "her": {"loc": state.get("location"), "act": state.get("activity")}, "applied_by": by})
    return ill


def _death_hazard_per_day(h: dict, age: float, cond: float) -> float:
    per_y = 0.0
    for lo, v in AGE_HAZARD_PER_Y:
        if age >= lo:
            per_y = v
    hz = per_y / 365.25
    ill = h.get("illness") or {}
    if ill:
        hz += ILL_DEATH_PER_DAY * float(ill.get("severity") or 0.5) * (3.0 if age >= OLD_AGE_Y else 1.0) * (2.0 if cond < POOR_CONDITION_BELOW else 1.0)
    inj = h.get("injury") or {}
    if inj:
        hz += INJURY_DEATH_PER_DAY * max(0.0, float(inj.get("severity") or 0.0) - 0.5) * 2.0 * (2.0 if cond < POOR_CONDITION_BELOW else 1.0)
    if cond < STARVED_BELOW:
        hz += STARVED_DEATH_PER_DAY
    return hz


def _cause(h: dict, cond: float, age: float) -> str:
    inj, ill = h.get("injury") or {}, h.get("illness") or {}
    if ill and (not inj or float(ill.get("severity") or 0) >= float(inj.get("severity") or 0)):
        return "illness"
    if inj and float(inj.get("severity") or 0.0) > 0.5:
        return str(inj.get("kind") or "injury")
    if cond < STARVED_BELOW:
        return "starved"
    if ill:
        return "illness"
    if inj:
        return str(inj.get("kind") or "injury")
    return "age"


def _die(state: dict, h: dict, now: float, door_open: bool, age: float, cond: float, cause: str | None = None,
         by: str = "tick") -> dict:
    """She dies: FOUND where she lay (a carcass through life_traces) or AWAY (absence). Phase -> "dead"."""
    cause = cause or _cause(h, cond, age)
    loc = str(state.get("location") or "")
    arc = (state.get("arc") or {}).get("kind")
    spot = _DIES_WHERE.get(loc)
    away = spot is None or arc == "gone_missing" or loc == "in_transit"
    if not away and age >= AWAY_OLD_Y and loc not in _INDOORS and loc != "doorstep":
        away = True
    if not away and loc in ("garden", "garden_wall") and _roll() < 0.3:
        away = True   # even in the garden a cat may slip under the hedge and on, out of sight
    death = {"ts": now, "cause": cause, "mode": "away" if away else "found", "age_y": round(age, 2),
             "place": None if away else spot[0], "where": None if away else spot[1], "carcass_id": None,
             "found_ts": 0.0, "last_loc": loc}
    if not away:
        try:
            from core import life_traces as _lt
            c = _lt.add_carcass("cat", spot[0], spot[1], cause, now)
            death["carcass_id"] = c.get("id")
        except profile.NonLiveWriteError:
            raise
        except Exception as exc:
            logger.debug("[cat_harm] carcass failed (non-fatal): %s", exc)
    h["death"] = death
    h["injury"], h["illness"] = None, None
    state["phase"] = "dead"
    state["location"], state["activity"], state["mood"] = "gone", "gone", ""
    state["arc"], state["reaction"], state["transit"] = {}, None, None
    state["position"] = [0.0, 0.0, 0.0]
    try:
        bdy = state.get("body") or {}
        bdy["bout"], bdy["bout_until"] = "", 0.0
    except Exception:
        pass
    _log({"ts": round(now, 1), "kind": "death", "cause": cause, "mode": death["mode"], "place": death["place"],
          "where": death["where"], "age_y": round(age, 2), "condition": round(cond, 3), "last_loc": loc,
          "bond": round(float(state.get("bond", 0) or 0.0), 3), "applied_by": by})
    try:
        from core import activity_memory
        activity_memory.record("cat_died", death["mode"])   # the fact, truth-side; never a prompt line
    except Exception:
        pass
    return death


# ── her body, found (the FOUND mode) ────────────────────────────────────────────────────────────────────────
def _carcass(state: dict, now: float) -> dict | None:
    """Her carcass row in life state, if it is still there (life_traces' stages; gone = None)."""
    d = ((state.get("harm") or {}).get("death")) or {}
    cid = d.get("carcass_id")
    if not cid:
        return None
    try:
        from core import life_traces as _lt
        for c in _lt.carcasses_at(str(d.get("place") or ""), now):
            if c.get("id") == cid:
                return c
    except Exception:
        return None
    return None


def _stage(c: dict, now: float) -> str:
    """The carcass's stage on the world's clock NOW (life_traces.carcass_state), not the row's last carcass_pass stamp."""
    try:
        from core import life_traces as _lt
        s = _lt.carcass_state(c, now)
        return s if s in ("fresh", "picked", "bones") else "bones"
    except Exception:
        return str(c.get("state") or "fresh")


def _note_found(state: dict, c: dict, now: float) -> None:
    """He found her: the carcass is `noticed` (life's own flag, saved), the death records the finding."""
    h = _h(state)
    d = h.get("death") or {}
    if not d.get("found_ts"):
        d["found_ts"] = now
        _log({"ts": round(now, 1), "kind": "found", "mode": "found", "stage": _stage(c, now), "place": c.get("place"),
              "days_after": round((now - float(d.get("ts") or now)) / DAY_S, 2), "applied_by": "tick"})
    if not c.get("noticed"):
        c["noticed"] = True
        try:
            from core import life as _life
            _life._save(force=True)
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass


def found_line(state: dict, his_location: str, now: float | None = None) -> str:
    """The FOUND path, for cat.presence_line: her body where she lies, by its stage, when he is at that place —
    once (then the look answers). '' otherwise."""
    now = time.time() if now is None else now
    c = _carcass(state, now)
    if not c or c.get("place") != his_location or c.get("noticed"):
        return ""
    stage = _stage(c, now)
    line = _pool("HARM", f"found_{stage}")
    if line:
        line = line.replace("{where}", str(c.get("where") or "here"))
        _note_found(state, c, now)
    return line


def _grave_age_key(now: float, grave: dict) -> str:
    days = (now - float(grave.get("ts") or now)) / DAY_S
    return "grave_fresh" if days < 7 else "grave_settled" if days < 60 else "grave_old"


def absence_line(state: dict, his_location: str, now: float | None = None) -> str:
    """The ABSENCE path (and the found cat's own house without her), for cat.presence_line: dosed, rotating, by
    how long it has been; the grave in the garden, rarer still. Never a verdict."""
    now = time.time() if now is None else now
    h = _h(state)
    d = h.get("death") or {}
    if not d:
        return ""
    g = h.get("grave")
    if g and his_location == g.get("place") and now - float(h.get("last_grave_line_ts") or 0.0) >= GRAVE_GAP_S and random.random() < GRAVE_P:
        line = _pool("HARM", _grave_age_key(now, g))
        if line:
            h["last_grave_line_ts"] = now
            return line.replace("{where}", str(g.get("where") or "in the garden"))
    if his_location not in ("study", "garden"):
        return ""
    days = (now - float(d.get("ts") or now)) / DAY_S
    gap = ABSENCE_GAP_S if days < ABSENCE_LONG_AFTER_D else 4 * ABSENCE_GAP_S
    if now - float(h.get("last_absence_line_ts") or 0.0) < gap or random.random() > ABSENCE_P:
        return ""
    if d.get("mode") == "found" and not d.get("found_ts") and days < 3:
        return ""   # her body is still to be found; the house does not say she is gone before he knows it
    key = "absence_early" if days < 3 else "absence_mid" if days < ABSENCE_LONG_AFTER_D else "absence_long"
    line = _pool("HARM", key)
    if line:
        h["last_absence_line_ts"] = now
        if "{saucer}" in line:
            try:
                from core import cat as _cat
                line = line.replace("{saucer}", _cat._saucer_absence_line())
            except Exception:
                line = line.replace("{saucer}", "her saucer sits by the door")
    return line


def look(state: dict, his_location: str, target: str = "", now: float | None = None) -> str:
    """A dead cat, looked for: her body where it lies (and he is), the grave (in its place), else the honest
    nothing — '' is never returned (the caller returns this)."""
    now = time.time() if now is None else now
    h = _h(state)
    c = _carcass(state, now)
    if c and c.get("place") == his_location:
        stage = _stage(c, now)
        line = _pool("HARM", f"look_{stage}").replace("{where}", str(c.get("where") or "here"))
        _note_found(state, c, now)
        if line:
            return line
    g = h.get("grave")
    if g and his_location == g.get("place"):
        line = _pool("HARM", "look_" + _grave_age_key(now, g)).replace("{where}", str(g.get("where") or "in the garden"))
        if line:
            return line
    line = _pool("HARM", "look_nothing")
    if "{saucer}" in line:
        try:
            from core import cat as _cat
            line = line.replace("{saucer}", _cat._saucer_absence_line())
        except Exception:
            line = line.replace("{saucer}", "her saucer sits by the door")
    return line or "You look for her: nothing."


def clause(state: dict, now: float | None = None, dosed: bool = True) -> str:
    """The honest clause a look or a presence line may carry: an injury's own mark (she favours a foreleg, the
    torn ear), an illness (thin, dull, not eating), old age (the grey muzzle), an old scar. Prose, never a word
    that judges. '' most of the time (CLAUSE_P) when dosed."""
    now = time.time() if now is None else now
    h = state.get("harm") or {}
    inj, ill = h.get("injury") or {}, h.get("illness") or {}
    if inj and (not dosed or random.random() < CLAUSE_P):
        kind = str(inj.get("kind") or "fight")
        line = _pool("HARM", f"clause_{kind}")
        return line.replace("{where}", str(inj.get("where") or "a foreleg"))
    if ill and (not dosed or random.random() < CLAUSE_P):
        return _pool("HARM", "clause_ill")
    if _age_y(state, now) >= OLD_AGE_Y + 1.0 and (not dosed or random.random() < AGE_CLAUSE_P):
        return _pool("HARM", "clause_old")
    scars = h.get("scars") or []
    if scars and (not dosed or random.random() < SCAR_CLAUSE_P):
        return _pool("HARM", "clause_scar").replace("{scar}", str(_choice(scars)))
    return ""


# ── his hands on a dead cat ─────────────────────────────────────────────────────────────────────────────────
def hand(state: dict, thought: str, intention: str, his_location: str, now: float | None = None) -> str | None:
    """cat.react's dead branch: burying her (the carcass found, him where it lies or in the garden), or a hand
    laid on her body where it lies. None when there is nothing here to act on."""
    now = time.time() if now is None else now
    txt = f"{thought} {intention}".lower()
    c = _carcass(state, now)
    if not c or not his_location:
        return None
    name_l = str(state.get("name") or "").lower()
    if not (any(w in txt for w in _CAT_WORDS) or (name_l and name_l in txt)):
        return None   # a thought that does not name her is a thought, never a hand (A2's own rule)
    here = c.get("place") == his_location
    if any(w in txt for w in _HAND_BURY):
        if not here and his_location != "garden":
            return None
        if not here and not (((state.get("harm") or {}).get("death") or {}).get("found_ts")):
            return None   # he cannot bury what he has not found
        return bury(state, his_location, now)
    if here and any(w in txt for w in _HAND_TEND):
        _note_found(state, c, now)
        stage = _stage(c, now)
        return _pool("HARM", "hand_fresh" if stage == "fresh" else "hand_later")
    return None


def bury(state: dict, his_location: str, now: float | None = None) -> str | None:
    """The burial: her carcass leaves life state (a burial row in life_events), the grave becomes a fact of the
    place — the garden, or where she lay at the shore / in the wood. Returns the line, or None without a body."""
    now = time.time() if now is None else now
    h = _h(state)
    c = _carcass(state, now)
    if not c:
        return None
    place = his_location if his_location in ("garden", "wood", "shore") else "garden"
    if c.get("place") in ("wood", "shore") and his_location == c.get("place"):
        place = str(c.get("place"))
    where = _choice(_GRAVE_WHERE.get(place) or _GRAVE_WHERE["garden"])
    try:
        from core import life as _life
        st = _life._load()
        st["carcasses"] = [x for x in (st.get("carcasses") or []) if x.get("id") != c.get("id")]
        _life._save(force=True)
        _life._log(_life._EVENTS, {"kind": "burial", "key": "cat", "place": place, "where": where, "carcass": c.get("id")})
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat_harm] burial in life state failed (non-fatal): %s", exc)
    h["grave"] = {"ts": now, "place": place, "where": where, "from": c.get("place")}
    d = h.get("death") or {}
    if not d.get("found_ts"):
        d["found_ts"] = now
    _log({"ts": round(now, 1), "kind": "burial", "place": place, "where": where, "from": c.get("place"), "stage": _stage(c, now),
          "days_after": round((now - float(d.get("ts") or now)) / DAY_S, 2), "applied_by": "hand"})
    try:
        from core import activity_memory
        activity_memory.record("buried_the_cat", where)
    except Exception:
        pass
    key = "bury_carried" if c.get("place") != place else "bury_here"
    line = _pool("HARM", key).replace("{where}", where)
    return line or f"You bury her {where}."


def affordance(state: dict, his_location: str, now: float | None = None) -> str:
    """cat.affordance_line's dead / ill branches: the spade only once he has FOUND her (an offer before that would
    tell him); an ill cat asks to be left be. '' when nothing is offered."""
    now = time.time() if now is None else now
    if is_dead(state):
        d = ((state.get("harm") or {}).get("death")) or {}
        c = _carcass(state, now)
        if c and d.get("found_ts") and (c.get("place") == his_location or his_location == "garden"):
            return _lower(_pool("HARM", "afford_bury"))
        return ""
    if is_ill(state):
        return _lower(_pool("HARM", "afford_ill"))
    return ""


def _lower(line: str) -> str:
    """Affordance lines are lower-case by cat.affordance_line's own convention ("coax the wary STRAY ...")."""
    return line[:1].lower() + line[1:] if line else line


# ── offline application (the fell_tree pattern; never from a live tick) ────────────────────────────────────
def _du_running() -> bool:
    """Is scripts/run_nascence.py running? Can't tell -> True (refuse)."""
    try:
        import subprocess
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ForEach-Object { $_.CommandLine }"],
            capture_output=True, text=True, timeout=30).stdout
        return "run_nascence.py" in out
    except Exception:
        return True


def apply_offline(kind: str, severity: float | None = None, days: float | None = None, now: float | None = None) -> dict:
    """A deliberate act while Du is STOPPED (D-0506's clock rule, J-1444's felling pattern): `kind` is "injury:fight"
    / "injury:fall" / "injury:possum" / "illness". Refuses while Du runs (a lost update on cat_state.json is the
    defeater), refuses to stack on an injury / illness already in progress, writes through cat._save (the fence's
    own maintenance path: a non-live caller must profile / mark itself, exactly as fell_tree's caller must), and
    records applied_by "offline". Returns what was applied, or {"refused": why}."""
    now = time.time() if now is None else now
    if _du_running():
        _log({"ts": round(now, 1), "kind": "offline_refused", "why": "du_running", "asked": kind})
        return {"refused": "du_running"}
    from core import cat as _cat
    state = _cat._load()
    if state.get("phase") not in ("kept", "companion"):
        return {"refused": f"phase {state.get('phase')}"}
    h = _h(state)
    age = _age_y(state, now)
    cond = float((state.get("body") or {}).get("condition", 0.7))
    if kind.startswith("injury"):
        if h.get("injury"):
            return {"refused": "injury in progress"}
        sub = kind.split(":", 1)[1] if ":" in kind else "fall"
        if sub not in INJURY_SEVERITY:
            return {"refused": f"unknown injury kind {sub}"}
        out = _begin_injury(state, h, sub, now, "offline", age, cond, severity=severity)
    elif kind == "illness":
        if h.get("illness"):
            return {"refused": "illness in progress"}
        out = _begin_illness(state, h, now, "offline", age, cond, severity=severity, days=days)
    else:
        return {"refused": f"unknown kind {kind}"}
    _cat._save()
    return dict(out)


# ── HUD ────────────────────────────────────────────────────────────────────────────────────────────────────
def status(now: float | None = None) -> dict:
    """HUD only. Never read by anything in a prompt path (D-0434)."""
    now = time.time() if now is None else now
    try:
        from core import cat as _cat
        st = _cat._load()
    except Exception:
        st = {}
    h = (st or {}).get("harm") or {}
    try:
        n = sum(1 for _ in open(_LEDGER, encoding="utf-8")) if _LEDGER.exists() else 0
    except Exception:
        n = 0
    return {"live": live_on(), "phase": st.get("phase"), "age_y": round(_age_y(st, now), 2) if st else None,
            "injury": h.get("injury"), "illness": h.get("illness"), "scars": h.get("scars"),
            "injuries": h.get("injuries"), "illnesses": h.get("illnesses"), "death": h.get("death"), "grave": h.get("grave"),
            "ledger_rows": n}
