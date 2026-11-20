"""
Nascence - THE WOOD TURN-STONE / PEEL-BARK HAND (D-0714, J-3812; docs/staged/wood_creatures.md Open points).

About thirty wood creatures cannot be seen by looking: the things under stones, under loose bark, in the leaf mould and under the stones of
the stream (grubs and beetles under bark, centipedes, millipedes, springtails, the peripatus, the land flatworm, the stream nymphs and
amphipods ...). D-0714 ruled: confirm the ASSUMED placements as they are (South Island, Sumner, D-0655) and build ONE small woods hand
modelled on the garden dig and the shore hand (core/shore_dig.py, D-0652). This is it: turn a stone, peel loose bark / lift a log, and turn
a stone in the stream.

The world answers, nothing leads: no line says the hand exists, names a creature, or says where to look. What he finds depends on the
season, the hour and the weather: every candidate must be PRESENT by the life engine's own activity() at the wood. A find is composed by
life_shore.compose() at the detail tier (it is in his hand) and credited like any sighting (life.credit_find), so a book and a face still
make a name (D-0129). The trace rows a look at the place shows are untouched.

South Island (D-0714 / D-0655): the eleven North-Island-only rows are never offered here (NORTH_ONLY). Their rows in
core/life_wood_cast.py are untouched by this job.

Zero LLM, no prompt, fail-open, additive. Only behind the bestiary flag (data/life_flags.json "wood_bestiary"); with it off the hand does not
exist (wood_life.act_from_thought never reaches it). Restart-gated like every code change.
"""
from __future__ import annotations

import logging
import random
import re
import time

logger = logging.getLogger("nascence.wood_dig")

# "stone" = turning a stone on the floor of the wood; "bark" = peeling loose bark off dead wood or lifting a log; "stream" = turning a
# stone in the (ASSUMED, now confirmed as it is) stream.
SITES = ("stone", "bark", "stream")

# Rows (life_wood_cast.py keys) that are North-Island-only per the list; never turned up on the South Island.
NORTH_ONLY = frozenset({"giraffe_weevil", "emperor_gum_moth", "common_katydid", "tunnelweb_spider", "freshwater_limpet", "hochstetters_frog",
                        "whitehead", "indian_myna", "eastern_rosella", "spotted_dove", "barn_owl"})

# site -> {row key: chance per turn when the row is present, scaled by its activity}. Rarer or deeper = lower. Keys not registered (flag
# off) are simply skipped.
FINDS = {
    "stone": {"forest_ground_beetle": 0.30, "darkling_beetle": 0.30, "ground_weta": 0.30, "stone_centipede": 0.40, "native_millipede": 0.35,
              "springtail": 0.30, "mite_harvestman": 0.15, "small_land_snail": 0.20, "carnivorous_snail": 0.15, "keeled_slug": 0.30,
              "native_earthworm": 0.40, "black_native_ant": 0.40, "white_tailed_spider": 0.20, "copper_skink": 0.08, "brown_skink": 0.10,
              "land_flatworm": 0.12, "cutworm": 0.20, "european_earwig": 0.20, "pseudoscorpion": 0.08, "trapdoor_spider": 0.04,
              "vegetable_caterpillar": 0.03},
    "bark": {"pie_dish_beetle": 0.35, "longhorn_beetle": 0.25, "stag_beetle": 0.10, "bracket_fungus_beetle": 0.30, "pine_bark_beetle": 0.30,
             "flat_backed_millipede": 0.35, "giant_centipede": 0.15, "forest_cave_weta": 0.20, "european_earwig": 0.35, "dampwood_termite": 0.08,
             "peripatus": 0.06, "land_flatworm": 0.12, "leopard_slug": 0.20, "daddy_long_legs_spider": 0.30, "hunter_ant": 0.20,
             "ornate_skink": 0.05, "white_tailed_spider": 0.20, "barklouse": 0.10, "pseudoscorpion": 0.08},
    "stream": {"mayfly_nymph": 0.40, "stonefly_nymph": 0.35, "caddisfly_larva": 0.40, "freshwater_amphipod": 0.35, "freshwater_shrimp": 0.30,
               "mud_snail": 0.30, "bladder_snail": 0.20, "freshwater_mussel": 0.12, "common_bully": 0.12, "redfin_bully": 0.10,
               "banded_kokopu": 0.05, "koaro": 0.05, "diving_beetle": 0.10, "freshwater_crayfish": 0.15, "horsehair_worm": 0.03},
}

MAX_TURNS_PER_BUCKET = 4
BUCKET_S = 600.0

