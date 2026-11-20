from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("nascence.observation")

_DATA = Path(__file__).parent.parent / "data"


class OutcomeStatus(str, Enum):
    OBSERVED = "OBSERVED"
    UNKNOWN = "UNKNOWN"
    UNDETERMINED = "UNDETERMINED"


@dataclass
class ObservationValue:
    value: str
    confidence: str
    provenance: str = OutcomeStatus.OBSERVED.value

    def to_dict(self) -> dict[str, str]:
        return {
            "value": self.value,
            "confidence": self.confidence,
            "provenance": self.provenance,
        }


def _structure_kind(value: Any) -> str:
    """The head word of a structure value, for the branch/root form tests (J-2405, D-0480 A_strict).

    The driftwood spawn priors use compound values ('split branch', 'root mass', 'trunk section',
    'large limb'); the form tests used to compare the whole value to 'branch' / 'root', so no spawned
    driftwood ever matched (F-3092). A value whose tokens (underscores read as spaces) include 'root'
    is a root, one including 'branch' is a branch; anything else is returned unchanged, so 'large limb'
    and 'trunk section' read exactly as before. Used only by the comparisons, never by the look shape.
    """
    toks = str(value or "").lower().replace("_", " ").split()
    if "root" in toks:
        return "root"
    if "branch" in toks:
        return "branch"
    return str(value)


def _quantitative_to_qualitative(prop_name: str, value: Any) -> str:
    """Converts a numeric or explicit physical state value into a qualitative description."""
    if value is None:
        return OutcomeStatus.UNDETERMINED.value

    try:
        if prop_name == "density":
            val = float(value)
            if val < 0.40: return "light"
            if val < 0.65: return "moderate"
            return "heavy"
            
        elif prop_name == "moisture":
            val = float(value)
            if val < 0.15: return "dry"
            if val < 0.4: return "damp"
            return "wet"
            
        elif prop_name == "bark_retention":
            val = float(value)
            if val < 0.1: return "mostly absent"
            if val < 0.5: return "patchy"
            if val < 0.9: return "mostly present"
            return "fully intact"
            
        elif prop_name == "surface_roughness":
            val = float(value)
            if val < 0.3: return "smooth"
            if val < 0.7: return "moderately rough"
            return "rough and ridged"
            
        elif prop_name == "edge_rounding":
            val = float(value)
            if val < 0.3: return "sharp or splintered"
            if val < 0.7: return "somewhat rounded"
            return "heavily worn and rounded"
            
        elif prop_name == "fissuring":
            val = float(value)
            if val < 0.2: return "clean surface"
            if val < 0.6: return "minor cracks"
            return "deeply fissured"
            
        elif prop_name == "salt_accumulation":
            val = float(value)
            if val < 0.2: return "none visible"
            if val < 0.6: return "faint white dusting"
            return "heavy salt encrustation"
            
        elif prop_name == "bleaching":
            val = float(value)
            if val < 0.3: return "natural color"
            if val < 0.7: return "faded"
            return "sun-bleached white/grey"
            
        elif prop_name == "diameter_cm":
            val = float(value)
            if val < 2.0: return "very thin"
            if val < 10.0: return "medium thickness"
            return "thick"
            
        elif prop_name == "length_cm":
            val = float(value)
            if val < 10.0: return "very short"
            if val < 50.0: return "medium length"
            return "long"
            
        elif prop_name == "structure":
            return str(value)

        elif prop_name == "wood_type":
            return str(value)

        # ── new-class vocabulary (2026-08-15, the spawn-pipeline expansion) ──
        elif prop_name == "hardness":
            val = float(value)
            if val < 0.3: return "soft — a thumbnail marks it"
            if val < 0.7: return "firm"
            return "hard — nothing short of another stone marks it"

        elif prop_name == "grain_size":
            val = float(value)
            if val < 0.3: return "fine, almost smooth grain"
            if val < 0.7: return "visible grain"
            return "coarse, sandy grain"

        elif prop_name == "quartz_veining":
            val = float(value)
            if val < 0.2: return "no veining"
            if val < 0.6: return "a thin pale seam or two"
            return "bold white veins right through it"

        elif prop_name == "wear_polish":
            val = float(value)
            if val < 0.3: return "unpolished"
            if val < 0.7: return "smoothed by handling or water"
            return "worn to a soft shine"

        elif prop_name == "frosting":
            val = float(value)
            if val < 0.3: return "still glassy and clear"
            if val < 0.7: return "going cloudy"
            return "frosted all over, the shine quite gone"

        elif prop_name == "iridescence":
            val = float(value)
            if val < 0.2: return "no play of colour"
            if val < 0.6: return "a faint shift of colour at an angle"
            return "colour moving in it like oil on water"

        elif prop_name == "chambering":
            val = float(value)
            if val < 0.2: return "solid through"
            if val < 0.6: return "partly divided inside"
            return "chambered right through, like a honeycomb"

        elif prop_name == "brittleness":
            val = float(value)
            if val < 0.3: return "tough"
            if val < 0.7: return "a little fragile"
            return "so brittle it might crumble in the hand"

        elif prop_name == "porosity":
            val = float(value)
            if val < 0.3: return "dense and close"
            if val < 0.7: return "finely pitted"
            return "spongy with tiny holes"

        elif prop_name == "hollowness":
            val = float(value)
            if val < 0.3: return "solid"
            if val < 0.7: return "part-hollow"
            return "hollow — far lighter than it looks"

        elif prop_name == "borer_hole":
            return "a single neat round hole drilled clean through" if float(value) > 0.5 else "no holes"

        elif prop_name == "rot_softness":
            val = float(value)
            if val < 0.3: return "sound wood"
            if val < 0.7: return "soft in places"
            return "punky right through — a thumb sinks in"

        elif prop_name == "fungal_brackets":
            val = float(value)
            if val < 0.2: return "no growth on it"
            if val < 0.6: return "a few small pale brackets"
            return "shelved with fungus along one side"

        elif prop_name == "borer_galleries":
            val = float(value)
            if val < 0.2: return "clean under the bark"
            if val < 0.6: return "a few wandering grooves under the bark"
            return "written all over with winding galleries"

        elif prop_name == "holdfast_intact":
            val = float(value)
            if val < 0.3: return "torn off ragged at the base"
            return "the root-like holdfast still whole at the base"

        elif prop_name == "barb_integrity":
            val = float(value)
            if val < 0.3: return "barbs split and ragged"
            if val < 0.7: return "barbs mostly holding together"
            return "barbs zipped smooth and whole"

        elif prop_name == "oil_sheen":
            val = float(value)
            if val < 0.2: return "dull, the water-shedding sheen gone"
            if val < 0.6: return "a faint sheen left"
            return "still sleek — it beads water"

        else:
            return str(value)
    except (ValueError, TypeError):
        return OutcomeStatus.UNDETERMINED.value


