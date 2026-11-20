"""
Nascence - THE SHORE DIG AND TURN-STONE HAND (D-0652, J-3261; docs/staged/shore_creatures.md Open points).

About ten shore creatures cannot be seen by looking: the burrowers (pipi, tuatua, toheroa, cockle, ghost shrimp, ragworm, lugworm, heart
urchin, sand dollar, sand sea cucumber) and the inside-thing (pea crab, inside a mussel). The founder ruled BOTH: a dig / turn-a-stone /
open-a-shell hand (modelled on garden.dig, which calls life.note_deed) so they surface by his deed, AND the traces kept (the mound, the
cast, the dead test: those rows in core/life_shore_cast.py are untouched and still found by a look at the place).

The world answers, nothing leads: no line says the hand exists, names a creature, or says where to dig. What he finds depends on the
tide, the place he stands, the season, the hour and the weather: every candidate must be PRESENT by the life engine's own activity()
(season x hours x weather x tide state) and the site's own tide gate. A find is composed by life_shore.compose() at the detail tier (it is
in his hand) and credited like any sighting (life.credit_find), so a book and a face still make a name (D-0129).

Zero LLM, no prompt, fail-open, additive. Only behind the bestiary flag (data/life_flags.json "shore_bestiary"); with it off the hand
does not exist (shore_life.act_from_thought never reaches it). Restart-gated like every code change.
"""
from __future__ import annotations

import logging
import random
import time

logger = logging.getLogger("nascence.shore_dig")

# site -> where he is digging. "sand" = the flat (bared below 0.45); "wet" = the tideline sand at the water's edge (any tide below 0.6);
# "stone" = turning a stone at the shingle or shelf edge (below 0.5); "shell" = opening a mussel he has gathered.
SITE_MAX_LEVEL = {"sand": 0.45, "wet": 0.60, "stone": 0.50}

# row key -> {site: chance per dig when the row is present, scaled by its activity}. A burrower that lives deeper (ghost shrimp) or is
# rarer (toheroa, protected) is lower. Keys not registered (flag off) are simply skipped.
FINDS = {
    "sand": {"pipi": 0.55, "cockle": 0.55, "toheroa": 0.25, "ghost_shrimp": 0.30, "lugworm": 0.45, "ragworm": 0.30,
             "heart_urchin": 0.25, "sand_dollar": 0.30, "sand_sea_cucumber": 0.30},
    "wet": {"tuatua": 0.55, "pipi": 0.35, "sand_dollar": 0.15},
    "stone": {"ragworm": 0.40},
    "shell": {"pea_crab": 0.12},
}

# What the animal itself looks like when it is out of the sand and in his hand. Rows whose own obs is already the animal (pipi, tuatua,
# toheroa, cockle, ragworm, sand dollar, cucumber, pea crab) are NOT here: they use their registered obs. The three written as the SIGN
# that shows at the surface (mound, cast, dead test) get the living animal here. Validated by life_shore.make_obs at first use.
DUG_OBS = {
    "ghost_shrimp": dict(size_cm=9, span_cm=9, shape="jointed_curve", colour="cream", colour2="tan", pattern="banded", sheen="glassy",
                         covering="smooth", motion="jet", position="half_buried", on_disturb="jets_away"),
    "lugworm": dict(size_cm=18, span_cm=18, shape="soft_worm", colour="dark_brown", colour2="tan", pattern="mottled", sheen="wet_gloss",
                    covering="soft", motion="wriggle", position="half_buried", on_disturb="retracts"),
    "heart_urchin": dict(size_cm=5, span_cm=6, shape="sphere_spines", colour="tan", colour2="cream", pattern="banded", sheen="matt",
                         covering="spined", motion="glide_slow", position="half_buried", on_disturb="buries"),
}

MAX_DIGS_PER_BUCKET = 4
BUCKET_S = 600.0

_NIGHT = "You could not tell sand from shell in this dark; you would only be putting your hands in cold water."
_FLOODED = {"sand": "The flat is under the sea; the sand will bare again as the tide drops.",
            "wet": "The sea is right up the beach; there is no wet sand to dig at the edge of it.",
            "stone": "The stones at the water's edge are awash; they will not be turned until the tide drops."}
_NOTHING = {"sand": ("You dig a hand-deep hole in the wet sand. It darkens, greys, and seeps full of water. Nothing but sand.",
                     "You work your hands down into the sand and lift it out in clots. The hole fills from below as you watch."),
            "wet": ("You scoop a hole in the wet sand at the water's edge; it fills and slumps. Nothing in it.",),
            "stone": ("You lever a stone over. Wet dark sand under it, and a smell of the sea, and nothing that moves.",
                      "You turn a stone. The ground under it is pale and wet, with nothing in it."),
            "shell": ("You prise the shell open with the knife. Only the meat, orange and shut, and nothing else in it.",)}
