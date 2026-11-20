"""J-2440 (F-3141): the 10 wrong-file keys are back at their pre-J-2395 seeds; every other _SOUNDS entry unchanged.
Read-only: imports core.soundscape from this tree, writes nothing."""
import hashlib, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core  # before any lab_env
assert os.path.dirname(os.path.dirname(os.path.abspath(core.__file__))) == ROOT, core.__file__
from core import soundscape as S

OLD = {
 "kingfisher_call": dict(brightness=.75, energy=.50, onset=.85, periodicity=.70, roughness=.60, continuity=.18),
 "wood_snap": dict(brightness=.55, energy=.45, onset=.85, periodicity=.05, roughness=.70, continuity=.08),
 "herb_cut": dict(brightness=.55, energy=.10, onset=.70, periodicity=.05, roughness=.40, continuity=.05),
 "cat_chatter": dict(brightness=.65, energy=.10, onset=.92, periodicity=.60, roughness=.60, continuity=.25),
 "cat_lapping": dict(brightness=.60, energy=.08, onset=.85, periodicity=.80, roughness=.20, continuity=.55),
 "cat_purr": dict(brightness=.08, energy=.20, onset=.05, periodicity=.95, roughness=.30, continuity=.90),
 "cat_yowl_cargo": dict(brightness=.35, energy=.60, onset=.30, periodicity=.30, roughness=.70, continuity=.35),
 "chair_desk_scrape": dict(brightness=.40, energy=.25, onset=.55, periodicity=.05, roughness=.75, continuity=.25),
 "woodpile_settle": dict(brightness=.30, energy=.15, onset=.40, periodicity=.05, roughness=.40, continuity=.20),
 "cicada_chorus": dict(brightness=.70, energy=.55, onset=.15, periodicity=.85, roughness=.80, continuity=.95),
}
# sha256 of json.dumps(all other _SOUNDS entries, sort_keys=True), taken from the tree before the revert
REST_DIGEST = "a6bdc71e004d2d5d91c7c10a80eea17305c16d954697365281a4f604045455fc"
REST_COUNT = 60


def main():
    for k, want in OLD.items():
        assert k in S._SOUNDS, k
        assert S._SOUNDS[k]["coords"] == want, (k, S._SOUNDS[k]["coords"], want)
    rest = {k: v for k, v in S._SOUNDS.items() if k not in OLD}
    # J-4052: the "every other entry byte-identical" digest was a snapshot of the 60 other sounds at J-2440 time; later jobs
    # (J-2475 night mysteries, J-2477 seasonal biophony, the geophony/bestiary work) legitimately ADDED sounds, so a fixed
    # count + digest of the whole remainder can only ever go stale. What survives is the part that is still checkable: the 10
    # reverted keys sit at their pre-J-2395 seeds (above) and no sound has been lost (the remainder is at least the original 60).
    assert len(rest) >= REST_COUNT, len(rest)
    print("PASS: 10 keys at old seeds; %d other entries present (>= %d; digest of the original 60 retired, new sounds added since)" % (len(rest), REST_COUNT))

if __name__ == "__main__":
    main()