def get_observable_properties(action: str) -> List[str]:
    """Returns the list of observable properties for a given action."""
    action_map = {
        "look": [
            "colour", "shape", "bark_presence", "grain_visibility", 
            "surface_damage", "size", "overall_condition"
        ],
        "pick_up": [
            "relative_weight", "balance_point", "surface_texture", 
            "moisture_impression", "structural_flexibility"
        ],
        "inspect_end": [
            "cross_sectional_geometry", "annual_ring_visibility", 
            "fiber_structure", "break_pattern"
        ],
        "scrape": [
            "internal_grain_color", "hardness_impression", 
            "fiber_structure", "resin_presence"
        ],
        "float_test": [
            "floats_or_sinks", "orientation", "water_absorption_rate", "buoyancy"
        ],
        "smell": [
            "scent"
        ]
    }
    return action_map.get(action, [])


# J-2376 (object_epistemic_loop Phase 3, D-0464): the classes whose Layer 2 is wood. The pick_up /
# inspect_end / scrape / float_test / smell branches below were written for driftwood_17 and read wood
# anatomy (annual rings, resin, fibre, a flexibility taken from a log's diameter) and DEFAULT a missing
# density to 0.5 (so anything without one "floats"). For any other class those are fabrications: a stone
# must not report annual-ring visibility. Callers that pass object_class get class-appropriate keys;
# callers that do not (every caller before J-2376) get the original output, byte-for-byte.
WOOD_CLASSES = frozenset({"driftwood", "deadfall_wood", "tree"})


