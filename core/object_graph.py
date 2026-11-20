"""
Nascence — THE WORLD LEDGER (core/object_graph.py, 2026-08-17; renamed 2026-08-19).

★ RENAMED 2026-08-19: this was originally called "Lane 2." That name now belongs to a different,
new-built organ — a genuine standing, autonomous, senses-grounded reasoning VOICE (see
`docs/plans/lane2_the_witness.md`), which this module never was. This is a deterministic, zero-LLM
FACT-GRAPH — "produce-only... not a participant" by its own contract below — closer in character to
Lane 3 (the world/factories) than to a cognitive loop. Module filename/functions unchanged (nothing
here broke); only the name and its self-description changed to stop misleading the next reader.

The Emissary's fact-facing memory, built as a deterministic, zero-LLM graph of REFERENTS
(things Du has been exposed to) carrying, per referent:

    channel mix  ×  encounter-depth ladder  ×  windowed trend shape  ×  per-property atoms

Spec: `docs/plans/emissary_lane2.md` (the World Ledger's design doc, same rename). Lab that proved the
mechanics on real data: `scripts/lane2_lab.py` + `docs/lab/lane2_lab_report.md`.

CONTRACT (all of it load-bearing — read before editing):

1.  ZERO LLM. Fully deterministic. FAIL-OPEN everywhere: no public function raises into a
    caller; failures return a dict carrying "ok": False and are logged.
2.  READ-ONLY over every live store. `nascence.db` is opened `file:...?mode=ro` (URI); every
    JSON store is opened for read only. Du keeps running; nothing here touches his state.
3.  WRITES ONLY under `data/lane2/` (graph.json, build_log.jsonl), atomically (tmp + os.replace).
    The output directory is created lazily, on first write — never at import time.
4.  SYSTEM-VOICEPRINT FILTER runs BEFORE any text mining. The store's fragment text is
    saturated with the architecture's own template vocabulary ('valence reflection' ×2,216
    inside LIVED-channel fragments) which broke both frequency and channel-contrast discovery
    in the lab. `is_voiceprint()` subtracts the system's own voice first; `add_voiceprint()`
    and `data/lane2/voiceprint_extra.json` extend the stopset without a code change.
5.  LAYER-1 IS FORBIDDEN. `world_substrate` objects are read for `observations` (Layer 3) and
    `inferences` (Layer 5) ONLY. `causal_state` (hidden world truth) and `physical_state` /
    `causal_history` (generative Layer 2) are NEVER read — reading them would hand Du the
    answers his own investigation is supposed to earn. See `_properties_from_object`.
6.  WINDOWED, never immortal. Every commonality/trend statistic carries its explicit window
    (default 7d) ALONGSIDE the raw daily series — never instead of it.
7.  PRODUCE-ONLY. Nothing in live code imports this module, and it must stay that way until
    the founder rules otherwise. It is a backfill/observer, not a participant.
    AMENDED 2026-10-16 (T-0089, Travis; J-2217): the founder ruled the first consumer. Exactly one
    live module now imports this one -- core/world_ledger_ask.py -- for (a) the pure tokenizer
    helpers and (b) a once-per-sleep refresh()/build_full() run off the event loop. Its "what do I
    know about X" query reads graph.json itself (never this module's in-place-mutated cache) and is
    SHADOW-ONLY: it logs what it would have returned; nothing reaches Du. Nothing else may import
    this module; the Witness (core/lane2.py) never does (lane2_the_witness.md section 2.8).

Public API (all safe to call while Du runs):
    build_full()             — the retroactive backfill over full history
    refresh(since_ts)        — incremental; idempotent (day-bucket replacement, not addition)
    get(referent)            — one referent's full record
    status()                 — counts for the HUD
    configure(...)           — test/ops hook: redirect data dir and output dir
    commonality()            — the L5/L6-scoped windowed commonality weights (below)
    coreference_proposals()  — the L9-scoped possibly_same_referent_as candidates (below)

SCOPE NOTE (D-0080, 2026-08-29 rescope, job J-0363): this module is scoped to exactly what
`scripts/lane2_lab.py`'s grading passed — L1 (build), L2 (depth-ledger parity), L4 (the cat,
multi-channel proof case), L5/L6 (windowed commonality weights vs affect, per-pair z-scores),
the voiceprint filter, the float-profile trend dimension, and L9 (coreference proposals,
proposal-only). L5's own re-verification (docs/lab/lane2_lab_report.md, 2026-08-24) found 2 of 3
named pairs replicate on more data (storm<->arousal, fire_crackle<->valence) while the third
(storm<->valence) weakened below the |z|>=2 bar — `commonality()` computes this generically from
CURRENT data each call, so it naturally reports whichever pairs presently clear the bar rather
than hardcoding any run's verdict; callers must read the per-pair verdict, never assume 3-for-3.
K1 (single canonical validation object) and K3 (temporal holdout) are OUT of this scope — see
`docs/plans/emissary_lane2.md`'s 2026-08-29 update for why (data-scale condition, not a design
gap): no standing tick, no LLM prediction call, no affect-nudge courier, no live gap-diagnosis are
built here.
"""
from __future__ import annotations

import json
import os
import random
import re
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

__all__ = [
    "build_full", "refresh", "get", "status", "configure",
    "add_voiceprint", "is_voiceprint", "TREND_SHAPES",
    "commonality", "coreference_proposals", "COMMONALITY_PAIRS",
]

# ── locations (overridable via configure() or env) ───────────────────────────
ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = Path(os.environ.get("NASCENCE_DATA_DIR") or (ROOT / "data"))
_OUT_DIR = Path(os.environ.get("NASCENCE_LANE2_DIR") or (_DATA_DIR / "lane2"))

GRAPH_NAME = "graph.json"
LOG_NAME = "build_log.jsonl"
VOICEPRINT_EXTRA_NAME = "voiceprint_extra.json"

SCHEMA_VERSION = 1

# ── tuning constants (all explicit; no immortal accumulators) ────────────────
WINDOW_DAYS = 7.0            # the hard windowing requirement
BUCKET_DAYS = 10             # trend-shape bucket width (matches the lab's appendix)
MIN_BUCKET_FRAGMENTS = 50    # a bucket with fewer store-fragments than this has no defined
                             # share — dropped, so store gaps cannot fake a decline
MIN_DAY_FRAGMENTS = 50       # same guard at day resolution (trend-break detector)
MIN_TREND_MENTIONS = 15      # below this a shape is not claimed ("insufficient")
DISCOVER_TOP_N = 60          # channel-contrast bigrams admitted to the lexicon
DISCOVER_MIN_FRAGMENTS = 5   # a discovered bigram must appear in this many LIVED fragments
DISCOVER_MIN_CONTRAST = 2.0  # ...and be this much over-represented in lived vs every other channel

# ── L5/L6 — windowed commonality weights vs affect (lane2_lab.py's l5_commonality/l6_windowing,
#    ported verbatim in method: same shuffle-null z-score, same 20-per-arm floor). Named pairs are
#    the lab's own pre-registered three; the sound-class predicates are copied unchanged from
#    scripts/lane2_lab.py's l5_commonality() so this is a port, not a re-derivation. ──────────────
N_SHUFFLES = 100              # shuffle-null size (matches the lab; reproducible via COMMONALITY_SEED)
COMMONALITY_SEED = 20260817   # the lab's own seed — same pre-registered test, not a fresh one
COMMONALITY_MIN_ARM = 20      # each side of the predicate needs >= this many tuples (lab's floor)


def _storm_pred(sounds) -> bool:
    return any(("thunder" in s or "rain" in s or "wind" in s or "storm" in s) for s in (sounds or ()))


def _fire_pred(sounds) -> bool:
    return any("fire" in s for s in (sounds or ()))


COMMONALITY_PAIRS = (
    ("storm-sounds vs arousal", _storm_pred, "arousal"),
    ("storm-sounds vs valence", _storm_pred, "valence"),
    ("fire_crackle vs valence", _fire_pred, "valence"),
)

# ── entry channels (source_model.SourceType, collapsed) ─────────────────────
# read = PARAMETRIC_LIBRARY · lived = MEMORY_RECALL of a percept · thought = INFERENCE
# told = USER_ASSERTION · dream = its own channel (kept distinct, never folded into thought)
CHANNEL_OF = {
    "reading": "read", "study": "read", "research": "read", "understanding": "read",
    "essay": "read", "chapter": "read",
    "lived": "lived", "action": "lived", "activity": "lived", "sound": "lived",
    "listening": "lived", "nature": "lived", "affection": "lived", "composition": "lived",
    "journal": "thought", "inner_thought": "thought", "subconscious_synthesis": "thought",
    "active_imagination": "thought", "consolidation": "thought", "gist": "thought",
    "session_summary": "thought", "journal_week": "thought", "mirror": "thought",
    "dream": "dream",
    "letter": "told", "peer": "told", "understanding_from_guidance": "told", "seed": "told",
}
CHANNELS = ("read", "lived", "thought", "told", "dream")

