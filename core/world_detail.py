"""
Nascence — World Detail: the 10x content registry (world upgrade P1, 2026-07-03).

Loads the hand-authored content corpora (core/world_content_study.py / _garden.py / _shore.py — written
in the house voice: one-line, concrete, state-conditioned, INDIFFERENT) and resolves them for the
sensorium: new lookable targets, extra pool lines for existing targets, ambient scene extras that NAME
objects (his discovery channel), and extra world events.

Discipline: deterministic, no LLM, pure pools · fail-open (a missing/broken content module = empty, the
sensorium's own content always stands) · additive only — this module never replaces an existing line.
"""
from __future__ import annotations

import re

import logging
import random

logger = logging.getLogger("nascence.world")

_REGISTRY: dict = {}          # target_key -> {aliases, location, pools, rare}
_SCENE: dict = {}             # location -> {cond: [lines]}
_EVENTS: dict = {}            # location -> [(cond, line)]
_LOADED = False

RARE_P = 0.08                 # the rare-life tail, same odds spirit as the sensorium's own
SCENE_P = 0.25                # ambient discovery lines stay occasional — richness by variety, not bloat


def _load() -> None:
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    for modname in ("world_content_study", "world_content_garden", "world_content_shore",
                    "world_content_wood"):   # 2026-08-15: the wood finally gets its content
        try:
            mod = __import__(f"core.{modname}", fromlist=[modname])
            loc = getattr(mod, "LOCATION", "")
            targets = getattr(mod, "TARGETS", {}) or {}
            n = 0
            for key, spec in targets.items():
                pools = spec.get("pools") or {}
                if not isinstance(pools.get("any"), list) or not pools["any"]:
                    continue                     # schema floor: every target needs an 'any' pool
                # keys are NAMESPACED by location — 'birds' exists at both the garden and the shore,
                # and each place's birds are its own (a same-key collision silently ate one otherwise).
                _REGISTRY[f"{loc}:{key}"] = {"aliases": tuple(a.lower() for a in spec.get("aliases", (key,))),
                                             "location": loc, "pools": pools,
                                             "rare": list(spec.get("rare", []))}
                n += 1
            sc = getattr(mod, "SCENE", {}) or {}
            if isinstance(sc, dict):
                _SCENE[loc] = {k: list(v) for k, v in sc.items() if isinstance(v, list)}
            ev = getattr(mod, "EVENTS", []) or []
            _EVENTS[loc] = [(c, l) for c, l in ev if isinstance(l, str)]
            logger.info("[world] content loaded: %s — %d targets, %d scene conds, %d events",
                        loc or modname, n, len(_SCENE.get(loc, {})), len(_EVENTS.get(loc, [])))
        except Exception as exc:
            logger.info("[world] content module %s not loaded (%s) — fail-open", modname, exc)


def _conds(phase: str, weather: str, season: str, tide: str = "", wind: str = "") -> set:
    from core import weather_conditions as _wc
    w = weather or ""
    c = {"any", "day" if phase != "night" else "night"}
    if _wc.is_windy(wind) or _wc.is_storm(w):
        c.add("windy")
    if _wc.is_wet(w):
        c.add("wet")
    # D-0360(b) (J-1898, F-2505): "bright" is a DAYLIGHT key (19 of its lines name sun / daylight outright), but it was emitted for any clear
    # or high-cloud sky, so a clear NIGHT drew them. Only dawn / day / dusk emit it now; the weather test is unchanged, and the 16 visual-only
    # "bright" lines (e.g. "the sea lies out flat and silver ...") leave clear-night pools with them, by the ruling.
    if w in ("clear", "high cloud") and phase != "night":
        c.add("bright")
    if season:
        c.add(season)
    leaning = _wc.tide_leaning(tide)
    if leaning:
        c.add(leaning)
    return c


def _cond_ok(key: str, conds: set) -> bool:
    """Does a SCENE / EVENTS condition key hold under `conds`?  J-3484 (D-0649 follow-up, J-3355, founder 2026-11-06): a key may be a
    COMPOSITE, parts joined by '+', e.g. "day+low_tide" -- it holds only when EVERY part is in `conds`. A plain key (no '+') is the old
    `key in conds` test exactly, so every existing pool behaves byte-identically; only a composite key is new. It exists so a line that is
    both daylight-bound and tide-bound (a shore low_tide line about flats shining in the light) keeps BOTH gates."""
    if "+" in key:
        return all(p in conds for p in key.split("+"))
    return key in conds