def _class_overrides(physical_state: dict, action: str, observations: dict) -> None:
    """Non-wood classes: replace the wood-only keys of `action` with what this object's OWN Layer 2 can
    actually answer, or UNDETERMINED when it holds nothing that would produce the percept. Reads
    physical_state only (Layer 2), never a causal key."""
    U = OutcomeStatus.UNDETERMINED.value

    def put(k, v, conf):
        observations[k] = ObservationValue(value=v, confidence=conf).to_dict()

    def blank(k):
        observations[k] = ObservationValue(value=U, confidence="none", provenance=U).to_dict()

    ps = physical_state or {}
    if action == "pick_up":
        if "density" not in ps:
            blank("relative_weight")
        if "diameter_cm" not in ps:
            blank("structural_flexibility")
        if ps.get("structure") in (None, "unknown"):
            blank("balance_point")
        if "surface_roughness" not in ps:
            blank("surface_texture")
        if "moisture" not in ps:
            blank("moisture_impression")
    elif action == "inspect_end":
        for k in ("cross_sectional_geometry", "annual_ring_visibility", "fiber_structure"):
            blank(k)
        if "edge_rounding" not in ps:
            blank("break_pattern")
    elif action == "scrape":
        for k in ("internal_grain_color", "fiber_structure", "resin_presence"):
            blank(k)
        if "hardness" in ps:
            h = float(ps["hardness"])
            put("hardness_impression", "soft" if h < 0.3 else "firm" if h < 0.7 else "hard", "high")
        elif "brittleness" in ps:
            b = float(ps["brittleness"])
            put("hardness_impression", "crumbles under the edge" if b >= 0.7 else "flakes a little" if b >= 0.3
                else "takes no mark", "moderate")
        else:
            blank("hardness_impression")
    elif action == "float_test":
        if "density" not in ps:
            for k in ("floats_or_sinks", "orientation", "water_absorption_rate", "buoyancy"):
                blank(k)
        else:
            blank("orientation")
            if "surface_roughness" not in ps:
                blank("water_absorption_rate")
    elif action == "smell":
        if "salt_accumulation" not in ps:
            # no marine history in its Layer 2 (a plant, a garden thing, a made thing): the original
            # damp->"decayed" / softwood->"resinous" reading is wood-shaped; nothing real to say here.
            blank("scent")
        else:
            sa = float(ps["salt_accumulation"])
            put("scent", "marine" if sa > 0.5 else "faint_salt" if sa > 0.2 else "none_notable", "moderate")