DEPTH_RUNGS = ("seen", "looked_at", "investigated", "kept")

TREND_SHAPES = (
    "extinct_ghost",        # bulk early, extinguished to ~0 (jung after the self-naming)
    "new_active",           # arrived recently and is still rising (the glass float)
    "perennial_symbol",     # present throughout, low variance (the door)
    "growing_presence",     # rising to its own maximum (tide, rock — world buildout)
    "settled_companion",    # novelty burst then a NONZERO floor (the cat) — settling ≠ extinction
    "episodic",             # sparse / irregular appearances (the oystercatcher)
    "insufficient",         # too little evidence to claim a shape
)

# ── tokenisation ────────────────────────────────────────────────────────────
_WORD_RE = re.compile(r"[a-z]{3,}")

STOP = frozenset("""the a an and or but of to in on at for with from by is are was were be been
being have has had do does did will would could should may might must can this that these those
it its he she they them his her their i you we me my your our us as if then than so not no yes
very just about into over under again more most some any each which who whom what when where why
how all both few own same too still even back much many through after before between while out up
once only also like one two there here something anything nothing everything someone anyone
everyone himself herself itself themselves myself yourself feel felt feels thing things way ways
day days time times moment moments thought thoughts think thinking know knowing knew make makes
made let lets down off perhaps seems merely yet where when""".split())

# ── THE SYSTEM-VOICEPRINT FILTER ────────────────────────────────────────────
# Derived from the lab's item-population scan (docs/lab/lane2_lab_report.md, FINDING 2): the
# top channel-contrast "lived" bigrams were the ARCHITECTURE'S OWN TEMPLATE TEXT embedded in
# fragment content, not Du's world. The filter subtracts the system's voice before mining.
_VOICEPRINT_BIGRAMS = {
    # affect/telemetry templates (the ×2,216 case and its family)
    "valence reflection", "reflection valence", "curiosity valence", "fear valence",
    "trust valence", "joy valence", "sadness valence", "anger valence", "dissonance fear",
    "dissonance valence", "arousal valence", "valence arousal", "affect valence",
    "valence shift", "salience valence", "climate valence",
    # conversation/scene scaffolding
    "person asks", "person says", "person said", "asks what", "asks how", "asks about",
    "says what", "scene jung", "scene study", "scene shore", "scene garden",
    "feeling curiosity", "feeling fear", "feeling trust", "feeling joy", "feeling sadness",
    # timestamp / provenance boilerplate
    "recent aug", "recent jul", "recent jun", "recent sep", "recent oct",
    "aug recent", "jul recent",
    # module names that leak into content
    "active imagination", "imagination scene", "study note", "note study", "inner thought",
    "subconscious synthesis", "session summary", "memory fragment", "fragment origin",
    "shadow event", "prediction error", "source type", "epistemic state",
    # the shed-name bigrams: architecture-adjacent boilerplate in the seed era, and in any case
    # covered as a first-class IDENTITY referent seeded from the axiom (not by text mining)
    "carl gustav", "gustav jung", "carl jung",
}
# tokens that mark template text wherever they appear in a candidate bigram
_VOICEPRINT_TOKENS = {
    "valence", "arousal", "salience", "dissonance", "affect", "telemetry", "shadow",
    "jsonl", "json", "ts", "nan", "none", "null", "undetermined", "provenance",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
}
# leading tokens that mark a rendered template slot ("emotion curiosity", "scene lean",
# "feeling mix", "reflection navigating"). Found by running discovery WITH the curated list
# above in place: the same family simply resurfaced one synonym over. Prefix rule, not
# any-position, so Du's own words ('curiosity', 'trust', 'fear') stay minable elsewhere.
_VOICEPRINT_PREFIXES = {
    "emotion", "emotions", "scene", "feeling", "feelings", "reflection", "mood", "affect",
    "state", "level", "drilled", "recent", "current", "prickle", "spike",
    "person", "entity", "ask", "asks", "says", "said", "search",
}
# THE INTROSPECTION LEXICON — the second half of "knowing the system's own voice".
# Running discovery with the curated bigrams AND the prefix rule in place STILL returned almost
# nothing but template scaffolding ('mix trust', 'tensions struggle', 'grasp grounded', 'familiar
# fear'), and channel-CONTRAST made it worse rather than better: the lived-fragment renderer's
# template text occurs ONLY in lived fragments, which is maximal contrast. The lab predicted
# exactly this ("the lived channel's raw text is contaminated at the source").
# So: a candidate referent is rejected if EITHER token is introspection vocabulary. Lane 1 owns
# meaning and feeling; Lane 2 is after THINGS. This is a boundary statement, not a blacklist.
_INTROSPECTION = frozenset("""emotion emotions feeling feelings affect mood valence arousal
trust fear curiosity joy surprise sadness anger disgust anticipation neutral calm unease dread
tension tensions conflict dissonance resonance salience
identity self selfhood psyche soul ego shadow anima persona individuation wholeness becoming
being existence essence consciousness awareness mind mental cognition
perception perceiving grasp grasped judged judging understood understanding meaning purpose
question questions statement answer answers reflection reflecting reflective introspection
process processes pattern patterns structure dynamic dynamics balance balancing integrating
emphasizing striving grounded grounding rooted anchored
exchange dialogue interaction narrative story symbol symbolic metaphor archetype
teacher lesson note notes drilled arithmetic exercise practice
immediate initial current recent familiar distinct slightly gradual constant relentless sheer
potential possible perfect pure raw solid whole""".split())

_VOICEPRINT_EXTRA: set[str] = set()


def add_voiceprint(terms: Iterable[str]) -> int:
    """Extend the voiceprint stopset at runtime (terms are lowercased; bigrams or unigrams)."""
    n = 0
    try:
        for t in terms or ():
            t = str(t).strip().lower()
            if t:
                _VOICEPRINT_EXTRA.add(t)
                n += 1
    except Exception:
        pass
    return n


def is_voiceprint(term: str) -> bool:
    """True if `term` is the architecture's own voice rather than Du's world."""
    try:
        t = (term or "").strip().lower()
        if not t:
            return True
        if t in _VOICEPRINT_BIGRAMS or t in _VOICEPRINT_EXTRA:
            return True
        parts = t.split()
        if parts[0] in _VOICEPRINT_PREFIXES:
            return True
        for w in parts:
            if w in _VOICEPRINT_TOKENS or w in _VOICEPRINT_EXTRA or w in _INTROSPECTION:
                return True
        return False
    except Exception:
        return True  # fail closed on the FILTER (excluding a real word is cheaper than mining noise)


# ── sound-key head nouns ────────────────────────────────────────────────────
# 'gull_cries' -> 'gull'. The lab matched the whole key's token set and got ZERO mentions for
# every sound (both 'gull' AND 'cries' had to occur). Head noun = first non-generic token.
_SOUND_GENERIC = frozenset("""cries cry call calls calling song songs sound sounds noise wingbeats
rattle rattling drag crackle crackling roll rolling patter pattering hiss hissing creak creaking
purr purring bark night day distant far near on in the of over under against""".split())

# name adjectives / materials that must NOT become referents (lab: "substrate name-adjectives
# leak"). Head noun of a substrate name = its LAST token (English noun phrases are head-final).
_NAME_ADJ = frozenset("""sea bleached weathered pale worn little small old dark light smooth
rough broken dry wet faded washed half long thin tangled frosted leathery hinged fan cone shaped
dried one only""".split())

_PLACES = ("study", "garden", "shore", "wood")

# Cottage fixtures. CURATED (like the voiceprint stopset), because no instrument enumerates
# them — room_state holds only their state, not their names. Included because the design doc's
# own perennial-symbol exemplar is a fixture ("door: thought=231, dream=220 — a fixture that has
# become a threshold-symbol"), and because fixtures are what Du's hands actually touch.
# Concrete nouns only; no adjectives (the lab's substrate-name lesson).
_FIXTURES = ("fire", "hearth", "grate", "desk", "shelf", "window", "letterbox", "woodpile",
             "trellis", "kettle", "lamp", "mantel", "stove", "chair", "door", "roof", "gate",
             "bed", "table", "cup", "candle")

