"""
Nascence — Generative Epistemic World Substrate (Generation 3B, 2026-08-11)
============================================================================
The missing half of Generation 3. The Epistemic Affordance Advisor answers "What could I do
to find out?" — this module answers "What is there to find out, and what actually exists behind
the observation?"

5-Layer Architecture:
    Layer 1: CAUSAL_WORLD_STATE — hidden simulation biography (species, exposure, storms)
    Layer 2: PHYSICAL_STATE     — generative properties (density, moisture, roughness, rounding)
    Layer 3: OBSERVATION        — raw perceptual facts from specific actions (core/observation.py)
    Layer 4: DOMAIN_KNOWLEDGE   — general diagnostic relationships (archived: scripts/archive/world_knowledge.py, no runtime module)
    Layer 5: DU_INFERENCE       — candidate hypotheses, confidence, model revisions

Architectural Contracts:
    - Invariant 1: Du NEVER receives Layer 1 data directly. The arrow is lossy.
    - Invariant 2: Observations NEVER overwrite observations. Each is timestamped and append-only.
    - Invariant 3: Inferences carry explicit provenance (which observations + which knowledge).
    - Invariant 4: UNDETERMINED is a successful epistemic outcome, not a failure.
    - Invariant 5: Causal events (storms, sun, tides) modify physical state generatively.

Extends (does NOT replace) core/world_objects.py — the existing spatial/history persistence layer.
"""
from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core import profile

logger = logging.getLogger("nascence.world_substrate")

_DATA = Path(__file__).parent.parent / "data"
_SUBSTRATE_F = _DATA / "world_substrate.json"
_SUBSTRATE_LOG = _DATA / "world_substrate_events.jsonl"


# ── Provenance & Outcome Enums ──────────────────────────────────────────────