_TIRED = "Your arms are tired of it and the ground is sodden; leave it a while."
_NO_SHELL = "You have no shell in hand to open."


def _life():
    from core import life as _l
    return _l


def enabled() -> bool:
    """The hand exists only when the shore bestiary is registered (data/life_flags.json "shore_bestiary")."""
    try:
        from core import life_shore as _ls
        return bool(_ls.enabled())
    except Exception:
        return False


def site_for(standpoint: str | None, level: float) -> str:
    """Where a dig lands: at the water's edge when he stands in the shallows, else on the flat."""
    return "wet" if standpoint == "in_the_shallows" else "sand"


def candidates(site: str, now: float | None = None) -> list[dict]:
    """[{'key','row','p','act'}] for the rows a dig at this site could turn up right now: registered, in FINDS[site], present by the
    engine's own activity() (season, hour, weather, tide). Tide gate on the site is the caller's."""
    now = time.time() if now is None else now
    life = _life()
    out = []
    for key, p in FINDS.get(site, {}).items():
        r = life._ROWS.get(key)
        if not r or not r.get("obs"):
            continue
        act = life.activity(r, "shore", now)
        if act < life.PRESENT_AT:
            continue
        out.append({"key": key, "row": r, "p": min(0.9, p * min(act, 1.0)), "act": act})
    return out


def dug_obs(r: dict) -> dict:
    """The observable tuple of the animal as it lies in his hand."""
    from core import life_shore as _ls
    k = r["key"]
    if k in DUG_OBS:
        return _ls.make_obs(**DUG_OBS[k])
    return r["obs"]


def pick(site: str, rng: random.Random, now: float | None = None) -> dict | None:
    """The one candidate a dig turns up (or None). Candidates are tried in a seeded order, each by its own chance."""
    cands = candidates(site, now)
    rng.shuffle(cands)
    for c in cands:
        if rng.random() < c["p"]:
            return c
    return None


def line_for(c: dict, site: str, night: bool = False) -> str:
    from core import life_shore as _ls
    r = c["row"]
    body = _ls.compose(dug_obs(r), "detail", night=night)
    band = ""
    try:
        band = _life()._count_band(r, c["act"])
    except Exception:
        pass
    more = {"a few": " There are a few more where it came from.", "several": " There are several more where it came from.",
            "a scatter": " There are more, scattered about it.", "a bed of them": " There is a whole bed of them under here.",
            "a field of them": " There are many more, all about."}.get(band, "")
    lead = {"sand": "You dig down into the sand, and your fingers close on something. ",
            "wet": "You dig into the wet sand at the water's edge, and something is there. ",
            "stone": "You turn the stone, and something lies under it. ",
            "shell": "You work the shell open with the knife, and there is something inside it. "}[site]
    return lead + body + more


def dig(site: str, state: dict, now: float | None = None, rng: random.Random | None = None) -> str:
    """One deed at a site. `state` is a dict this call may update ('dig_bucket', 'dig_n'); the caller saves it. Returns the world's answer.
    No store write other than life's own deed note and sighting credit."""
    now = time.time() if now is None else now
    life = _life()
    if life._phase(now) == "night":
        return _NIGHT
    if site in SITE_MAX_LEVEL:
        try:
            from core import world_clock as _wc
            level = float(_wc.tide(now)["level"])
        except Exception:
            level = 0.5
        if level >= SITE_MAX_LEVEL[site]:
            return _FLOODED[site]
    bucket = int(now // BUCKET_S)
    if state.get("dig_bucket") != bucket:
        state["dig_bucket"], state["dig_n"] = bucket, 0
    if int(state.get("dig_n", 0)) >= MAX_DIGS_PER_BUCKET:
        return _TIRED
    state["dig_n"] = int(state.get("dig_n", 0)) + 1
    rng = rng or random.Random(f"shore_dig:{site}:{bucket}:{state['dig_n']}")
    try:
        life.note_deed("dig" if site != "stone" else "turn_stone", "shore", now)
    except Exception as exc:
        if exc.__class__.__name__ == "NonLiveWriteError":
            raise
    c = pick(site, rng, now)
    if c is None:
        return rng.choice(_NOTHING[site])
    night = False
    text = line_for(c, site, night)
    try:
        life.credit_find(c["key"], "shore", now, text)
    except Exception as exc:
        if exc.__class__.__name__ == "NonLiveWriteError":
            raise
        logger.debug("[shore_dig] credit_find failed (non-fatal): %s", exc)
    return text