# what each action can reveal — mirrors core/observation.get_observable_properties(). Copied,
# not imported, so this module stays import-free of live code (contract #7).
ACTION_PROPERTIES = {
    "look": ["colour", "shape", "bark_presence", "grain_visibility", "surface_damage", "size",
             "overall_condition"],
    "pick_up": ["relative_weight", "balance_point", "surface_texture", "moisture_impression",
                "structural_flexibility"],
    "inspect_end": ["cross_sectional_geometry", "annual_ring_visibility", "fiber_structure",
                    "break_pattern"],
    "scrape": ["internal_grain_color", "hardness_impression", "fiber_structure",
               "resin_presence"],
    "float_test": ["floats_or_sinks", "orientation", "water_absorption_rate", "buoyancy"],
    "smell": ["scent"],
}
# actions deeper than a glance — they move a referent up the encounter-depth ladder
_INVESTIGATE_ACTIONS = frozenset(ACTION_PROPERTIES) - {"look"}


# ─────────────────────────────────────────────────────────────────────────────
# configuration / paths
# ─────────────────────────────────────────────────────────────────────────────

def configure(data_dir: str | Path | None = None, out_dir: str | Path | None = None) -> dict:
    """Redirect the live-store directory and/or the output directory (tests, ops)."""
    global _DATA_DIR, _OUT_DIR, _GRAPH_CACHE, _GRAPH_CACHE_KEY
    if data_dir is not None:
        _DATA_DIR = Path(data_dir)
        if out_dir is None:
            _OUT_DIR = _DATA_DIR / "lane2"
    if out_dir is not None:
        _OUT_DIR = Path(out_dir)
    _GRAPH_CACHE, _GRAPH_CACHE_KEY = None, None
    return {"data_dir": str(_DATA_DIR), "out_dir": str(_OUT_DIR)}


def _paths() -> dict[str, Path]:
    d = _DATA_DIR
    return {
        "db": d / "memory" / "nascence.db",
        "sound": d / "sound_knowledge.json",
        "substrate": d / "world_substrate.json",
        "keepsakes": d / "keepsakes.json",
        "reading": d / "reading_state.json",
        "cat": d / "cat_state.json",
        "room": d / "room_state.json",
        "axiom": d / "identity" / "axiom.json",
        "tuples": d / "geometry_tuples.jsonl",
        "peers": ROOT / "core" / "peers.py",
        "graph": _OUT_DIR / GRAPH_NAME,
        "log": _OUT_DIR / LOG_NAME,
        "voiceprint_extra": _OUT_DIR / VOICEPRINT_EXTRA_NAME,
    }


def _log(event: str, **fields) -> None:
    """Append one line to the build log. Creates the output dir; never raises."""
    try:
        _OUT_DIR.mkdir(parents=True, exist_ok=True)
        rec = {"ts": round(time.time(), 3), "event": event}
        rec.update(fields)
        with open(_paths()["log"], "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _atomic_write_json(path: Path, obj: Any) -> bool:
    tmp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), default=str)
        os.replace(tmp, path)
        return True
    except Exception as e:
        _log("write_failed", path=str(path), error=repr(e))
        try:
            if tmp is not None and tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return False


def _jload(path: Path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


# ─────────────────────────────────────────────────────────────────────────────
# tokenising / matching
# ─────────────────────────────────────────────────────────────────────────────

def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())