class Provenance(str, Enum):
    WORLD_TRUTH = "WORLD_TRUTH"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class EpistemicOutcome(str, Enum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    UNDETERMINED = "UNDETERMINED"
    UNOBSERVED = "UNOBSERVED"
    CONFLICTING = "CONFLICTING"


# ── Core Data Model ─────────────────────────────────────────────────────────

@dataclass
class PhysicalProperty:
    """A single property of a world object with explicit provenance tracking."""
    key: str
    value: Any
    provenance: str  # Provenance enum value
    accessible_to_du: bool = False
    observed_at: float | None = None
    observed_via: str | None = None      # action that produced this observation
    confidence: float | None = None
    basis: list[str] = field(default_factory=list)  # observation/knowledge IDs supporting this

    def to_dict(self) -> dict:
        d = asdict(self)
        d = {k: v for k, v in d.items() if v is not None}
        return d

    @classmethod
    def from_dict(cls, d: dict) -> PhysicalProperty:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ObservationRecord:
    """A single observation Du made of this object — append-only, never overwritten."""
    observation_id: str
    timestamp: float
    action: str                      # "look", "pick_up", "inspect_end", etc.
    features: dict[str, str]         # {feature_name: qualitative_value}
    provenance: str = Provenance.OBSERVED.value

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> ObservationRecord:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class InferenceRecord:
    """A hypothesis Du formed about this object — carries provenance back to observations."""
    inference_id: str
    timestamp: float
    hypothesis: str
    confidence: float
    supporting_observations: list[str]   # observation_ids
    supporting_knowledge: list[str]      # knowledge entry references
    outcome: str = EpistemicOutcome.UNOBSERVED.value
    superseded_by: str | None = None
    # J-2524 (I-0102): optional, additive -- what he could observe / do / withhold that would tell this
    # hypothesis from coincidence (core/object_hypothesis.intervention_test). None = never derived (dropped
    # by to_dict, so rows written with the NASCENCE_INTERVENTION_TEST gate off are byte-identical); [] = derived,
    # no deterministic candidate. No consumer reads it yet.
    intervention_test: list | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d = {k: v for k, v in d.items() if v is not None}
        return d

    @classmethod
    def from_dict(cls, d: dict) -> InferenceRecord:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SubstrateObject:
    """
    A physical object with 5-layer epistemic provenance.

    Layer 1 (causal_state): Hidden world truth — accessible_to_du is always False.
    Layer 2 (physical_state): Generative properties that produce observable consequences.
    Layer 3 (observations): Append-only record of what Du actually perceived.
    Layer 4: Domain knowledge was scripts/archive/world_knowledge.py (archived, no runtime module).
    Layer 5 (inferences): Du's hypotheses with provenance chains.
    """
    object_id: str
    name: str
    location: str
    object_class: str                               # "driftwood", "stone", "shell", "plant"

    # Layer 1: Hidden causal world state (Du cannot access)
    causal_state: dict[str, Any] = field(default_factory=dict)

    # Layer 2: Physical state (generates observations)
    physical_state: dict[str, float] = field(default_factory=dict)

    # Causal biography (generative event sequence)
    causal_history: list[dict] = field(default_factory=list)

    # Layer 3: Du's observations (append-only)
    observations: list[dict] = field(default_factory=list)

    # Layer 5: Du's inferences (with provenance)
    inferences: list[dict] = field(default_factory=list)

    def get_world_truth(self, key: str) -> Any:
        """Layer 1 access — for the SIMULATION ONLY, never exposed to Du."""
        return self.causal_state.get(key)

    def get_physical(self, key: str) -> float | None:
        """Layer 2 access — used by observation.py to generate perceptual output."""
        return self.physical_state.get(key)

    def record_observation(self, record: ObservationRecord) -> None:
        """Append-only observation recording. Observations are never overwritten."""
        self.observations.append(record.to_dict())

    def record_inference(self, record: InferenceRecord) -> None:
        """Record a hypothesis Du formed, with provenance chain."""
        self.inferences.append(record.to_dict())

    def get_observation_history(self) -> list[ObservationRecord]:
        """All observations Du has made of this object, chronologically."""
        return [ObservationRecord.from_dict(d) for d in self.observations]

    def get_inference_history(self) -> list[InferenceRecord]:
        """All inferences Du has formed about this object, chronologically."""
        return [InferenceRecord.from_dict(d) for d in self.inferences]

    def get_latest_inference(self, hypothesis_prefix: str = "") -> InferenceRecord | None:
        """Most recent non-superseded inference matching a hypothesis prefix."""
        for d in reversed(self.inferences):
            rec = InferenceRecord.from_dict(d)
            if rec.superseded_by is None and rec.hypothesis.startswith(hypothesis_prefix):
                return rec
        return None

    def to_dict(self) -> dict:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "location": self.location,
            "object_class": self.object_class,
            "causal_state": self.causal_state,
            "physical_state": self.physical_state,
            "causal_history": self.causal_history,
            "observations": self.observations,
            "inferences": self.inferences,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SubstrateObject:
        return cls(
            object_id=d["object_id"],
            name=d.get("name", d["object_id"]),
            location=d.get("location", "shore"),
            object_class=d.get("object_class", "unknown"),
            causal_state=d.get("causal_state", {}),
            physical_state=d.get("physical_state", {}),
            causal_history=d.get("causal_history", []),
            observations=d.get("observations", []),
            inferences=d.get("inferences", []),
        )


# ── Registry (Load/Save) ────────────────────────────────────────────────────

_cache: dict[str, SubstrateObject] = {}
_cache_ts: float = 0.0


def _load() -> dict[str, SubstrateObject]:
    global _cache, _cache_ts
    if _cache and (time.time() - _cache_ts < 5.0):
        return _cache
    if _SUBSTRATE_F.exists():
        try:
            raw = json.loads(_SUBSTRATE_F.read_text(encoding="utf-8"))
            _cache = {k: SubstrateObject.from_dict(v) for k, v in raw.items()}
        except Exception:
            _cache = {}
    else:
        _cache = _seed_default_objects()
        _save()
    _cache_ts = time.time()
    return _cache


def _save() -> None:
    path = profile.guard_path(_SUBSTRATE_F)   # J-0610: real data/ only if this process is live; raises if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = {k: v.to_dict() for k, v in _cache.items()}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except Exception as e:
        logger.warning("world_substrate save failed: %s", e)


# ── Public API ───────────────────────────────────────────────────────────────

def get_object(object_id: str) -> SubstrateObject | None:
    """Retrieve a substrate object by ID."""
    return _load().get(object_id)


def get_objects_at_location(location: str) -> list[SubstrateObject]:
    """All substrate objects at a given location."""
    return [obj for obj in _load().values() if obj.location == location]


def update_location(object_id: str, new_location: str) -> bool:
    """Sync this authority's location field when world_objects.py (the position authority) moves an
    object — e.g. keepsakes.py's keep(). Without this, the two registries silently disagree about
    where a thing is (world_objects says 'study', world_substrate still says 'shore') — the exact bug
    class this whole integration exists to close. False if the object isn't tracked here."""
    objs = _load()
    obj = objs.get(object_id)
    if not obj:
        return False
    obj.location = new_location
    _save()
    return True


def get_generative_state(object_id: str) -> dict:
    """2026-08-14: the state observation.py actually needs. Layer 2 physical floats PLUS the two
    causal keys that generate observable form ('structure', 'wood_type') — observation.py reads
    them from physical_state, but they were seeded into causal_state only, so every object read
    as 'irregular/fine diffuse rings' (species discrimination collapsed to uniform output).
    Passing them here does NOT leak Layer 1: they only shape which qualitative percepts the
    lossy observation generator emits — Du still never sees the keys or the species."""
    obj = get_object(object_id)
    if not obj:
        return {}
    g = dict(obj.physical_state)
    # J-2388 (F-3087) / J-2411 (D-0479 part 2): the two form keys are Layer-2 facts ('structure' /
    # 'wood_type' in physical_state, mirrored at spawn and copied into the existing objects by
    # scripts/migrate_wood_form_keys.py, applied 2026-10-18). This function reads physical_state ONLY:
    # the pre-migration Layer-1 (causal_state) fallback is gone, so Layer 1 cannot reach text by this
    # path at all. An object without the Layer-2 key reads "unknown" (the 2026-08-14 default).
    for l2, _l1 in _FORM_KEYS:
        g.setdefault(l2, "unknown")
    return g


# J-2388: (Layer-2 physical_state key, its Layer-1 causal_state twin). Used by spawn_object() to mirror
# the form keys into physical_state at birth; get_generative_state() reads only the Layer-2 side (J-2411).
_FORM_KEYS = (("structure", "original_structure"), ("wood_type", "wood_type"))


def find_object_at(location: str, target_text: str) -> str | None:
    """Match Du's free-text look-target against a real tracked object at his location, by class
    keyword (reusing _MENTION_CLASSES' vocabulary) or a word from its name. Deterministic: among
    multiple candidates of the same class, the one with the most observations wins (favor the thing
    he already knows something about over a fresh unexplored twin), then object_id for a stable tie-
    break. '' target or no match -> None."""
    t = (target_text or "").lower().strip()
    if not t:
        return None
    objs = _load()
    candidates = [o for o in objs.values() if o.location == location]
    if not candidates:
        return None
    # class match first (the vocabulary already used for spawn_from_mention)
    cls_hit = None
    for keys, cls in _MENTION_CLASSES:
        if any(k in t for k in keys):
            cls_hit = cls
            break
    if cls_hit is not None:
        # a class was named ("stone", "shell", ...) — only objects of THAT class are candidates. A
        # generic adjective overlap ("small") against some unrelated object's name must never override
        # an explicit class the text actually named (the fix for a real false-positive found live: "a
        # small dark stone" matched "a small cone-shaped SHELL" on the word "small" alone).
        scored = [o for o in candidates if o.object_class == cls_hit]
    else:
        # no class keyword at all — fall back to a real word of the object's own name (still requires
        # a distinguishing word, not just any 4+ letter overlap; short common adjectives are excluded).
        _GENERIC = {"small", "large", "long", "short", "with", "that", "this", "dark", "pale",
                   "worn", "wide", "thin", "flat", "hard", "soft"}
        scored = [o for o in candidates
                 if any(w in set((o.name or "").lower().split())
                        for w in t.split() if len(w) > 3 and w not in _GENERIC)]
    if not scored:
        return None
    # THE GARDEN (2026-08-22): a class may hold many named things (trowel, barrel, tin are all garden_item) -
    # a word of the object's own name decides before observation count does.
    import re as _re
    _words = {w for w in _re.findall(r"[a-z]+", t) if len(w) > 2 and w not in ("the", "and", "for", "his", "its")}
    scored.sort(key=lambda o: (-len(_words & set(_re.findall(r"[a-z]+", (o.name or "").lower()))), -len(o.observations), o.object_id))
    return scored[0].object_id


_QUALITY_FIELDS = ["colour", "shape", "bark_presence", "grain_visibility", "surface_damage",
                   "overall_condition", "quartz_veining", "iridescence", "frosting", "borer_hole",
                   "fungal_brackets", "borer_galleries", "wear_polish", "holdfast_intact",
                   "barb_integrity"]

# 2026-08-18 (polish pass): the original driftwood-only version of this function had hand-written,
# natural prefixes per field ("the wood {v}", "its bark {v}", "the surface shows {v}") — generalizing
# it across every class in the audit collapsed that to one generic "the {field} {value}" template,
# which reads badly wherever field and value don't compose as a clean predicate ("the shape
# trunk_section" — no article, raw enum). Two fixes: the "driftwood core" fields (present for every
# class) get their natural prefix back; the "class-extra" fields (quartz_veining, iridescence, ...)
# were always written in observation.py as complete standalone clauses ("no play of colour", "barbs
# split and ragged") — they read best bare, no prefix needed at all.
_QUALITY_PREFIX = {
    "colour": "the wood {v}", "shape": "its shape a {v}", "bark_presence": "its bark {v}",
    "grain_visibility": "the grain {v}", "surface_damage": "the surface shows {v}",
    "overall_condition": "it looks {v}",
}

_LAST_LOOKED_F = _DATA / "world_substrate_last_looked.json"
_LAST_LOOKED_WINDOW_S = 1800.0   # a hypothesis only attaches to something looked at in the last ~30 min


def _stamp_last_looked(object_id: str) -> None:
    """The one thing Du most recently looked at closely enough to generate a real observation —
    read by record_du_inference's live latch (nodes/inner_monologue_node.py) so a hypothesis he
    voices shortly after looking has something concrete to attach to."""
    path = profile.guard_path(_LAST_LOOKED_F)   # J-0610; raises before any I/O if non-live (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"object_id": object_id, "ts": time.time()}), encoding="utf-8")
    except Exception:
        pass


def last_looked_object(max_age_s: float = _LAST_LOOKED_WINDOW_S) -> str | None:
    """The most recently looked-at object, if within max_age_s. None if nothing recent enough."""
    try:
        d = json.loads(_LAST_LOOKED_F.read_text(encoding="utf-8"))
        if time.time() - float(d.get("ts", 0)) <= max_age_s:
            return d.get("object_id")
    except Exception:
        pass
    return None


# ── J-2376 (object_epistemic_loop Phase 3, D-0464 ALLOWED by travis 2026-10-17) ───────────────────────
# Short prose for the REAL keys of each non-look action (core/observation.py), read off the observation
# dict only. The values are observation.py's own qualitative strings; nothing here reads causal_state.
_TEST_ACTIONS = ("pick_up", "inspect_end", "scrape", "smell", "float_test")
_WEIGHT_PHRASE = {"light": "light for its size", "moderate": "of middling weight", "heavy": "heavy for its size"}
_SCENT_PHRASE = {"marine": "salt and weed and old sea", "faint_salt": "a faint ghost of salt",
                 "none_notable": "nothing much at all", "decayed": "damp rot, soft and mushroomy",
                 "resinous": "a clean edge of resin"}
_TEST_EXTRAS = {"pick_up": ("hardness", "hollowness", "porosity", "brittleness", "rot_softness", "oil_sheen",
                            "grain_size"),
                "inspect_end": ("chambering", "porosity", "grain_size"),
                "scrape": ("rot_softness", "grain_size")}


def _test_bits(action: str, o: dict) -> list[str]:
    def _v(k):
        d = o.get(k) or {}
        v = str(d.get("value", "")).replace("_", " ")
        return v if v and v.lower() not in ("unknown", "undetermined") else ""

    bits: list[str] = []
    if action == "pick_up":
        if not _v("relative_weight"):
            return []   # a heft that cannot say how heavy it is says nothing (no density in its Layer 2)
        if _v("relative_weight"):
            bits.append(_WEIGHT_PHRASE.get(_v("relative_weight"), _v("relative_weight")))
        if _v("surface_texture"):
            bits.append(_v("surface_texture") + " to the touch")
        if _v("moisture_impression"):
            bits.append(_v("moisture_impression"))
        if _v("structural_flexibility"):
            bits.append(_v("structural_flexibility"))
    elif action == "inspect_end":
        if _v("cross_sectional_geometry"):
            bits.append("the section " + _v("cross_sectional_geometry"))
        if _v("annual_ring_visibility"):
            bits.append(_v("annual_ring_visibility"))
        if _v("break_pattern"):
            bits.append("the edges " + _v("break_pattern"))
    elif action == "scrape":
        if _v("internal_grain_color"):
            bits.append("underneath it comes up " + _v("internal_grain_color"))
        if _v("hardness_impression"):
            h = _v("hardness_impression")
            bits.append(h if " " in h else h + " under the edge")
        if _v("resin_presence"):
            bits.append("resin in the scrapings" if _v("resin_presence") == "present" else "no resin")
    elif action == "smell":
        sc = str((o.get("scent") or {}).get("value", "")).lower()
        if sc and sc not in ("unknown", "undetermined"):
            bits.append(_SCENT_PHRASE.get(sc, sc.replace("_", " ")))
    elif action == "float_test":
        fs = _v("floats_or_sinks")
        if fs == "floats":
            bits.append("it floats")
            if _v("buoyancy"):
                bits.append("riding high" if _v("buoyancy") == "high" else "sitting low in the water")
            if _v("water_absorption_rate") == "quick":
                bits.append("darkening fast where the water takes it")
        elif fs == "sinks":
            bits.append("it sinks")
    for k in _TEST_EXTRAS.get(action, ()):
        if _v(k) and len(bits) < 4:
            bits.append(_v(k))
    return bits[:4]


def _test_state(object_id: str) -> tuple[dict, str]:
    """(generative state, object_class) for a non-look test. Non-wood classes: Layer 2 only — no causal
    key at all. Wood classes: get_generative_state()'s two form keys (2026-08-14, structure /
    wood_type), since the wood anatomy vocabulary is generated from them — Layer-2 facts since J-2388
    (read from physical_state only since J-2411; no Layer-1 fallback)."""
    obj = get_object(object_id)
    if not obj:
        return {}, ""
    from core import observation as _obs
    if obj.object_class in _obs.WOOD_CLASSES:
        return get_generative_state(object_id), obj.object_class
    return dict(obj.physical_state), obj.object_class


def describe_and_observe(object_id: str, action: str = "look") -> str:
    """Generic version of what used to be driftwood_17's own hardcoded branch (sensorium.py, until
    2026-08-18): pull this object's generative state, run it through observation.py for ANY class
    (the function was always class-generic — only its one caller wasn't), record what's genuinely
    revealed as a real Layer-3 observation, and return a short 'looking closer' clause. '' if nothing
    to say (unknown object, or every property came back unknown/undetermined for this action)."""
    try:
        from core import observation as _obs
        if action in _TEST_ACTIONS:
            # J-2376: the non-look tests (only reached by sensorium's generic test helper, itself behind
            # NASCENCE_GENERIC_OBJECT_TESTS). Class-aware keys, Layer-2-only state for non-wood classes,
            # prose for this action's own keys. Recording unchanged in shape: the revealed features as
            # one Layer-3 observation under this action. '' when the object's Layer 2 answers nothing.
            gen, cls = _test_state(object_id)
            if not gen:
                return ""
            o = _obs.generate_observation(gen, action, object_class=cls)
            feats = {k: str((v or {}).get("value", "")).replace("_", " ") for k, v in o.items()
                    if str((v or {}).get("value", "")).lower() not in ("", "unknown", "undetermined")}
            bits = _test_bits(action, o)
            if not bits:
                return ""
            if feats:
                record_du_observation(object_id, action, feats)
            _stamp_last_looked(object_id)
            txt = "; ".join(bits)
            return " " + txt[0].upper() + txt[1:] + "."
        gen = get_generative_state(object_id)
        if not gen:
            return ""
        o = _obs.generate_observation(gen, action)

        def _v(k):
            d = o.get(k) or {}
            v = str(d.get("value", "")).replace("_", " ")
            return v if v and v.lower() not in ("unknown", "undetermined") else ""

        bits = [_QUALITY_PREFIX.get(f, "{v}").format(v=_v(f)) for f in _QUALITY_FIELDS if _v(f)][:3]
        # root-cause clean here, not just at each display site (buses.object_ledger_line, moved from
        # couriers 2026-08-22, reads these stored features back later, verbatim) — no consumer
        # should ever see a raw enum again.
        feats = {k: str((v or {}).get("value", "")).replace("_", " ") for k, v in o.items()
                if str((v or {}).get("value", "")).lower() not in ("", "unknown", "undetermined")}
        if feats:
            record_du_observation(object_id, action, feats)
        _stamp_last_looked(object_id)
        return " Looking closer: " + "; ".join(bits) + "." if bits else ""
    except profile.NonLiveWriteError:
        # J-0751: let D-0179's hard-raise (guard_path(), F-1024) escape this function's own
        # broad except -- describe_and_observe() is the real sink _stamp_last_looked() sits
        # behind on the "look" dispatch chain (dispatch._look -> sensorium.look() -> the per-
        # place _*_look() helpers -> here), the same shape J-0726 already fixed for the deed chain.
        raise
    except Exception:
        return ""


def record_du_observation(object_id: str, action: str,
                          features: dict[str, str]) -> ObservationRecord | None:
    """Record an observation Du made of an object. Append-only. Never overwrites."""
    obj = get_object(object_id)
    if not obj:
        return None
    record = ObservationRecord(
        observation_id=f"obs_{object_id}_{int(time.time())}",
        timestamp=time.time(),
        action=action,
        features=features,
    )
    obj.record_observation(record)
    _save()
    return record


def record_du_inference(object_id: str, hypothesis: str, confidence: float,
                        supporting_observations: list[str],
                        supporting_knowledge: list[str],
                        intervention_test: list | None = None) -> InferenceRecord | None:
    """Record an inference Du formed about an object. Carries provenance chain.

    J-2359 (object_epistemic_loop Phase 1 step 4): dedup + supersession, collision-safe ids.
      - If his latest still-active inference on this object says nearly the same thing (word Jaccard
        >= _INFER_DEDUP_JACCARD), that record is REFRESHED (timestamp, confidence, provenance merged)
        instead of a near-copy being appended.
      - Otherwise the new record is appended and the prior active one gets superseded_by = new id
        (the field existed since 2026-08-11; nothing ever set it).
      - Ids carry a per-object counter suffix, so two inferences in the same second never collide."""
    obj = get_object(object_id)
    if not obj:
        return None
    now = time.time()
    prev = None
    for d in reversed(obj.inferences):
        if not d.get("superseded_by"):
            prev = d
            break
    if prev is not None and _word_jaccard(prev.get("hypothesis", ""), hypothesis) >= _INFER_DEDUP_JACCARD:
        prev["timestamp"] = now
        prev["confidence"] = confidence
        merged = list(prev.get("supporting_observations") or [])
        merged += [o for o in supporting_observations if o not in merged]
        prev["supporting_observations"] = merged
        mk = list(prev.get("supporting_knowledge") or [])
        mk += [k for k in supporting_knowledge if k not in mk]
        prev["supporting_knowledge"] = mk
        if intervention_test is not None:   # J-2524: only when the gated writer derived one
            prev["intervention_test"] = intervention_test
        _save()
        return InferenceRecord.from_dict(prev)
    existing = {d.get("inference_id") for d in obj.inferences}
    n = len(obj.inferences)
    iid = f"inf_{object_id}_{int(now)}_{n}"
    while iid in existing:
        n += 1
        iid = f"inf_{object_id}_{int(now)}_{n}"
    record = InferenceRecord(
        inference_id=iid,
        timestamp=now,
        hypothesis=hypothesis,
        confidence=confidence,
        supporting_observations=supporting_observations,
        supporting_knowledge=supporting_knowledge,
        intervention_test=intervention_test,
    )
    if prev is not None:
        prev["superseded_by"] = iid
    obj.record_inference(record)
    _save()
    return record


def inferences_with_test() -> list[dict]:
    """J-3244 (D-0632): every stored inference whose intervention_test is a non-empty list, one dict each
    ({object_id, object_class, name, location} + the inference's own fields), newest first. READ-ONLY and
    side-effect free: never seeds, never saves (so it is safe in a non-live process); uses the in-memory registry
    when loaded, else reads _SUBSTRATE_F directly; [] on any failure or when the file is absent."""
    try:
        if _cache:
            objs = {k: v.to_dict() for k, v in _cache.items()}
        elif _SUBSTRATE_F.exists():
            objs = json.loads(_SUBSTRATE_F.read_text(encoding="utf-8"))
        else:
            return []
        out: list[dict] = []
        for oid, o in objs.items():
            for d in (o.get("inferences") or []):
                if isinstance(d.get("intervention_test"), list) and d["intervention_test"]:
                    out.append({"object_id": oid, "object_class": o.get("object_class", ""), "name": o.get("name", ""),
                                "location": o.get("location", ""), **d})
        out.sort(key=lambda r: float(r.get("timestamp", 0) or 0), reverse=True)
        return out
    except Exception:
        return []


_INFER_DEDUP_JACCARD = 0.75


def _word_jaccard(a: str, b: str) -> float:
    import re as _re
    wa = set(_re.findall(r"[a-z']+", (a or "").lower()))
    wb = set(_re.findall(r"[a-z']+", (b or "").lower()))
    if not wa and not wb:
        return 1.0
    return len(wa & wb) / len(wa | wb) if (wa | wb) else 0.0


def status() -> dict:
    """System status for the pulse."""
    objects = _load()
    return {
        "substrate_objects": len(objects),
        "total_observations": sum(len(o.observations) for o in objects.values()),
        "total_inferences": sum(len(o.inferences) for o in objects.values()),
        "total_causal_events": sum(len(o.causal_history) for o in objects.values()),
        "locations": list(set(o.location for o in objects.values())),
    }


# ── Seed Data ────────────────────────────────────────────────────────────────

def _seed_default_objects() -> dict[str, SubstrateObject]:
    """
    Seed the substrate with the founding driftwood object.
    Its biography: tree fell → entered river → transported to sea → 3 storms → beached.
    """
    driftwood = SubstrateObject(
        object_id="driftwood_17",
        # 2026-08-14 reconciled with the LIVED object (world_objects.py / sensorium): Du has hauled
        # this with his shoulder for weeks — it is a heavy log, not a 71cm branch. Species and
        # weathering ground truth unchanged (that is the inference experiment).
        name="sea-bleached driftwood log",
        location="shore",
        object_class="driftwood",
        # Layer 1: Hidden causal world state — Du NEVER sees this directly
        causal_state={
            "species_ground_truth": "silver_beech",
            "wood_type": "hardwood",
            "original_structure": "trunk_section",
            "original_diameter_cm": 24.0,
            "original_length_cm": 215.0,
            "tree_fall_timestamp": 1778150400.0,       # ~2026-03-15
            "river_entry_timestamp": 1778236800.0,      # ~2026-03-16
            "marine_entry_timestamp": 1782806400.0,     # ~2026-05-17
            "cumulative_marine_days": 86,
            "cumulative_freshwater_days": 52,
            "storm_events_experienced": 3,
            "transport_events": ["tree_fall", "river_transport", "marine_entry",
                                 "storm_01", "beach_stranding", "marine_reentry",
                                 "storm_02", "storm_03", "current_beach_position"],
            "likely_origin": "river",
        },
        # Layer 2: Physical state — generative properties that produce observable consequences
        physical_state={
            "density": 0.62,              # normalized: actual 620 kg/m³ for silver beech
            "moisture": 0.31,
            "bark_retention": 0.11,
            "surface_roughness": 0.74,
            "edge_rounding": 0.68,
            "fissuring": 0.28,
            "salt_accumulation": 0.42,
            "bleaching": 0.65,
            "diameter_cm": 23.2,          # slightly reduced from original by abrasion
            "length_cm": 208.0,           # slightly reduced
            "biological_colonization": 0.15,  # barnacle scars, minimal current colonization
            # J-2388: observable form as Layer-2 facts (mirror of causal original_structure / wood_type)
            "structure": "trunk_section",
            "wood_type": "hardwood",
        },
        # Causal biography (generative event sequence)
        causal_history=[
            {"event_type": "tree_fall", "timestamp": 1778150400.0,
             "description": "branch broke from silver beech in wind event",
             "state_deltas": {}},
            {"event_type": "river_transport", "timestamp": 1778236800.0,
             "description": "entered river, transported downstream over 52 days",
             "state_deltas": {"bark_retention": -0.25, "edge_rounding": 0.20, "moisture": 0.40}},
            {"event_type": "marine_entry", "timestamp": 1782806400.0,
             "description": "entered marine environment at river mouth",
             "state_deltas": {"salt_accumulation": 0.15, "bleaching": 0.10}},
            {"event_type": "storm_impact", "timestamp": 1784620800.0,
             "description": "first major storm — significant wave impact",
             "state_deltas": {"bark_retention": -0.12, "edge_rounding": 0.10, "fissuring": 0.08}},
            {"event_type": "solar_bleaching", "timestamp": 1785830400.0,
             "description": "stranded above tide line, extensive sun exposure",
             "state_deltas": {"bleaching": 0.20, "moisture": -0.15}},
            {"event_type": "storm_impact", "timestamp": 1786003200.0,
             "description": "second storm returned driftwood to water",
             "state_deltas": {"bark_retention": -0.06, "edge_rounding": 0.08, "salt_accumulation": 0.10}},
            {"event_type": "storm_impact", "timestamp": 1786262400.0,
             "description": "third storm deposited at current beach position",
             "state_deltas": {"bark_retention": -0.04, "edge_rounding": 0.05, "fissuring": 0.05}},
        ],
        observations=[],
        inferences=[],
    )

    birch = SubstrateObject(
        object_id="shore_birch_042",
        name="weathered pale branch",
        location="shore",
        object_class="driftwood",
        # Layer 1: Hidden causal world state — Du NEVER sees this directly
        causal_state={
            "species_ground_truth": "birch",
            "wood_type": "hardwood",
            "original_structure": "branch",
            "original_diameter_cm": 7.0,
            "original_length_cm": 70.0,
            "tree_fall_timestamp": 1782000000.0,
            "river_entry_timestamp": 1782500000.0,
            "marine_entry_timestamp": 1783472000.0,     # ~34 marine days ago
            "cumulative_marine_days": 34,
            "cumulative_freshwater_days": 11,
            "storm_events_experienced": 1,
            "transport_events": ["tree_fall", "river_transport", "marine_entry",
                                 "storm_01", "current_beach_position"],
            "likely_origin": "river",
        },
        # Layer 2: Physical state — calibrated so initial LOOK is very similar to driftwood_17
        physical_state={
            "density": 0.54,              # normalized: ~540 kg/m³ for birch
            "moisture": 0.28,
            "bark_retention": 0.14,       # patchy, close to driftwood_17 (0.11)
            "surface_roughness": 0.68,   # rough and ridged
            "edge_rounding": 0.62,       # rounded
            "fissuring": 0.22,           # minor cracks
            "salt_accumulation": 0.25,   # less salt than 86 days
            "bleaching": 0.62,           # sun-bleached
            "diameter_cm": 6.8,
            "length_cm": 68.0,
            "biological_colonization": 0.0, # no barnacles (only 34 days, 1 storm)
            "structure": "branch",        # J-2388: Layer-2 form facts (mirror of causal_state)
            "wood_type": "hardwood",
        },
        # Causal biography
        causal_history=[
            {"event_type": "tree_fall", "timestamp": 1782000000.0,
             "description": "birch branch fell into river tributary",
             "state_deltas": {}},
            {"event_type": "river_transport", "timestamp": 1782500000.0,
             "description": "rapid river transport downstream over 11 days",
             "state_deltas": {"bark_retention": -0.30, "edge_rounding": 0.15, "moisture": 0.35}},
            {"event_type": "marine_entry", "timestamp": 1783472000.0,
             "description": "entered sea at estuarine mouth",
             "state_deltas": {"salt_accumulation": 0.10, "bleaching": 0.15}},
            {"event_type": "storm_impact", "timestamp": 1786100000.0,
             "description": "single coastal storm deposited branch on upper shingle",
             "state_deltas": {"bark_retention": -0.06, "edge_rounding": 0.08, "fissuring": 0.05, "bleaching": 0.20}},
        ],
        observations=[],
        inferences=[],
    )

    return {"driftwood_17": driftwood, "shore_birch_042": birch}


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# SPAWN PIPELINE (2026-08-15 — the small-item-count fix: the substrate had TWO entities, ever)
# When the world MENTIONS a find (a storm wash-up, a gather in the wood, a kept curio), a substrate
# entity is born behind it: a hidden Layer-1 biography sampled from class priors, a coherent Layer-2
# derived from that biography, and a species-NEUTRAL display name (the name must never pre-answer
# the inference — the driftwood lesson). Deterministic (seeded RNG per spawn), no LLM, fail-open.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

import random as _random

_SPAWN_CAP = 300          # total entities (60 -> 120 -> 300 on 2026-08-22: garden ~25 + study 22 + larder 26 + wood 6, and the bank keeps minting volunteers)

# Class priors: hidden kinds (weighted), neutral name pools, Layer-2 base per kind.
# DENSITY = specific gravity (water=1.0): float_test sinks at >=1.0 — pumice, dry bird bone,
# cuttlebone and egg-cases genuinely FLOAT; stone, glass and most shell sink. The old [0,1]
# convention was driftwood-only (a world with no sinkers). Every kind is
# NZ-coastal-plausible; observable properties either reuse the renderer's existing vocabulary
# (density/moisture/rounding/bleaching/…) or have mappings added in observation.py the same day.
CLASS_PRIORS: dict[str, dict] = {
    "stone": {
        "kinds": [("greywacke", 0.55), ("sandstone", 0.15), ("quartz_veined_pebble", 0.12),
                  ("pumice", 0.10), ("argillite", 0.08)],
        "names": ["a smooth grey beach stone", "a flat water-worn stone", "a rounded pale pebble",
                  "a dark heavy little stone", "a light rough grey stone"],
        "base": {"greywacke": {"density": 2.70, "hardness": 0.75, "grain_size": 0.25, "quartz_veining": 0.30},
                 "sandstone": {"density": 2.30, "hardness": 0.35, "grain_size": 0.65, "quartz_veining": 0.05},
                 "quartz_veined_pebble": {"density": 2.65, "hardness": 0.85, "grain_size": 0.20, "quartz_veining": 0.90},
                 "pumice": {"density": 0.35, "hardness": 0.15, "grain_size": 0.55, "quartz_veining": 0.0,
                            "porosity": 0.90},
                 "argillite": {"density": 2.75, "hardness": 0.65, "grain_size": 0.10, "quartz_veining": 0.10}},
    },
    "shell": {
        "kinds": [("whelk", 0.30), ("tuatua", 0.25), ("limpet", 0.18), ("mussel", 0.15),
                  ("paua_fragment", 0.07), ("cuttlebone", 0.05)],
        "names": ["a worn spiral shell", "a pale fan-shaped shell", "a small cone-shaped shell",
                  "a dark hinged shell, one half only", "a fragment of shell with colour in its grain",
                  "a white chalky oval, light as paper"],
        "base": {"whelk": {"density": 2.00, "iridescence": 0.05, "chambering": 0.7, "brittleness": 0.35},
                 "tuatua": {"density": 2.00, "iridescence": 0.10, "chambering": 0.0, "brittleness": 0.45},
                 "limpet": {"density": 2.00, "iridescence": 0.05, "chambering": 0.0, "brittleness": 0.30},
                 "mussel": {"density": 1.90, "iridescence": 0.35, "chambering": 0.0, "brittleness": 0.50},
                 "paua_fragment": {"density": 2.10, "iridescence": 0.95, "chambering": 0.0, "brittleness": 0.40},
                 "cuttlebone": {"density": 0.15, "iridescence": 0.0, "chambering": 0.95, "brittleness": 0.80}},
    },
    "bone": {
        "kinds": [("gull_wing_bone", 0.4), ("gannet_wing_bone", 0.25), ("fish_vertebra", 0.25),
                  ("small_mammal_bone", 0.10)],
        "names": ["a pale light bone", "a small knuckle of bone, sea-cleaned",
                  "a slender hollow-looking bone", "a bleached bone the size of a finger"],
        "base": {"gull_wing_bone": {"density": 0.70, "porosity": 0.75, "hollowness": 0.9},
                 "gannet_wing_bone": {"density": 0.75, "porosity": 0.70, "hollowness": 0.9},
                 "fish_vertebra": {"density": 1.30, "porosity": 0.55, "hollowness": 0.2},
                 "small_mammal_bone": {"density": 1.80, "porosity": 0.35, "hollowness": 0.3}},
    },
    "egg_case": {
        "kinds": [("whelk_egg_case", 0.7), ("skate_purse", 0.3)],
        "names": ["a dry papery honeycomb thing, light as air", "a small dark leathery pouch with horns"],
        "base": {"whelk_egg_case": {"density": 0.30, "chambering": 0.95, "brittleness": 0.85},
                 "skate_purse": {"density": 0.50, "chambering": 0.10, "brittleness": 0.40}},
    },
    "bottle": {
        "kinds": [("page_bottle", 0.7), ("empty_bottle", 0.3)],
        "names": ["a corked bottle, salt-dulled, with a folded paper inside it", "a green bottle, corked, empty but for sand"],
        "base": {"page_bottle": {"density": 2.50, "hardness": 0.80, "frosting": 0.3, "chambering": 0.0},
                 "empty_bottle": {"density": 2.50, "hardness": 0.80, "frosting": 0.4, "chambering": 0.0}},
    },
    "fishing_float": {
        "kinds": [("glass_float", 0.8), ("cork_float", 0.2)],
        "names": ["a glass fishing-float, green and whole", "a cork float, black with tar, a hole through it"],
        "base": {"glass_float": {"density": 0.30, "hardness": 0.75, "frosting": 0.4},
                 "cork_float": {"density": 0.25, "hardness": 0.20, "frosting": 0.0}},
    },
    "sea_glass": {
        "kinds": [("green_glass", 0.5), ("brown_glass", 0.3), ("white_glass", 0.15), ("blue_glass", 0.05)],
        "names": ["a frosted pebble of glass", "a sea-milled piece of glass, cloudy and cool"],
        "base": {"green_glass": {"density": 2.50, "hardness": 0.80, "frosting": 0.5},
                 "brown_glass": {"density": 2.50, "hardness": 0.80, "frosting": 0.5},
                 "white_glass": {"density": 2.50, "hardness": 0.80, "frosting": 0.5},
                 "blue_glass": {"density": 2.50, "hardness": 0.80, "frosting": 0.5}},
    },
    "kelp": {
        "kinds": [("bull_kelp", 0.6), ("bladder_wrack", 0.4)],
        "names": ["a long leathery strap of weed", "a tangle of dried weed with little floats in it"],
        "base": {"bull_kelp": {"density": 0.90, "moisture": 0.6, "holdfast_intact": 0.5},
                 "bladder_wrack": {"density": 0.70, "moisture": 0.5, "holdfast_intact": 0.3}},
    },
    "feather": {
        "kinds": [("gull_primary", 0.5), ("songbird_body_feather", 0.3), ("shag_feather", 0.2)],
        "names": ["a long grey-white feather", "a small soft breast-feather", "a dark stiff feather"],
        "base": {"gull_primary": {"density": 0.10, "barb_integrity": 0.6, "oil_sheen": 0.4},
                 "songbird_body_feather": {"density": 0.08, "barb_integrity": 0.5, "oil_sheen": 0.2},
                 "shag_feather": {"density": 0.10, "barb_integrity": 0.55, "oil_sheen": 0.3}},
    },
    "deadfall_wood": {
        "kinds": [("beech_limb", 0.45), ("manuka_branch", 0.30), ("rotten_limb", 0.25)],
        "names": ["a dropped grey limb, half in the leaf-mould", "a hard dark crooked branch",
                  "a soft crumbling length of old wood"],
        "base": {"beech_limb": {"density": 0.60, "rot_softness": 0.25, "fungal_brackets": 0.15,
                                "borer_galleries": 0.30, "bark_retention": 0.55, "moisture": 0.45},
                 "manuka_branch": {"density": 0.75, "rot_softness": 0.10, "fungal_brackets": 0.05,
                                   "borer_galleries": 0.15, "bark_retention": 0.70, "moisture": 0.35},
                 "rotten_limb": {"density": 0.30, "rot_softness": 0.85, "fungal_brackets": 0.60,
                                 "borer_galleries": 0.70, "bark_retention": 0.20, "moisture": 0.65}},
    },
    # 2026-08-18: was hand-authored ONLY (driftwood_17 + shore_birch_042, predating this class system —
    # see the schema-gap fix in docs/completed/ for that pair). Every OTHER piece of shore driftwood —
    # keepsakes backfill, any future spawn_from_mention("driftwood", "shore") — needs a real class to
    # mint through. Marine env (unlike deadfall_wood, which is ground/leaf-mould): salt, bleaching,
    # rounding, not rot and fungus. kind_ground_truth stays Layer-1 hidden, same law as every class here.
    "driftwood": {
        "kinds": [("silver_beech", 0.35), ("rimu", 0.25), ("kanuka", 0.20), ("macrocarpa", 0.20)],
        "names": ["a sea-smoothed length of driftwood", "a bleached grey branch off the tideline",
                  "a heavy weathered piece of driftwood", "a pale, salt-worn length of wood"],
        "base": {"silver_beech": {"density": 0.68, "hardness": 0.55, "bark_retention": 0.10},
                 "rimu":         {"density": 0.52, "hardness": 0.40, "bark_retention": 0.05},
                 "kanuka":       {"density": 0.90, "hardness": 0.80, "bark_retention": 0.15},
                 "macrocarpa":   {"density": 0.44, "hardness": 0.30, "bark_retention": 0.05}},
        "structure": ["trunk section", "large limb", "root mass", "split branch"],
        "wood_type": {"silver_beech": "hardwood", "rimu": "softwood", "kanuka": "hardwood",
                      "macrocarpa": "softwood"},
    },
}

# What the sea/ground does to a thing over time — class-generic weathering curves applied per
# history-day with per-spawn noise. Marine tumbling rounds, polishes and frosts; sun bleaches;
# ground-contact rots, softens and invites the borers.
_WEATHER_CURVES = {
    "marine": {"edge_rounding": 0.006, "surface_roughness": -0.003, "bleaching": 0.004,
               "salt_accumulation": 0.005, "wear_polish": 0.005, "frosting": 0.004,
               "brittleness": 0.002, "oil_sheen": -0.006, "barb_integrity": -0.004},
    "ground": {"rot_softness": 0.002, "fungal_brackets": 0.0015, "borer_galleries": 0.002,
               "bark_retention": -0.002, "moisture": 0.001},
}

_MENTION_CLASSES = [                        # keyword scan, first match per class wins
    # THE GARDEN (2026-08-22): plants and tools are tracked objects too — the garden's words find them
    (("rosemary", "thyme", "mint", "parsley", "chive", "radish", "lettuce", "silverbeet", "peas", "bean",
      "tomato", "potato", "garlic", "strawberr", "sunflower", "calendula", "marigold", "nasturtium", "popp",
      "chickweed", "dandelion", "oxalis", "seedling", "plant"), "plant"),
    (("trowel", "hand fork", "watering can", "barrel", "seed tin", "twine", "stake", "terracotta", "bucket",
      "netting", "bird bath", "shears", "compost"), "garden_item"),
    (("lamp", "oil can", "oil tin", "ash bucket", "hearth brush", "poker", "pail", "kettle", "teapot", "clock", "coat", "boots",
      "candle", "matches", "cloth", "blanket", "almanac"), "study_item"),
    (("kelp", "weed", "wrack"), "kelp"),
    (("cuttlebone", "mussel-shell", "mussel", "shell", "paua", "tuatua", "limpet"), "shell"),
    (("egg-case", "egg case", "purse"), "egg_case"),
    (("gannet", "bone", "skull", "crab"), "bone"),
    (("bottle",), "bottle"),
    (("float",), "fishing_float"),
    (("pumice",), "stone"),
    (("paua",), "shell"),
    (("glass",), "sea_glass"),
    (("feather",), "feather"),
    (("stone", "pebble",), "stone"),
    (("deadfall", "limb", "branch", "bough"), "deadfall_wood"),
]


def spawn_object(object_class: str, location: str, seed: str = "",
                 days_hint: int | None = None, as_of: float | None = None) -> SubstrateObject | None:
    """Mint one entity: hidden kind from priors → Layer-1 biography → coherently derived Layer-2.
    Deterministic per (class, seed). Species-neutral name. Returns None at cap or unknown class.
    `as_of` (2026-08-18, keepsakes backfill): backdate the whole biography to end at this timestamp
    instead of now — so a retroactively-authored object's origin/storms genuinely predate the moment
    it was kept, rather than reading as born today. Defaults to now, unchanged for every other caller."""
    try:
        priors = CLASS_PRIORS.get(object_class)
        if not priors:
            return None
        objects = _load()
        if len(objects) >= _SPAWN_CAP:
            logger.info("[substrate] spawn skipped — cap %d reached", _SPAWN_CAP)
            return None
        rng = _random.Random(f"{object_class}|{seed}")
        kinds, weights = zip(*priors["kinds"])
        kind = rng.choices(kinds, weights=weights, k=1)[0]
        days = days_hint if days_hint is not None else rng.randint(5, 220)
        env = "ground" if object_class == "deadfall_wood" else "marine"
        now = as_of if as_of is not None else time.time()
        phys = {"moisture": 0.3, "edge_rounding": 0.15, "surface_roughness": 0.6,
                "bleaching": 0.15, "salt_accumulation": 0.1}
        phys.update(priors["base"][kind])
        for prop, rate in _WEATHER_CURVES[env].items():
            if prop in phys or rate > 0:
                cur = phys.get(prop, 0.15 if rate > 0 else 0.5)
                phys[prop] = max(0.0, min(1.0, cur + rate * days * rng.uniform(0.7, 1.3)))
        oid = f"{location}_{object_class}_{rng.randrange(16**6):06x}"
        events = [{"event_type": "origin", "timestamp": now - days * 86400,
                   "description": f"entered the {'sea' if env == 'marine' else 'leaf-mould'} "
                                  f"~{days} days ago", "state_deltas": {}}]
        storms = rng.randint(0, max(1, days // 45)) if env == "marine" else 0
        for _i in range(storms):
            events.append({"event_type": "storm_impact", "timestamp": now - rng.uniform(0, days) * 86400,
                           "description": "worked and thrown by a storm", "state_deltas": {}})
        causal_state = {"kind_ground_truth": kind, "environment": env,
                        "cumulative_days": days, "storm_events_experienced": storms,
                        "predation_marks": bool(object_class == "shell" and rng.random() < 0.25)}
        # get_generative_state() reads original_structure/wood_type for the inspect_end/scrape
        # observation vocabulary — only driftwood declares them (its "structure"/"wood_type" priors).
        if "structure" in priors:
            causal_state["original_structure"] = rng.choice(priors["structure"])
        if "wood_type" in priors:
            causal_state["wood_type"] = priors["wood_type"].get(kind, "unknown")
        obj = SubstrateObject(
            object_id=oid, name=rng.choice(priors["names"]), location=location,
            object_class=object_class,
            causal_state=causal_state,
            physical_state={k: round(v, 3) for k, v in phys.items()},
            causal_history=sorted(events, key=lambda e: e["timestamp"]),
        )
        if obj.causal_state["predation_marks"]:
            obj.physical_state["borer_hole"] = 1.0     # the naticid drill-hole — a predation story in one mark
        # J-2388 (F-3087): the observable form is a Layer-2 fact too — mirror the two form keys into
        # physical_state so get_generative_state() reads them without touching Layer 1. Added after the
        # rng draws above, so every other spawned value is unchanged.
        for l2, l1 in _FORM_KEYS:
            if l1 in causal_state:
                obj.physical_state[l2] = causal_state[l1]
        objects[oid] = obj
        _save()
        # POSITION AUTHORITY (2026-08-17): a place is born with the object — world_objects.py holds
        # position + movement history for ALL objects (the "extends" contract, finally honored).
        try:
            from core import world_objects as _wo
            _wo.ensure_record(oid, location, object_class, obj.name)
        except profile.NonLiveWriteError:
            # J-0726: spawn_object()'s own _save() above is unwrapped and already raises — but this
            # world_objects position-registration write attempt was still silently swallowed here
            # first (mirrors J-0727's whittle() fix; world_objects.ensure_record() re-raises this
            # itself too, this job's own fix).
            raise
        except Exception:
            pass
        logger.info("[substrate] spawned %s (%s at %s, hidden kind=%s, %dd)",
                    oid, obj.name, location, kind, days)
        return obj
    except profile.NonLiveWriteError:
        # J-0726: spawn_object() is one of world_substrate.py's own shared functions, called from
        # deed functions across MANY of the other 10 modules (wood_life's acorn-gather, study_life.
        # draw_sketch, shore_life.enter_cave, etc via spawn_from_mention()) — without this, even this
        # function's OWN _save() above would be swallowed by this outer catch-all.
        raise
    except Exception as exc:
        logger.debug("[substrate] spawn failed (non-fatal): %s", exc)
        return None


def spawn_from_mention(mention: str, location: str) -> list[str]:
    """The discovery channel made epistemically real: when the world names a find in prose, mint the
    entity behind it (up to 2 per mention). Deterministic per mention+day. Fail-open; returns ids.
    Driftwood class is NOT minted here — the two hand-authored logs own it."""
    out: list[str] = []
    try:
        low = (mention or "").lower()
        if not low:
            return out
        seed_base = f"{low[:60]}|{int(time.time() // 86400)}"
        seen: set[str] = set()
        for keys, cls in _MENTION_CLASSES:
            if len(out) >= 2 or cls in seen:
                continue
            if any(k in low for k in keys):
                seen.add(cls)
                obj = spawn_object(cls, location, seed=seed_base + cls)
                if obj:
                    out.append(obj.object_id)
    except profile.NonLiveWriteError:
        # J-0726: spawn_from_mention() is called from deed functions across most of the other 10
        # modules (wood_life's acorn-gather, study_life.draw_sketch, shore_life.enter_cave/
        # gather_shellfish) as a "a found thing enters the world" side effect — let D-0179's
        # hard-raise (guard_path(), F-1024, via spawn_object() above, this job's own fix) reach the
        # caller instead of being swallowed here.
        raise
    except Exception as exc:
        logger.debug("[substrate] spawn_from_mention failed (non-fatal): %s", exc)
    return out