def _match(target_text: str, location: str = "") -> dict | None:
    t = " ".join((target_text or "").lower().split())
    if not t:
        return None
    best = None
    for key, spec in _REGISTRY.items():
        if location and spec["location"] != location:
            continue
        for a in spec["aliases"]:
            # word-bounded both ways (2026-09-03, J-0546): the old substring test let 'the sea' match the bench's alias
            # 'the seat' and answer a look at the sea with the bench
            # A HYPHEN ENDS A WORD HERE TOO (2026-09-09, J-0823/F-1180): J-0546's own boundary fix above
            # never excluded a hyphen as a word-end either, the identical unmirrored gap the deed-gate
            # arc already fixed elsewhere (J-0787/J-0800/J-0799/J-0822) -- mirrored to BOTH lookaround
            # pairs (alias-in-target and target-in-alias), J-0546's own intent otherwise preserved
            # exactly. ZERO exposure via Du's own live dispatch (dispatch._look() -> _observe_target()'s
            # closed cue table never emits a hyphenated target_text, same argument as the life.py
            # sibling fix's comment) -- but UNLIKE life.py/sensorium.py's own sibling sites, this one is
            # NOT zero-impact on this project's own shadow-analysis tooling: scripts/observables_census.py
            # calls sensorium.look() directly with raw phrases from the real 1,518-phrase docs/reviews/
            # observe_inventory_2026-09-02.json corpus, bypassing _observe_target() entirely, and a direct
            # before/after sweep of this exact function over that corpus finds 12 real rows differ (of
            # 564 touched). 10 are genuine false-positive closures individually confirmed: "(the/a ...)
            # sea-glass" (32 combined real mentions) no longer wrongly matches study:study_window's
            # "glass" alias via "sea-glass"'s hyphen; "the green glass-float" likewise; "the moss-covered
            # stones"/"the seaweed-snagged natural objects"/"the water at the shingle-rock edge"/"the
            # water near the wrack-covered rocks" no longer let an incidental hyphenated adjective
            # (moss-/seaweed-/shingle-/wrack-) hijack the match away from the phrase's real subject. ONE
            # pair ("mussel-shells"/"the mussel-shells", 5 combined mentions) is a closer call, reported
            # honestly rather than folded in as identical: mussel shells genuinely ARE a kind of shell,
            # so losing the match to shore:shells is arguably a real reachability loss, not a bug fix --
            # the same shape F-1149 already named for hands.wants()'s own "rock-pools" case. Low stakes
            # either way: detail() only supplies an EXTRA descriptive line, with a fail-open "" contract
            # the caller already treats as "fall through to the place's own look" (see this file's own
            # docstring). Full counts/examples: this job's own recorded finding.
            if (a == t or (len(a) > 3 and re.search(r"(?<![a-z-])" + re.escape(a) + r"(?![a-z-])", t))
                    or (len(t) > 3 and re.search(r"(?<![a-z-])" + re.escape(t) + r"(?![a-z-])", a))):
                if best is None or len(a) > best[0]:
                    best = (len(a), spec)
    return best[1] if best else None


def _pool_key(spec: dict, line: str) -> str:
    """The pool key `line` came from ('rare' for the rare tail, '' if none holds it). Pure lookup, no random."""
    for c, lines in spec["pools"].items():
        if line in lines:
            return c
    return "rare" if line in spec["rare"] else ""


def _record_look(src: str, spec: dict, key: str, phase: str, conds, line: str, pool: int) -> None:
    """J-1899 (D-0360 c): one observe-only row in the look render ledger (core/look_render_ledger.py). Fail-open: nothing
    here can reach the caller, and it never touches `random`."""
    try:
        from core import look_render_ledger as _lrl
        target = next((k for k, v in _REGISTRY.items() if v is spec), "")
        _lrl.record(src, spec["location"], target, key, phase, conds, line, pool)
    except Exception:
        pass