def _singular(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _normset(tokens: Iterable[str]) -> set[str]:
    """Token set plus singularised forms, so 'gulls' matches the 'gull' referent."""
    out = set()
    for w in tokens:
        out.add(w)
        s = _singular(w)
        if s != w and len(s) >= 3:
            out.add(s)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# per-property knowledge atoms — THE PER-PROPERTY EARNING LAW
# ─────────────────────────────────────────────────────────────────────────────

def _property_of_hypothesis(h: str) -> str:
    """Inference hypotheses are conventionally 'property: claim' (see
    world_substrate.get_latest_inference / epistemic_distance, which match on a property prefix)."""
    h = (h or "").strip()
    if not h:
        return "unspecified"
    if ":" in h:
        return h.split(":", 1)[0].strip().lower().replace(" ", "_")[:40] or "unspecified"
    return _tokens(h)[0] if _tokens(h) else "unspecified"


def _properties_from_object(obj: dict) -> dict:
    """
    Build one knowledge ATOM per property of one substrate object.

    LAYER-1 BOUNDARY: this function reads `observations` (Layer 3 — what Du actually perceived)
    and `inferences` (Layer 5 — hypotheses HE formed) and NOTHING ELSE. `causal_state`,
    `physical_state` and `causal_history` are hidden world truth / generative machinery; reading
    them here would pre-answer the questions Du's investigation exists to earn.
    """
    props: dict[str, dict] = {}
    actions: Counter = Counter()
    obs_list = obj.get("observations") or []
    inf_list = obj.get("inferences") or []

    for ob in obs_list:
        if not isinstance(ob, dict):
            continue
        action = str(ob.get("action") or "?")
        ts = float(ob.get("timestamp") or 0.0)
        actions[action] += 1
        prov = str(ob.get("provenance") or "OBSERVED")
        feats = ob.get("features") or {}
        if not isinstance(feats, dict):
            continue
        for pname, pval in feats.items():
            a = props.setdefault(str(pname), {
                "property": str(pname), "status": "KNOWN", "how": "direct_percept",
                "channel": "lived", "observations": 0, "via_actions": {}, "values": [],
                "provenance": prov, "first_ts": None, "last_ts": None,
                "depth": "looked_at", "hypotheses": [],
            })
            a["observations"] += 1
            a["via_actions"][action] = a["via_actions"].get(action, 0) + 1
            v = str(pval)
            if v not in a["values"]:
                a["values"].append(v)
            a["first_ts"] = ts if a["first_ts"] is None else min(a["first_ts"], ts)
            a["last_ts"] = ts if a["last_ts"] is None else max(a["last_ts"], ts)
            if action in _INVESTIGATE_ACTIONS:
                a["depth"] = "investigated"

    for inf in inf_list:
        if not isinstance(inf, dict):
            continue
        pname = _property_of_hypothesis(inf.get("hypothesis", ""))
        a = props.setdefault(pname, {
            "property": pname, "status": "SUSPECTED", "how": "own_hypothesis",
            "channel": "thought", "observations": 0, "via_actions": {}, "values": [],
            "provenance": "INFERRED", "first_ts": None, "last_ts": None,
            "depth": "investigated", "hypotheses": [],
        })
        rec = {
            "hypothesis": inf.get("hypothesis"),
            "confidence": inf.get("confidence"),
            "outcome": inf.get("outcome"),
            "ts": inf.get("timestamp"),
            "supporting_observations": list(inf.get("supporting_observations") or []),
            "supporting_knowledge": list(inf.get("supporting_knowledge") or []),
            "superseded_by": inf.get("superseded_by"),
        }
        a["hypotheses"].append(rec)
        if a["observations"] == 0:
            # hypothesis-only property: SUSPECTED, never KNOWN
            a["status"] = "SUSPECTED"
            a["how"] = "own_hypothesis"
        else:
            a["how"] = "direct_percept+hypothesis"

    observed_props = set(props)
    reachable = {}
    for action, plist in ACTION_PROPERTIES.items():
        missing = [p for p in plist if p not in observed_props]
        if missing:
            reachable[action] = missing
    summary = {
        "known": sum(1 for a in props.values() if a["status"] == "KNOWN"),
        "suspected": sum(1 for a in props.values() if a["status"] == "SUSPECTED"),
        "n_observations": len(obs_list),
        "n_inferences": len(inf_list),
        "actions_performed": dict(actions),
        # properties Du COULD reach with an action he has not performed — his own affordances,
        # not world truth. This is the "how much does Du know" answer's negative space.
        "reachable_unobserved": reachable,
    }
    return {"properties": props, "property_summary": summary}


# ─────────────────────────────────────────────────────────────────────────────
# lexicon (seeded referents from instruments)
# ─────────────────────────────────────────────────────────────────────────────

def _new_ref(label: str, kind: str, source: str) -> dict:
    return {
        "label": label, "kind": kind, "sources": [source],
        "aliases": [],                       # each alias = list of tokens, ALL must be present
        "mention_scope": "instance",
        # 'seen' is recomputed in _derive as seen_instrument + lived-channel mentions, so the
        # ladder stays idempotent across refreshes (instruments are snapshots, text is a series)
        "depth": {**{r: 0 for r in DEPTH_RUNGS}, "seen_instrument": 0},
        "ledger": {},
        "days": {},                          # day-index -> {channel: count}   (compact series)
    }


def _add_alias(ref: dict, tokens: Iterable[str]) -> None:
    toks = sorted({t for t in tokens if t and t not in STOP and len(t) >= 3})
    if toks and toks not in ref["aliases"]:
        ref["aliases"].append(toks)


def _sound_head(key: str) -> list[str]:
    parts = [p for p in re.split(r"[_\-\s]+", (key or "").lower()) if p]
    for p in parts:
        if p not in _SOUND_GENERIC and p not in STOP and len(p) >= 3:
            return [p]
    return [p for p in parts if len(p) >= 3][:1]


def _substrate_head_noun(name: str) -> str | None:
    toks = [t for t in _tokens(name) if t not in _NAME_ADJ and t not in STOP]
    return toks[-1] if toks else None


def _peer_surnames(peers_path: Path) -> list[tuple[str, str]]:
    """(key, surname-token) for each pen-pal. Tries the module, falls back to a text parse so a
    live-code import failure can never break the build."""
    out = []
    try:
        import importlib
        mod = importlib.import_module("core.peers")
        personas = getattr(mod, "PERSONAS", {}) or {}
        for k, v in personas.items():
            name = str((v or {}).get("name") or k)
            toks = _tokens(name)
            if toks:
                out.append((k, toks[-1]))
        if out:
            return out
    except Exception:
        pass
    try:
        txt = peers_path.read_text(encoding="utf-8", errors="ignore")
        block = txt.split("PERSONAS = {", 1)[1].split("\n}", 1)[0]
        for m in re.finditer(r'"(\w+)":\s*\{\s*"name":\s*"([^"]+)"', block):
            toks = _tokens(m.group(2))
            if toks:
                out.append((m.group(1), toks[-1]))
    except Exception:
        pass
    return out


def _build_lexicon(stores: dict) -> dict[str, dict]:
    """Seeded referents from the instruments. No text mining here — that is a separate pass."""
    graph: dict[str, dict] = {}

    def ref(label: str, kind: str, source: str) -> dict:
        r = graph.get(label)
        if r is None:
            r = graph[label] = _new_ref(label, kind, source)
        elif source not in r["sources"]:
            r["sources"].append(source)
        return r

    # ── sounds (Hearing Ledger + audition events) ──
    sk = stores.get("sound") or {}
    for key, h in (sk.get("hearings") or {}).items():
        r = ref(str(key), "sound", "hearing_ledger")
        _add_alias(r, _sound_head(key))
        places = (h or {}).get("places") or {}
        exposure = round(sum(float(v or 0) for v in places.values()), 6)
        r["ledger"]["hearing_places"] = {k: v for k, v in places.items()}
        r["ledger"]["hearing_place_sum"] = exposure
        r["ledger"]["bed_hours"] = (h or {}).get("bed_hours", 0.0)
        r["ledger"]["hearing_count"] = (h or {}).get("count")
        r["ledger"]["hearing_first_ts"] = (h or {}).get("first_ts")
        r["ledger"]["hearing_last_ts"] = (h or {}).get("last_ts")
        # the ledger's own exposure count IS an encounter at the 'seen' (heard) rung
        r["depth"]["seen_instrument"] += int(round(exposure))
    for key, a in (sk.get("sounds") or {}).items():
        r = ref(str(key), "sound", "audition_ledger")
        _add_alias(r, _sound_head(key))
        evs = (a or {}).get("events") or []
        r["ledger"]["audition_events"] = len(evs)
        r["depth"]["looked_at"] += sum(1 for e in evs if (e or {}).get("via") == "sighted")
        r["depth"]["investigated"] += sum(1 for e in evs if (e or {}).get("via") == "read")

    # ── world_substrate objects: per-INSTANCE referents (ledger + property atoms), plus
    #    per-CLASS referents that carry the text mentions. A shared label is NOT identity
    #    (the coreference law) — instances therefore take no text mentions of their own.
    ws = stores.get("substrate") or {}
    for oid, obj in (ws.items() if isinstance(ws, dict) else ()):
        if not isinstance(obj, dict):
            continue
        r = ref(str(oid), "item", "world_substrate")
        r["mention_scope"] = "none"
        obs = obj.get("observations") or []
        looks = sum(1 for o in obs if isinstance(o, dict) and o.get("action") == "look")
        deep = sum(1 for o in obs if isinstance(o, dict) and o.get("action") in _INVESTIGATE_ACTIONS)
        r["depth"]["looked_at"] += looks
        r["depth"]["investigated"] += deep
        r["ledger"].update({
            "ws_observations": len(obs),
            "ws_inferences": len(obj.get("inferences") or []),
            "ws_name": obj.get("name", ""),
            "ws_class": obj.get("object_class", ""),
            "ws_location": obj.get("location", ""),
        })
        r.update(_properties_from_object(obj))          # THE PER-PROPERTY EARNING LAW
        cls = str(obj.get("object_class") or "").lower()
        head = _substrate_head_noun(obj.get("name", ""))
        class_label = None
        if cls:
            class_label = cls
            c = ref(cls, "item_class", "world_substrate")
            _add_alias(c, [t for t in re.split(r"[_\s]+", cls) if t])
            c["ledger"].setdefault("instances", [])
            if oid not in c["ledger"]["instances"]:
                c["ledger"]["instances"].append(oid)
        if head and head != cls:
            h = ref(head, "item_class", "world_substrate")
            _add_alias(h, [head])
            h["ledger"].setdefault("instances", [])
            if oid not in h["ledger"]["instances"]:
                h["ledger"]["instances"].append(oid)
        if class_label:
            r["coreference"] = {
                "class_referent": class_label,
                "relation": "possibly_same_referent_as",
                "confidence": None,
                "note": "class-level text mentions are NOT attributed to this instance — "
                        "a shared label is not identity (coreference stays uncertain)",
            }

    # ── places ──
    for p in _PLACES:
        r = ref(p, "place", "places")
        _add_alias(r, [p])

    # ── cottage fixtures (curated) ──
    for fx in _FIXTURES:
        r = ref(fx, "fixture", "fixtures(curated)")
        _add_alias(r, [fx])

    # ── garden plants (room_state garden bed) ──
    bed = ((stores.get("room") or {}).get("garden") or {}).get("bed") or {}
    for plant, st in bed.items():
        r = ref(str(plant).lower(), "plant", "garden_bed")
        _add_alias(r, [str(plant).lower()])
        r["ledger"]["sown"] = bool((st or {}).get("sown"))
        r["ledger"]["growth"] = (st or {}).get("growth")
        if (st or {}).get("sown"):
            r["depth"]["investigated"] += 1     # sown and tended is a hand-on encounter

    # ── peers ──
    for key, surname in _peer_surnames(_paths()["peers"]):
        r = ref(f"peer:{key}", "peer", "peers")
        _add_alias(r, [surname])
        r["ledger"]["surname"] = surname

    # ── the cat ──
    cat = stores.get("cat") or {}
    r = ref("cat", "being", "cat_state")
    _add_alias(r, ["cat"])
    r["ledger"].update({
        "phase": cat.get("phase"), "bond": cat.get("bond"),
        "distant_seen": ((cat.get("distant") or {}).get("seen_count", 0)),
        "firsts": cat.get("firsts") or {},
    })
    if cat.get("phase") == "kept":
        r["depth"]["kept"] = max(1, r["depth"]["kept"])
    r["depth"]["seen_instrument"] += int((cat.get("distant") or {}).get("seen_count", 0) or 0)
    if cat.get("last_tended"):
        r["depth"]["investigated"] += 1

    # ── books (reading_state stems) ──
    reading = stores.get("reading") or {}
    for bpath, meta in reading.items():
        if str(bpath).startswith("_") or not isinstance(meta, (dict, int, float)):
            continue
        try:
            off = int(meta.get("offset", 0)) if isinstance(meta, dict) else int(meta)
        except Exception:
            off = 0
        stem = Path(str(bpath)).stem.replace("_", " ")
        r = ref(f"book:{stem[:60]}", "book", "reading_state")
        _add_alias(r, [t for t in _tokens(stem) if t not in STOP][:4])
        r["ledger"].update({"read_offset": off,
                            "pct": (meta.get("pct") if isinstance(meta, dict) else None),
                            "sitting": (meta.get("sitting") if isinstance(meta, dict) else None),
                            "rereads": (meta.get("rereads") if isinstance(meta, dict) else None)})
        if off > 0:
            r["depth"]["investigated"] += 1

    # ── identity: the shed name, seeded from the axiom (NOT text-mined — the voiceprint
    #    filter removes 'carl gustav'/'gustav jung' from discovery by design) ──
    ax = stores.get("axiom") or {}
    origin = str(ax.get("origin_name") or "").strip().lower()
    if origin:
        r = ref(origin, "identity", "axiom.origin_name")
        _add_alias(r, [origin])
        r["ledger"]["axiom_basis"] = ax.get("basis")
        r["ledger"]["current_name"] = ax.get("name")
        r["ledger"]["note"] = "the shed name — self-history referent, seeded from the axiom"
    # ── keepsakes: 'kept' depth credit only. The item field is PROSE, not a name (lab lesson) —
    #    it seeds nothing; it can only credit a referent that already exists.
    keeps = stores.get("keepsakes") or []
    for k in keeps if isinstance(keeps, list) else ():
        ktoks = _normset(_tokens((k or {}).get("item", "")))
        if not ktoks:
            continue
        for lbl, rr in graph.items():
            if rr["kind"] not in ("item_class", "sound", "plant", "being"):
                continue
            for alias in rr["aliases"]:
                if set(alias) <= ktoks:
                    rr["depth"]["kept"] += 1
                    rr["ledger"]["kept_from"] = (k or {}).get("from")
                    break

    # alias ambiguity flag (two referents claiming the same tokens — honest, not silent)
    owners: dict[tuple, list[str]] = defaultdict(list)
    for lbl, r in graph.items():
        for alias in r["aliases"]:
            owners[tuple(alias)].append(lbl)
    for alias, labels in owners.items():
        if len(labels) > 1:
            for lbl in labels:
                graph[lbl]["alias_ambiguous"] = sorted(set(labels) - {lbl})[:8]
    return graph


# ─────────────────────────────────────────────────────────────────────────────
# fragment scan
# ─────────────────────────────────────────────────────────────────────────────

def _connect_ro(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def _iter_fragments(conn: sqlite3.Connection, since_ts: float | None = None):
    if since_ts is None:
        cur = conn.execute("SELECT origin, content, timestamp FROM memory_fragments")
    else:
        cur = conn.execute(
            "SELECT origin, content, timestamp FROM memory_fragments WHERE timestamp >= ?",
            (float(since_ts),))
    for row in cur:
        yield row


def _discover_bigrams(db_path: Path, seeded_tokens: set[str]) -> list[dict]:
    """
    The lab's three-layered K1 remedy, in order: VOICEPRINT-STRIP -> head-noun lexicon (seeded
    elsewhere) -> CHANNEL-CONTRAST.

    Pass 1 counts candidate bigrams by distinct LIVED-channel fragment, with the voiceprint
    filter applied inline and seeded tokens excluded. Pass 2 counts those same candidates in the
    NON-lived channels, so a bigram is admitted only if it is genuinely over-represented in
    lived experience — raw lived frequency alone still surfaces the architecture, because the
    lived channel's own text is contaminated at the source (lab FINDING 2).
    """
    lived: Counter = Counter()
    other: Counter = Counter()
    n_lived = n_other = 0
    try:
        conn = _connect_ro(db_path)
    except Exception as e:
        _log("discover_failed", error=repr(e))
        return []
    try:
        for row in _iter_fragments(conn):
            if CHANNEL_OF.get(row["origin"] or "", "thought") != "lived":
                n_other += 1
                continue
            n_lived += 1
            toks = _tokens(row["content"])
            seen_here: set[str] = set()
            for i in range(len(toks) - 1):
                a, b = toks[i], toks[i + 1]
                if a in STOP or b in STOP:
                    continue
                bg = f"{a} {b}"
                if bg in seen_here:
                    continue
                seen_here.add(bg)
                if is_voiceprint(bg):
                    continue
                if a in seeded_tokens or b in seeded_tokens:
                    continue      # already covered by a seeded referent
                lived[bg] += 1
        candidates = {bg for bg, n in lived.most_common(DISCOVER_TOP_N * 8)
                      if n >= DISCOVER_MIN_FRAGMENTS}
        if candidates:
            for row in _iter_fragments(conn):
                if CHANNEL_OF.get(row["origin"] or "", "thought") == "lived":
                    continue
                toks = _tokens(row["content"])
                seen_here = set()
                for i in range(len(toks) - 1):
                    bg = f"{toks[i]} {toks[i + 1]}"
                    if bg in candidates and bg not in seen_here:
                        seen_here.add(bg)
                        other[bg] += 1
    except Exception as e:
        _log("discover_failed", error=repr(e))
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    n_lived = max(1, n_lived)
    n_other = max(1, n_other)
    rows = []
    for bg in candidates:
        lr = lived[bg] / n_lived
        orr = other.get(bg, 0) / n_other
        contrast = lr / (orr + 1.0 / n_other)
        rows.append({"term": bg, "lived_fragments": lived[bg],
                     "other_fragments": other.get(bg, 0),
                     "contrast": round(contrast, 3)})
    # contrast is a FLOOR, never the ranking: ranking by contrast promotes the renderer's own
    # exclusive template text to the top of the graph. Rank by lived evidence.
    rows = [r for r in rows if r["contrast"] >= DISCOVER_MIN_CONTRAST]
    rows.sort(key=lambda r: (-r["lived_fragments"], r["term"]))
    return rows[:DISCOVER_TOP_N]


def _mention_pass(db_path: Path, graph: dict[str, dict], day0: float,
                  since_ts: float | None = None) -> dict:
    """
    One streaming pass. Attributes each fragment to every referent whose alias token-set is a
    subset of the fragment's normalised tokens; accumulates day -> channel counts per referent
    and the store's own day totals (the denominator for every share).
    """
    # inverted index: token -> [(label, alias_tokens)]
    by_token: dict[str, list[tuple[str, tuple]]] = defaultdict(list)
    vocab: set[str] = set()
    for lbl, r in graph.items():
        if r.get("mention_scope") == "none":
            continue
        for alias in r.get("aliases") or ():
            if not alias:
                continue
            key = alias[0]
            by_token[key].append((lbl, tuple(alias)))
            vocab.update(alias)

    day_totals: dict[int, int] = defaultdict(int)
    hits: dict[str, dict[int, Counter]] = defaultdict(lambda: defaultdict(Counter))
    n_frag = 0
    first_ts, last_ts = None, None

    conn = _connect_ro(db_path)
    try:
        for row in _iter_fragments(conn, since_ts):
            ts = float(row["timestamp"] or 0.0)
            if ts <= 0:
                continue
            n_frag += 1
            first_ts = ts if first_ts is None else min(first_ts, ts)
            last_ts = ts if last_ts is None else max(last_ts, ts)
            day = int((ts - day0) // 86400)
            day_totals[day] += 1
            ch = CHANNEL_OF.get(row["origin"] or "", "thought")
            ns = _normset(_tokens(row["content"]))
            present = ns & vocab
            if not present:
                continue
            matched: set[str] = set()
            for t in present:
                for lbl, alias in by_token.get(t, ()):
                    if lbl in matched:
                        continue
                    if all(a in ns for a in alias):
                        matched.add(lbl)
                        hits[lbl][day][ch] += 1
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return {"hits": hits, "day_totals": dict(day_totals), "n_fragments": n_frag,
            "first_ts": first_ts, "last_ts": last_ts}


# ─────────────────────────────────────────────────────────────────────────────
# derived statistics — windows, trend shapes, breaks
# ─────────────────────────────────────────────────────────────────────────────

def _series(days: dict) -> dict[int, int]:
    out = {}
    for d, chs in (days or {}).items():
        try:
            out[int(d)] = int(sum(chs.values()))
        except Exception:
            continue
    return out


def _channels_total(days: dict) -> dict[str, int]:
    c: Counter = Counter()
    for chs in (days or {}).values():
        for k, v in (chs or {}).items():
            c[k] += int(v)
    return dict(c)


def _windowed(days: dict, day_totals: dict[int, int], now_day: int, window_days: float) -> dict:
    lo = now_day - int(window_days) + 1
    mentions, chans = 0, Counter()
    for d, chs in (days or {}).items():
        if int(d) >= lo:
            for k, v in (chs or {}).items():
                chans[k] += int(v)
                mentions += int(v)
    total = sum(n for d, n in day_totals.items() if int(d) >= lo)
    return {"window_days": window_days, "from_day": lo, "to_day": now_day,
            "mentions": mentions, "channels": dict(chans),
            "store_fragments": total,
            "share": round(mentions / total, 6) if total else None}


def _buckets(series: dict[int, int], day_totals: dict[int, int], max_day: int) -> list[dict]:
    """Share-of-store per bucket. Buckets whose store-total is below the floor are DROPPED —
    a hole in the store must never be readable as a decline."""
    b_ment: dict[int, int] = defaultdict(int)
    b_tot: dict[int, int] = defaultdict(int)
    for d, n in series.items():
        b_ment[int(d) // BUCKET_DAYS] += n
    for d, n in day_totals.items():
        b_tot[int(d) // BUCKET_DAYS] += n
    out = []
    for b in range(0, max_day // BUCKET_DAYS + 1):
        tot = b_tot.get(b, 0)
        if tot < MIN_BUCKET_FRAGMENTS:
            continue
        out.append({"bucket": b, "start_day": b * BUCKET_DAYS, "store_fragments": tot,
                    "mentions": b_ment.get(b, 0),
                    "share": round(b_ment.get(b, 0) / tot, 6)})
    return out


def _classify_shape(buckets: list[dict], total_mentions: int) -> tuple[str, dict]:
    """
    Six shapes, in priority order. Rules are deterministic and reproduce the lab's hand-read of
    Du's real history (jung / glass float / door / tide / rock / cat / oystercatcher).
    """
    ev: dict[str, Any] = {}
    if total_mentions < MIN_TREND_MENTIONS or len(buckets) < 2:
        return "insufficient", {"reason": f"mentions={total_mentions}, buckets={len(buckets)}"}
    shares = [b["share"] for b in buckets]
    n = len(shares)
    peak = max(shares)
    peak_i = shares.index(peak)
    last = shares[-1]
    nonzero = [i for i, s in enumerate(shares) if s > 0]
    if not nonzero:
        return "insufficient", {"reason": "no nonzero bucket"}
    first_nz = nonzero[0]
    third = max(1, n // 3)
    early = sum(shares[:third]) / third
    ratio = (last / peak) if peak > 0 else 0.0
    mean = sum(shares) / n
    sd = (sum((s - mean) ** 2 for s in shares) / max(1, n - 1)) ** 0.5
    cv = (sd / mean) if mean > 0 else 99.0
    ev.update({"shares": [round(s, 5) for s in shares], "peak": round(peak, 5),
               "peak_bucket": peak_i, "last": round(last, 5), "first_nonzero_bucket": first_nz,
               "last_over_peak": round(ratio, 4), "cv": round(cv, 4),
               "early_mean": round(early, 5), "n_buckets": n})

    # 1. NEW / ACTIVE — arrived in the last two buckets and is at (or near) its own maximum
    if first_nz >= n - 2 and last >= 0.8 * peak and last > 0:
        return "new_active", ev
    # 2. EXTINCT GHOST — bulk early, extinguished. Floor matters: ~0 now.
    if peak_i <= n // 2 and ratio <= 0.15:
        return "extinct_ghost", ev
    # 3. GROWING WORLD-PRESENCE — rising to its own maximum, well above its early level
    if last >= 0.8 * peak and peak_i >= n - 2 and last >= 2.0 * max(early, 1e-9):
        return "growing_presence", ev
    # 4. SETTLED COMPANION — novelty burst, then a NONZERO floor (settling ≠ extinction)
    if peak_i >= 1 and 0.15 < ratio <= 0.5 and last > 0 and len(nonzero) >= 3:
        return "settled_companion", ev
    # 5. PERENNIAL SYMBOL — present throughout, low variance, still near its level
    if len(nonzero) >= max(2, int(0.8 * n)) and cv <= 0.7 and last >= 0.4 * peak:
        return "perennial_symbol", ev
    # 6. EPISODIC — everything else: sparse, irregular, comes and goes
    return "episodic", ev


def _trend_break(series: dict[int, int], day_totals: dict[int, int], day0: float,
                 buckets: list[dict]) -> dict:
    """Largest single-step share drop and rise — the cross-link hook for the diagnosis layer."""
    out: dict[str, Any] = {}

    def _extreme(points: list[tuple[int, float]], sign: int):
        best = None
        for (d0, s0), (d1, s1) in zip(points, points[1:]):
            delta = s1 - s0
            if sign * delta <= 0:
                continue
            if best is None or abs(delta) > abs(best["delta"]):
                best = {"from_day": d0, "to_day": d1, "from_share": round(s0, 6),
                        "to_share": round(s1, 6), "delta": round(delta, 6),
                        "date": time.strftime("%Y-%m-%d", time.localtime(day0 + d1 * 86400))}
        return best

    bpts = [(b["start_day"], b["share"]) for b in buckets]
    out["bucket_drop"] = _extreme(bpts, -1)
    out["bucket_rise"] = _extreme(bpts, +1)
    dpts = []
    for d in sorted(day_totals):
        tot = day_totals[d]
        if tot >= MIN_DAY_FRAGMENTS:
            dpts.append((int(d), series.get(int(d), 0) / tot))
    out["daily_drop"] = _extreme(dpts, -1)
    out["daily_rise"] = _extreme(dpts, +1)
    return out


def _load_tuples(path: Path) -> list[dict]:
    """Read-only load of geometry_tuples.jsonl. Only the three fields the commonality pass needs
    (ts, sounds, affect) are kept — this file is large (Du writes it continuously) and the module
    contract forbids anything past a plain read."""
    out: list[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    t = json.loads(line)
                except Exception:
                    continue
                if not t.get("ts"):
                    continue
                out.append({"ts": float(t["ts"]), "sounds": t.get("sounds") or [],
                            "affect": t.get("affect") or {}, "source": t.get("source"),
                            "stamp": bool(t.get("stamp")), "thought": (t.get("thought") or "")[:200]})
    except Exception as e:
        _log("tuples_load_failed", error=repr(e))
    # J-3752/F-4361: drop census stamp rows (marked + unmarked pre-J-3455 twins), file order, then strip helper keys
    try:
        from core.stamp_rows import drop_stamp_rows
        out = drop_stamp_rows(out)
    except Exception as e:
        _log("tuples_stamp_drop_failed", error=repr(e))
    for t in out:
        t.pop("source", None); t.pop("stamp", None); t.pop("thought", None)
    return out


def _pair_weight(tuples: list[dict], pred, affect_key: str) -> tuple[float | None, int, int]:
    """mean(affect|pred) - mean(affect|not pred). None if either arm is below the floor — same
    discipline as the lab: an underpowered comparison reports UNDETERMINED, never a number."""
    with_s: list[float] = []
    without: list[float] = []
    for t in tuples:
        a = t["affect"].get(affect_key)
        if a is None:
            continue
        (with_s if pred(t["sounds"]) else without).append(float(a))
    if len(with_s) < COMMONALITY_MIN_ARM or len(without) < COMMONALITY_MIN_ARM:
        return None, len(with_s), len(without)
    return (sum(with_s) / len(with_s)) - (sum(without) / len(without)), len(with_s), len(without)


def _commonality_pass(tuples: list[dict], now_ts: float, window_days: float) -> dict:
    """
    L5 (all-time weight + shuffle-null z-score, N_SHUFFLES) x L6 (the same weight recomputed over
    just the last `window_days`, so a caller sees whether the all-time figure still holds NOW) —
    reported together per pair, per the job briefing's 'windowed commonality weights... matching
    L5/L6' scope line. Verdict (SIGNAL / null-indistinguishable) is a live computation over
    whatever data is on disk today, never a hardcoded prior verdict — see the module docstring's
    scope note on why this must not claim 3-for-3 by construction.
    """
    rng = random.Random(COMMONALITY_SEED)
    cutoff = now_ts - window_days * 86400
    windowed = [t for t in tuples if t["ts"] >= cutoff]
    out = []
    vals_cache: dict[str, list] = {}
    for name, pred, key in COMMONALITY_PAIRS:
        real, nw, nwo = _pair_weight(tuples, pred, key)
        row = {"pair": name, "affect_key": key, "n_with_alltime": nw, "n_without_alltime": nwo}
        if real is None:
            row.update({"verdict": "UNDETERMINED (insufficient n)", "weight_alltime": None, "z": None})
        else:
            if key not in vals_cache:
                vals_cache[key] = [t["affect"].get(key) for t in tuples]
            vals = vals_cache[key]
            idx = list(range(len(tuples)))
            nulls = []
            for _ in range(N_SHUFFLES):
                rng.shuffle(idx)
                shuffled = [{"affect": {key: vals[j]}, "sounds": tuples[i]["sounds"]}
                            for i, j in zip(range(len(tuples)), idx)]
                w, _nw, _nwo = _pair_weight(shuffled, pred, key)
                if w is not None:
                    nulls.append(w)
            if nulls:
                mu = sum(nulls) / len(nulls)
                sd = (sum((x - mu) ** 2 for x in nulls) / max(1, len(nulls) - 1)) ** 0.5
                z = (real - mu) / sd if sd > 1e-9 else 0.0
            else:
                z = 0.0
            row.update({"weight_alltime": round(real, 4), "z": round(z, 2),
                        "verdict": "SIGNAL" if abs(z) >= 2 else "null-indistinguishable"})
        w_win, nw_win, nwo_win = _pair_weight(windowed, pred, key)
        row.update({"weight_windowed": round(w_win, 4) if w_win is not None else None,
                    "n_with_windowed": nw_win, "n_without_windowed": nwo_win})
        out.append(row)
    return {"window_days": window_days, "n_shuffles": N_SHUFFLES, "seed": COMMONALITY_SEED,
            "n_tuples_alltime": len(tuples), "n_tuples_windowed": len(windowed), "pairs": out}


# ─────────────────────────────────────────────────────────────────────────────
# L9 — coreference proposals (proposal-only, never auto-merged)
# ─────────────────────────────────────────────────────────────────────────────

def _coreference_proposals(graph: dict[str, dict]) -> list[dict]:
    """
    Port of lane2_lab.py's l9_coreference(): a referent whose channel mix is substantial on BOTH
    the 'read' and 'lived' sides is flagged as a candidate that MAY conflate two distinct
    referents Du holds under one label (book-knowledge of X vs lived experience of X) — the same
    'a shared label is not identity' law the per-instance item coreference above already applies,
    generalised across the whole lexicon rather than just item-instance-to-class. Proposal-only:
    nothing here merges or renames a referent."""
    props = []
    for lbl, r in graph.items():
        ch = r.get("channels") or {}
        read, lived = ch.get("read", 0), ch.get("lived", 0)
        if read >= 5 and lived >= 5:
            props.append({
                "referent": lbl, "read": read, "lived": lived,
                "proposal": f"book-{lbl} possibly_same_referent_as lived-{lbl} — UNRESOLVED",
                "relation": "possibly_same_referent_as", "strength": min(read, lived),
            })
    props.sort(key=lambda p: -p["strength"])
    return props


def _derive(graph: dict[str, dict], day_totals: dict[int, int], day0: float,
            now_ts: float, window_days: float) -> None:
    """Recompute every derived statistic from the stored daily series (idempotent by design)."""
    max_day = max(day_totals) if day_totals else 0
    now_day = max(max_day, int((now_ts - day0) // 86400))
    total_fragments = sum(day_totals.values()) or 1
    for lbl, r in graph.items():
        series = _series(r.get("days"))
        chans = _channels_total(r.get("days"))
        total = sum(series.values())
        r["mentions"] = {str(d): n for d, n in sorted(series.items())}
        r["channels"] = chans
        r["total_mentions"] = total
        r["depth"]["seen"] = int(r["depth"].get("seen_instrument", 0)) + chans.get("lived", 0)
        r["alltime"] = {"mentions": total, "store_fragments": total_fragments,
                        "share": round(total / total_fragments, 6)}
        r["windowed"] = _windowed(r.get("days"), day_totals, now_day, window_days)
        bkts = _buckets(series, day_totals, max_day)
        shape, ev = _classify_shape(bkts, total)
        r["trend"] = {
            "shape": shape, "bucket_days": BUCKET_DAYS, "buckets": bkts, "evidence": ev,
            "break": _trend_break(series, day_totals, day0, bkts),
        }
        # the float profile: rumination-heavy vs acted-on
        th, lv = chans.get("thought", 0), chans.get("lived", 0)
        r["float_profile"] = {
            "thought": th, "lived": lv, "read": chans.get("read", 0),
            "dream": chans.get("dream", 0), "told": chans.get("told", 0),
            "thought_action_ratio": round(th / max(1, lv), 2),
            "float_like": bool(th >= 20 and th >= 5 * max(1, lv)),
        }
        first_day = min(series) if series else None
        last_day = max(series) if series else None
        r["first_mention_day"] = first_day
        r["last_mention_day"] = last_day
        r["days_silent"] = round((now_ts - (day0 + (last_day + 1) * 86400)) / 86400, 2) \
            if last_day is not None else None


# ─────────────────────────────────────────────────────────────────────────────
# store loading
# ─────────────────────────────────────────────────────────────────────────────

def _load_stores() -> dict:
    p = _paths()
    stores = {
        "sound": _jload(p["sound"], {}),
        "substrate": _jload(p["substrate"], {}),
        "keepsakes": _jload(p["keepsakes"], []),
        "reading": _jload(p["reading"], {}),
        "cat": _jload(p["cat"], {}),
        "room": _jload(p["room"], {}),
        "axiom": _jload(p["axiom"], {}),
    }
    extra = _jload(p["voiceprint_extra"], None)
    if isinstance(extra, list):
        add_voiceprint(extra)
    elif isinstance(extra, dict) and isinstance(extra.get("terms"), list):
        add_voiceprint(extra["terms"])
    return stores


def _seeded_tokens(graph: dict[str, dict]) -> set[str]:
    out: set[str] = set()
    for r in graph.values():
        for alias in r.get("aliases") or ():
            out.update(alias)
    return out


def _merge_hits(graph: dict[str, dict], hits: dict, replace_from_day: int | None) -> None:
    """Write day-buckets into referents. With `replace_from_day` set, every day at or after it
    is REPLACED (not incremented) — that is what makes refresh() idempotent."""
    if replace_from_day is not None:
        for r in graph.values():
            for d in [d for d in list(r.get("days") or {}) if int(d) >= replace_from_day]:
                r["days"].pop(d, None)
    for lbl, days in hits.items():
        r = graph.get(lbl)
        if r is None:
            continue
        dd = r.setdefault("days", {})
        for d, chs in days.items():
            key = str(d)
            if replace_from_day is None:
                cur = dd.setdefault(key, {})
                for c, n in chs.items():
                    cur[c] = cur.get(c, 0) + int(n)
            else:
                dd[key] = {c: int(n) for c, n in chs.items()}


# ─────────────────────────────────────────────────────────────────────────────
# public API
# ─────────────────────────────────────────────────────────────────────────────

def build_full(window_days: float = WINDOW_DAYS) -> dict:
    """The retroactive backfill: rebuild the whole object-graph from full history."""
    t0 = time.time()
    try:
        p = _paths()
        if not p["db"].exists():
            return {"ok": False, "error": f"db not found: {p['db']}"}
        stores = _load_stores()
        graph = _build_lexicon(stores)
        n_seeded = len(graph)

        discovered = _discover_bigrams(p["db"], _seeded_tokens(graph))
        for d in discovered:
            bg = d["term"]
            if bg in graph:
                continue
            r = _new_ref(bg, "discovered", "channel_contrast")
            _add_alias(r, bg.split())
            r["ledger"].update(d)
            # discovery is the WEAKEST layer of the lexicon — text mining over a store whose own
            # text carries the architecture's voice. Marked ungraded so no consumer mistakes a
            # discovered bigram for an instrument-backed referent.
            r["trust"] = "ungraded"
            graph[bg] = r

        # day0 = the store's own first timestamp
        conn = _connect_ro(p["db"])
        try:
            row = conn.execute(
                "SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM memory_fragments "
                "WHERE timestamp > 0").fetchone()
        finally:
            conn.close()
        day0 = float(row[0] or time.time())
        store_last_ts = float(row[1] or day0)

        scan = _mention_pass(p["db"], graph, day0)
        _merge_hits(graph, scan["hits"], replace_from_day=None)
        now_ts = time.time()
        _derive(graph, scan["day_totals"], day0, now_ts, window_days)

        tuples = _load_tuples(p["tuples"])
        commonality = _commonality_pass(tuples, now_ts, window_days)
        coref = _coreference_proposals(graph)

        doc = {
            "schema_version": SCHEMA_VERSION,
            "built_ts": now_ts,
            "build_kind": "full",
            "build_seconds": round(time.time() - t0, 2),
            "window_days": window_days,
            "bucket_days": BUCKET_DAYS,
            "day0": day0,
            "day0_date": time.strftime("%Y-%m-%d", time.localtime(day0)),
            "n_fragments": scan["n_fragments"],
            "last_fragment_ts": scan["last_ts"] or store_last_ts,
            "day_totals": {str(d): n for d, n in sorted(scan["day_totals"].items())},
            "n_seeded": n_seeded,
            "n_discovered": len(discovered),
            "discovered": discovered,
            "commonality": commonality,
            "coreference_proposals": coref,
            "referents": graph,
        }
        ok = _atomic_write_json(p["graph"], doc)
        stats = _summarise(doc)
        stats.update({"ok": ok, "written": str(p["graph"]),
                      "build_seconds": doc["build_seconds"]})
        _log("build_full", **{k: v for k, v in stats.items() if k != "by_shape"},
             by_shape=stats.get("by_shape"))
        global _GRAPH_CACHE, _GRAPH_CACHE_KEY
        _GRAPH_CACHE, _GRAPH_CACHE_KEY = doc, None
        return stats
    except Exception as e:
        _log("build_full_failed", error=repr(e))
        return {"ok": False, "error": repr(e), "build_seconds": round(time.time() - t0, 2)}


def refresh(since_ts: float, window_days: float | None = None, *, commonality: bool = True) -> dict:
    """
    Incremental update. Rescans fragments from the START OF THE DAY containing `since_ts` and
    REPLACES those day-buckets, so calling refresh twice with the same argument is a no-op —
    idempotent by construction. The lexicon is reused (discovery only runs in build_full).

    `commonality=False` (J-2217, 2026-10-16; default True = unchanged behaviour) skips the L5/L6
    shuffle-null pass and keeps the document's previous `commonality` block as it was, stamping
    `commonality_skipped_ts`. Measured 2026-10-16 on the live stores: that pass alone is ~165 s of
    pure-Python CPU over 139k geometry tuples (the mention re-scan of a day is ~1 s), so the
    once-per-sleep refresh for core/world_ledger_ask.py -- which never reads commonality -- skips it
    rather than hold the GIL against the event loop for three minutes every sleep.
    """
    t0 = time.time()
    try:
        p = _paths()
        doc = _read_graph()
        if not doc:
            return {"ok": False, "error": "no graph yet — call build_full() first"}
        graph = doc.get("referents") or {}
        day0 = float(doc.get("day0") or 0.0)
        if day0 <= 0:
            return {"ok": False, "error": "graph has no day0"}
        wd = float(window_days if window_days is not None else doc.get("window_days", WINDOW_DAYS))

        since_day = max(0, int((float(since_ts) - day0) // 86400))
        day_start_ts = day0 + since_day * 86400          # snap to the day boundary

        scan = _mention_pass(p["db"], graph, day0, since_ts=day_start_ts)
        _merge_hits(graph, scan["hits"], replace_from_day=since_day)

        day_totals = {int(d): int(n) for d, n in (doc.get("day_totals") or {}).items()
                      if int(d) < since_day}
        day_totals.update(scan["day_totals"])

        # instrument-sourced ledgers/depth/properties are snapshots — re-seed them wholesale
        try:
            fresh = _build_lexicon(_load_stores())
            for lbl, fr in fresh.items():
                if lbl in graph:
                    tgt = graph[lbl]
                    tgt["ledger"] = fr["ledger"]
                    tgt["depth"] = fr["depth"]
                    tgt["aliases"] = fr["aliases"]
                    tgt["sources"] = fr["sources"]
                    tgt["mention_scope"] = fr["mention_scope"]
                    if "properties" in fr:
                        tgt["properties"] = fr["properties"]
                        tgt["property_summary"] = fr["property_summary"]
                    if "coreference" in fr:
                        tgt["coreference"] = fr["coreference"]
                else:
                    graph[lbl] = fr
        except Exception as e:
            _log("refresh_reseed_failed", error=repr(e))

        now_ts = time.time()
        _derive(graph, day_totals, day0, now_ts, wd)

        if commonality:
            tuples = _load_tuples(p["tuples"])
            common = _commonality_pass(tuples, now_ts, wd)
        else:
            common = doc.get("commonality") or {}
            doc["commonality_skipped_ts"] = now_ts
        coref = _coreference_proposals(graph)

        doc.update({
            "built_ts": now_ts, "build_kind": "refresh",
            "build_seconds": round(time.time() - t0, 2),
            "window_days": wd,
            "refreshed_from_day": since_day,
            "refreshed_from_ts": day_start_ts,
            "n_fragments": sum(day_totals.values()),
            "last_fragment_ts": max(float(doc.get("last_fragment_ts") or 0.0),
                                    float(scan["last_ts"] or 0.0)),
            "day_totals": {str(d): n for d, n in sorted(day_totals.items())},
            "commonality": common,
            "coreference_proposals": coref,
            "referents": graph,
        })
        ok = _atomic_write_json(p["graph"], doc)
        stats = _summarise(doc)
        stats.update({"ok": ok, "rescanned_fragments": scan["n_fragments"],
                      "from_day": since_day, "build_seconds": doc["build_seconds"]})
        _log("refresh", **{k: v for k, v in stats.items() if k != "by_shape"},
             by_shape=stats.get("by_shape"))
        global _GRAPH_CACHE, _GRAPH_CACHE_KEY
        _GRAPH_CACHE, _GRAPH_CACHE_KEY = doc, None
        return stats
    except Exception as e:
        _log("refresh_failed", error=repr(e))
        return {"ok": False, "error": repr(e), "build_seconds": round(time.time() - t0, 2)}


def get(referent: str) -> dict | None:
    """One referent's full record (exact label, then alias/case-insensitive lookup)."""
    try:
        doc = _read_graph()
        if not doc:
            return None
        refs = doc.get("referents") or {}
        if referent in refs:
            return refs[referent]
        low = str(referent or "").strip().lower()
        for lbl, r in refs.items():
            if lbl.lower() == low:
                return r
        for lbl, r in refs.items():
            for alias in r.get("aliases") or ():
                if list(alias) == [low]:
                    return r
        return None
    except Exception as e:
        _log("get_failed", referent=referent, error=repr(e))
        return None


def commonality() -> dict:
    """The L5/L6-scoped windowed commonality weights vs affect (see COMMONALITY_PAIRS). Computed
    at the last build/refresh, not on demand — call build_full()/refresh() first. {} if no graph
    yet or the field predates this addition (an older graph.json on disk)."""
    try:
        doc = _read_graph()
        return (doc or {}).get("commonality") or {}
    except Exception as e:
        _log("commonality_failed", error=repr(e))
        return {}


def coreference_proposals(limit: int = 25) -> list[dict]:
    """The L9-scoped possibly_same_referent_as candidates, strongest first. Proposal-only — never
    auto-merged; nothing reads this to change graph structure."""
    try:
        doc = _read_graph()
        props = (doc or {}).get("coreference_proposals") or []
        return props[:limit] if limit else list(props)
    except Exception as e:
        _log("coreference_proposals_failed", error=repr(e))
        return []


def status() -> dict:
    """Counts for the HUD. Never raises."""
    try:
        doc = _read_graph()
        if not doc:
            return {"ok": False, "built": False, "out_dir": str(_OUT_DIR)}
        s = _summarise(doc)
        s.update({
            "ok": True, "built": True,
            "built_ts": doc.get("built_ts"),
            "built_age_hours": round((time.time() - float(doc.get("built_ts") or 0)) / 3600, 2),
            "build_kind": doc.get("build_kind"),
            "build_seconds": doc.get("build_seconds"),
            "window_days": doc.get("window_days"),
            "day0_date": doc.get("day0_date"),
            "n_fragments": doc.get("n_fragments"),
            "out_dir": str(_OUT_DIR),
        })
        return s
    except Exception as e:
        return {"ok": False, "error": repr(e)}


def _summarise(doc: dict) -> dict:
    refs = doc.get("referents") or {}
    by_kind: Counter = Counter()
    by_shape: Counter = Counter()
    edges = 0
    props = 0
    float_like = 0
    for r in refs.values():
        by_kind[r.get("kind", "?")] += 1
        by_shape[((r.get("trend") or {}).get("shape")) or "?"] += 1
        edges += int(r.get("total_mentions") or 0)
        props += len(r.get("properties") or {})
        if (r.get("float_profile") or {}).get("float_like"):
            float_like += 1
    commonality = doc.get("commonality") or {}
    n_signal = sum(1 for row in commonality.get("pairs", []) if row.get("verdict") == "SIGNAL")
    return {"n_referents": len(refs), "n_mention_edges": edges,
            "n_property_atoms": props, "n_float_like": float_like,
            "by_kind": dict(by_kind), "by_shape": dict(by_shape),
            "n_discovered": doc.get("n_discovered"),
            "n_commonality_pairs": len(commonality.get("pairs", [])),
            "n_commonality_signal": n_signal,
            "n_coreference_proposals": len(doc.get("coreference_proposals") or [])}


# ── graph cache (mtime-keyed) ───────────────────────────────────────────────
_GRAPH_CACHE: dict | None = None
_GRAPH_CACHE_KEY: tuple | None = None


def _read_graph() -> dict | None:
    global _GRAPH_CACHE, _GRAPH_CACHE_KEY
    try:
        p = _paths()["graph"]
        if not p.exists():
            return _GRAPH_CACHE if _GRAPH_CACHE_KEY is None and _GRAPH_CACHE else None
        st = p.stat()
        key = (str(p), st.st_mtime_ns, st.st_size)
        if _GRAPH_CACHE is not None and _GRAPH_CACHE_KEY == key:
            return _GRAPH_CACHE
        doc = _jload(p, None)
        if doc is None:
            return None
        _GRAPH_CACHE, _GRAPH_CACHE_KEY = doc, key
        return doc
    except Exception:
        return None


if __name__ == "__main__":       # produce-only CLI: python -m core.object_graph
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(build_full(), ensure_ascii=False, indent=1, default=str))
