"""
J-1473: strings_and_sheets Phase 1 dry run -- constructed 3-point world-sound strings + offline realness
test. NO LIVE CHANGE: reads core.soundscape._SOUNDS, writes only this script's own two outputs. Method
pinned in docs/lab/strings_sheets_phase1_dryrun_metric_sheet.md, written BEFORE this script ran.

Usage: python scripts/sound_strings_phase1_dryrun.py
Outputs:
  data/sound_strings_constructed.json          -- the sidecar (onset/peak/tail per key + rationale)
  docs/lab/strings_sheets_phase1_dryrun_<date>.json -- full per-key realness + peak-proximity results
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from core import soundscape as ss  # noqa: E402

AXES = ss._AXES  # ("brightness","energy","onset","periodicity","roughness","continuity") -- reused, not copied
ENVELOPE = ("brightness", "energy", "onset")
TIMBRE = ("periodicity", "roughness", "continuity")

# ---------------------------------------------------------------------------------------------------
# (1) Archetype assignment -- hand-classified from _SOUNDS' own object field / inline comments /
# _PERCEPT_LINES prose, per the metric sheet's (b). Every one of the 70 keys appears exactly once.
# ---------------------------------------------------------------------------------------------------

_BED_LIKE = {"bees_in_garden", "wind_in_trees", "stream_run", "clock_tick", "kettle_sing", "dawn_chorus",
             "tide_pool_trickle", "footsteps_shingle", "footsteps_leafmould", "saw_rasp", "cat_chatter",
             "hedgehog_snuffle",                         # J-2475 (§2): a busy continuous snuffling, bed-like while it lasts
             "hail_on_roof", "hail_on_leaves", "drizzle_hiss", "downpour_drum", "stream_over_stones",
             "undertow_rumble", "calm_sea_hush",         # J-2476 (§3): continuous presences carried as rate 0.0 (the trickle convention)
             "kelp_fly_buzz",                            # J-2477 (§4): the wrack-line's summer flies, a bed (rate 0.0)
             "runout_hiss"}                              # J-2478 (§5): the run-out groove hissing round, a bed (rate 0.0)

_CALL = {"gull_cries", "tui_song", "blackbird_song", "bellbird_song", "morepork_call", "cat_trill",
         "cat_meow_at_door", "cat_demand", "cat_yowl_cargo", "oystercatcher_call", "cuckoo_call",
         "godwits_overhead", "blackbird_alarm", "small_birds", "wood_pigeon", "wren_scold",
         "fantail_chatter", "riroriro_trill", "kingfisher_call", "robin_song", "penguin_bray",
         "possum_rasp", "distant_yowl",                  # J-2475 (§2): two night voices, call-shaped
         "cat_hiss", "cat_growl", "cat_call",            # cat_overhaul B3/C3 (J-2470/J-2468): hers at the tom; his voice calling her
         "silvereye_flock", "paradise_duck_flyover"}     # J-2477 (§4): a flock's contact cheeps; a pair's honking going over -- calls

_WINGBEAT = {"shag_wingbeats", "kereru_wingbeats"}

_THUMP = {"cat_thump", "thunder", "wood_snap", "gate_latch", "window_rattle", "moth_tap", "canopy_drip",
          "woodpile_settle", "chair_desk_scrape", "pen_scratch", "page_turn", "herb_cut", "sow_dig",
          "door_sound", "log_on_fire", "kettle_fill", "kettle_pour", "bed_watering", "wood_haul_clatter",
          "leaf_rustle", "branches_creak", "footsteps_floorboards", "footsteps_grass_soil",
          "wall_scratch", "dolphin_blow",                # J-2475 (§2): a few strokes and a pause; one breath, and gone
          "rain_down_chimney", "tin_roof_tick", "frost_crack",   # J-2476 (§3): a spit, a tick, one report -- strikes, each
          "needle_crackle", "letterbox_flag_clank"}      # J-2478 (§5): dust-pops in the lead-in; the flag's tin knock -- strikes

# One-line semantic snippets, drawn from _SOUNDS' own inline comments / _PERCEPT_LINES prose / the
# module docstring -- the "render strings and object semantics" the job names. Not a re-derivation:
# these are the SAME words already in core/soundscape.py, carried into the rationale.
_SNIPPETS = {
    "waves_on_shingle": "waves working steadily at the shingle",
    "gull_cries": "the gulls' discrete cries overhead",
    "tui_song": "long bright trill, falling away (the plan's own §3A example)",
    "blackbird_song": "a fluted, easy bird phrase",
    "bellbird_song": "a clear, pure bell-note, more periodic and far less rough than the blackbird",
    "morepork_call": "two spaced, falling notes -- \"more-pork, more-pork\"",
    "cat_purr": "a steady, unhurried motor, barely above the quiet",
    "cat_trill": "the greeting chirrup: short, rising, rolled",
    "cat_meow_at_door": "one flat vowel at the shut door, evenly repeated",
    "cat_demand": "the food cry: flatter, louder, a rasp coming in",
    "cat_chatter": "jaw-juddering at birds through glass: fast, dry, tiny",
    "cat_yowl_cargo": "the muffled announcing yowl, mouth full",
    "cat_thump": "off the sill onto the boards: one soft double thud",
    "cat_lapping": "at the saucer: a rapid liquid ticking",
    "cat_storm_rustle": "under the desk between thunderclaps",
    "cat_hiss": "the long flat tearing breath, mouth open, at the tom",
    "cat_growl": "the low held note at the glass, under her breath",
    "cat_call": "his own voice calling her -- puss-puss, the kissing noise, her name",
    "fire_crackle": "dry snaps settling into a low, busy conversation with itself",
    "rain_on_roof": "rain on the roof, continuous",
    "wind_in_eaves": "the wind worked loose-toothed by a gale, in the eaves",
    "thunder": "a single storm-class report",
    "moth_tap": "a moth (or several) tapping the lamp",
    "waves_crashing": "a big, breaking sea",
    "shingle_drag": "the shingle dragged by the water",
    "oystercatcher_call": "a shore bird's discrete call",
    "cuckoo_call": "the shining cuckoo's call",
    "godwits_overhead": "godwits passing overhead",
    "blackbird_alarm": "the blackbird's alarm, sudden and sharp",
    "bees_in_garden": "a steady garden drone",
    "small_birds": "small garden birds, active and light",
    "wind_in_trees": "wind working steadily through the trees",
    "wood_pigeon": "a soft, round, drowsy five-note coo from the canopy",
    "wren_scold": "a sudden loud scolding trill from the undergrowth",
    "branches_creak": "high branches groaning against each other in wind",
    "canopy_drip": "water ticking off the leaves after rain",
    "leaf_rustle": "small movement in the leaf-litter",
    "fantail_chatter": "follows movement, snapping at stirred insects",
    "riroriro_trill": "a long wistful falling trill, heard not seen",
    "kereru_wingbeats": "the wood pigeon's second spoke -- the heavy whoosh-whoosh",
    "kingfisher_call": "a dry staccato kek-kek-kek from a high perch",
    "shag_wingbeats": "heavy slow wingbeats low over the water",
    "cicada_chorus": "summer's wall of sound in the trees",
    "cricket_night": "a summer night's slow pulse from the grass",
    "embers_settle": "the fire's late voice: a soft collapse, a tick of cooling",
    "window_rattle": "the north window worked loose-toothed by a gale",
    "tide_pool_trickle": "low tide: the bared pools draining thread by thread",
    "distant_surf_boom": "a big sea heard from indoors/uphill",
    "dawn_chorus": "first light: every voice at once",
    "robin_song": "clear even phrases from a low perch, bold",
    "footsteps_shingle": "his own steps on shingle",
    "footsteps_leafmould": "his own steps on leaf-mould",
    "clock_tick": "the study clock, running",
    "kettle_sing": "the kettle come to the boil",
    "stream_run": "the stream from the spring",
    "penguin_bray": "the small penguin's bray",
    "saw_rasp": "his own saw, back and forth",
    "footsteps_floorboards": "his own steps on the floorboards",
    "footsteps_grass_soil": "his own steps on grass/soil",
    "kettle_fill": "the water in, the kettle set on the hob",
    "kettle_pour": "the boiled water poured onto the leaves",
    "page_turn": "a single page turned",
    "pen_scratch": "his own pen on paper",
    "wood_snap": "a single crack from the deadfall",
    "log_on_fire": "a log placed on the fire",
    "gate_latch": "the garden gate's latch",
    "woodpile_settle": "the stocked woodpile settling at night",
    "wood_haul_clatter": "his own armful of wood, clattering",
    "bed_watering": "watering the garden bed",
    "herb_cut": "a single snip of the shears",
    "sow_dig": "digging into the garden bed",
    "door_sound": "the cottage door",
    "chair_desk_scrape": "his own chair, scraped back",
    # J-2475 (sound_world_expansion §2, D-0500): the night mysteries, words carried from _SOUNDS' own comments
    "possum_rasp": "a harsh coughing rasp from the tree / the oak -- frightening unnamed",
    "wall_scratch": "a tiny dry scratching INSIDE the study wall: intimate, unfindable",
    "distant_yowl": "a cat's long rising yowl, far off -- but WHOSE?",
    "hedgehog_snuffle": "busy wet snuffling and snorting along the bed edges",
    "dolphin_blow": "one breath out on the water -- a single wet gust, and gone",
    # J-2476 (sound_world_expansion §3, D-0500): the geophony fills, words carried from _SOUNDS' own comments
    "hail_on_roof": "a winter squall's stones on the iron: a hard bright drumming rattle",
    "hail_on_leaves": "the same stones through the canopy and the beds: a shredding patter",
    "drizzle_hiss": "the fine grade: a hiss on the roof, barely a sound, that does not stop",
    "downpour_drum": "the heavy grade: the roof drumming, the gutters overrun",
    "rain_down_chimney": "rain reaching the lit fire: a sizzle and a spit, now and then",
    "tin_roof_tick": "the corrugated iron easing as the sun warms it / lets it go: single ticks",
    "stream_over_stones": "the stream's SECOND spoke: its mouth at the shore, quick over the stones",
    "undertow_rumble": "a big sea's backwash rolling the shingle: bass felt in the feet",
    "frost_crack": "a hard-frost night: one sharp report from timber or ground, and nothing",
    "calm_sea_hush": "the near-silence state: a glass sea, quiet registered as a state, not an absence",
    # J-2477 (sound_world_expansion §4, D-0500): the seasonal biophony, words carried from _SOUNDS' own comments
    "silvereye_flock": "a loose winter flock working the hedge: soft contact cheeps from many throats",
    "paradise_duck_flyover": "a pair passing high: her thin zeek-zeek, his hoarse honk answering, going away",
    "kelp_fly_buzz": "summer wrack-line flies: a low rising cloud-buzz off the heaps, settling again",
    # J-2478 (sound_world_expansion §5, D-0500): the apparatus, words carried from _SOUNDS' own comments
    "needle_crackle": "the lead-in groove: dust-pops over a faint hiss, dry, irregular, brief",
    "runout_hiss": "the run-out groove: a steady hiss with one soft click each turn, until lifted",
    "letterbox_flag_clank": "the raised tin flag knocked against the box by the gusts, from the gate",
}


def _archetype(key: str) -> str:
    if key in ss._BEDS:
        return "bed"
    if key in _BED_LIKE:
        return "bed_like"
    if key in _CALL:
        return "call"
    if key in _WINGBEAT:
        return "wingbeat"
    if key in _THUMP:
        return "thump"
    raise ValueError(f"key {key!r} not classified into any archetype -- fix the tables above")


def _clip(x: float) -> float:
    return round(max(0.0, min(1.0, x)), 3)


# ---------------------------------------------------------------------------------------------------
# (2) Construction -- per the metric sheet's (b). Only ENVELOPE axes move; TIMBRE axes held fixed.
# ---------------------------------------------------------------------------------------------------

def build_string(key: str, fixed: dict) -> tuple[dict, dict, dict, str]:
    arche = _archetype(key)
    peak = dict(fixed)
    onset, tail = dict(fixed), dict(fixed)

    if arche in ("bed", "bed_like"):
        onset["energy"] = _clip(peak["energy"] - 0.08)
        onset["brightness"] = _clip(peak["brightness"] - 0.03)
        onset["onset"] = _clip(peak["onset"] - 0.04)
        tail["energy"] = _clip(peak["energy"] - 0.06)
        tail["brightness"] = _clip(peak["brightness"] - 0.02)
        tail["onset"] = _clip(peak["onset"] - 0.03)
        why = "bed: flat body -- onset/tail nudge only the loudness envelope; peak holds the registered point"
        if arche == "bed_like":
            why = "bed-like (continuity>=0.60, not in the curated _BEDS set): " + why

    elif arche == "call":
        continuity = peak["continuity"]
        scale = 1.0 - 0.4 * continuity
        onset["brightness"] = _clip(peak["brightness"] - 0.12 * scale)
        onset["energy"] = _clip(peak["energy"] - 0.15 * scale)
        onset["onset"] = _clip(peak["onset"] - 0.10 * scale)
        tail["brightness"] = _clip(peak["brightness"] - 0.15 * scale)
        tail["energy"] = _clip(peak["energy"] - 0.18 * scale)
        tail["onset"] = _clip(peak["onset"] - 0.12 * scale)
        why = f"call: builds into voice, full brightness/energy/onset-density at peak, falls away at tail (fade scaled x{scale:.2f} by its own continuity)"

    elif arche == "wingbeat":
        onset["brightness"] = _clip(peak["brightness"] - 0.05)
        onset["energy"] = _clip(peak["energy"] - 0.15)
        onset["onset"] = _clip(peak["onset"] - 0.06)
        # J-2067: tail used to equal onset (identical offsets) -> nearest_vertex ties. The recede decays further
        # than the approach built: a distinct, lower decay point.
        tail["brightness"] = _clip(peak["brightness"] - 0.12)
        tail["energy"] = _clip(peak["energy"] - 0.30)
        tail["onset"] = _clip(peak["onset"] - 0.12)
        why = "wingbeat: approach/recede arc -- quieter at onset, receding to a distinctly lower tail, peak is the close pass"

    elif arche == "thump":
        # J-2067: onset used to equal peak -> nearest_vertex ties. The strike is near-instantaneous but its
        # onset vertex is the pre-strike contact: a little quieter/softer than the peak, distinct from it.
        onset["brightness"] = _clip(peak["brightness"] - 0.04)
        onset["energy"] = _clip(peak["energy"] - 0.12)
        onset["onset"] = _clip(peak["onset"] - 0.08)
        tail["brightness"] = _clip(peak["brightness"] - 0.10)
        tail["energy"] = _clip(peak["energy"] - 0.30)
        tail["onset"] = _clip(peak["onset"] - 0.45)
        why = "thump: near-instantaneous strike, onset a distinct slightly-softer pre-strike contact, sharp decay to near-silence at tail"

    else:
        raise AssertionError(arche)

    snippet = _SNIPPETS.get(key)
    rationale = f"{arche}: {snippet} -- {why}" if snippet else why
    return onset, peak, tail, rationale


def build_all() -> dict:
    keys = sorted(ss._SOUNDS)
    # J-2475 (2026-10-28): the metric sheet's own count was 70 at the dry run; the registry grows by section under
    # D-0500 (sound_world_expansion §2-§5), so the invariant is kept as what it always meant -- EVERY registered key
    # classified into exactly one archetype, and no archetype key left unregistered -- rather than as a magic number.
    classified = set(ss._BEDS) | _BED_LIKE | _CALL | _WINGBEAT | _THUMP
    unclassified = sorted(set(keys) - classified)
    stale = sorted((classified - set(ss._BEDS)) - set(keys))
    if unclassified or stale:
        raise AssertionError(f"registry/archetype mismatch -- unclassified {unclassified}, stale {stale}: fix the tables above")
    out = {}
    arche_counts: dict[str, int] = {}
    for key in keys:
        entry = ss._SOUNDS[key]
        fixed = dict(entry["coords"])
        onset, peak, tail, rationale = build_string(key, fixed)
        arche = _archetype(key)
        arche_counts[arche] = arche_counts.get(arche, 0) + 1
        out[key] = {
            "object": entry["object"],
            "archetype": arche,
            "fixed_point": fixed,
            "string": {"onset": onset, "peak": peak, "tail": tail},
            "rationale": rationale,
        }
    # J-2475: expected counts are the tables' own sizes (the 70-key dry run was bed 13 / bed_like 11 / call 21 /
    # wingbeat 2 / thump 23; §2 adds bed_like +1, call +2, thump +2) -- a key in two tables still fails here.
    expected = {"bed": len(set(ss._BEDS) & set(keys)), "bed_like": len(_BED_LIKE - set(ss._BEDS)),
                "call": len(_CALL), "wingbeat": len(_WINGBEAT), "thump": len(_THUMP)}
    if arche_counts != expected:
        raise AssertionError(f"archetype counts {arche_counts} != expected {expected} -- metric sheet (b) is now wrong, fix it or this table")
    return out


# ---------------------------------------------------------------------------------------------------
# (3) Realness test -- reuses core.soundscape.distance()/neighbours() via a temporary, restored-after
# substitution of _SOUNDS with the constructed PEAK points. Nothing written to disk by this step.
# ---------------------------------------------------------------------------------------------------

def run_realness(strings: dict) -> dict:
    peak_sounds = {k: {"object": v["object"], "coords": v["string"]["peak"]} for k, v in strings.items()}
    orig = ss._SOUNDS
    ss._SOUNDS = peak_sounds
    try:
        per_key = {}
        n_pass = 0
        for key in sorted(strings):
            nbrs = ss.neighbours(key, k=1)  # reuses soundscape's own Euclidean distance, unmodified
            if not nbrs:
                per_key[key] = {"pass": False, "reason": "no neighbour found (registry too small?)"}
                continue
            nb_key, dist = nbrs[0]
            a, b = peak_sounds[key]["coords"], peak_sounds[nb_key]["coords"]
            timbre_deltas = {ax: round(abs(a[ax] - b[ax]), 3) for ax in TIMBRE}
            n_agree = sum(1 for ax in TIMBRE if timbre_deltas[ax] <= 0.25)
            verdict = n_agree >= 2
            if verdict:
                n_pass += 1
            per_key[key] = {
                "pass": verdict,
                "nearest_neighbour": nb_key,
                "neighbour_object": peak_sounds[nb_key]["object"],
                "same_object": peak_sounds[nb_key]["object"] == peak_sounds[key]["object"],
                "distance_6ax": dist,
                "timbre_deltas": timbre_deltas,
                "timbre_axes_agreeing": n_agree,
            }
        return {"per_key": per_key, "n_pass": n_pass, "n_total": len(strings),
                "pass_rate": round(n_pass / len(strings), 4)}
    finally:
        ss._SOUNDS = orig  # restore -- this script never leaves the live module state changed


def run_peak_proximity(strings: dict) -> dict:
    per_key = {}
    n_within = 0
    for key, v in strings.items():
        fixed, peak = v["fixed_point"], v["string"]["peak"]
        offset = round(sum((fixed[ax] - peak[ax]) ** 2 for ax in AXES) ** 0.5, 4)
        within = offset <= 0.15
        if within:
            n_within += 1
        per_key[key] = {"offset": offset, "within_0.15": within}
    return {"per_key": per_key, "n_within": n_within, "n_total": len(strings),
            "within_rate": round(n_within / len(strings), 4)}


def main(argv=None):
    # J-2487 (2026-10-30): output paths are arguments. The lab result is written to a NEW dated file by default so a
    # regeneration never overwrites the historical J-1473 dry run (docs/lab/strings_sheets_phase1_dryrun_2026-09-28.json);
    # --sidecar-out lets a regeneration be staged and diffed off the live data/ copy while Du runs.
    import argparse
    ap = argparse.ArgumentParser(description="strings_and_sheets Phase 1 constructed strings + realness test")
    ap.add_argument("--sidecar-out", default=str(_ROOT / "data" / "sound_strings_constructed.json"))
    ap.add_argument("--lab-out", default=str(_ROOT / "docs" / "lab" /
                                              f"strings_sheets_phase1_dryrun_{time.strftime('%Y-%m-%d')}.json"))
    args = ap.parse_args(argv)
    strings = build_all()

    sidecar_path = Path(args.sidecar_out)
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(strings, f, indent=2, ensure_ascii=False)
    print(f"[written] {sidecar_path} ({len(strings)} keys)")

    realness = run_realness(strings)
    proximity = run_peak_proximity(strings)

    result = {
        "job": "J-1473", "ts": round(time.time(), 1),
        "n_keys": len(strings),
        "realness_test": realness,
        "peak_proximity": proximity,
        "bars": {
            "realness_pass_rate_ge_0.80": realness["pass_rate"] >= 0.80,
            "peak_within_rate_ge_0.70": proximity["within_rate"] >= 0.70,
        },
    }
    out_path = Path(args.lab_out)
    if out_path.name == "strings_sheets_phase1_dryrun_2026-09-28.json":
        raise SystemExit("refusing to overwrite the historical J-1473 dry-run result; pass a new --lab-out")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[written] {out_path}")
    print(json.dumps({"realness_pass_rate": realness["pass_rate"],
                       "peak_within_rate": proximity["within_rate"],
                       "bars": result["bars"]}, indent=2))


if __name__ == "__main__":
    main()
