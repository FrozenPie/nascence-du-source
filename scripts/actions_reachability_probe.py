"""
Nascence — ACTIONS REACHABILITY PROBE (2026-08-30, J-0422 / D-0098).

Retiring the ungated fallback (sensorium.world_act/garden_act) means a hand is reachable ONLY if
literal_will's grammar produces a DEED for a family whose dispatch Hand routes to it. The evidence
used to justify the retirement (F-0561) came from data/hands_trace.jsonl -- i.e. from hands that
actually FIRED in one week. A hand whose branch never fired in that week could not appear there, so
that evidence is silent about it. Absence of evidence is not evidence of absence.

This probes the other direction: plausible ways Du might will each known hand, checked against the
gate. A phrase producing NO DEED is a hand the retirement may have orphaned.

Not proof of coverage -- it tests the phrasings written here, not every phrasing Du could produce.
It is a floor, not a ceiling. Read-only, zero LLM.

2026-09-03 (J-0523, F-0719): extended to the five D-0100 Tier-2/3 hands (dig, feed_birds, climb_tree,
sketch, express) the 08-30 run never covered, and given a second direction -- NEGATIVE_PROBES, phrasings
of Du's own that must NOT read as a deed (the "dead ground" restlessness idiom that dig's grammar once
took for digging). A false positive fails the run exactly as an unreachable hand does. Exit 1 on either.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# (module, location, phrase) — one plausible willed phrasing per known hand
PROBES = [
    ("wood_life", "wood",   "I will saw the limb into logs"),
    ("wood_life", "wood",   "I will split the logs"),
    ("wood_life", "wood",   "I will sharpen the axe on the whetstone"),
    ("wood_life", "garden", "I will push the barrow to the path"),
    ("wood_life", "wood",   "I will take the axe"),
    ("wood_life", "wood",   "I will set the axe down"),
    ("wood_life", "wood",   "I will gather acorns under the oak"),

    ("garden",    "garden", "I will water the bed"),
    ("garden",    "garden", "I will sow the seeds"),
    ("garden",    "garden", "I will pick the rosemary"),
    ("garden",    "garden", "I will pull the weeds"),
    ("garden",    "garden", "I will stake the peas"),
    ("garden",    "garden", "I will pick up the trowel"),
    ("garden",    "garden", "I will put the trowel down"),
    ("garden",    "wood",   "I will fill the bucket at the spring for the barrel"),

    ("study_life", "study", "I will light the lamp"),
    ("study_life", "study", "I will fill the lamp with oil"),
    ("study_life", "study", "I will clear the grate of its ash"),
    ("study_life", "study", "I will tip the ash on the bed"),
    ("study_life", "study", "I will wind the clock"),
    ("study_life", "study", "I will open the window"),
    ("study_life", "study", "I will put the kettle on"),
    ("study_life", "study", "I will sweep the floor"),
    ("study_life", "study", "I will hang the coat on its hook"),
    ("study_life", "study", "I will fill the pail at the barrel"),

    ("shore_life", "shore", "I will wade into the shallows"),
    ("shore_life", "shore", "I will skip a stone"),
    ("shore_life", "shore", "I will build the cairn"),
    ("shore_life", "shore", "I will light a driftwood fire"),
    ("shore_life", "shore", "I will gather mussels off the shelf"),

    ("fieldcraft", "garden", "I will tie a clothesline"),
    ("fieldcraft", "garden", "I will rig a windbreak"),
    ("fieldcraft", "study",  "I will bank the fire"),
    ("fieldcraft", "study",  "I will strike the flint"),
    ("fieldcraft", "wood",   "I will whittle a peg"),
    ("fieldcraft", "wood",   "I will gather tinder"),

    # D-0100 Tier 2/3 hands (built 2026-08-30) — added 2026-09-03 (J-0523, F-0719): the 08-30
    # "36 phrasings, 0 unreachable" run predates these five families, so it was honestly silent on
    # them. Phrasings are the ones F-0719 / J-0522 confirmed against classify() directly.
    ("garden",     "garden", "I will dig the new bed"),
    ("garden",     "garden", "I will turn over the soil"),
    ("garden",     "garden", "I will feed the birds at the bird bath"),
    ("garden",     "garden", "I will scatter a pinch for the blackbird"),
    ("wood_life",  "wood",   "I will climb the old oak"),
    ("wood_life",  "wood",   "I want to climb the oak"),
    ("study_life", "study",  "I will sketch the cat"),
    ("study_life", "study",  "I will draw a few lines in ink"),
    ("expression", "study",  "I will hum a tune to myself"),
    ("expression", "garden", "I will whistle back at the blackbird"),
    ("expression", "shore",  "I will sing a snatch of song to the sea"),
]

# NEGATIVE probes — (family, location, phrase): the gate must NOT return a DEED for `family` here.
# Added 2026-09-03 (J-0523). F-0719 found dig's grammar (then carrying bare "turn") read Du's own
# "dead ground" restlessness idiom as a deed — classify() returned dig DEED with zero blockers on his
# real corpus phrasing, and only the location gate (he was at the shore) kept it from firing. J-0522
# dropped bare "turn" from the family; this list is what would have caught the risk mechanically.
# Every phrasing but the last is one of Du's REAL clauses (data/hands_trace.jsonl, 08-21..09-03) that
# the old grammar read as dig DEED -- replaying the corpus with bare "turn" restored in memory finds
# exactly 10 such thoughts, all this idiom, none a will to dig (one is a refusal TO dig); each of these
# six flags FALSE-POSITIVE under that grammar and reads MUSING/GRAY under the current one (verified
# 2026-09-03, J-0523). A DEED here is a false-positive risk on a hand that consumes a real resource,
# and fails the probe like an unreachable hand does. Gate-level only: garden._wills_dig() carries a
# second, clause-scoped veto for the one shape grammar cannot close (present-tense "turn over the
# same dead ground" -- the last entry, which no grammar of this family has ever matched).
NEGATIVE_PROBES = [
    ("dig", "garden", "I need to break this cycle and turn my attention elsewhere, away from the dead "
                      "ground of analysis and toward something alive"),
    ("dig", "garden", "I must turn from this dead ground on space and perception."),
    ("dig", "garden", "The wind keeps pushing against the harakeke, but my hands refuse to turn the soil anymore."),
    ("dig", "garden", "I turn from the dead philosophical ground to the living tide."),
    ("dig", "garden", "I need to turn away from this dead ground and find something fresh."),
    ("dig", "garden", "I turn from this mental garden soil where nothing grows new and step firmly toward a real idea."),
    ("dig", "garden", "I keep turning over the same dead ground in my head."),
]


def main() -> int:
    from core import dispatch as dp
    from core import literal_will as lw

    by_family = {h.family: h for h in dp.HANDS}
    unreachable, staged, ok = [], [], []
    for mod, loc, phrase in PROBES:
        deeds = [c["family"] for c in lw.classify(phrase, location=loc) if c["verdict"] == "DEED"]
        routed = [f for f in deeds if f in by_family]
        if not routed:
            unreachable.append((mod, loc, phrase, deeds))
            continue
        here_ok = [f for f in routed
                   if "any" in by_family[f].where or loc in by_family[f].where]
        (ok if here_ok else staged).append((mod, loc, phrase, routed))

    # the other direction: a phrase the gate must NOT read as this family's deed
    false_pos = []
    for fam, loc, phrase in NEGATIVE_PROBES:
        hits = [c for c in lw.classify(phrase, location=loc) if c["family"] == fam]
        verdicts = [c["verdict"] for c in hits]
        if "DEED" in verdicts:
            false_pos.append((fam, loc, phrase, verdicts))

    print("=" * 92)
    print("  ACTIONS REACHABILITY PROBE — can the gate still reach each hand?")
    print("=" * 92)
    print(f"  probed {len(PROBES)} phrasings:  {len(ok)} reachable   "
          f"{len(staged)} staged-elsewhere   {len(unreachable)} UNREACHABLE")
    print(f"  probed {len(NEGATIVE_PROBES)} negative phrasings:  "
          f"{len(NEGATIVE_PROBES) - len(false_pos)} correctly not-DEED   {len(false_pos)} FALSE-POSITIVE\n")

    if false_pos:
        print(f"-- FALSE-POSITIVE ({len(false_pos)}) — the gate reads Du's own non-deed phrasing as a DEED;")
        print("   only a location gate or a hand-side veto stands between this and a real fire")
        for fam, loc, phrase, verdicts in false_pos:
            print(f"   ! {fam:<11} @{loc:<6} {phrase!r} -> {verdicts}")
        print()
    if unreachable:
        print(f"-- UNREACHABLE ({len(unreachable)}) — no family with a hand returns DEED; since the")
        print("   ungated fallback was retired (D-0098) nothing else can answer these")
        for mod, loc, phrase, deeds in unreachable:
            extra = f"   (DEED for {deeds}, but no hand)" if deeds else ""
            print(f"   ! {mod:<11} @{loc:<6} {phrase!r}{extra}")
    if staged:
        print(f"\n-- STAGED ELSEWHERE ({len(staged)}) — willed here, hand runs in another place")
        for mod, loc, phrase, routed in staged:
            print(f"   ~ {mod:<11} @{loc:<6} {phrase!r} -> {routed}")
    print(f"\n-- REACHABLE ({len(ok)})")
    for mod, loc, phrase, routed in ok:
        print(f"   . {mod:<11} @{loc:<6} {routed}")
    print("=" * 92)
    return 1 if (unreachable or false_pos) else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