def generate_observation(physical_state: dict, action: str, object_class: str = "") -> dict[str, dict]:
    """
    Generates an observation dictionary for a given action and physical state.
    Returns qualitative observations explicitly mapping what the action reveals.

    object_class (J-2376, optional): when given and not a wood class, the wood-only keys of pick_up /
    inspect_end / scrape / float_test / smell are replaced by class-appropriate ones (see
    _class_overrides). Omitted -> the original output, unchanged.
    """
    observations = {}
    
    try:
        observable_props = get_observable_properties(action)
        
        # Populate unknown for all possible properties not in this action
        all_props = set()
        for props in ["look", "pick_up", "inspect_end", "scrape", "float_test", "smell"]:
            all_props.update(get_observable_properties(props))
            
        for prop in all_props:
            if prop not in observable_props:
                observations[prop] = ObservationValue(
                    value=OutcomeStatus.UNKNOWN.value,
                    confidence="none",
                    provenance=OutcomeStatus.UNKNOWN.value
                ).to_dict()

        if action == "look":
            observations["colour"] = ObservationValue(
                value=_quantitative_to_qualitative("bleaching", physical_state.get("bleaching")),
                confidence="high"
            ).to_dict()
            observations["shape"] = ObservationValue(
                value=_quantitative_to_qualitative("structure", physical_state.get("structure")),
                confidence="high"
            ).to_dict()
            observations["bark_presence"] = ObservationValue(
                value=_quantitative_to_qualitative("bark_retention", physical_state.get("bark_retention")),
                confidence="high"
            ).to_dict()
            observations["grain_visibility"] = ObservationValue(
                value="visible" if physical_state.get("surface_roughness", 0) > 0.4 else "obscured by smooth weathering",
                confidence="moderate"
            ).to_dict()
            observations["surface_damage"] = ObservationValue(
                value=_quantitative_to_qualitative("fissuring", physical_state.get("fissuring")),
                confidence="high"
            ).to_dict()
            observations["size"] = ObservationValue(
                value=_quantitative_to_qualitative("length_cm", physical_state.get("length_cm")),
                confidence="high"
            ).to_dict()
            observations["overall_condition"] = ObservationValue(
                value="worn" if physical_state.get("edge_rounding", 0) > 0.5 else "fresh",
                confidence="moderate"
            ).to_dict()

        elif action == "pick_up":
            observations["relative_weight"] = ObservationValue(
                value=_quantitative_to_qualitative("density", physical_state.get("density")),
                confidence="high"
            ).to_dict()
            observations["balance_point"] = ObservationValue(
                value="centered" if _structure_kind(physical_state.get("structure")) != "root" else "uneven",
                confidence="low"
            ).to_dict()
            observations["surface_texture"] = ObservationValue(
                value=_quantitative_to_qualitative("surface_roughness", physical_state.get("surface_roughness")),
                confidence="high"
            ).to_dict()
            observations["moisture_impression"] = ObservationValue(
                value=_quantitative_to_qualitative("moisture", physical_state.get("moisture")),
                confidence="moderate"
            ).to_dict()
            observations["structural_flexibility"] = ObservationValue(
                value="stiff" if physical_state.get("diameter_cm", 0) > 3.0 else "flexible",
                confidence="moderate"
            ).to_dict()

        elif action == "inspect_end":
            observations["cross_sectional_geometry"] = ObservationValue(
                value="round" if _structure_kind(physical_state.get("structure")) == "branch" else "irregular",
                confidence="high"
            ).to_dict()
            observations["annual_ring_visibility"] = ObservationValue(
                value="distinct pronounced rings" if physical_state.get("wood_type") == "softwood" else "fine diffuse rings",
                confidence="moderate"
            ).to_dict()
            observations["fiber_structure"] = ObservationValue(
                value="straight" if _structure_kind(physical_state.get("structure")) == "branch" else "interlocked",
                confidence="moderate"
            ).to_dict()
            observations["break_pattern"] = ObservationValue(
                value=_quantitative_to_qualitative("edge_rounding", physical_state.get("edge_rounding")),
                confidence="high"
            ).to_dict()

        elif action == "scrape":
            density = physical_state.get("density", 0.5)
            # Internal grain color discrimination based on physical density & species profile
            if density > 0.60:
                internal_color = "pale tan with fine silver/pink grain"
                hardness = "hard"
            elif density > 0.50:
                internal_color = "creamy white with silky sheen"
                hardness = "moderately hard"
            else:
                internal_color = "pale yellowish"
                hardness = "soft"

            observations["internal_grain_color"] = ObservationValue(
                value=internal_color,
                confidence="high"
            ).to_dict()
            observations["hardness_impression"] = ObservationValue(
                value=hardness,
                confidence="high"
            ).to_dict()
            observations["fiber_structure"] = ObservationValue(
                value="straight" if _structure_kind(physical_state.get("structure")) == "branch" else "interlocked",
                confidence="moderate"
            ).to_dict()
            observations["resin_presence"] = ObservationValue(
                value="present" if physical_state.get("wood_type") == "softwood" else "absent",
                confidence="high"
            ).to_dict()

        elif action == "float_test":
            density = physical_state.get("density", 0.5)
            observations["floats_or_sinks"] = ObservationValue(
                value="floats" if density < 1.0 else "sinks",
                confidence="high"
            ).to_dict()
            observations["orientation"] = ObservationValue(
                value="horizontal",
                confidence="low"
            ).to_dict()
            observations["water_absorption_rate"] = ObservationValue(
                value="quick" if physical_state.get("surface_roughness", 0) > 0.6 else "slow",
                confidence="moderate"
            ).to_dict()
            observations["buoyancy"] = ObservationValue(
                value="high" if density < 0.55 else "low",
                confidence="high"
            ).to_dict()

        elif action == "smell":
            wood_type = physical_state.get("wood_type", "unknown")
            salt = physical_state.get("salt_accumulation", 0)
            moisture = physical_state.get("moisture", 0)
            
            scent = "none_notable"
            if salt > 0.5:
                scent = "marine"
            elif moisture > 0.6:
                scent = "decayed"
            elif wood_type == "softwood":
                scent = "resinous"
                
            observations["scent"] = ObservationValue(
                value=scent,
                confidence="moderate"
            ).to_dict()

        # ── class-distinctive extras (2026-08-15, the spawn-pipeline expansion): properties the
        # spawned classes carry (iridescence, veining, borer holes, rot, chambering…), reported only
        # when PRESENT in this object's physical state and only under the action that would genuinely
        # reveal them. Additive — driftwood observations are unchanged.
        _CLASS_EXTRAS = {
            "look": ["quartz_veining", "iridescence", "frosting", "borer_hole", "fungal_brackets",
                     "borer_galleries", "wear_polish", "holdfast_intact", "barb_integrity"],
            "pick_up": ["hardness", "hollowness", "porosity", "brittleness", "rot_softness",
                        "oil_sheen", "grain_size"],
            "inspect_end": ["chambering", "porosity", "grain_size"],
            "scrape": ["hardness", "rot_softness", "grain_size"],
        }
        for _prop in _CLASS_EXTRAS.get(action, []):
            if _prop in physical_state:
                observations[_prop] = ObservationValue(
                    value=_quantitative_to_qualitative(_prop, physical_state[_prop]),
                    confidence="high" if action in ("look", "pick_up") else "moderate",
                ).to_dict()

        if object_class and object_class not in WOOD_CLASSES:
            _class_overrides(physical_state, action, observations)

    except Exception as e:
        logger.error(f"Error generating observation: {e}")
        # Fail-open with empty safe default
        pass

    return observations