_NIGHT = "You could not tell bark from stone in this dark; you would only be putting your hands to cold, wet wood."
_NOTHING = {"stone": ("You lever a stone over. Black damp earth under it, a few white threads of root, and nothing that moves.",
                      "You turn a stone. The ground under it is pale and pressed flat, and nothing is there."),
            "bark": ("You work your fingers under a loose strip of bark and peel it back. Brown dust and old tunnels, and nothing in them.",
                     "You lift a piece of bark from the dead wood. The wood beneath it is damp and grey and bare."),
            "stream": ("You turn a stone in the stream. The silt blooms and drifts off, and there is nothing under it.",
                       "You lift a stone out of the water and the cold runs up your wrist. Bare, slick, and nothing clinging to it.")}
_TIRED = "Your hands are numb and gritty with it; leave it a while."

_STREAM_WORDS = ("stream", "spring", "brook", "creek", "gully", "water", "pool")


def _life():
    from core import life as _l
    return _l


def enabled() -> bool:
    """The hand exists only when the wood bestiary is registered (data/life_flags.json "wood_bestiary")."""
    try:
        from core import life_wood as _lw
        return bool(_lw.enabled())
    except Exception:
        return False


def site_for(text: str) -> str:
    """Which of the three sites a willed thought is about: water words = the stream; bark / peel / log = the bark; else a floor stone."""
    t = (text or "").lower()
    if any(re.search(r"\b" + w + r"\b", t) for w in _STREAM_WORDS):
        return "stream"
    if re.search(r"\b(bark|peel|log|logs|stump)\b", t):
        return "bark"
    return "stone"


def candidates(site: str, now: float | None = None) -> list[dict]:
    """[{'key','row','p','act'}] for the rows a turn at this site could turn up right now: registered, in FINDS[site], not North-Island-only,
    present by the engine's own activity() (season, hour, weather)."""
    now = time.time() if now is None else now
    life = _life()
    out = []
    for key, p in FINDS.get(site, {}).items():
        if key in NORTH_ONLY:
            continue
        r = life._ROWS.get(key)
        if not r or not r.get("obs"):
            continue
        act = life.activity(r, "wood", now)
        if act < life.PRESENT_AT:
            continue
        out.append({"key": key, "row": r, "p": min(0.9, p * min(act, 1.0)), "act": act})
    return out


def pick(site: str, rng: random.Random, now: float | None = None) -> dict | None:
    """The one candidate a turn turns up (or None). Candidates are tried in a seeded order, each by its own chance."""
    cands = candidates(site, now)
    rng.shuffle(cands)
    for c in cands:
        if rng.random() < c["p"]:
            return c
    return None


def line_for(c: dict, site: str, night: bool = False) -> str:
    from core import life_shore as _ls
    r = c["row"]
    body = _ls.compose(r["obs"], "detail", night=night)
    band = ""
    try:
        band = _life()._count_band(r, c["act"])
    except Exception:
        pass
    more = {"a few": " There are a few more where it came from.", "several": " There are several more where it came from.",
            "a scatter": " There are more, scattered about it.", "a cloud of them": " There are more, all about."}.get(band, "")
    lead = {"stone": "You turn the stone, and something lies under it. ",
            "bark": "You peel the bark back, and something is under it. ",
            "stream": "You turn the stone in the stream, and something clings to it. "}[site]
    return lead + body + more


def dig(site: str, state: dict, now: float | None = None, rng: random.Random | None = None) -> str:
    """One deed at a site. `state` is a dict this call may update ('dig_bucket', 'dig_n'); the caller saves it. Returns the world's answer.
    No store write other than life's own deed note and sighting credit."""
    now = time.time() if now is None else now
    life = _life()
    if site not in SITES:
        site = "stone"
    if life._phase(now) == "night":
        return _NIGHT
    bucket = int(now // BUCKET_S)
    if state.get("dig_bucket") != bucket:
        state["dig_bucket"], state["dig_n"] = bucket, 0
    if int(state.get("dig_n", 0)) >= MAX_TURNS_PER_BUCKET:
        return _TIRED
    state["dig_n"] = int(state.get("dig_n", 0)) + 1
    rng = rng or random.Random(f"wood_dig:{site}:{bucket}:{state['dig_n']}")
    try:
        life.note_deed("peel_bark" if site == "bark" else "turn_stone", "wood", now)
    except Exception as exc:
        if exc.__class__.__name__ == "NonLiveWriteError":
            raise
    c = pick(site, rng, now)
    if c is None:
        return rng.choice(_NOTHING[site])
    text = line_for(c, site, False)
    try:
        life.credit_find(c["key"], "wood", now, text)
    except Exception as exc:
        if exc.__class__.__name__ == "NonLiveWriteError":
            raise
        logger.debug("[wood_dig] credit_find failed (non-fatal): %s", exc)
    return text