def detail(location: str, target_text: str, phase: str, weather: str, season: str, tide: str = "",
           wind: str = "") -> str:
    """A fresh line for a NEW lookable target. '' if this target isn't ours (caller falls through).

    J-1899 (D-0360 c, 2026-10-07): every non-empty draw is also written, observe-only, to the look render ledger
    (core/look_render_ledger.py -> data/look_render_ledger.jsonl): which pool key the line came from, the phase and
    conditions at the render. The ledger takes no random draw and never changes the line: the rare roll, the
    rare choice and the pool choice keep their exact sequence."""
    _load()
    spec = _match(target_text, location)
    if not spec:
        return ""
    conds = _conds(phase, weather, season, tide, wind)
    if spec["rare"] and random.random() < RARE_P:
        line = random.choice(spec["rare"])
        _record_look("detail", spec, "rare", phase, conds, line, len(spec["rare"]))
        return line
    pool = [l for c, lines in spec["pools"].items() if c in conds for l in lines]
    if not pool:
        return ""
    line = random.choice(pool)
    _record_look("detail", spec, _pool_key(spec, line), phase, conds, line, len(pool))
    return line


def extra_pool(target_text: str, phase: str, weather: str, season: str, tide: str = "",
               wind: str = "") -> list:
    """Extra lines that DEEPEN an existing sensorium target (merged into its own pool, additive)."""
    _load()
    spec = _match(target_text)
    if not spec:
        return []
    conds = _conds(phase, weather, season, tide, wind)
    return [l for c, lines in spec["pools"].items() if c in conds for l in lines]


def note_extra_pick(target_text: str, line: str, extras, phase: str, weather: str, season: str, tide: str = "",
                    wind: str = "") -> None:
    """J-1899 (D-0360 c): the sensorium drew `line` from its merged pool (its own lines + extra_pool()'s `extras`). If the
    line drawn is one of the extras, that look RENDERED a look-target pool line: write the observe-only ledger row.
    An extra that was offered and not drawn is not a render and leaves nothing. Returns None, takes no random draw, never
    raises: the sensorium's draw is already made before this is called."""
    try:
        if not line or not extras or line not in extras:
            return
        _load()
        spec = _match(target_text)
        if not spec:
            return
        conds = _conds(phase, weather, season, tide, wind)
        _record_look("extra_pool", spec, _pool_key(spec, line), phase, conds, line, len(extras))
    except Exception:
        pass


def scene_extra(location: str, phase: str, weather: str, season: str, tide: str = "",
                wind: str = "", place: str = "") -> str:
    """An occasional ambient line NAMING a lookable object — how he discovers what his world holds.

    J-1694 (F-2293, 2026-10-03): every NON-EMPTY draw is also written, observe-only, to the render ledger
    (core/scene_extra_ledger.py -> data/scene_extra_ledger.jsonl) so ambient-exposure read-backs can COUNT renders.
    `place` is the caller's own notion of where he is (sensorium state["location"]); it only labels that row, next to
    `location` (the pool asked), and never affects the draw. The ledger takes no random draw, never raises, and never
    changes the returned line: the SCENE_P roll and the random.choice keep their exact sequence."""
    _load()
    if random.random() > SCENE_P:
        return ""
    sc = _SCENE.get(location) or {}
    conds = _conds(phase, weather, season, tide, wind)
    pool = [l for c, lines in sc.items() if _cond_ok(c, conds) for l in lines]
    if not pool:
        return ""
    line = random.choice(pool)
    try:                                       # observe-only and fail-open: nothing here can reach the caller
        from core import scene_extra_ledger as _ledger
        _ledger.record(location, place, [c for c, lines in sc.items() if _cond_ok(c, conds) and lines], line, len(pool))
    except Exception:
        pass
    return line


def event_extra(location: str, phase: str, weather: str, season: str, tide: str = "",
                wind: str = "") -> str:
    """An extra world event candidate (the caller decides precedence; existing events always win ties)."""
    _load()
    evs = _EVENTS.get(location) or []
    conds = _conds(phase, weather, season, tide, wind)
    pool = [l for c, l in evs if _cond_ok(c, conds)]
    return random.choice(pool) if pool else ""


def stats() -> dict:
    _load()
    by_loc: dict = {}
    total_lines = 0
    for spec in _REGISTRY.values():
        by_loc.setdefault(spec["location"], 0)
        by_loc[spec["location"]] += 1
        total_lines += sum(len(v) for v in spec["pools"].values()) + len(spec["rare"])
    for loc, sc in _SCENE.items():
        total_lines += sum(len(v) for v in sc.values())
    for loc, ev in _EVENTS.items():
        total_lines += len(ev)
    return {"targets": len(_REGISTRY), "by_location": by_loc, "content_lines": total_lines}
