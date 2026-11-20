from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nascence.world_knowledge")

_DATA = Path(__file__).parent.parent / "data"


@dataclass
class DiagnosticEntry:
    domain: str
    claim: str
    diagnostic_features: list[str]
    source: str
    confidence: str
    limitations: list[str]


@dataclass
class DiagnosticResult:
    candidate_explanations: list[dict]
    undetermined_aspects: list[str]
    discriminative_actions: list[str]
    limitations_note: str


# --- KNOWLEDGE BASE ---

_KNOWLEDGE_BASE: list[DiagnosticEntry] = [
    # Wood Anatomy
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Silver beech timber is characteristically pale with fine even grain.",
        diagnostic_features=["pale grain", "fine texture", "even grain", "diffuse porous"],
        source="botanical reference",
        confidence="established",
        limitations=["Bark loss or heavy weathering can obscure fine texture.", "Can be confused with other pale hardwoods."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Birch timber exhibits pale coloration with faint growth rings.",
        diagnostic_features=["pale grain", "faint growth rings", "fine texture"],
        source="botanical reference",
        confidence="established",
        limitations=["Extremely difficult to distinguish from silver beech when heavily weathered without microscopic analysis."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Willow is a lightweight hardwood with pale color and indistinct rings.",
        diagnostic_features=["pale color", "lightweight", "indistinct rings"],
        source="field guide",
        confidence="established",
        limitations=["Low density can be confused with decayed wood of heavier species."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Fir is a softwood, typically pale but showing distinct early/latewood transitions.",
        diagnostic_features=["pale grain", "distinct rings", "softwood", "resinous smell"],
        source="botanical reference",
        confidence="established",
        limitations=["Smell fades with prolonged marine exposure."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Pine features pronounced growth rings and resin canals.",
        diagnostic_features=["pronounced rings", "resin canals", "yellowish tint", "resinous smell"],
        source="botanical reference",
        confidence="established",
        limitations=["Yellowish tint can bleach to white in marine environments."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Rimu heartwood is distinctively reddish-brown with fine, even texture.",
        diagnostic_features=["reddish-brown", "fine texture", "distinct color zones"],
        source="NZ botanical reference",
        confidence="established",
        limitations=["Sapwood is pale and can be confused with other pale softwoods."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Kahikatea is a very pale softwood without odor, widely used for food boxes.",
        diagnostic_features=["very pale", "no odor", "uniform texture"],
        source="NZ botanical reference",
        confidence="established",
        limitations=["Susceptible to rapid rot if not treated; often confused with other pale softwoods."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Totara is a durable reddish softwood, resistant to marine borers.",
        diagnostic_features=["reddish", "durable", "resistant to rot"],
        source="NZ botanical reference",
        confidence="established",
        limitations=["Red coloration can darken or bleach depending on environment."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="Hardwoods possess vessels (pores), whereas softwoods lack them.",
        diagnostic_features=["vessels present", "pores visible"],
        source="general botanical knowledge",
        confidence="established",
        limitations=["Requires magnifying lens or clean cross-sectional cut to confirm."]
    ),
    DiagnosticEntry(
        domain="wood_anatomy",
        claim="High density implies slow growth or specific taxonomic groups, but can be altered by waterlogging.",
        diagnostic_features=["heavy", "dense", "hard to scratch"],
        source="field guide",
        confidence="established",
        limitations=["Waterlogged wood feels artificially dense; dry rotted wood feels artificially light."]
    ),

    # Intertidal/Marine Weathering
    DiagnosticEntry(
        domain="marine_weathering",
        claim="Prolonged marine transport removes bark, smooths sharp edges, and bleaches external color.",
        diagnostic_features=["no bark", "rounded edges", "smooth surface", "bleached white", "salt accumulation"],
        source="general ecology",
        confidence="established",
        limitations=["Cannot provide a precise timeline. Intermittent stranding on beaches pauses the rounding process."]
    ),
    DiagnosticEntry(
        domain="marine_weathering",
        claim="Salt accumulation and checking (surface cracking) indicate cycles of wetting and drying.",
        diagnostic_features=["salt crystals", "surface checking", "cracks along grain"],
        source="field guide",
        confidence="established",
        limitations=["Does not specify the number of cycles or total duration."]
    ),

    # Geological/Physical
    DiagnosticEntry(
        domain="geological",
        claim="Wave action sorts materials by density and size along the strandline.",
        diagnostic_features=["strandline accumulation", "sorted by size", "entangled with seaweed"],
        source="coastal geomorphology",
        confidence="established",
        limitations=["Storm surges can scatter sorted materials unpredictably."]
    ),

    # Ecological
    DiagnosticEntry(
        domain="ecological",
        claim="Marine organism colonization (e.g., barnacles, shipworms) indicates prolonged uninterrupted submersion.",
        diagnostic_features=["barnacle attachment", "shipworm tunnels", "algal mat"],
        source="marine biology",
        confidence="established",
        limitations=["Absence of colonization does not prove short duration, as abrasive high-energy environments prevent settlement."]
    ),

    # ═══ 2026-08-15 expansion packs — one domain per spawned class (the substrate had one domain) ═══

    # Stone lithology
    DiagnosticEntry(
        domain="stone_lithology",
        claim="Greywacke — the common grey stone of these coasts — is hard, fine-grained, and often carries thin pale quartz veins.",
        diagnostic_features=["hard", "fine grain", "grey", "thin pale seam", "quartz veins"],
        source="field geology",
        confidence="established",
        limitations=["Weathered argillite can look similar; argillite is finer-grained and splits in flakes."]
    ),
    DiagnosticEntry(
        domain="stone_lithology",
        claim="Sandstone is soft enough for a thumbnail or another stone to scratch, with visible sandy grain.",
        diagnostic_features=["soft", "coarse grain", "sandy grain", "scratches easily"],
        source="field geology",
        confidence="established",
        limitations=["Surface weathering can soften the rind of harder stones; scratch a fresh face."]
    ),
    DiagnosticEntry(
        domain="stone_lithology",
        claim="Pumice is stone that floats: frothed volcanic glass, feather-light, full of pores — it drifts on ocean currents for years.",
        diagnostic_features=["floats", "very light", "porous", "pale", "rough"],
        source="field geology",
        confidence="established",
        limitations=["Waterlogged pumice slowly sinks; dry it first."]
    ),
    DiagnosticEntry(
        domain="stone_lithology",
        claim="The rounding of a stone records its transport: sharp edges mean a fresh break or short journey; full rounding means long tumbling in water.",
        diagnostic_features=["rounded", "sharp edges", "worn", "smooth"],
        source="field geology",
        confidence="established",
        limitations=["Soft stones round quickly — rounding alone cannot give a duration without knowing the hardness."]
    ),

    # Shell biology
    DiagnosticEntry(
        domain="shell_biology",
        claim="A single neat round hole drilled through a shell is the mark of a predatory sea-snail — the shell records its own death.",
        diagnostic_features=["neat round hole", "drilled", "single hole"],
        source="marine biology",
        confidence="established",
        limitations=["Wave-wear against a sharp point can bore a ragged hole; the predatory hole is countersunk and clean."]
    ),
    DiagnosticEntry(
        domain="shell_biology",
        claim="Strong blue-green fire in a shell fragment's inner surface marks paua (abalone); most other local shells are dull inside.",
        diagnostic_features=["colour moving", "blue-green", "iridescent", "play of colour"],
        source="marine biology",
        confidence="established",
        limitations=["Mussel nacre shows a weaker, silvery iridescence — the paua fire is unmistakably stronger."]
    ),
    DiagnosticEntry(
        domain="shell_biology",
        claim="A chalky white oval, chambered like a honeycomb and nearly weightless, is cuttlebone — the internal float of a cuttlefish, not a true shell.",
        diagnostic_features=["chambered", "chalky", "very light", "white oval", "floats"],
        source="marine biology",
        confidence="established",
        limitations=[]
    ),
    DiagnosticEntry(
        domain="shell_biology",
        claim="Wear tells a shell's post-mortem history: a fresh shell keeps its ridges and colour; a long-tumbled one is worn to a smooth, bleached blank.",
        diagnostic_features=["worn smooth", "bleached", "ridges gone", "soft shine"],
        source="marine biology",
        confidence="established",
        limitations=["Species differ in toughness; thin shells wear far faster than thick ones."]
    ),

    # Bone taphonomy
    DiagnosticEntry(
        domain="bone_taphonomy",
        claim="Bird bones are hollow and astonishingly light for their size — a dry wing-bone will float; mammal bone of the same size is dense and sinks.",
        diagnostic_features=["hollow", "very light", "floats", "thin walls"],
        source="natural history",
        confidence="established",
        limitations=["Waterlogged or mineral-soaked bone loses this signature."]
    ),
    DiagnosticEntry(
        domain="bone_taphonomy",
        claim="A fish vertebra is a spool: round, waisted like an hourglass in section, with a pit at each face.",
        diagnostic_features=["spool shape", "hourglass", "round", "pitted faces"],
        source="natural history",
        confidence="established",
        limitations=[]
    ),
    DiagnosticEntry(
        domain="bone_taphonomy",
        claim="Sun-bleached bone whitens and its surface fissures in fine cracks along the grain; sea-worn bone smooths and rounds instead.",
        diagnostic_features=["bleached white", "fine cracks", "smoothed", "rounded ends"],
        source="natural history",
        confidence="established",
        limitations=["A bone may show both, in sequence — beach-cast, then stranded above the tide line."]
    ),

    # Egg cases and sea-litter
    DiagnosticEntry(
        domain="sea_litter",
        claim="A dark leathery pouch with a horn at each corner is a mermaid's purse — the egg case of a skate or shark, its young long gone if a corner is split.",
        diagnostic_features=["leathery pouch", "horns", "dark", "split corner"],
        source="marine biology",
        confidence="established",
        limitations=[]
    ),
    DiagnosticEntry(
        domain="sea_litter",
        claim="Sea-glass records its tumbling: fresh glass is clear and sharp; years of sand-milling frost the surface all over and round every edge.",
        diagnostic_features=["frosted", "cloudy", "rounded edges", "no shine"],
        source="beachcombing lore",
        confidence="established",
        limitations=["Frosting rate varies with the beach's energy — a duration is a guess, an ordering is not."]
    ),
    DiagnosticEntry(
        domain="sea_litter",
        claim="Kelp torn up with its holdfast intact came off in a storm; a ragged base means it broke at sea and drifted.",
        diagnostic_features=["holdfast", "root-like base", "torn base", "ragged"],
        source="marine biology",
        confidence="established",
        limitations=[]
    ),
    DiagnosticEntry(
        domain="sea_litter",
        claim="A feather's condition tells its age off the bird: fresh ones zip smooth and shed water; old ones split, ragged, with the oil-sheen gone.",
        diagnostic_features=["barbs split", "ragged", "dull", "zipped smooth", "beads water"],
        source="natural history",
        confidence="established",
        limitations=["A preened feather freshly dropped can already look worn if the bird was in moult."]
    ),

    # Deadfall & rot (the wood)
    DiagnosticEntry(
        domain="wood_decay",
        claim="Winding grooves under loose bark are borer-beetle galleries — written after death; a limb riddled with them fell long ago.",
        diagnostic_features=["winding grooves", "galleries", "under the bark"],
        source="forest ecology",
        confidence="established",
        limitations=["Standing dead wood is also bored — galleries date the death, not the fall."]
    ),
    DiagnosticEntry(
        domain="wood_decay",
        claim="Bracket fungus needs a season or more of stillness: a shelved limb has lain unmoved at least that long.",
        diagnostic_features=["brackets", "shelved", "fungus"],
        source="forest ecology",
        confidence="established",
        limitations=[]
    ),
    DiagnosticEntry(
        domain="wood_decay",
        claim="Rot works from the ground up: a limb soft and punky on its underside but sound above has lain where it fell; soft right through, it is old ground-wood.",
        diagnostic_features=["punky", "soft underside", "sound above", "crumbling"],
        source="forest ecology",
        confidence="established",
        limitations=["In a wet winter the whole limb wets through — test in a dry spell."]
    ),
    DiagnosticEntry(
        domain="wood_decay",
        claim="Manuka is hard, dark, slow-grown and burns hot and long; a crooked dense branch that blunts the knife is likely manuka.",
        diagnostic_features=["hard", "dark", "dense", "crooked", "heavy for its size"],
        source="bush lore",
        confidence="established",
        limitations=["Old dry beech can also be hard; manuka's tight crooked growth and dark bark distinguish it."]
    ),
]


def query_diagnostic_knowledge(observed_features: list[str], domain: Optional[str] = None) -> DiagnosticResult:
    """
    Main entry point. Takes a list of observed feature strings and optionally a domain filter.
    Returns candidate explanations ranked by feature match, with explicit undetermined aspects.
    """
    try:
        candidates = []
        undetermined = set()
        actions = set()
        
        for entry in _KNOWLEDGE_BASE:
            if domain and entry.domain != domain:
                continue
                
            match_count = sum(1 for feat in observed_features if any(feat.lower() in d_feat.lower() or d_feat.lower() in feat.lower() for d_feat in entry.diagnostic_features))
            
            if match_count > 0:
                confidence_score = min(0.95, round(0.2 + (match_count * 0.15), 2))
                candidates.append({
                    "hypothesis": entry.claim,
                    "supporting_features": entry.diagnostic_features,
                    "confidence": confidence_score
                })
                
                for limitation in entry.limitations:
                    undetermined.add(limitation)
                    
        # Sort candidates by confidence descending
        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Determine standard discriminative actions based on features
        if any("pale" in f.lower() or "grain" in f.lower() for f in observed_features):
            actions.add("inspect_end for annual ring pattern")
            actions.add("scrape for internal grain color")
            actions.add("check for vessels/pores with magnification")
            undetermined.add("exact species")
            
        if any("smooth" in f.lower() or "bark" in f.lower() or "weather" in f.lower() for f in observed_features):
            actions.add("check for internal moisture")
            actions.add("look for marine borer holes")
            undetermined.add("exact exposure duration")
            undetermined.add("precise origin")
            
        limitations_note = "Available evidence provides clues but is insufficient to make definitive identifications. Multiple phenomena produce similar observable characteristics."
        
        return DiagnosticResult(
            candidate_explanations=candidates,
            undetermined_aspects=list(undetermined),
            discriminative_actions=list(actions),
            limitations_note=limitations_note
        )
    except Exception as e:
        logger.error(f"Error querying diagnostic knowledge: {e}")
        return DiagnosticResult(
            candidate_explanations=[],
            undetermined_aspects=["system_error"],
            discriminative_actions=[],
            limitations_note=f"An error occurred while querying knowledge: {str(e)}"
        )


def get_species_diagnostics(features: dict) -> list[dict]:
    """
    Specific helper for wood species identification. 
    Returns candidate species with supporting/conflicting evidence.
    """
    try:
        feature_list = []
        for key, value in features.items():
            if isinstance(value, str):
                feature_list.append(value)
            elif isinstance(value, list):
                feature_list.extend(value)
                
        result = query_diagnostic_knowledge(feature_list, domain="wood_anatomy")
        
        # Map back to species names roughly
        species_candidates = []
        for c in result.candidate_explanations:
            claim = c["hypothesis"].lower()
            species_name = "unknown"
            if "silver beech" in claim: species_name = "silver beech"
            elif "birch" in claim: species_name = "birch"
            elif "willow" in claim: species_name = "willow"
            elif "fir" in claim: species_name = "fir"
            elif "pine" in claim: species_name = "pine"
            elif "rimu" in claim: species_name = "rimu"
            elif "kahikatea" in claim: species_name = "kahikatea"
            elif "totara" in claim: species_name = "totara"
            
            if species_name != "unknown":
                species_candidates.append({
                    "species": species_name,
                    "supporting_evidence": c["supporting_features"],
                    "confidence": c["confidence"]
                })
                
        return species_candidates
    except Exception as e:
        logger.error(f"Error in species diagnostics: {e}")
        return []


def assess_exposure_duration(weathering_features: dict) -> dict:
    """
    Returns an exposure estimate range (NOT a point estimate) with confidence and explicit limitations.
    """
    try:
        estimate = {
            "estimated_range": "unknown",
            "confidence": "low",
            "limitations": [
                "Duration cannot be precisely determined from appearance alone.",
                "Intermittent stranding and storm events complicate estimation.",
                "Multiple exposure timelines can yield identical physical states."
            ]
        }
        
        has_bleaching = weathering_features.get("bleached", False) or "bleached white" in weathering_features.values()
        has_rounding = weathering_features.get("rounded", False) or "rounded edges" in weathering_features.values()
        has_colonization = weathering_features.get("colonized", False) or "barnacle" in str(weathering_features)
        
        if has_colonization:
            estimate["estimated_range"] = "months to years (uninterrupted submersion)"
            estimate["confidence"] = "medium"
        elif has_bleaching and has_rounding:
            estimate["estimated_range"] = "weeks to months (prolonged transport)"
            estimate["confidence"] = "medium"
        elif not has_bleaching and not has_rounding:
            estimate["estimated_range"] = "days to weeks (recent entry)"
            estimate["confidence"] = "low"
            
        return estimate
    except Exception as e:
        logger.error(f"Error assessing exposure duration: {e}")
        return {"estimated_range": "error", "confidence": "none", "limitations": []}


def get_discriminative_actions(question: str, current_observations: list[str]) -> list[dict]:
    """
    Given a question and current observations, suggests which actions could provide discriminating evidence.
    """
    try:
        actions = []
        q_lower = question.lower()
        
        if "species" in q_lower or "wood" in q_lower or "tree" in q_lower:
            actions.append({
                "action": "inspect_end",
                "purpose": "Check annual ring pattern and porosity to distinguish hardwood vs softwood.",
                "expected_discriminator": "Presence of vessels (pores) indicates hardwood."
            })
            actions.append({
                "action": "scrape_surface",
                "purpose": "Reveal unweathered internal grain color beneath the bleached exterior.",
                "expected_discriminator": "True color (e.g., reddish vs pale) helps eliminate candidates."
            })
            
        if "time" in q_lower or "duration" in q_lower or "how long" in q_lower or "weathering" in q_lower:
            actions.append({
                "action": "inspect_surface_closely",
                "purpose": "Look for micro-colonization (e.g., tiny barnacles) or shipworm entry holes.",
                "expected_discriminator": "Biological colonization indicates continuous submersion vs intermittent stranding."
            })
            actions.append({
                "action": "assess_moisture",
                "purpose": "Check how deep the waterlogged layer extends.",
                "expected_discriminator": "Deep waterlogging suggests longer submersion compared to surface-only wetting."
            })
            
        if not actions:
            actions.append({
                "action": "gather_more_observations",
                "purpose": "Current question does not map to a specific discriminative action.",
                "expected_discriminator": "Any novel feature."
            })
            
        return actions
    except Exception as e:
        logger.error(f"Error getting discriminative actions: {e}")
        return []
