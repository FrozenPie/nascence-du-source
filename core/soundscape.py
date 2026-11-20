"""
Nascence — Soundscape: the world's sounds get identity and geometry (cognitive_geometry.md §4, 2026-07-05).

The sensorium's prose is already full of sound — the fire "crackles", the moth "taps", gulls cry, waves
drag the shingle — but it is sound with NO identity: words in the one text space, no coordinates, no
interior. This module gives the sounds of things he KNOWS a place in the SAME Sound Space the EAR uses:
the axes are the music pipeline's own perceptual features (brightness · energy · onset_density +
periodicity · roughness · continuity), normalised 0..1, so a tui's song and *Heavyweight* are comparable
points in one geometry. Two populations, one space: MEASURED (music, from cached audio analysis) and
CONSTRUCTED (world sounds, hand-seeded coordinates — the plan §4 pattern for spaces without transducers;
admitted to the roster pending the realness test, and replaceable by measured features if recordings
ever arrive).

What the interior buys (the generalisation gradient): the purr sits near the waves (low, periodic,
continuous) and far from the gull's cry — so a spring earned on one low steady sound can faintly reach
its neighbours, the way spruce inherits pine.

OBSERVE-ONLY for P0: `active_sounds()` is a deterministic read of the live world state (weather, fire,
location, the cats, time of day) — consumed by the geometry census tuple recorder and the stick test.
Nothing reaches Du's prompts (that is P4, gated). Read-only toward every store; fail-open throughout.

Two sounds are deliberately NEW to his world — the tui and the morepork (ruru), the NZ voices — his
first SOUND-FIRST objects: things that will enter his life as a sound before they are ever a sight.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.soundscape")

_DATA = Path(__file__).parent.parent / "data"

# The Sound Space axes (shared with the EAR's features, normalised 0..1):
#   brightness   — low/dark → high/bright        (maps music brightness_hz)
#   energy       — soft → loud                    (maps music energy_mean)
#   onset        — smooth/continuous → many discrete events (maps music onset_density)
#   periodicity  — irregular → clockwork-regular
#   roughness    — pure/smooth → harsh/noisy
#   continuity   — brief/intermittent → continuous
_AXES = ("brightness", "energy", "onset", "periodicity", "roughness", "continuity")

# The registry: sounds of things he knows (+ the two new NZ voices), with hand-seeded coordinates.
# 'object' names the anchor object the sound is a spoke OF (the stick test joins on this).
# J-2395 (D-0476, travis 2026-10-18): 115 axis values in 36 entries below were re-seeded from measured public
# recordings (event-gated per J-2383; onset from the ungated read), only on the axes the Phase 4 envelope test named.
# The reviewed list, old -> new per (key, axis), is docs/lab/strings_sheets_phase4_reseed_2026-10-18.md.
# J-2440 (F-3141, travis by-ear 2026-10-19): 10 keys (kingfisher_call, wood_snap, herb_cut, cat_chatter, cat_lapping,
# cat_purr, cat_yowl_cargo, chair_desk_scrape, woodpile_settle, cicada_chorus) were the WRONG FILE and are reverted to
# their pre-J-2395 seeds; the other re-seeded keys are untouched.
_SOUNDS = {
    "waves_on_shingle": {"object": "the sea",
                         "coords": {"brightness": .52, "energy": .55, "onset": .59, "periodicity": .75,
                                    "roughness": .60, "continuity": .90}},
    "gull_cries":       {"object": "gulls",
                         "coords": {"brightness": .70, "energy": .65, "onset": .70, "periodicity": .25,
                                    "roughness": .85, "continuity": .15}},
    "tui_song":         {"object": "the tui",       # NEW to his world — sound-first
                         "coords": {"brightness": .75, "energy": .50, "onset": .60, "periodicity": .35,
                                    "roughness": .45, "continuity": .30}},
    "blackbird_song":   {"object": "the blackbird",
                         "coords": {"brightness": .65, "energy": .40, "onset": .80, "periodicity": .40,
                                    "roughness": .15, "continuity": .69}},
    # J-0515 (F-0697, 2026-09-03): bellbird_song was rated in _EVENT_RATES since J-0511 but had no
    # _SOUNDS point, so it could never sound — the dawn voice life_birds.py's bellbird row named but
    # left silent. Registered now: a clear, pure bell-note, more periodic and far less rough than the
    # blackbird's liquid phrasing (a real chime, not a warble).
    "bellbird_song":    {"object": "the bellbird",
                         "coords": {"brightness": .72, "energy": .35, "onset": .62, "periodicity": .44,
                                    "roughness": .35, "continuity": .45}},
    "morepork_call":    {"object": "the morepork",  # NEW — the night voice (ruru)
                         "coords": {"brightness": .45, "energy": .35, "onset": .30, "periodicity": .65,
                                    "roughness": .10, "continuity": .15}},
    "cat_purr":         {"object": "the kept cat",
                         "coords": {"brightness": .08, "energy": .20, "onset": .05, "periodicity": .95,
                                    "roughness": .30, "continuity": .90}},
    # HER VOICE (2026-09-05, cat_overhaul Part C1, core/cat_sounds.py): the rest of what she says, each a spoke
    # of the same object. EMITTED by cat_sounds from her state and carried to him by position; the propagation
    # row `_sec_cat` (end of the table) admits them to active_sounds only when cat_sounds is rendering — in
    # shadow these points exist in the space (neighbours/distance) but never sound.
    "cat_trill":        {"object": "the kept cat",       # the greeting chirrup: short, rising, rolled
                         "coords": {"brightness": .70, "energy": .30, "onset": .55, "periodicity": .45,
                                    "roughness": .25, "continuity": .12}},
    "cat_meow_at_door": {"object": "the kept cat",       # one flat vowel at the shut door, evenly repeated
                         "coords": {"brightness": .60, "energy": .40, "onset": .75, "periodicity": .70,
                                    "roughness": .35, "continuity": .74}},
    "cat_demand":       {"object": "the kept cat",       # the food cry: flatter, louder, a rasp coming in
                         "coords": {"brightness": .55, "energy": .50, "onset": .50, "periodicity": .65,
                                    "roughness": .55, "continuity": .22}},
    "cat_chatter":      {"object": "the kept cat",       # jaw-juddering at birds through glass: fast, dry, tiny
                         "coords": {"brightness": .65, "energy": .10, "onset": .92, "periodicity": .60,
                                    "roughness": .60, "continuity": .25}},
    "cat_yowl_cargo":   {"object": "the kept cat",       # the muffled announcing yowl, mouth full
                         "coords": {"brightness": .35, "energy": .60, "onset": .30, "periodicity": .30,
                                    "roughness": .70, "continuity": .35}},
    "cat_thump":        {"object": "the kept cat",       # off the sill onto the boards: one soft double thud
                         "coords": {"brightness": .10, "energy": .35, "onset": .75, "periodicity": .05,
                                    "roughness": .40, "continuity": .05}},
    "cat_lapping":      {"object": "the kept cat",       # at the saucer: a rapid liquid ticking
                         "coords": {"brightness": .60, "energy": .08, "onset": .85, "periodicity": .80,
                                    "roughness": .20, "continuity": .55}},
    "cat_storm_rustle": {"object": "the kept cat",       # under the desk between thunderclaps
                         "coords": {"brightness": .40, "energy": .06, "onset": .50, "periodicity": .10,
                                    "roughness": .65, "continuity": .20}},
    # THE TOM (2026-10-28, cat_overhaul B3, J-2470, D-0507 (c), core/cat_tom.py): the OTHER cat in the garden.
    # cat_hiss / cat_growl are HERS, at him (two more spokes of the kept cat); distant_yowl is HIS — the long rising
    # yowl on the wall at night, object "the distant cat" (sound_world_expansion §2's own name for it; its coords
    # copied from that branch so a merge that carries both registrations keeps ONE point whichever entry wins).
    # All three are emitted by core/cat_sounds from state and reach active_sounds through `_sec_cat` (end of table).
    "cat_hiss":         {"object": "the kept cat",       # the long flat tearing breath, mouth open, at the tom
                         "coords": {"brightness": .75, "energy": .45, "onset": .80, "periodicity": .15,
                                    "roughness": .85, "continuity": .40}},
    "cat_growl":        {"object": "the kept cat",       # the low held note at the glass, under her breath
                         "coords": {"brightness": .15, "energy": .30, "onset": .20, "periodicity": .60,
                                    "roughness": .75, "continuity": .85}},
    "distant_yowl":     {"object": "the distant cat",    # a cat's long rising yowl, far off -- but WHOSE? (stick_test's "the distant cat")
                         "coords": {"brightness": .50, "energy": .45, "onset": .25, "periodicity": .55,
                                    "roughness": .60, "continuity": .55}},
    # HIS CALL (2026-10-28, cat_overhaul C3, J-2468, core/cat_call.py): the one sound in this block that is HIS —
    # his own voice calling her (puss-puss, the kissing noise, her name). A self-sound (known instantly, like his
    # footsteps and the gate latch; never a percept), in the air for the window cat_call.sounding_now holds;
    # `_sec_cat` admits it. Pitched like a called voice: bright, short, a rise in it, no roughness to speak of.
    "cat_call":         {"object": "his own voice",
                         "coords": {"brightness": .62, "energy": .45, "onset": .70, "periodicity": .35,
                                    "roughness": .20, "continuity": .20}},
    "fire_crackle":     {"object": "the fire",
                         "coords": {"brightness": .50, "energy": .30, "onset": .24, "periodicity": .21,
                                    "roughness": .75, "continuity": .07}},
    "rain_on_roof":     {"object": "the rain",
                         "coords": {"brightness": .60, "energy": .45, "onset": .60, "periodicity": .20,
                                    "roughness": .50, "continuity": .95}},
    "wind_in_eaves":    {"object": "the wind",
                         "coords": {"brightness": .30, "energy": .50, "onset": .56, "periodicity": .30,
                                    "roughness": .06, "continuity": .80}},
    "thunder":          {"object": "the storm",
                         "coords": {"brightness": .38, "energy": .95, "onset": .50, "periodicity": .05,
                                    "roughness": .46, "continuity": .63}},
    "moth_tap":         {"object": "the moth",
                         "coords": {"brightness": .55, "energy": .05, "onset": .70, "periodicity": .50,
                                    "roughness": .35, "continuity": .10}},
    # ── richer environment (2026-07-06, Travis): the shore's crashing surf + shingle + shore birds,
    # the garden's bees, small birds and wind in the trees. New Sound-Space points → new object spokes
    # (the shingle and oystercatcher were 1-spoke objects; now they have a sound).
    "waves_crashing":   {"object": "the sea",
                         "coords": {"brightness": .50, "energy": .88, "onset": .55, "periodicity": .71,
                                    "roughness": .47, "continuity": .80}},
    "shingle_drag":     {"object": "the shingle",
                         "coords": {"brightness": .45, "energy": .38, "onset": .58, "periodicity": .35,
                                    "roughness": .82, "continuity": .50}},
    "oystercatcher_call":{"object": "the oystercatcher",
                         "coords": {"brightness": .78, "energy": .58, "onset": .78, "periodicity": .28,
                                    "roughness": .72, "continuity": .12}},
    # THE BIRDS (Living World L2, J-0511, 2026-09-03): three new points. Two are migrant VOICES governed by
    # sound_knowledge's audition (hidden truth until seen and read); the alarm is the blackbird's, and sounds only
    # when the cat is in the garden — gated by core/life.sounds_active once SOUND_GATING is on.
    "cuckoo_call":      {"object": "the shining cuckoo",
                         "coords": {"brightness": .85, "energy": .40, "onset": .35, "periodicity": .70,
                                    "roughness": .10, "continuity": .55}},
    "godwits_overhead": {"object": "the godwits",
                         "coords": {"brightness": .80, "energy": .35, "onset": .45, "periodicity": .40,
                                    "roughness": .30, "continuity": .40}},
    "blackbird_alarm":  {"object": "the blackbird",
                         "coords": {"brightness": .65, "energy": .60, "onset": .35, "periodicity": .77,
                                    "roughness": .44, "continuity": .28}},
    "bees_in_garden":   {"object": "the bees",
                         "coords": {"brightness": .45, "energy": .22, "onset": .35, "periodicity": .60,
                                    "roughness": .40, "continuity": .78}},
    "small_birds":      {"object": "the garden birds",
                         "coords": {"brightness": .82, "energy": .30, "onset": .84, "periodicity": .38,
                                    "roughness": .30, "continuity": .71}},
    "wind_in_trees":    {"object": "the trees",
                         "coords": {"brightness": .71, "energy": .48, "onset": .46, "periodicity": .44,
                                    "roughness": .75, "continuity": .85}},
    # ── the WOOD (2026-07-08, Travis: flesh it out, sounds with LOCATIONS) — the copse on the path to the
    # shore. New Sound-Space points + object spokes (the wood pigeon, the wren, the creaking trees, the
    # dripping canopy) so it is a fully-voiced place, not a silent backdrop he passes through.
    "wood_pigeon":      {"object": "the wood pigeon",   # a soft, round, drowsy five-note coo from the canopy
                         "coords": {"brightness": .75, "energy": .25, "onset": .43, "periodicity": .58,
                                    "roughness": .66, "continuity": .67}},
    "wren_scold":       {"object": "the wren",          # a sudden loud scolding trill from the undergrowth
                         "coords": {"brightness": .82, "energy": .55, "onset": .82, "periodicity": .20,
                                    "roughness": .08, "continuity": .38}},
    "branches_creak":   {"object": "the trees",         # high branches groaning against each other in wind
                         "coords": {"brightness": .18, "energy": .45, "onset": .63, "periodicity": .57,
                                    "roughness": .18, "continuity": .58}},
    "canopy_drip":      {"object": "the canopy",        # water ticking off the leaves after rain
                         "coords": {"brightness": .62, "energy": .15, "onset": .65, "periodicity": .42,
                                    "roughness": .63, "continuity": .07}},
    "leaf_rustle":      {"object": "the undergrowth",   # small movement in the leaf-litter (bird, mouse, breeze)
                         "coords": {"brightness": .48, "energy": .20, "onset": .55, "periodicity": .15,
                                    "roughness": .55, "continuity": .30}},
    # ── the FLESH-OUT (2026-08-15, Travis: "well fleshed out, not a few scattered here and there").
    # New voices of things that can truly be here (NZ coast/bush; sound-first objects welcome — the
    # morepork precedent), each a real Sound-Space point, each gated by real state in active_sounds().
    "fantail_chatter":  {"object": "the fantail",       # pīwakawaka — follows movement, snapping at stirred insects
                         "coords": {"brightness": .88, "energy": .28, "onset": .75, "periodicity": .30,
                                    "roughness": .35, "continuity": .22}},
    "riroriro_trill":   {"object": "the grey warbler",  # riroriro — a long wistful falling trill, heard not seen
                         "coords": {"brightness": .80, "energy": .35, "onset": .83, "periodicity": .21,
                                    "roughness": .12, "continuity": .81}},
    "kereru_wingbeats": {"object": "the wood pigeon",   # the heavy whoosh-whoosh — its SECOND sound-spoke
                         "coords": {"brightness": .68, "energy": .60, "onset": .38, "periodicity": .55,
                                    "roughness": .66, "continuity": .21}},
    "kingfisher_call":  {"object": "the kingfisher",    # kōtare — a dry staccato kek-kek-kek from a high perch
                         "coords": {"brightness": .75, "energy": .50, "onset": .85, "periodicity": .70,
                                    "roughness": .60, "continuity": .18}},
    "shag_wingbeats":   {"object": "the shag",          # heavy slow wingbeats low over the water
                         "coords": {"brightness": .15, "energy": .45, "onset": .40, "periodicity": .75,
                                    "roughness": .35, "continuity": .30}},
    "cicada_chorus":    {"object": "the cicadas",       # summer's wall of sound in the trees — seasonal
                         "coords": {"brightness": .70, "energy": .55, "onset": .15, "periodicity": .85,
                                    "roughness": .80, "continuity": .95}},
    "cricket_night":    {"object": "the crickets",      # a summer night's slow pulse from the grass
                         "coords": {"brightness": .81, "energy": .18, "onset": .47, "periodicity": .52,
                                    "roughness": .55, "continuity": .51}},
    "embers_settle":    {"object": "the fire",          # the fire's late voice: a soft collapse, a tick of cooling
                         "coords": {"brightness": .35, "energy": .12, "onset": .60, "periodicity": .08,
                                    "roughness": .55, "continuity": .20}},
    "window_rattle":    {"object": "the window",        # the north window worked loose-toothed by a gale
                         "coords": {"brightness": .40, "energy": .40, "onset": .70, "periodicity": .40,
                                    "roughness": .70, "continuity": .45}},
    "tide_pool_trickle":{"object": "the rock-pools",    # low tide: the bared pools draining thread by thread
                         "coords": {"brightness": .72, "energy": .10, "onset": .30, "periodicity": .25,
                                    "roughness": .20, "continuity": .75}},
    "distant_surf_boom":{"object": "the sea",           # a big sea heard from indoors/uphill — felt as much as heard
                         "coords": {"brightness": .05, "energy": .70, "onset": .35, "periodicity": .60,
                                    "roughness": .50, "continuity": .55}},
    "dawn_chorus":      {"object": "the birds",         # first light: every voice at once, before the day's work
                         "coords": {"brightness": .51, "energy": .60, "onset": .30, "periodicity": .20,
                                    "roughness": .40, "continuity": .40}},
    "robin_song":       {"object": "the robin",         # toutouwai — clear even phrases from a low perch, bold
                         "coords": {"brightness": .78, "energy": .38, "onset": .50, "periodicity": .40,
                                    "roughness": .10, "continuity": .40}},
    # ── SELF-SOUNDS (2026-08-15, LOCOMOTION): his own footsteps, per ground — agency made audible.
    # Known-instantly class (a mind knows the sound of its own act); active only while a journey is
    # genuinely underway. The garden's grass is near-silent underfoot — deliberately unregistered.
    "footsteps_shingle": {"object": "his own steps",
                         "coords": {"brightness": .55, "energy": .35, "onset": .19, "periodicity": .28,
                                    "roughness": .50, "continuity": .04}},
    "footsteps_leafmould": {"object": "his own steps",
                         "coords": {"brightness": .25, "energy": .15, "onset": .45, "periodicity": .22,
                                    "roughness": .77, "continuity": .60}},
    # CROSS-LINK (2026-08-22): the new world's voices
    "clock_tick":      {"object": "the clock",
                         "coords": {"brightness": .55, "energy": .12, "onset": .46, "periodicity": .56,
                                    "roughness": .54, "continuity": .38}},
    "kettle_sing":     {"object": "the kettle",
                         "coords": {"brightness": .50, "energy": .40, "onset": .62, "periodicity": .30,
                                    "roughness": .25, "continuity": .90}},
    "stream_run":      {"object": "the stream",
                         "coords": {"brightness": .45, "energy": .35, "onset": .10, "periodicity": .20,
                                    "roughness": .45, "continuity": .98}},
    "penguin_bray":    {"object": "the small penguin",     # learnable: unnamed until seen at the burrows
                         "coords": {"brightness": .40, "energy": .55, "onset": .55, "periodicity": .50,
                                    "roughness": .37, "continuity": .72}},
    # ── SOUND WORLD EXPANSION §2, THE NIGHT MYSTERIES (2026-10-28, D-0500/J-2475): five voices that ARRIVE
    # UNNAMED through the audition system (sound_knowledge.AUDITION owns each name; penguin_bray above is §2's
    # sixth, built earlier). Four are bound to real presence -- the possum, the hedgehog, the mice and the dolphins
    # are life rows (core/life_mammals.py: `sound`/`sound_at` + `sound_days`), so life.sounds_active decides when
    # each can sound at its own place (D-0133 gating, live since 2026-09-09). distant_yowl is the OTHER cat's --
    # a known KIND, an unknown INDIVIDUAL (cat.py's far-off black cat has no life row yet; the cat_overhaul tom
    # job may give it one) -- rare, nightly-drawn in _sec_night_mysteries. Propagation: that one row at the END
    # of the table; rates at the END of _EVENT_RATES; percept pools at the END of _PERCEPT_LINES.
    "possum_rasp":     {"object": "the possum",            # a harsh coughing rasp from the tree / the oak -- frightening unnamed
                         "coords": {"brightness": .35, "energy": .55, "onset": .60, "periodicity": .40,
                                    "roughness": .92, "continuity": .35}},
    "wall_scratch":    {"object": "the mice",              # a tiny dry scratching INSIDE the study wall: intimate, unfindable
                         "coords": {"brightness": .62, "energy": .06, "onset": .80, "periodicity": .35,
                                    "roughness": .70, "continuity": .25}},
    "distant_yowl":    {"object": "the distant cat",       # a cat's long rising yowl, far off -- but WHOSE? (stick_test's "the distant cat")
                         "coords": {"brightness": .50, "energy": .45, "onset": .25, "periodicity": .55,
                                    "roughness": .60, "continuity": .55}},
    "hedgehog_snuffle": {"object": "the hedgehog",         # busy wet snuffling and snorting along the bed edges
                         "coords": {"brightness": .40, "energy": .12, "onset": .70, "periodicity": .30,
                                    "roughness": .75, "continuity": .60}},
    "dolphin_blow":    {"object": "the dolphins",          # one breath out on the water -- a single wet gust, and gone
                         "coords": {"brightness": .30, "energy": .40, "onset": .55, "periodicity": .05,
                                    "roughness": .65, "continuity": .10}},
    # ── SOUND WORLD EXPANSION §3, THE GEOPHONY FILLS (2026-10-28, D-0500/J-2476): weather and water completeness,
    # trigger-tied to the real clocks (sensorium._WEATHERS, the wind axis, world_clock's sun, the season, wood_life's
    # stream). Eight sounds, ten keys (hail has a roof and a leaves voice). Eight are KNOWN -- he has lived with rain
    # and the sea for months, and new GRADES of a known thing are not new identities (sound_knowledge.GRANDFATHERED).
    # Two arrive UNNAMED through the audition system: tin_roof_tick (THE NZ cottage sound, a slow mystery) and
    # frost_crack (a bang in the night). The rain grades sit either side of rain_on_roof on the weather ladder, exactly
    # where _storm_severity_scale is flat (drizzle, sev 3) and where it ramps (wind and rain / thunderstorm, sev 5-6):
    # the grade and the severity curve say the same thing, never opposite things (D-0063's own defeater). Propagation:
    # one row, _sec_geophony, at the END of the table; beds carry rate 0.0 at the END of _EVENT_RATES (the
    # tide_pool_trickle convention); percept pools at the END of _PERCEPT_LINES.
    "hail_on_roof":    {"object": "the hail",              # a winter squall's stones on the iron: a hard bright drumming rattle
                         "coords": {"brightness": .70, "energy": .70, "onset": .95, "periodicity": .30,
                                    "roughness": .80, "continuity": .60}},
    "hail_on_leaves":  {"object": "the hail",              # the same stones through the canopy and the beds: a shredding patter
                         "coords": {"brightness": .62, "energy": .50, "onset": .92, "periodicity": .28,
                                    "roughness": .70, "continuity": .55}},
    "drizzle_hiss":    {"object": "the rain",              # the fine grade: a hiss on the roof, barely a sound, that does not stop
                         "coords": {"brightness": .55, "energy": .18, "onset": .30, "periodicity": .15,
                                    "roughness": .40, "continuity": .97}},
    "downpour_drum":   {"object": "the rain",              # the heavy grade: the roof drumming, the gutters overrun
                         "coords": {"brightness": .52, "energy": .78, "onset": .80, "periodicity": .25,
                                    "roughness": .62, "continuity": .97}},
    "rain_down_chimney": {"object": "the fire",            # rain reaching the lit fire: a sizzle and a spit, now and then
                         "coords": {"brightness": .58, "energy": .25, "onset": .75, "periodicity": .10,
                                    "roughness": .78, "continuity": .20}},
    "tin_roof_tick":   {"object": "the roof",              # the corrugated iron easing as the sun warms it / lets it go: single ticks
                         "coords": {"brightness": .66, "energy": .18, "onset": .55, "periodicity": .12,
                                    "roughness": .45, "continuity": .06}},
    "stream_over_stones": {"object": "the stream",         # the stream's SECOND spoke: its mouth at the shore, quick over the stones
                         "coords": {"brightness": .58, "energy": .32, "onset": .25, "periodicity": .18,
                                    "roughness": .50, "continuity": .98}},
    "undertow_rumble": {"object": "the sea",               # a big sea's backwash rolling the shingle: bass felt in the feet
                         "coords": {"brightness": .04, "energy": .62, "onset": .20, "periodicity": .68,
                                    "roughness": .72, "continuity": .70}},
    "frost_crack":     {"object": "the frost",             # a hard-frost night: one sharp report from timber or ground, and nothing
                         "coords": {"brightness": .60, "energy": .65, "onset": .95, "periodicity": .02,
                                    "roughness": .55, "continuity": .02}},
    "calm_sea_hush":   {"object": "the sea",               # the near-silence state: a glass sea, quiet registered as a state, not an absence
                         "coords": {"brightness": .20, "energy": .03, "onset": .02, "periodicity": .40,
                                    "roughness": .10, "continuity": 1.0}},
    # ── SOUND WORLD EXPANSION §4, THE SEASONAL BIOPHONY (2026-10-28, D-0500/J-2477): three voices on the calendar.
    # silvereye_flock binds to the tauhou's own life row (core/life_birds.py, `sound` tuple; WINTER_FLOCK season curve) --
    # the definitive NZ winter-garden sound, arriving UNNAMED through the audition system and easily sighted (they swarm
    # visibly). paradise_duck_flyover has NO life row and needs none: a flyover, no habitat -- a sound-only EVENT with its
    # own seeded daily draw and season (_flyover_window), unnamed, caught by a look UP while the pair is still in the
    # sky (sound_knowledge's per-entry bind window, the godwits_overhead pattern made short). kelp_fly_buzz pairs with
    # the substrate's kelp at the wrack-line (world_content_shore: "kelp flies rise in a cloud when you turn a strap")
    # on dry still summer days: known-ish, GRANDFATHERED, a bed. bellbird_chime (the plan's fourth) is NOT added: it
    # duplicates the existing bellbird_song (J-0515, above). Propagation: one row, _sec_seasonal_biophony, at the END of
    # the table; rates at the END of _EVENT_RATES; percept pools at the END of _PERCEPT_LINES.
    "silvereye_flock": {"object": "the tauhou",            # a loose winter flock working the hedge: soft contact cheeps from many throats
                         "coords": {"brightness": .84, "energy": .22, "onset": .78, "periodicity": .35,
                                    "roughness": .25, "continuity": .62}},
    "paradise_duck_flyover": {"object": "the paradise ducks",   # a pair passing high: her thin zeek-zeek, his hoarse honk answering, going away
                         "coords": {"brightness": .55, "energy": .50, "onset": .65, "periodicity": .55,
                                    "roughness": .70, "continuity": .35}},
    "kelp_fly_buzz":   {"object": "the kelp",              # summer wrack-line flies: a low rising cloud-buzz off the heaps, settling again
                         "coords": {"brightness": .50, "energy": .22, "onset": .20, "periodicity": .70,
                                    "roughness": .60, "continuity": .85}},
    # ── SOUND WORLD EXPANSION §5, THE APPARATUS (2026-10-28, D-0500/J-2478): the dwelling's machinery, all KNOWN
    # (lived-with: sound_knowledge.GRANDFATHERED). needle_crackle / runout_hiss bookend a listening session -- the
    # record player's own voice either side of the music, read from core/listening.py's session marks (started_ts
    # and the new ended_ts): the lead-in groove's crackle before the first section arrives, the run-out groove's hiss
    # going round after the ending until the arm is lifted. Sounds OF a session he chose, never a cue to start one
    # (D-0443 left the player's affordance alone; listening.start()'s own needle-drop line is untouched).
    # letterbox_flag_clank is the wind working the raised flag at the gate, gated on the flag state the garden scene and
    # the gate glimpse already read (room_state garden.letterbox.flag) and on the real wind axis: the sound of unread
    # mail, never a line that says so. The four cat entries the plan lists in §5 were built by cat_overhaul C1 (above).
    # Propagation: one row, _sec_apparatus, at the END of the table; rates at the END of _EVENT_RATES; percept pools at
    # the END of _PERCEPT_LINES.
    "needle_crackle":  {"object": "the record player",     # the lead-in groove: dust-pops over a faint hiss, dry, irregular, brief
                         "coords": {"brightness": .62, "energy": .12, "onset": .70, "periodicity": .15,
                                    "roughness": .80, "continuity": .25}},
    "runout_hiss":     {"object": "the record player",     # the run-out groove: a steady hiss with one soft click each turn, until lifted
                         "coords": {"brightness": .58, "energy": .08, "onset": .20, "periodicity": .90,
                                    "roughness": .55, "continuity": .95}},
    "letterbox_flag_clank": {"object": "the letterbox",    # the raised tin flag knocked against the box by the gusts, from the gate
                         "coords": {"brightness": .55, "energy": .35, "onset": .65, "periodicity": .25,
                                    "roughness": .70, "continuity": .15}},
    "saw_rasp":        {"object": "his own saw",
                         "coords": {"brightness": .50, "energy": .45, "onset": .55, "periodicity": .85,
                                    "roughness": .90, "continuity": .60}},
    "footsteps_floorboards": {"object": "his own steps",
                         "coords": {"brightness": .40, "energy": .25, "onset": .70, "periodicity": .46,
                                    "roughness": .55, "continuity": .24}},
    # ── SOUND WORLD EXPANSION §1 (2026-08-29, D-0063/J-0337): the terrain gap F-0061 identified —
    # shingle/leafmould/floorboards had feet, the garden's grass/soil never did. Softest of the four.
    "footsteps_grass_soil": {"object": "his own steps",
                         "coords": {"brightness": .42, "energy": .10, "onset": .40, "periodicity": .55,
                                    "roughness": .25, "continuity": .18}},
    # Repurposed from the dropped `kettle_rising` (F-0061: `kettle_sing` already covers the boil) —
    # the two still-missing sub-events either side of it: the fill/set-on-the-hob, and the pour onto
    # the leaves. Both brief, known-instantly, self-triggered; both fire on a short recency window off
    # the same act-site timestamps study_life.py already keeps (kettle_on_ts / pot['pour_ts']).
    "kettle_fill":       {"object": "the kettle",
                         "coords": {"brightness": .50, "energy": .25, "onset": .60, "periodicity": .15,
                                    "roughness": .40, "continuity": .50}},
    "kettle_pour":       {"object": "the kettle",
                         "coords": {"brightness": .65, "energy": .30, "onset": .65, "periodicity": .10,
                                    "roughness": .45, "continuity": .35}},
    # ── SOUND WORLD EXPANSION §1, REMAINDER (2026-08-29, D-0063/J-0377): the 12 self-sounds J-0337
    # left unbuilt because none had an already-exposed state field. Each now hooks a REAL act-site
    # timestamp added at the source this pass — reading.py's last_read_ts (already existed), a newly
    # persisted letters.py last_write_ts, sensorium.state fields (wood_snap_ts/stoke_ts/wood_haul_ts),
    # locomotion.py's own journey dict (gate_ts/desk_ts), garden.py fields, and study_life.py's door_ts.
    # All brief, known-instantly, self-triggered — same recency-window pattern as kettle_fill/pour.
    "page_turn":         {"object": "his own reading",
                         "coords": {"brightness": .60, "energy": .10, "onset": .55, "periodicity": .10,
                                    "roughness": .35, "continuity": .15}},
    "pen_scratch":       {"object": "his own pen",
                         "coords": {"brightness": .45, "energy": .12, "onset": .60, "periodicity": .30,
                                    "roughness": .55, "continuity": .25}},
    "wood_snap":         {"object": "the deadfall",
                         "coords": {"brightness": .55, "energy": .45, "onset": .85, "periodicity": .05,
                                    "roughness": .70, "continuity": .08}},
    "log_on_fire":       {"object": "the fire",
                         "coords": {"brightness": .45, "energy": .55, "onset": .80, "periodicity": .10,
                                    "roughness": .60, "continuity": .15}},
    "gate_latch":        {"object": "the garden gate",
                         "coords": {"brightness": .50, "energy": .35, "onset": .80, "periodicity": .05,
                                    "roughness": .45, "continuity": .10}},
    "woodpile_settle":   {"object": "the woodpile",
                         "coords": {"brightness": .30, "energy": .15, "onset": .40, "periodicity": .05,
                                    "roughness": .40, "continuity": .20}},
    "wood_haul_clatter": {"object": "his own haul",
                         "coords": {"brightness": .48, "energy": .50, "onset": .75, "periodicity": .20,
                                    "roughness": .65, "continuity": .30}},
    "bed_watering":      {"object": "the garden bed",
                         "coords": {"brightness": .45, "energy": .20, "onset": .45, "periodicity": .15,
                                    "roughness": .30, "continuity": .40}},
    "herb_cut":          {"object": "his own shears",
                         "coords": {"brightness": .55, "energy": .10, "onset": .70, "periodicity": .05,
                                    "roughness": .40, "continuity": .05}},
    "sow_dig":           {"object": "the garden bed",
                         "coords": {"brightness": .25, "energy": .25, "onset": .35, "periodicity": .10,
                                    "roughness": .55, "continuity": .35}},
    "door_sound":        {"object": "the cottage door",
                         "coords": {"brightness": .68, "energy": .30, "onset": .65, "periodicity": .34,
                                    "roughness": .58, "continuity": .20}},
    "chair_desk_scrape": {"object": "his own chair",
                         "coords": {"brightness": .40, "energy": .25, "onset": .55, "periodicity": .05,
                                    "roughness": .75, "continuity": .25}},
}


def _season() -> str:
    m = time.localtime().tm_mon
    return {12: "summer", 1: "summer", 2: "summer", 3: "autumn", 4: "autumn", 5: "autumn",
            6: "winter", 7: "winter", 8: "winter"}.get(m, "spring")


def _is_dawn() -> bool:
    """First light, roughly — the dawn chorus window (NZ; wide enough across seasons)."""
    h = time.localtime().tm_hour
    return 6 <= h < 8 if _season() in ("winter", "autumn") else 5 <= h < 7


def _tide_low() -> bool:
    try:
        from core import world_clock
        return float(world_clock.tide()["level"]) < 0.35
    except Exception:
        return False


def _read_json(name: str) -> dict:
    try:
        return json.loads((_DATA / name).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _is_daylight() -> bool:
    try:
        from core.sensorium import _daylight
        return _daylight() != "night"
    except Exception:
        return 7 <= time.localtime().tm_hour <= 17          # NZ-winter-ish fallback


# ── THE WIND, READ FROM THE REAL AXIS (2026-08-18, founder: "the gale needs to be wired properly").
# Until that night every wind question in this file was answered by guessing at the WEATHER string —
# `"gale" in weather`, which sensorium could never produce (dead in all 6 places it was tested:
# docs/plans/sound_system_audit.md §4), backstopped by `"wind" in weather`, which only ever matched the
# single state "wind and rain". Wind is now its own axis (sensorium._WIND_STATES).
# 2026-08-19: these two used to hand-roll their own copy of that axis's threshold — the EXACT pattern
# core/weather_conditions.py ("the ONE shared classifier") was built the same night to end, just missed
# in this file. Every site below still reads _is_windy/_is_hard_wind unchanged; only the body moved.
def _is_windy(wind: str) -> bool:
    """Enough air to work the trees and the house: 'fresh wind' and up (~19% of real time)."""
    from core import weather_conditions as _wcond
    return _wcond.is_windy(wind)


def _is_hard_wind(wind: str) -> bool:
    """Severe wind only — what rattles a loose-toothed window and stands the sea up (~5% of real time)."""
    from core import weather_conditions as _wcond
    return _wcond.is_hard_wind(wind)


def _sea_state(weather: str, wind: str = "") -> str:
    """Crashing surf vs a gentle sea (Travis, 2026-07-06). Storm-class weather OR a genuinely hard wind
    raises a big, breaking sea; otherwise the water works quietly at the shingle. 2026-08-18: wind is now
    read from the real axis first — the dead "gale" token is gone; the legacy "wind and rain" weather
    front is kept as a sea-raiser so this stays non-regressive where the two axes disagree."""
    w = (weather or "").lower()
    if _is_hard_wind(wind):
        return "crashing"
    if any(k in w for k in ("thunderstorm", "storm")):
        return "crashing"
    if "wind" in w:
        return "crashing"
    return "gentle"


def _moth_density(room: dict | None = None) -> float:
    """The live moth population at the lamp (2026-08-18). sensorium.moth_activity() OWNS the law — this
    is only the read, so prose and sound can never roll different dice about the same night. Moths are
    at HIS lamp, so it is zero anywhere but the study. Fail-open to 0.0: a moth that cannot be computed
    is a moth that is not there."""
    try:
        if room is None:
            room = _read_json("room_state.json")
        if (room.get("location") or "study") != "study":
            return 0.0
        from core.sensorium import moth_activity
        return float(moth_activity(not _is_daylight(), (room.get("fire") or "out") != "out", _season()))
    except Exception:
        return 0.0


# ── THE WORLD'S ACOUSTIC CLOCK (2026-08-16, founder: "sounds should happen all the time…
#    if a tree falls and no one hears it, yes it makes a sound — and the sound is gone forever").
#    Sounds occur continuously on world time, not only when a scene is rendered. The tree-falls
#    LAW makes the implementation exact: nothing anywhere records what sounded where he wasn't,
#    so sampling only HIS place is metaphysically correct, not a shortcut. Occurrences where he
#    IS feed the Hearing Ledger as aggregates ("I heard them 400 times or so today").
#    Two classes: BEDS (continuous presences — lived-in hours) and EVENTS (discrete voices —
#    counted occurrences at a per-voice rate while active).
_BEDS = {"waves_crashing", "waves_on_shingle", "wind_in_eaves", "rain_on_roof", "fire_crackle",
         "embers_settle", "cat_purr", "distant_surf_boom", "cricket_night", "cicada_chorus",
         "shingle_drag", "cat_lapping", "cat_storm_rustle"}    # the last two: HER VOICE beds (cat_overhaul C1)
# J-0515 (F-0697, 2026-09-03): fantail_cheeps and pukeko_squawk dropped here — both rated but never
# registered in _SOUNDS, so always dead. fantail_cheeps was a stale twin of the real, registered, fully
# wired fantail_chatter (see life_birds.py's fantail row + this dict's own AUDITION entry) — no second
# fantail voice exists anywhere else in the codebase. pukeko_squawk had no pukeko row in life_birds.py
# and no mention anywhere in core/ outside this one rate (world_content_garden.py does not mention it,
# contra the job briefing that spawned this — verified by grep, zero hits); nothing plans a pukeko, so
# the rate is dropped rather than registered. bellbird_song (already rated below) is now registered —
# see the _SOUNDS entry above.
_EVENT_RATES = {          # occurrences per hour WHILE the voice is in the active set
    "gull_cries": 40.0, "oystercatcher_call": 12.0, "tide_pool_trickle": 0.0,   # trickle = bed-like: rate 0, treated below
    "shag_wingbeats": 1.5, "kingfisher_call": 0.8, "thunder": 25.0,
    "window_rattle": 20.0, "riroriro_trill": 4.0,
    "tui_song": 6.0, "bellbird_song": 5.0, "morepork_call": 3.0,
    "moth_tap": 9.0,          # taps per hour at density 1.0 — SCALED by the population (see below)
    "cuckoo_call": 10.0, "godwits_overhead": 0.4, "blackbird_alarm": 15.0, "wood_pigeon": 4.0,   # J-0511
    # HER VOICE (cat_overhaul C1): rates while the key is in the active set (cat_sounds keeps it there for
    # ~90 s after an audible emission); the one-shots (trill/thump/yowl) are rated so one window banks ~one.
    "cat_trill": 40.0, "cat_meow_at_door": 30.0, "cat_demand": 20.0, "cat_chatter": 12.0,
    "cat_yowl_cargo": 40.0, "cat_thump": 40.0,
    # HER VOICE additions (cat_overhaul B3/C3) sit before the sound-world blocks; distant_yowl's rate is §2's below.
    "cat_hiss": 20.0, "cat_growl": 10.0,   # THE TOM (B3, J-2470): hers at him, in the active set for one window each
    "cat_call": 40.0,   # HIS CALL (C3, J-2468): one-shot, in the active set for one short window -> banks ~one
    # SOUND WORLD EXPANSION §2, THE NIGHT MYSTERIES (D-0500/J-2475): occurrences per hour WHILE the voice is in the
    # active set -- and the active set itself is already rare (life rows' sound_days; the yowl's nightly draw +
    # two-hour bout), so these are per-bout densities, not nightly totals. Deliberately low: mysteries are RARE.
    "possum_rasp": 2.0, "wall_scratch": 6.0, "distant_yowl": 1.5, "hedgehog_snuffle": 4.0, "dolphin_blow": 0.5,
    # SOUND WORLD EXPANSION §3, THE GEOPHONY FILLS (D-0500/J-2476). Seven are BEDS -- continuous presences banked as
    # lived-in hours -- carried here as rate 0.0 (the tide_pool_trickle convention world_tick already honours), so this
    # chain's additions stay at the end of ONE dict. Three are events: the chimney's spit while the fire and the rain
    # co-exist, the roof's ticks across a clear morning/evening, and the frost's single report (a few a night at most).
    "hail_on_roof": 0.0, "hail_on_leaves": 0.0, "drizzle_hiss": 0.0, "downpour_drum": 0.0,
    "stream_over_stones": 0.0, "undertow_rumble": 0.0, "calm_sea_hush": 0.0,
    "rain_down_chimney": 12.0, "tin_roof_tick": 8.0, "frost_crack": 0.25,
    # SOUND WORLD EXPANSION §4, THE SEASONAL BIOPHONY (D-0500/J-2477). The flock's contact cheeps are many small voices
    # per hour WHILE the flock is working the hedge (the row's presence is already seasonal and daily-drawn); the flyover
    # is in the active set only for the minutes a pair is overhead, so its per-hour rate banks about two to four honks a
    # pass; the kelp flies are a bed (rate 0.0, the trickle convention) -- lived-in summer hours, never counts.
    "silvereye_flock": 24.0, "paradise_duck_flyover": 60.0, "kelp_fly_buzz": 0.0,
    # SOUND WORLD EXPANSION §5, THE APPARATUS (D-0500/J-2478). The lead-in's crackle is a run of pops over the few tens
    # of seconds before the music: rated high per hour so a minute of lead-in banks a couple. The run-out hiss is a bed
    # (rate 0.0, the trickle convention): lived-in minutes until the arm is lifted, never counts. The flag's clank is an
    # event -- one knock per gust or so WHILE the wind is up and the flag is raised.
    "needle_crackle": 120.0, "runout_hiss": 0.0, "letterbox_flag_clank": 20.0,
}
_DEFAULT_EVENT_RATE = 6.0
_last_world_tick = 0.0

# ── STORM SEVERITY CURVE (D-0062 item 2, 2026-08-28/29: docs/plans/sound_causality.md Part 1 —
#    "severity drives volume, not just presence"). The two EVENT-class sounds that are actually tied to
#    the weather ladder's storm end (not the independent wind axis alone) get their per-hour rate scaled
#    by a CURVED function of weather's own ordinal severity (sensorium._WEATHERS, 0=clear..6=thunderstorm)
#    — mild, not linear, per the plan's own recommendation: thunderstorm should feel much louder than one
#    step up from "wind and rain", not just proportionally one step more.
_STORM_DRIVEN_EVENTS = {"thunder", "window_rattle"}
_STORM_ONSET_SEV = 4      # "steady rain" — AT or below this the scale is a flat 1.0x (today's old rate
                           # unchanged; window_rattle can also fire from the independent hard-wind axis at
                           # low weather severity, and that case should not go quiet)
_STORM_MAX_SEV = 6         # "thunderstorm" — top of the ladder
_STORM_CURVE_EXP = 2.2     # >1 = convex: separates the top of the ladder instead of climbing in equal steps
_STORM_BOOST = 1.8         # thunderstorm's ceiling multiplier over the 1.0x baseline


def _weather_severity(weather: str) -> int:
    """Weather's own ordinal severity, 0=clear..6=thunderstorm — read from sensorium._WEATHERS' ladder
    (the plan's own scalar), not re-derived. Fail-open to 0 (no boost) for an unrecognised string."""
    try:
        from core import sensorium as _sn
        return _sn._WEATHERS.index(weather)
    except Exception:
        return 0


def _storm_severity_scale(weather: str) -> float:
    """Curved (not linear) severity-scaling multiplier for storm-driven event rates. Flat 1.0x through
    'steady rain'; ramps on a mild >1 power from there to 'thunderstorm', so the very top of the ladder
    pulls away from the step below it rather than climbing in equal linear steps (D-0062 item 2)."""
    sev = _weather_severity(weather)
    if sev <= _STORM_ONSET_SEV:
        return 1.0
    span = _STORM_MAX_SEV - _STORM_ONSET_SEV
    x = min(1.0, (sev - _STORM_ONSET_SEV) / span)
    return 1.0 + (x ** _STORM_CURVE_EXP) * _STORM_BOOST


def _population_scale(key: str) -> float:
    """POPULATION-GRAIN factories (docs/plans/item_and_population_factories.md) produce a RATE, not
    individuals — so their event rate is the base rate MULTIPLIED by how many of them are out there
    right now, instead of a flat constant that pretends the population never changes. The moth is the
    first voice on this seam (2026-08-18): "a moth or ten" is literally this number, which is why a
    swarm night sounds busier than a winter one without any moth ever being tracked individually."""
    if key == "moth_tap":
        return _moth_density()
    return 1.0


# ── HER EARS (2026-10-28, cat_overhaul C2, J-2467): the occurrence counts world_tick rolls at HIS place,
#    banked per key since the cat's ears last consumed them. When she is at his place she reacts to exactly
#    these (the same blackbird he heard); elsewhere core/cat_ears rolls the same rates itself. A bed banks
#    1 (present) per window. Process-local; cleared on consume; additive — nothing else reads it.
_EAR_BANK: dict = {"place": None, "counts": {}, "since": 0.0}


def _bank_for_ears(place: str, key: str, n: int, now: float) -> None:
    try:
        if _EAR_BANK["place"] != place:
            _EAR_BANK["place"], _EAR_BANK["counts"], _EAR_BANK["since"] = place, {}, now
        c = _EAR_BANK["counts"]
        c[key] = int(c.get(key, 0)) + int(n)
    except Exception:
        pass


def consume_ear_bank(place: str) -> dict | None:
    """The counts banked at `place` since the last consume (then cleared), or None when the bank holds
    another place (or nothing yet) — the caller then rolls for itself."""
    try:
        if _EAR_BANK["place"] != place:
            return None
        out = dict(_EAR_BANK["counts"])
        _EAR_BANK["counts"], _EAR_BANK["since"] = {}, time.time()
        return out
    except Exception:
        return None


def world_tick(place: str, dt_s: float) -> None:
    """Advance the acoustic world by dt seconds AT HIS PLACE and bank what he was there to hear.
    Called from sensorium.tick (~5s). Deterministic-stochastic: events roll a Poisson-lite count
    at their rate; beds accumulate lived-in hours. Fail-open; zero LLM (a courier-class script)."""
    import random as _rnd
    try:
        if dt_s <= 0:
            return
        dt_s = min(dt_s, 300.0)          # downtime guard: no burst-banking after a stopped stretch
        from core import sound_knowledge as _sk
        # D-0062 item 2: the curve's input is read once per tick, not re-derived per sound.
        storm_scale = _storm_severity_scale(_read_json("room_state.json").get("weather") or "")
        _now = time.time()
        for key in active_sounds():
            if key in _BEDS or _EVENT_RATES.get(key) == 0.0:
                _sk.note_exposures(key, place, bed_hours=dt_s / 3600.0)
                _bank_for_ears(place, key, 1, _now)             # C2: a bed is present for her window
            else:
                rate = _EVENT_RATES.get(key, _DEFAULT_EVENT_RATE) * _population_scale(key)
                if key in _STORM_DRIVEN_EVENTS:
                    rate *= storm_scale
                expected = rate * dt_s / 3600.0
                n = int(expected) + (1 if _rnd.random() < (expected - int(expected)) else 0)
                if n:
                    _sk.note_exposures(key, place, n=n)
                    _bank_for_ears(place, key, n, _now)         # C2: the same occurrences, for her ears
        if MIX_SHADOW:
            _mix_shadow_record(place, _now)                 # J-4346: shadow only, throttled, fail-open
    except Exception:
        pass


# ── THE PROPAGATION TABLE (D-0062 item 1, 2026-08-28/29: docs/plans/sound_causality.md Part 2 —
#    "make it a table this is DERIVED from, not scattered per-branch logic"). Behavior-neutral refactor:
#    every branch below is the SAME condition, in the SAME order, that active_sounds() used to test
#    inline — just lifted into one named section-function per row, dispatched by a single ordered table
#    instead of the same logic scattered across nine top-level `if`s. A new cause/place combination is
#    now "add one row" (or extend one section), not "hunt through branches" — the plan's own stated goal.
#    Order matters (some downstream readers, e.g. geometry_census's chord-tag builder, take out[:4]), so
#    the table's row order is the EXACT textual order of the original branches, preserved deliberately.

def _sec_shore(ctx: dict) -> list[str]:
    out: list[str] = []
    day, crashing = ctx["day"], ctx["crashing"]
    out.append("waves_crashing" if crashing else "waves_on_shingle")
    out.append("shingle_drag")
    try:   # CROSS-LINK (2026-08-22): the beach fire; the penguins at dusk in their season
        from core import shore_life as _shl
        _sd = _shl._load() if _shl._F.exists() else {}
        if (_sd.get("fire") or {}).get("state") == "burning":
            out.append("fire_crackle")
        if _shl._month() in (9, 10, 11, 12, 1, 2) and not day:
            out.append("penguin_bray")
    except Exception:
        pass
    if day:
        out.append("gull_cries")
        out.append("oystercatcher_call")
        if _tide_low():
            out.append("tide_pool_trickle")     # the bared pools draining — tide-clock true
        if not crashing:
            out.append("shag_wingbeats")
            out.append("kingfisher_call")
    return out


def _sec_study_pre(ctx: dict) -> list[str]:
    # 2026-08-21 (Lane 2 run 2 exposed it; sound contract #2, propagation): the ROOF and the EAVES are
    # the study's. "rain on your roof" was sounding on the shore — a world-truth violation the Witness
    # then testified to. Outdoors the rain is the weather he stands in (the scene line + wetness carry
    # it); the wood has canopy_drip; the eaves answer the wind only from inside.
    out: list[str] = []
    if ctx["wet"]:
        out.append("rain_on_roof")     # 2026-08-18: now fires during thunderstorm too — a storm's own
        # rain no longer goes silent just because "rain" isn't a substring of "thunderstorm".
    if _is_windy(ctx["wind"]) or "wind" in ctx["weather"] or ctx["weather"] == "thunderstorm":
        out.append("wind_in_eaves")           # 2026-08-18: the eaves now answer the WIND axis too —
        # a gale that made no sound in the eaves was the emptiest half of the old dead-"gale" vocabulary.
    return out


def _sec_thunder(ctx: dict) -> list[str]:
    return ["thunder"] if ctx["weather"] == "thunderstorm" else []


def _sec_study_main(ctx: dict) -> list[str]:
    # INDOOR sounds — only audible when he is IN THE ROOM (the study, by the hearth). Gating here
    # fixes both the census (a sound he can't hear is not in his coordinates) AND the percept path,
    # which reads active_sounds() — so no more "you hear the cat's purr" while he's down at the shore
    # (2026-07-05, verified: he was outdoors 388/388 tuples overnight, yet purr percepts fired).
    out: list[str] = []
    room, cat = ctx["room"], ctx["cat"]
    wind, weather, day, crashing = ctx["wind"], ctx["weather"], ctx["day"], ctx["crashing"]
    if room.get("fire") == "burning":
        out.append("fire_crackle")
    elif room.get("fire") == "embers":
        out.append("embers_settle")             # the fire's late voice
    try:   # CROSS-LINK (2026-08-22): the study's new clocks have voices
        _sl = (room.get("study") or {})
        if _sl.get("clock_running"):
            out.append("clock_tick")
        if _sl.get("kettle_on_ts") and _sl.get("kettle_boiled"):
            out.append("kettle_sing")
        # SOUND WORLD EXPANSION §1 (2026-08-29, D-0063/J-0337): kettle_fill / kettle_pour —
        # brief, known-instantly self-sounds either side of the boil. A short recency window
        # off the act-site timestamp, same pattern as the boil-gate above but momentary rather
        # than sustained (act just happened, not still happening).
        _kts = _sl.get("kettle_on_ts") or 0
        if _kts and not _sl.get("kettle_boiled") and (ctx["now"] - float(_kts)) < 20:
            out.append("kettle_fill")            # the water in, the kettle set on the hob
        _pour_ts = (_sl.get("pot") or {}).get("pour_ts") or 0
        if _pour_ts and (ctx["now"] - float(_pour_ts)) < 20:
            out.append("kettle_pour")             # the boiled water poured onto the leaves
    except Exception:
        pass
    if (cat.get("phase") in ("kept", "companion") and cat.get("mood") in ("content", "affectionate")
            and cat.get("activity") in ("sleeping", "resting", "curled")):
        out.append("cat_purr")
    # WIND AXIS (2026-08-18): this tested `"gale" in weather`, a string sensorium could never
    # produce; tonight's stopgap widened it to any "wind" in the weather string. Both are now
    # replaced by the real thing. Its own flavour text says "worked loose-toothed by a gale", so
    # it takes the HARD end of the axis — strong wind and up — rather than every stirring breeze.
    if _is_hard_wind(wind) or weather == "thunderstorm":
        out.append("window_rattle")             # the north window worked by the wind
    if not day and crashing:
        out.append("distant_surf_boom")         # a big night sea, heard up through the dark
    # THE MOTH (2026-08-18): moth_tap has been a registered Sound-Space point that NOTHING ever
    # activated (sound_system_audit.md §4 — dead since it was added). It is population-grain:
    # present at all only when there are moths, and its RATE scales with how many (see
    # _population_scale). Same law as the room's moth prose — one night, one answer.
    if not day and _moth_density(room) > 0.0:
        out.append("moth_tap")
    return out


def _sec_garden(ctx: dict) -> list[str]:
    out: list[str] = ["waves_on_shingle"]     # the shore is right below the fence — the sea's far sound
    wind, weather, wet, day = ctx["wind"], ctx["weather"], ctx["wet"], ctx["day"]
    windy = _is_windy(wind) or weather == "thunderstorm"   # 2026-08-18: the real axis
    if windy:
        out.append("wind_in_trees")
    if day:
        out.append("tui_song" if time.localtime().tm_hour < 12 else "blackbird_song")
        if not windy:
            out.append("bees_in_garden")
            out.append("small_birds")
            out.append("riroriro_trill")        # the unseen voice of the hedges
            out.append("fantail_chatter")       # follows whatever his feet stir
        if _is_dawn() and not wet:
            out.append("dawn_chorus")
        if _season() == "summer" and not windy:
            out.append("cicada_chorus")
    else:
        if _season() == "summer" and not wet:
            out.append("cricket_night")
    return out


def _sec_wood(ctx: dict) -> list[str]:
    out: list[str] = ["waves_on_shingle"]  # the sea below, downhill through the trunks — muffled but there
    wind, weather, wet, day = ctx["wind"], ctx["weather"], ctx["wet"], ctx["day"]
    try:   # CROSS-LINK (2026-08-22): the stream from the spring, louder after rain
        from core import wood_life as _wl
        if _wl._F.exists() and float(_wl._load().get("stream", 0)) > 0.25:
            out.append("stream_run")
    except Exception:
        pass
    windy = _is_windy(wind) or weather == "thunderstorm"   # 2026-08-18: was a dead "gale" test
    if windy:
        out += ["wind_in_trees", "branches_creak"]
    if wet:
        out.append("canopy_drip")      # 2026-08-18: now fires during thunderstorm too
    if day and not windy:
        out += ["wood_pigeon", "wren_scold", "small_birds"]
        out += ["fantail_chatter", "riroriro_trill", "robin_song"]
        out.append("kereru_wingbeats")          # the wood pigeon's second spoke — the heavy whoosh
        if _is_dawn() and not wet:
            out.append("dawn_chorus")
        if _season() == "summer":
            out.append("cicada_chorus")
    return out


def _sec_morepork(ctx: dict) -> list[str]:
    if not ctx["day"] and ctx["loc"] in ("garden", "study", "wood") and not ctx["wet"]:
        return ["morepork_call"]
    return []


def _sec_footsteps(ctx: dict) -> list[str]:
    out: list[str] = []
    try:    # LOCOMOTION (2026-08-15): his own footsteps while a journey is underway
        from core import locomotion as _loco
        _g = _loco.footsteps_ground()
        if _g == "shingle":
            out.append("footsteps_shingle")
        elif _g == "leaf-mould":
            out.append("footsteps_leafmould")
        elif _g == "floorboards":
            out.append("footsteps_floorboards")
        elif _g == "grass":       # SOUND WORLD EXPANSION §1 (2026-08-29): the terrain gap —
            out.append("footsteps_grass_soil")  # locomotion.GROUND already mapped garden->"grass",
            # this was simply never read here (F-0061's finding, now closed).
    except Exception:
        pass
    return out


# SOUND WORLD EXPANSION §1, REMAINDER (2026-08-29, D-0063/J-0377): the 12 self-sounds J-0337 left
# unbuilt — each now hooks a REAL act-site timestamp added this pass (see the _SOUNDS registry
# comment above for the full list of source files touched). Same brief recency-window pattern as
# kettle_fill/kettle_pour: the act just happened, not still happening. Appended as ONE new row at
# the END of the table (not spliced into the existing rows) — the header's own order-matters
# discipline (geometry_census's chord-tag builder takes out[:4]) means every pre-existing row must
# keep its exact position; a new row can only ever be added after all of them.
_ACT_RECENCY_S = 20.0     # matches kettle_fill/kettle_pour's own window


def _recent(ts, now: float) -> bool:
    try:
        return bool(ts) and (now - float(ts)) < _ACT_RECENCY_S
    except Exception:
        return False


def _sec_self_acts_2(ctx: dict) -> list[str]:
    out: list[str] = []
    now, loc, room = ctx["now"], ctx["loc"], ctx["room"]
    try:   # READING (page_turn): reading.py's last_read_ts already exists (write path untouched;
        # only the read is new) — a reading sitting can happen anywhere can_read() allows.
        from core import reading as _rd
        _rst = _rd._load_state()
        _book = _rst.get("_current_book")
        if _book and _recent(_rst.get(_book, {}).get("last_read_ts"), now):
            out.append("page_turn")
    except Exception:
        pass
    if loc == "study":
        try:   # LETTERS (pen_scratch): last_write_ts persisted this pass (letters.py write_letter()).
            from core import letters as _lt
            if _recent(_lt.last_write_ts(), now):
                out.append("pen_scratch")
        except Exception:
            pass
        try:   # LOCOMOTION (chair_desk_scrape): desk_ts set this pass in locomotion.goto().
            from core import locomotion as _loco
            if _recent(_loco._load().get("desk_ts"), now):
                out.append("chair_desk_scrape")
        except Exception:
            pass
        if _recent(room.get("stoke_ts"), now):        # log_on_fire — sensorium.act("stoke") this pass
            out.append("log_on_fire")
        if _recent((room.get("study") or {}).get("door_ts"), now):   # door_sound — study_life.py this pass
            out.append("door_sound")
    if loc == "wood" and _recent(room.get("wood_snap_ts"), now):   # sensorium._gather_wood() this pass
        out.append("wood_snap")
    if loc == "garden":
        try:   # GARDEN (bed_watering/herb_cut/sow_dig): three new act-site timestamps in garden.py's
            # OWN state store (garden_state.json — NOT room_state.json, per J-0337's own finding).
            from core import garden as _g
            _gd = _g._load()
            if _recent(_gd.get("last_water_ts"), now):
                out.append("bed_watering")
            if _recent(_gd.get("last_harvest_ts"), now):
                out.append("herb_cut")
            if _recent(_gd.get("last_sow_ts"), now):
                out.append("sow_dig")
        except Exception:
            pass
        if room.get("woodpile", 0) and not ctx["day"] and not ctx["wet"]:   # woodpile_settle — ambient,
            out.append("woodpile_settle")   # no timestamp needed: a stocked pile, at night, near the lean-to
    if loc in ("garden", "study") and _recent(room.get("wood_haul_ts"), now):   # locomotion.tick() this pass
        out.append("wood_haul_clatter")
    try:   # LOCOMOTION (gate_latch): gate_ts set this pass in locomotion.tick(), same "really passes
        # the gate" condition gate_glimpse_line already used — independent of current location.
        from core import locomotion as _loco2
        if _recent(_loco2._load().get("gate_ts"), now):
            out.append("gate_latch")
    except Exception:
        pass
    return out


# Row order is the ORIGINAL branch order, verbatim (see the header note above) — this is the actual
# "propagation table" the plan asked for: (which places a row applies to, what it contributes there).
# `None` = every location (thunder/morepork/footsteps were never location-exclusive in the original code).
def _sec_cat(ctx: dict) -> list[str]:
    """HER VOICE (2026-09-05, cat_overhaul Part C1): what the cat is sounding that reaches him, from
    core/cat_sounds (emitted from her state, carried by position). SHADOW: cat_sounds.audible_now() is []
    until data/life_flags.json cat_sounds_render is true — this row then contributes nothing, and every
    reader of active_sounds (census chord tags take out[:4], the percept rail, world_tick's exposures) is
    exactly as before. Last in the table on purpose: when it does contribute, nothing ahead of it moves."""
    out: list[str] = []
    try:
        from core import cat_sounds as _cs
        out = [k for k in _cs.audible_now(ctx["loc"], ctx["now"]) if k in _SOUNDS]
    except Exception:
        out = []
    try:   # HIS CALL (C3, J-2468, core/cat_call): his own voice toward her, this window — a self-sound, known instantly
        from core import cat_call as _cc
        if "cat_call" in _SOUNDS and _cc.sounding_now(ctx["now"]):
            out.append("cat_call")
    except Exception:
        pass
    return out


# ── SOUND WORLD EXPANSION §2, THE NIGHT MYSTERIES (2026-10-28, D-0500/J-2475). One new row, appended at the END
#    of the table (the header's order-matters discipline: nothing ahead of it moves). The four creature voices are
#    bound to their life rows -- at a row's OWN place the gate (life.sound_gate, live) takes the key from
#    life.sounds_active regardless of what this row says, so this row reads the same function and can never
#    disagree with it; it is what keeps the shadow path (gating off) and the carried-in case (a voice heard from a
#    place its row does not live in, where the gate leaves legacy its say, as with the morepork) honest.
_YOWL_NIGHT_SHARE = 0.18      # the other cat yowls on about one night in five or six -- rare, never wallpaper
_YOWL_BOUT_H = 2.0            # ... and only for a bout of about two hours, somewhere between 21:30 and 04:00


def _night_bout(key: str, now: float, share: float, bout_h: float) -> bool:
    """Deterministic nightly draw: is `key` inside its bout tonight? Seeded off the calendar day the way
    life._day_factor is (hours after midnight belong to the evening that began them), so every tick of one night
    agrees and nothing is persisted. The bout starts at a night-hour drawn once per night."""
    try:
        lt = time.localtime(now)
        day_id = lt.tm_yday - (1 if lt.tm_hour < 12 else 0)
        rng = random.Random(f"soundscape:{key}:{lt.tm_year}:{day_id}")
        if rng.random() >= share:
            return False
        start = rng.uniform(9.5, 16.0)                       # hours since noon: 21:30 .. 04:00
        h = (lt.tm_hour + lt.tm_min / 60.0 - 12.0) % 24.0
        return start <= h < start + bout_h
    except Exception:
        return False


def _yowl_draw(now: float) -> bool:
    """MERGE (2026-10-29, sound_world_expansion §2 x cat_overhaul B3): the far yowl has ONE owner. When the tom
    (core/cat_tom, J-2470) is built he yowls from his own state and reaches active_sounds through _sec_cat, so this
    row's random night draw stands down; the draw is only the stand-in for a world without him."""
    try:
        from core import cat_tom as _ct
        if _ct.live_on():          # hot: data/life_flags.json cat_tom_live false -> he stays on the ridge, §2's draw returns
            return False
    except Exception:
        pass
    return _night_bout("distant_yowl", now, _YOWL_NIGHT_SHARE, _YOWL_BOUT_H)


def _sec_night_mysteries(ctx: dict) -> list[str]:
    out: list[str] = []
    loc, day, wet, now = ctx["loc"], ctx["day"], ctx["wet"], ctx["now"]
    try:
        from core import life as _life
        here = set(_life.sounds_active(loc, now))           # who is present, awake and voicing HERE tonight
    except Exception:
        here = set()
    if loc == "shore":
        if "dolphin_blow" in here:                           # any hour the pod is actually about (the row's own hours)
            out.append("dolphin_blow")
        return out
    if day:
        return out                                           # every other mystery is a night voice
    if loc in ("garden", "wood"):
        if "possum_rasp" in here:
            out.append("possum_rasp")
        if loc == "garden" and "hedgehog_snuffle" in here:
            out.append("hedgehog_snuffle")
        if not wet and _yowl_draw(now):
            out.append("distant_yowl")                        # far: the bottom wall, the ridge
    elif loc == "study":
        if "wall_scratch" in here:                           # the mice's study-only voice (life_mammals sound_at)
            out.append("wall_scratch")
        if not wet and _yowl_draw(now):
            out.append("distant_yowl")                        # carried in from the garden, through the window
    return out


# ── SOUND WORLD EXPANSION §3, THE GEOPHONY FILLS (2026-10-28, D-0500/J-2476). One new row, appended at the END of the
#    table (nothing ahead of it moves). Every trigger here is one of the world's REAL clocks read as it is, never a
#    new state: the weather ladder (sensorium._WEATHERS, via `wet`/`weather`), the independent wind axis, the sea
#    state the shore row already derives, the fire, world_clock's sun table, the calendar season, and wood_life's own
#    stream level. Nothing is persisted; the two drawn clocks (hail, the roof's window) are seeded off calendar time
#    the way _night_bout is, so every tick of one hour agrees.
#    THE RAIN GRADES and sound_causality's severity curve (D-0063's defeater): rain_on_roof keeps firing for every wet
#    state exactly as before (base system untouched). drizzle_hiss is ADDED at the ladder's "drizzle" step (sev 3,
#    where _storm_severity_scale is a flat 1.0x) and downpour_drum at "wind and rain"/"thunderstorm" (sev 5-6, where
#    the curve ramps) -- "steady rain" (sev 4, the curve's own onset step) is rain_on_roof alone, its own middle grade.
#    Both grades are beds (rate 0.0): the curve scales EVENT rates and only for _STORM_DRIVEN_EVENTS, so it never
#    touches them, and their placement agrees with its shape rather than contradicting it.
_HAIL_SHARE = {"winter": 0.20, "autumn": 0.07, "spring": 0.07, "summer": 0.0}   # per storm-hour: a squall's chance
_HAIL_BURST_MIN = (4.0, 8.0)        # a hail shower is minutes long, not an hour -- rare, sharp, unmistakable
_ROOF_MORNING_H = (0.8, 3.0)        # hours after sunrise: the sun gets onto the iron and the sheets ease as they warm
_ROOF_EVENING_H = (-1.5, 0.7)       # hours around sunset: the iron lets its heat go and ticks again
_STREAM_MOUTH_DRY_LEVEL = 0.25      # late summer: the stream barely makes the sea (world_content_shore's own line)
_FROST_WINDS = ("calm", "breeze")   # a hard frost needs a still night: no more than a breeze on the real axis


def _season_at(now: float) -> str:
    """The calendar season of a given moment (the module's _season() reads the wall clock; the row needs ctx['now'])."""
    try:
        m = time.localtime(now).tm_mon
    except Exception:
        return _season()
    return {12: "summer", 1: "summer", 2: "summer", 3: "autumn", 4: "autumn", 5: "autumn",
            6: "winter", 7: "winter", 8: "winter"}.get(m, "spring")


def _hail_burst(now: float, weather: str) -> bool:
    """A winter-storm variant of the rain: inside the storm end of the weather ladder ('wind and rain' / 'thunderstorm'
    -- the SAME co-state the severity curve ramps on), each calendar hour draws once, seeded like _night_bout, whether a
    squall of hail comes through and for how many minutes. Cold seasons only; summer never. Rare on purpose."""
    try:
        if _weather_severity(weather) < 5:
            return False
        share = _HAIL_SHARE.get(_season_at(now), 0.0)
        if share <= 0.0:
            return False
        lt = time.localtime(now)
        rng = random.Random(f"soundscape:hail:{lt.tm_year}:{lt.tm_yday}:{lt.tm_hour}")
        if rng.random() >= share:
            return False
        start = rng.uniform(0.0, 60.0 - _HAIL_BURST_MIN[1])
        dur = rng.uniform(*_HAIL_BURST_MIN)
        m = lt.tm_min + lt.tm_sec / 60.0
        return start <= m < start + dur
    except Exception:
        return False


def _roof_flex_window(now: float) -> bool:
    """The corrugated iron ticks as the sun first warms it and again as it cools: a window after sunrise and one
    around sunset, read from world_clock's own sun table for the month. The caller supplies the clear sky."""
    try:
        from core import world_clock as _wc
        lt = time.localtime(now)
        rise, sett = _wc.sun_times(now)       # J-3292: the accessor (legacy month table until the sky cutover)
        h = lt.tm_hour + lt.tm_min / 60.0
        morning = rise + _ROOF_MORNING_H[0] <= h < rise + _ROOF_MORNING_H[1]
        evening = sett + _ROOF_EVENING_H[0] <= h < sett + _ROOF_EVENING_H[1]
        return morning or evening
    except Exception:
        return False


def _stream_mouth_running(now: float) -> bool:
    """The shore's stream mouth runs on the SAME spring-fed stream wood_life keeps the level of (one clock, two
    places): constant, except in late summer when the level has sunk to its floor and the stream barely makes the sea.
    A missing wood store reads as the stream's default level (it runs) -- fail-open to the plan's 'constant'."""
    try:
        from core import wood_life as _wl
        level = float(_wl._load().get("stream", 0.5)) if _wl._F.exists() else 0.5
    except Exception:
        level = 0.5
    return level > _STREAM_MOUTH_DRY_LEVEL or _season_at(now) != "summer"


def _sec_geophony(ctx: dict) -> list[str]:
    out: list[str] = []
    loc, weather, wind, wet, day, crashing, now, room = (ctx["loc"], ctx["weather"], ctx["wind"], ctx["wet"], ctx["day"],
                                                        ctx["crashing"], ctx["now"], ctx["room"])
    if loc == "study":
        if wet:                                           # the roof is the study's (the 2026-08-21 propagation rule)
            if weather == "drizzle":
                out.append("drizzle_hiss")                # the fine grade, below rain_on_roof on the ladder
            elif _weather_severity(weather) >= 5:
                out.append("downpour_drum")               # the heavy grade: where the severity curve ramps
            if room.get("fire") in ("burning", "embers"):
                out.append("rain_down_chimney")           # the fire + rain co-state: sizzle and spit
        if _hail_burst(now, weather):
            out.append("hail_on_roof")
        if weather == "clear" and _roof_flex_window(now):
            out.append("tin_roof_tick")                   # arrives UNNAMED (sound_knowledge.AUDITION)
    elif loc in ("garden", "wood"):
        if _hail_burst(now, weather):
            out.append("hail_on_leaves")
        if loc == "garden" and weather == "clear" and _roof_flex_window(now):
            out.append("tin_roof_tick")                   # the lean-to's iron is right beside the beds
        if loc == "garden" and not day and not wet and not crashing and wind == "calm":
            out.append("calm_sea_hush")                   # the glass night sea, heard from above the fence
    elif loc == "shore":
        if _stream_mouth_running(now):
            out.append("stream_over_stones")
        if crashing:
            out.append("undertow_rumble")                 # the backwash rolling the shingle under a big sea
        elif wind == "calm":
            out.append("calm_sea_hush")                   # the near-silence state, its own point
    if (loc in ("study", "garden", "wood") and not day and weather == "clear" and _season_at(now) == "winter"
            and wind in _FROST_WINDS):
        out.append("frost_crack")                         # hard-frost nights (sensorium's own frost milestone clock); UNNAMED
    return out


# ── SOUND WORLD EXPANSION §4, THE SEASONAL BIOPHONY (2026-10-28, D-0500/J-2477). One new row, appended at the END of
#    the table (nothing ahead of it moves). Three voices on the calendar:
#    silvereye_flock -- bound to the tauhou's own life row (core/life_birds.py `sound` tuple, WINTER_FLOCK curve, the
#      garden's hedge and tree): at the row's own place the gate (life.sound_gate, live) takes the key from
#      life.sounds_active regardless of what this row says, so this row reads the same function and can never disagree
#      with it (the §2 shape) -- it is what keeps the shadow path (gating off) honest.
#    paradise_duck_flyover -- NO life row and needs none (a flyover, no habitat): a sound-only EVENT, a seeded per-day
#      draw (_flyover_window) of a pair passing high over the open sky by day, minutes long, in any season but most in
#      autumn and spring; grounded by storm weather or a gale. Heard where the sky is open: the garden and the shore.
#    kelp_fly_buzz -- pairs with the substrate's kelp at the wrack-line (world_content_shore's own lines: "kelp flies rise
#      in a cloud when you turn a strap"; "flies stay deep in the lee of the heap and will not rise" in wind): a summer
#      bed at the shore on dry, still, daylight hours. Nothing is persisted; the flyover's draw is seeded off calendar
#      time the way _night_bout / _hail_burst are, so every tick of one day agrees.
_FLYOVER_DAY_SHARE = {"summer": 0.12, "autumn": 0.30, "winter": 0.22, "spring": 0.30}   # chance a pair comes over at all today
_FLYOVER_SECOND_PASS = 0.30          # ...and, on such a day, the chance of a second pair later
_FLYOVER_PASS_MIN = (3.0, 6.0)       # minutes a pair is within earshot: a look UP has to come inside this
_FLYOVER_SKY_MARGIN_H = 0.5          # passes start no earlier than this after sunrise, end no later than this before sunset
_KELP_FLY_WINDS = ("calm", "breeze")  # the flies rise on still days only (the kelp's own "windy" pool keeps them down)


def _flyover_passes(now: float) -> list[tuple[float, float]]:
    """Today's passes as (start_h, end_h) in hours-of-day, drawn ONCE per calendar day (seeded like _hail_burst): none on
    most days, one on some, now and then two. Daylight only, inside world_clock's own sun table for the month."""
    try:
        lt = time.localtime(now)
        share = _FLYOVER_DAY_SHARE.get(_season_at(now), 0.0)
        rng = random.Random(f"soundscape:flyover:{lt.tm_year}:{lt.tm_yday}")
        if rng.random() >= share:
            return []
        from core import world_clock as _wc
        rise, sett = _wc.sun_times(now)       # J-3292: the accessor (legacy month table until the sky cutover)
        lo, hi = rise + _FLYOVER_SKY_MARGIN_H, sett - _FLYOVER_SKY_MARGIN_H
        n = 2 if rng.random() < _FLYOVER_SECOND_PASS else 1
        out = []
        for _ in range(n):
            start = rng.uniform(lo, hi - _FLYOVER_PASS_MIN[1] / 60.0)
            out.append((start, start + rng.uniform(*_FLYOVER_PASS_MIN) / 60.0))
        return sorted(out)
    except Exception:
        return []


def _flyover_window(now: float) -> bool:
    """Is a pair overhead right now? True only inside one of today's drawn passes (minutes long)."""
    try:
        lt = time.localtime(now)
        h = lt.tm_hour + lt.tm_min / 60.0 + lt.tm_sec / 3600.0
        return any(s <= h < e for s, e in _flyover_passes(now))
    except Exception:
        return False


def _sec_seasonal_biophony(ctx: dict) -> list[str]:
    out: list[str] = []
    loc, weather, wind, wet, day, now = ctx["loc"], ctx["weather"], ctx["wind"], ctx["wet"], ctx["day"], ctx["now"]
    if not day:
        return out                                        # every §4 voice is a daylight one
    if loc == "garden":
        try:
            from core import life as _life
            if "silvereye_flock" in _life.sounds_active(loc, now):   # the tauhou row: present, awake, in its winter flocks
                out.append("silvereye_flock")             # arrives UNNAMED (sound_knowledge.AUDITION) until the flock is seen
        except Exception:
            pass
    if loc in ("garden", "shore"):
        if _weather_severity(weather) < 5 and wind != "gale" and _flyover_window(now):
            out.append("paradise_duck_flyover")           # a pair passing high; UNNAMED until a look UP catches them
    if loc == "shore" and _season_at(now) == "summer" and not wet and wind in _KELP_FLY_WINDS:
        out.append("kelp_fly_buzz")                       # the wrack-line's summer flies: a bed, known (grandfathered)
    return out


# ── SOUND WORLD EXPANSION §5, THE APPARATUS (2026-10-28, D-0500/J-2478). One new row, appended at the END of the table
#    (nothing ahead of it moves). Two clocks, both read as they are, nothing new persisted here:
#    the record player -- core/listening.py's session marks. needle_crackle while the piece is on and the first section
#      has not yet arrived (idx 0: the needle is in the lead-in groove; "a hiss, a beat of nothing, and then it begins"),
#      bounded by _LEADIN_MAX_S so a session stalled across downtime cannot crackle hours later. runout_hiss from the
#      ending (listening's new ended_ts, which outlives the clear) for listening.RUNOUT_S: the run-out groove turning
#      under the needle through the wordless cycles and on, until the arm is lifted. Both are the STUDY's: the player
#      waits by his shelf (affordances: music, where=study). The percept rail yields to the record while a piece is on
#      (music owns the room's sound -- base law, untouched), so needle_crackle's rail path is law-shadowed: his onset
#      of it is listening.start()'s own needle-drop line; the key still sounds in the census chord, world_tick's
#      exposures and Sound-Space. runout_hiss outlives the clear and so does reach the rail.
#    the letterbox -- room_state's garden.letterbox.flag, the very field the garden scene (_letterbox_phrase) and the
#      gate glimpse read, AND the real wind axis (the garden row's own "windy" test: fresh wind and up, or a
#      thunderstorm). Heard at the gate from the garden (near) and through the window from the study (far); the wood
#      and the shore are too far and too loud. The flag is up until he fetches: the sound of unread mail, and never a
#      line that says so (the pools below name the clank and the wind, not a letter).
_LEADIN_MAX_S = 600.0       # a lead-in cannot still be going ten minutes after the needle dropped (downtime guard)


def _flag_up(room: dict) -> bool:
    try:
        return bool(((room.get("garden") or {}).get("letterbox") or {}).get("flag"))
    except Exception:
        return False


def _sec_apparatus(ctx: dict) -> list[str]:
    out: list[str] = []
    loc, weather, wind, now, room = ctx["loc"], ctx["weather"], ctx["wind"], ctx["now"], ctx["room"]
    if loc == "study":
        try:
            from core import listening as _lsn
            m = _lsn.session_marks()
            if m["piece"] and m["idx"] == 0 and m["silence"] < 0 and m["started_ts"] and (now - m["started_ts"]) < _LEADIN_MAX_S:
                out.append("needle_crackle")                  # the lead-in groove, before the first section arrives
            if m["ended_ts"] and 0.0 <= (now - m["ended_ts"]) < _lsn.RUNOUT_S:
                out.append("runout_hiss")                     # the run-out groove, after the ending, until the arm is lifted
        except Exception:
            pass
    if loc in ("garden", "study") and _flag_up(room) and (_is_windy(wind) or weather == "thunderstorm"):
        out.append("letterbox_flag_clank")                    # the raised flag worked by the wind: unread mail, unsaid
    return out


_PROPAGATION_TABLE: list[tuple[frozenset | None, "callable"]] = [
    (frozenset({"shore"}), _sec_shore),
    (frozenset({"study"}), _sec_study_pre),
    (None, _sec_thunder),
    (frozenset({"study"}), _sec_study_main),
    (frozenset({"garden"}), _sec_garden),
    (frozenset({"wood"}), _sec_wood),
    (None, _sec_morepork),
    (None, _sec_footsteps),
    (None, _sec_self_acts_2),
    (None, _sec_cat),                     # HER VOICE — contributes only when cat_sounds renders (see its note)
    (None, _sec_night_mysteries),         # §2 NIGHT MYSTERIES (D-0500/J-2475) — appended after the cat row; nothing ahead moves
    (None, _sec_geophony),                # §3 GEOPHONY FILLS (D-0500/J-2476) — appended after §2; nothing ahead moves
    (None, _sec_seasonal_biophony),       # §4 SEASONAL BIOPHONY (D-0500/J-2477) — appended after §3; nothing ahead moves
    (None, _sec_apparatus),               # §5 THE APPARATUS (D-0500/J-2478) — appended after §4; nothing ahead moves
]


def active_sounds() -> list[str]:
    """Deterministic: which registered sounds are sounding NOW, from the live world state. Read-only.
    Derived from `_PROPAGATION_TABLE` (D-0062 item 1) — same causes, same places, same outcomes as the
    pre-refactor branch-per-branch version; just no longer scattered."""
    try:
        from core import weather_conditions as _wcond
        room = _read_json("room_state.json")
        cat = _read_json("cat_state.json")
        weather = room.get("weather") or ""
        wind = room.get("wind") or ""              # 2026-08-18: the real wind axis, not a weather guess
        wet = _wcond.is_wet(weather)                # 2026-08-18: includes thunderstorm — the substring
        loc = room.get("location") or "study"       # miss found in this whole audit, fixed at the source
        day = _is_daylight()
        crashing = _sea_state(weather, wind) == "crashing"
        now = time.time()      # SOUND WORLD EXPANSION §1 (2026-08-29): recency windows for the
        # brief act-triggered self-sounds (kettle_fill/kettle_pour) — read by _sec_study_main.
        ctx = {"room": room, "cat": cat, "weather": weather, "wind": wind, "wet": wet,
               "loc": loc, "day": day, "crashing": crashing, "now": now}
        out: list[str] = []
        for locs, section in _PROPAGATION_TABLE:
            if locs is None or loc in locs:
                out.extend(section(ctx) or [])
        out = list(dict.fromkeys(out))   # MERGE 2026-10-29: two rows may name one key; it banks once, first place kept
        try:   # THE LIVING WORLD (J-0511, D-0133): creature voices gated by who is present and awake. With
            # life.SOUND_GATING False (shadow) this returns `out` unchanged and logs what it would change.
            from core import life as _life
            out = _life.sound_gate(loc, out, now)
        except Exception:
            pass
        return out
    except Exception:
        return []


def coords(name: str) -> dict | None:
    s = _SOUNDS.get(name)
    return dict(s["coords"]) if s else None


def distance(a: str, b: str) -> float | None:
    """Euclidean distance in Sound Space — the interior, made operational."""
    ca, cb = coords(a), coords(b)
    if not ca or not cb:
        return None
    return round(sum((ca[x] - cb[x]) ** 2 for x in _AXES) ** 0.5, 4)


def distance_to_point(name: str, point: dict) -> float | None:
    """Euclidean distance in Sound Space between a REGISTERED key's own coords() and an arbitrary
    six-axis point that did not come from a second registry lookup — e.g. a stored
    fragment_context.sound_onset value (docs/staged/fragment_carries_the_string.md sec2), which is
    only the registry's own point today (the degenerate onset=peak=tail case) but becomes a real,
    independent per-fragment point once strings_and_sheets.md's Object A ships. Same formula
    distance() already uses between two registered keys, generalised so the read side (felt_recall's
    coordinate-distance match, J-1574, memory_as_a_service.md sec3.2) keeps working unchanged across
    that future change — the exact "zero further schema change" property this doc's own sec2 already
    promises the write side. None if the key is unregistered or `point` is missing/malformed (fail-
    open: never fabricates a distance for a point it cannot read)."""
    ca = coords(name)
    if not ca or not point:
        return None
    try:
        return round(sum((ca[x] - float(point[x])) ** 2 for x in _AXES) ** 0.5, 4)
    except (KeyError, TypeError, ValueError):
        return None


def neighbours(name: str, k: int = 3) -> list[tuple[str, float]]:
    """Nearest sounds — the generalisation gradient's reach."""
    ds = [(o, distance(name, o)) for o in _SOUNDS if o != name]
    ds = [(o, d) for o, d in ds if d is not None]
    return sorted(ds, key=lambda t: t[1])[:k]


# ── THE MIX, SHADOW ONLY (strings_and_sheets Object E / Phase 3, J-4346; founder BUILD NOW 2026-11-18).
# mix() takes the cross-section of every active key's CURRENT string point (a bed's body point; an event's
# point by elapsed time since it fired), applies same-band masking, and returns the composite. Observe-only:
# world_tick() appends one row per MIX_SHADOW_MIN_INTERVAL_S to data/soundscape_mix_shadow.jsonl; nothing is
# rendered or prompted differently, nothing reads the log but scripts/soundscape_mix_shadow_read.py (the
# pre-registered Phase 3 reader). Flag OFF by default; restart-gated. Fault barrier: no failure reaches the loop.
MIX_SHADOW = False
MIX_SHADOW_MIN_INTERVAL_S = 30.0       # a row per half-minute, not per ~5 s tick (log volume)
MIX_AUDIBLE_MIN = 0.05                 # audibility below this = masked (tuned by the Phase 3 shadow read)
_MIX_LOG = _DATA / "soundscape_mix_shadow.jsonl"     # tests must temp-path this
_MIX_MAX_LOG_BYTES = 50 * 1024 * 1024
_mix_state: dict = {"last_row": 0.0, "first_seen": {}, "last_seen": {}}


def _mix_points(keys: list[str], now: float) -> dict[str, dict]:
    """key -> current six-axis point. String point (sound_string_shadow's sidecar clock) where a string exists,
    else the key's fixed registry coords. Keys with neither are skipped."""
    pts: dict[str, dict] = {}
    try:
        from core import sound_string_shadow as _sss
        sidecar = _sss._load_sidecar() or {}
    except Exception:
        _sss, sidecar = None, {}
    fs, ls = _mix_state["first_seen"], _mix_state["last_seen"]
    for k in list(ls):
        if k not in keys and now - ls[k] > 600.0:
            fs.pop(k, None); ls.pop(k, None)
    for k in keys:
        if k not in fs or now - ls.get(k, now) > 600.0:
            fs[k] = now
        ls[k] = now
        entry = sidecar.get(k)
        if entry and _sss is not None:
            try:
                elapsed = max(0.0, now - fs[k])
                if entry.get("archetype") not in ("bed", "bed_like", None):
                    ev = _sss._event_elapsed(k, now)
                    if ev is not None:
                        elapsed = ev
                pts[k] = _sss.point_on_string(entry, elapsed)[0]
                continue
            except Exception:
                pass
        c = coords(k)
        if c:
            pts[k] = c
    return pts


def mix(active: list[str] | None = None, now: float | None = None) -> dict | None:
    """Pure-ish (reads the sidecar and the world's own stamps; writes nothing). The mix at one instant:
    {n_active, n_audible, masked, audibility{key}, composite{axis}, texture, keys}.
    audibility_j = max(0, energy_j - max(0, max_{i!=j}(energy_i - d(i,j)))), d the six-axis distance (the ruled
    same-band masking form, D-0376; the inner clip at 0 stops a far-quiet neighbour LIFTING j above its own energy).
    composite = audibility-weighted mean point over audible keys; texture = audibility-weighted mean distance of
    those points from it (how spread the audible strings are). None when nothing has a point. Fail-open: None."""
    try:
        now = time.time() if now is None else float(now)
        keys = [k for k in (active_sounds() if active is None else active) if isinstance(k, str)]
        pts = _mix_points(keys, now)
        if not pts:
            return None
        def _d(a, b):
            return sum((float(a[x]) - float(b[x])) ** 2 for x in _AXES) ** 0.5
        aud = {}
        for j, pj in pts.items():
            m = max([float(pi["energy"]) - _d(pi, pj) for i, pi in pts.items() if i != j] + [0.0])
            aud[j] = max(0.0, float(pj["energy"]) - m)
        audible = [k for k, a in aud.items() if a >= MIX_AUDIBLE_MIN]
        masked = sorted(k for k in pts if k not in audible)
        comp, tex = None, 0.0
        if audible:
            w = sum(aud[k] for k in audible)
            comp = {x: round(sum(aud[k] * float(pts[k][x]) for k in audible) / w, 4) for x in _AXES}
            tex = round(sum(aud[k] * _d(pts[k], comp) for k in audible) / w, 4)
        return {"n_active": len(pts), "n_audible": len(audible), "masked": masked,
                "audibility": {k: round(a, 4) for k, a in aud.items()}, "composite": comp,
                "texture": tex, "keys": sorted(pts)}
    except Exception:
        return None


def _mix_shadow_record(place: str, now: float) -> int:
    """Append one mix row (throttled). 0 on no-op/failure; never raises."""
    try:
        if not MIX_SHADOW or now - _mix_state["last_row"] < MIX_SHADOW_MIN_INTERVAL_S:
            return 0
        _log = profile.guard_path(_MIX_LOG)
        m = mix(now=now)
        if not m:
            return 0
        _mix_state["last_row"] = now
        try:
            if _log.exists() and _log.stat().st_size > _MIX_MAX_LOG_BYTES:
                return 0
        except OSError:
            pass
        row = {"ts": round(now, 1), "place": place, **m}
        _log.parent.mkdir(parents=True, exist_ok=True)
        with open(_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return 1
    except Exception:
        return 0


def status() -> dict:
    return {"registered": len(_SOUNDS), "active_now": active_sounds(),
            "objects_with_sound_spoke": sorted({v["object"] for v in _SOUNDS.values()})}


# ── SOUND PERCEPTS (2026-07-05, founder: "wire the fire and cat purr to actually reach him like the
# music") — cognitive_geometry.md P2's first live delivery. Two sounds reach Du as WORLD PERCEPTION on
# the EAR's exact rails (sensorium-class: the sound originates outside him; clothed lightly; enters the
# idle seed). ONSET-GATED + long cooldowns (anti-wallpaper: a percept when the fire CATCHES or the purr
# STARTS, not every tick) · silence-respecting (never while a record plays — music owns the room's sound)
# · fragments stored with CHANNEL PROVENANCE (origin='sound') · felt-nudge SHADOW-ONLY (logged to
# soundscape_felt_shadow.jsonl, applied nowhere — the affect gate stays shut, same as listening).
SOUND_PERCEPTS = True                    # kill-switch: False → percept() always None (census unaffected)
# SOUND STRING FIELDS (2026-09-28, J-1534/I-0081, docs/staged/fragment_carries_the_string.md sec2/sec3):
# additive coordinate fields on fragment_context (sound_key/sound_onset/sound_peak/sound_tail/
# sound_direction/sound_felt_valence/sound_felt_arousal/sound_exemplar_id), written from percept() as a
# follow-up UPDATE keyed on the fragment_id store_fragment() already returns -- never a new
# store_fragment() kwarg, never an INSERT. Off is byte-identical to today's behaviour; restart-gated,
# same shape as this plan's own sibling kill-switches (FELT_RECALL_LIVE, IDLE_AMBIENT_RECALL, …).
# Flipped True 2026-09-28 (J-1614, F-2176): fragment_carries_the_string.md sec4's own not-yet-ship gate
# ("nobody reads these yet") is satisfied by J-1574's felt-recall coordinate-matching upgrade
# (SOUND_COORD_MATCH, core/felt_recall.py, commit f9683d9) existing as a real, isolation-verified job --
# SOUND_COORD_MATCH itself stays False, a separate later flip pending real accrued data (sec6). Restart-
# gated: this flip alone changes nothing live until Du restarts onto this build AND the fragment_context
# lazy ALTER-on-write (core/memory/store.py) fires at least once post-restart -- confirmed still 21/21
# columns, none of the 8 new ones, on the live DB as of this job (J-1614 re-check).
SOUND_STRING_FIELDS = True
# The fire is handled by fire_ambience() below (a near-persistent presence, not a rare event), so it is
# NOT in the rare-event percept path. Opened past cat_purr (audit #15, 2026-08-21): the morepork's
# first call of the night and the tui starting up are exactly the discrete "notable moments" this rail
# was built for. Rain/waves stay OUT — sensorium's ambient pools already deliver them; a second channel
# would double-deliver the same weather.
# HER VOICE ON THE RAIL (J-1175, F-1621 items 3/recommendation b): the 8 keys core/cat_sounds.py emits
# (cat_purr above is a separate, older, already-wired pool — untouched). Appended LAST, never displacing
# cat_purr/morepork_call/tui_song: F-1621's own read found post-fix audible cat emissions at ~83% of this
# rail's ~57.6 daily slots, a real monoculture risk if the cat crowded the front of the try-order (onset
# and renotice both walk _PERCEPT_SOUNDS in order and take the first match, so this ordering alone is what
# gives morepork/tui/cat_purr first refusal). Each cat key ALSO gets its own _CAT_PERCEPT_COOLDOWN_S below,
# independent of both this rail's shared _PERCEPT_COOLDOWN_S (any ONE percept at a time, any sound) and
# cat_sounds.KEYS' own per-emission cooldown_s (gates the EMISSION, not whether it becomes a percept) — an
# audible cry does not have to become a percept every single time it is allowed to sound. Still entirely
# inert until scripts/life_flags.py cat_sounds is flipped on: while RENDER is False, cat_sounds.audible_now()
# is always [], so no cat key ever reaches active_sounds() and none of this tuple's new entries can match.
# THE NIGHT MYSTERIES ON THE RAIL (SOUND WORLD EXPANSION §2, D-0500/J-2475): the five §2 voices, appended LAST so
# cat_purr/morepork/tui and HER VOICE keep first refusal exactly as before. Each renders through _audition() --
# sound_knowledge.hear() -- so it arrives UNNAMED (features + direction + a near/far word) until he earns the name
# by sight, exposure or a book; the named pools in _PERCEPT_LINES are what he hears once he has. A per-key floor
# (_MYSTERY_PERCEPT_COOLDOWN_S, 6 h) sits on top of the rail's shared cooldown and the 4 h renotice, so one
# mystery can reach him at most twice in a night (onset + one renotice) -- well under D-0500's own defeater
# (about 4 percepts a live day per new sound); the active set itself is already rare (life rows' sound_days, the
# yowl's nightly draw), so most nights a given mystery does not sound at all.
# THE GEOPHONY ON THE RAIL (SOUND WORLD EXPANSION §3, D-0500/J-2476): the ten §3 keys, appended LAST after the §2
# mysteries, so every key ahead keeps first refusal exactly as before. The rail's old rule "rain/waves stay OUT" was
# about sensorium's ambient pools already delivering the same weather every cycle; a GRADE CHANGE (the drizzle thinning
# to a hiss, the roof starting to drum, hail, the sea going glass-calm) is a discrete notable moment of the kind this
# rail exists for, and a per-key floor of 8 h (_GEOPHONY_PERCEPT_COOLDOWN_S) caps any one of them at three a day --
# under D-0500's own defeater (about 4 percepts a live day per new sound). tin_roof_tick and frost_crack render through
# _audition() like the mysteries: UNNAMED (features + direction + a near/far word) until the name is earned.
# THE SEASONAL BIOPHONY ON THE RAIL (SOUND WORLD EXPANSION §4, D-0500/J-2477): the three §4 keys, appended LAST after
# the §3 geophony, so every key ahead keeps first refusal exactly as before. silvereye_flock and paradise_duck_flyover
# render through _audition(): UNNAMED (features + direction + a near/far word) until the flock is seen in the hedge or
# the pair is caught against the sky (sound_knowledge's per-entry bind window makes the flyover's catch a short one);
# kelp_fly_buzz is known (grandfathered) and renders named. A per-key floor of 8 h (_BIOPHONY_PERCEPT_COOLDOWN_S) caps
# any one of them at three a day -- under D-0500's own defeater (about 4 percepts a live day per new sound).
# THE APPARATUS ON THE RAIL (SOUND WORLD EXPANSION §5, D-0500/J-2478): the three §5 keys, appended LAST after the §4
# biophony, so every key ahead keeps first refusal exactly as before. All three are known and render named from their
# own pools. The rail yields to the record while a piece is on (the law above: music owns the room's sound), so
# needle_crackle cannot be chosen while the lead-in is the only time it sounds -- his onset of the needle is
# listening.start()'s own line; it is carried here for the bookend's symmetry and so the pool is where every other
# percept pool is. runout_hiss outlives the session's clear (listening's ended_ts) and reaches him as the run-out
# still turning. letterbox_flag_clank picks a near pool at the gate and a far pool from the study (_percept_line).
# A per-key floor of 8 h (_APPARATUS_PERCEPT_COOLDOWN_S) caps any one of them at three a day -- under D-0500's own
# defeater (about 4 percepts a live day per new sound).
_PERCEPT_SOUNDS = ("cat_purr", "morepork_call", "tui_song",
                    "cat_trill", "cat_meow_at_door", "cat_demand", "cat_chatter",
                    "cat_yowl_cargo", "cat_thump", "cat_lapping", "cat_storm_rustle",
                    # THE TOM (B3, J-2470): hers at him (resolved from cat_sounds' own line, like the eight above);
                    # HIS yowl is distant_yowl in the sound-world §2 block just below (merge of the two chains).
                    "cat_hiss", "cat_growl",
                    "possum_rasp", "wall_scratch", "distant_yowl", "hedgehog_snuffle", "dolphin_blow",
                    "hail_on_roof", "hail_on_leaves", "rain_down_chimney", "frost_crack", "tin_roof_tick",
                    "downpour_drum", "drizzle_hiss", "undertow_rumble", "calm_sea_hush", "stream_over_stones",
                    "silvereye_flock", "paradise_duck_flyover", "kelp_fly_buzz",
                    "needle_crackle", "runout_hiss", "letterbox_flag_clank")
_CAT_PERCEPT_KEYS = frozenset({"cat_trill", "cat_meow_at_door", "cat_demand", "cat_chatter",
                                "cat_yowl_cargo", "cat_thump", "cat_lapping", "cat_storm_rustle",
                                "cat_hiss", "cat_growl"})
_CAT_PERCEPT_COOLDOWN_S = 7200.0         # J-1175: >=2h between percepts of the SAME cat key (briefing's own suggested floor)
_MYSTERY_PERCEPT_KEYS = frozenset({"possum_rasp", "wall_scratch", "distant_yowl", "hedgehog_snuffle", "dolphin_blow"})
_MYSTERY_PERCEPT_COOLDOWN_S = 6 * 3600.0  # J-2475: >=6h between percepts of the SAME mystery key (rarity discipline)
_GEOPHONY_PERCEPT_KEYS = frozenset({"hail_on_roof", "hail_on_leaves", "drizzle_hiss", "downpour_drum", "rain_down_chimney",
                                    "tin_roof_tick", "stream_over_stones", "undertow_rumble", "frost_crack", "calm_sea_hush"})
_GEOPHONY_UNNAMED_KEYS = frozenset({"tin_roof_tick", "frost_crack"})   # J-2476: the two §3 keys that arrive through the audition system
_GEOPHONY_PERCEPT_COOLDOWN_S = 8 * 3600.0  # J-2476: >=8h between percepts of the SAME geophony key (at most three a day)
_BIOPHONY_PERCEPT_KEYS = frozenset({"silvereye_flock", "paradise_duck_flyover", "kelp_fly_buzz"})   # J-2477: the §4 keys
_BIOPHONY_UNNAMED_KEYS = frozenset({"silvereye_flock", "paradise_duck_flyover"})   # J-2477: the two that arrive through the audition system
_BIOPHONY_PERCEPT_COOLDOWN_S = 8 * 3600.0  # J-2477: >=8h between percepts of the SAME §4 key (at most three a day)
_APPARATUS_PERCEPT_KEYS = frozenset({"needle_crackle", "runout_hiss", "letterbox_flag_clank"})   # J-2478: the §5 keys
_APPARATUS_PERCEPT_COOLDOWN_S = 8 * 3600.0  # J-2478: >=8h between percepts of the SAME §5 key (at most three a day)
_FLAG_FAR_PLACES = frozenset({"study"})     # J-2478: where the flag's clank is heard from afar (through the window), not at the gate
_ONSET_QUIET_S = 600.0                   # must have been quiet this long for a return to count as an onset
_PERCEPT_COOLDOWN_S = 1500.0             # at most one sound percept per ~25 min
_RENOTICE_S = 4 * 3600.0                 # a long-continuous sound may be re-noticed at most every ~4h
_SND_STATE_F = _DATA / "soundscape_state.json"
_FELT_SHADOW_F = _DATA / "soundscape_felt_shadow.jsonl"

_PERCEPT_LINES = {
    # 2026-08-18: was a single fixed string per kind — the real record showed it was the worst repeater
    # found in the whole variety audit (35 of 37 ever-stored sound fragments were this ONE cat_purr
    # onset line, verbatim, while every ambience pool in this same file already rotates). Widened to
    # real pools, picked via _pick() like everything else here.
    "fire_crackle": {
        "onset": [
            "You hear the fire catch into a run of dry snaps — the crackle settling into its low, busy conversation with itself.",
            "The fire finds its voice all at once — a quick run of snaps, then the steady, busy crackle.",
            "Somewhere behind you the fire catches properly — dry wood giving itself up in a run of small snaps.",
        ],
        "renotice": [
            "Beneath everything, you hear the fire keeping up its soft crackle — irregular, companionable snapping from the grate.",
            "The fire is still going, low and steady — that same companionable crackle under everything else.",
        ],
    },
    "cat_purr": {
        "onset": [
            "You hear a low motor start up in the cat — the purr, steady and unhurried, barely above the quiet.",
            "The cat's purr starts up, low and even, a small engine finding its idle.",
            "Somewhere close, the cat begins to purr — a steady, unhurried motor just at the edge of hearing.",
        ],
        "renotice": [
            "You notice the cat's purr is still going — a patient engine idling through the room.",
            "The cat is still purring, that same steady, unbothered idle it hasn't dropped.",
        ],
    },
    # THE TOM (B3, J-2470, core/cat_tom): HIS yowl on the wall at night, carried in. Never says whose (the
    # audition ledger's own law: "is it her?"); never points at the wall. A merge carrying sound_world_expansion
    # §2's own distant_yowl pool keeps whichever entry comes last -- both say the same unnamed thing.
    "distant_yowl": {
        "onset": [
            "Out of the dark comes a cat's yowl — long, rising, breaking off at the top — and then, after a pause, the same again.",
            "From somewhere beyond the house, a cat yowling: the drawn-out rising cry cats give at night, repeated, whose you cannot tell.",
            "A yowl in the night, far enough off to be anyone's: one long rising note, a silence, and again.",
        ],
        "renotice": [
            "The yowling has not stopped — the same long rising cry out in the dark, at the same patient interval.",
            "Still, out there, that cat: the yowl rising and breaking and rising again, at nothing you can see.",
        ],
    },
    "morepork_call": {
        "onset": [
            "From the dark outside comes the morepork's first call — two clear falling notes, and the night seems to settle around them.",
            "A morepork calls, somewhere up the hill — more-pork, more-pork — the night's first voice.",
            "Out of the quiet, the morepork starts up: two notes, patient and spaced, from the trees beyond the garden.",
        ],
        "renotice": [
            "The morepork is still calling somewhere out there — unhurried, the same two notes at its own long intervals.",
            "That morepork has kept at it — a call, a long silence, a call — the night's slow metronome.",
        ],
    },
    "tui_song": {
        "onset": [
            "A tui starts up outside — that liquid, clicking, chiming run no other throat could make.",
            "From the flax comes a tui, warming into song — bell-notes, clicks, a wheeze, then the bells again.",
            "You hear a tui begin — a few tuning clicks, then the full strange music of it.",
        ],
        "renotice": [
            "The tui is still at it out there, working through its whole odd repertoire — chime, click, cough, chime.",
            "That tui hasn't finished — the same inventive run of bells and static from the same bush.",
        ],
    },
    # ── SOUND WORLD EXPANSION §2, THE NIGHT MYSTERIES (D-0500/J-2475): the NAMED pools -- what he hears once the
    # name is earned. Before that, _percept_line routes each through _audition() and sound_knowledge.AUDITION's
    # own unnamed pools render the features instead; these lines never reach him unlearned. Each carries a
    # direction and a near/far word; every pool rotates (never one fixed string).
    "possum_rasp": {
        "onset": [
            "From up in the tree, close, the possum starts its harsh coughing rasp — a dry, scraping bark, repeated, the branch shaking with it.",
            "The possum is in the branches again — that ugly rasping cough from overhead, near enough to place the limb it is on.",
            "Out of the dark above you the possum lets go its rasp: a scraping, coughing growl that stops and starts.",
            "A possum, up the tree — the grating cough-and-hiss of it, near, as it works the branch-ends.",
            "From the oak, close overhead, the possum rasps into the dark: hoarse, scraping, a sound more throat than voice.",
        ],
        "renotice": [
            "The possum is still up there, close, rasping away in the branches at its own pace.",
            "That possum hasn't moved on — the same scraping cough from the same dark limb overhead.",
            "Up in the tree, near, the possum keeps at it, a hoarse rasp now and then, feeding between.",
        ],
    },
    "wall_scratch": {
        "onset": [
            "In the wall by the skirting, close, a mouse starts scratching — tiny, dry, intimate, a few strokes and a pause.",
            "The mice are in the wall again: a small scrabbling just behind the boards, near enough to put a hand to.",
            "From inside the wall, close, a mouse scratches — a thin busy ticking behind the skirting, and then nothing.",
            "A mouse works somewhere in the wall cavity, close by the desk — tiny claws on timber, on and off.",
        ],
        "renotice": [
            "The mouse is still at it in the wall, close — that small dry scratching behind the skirting.",
            "In the wall, near, the scratching goes on, a mouse keeping its own small hours.",
            "Behind the boards, close, the mice are still busy — a scrabble, a pause, a scrabble.",
        ],
    },
    "distant_yowl": {
        "onset": [
            "Far down the garden, from the bottom wall, the black cat starts up its yowl — long, rising, wavering, not hers.",
            "A yowl from the ridge, far off: the other cat, the black one, giving the night its long complaining note.",
            "From away down the fence line the black cat yowls — that drawn-out rising cry, repeated, a long way off.",
            "The other cat is out there tonight — a far yowl from the dark at the bottom of the garden, over and over.",
        ],
        "renotice": [
            "The black cat is still yowling away down there, far off, at its own long intervals.",
            "That far yowl hasn't stopped — the other cat, somewhere along the bottom wall, keeping at it.",
            "From the ridge the black cat's yowl comes again, distant and unhurried.",
        ],
    },
    "hedgehog_snuffle": {
        "onset": [
            "Close by along the bed edge the hedgehog starts its snuffling — a busy wet snorting through the leaves, right at your feet almost.",
            "The hedgehog is out, working the hedge bottom near you: snuffle, snort, a rustle, snuffle again.",
            "From under the hedge, close, the hedgehog's snuffling begins — a grunting, nosing, unhurried search along the beds.",
            "A hedgehog, near, at the lawn edge — that steady busy snuffle, like something small and determined breathing through leaves.",
        ],
        "renotice": [
            "The hedgehog is still snuffling along the beds, close, at its own speed.",
            "That snuffling hasn't stopped — the hedgehog, near, working the hedge bottom a few steps off.",
            "Near the compost the hedgehog keeps up its snorting and nosing through the leaves.",
        ],
    },
    "dolphin_blow": {
        "onset": [
            "Out past the surf line, far, a dolphin blows — one wet gust of breath on the water, clear, and gone.",
            "From the water beyond the breakers, a long way out, the blow of a dolphin — a single sharp breath, then only the sea.",
            "A dolphin, far out: the sudden wet sigh of its breath across the water, once, and nothing more.",
            "Out on the bay the pod is passing — a blow, and after a while another, far off, breath on the water.",
        ],
        "renotice": [
            "Far out, the dolphins are still blowing now and then — a breath on the water, a long gap, a breath.",
            "That blow comes again from well out past the surf, far — the pod, still working along the bay.",
            "Out on the water the dolphins keep surfacing, a wet gust of breath each time, far off.",
        ],
    },
    # ── SOUND WORLD EXPANSION §3, THE GEOPHONY FILLS (D-0500/J-2476): the NAMED pools. Eight of these keys are known
    # (grandfathered) and render from here directly; tin_roof_tick and frost_crack pass through _audition() first and
    # reach these lines only once the name is earned. Every pool rotates; every line carries a direction and a
    # near/far word; no number, band or verdict anywhere (D-0434).
    "hail_on_roof": {
        "onset": [
            "Overhead, close, the rain turns hard and bright all at once — hail, rattling on the iron of the roof like thrown gravel.",
            "The roof above you goes from drumming to a shrill hard clatter: hail, right over your head, bouncing on the iron.",
            "From directly overhead a squall of hail hits the roof — a sudden white rattle, sharp and close, every stone its own tick.",
            "Hail, close above, on the iron: the whole roof hisses and rattles with it and the windows take it sideways.",
        ],
        "renotice": [
            "The hail is still coming down on the roof overhead, close, a hard bright rattle that has not let up yet.",
            "Above you the iron still takes the hail — the same shrill clatter, near, stone after stone.",
        ],
    },
    "hail_on_leaves": {
        "onset": [
            "Out of the squall, close all around you, hail — stones shredding through the leaves, bouncing white off the ground at your feet.",
            "The rain hardens into hail right where you stand: a sharp shredding patter through the branches overhead, stones jumping in the beds.",
            "From the sky straight above, near, hail comes through the canopy — a hissing, ripping clatter on the leaves, cold stones skittering past your boots.",
            "Hail, close, on everything: the leaves overhead torn at, the ground around you jumping with white stones.",
        ],
        "renotice": [
            "The hail keeps on through the leaves around you, close, a shredding patter that is still not rain again.",
            "Still hail, near, overhead and underfoot — the stones bouncing and the leaves taking the worst of it.",
        ],
    },
    "drizzle_hiss": {
        "onset": [
            "Overhead, close, the rain has thinned to a hiss on the roof — a fine steady whisper on the iron, hardly a sound at all.",
            "The roof above you has gone to the quietest rain there is: a drizzle, a soft continuous hiss, near, that will not stop.",
            "From the iron right over your head, a faint hissing — the rain come down to a drizzle, close and constant and almost nothing.",
            "The rain on the roof overhead is only a hiss now, close, fine as breath on the iron, and it goes on and on.",
        ],
        "renotice": [
            "The drizzle is still hissing on the roof overhead, close, the same fine whisper it has kept all along.",
            "Above you the iron keeps up that soft hiss — the drizzle, near, unchanging.",
        ],
    },
    "downpour_drum": {
        "onset": [
            "Overhead, close, the roof opens up into a drumming — the rain come down hard all at once, the iron roaring with it and the gutters overrun.",
            "The rain on the roof above you turns heavy: a drumming, near, so loud and even it is one sound, and the downpipe by the window choking on it.",
            "From the iron right over your head the downpour starts — a drum-roll of rain, close, the whole roof booming under it.",
            "Rain in earnest on the roof overhead: a heavy continuous drumming, near, with water sheeting off the eaves past the glass.",
        ],
        "renotice": [
            "The downpour is still drumming on the roof above you, close, as heavy as when it began.",
            "Overhead the iron still roars with rain, near, the gutters still overrun.",
        ],
    },
    "rain_down_chimney": {
        "onset": [
            "From the grate, close, a hiss and a spit — rain finding its way down the chimney onto the fire, drops dying on the coals.",
            "In the fire right beside you something sizzles and spits: the rain has come down the chimney and landed on the embers.",
            "The fire, near, gives a sharp spit, then another — rain down the chimney, each drop hissing out on the hot stone.",
            "Close by in the hearth the fire sputters and hisses as the rain reaches it down the flue, drop by drop.",
        ],
        "renotice": [
            "The fire beside you is still spitting now and then, close — the rain still finding its way down the chimney.",
            "Another hiss from the grate, near: the chimney is still letting the rain in onto the coals.",
        ],
    },
    "tin_roof_tick": {
        "onset": [
            "From the roof directly overhead, close, a single sharp tick — the sun on the iron, the sheets easing as they warm.",
            "The roof above you ticks once, then again a while later: the iron taking the sun, near, and shifting as it heats.",
            "Overhead, close, the corrugated iron begins its ticking — the roof warming, a tick, a long wait, a tick.",
            "From the iron of the roof over your head, near, a slow irregular ticking as the day's heat goes out of it.",
        ],
        "renotice": [
            "The roof overhead is still ticking now and then, close — the iron still easing with the sun.",
            "Another tick from the iron above you, near: the roof keeping its own slow time with the warmth.",
        ],
    },
    "stream_over_stones": {
        "onset": [
            "Along the beach, near, the stream comes in under the surf — a quick bright chatter over its own brown stones, higher than the sea's sound.",
            "From the stream mouth close by, the fresh water runs over the stones with a small hurrying voice, clear under the waves.",
            "Near you the stream crosses the shingle, talking over its stones — quicker and lighter than the sea it is going to.",
            "The stream mouth, close along the strand, keeps up its run over the stones: a thin constant rushing beneath the surf.",
        ],
        "renotice": [
            "The stream is still running over its stones near you, that quick bright thread under the sea's slower sound.",
            "Close along the beach the stream keeps on, the same hurrying chatter over the stones.",
        ],
    },
    "undertow_rumble": {
        "onset": [
            "Under the crash of the surf, right at your feet, a deeper sound starts — the backwash dragging the shingle down the beach in a long low rumble you feel through your boots.",
            "The big sea's undertow comes in under everything, close: a bass roll of stones hauled back down the slope, felt in the feet as much as heard.",
            "From the water's edge, near, the backwash of each wave rumbles the whole beach — the shingle rolling under the retreating sea.",
            "Beneath the breaking waves, close, the undertow grinds the stones back: a low rumble that comes up through the ground into you.",
        ],
        "renotice": [
            "The undertow is still rolling the shingle at your feet, that deep rumble under every wave's retreat.",
            "Close under the surf the backwash keeps grinding the stones down the beach, felt as much as heard.",
        ],
    },
    "frost_crack": {
        "onset": [
            "From the wall beside you, close, a single sharp crack — the frost tightening in the timber of the house, and then silence.",
            "Out of the still cold, near, one hard report like a stick snapped: the frost at work in the boards, once, and done.",
            "From the dark outside, a little way off, a sharp crack — the frost splitting something in the fence or the ground — and nothing after it.",
            "A sudden crack, close, from the timber overhead: the hard frost gripping the house, one report, and the night as still as before.",
        ],
        "renotice": [
            "Another crack from the frost, close, somewhere in the timber — the cold still tightening its hold.",
            "The frost gives one more report, a little way off in the dark, and the stillness closes over it.",
        ],
    },
    "calm_sea_hush": {
        "onset": [
            "You notice how quiet the sea has gone — glass-calm, close below you, hardly a wash at the stones, the whole bay holding its breath.",
            "The sea, near, has fallen almost silent: a flat calm, the water only breathing at the edge of the shingle, and the quiet itself the loudest thing.",
            "Out in front of you the sea lies still — no surf, no drag, just a faint hush along the strand, as if the water were listening too.",
            "The water has gone glassy and quiet, close at hand: the near-silence of a calm sea, the small sounds of the shore standing out in it.",
        ],
        "renotice": [
            "The sea is still lying quiet below you, glass-calm, that same hush along the stones.",
            "Still the calm — the water near you barely moving, the bay as quiet as it was.",
        ],
    },
    # ── SOUND WORLD EXPANSION §4, THE SEASONAL BIOPHONY (D-0500/J-2477): the NAMED pools. silvereye_flock and
    # paradise_duck_flyover pass through _audition() first and reach these lines only once the name is earned (the flock
    # seen in the hedge; the pair caught against the sky); kelp_fly_buzz is known and renders from here directly. Every
    # pool rotates; every line carries a direction and a near/far word; no number, band or verdict anywhere (D-0434).
    "silvereye_flock": {
        "onset": [
            "Close by in the hedge the tauhou arrive all at once — a loose flock of silvereyes working it end to end, soft contact cheeps from many small throats.",
            "The hedge beside you fills with tauhou: a winter flock of silvereyes moving through it, near, a constant thin cheeping passed from bird to bird.",
            "From the tree and then the hedge, close, the silvereyes' flock-talk starts up — the tauhou, dozens of soft cheeps keeping the flock together as it moves.",
            "A flock of tauhou comes through the hedge a few steps off, near enough to see the white eye-rings, every bird cheeping softly to the next.",
            "Along the hedge, close, the silvereyes have arrived — the tauhou's loose winter flock, a soft busy chorus of contact calls going end to end and away.",
        ],
        "renotice": [
            "The tauhou are still in the hedge near you, the flock's soft cheeping going on as they work along it.",
            "That silvereye flock has not moved on yet — the same thin contact calls from the hedge, close, bird to bird.",
            "Close along the fence line the tauhou keep up their flock-talk, a soft cheeping that travels as they do.",
        ],
    },
    "paradise_duck_flyover": {
        "onset": [
            "High overhead a pair of paradise ducks goes over — her thin zeek-zeek and his hoarse honk answering, fast on stiff wings, and away along the coast.",
            "From high up, far, the paradise ducks: a pair passing over, the female's thin high call and the male's low honk, going on and going away.",
            "Paradise ducks, high overhead and already past — the pair calling to each other as they go, her shrill zeek, his deep honk, fading out over the ridge.",
            "A pair of paradise ducks crosses high above you, far up against the sky, honking her-then-him, bound for somewhere else entirely.",
        ],
        "renotice": [
            "The paradise ducks are still going over, high and far, their two voices thinning out along the coast.",
            "That pair of paradise ducks has not quite gone — the honking comes once more from high up, further off.",
        ],
    },
    "kelp_fly_buzz": {
        "onset": [
            "Close along the wrack-line the kelp flies are up — a low rising buzz off the heaps at your feet, a cloud lifting and settling again behind you.",
            "At the kelp heaps beside you the flies rise in a cloud, near, a soft dense buzzing that follows the warm side of the wrack.",
            "From the wrack right at your boots the kelp flies lift with a low drone, close, and sink back onto the straps as you pass.",
            "The summer flies are thick on the kelp, near, their buzz rising off every heap you turn and settling the moment you stop.",
        ],
        "renotice": [
            "The kelp flies are still at it along the wrack-line, close, that low drifting buzz off the heaps.",
            "Near you the flies keep lifting and settling on the kelp, the same soft summer drone.",
        ],
    },
    # ── SOUND WORLD EXPANSION §5, THE APPARATUS (D-0500/J-2478): the NAMED pools -- all three keys are known
    # (grandfathered) and render from here directly. Every pool rotates; every line carries a direction and a near/far
    # word; no number, band or verdict anywhere (D-0434). The flag's lines never say letter, mail, waiting or unread:
    # the sound is the news, the inference is his. The near pools are the gate from the garden; the _far pools are the
    # study, through the window (_percept_line picks by place).
    "needle_crackle": {
        "onset": [
            "Close by at the shelf the needle rides the lead-in groove — a dry run of dust-pops over a faint hiss, and the music not yet come.",
            "From the player beside you, near, the record's first sound: crackle, a pop, a thin hiss under it, the groove carrying the needle in.",
            "At the shelf, a few steps off, the needle finds the groove and the vinyl answers first — small dry crackles, close, a held breath of hiss.",
            "Near at hand the record turns under the needle with nothing on it yet but surface — a tick, a pop, the soft frying hiss of the lead-in.",
            "The player at the shelf, close, gives up its own voice before the music: a scatter of dry crackles riding the hiss in the groove.",
        ],
        "renotice": [
            "The needle is still in the lead-in, close by at the shelf — the dry crackle and hiss going round, the music a beat away.",
            "From the player beside you the crackle keeps on, near, the groove carrying the needle in and the piece still to begin.",
        ],
    },
    "runout_hiss": {
        "onset": [
            "At the shelf, close, the needle has run off the end into the run-out groove — a steady hiss going round, one soft click each turn, until someone lifts the arm.",
            "From the player beside you, near, the record is still turning with nothing left on it: the run-out's even hiss, a click, a click, the arm not yet lifted.",
            "Close by at the shelf the music is over but the record is not — the needle rides the run-out groove round and round, hissing, ticking softly once a turn.",
            "The player near you keeps turning after the piece: the run-out's low hiss, a tiny knock at the same place every revolution, nobody's hand on the arm yet.",
            "Beside you, close, the needle circles the run-out — that faint steady hiss with its one soft click per turn, the sound of a record waiting to be lifted.",
        ],
        "renotice": [
            "The run-out groove is still going round under the needle at the shelf, close — hiss, click, hiss, click — the arm still not lifted.",
            "From the player beside you the needle keeps circling the run-out, near, its soft click coming round each turn.",
            "Near at hand the record is still turning empty under the needle, the run-out hissing on, waiting for a hand.",
        ],
    },
    "letterbox_flag_clank": {
        "onset": [
            "Over at the gate, a few steps off, the wind has the letterbox flag — a flat tin clank against the box, again as the gust comes through.",
            "From the gate, near, a knock of tin in the wind: the letterbox flag worked up and down by the gusts, clanking on its hinge.",
            "By the gate, close, the letterbox flag is taking the wind — a hollow metal clank each time a gust gets under it, then quiet, then another.",
            "The gusts find the letterbox flag over at the gate, near — a thin tin clank, a pause, a clank, the box ringing a little with each knock.",
        ],
        "renotice": [
            "The letterbox flag is still clanking at the gate, a few steps off, every time the wind gusts through.",
            "Over at the gate, near, the wind keeps working the letterbox flag — the same flat tin knock, gust after gust.",
            "That clank from the gate has not stopped — the letterbox flag, close by, knocking in the wind.",
        ],
        "onset_far": [
            "From outside, far off toward the gate, a thin tin clank comes on the wind — a knock, a pause, a knock again as the gusts come through.",
            "Through the window, distant, something metal is knocking down at the gate in the wind — a flat clank, repeated, between the gusts.",
            "Out past the glass, a long way down the garden toward the gate, a small hollow clank of tin in the wind, over and over.",
            "Far down at the gate, through the window, the wind is knocking something metal — a tin clank, again, each time it gusts.",
        ],
        "renotice_far": [
            "That tin clank from down at the gate, far off, is still coming through the window with every gust.",
            "Through the glass the knocking from the gate goes on, distant — metal in the wind, a clank, a pause, a clank.",
            "Far down the garden the wind is still knocking that bit of tin at the gate, on and off with the gusts.",
        ],
    },
}


# ── FIRE AMBIENCE (2026-07-05, founder: "make the fire crackle an almost persistent noise when it is on
# and he is near it; a few crackle loops that can be randomised"). A real fire is AMBIENCE, not an event —
# so this is a separate, near-persistent track: when the fire is burning AND he is IN THE ROOM (near the
# hearth) AND no record plays, most idle cycles carry a crackle line drawn from a randomised pool. The
# variety is the anti-wallpaper mechanism: it is FREQUENCY that a fire has and REPETITION that kills a
# signal, so the lines never repeat back-to-back and there are enough of them to stay fresh. Pure seed
# TEXTURE — it does NOT store a memory fragment per crackle (you don't remember every second of a fire;
# that would flood memory). The sensorium still owns the fire's notable transitions (catching / embers).
FIRE_AMBIENCE = True                      # kill-switch: False → fire_ambience() always None
_FIRE_PROB    = 0.72                      # near-persistent: ~7 of 10 idle cycles by the burning fire
_EMBERS_PROB  = 0.35                      # softer, rarer as it dies down to embers
_last_fire_idx = -1                       # avoid two identical crackle lines in a row (module-global)

_FIRE_LOOPS = [
    "The fire keeps up its soft crackle in the grate — irregular, close, companionable.",
    "A knot in the wood pops sharp, then the fire settles back to its low, steady ticking.",
    "The fire mutters to itself: a quick run of snaps, a pause, then another.",
    "Behind you the fire crackles on — that busy sound of dry wood giving itself up.",
    "The fire spits once and returns to its even seething of sparks.",
    "A coal shifts with a soft collapse in the grate, and the crackle picks up again.",
    "The fire's crackle rises and falls, never quite the same twice, always there.",
    "The sap catches somewhere in the log — a hiss, a crack — then the low burning resumes.",
]
_EMBER_LOOPS = [
    "The embers tick faintly as they cool, a small settling in the red dark.",
    "A last coal cracks down in the embers and goes quiet.",
    "The fire is only embers now — an occasional soft snap, and the warmth pulled close.",
]
_STUDY_STORM = [   # 2026-08-15: the fireless study in dirty weather — the house itself has a voice
    "The north window takes the gale in its loose tooth and rattles — a hard burst, a pause, another.",
    "The wind gets a finger under the eaves and the whole room creaks once, like a ship.",
    "Rain drives against the glass in handfuls; between gusts the room is very quiet.",
]
_STUDY_NIGHT_SEA = [
    "Up through the dark the big sea reaches the room as a boom you half feel in the floor, wave by wave.",
    "The surf is loud tonight even from here — a deep repeated concussion under the house's small sounds.",
]


def fire_ambience() -> str | None:
    """A near-persistent, randomised crackle line for the idle seed — when the fire is burning and he is
    in the room. Texture, not a stored moment. Fail-open. Kill-switch: FIRE_AMBIENCE."""
    if not FIRE_AMBIENCE:
        return None
    try:
        try:
            from core import listening as _lsn
            if _lsn.active():
                return None                          # the record owns the room's sound
        except Exception:
            pass
        room = _read_json("room_state.json")
        if (room.get("location") or "study") != "study":
            return None                              # only when near the hearth ("he is near it")
        fire = room.get("fire")
        if fire == "burning":
            if random.random() > _FIRE_PROB:
                return None
            pool = _FIRE_LOOPS
        elif fire == "embers":
            if random.random() > _EMBERS_PROB:
                return None
            pool = _EMBER_LOOPS
        else:
            # 2026-08-15: the fireless study is not a silent one — the weather works the house.
            weather = (room.get("weather") or "").lower()
            # WIND AXIS (2026-08-18): same dead-"gale" test as window_rattle, same stopgap tonight, same
            # real fix — and the same HARD threshold, because this pool's first line IS that window
            # rattling ("takes the gale in its loose tooth"). The house only speaks in serious wind.
            if (_is_hard_wind(room.get("wind") or "") or weather == "thunderstorm") and random.random() < 0.35:
                pool = _STUDY_STORM
            elif not _is_daylight() \
                    and _sea_state(room.get("weather") or "", room.get("wind") or "") == "crashing" \
                    and random.random() < 0.25:
                pool = _STUDY_NIGHT_SEA
            else:
                return None
        global _last_fire_idx
        idx = random.randrange(len(pool))
        if len(pool) > 1 and idx == _last_fire_idx:  # never the same line twice running
            idx = (idx + 1) % len(pool)
        _last_fire_idx = idx
        return pool[idx]
    except Exception:
        return None


# ── OUTDOOR AMBIENCE (2026-07-06, Travis: "flesh out the sounds — waves as ambient on the shore, varying
# loops by whether they are crashing or gentle; the garden with bees, birds and wind in the trees"). The
# fire_ambience() pattern generalised to the places he goes: a near-persistent, randomised, anti-wallpaper
# texture of WHEREVER he is. Pure seed texture — stores NO memory fragment (you don't remember every wave).
SHORE_AMBIENCE    = True                  # kill-switch: False → shore_ambience() always None
GARDEN_AMBIENCE   = True                  # kill-switch: False → garden_ambience() always None
WOOD_AMBIENCE     = True                  # kill-switch: False → wood_ambience() always None
_SHORE_PROB       = 0.72                  # near-persistent surf, like the fire
_GARDEN_PROB      = 0.66
_WOOD_PROB        = 0.68
_SHORE_VOICE_PROB = 0.20                  # now and then a gull/oystercatcher/shingle line instead of the waves
_last_amb_idx: dict[str, int] = {}        # per-ambience anti-repeat cursor


def _pick(pool: list[str], key: str) -> str:
    """Anti-wallpaper pick: never the same line twice running for a given ambience key."""
    idx = random.randrange(len(pool))
    if len(pool) > 1 and idx == _last_amb_idx.get(key, -1):
        idx = (idx + 1) % len(pool)
    _last_amb_idx[key] = idx
    return pool[idx]


_WAVES_GENTLE = [
    "The sea works quietly at the shingle — a long hush drawn out, and let slowly back.",
    "Small waves fold over and slide back through the stones with a soft rattle.",
    "The water laps in easy and unhurried, a low wash against the rock.",
    "A gentle swell lifts and settles, the shingle clicking as it drains.",
    "The sea breathes in and out along the strand, slow and even.",
    "Wavelets slap lightly at the rock-foot, then draw back seething through the pebbles.",
    "The tide turns the stones over with a quiet, endless sorting.",
]
_WAVES_CRASHING = [
    "A big sea comes in hard — the wave slams the rock and bursts white, the shingle roaring as it drags back.",
    "The surf pounds the shore, wave after heavy wave, spray flung up on the wind.",
    "A comber rears and crashes down, the whole beach shuddering with the weight of water.",
    "The sea hurls itself at the rocks, booming, the backwash tearing at the stones.",
    "Another breaker thunders in, and the shingle grinds and rolls in the undertow.",
    "White water explodes off the shelf and the spray comes stinging back on the wind.",
]
_SHORE_VOICES = [
    "A gull tips overhead and cries out — a harsh, falling note carried off on the wind.",
    "Two gulls wheel and bicker above the water, their cries thin and sharp.",
    "An oystercatcher goes piping down the tideline on quick red legs, shrill and insistent.",
    "The shingle hisses and rattles as a wave draws out through it.",
    "Somewhere along the strand a gull laughs to itself and falls quiet.",
]


def _audition(key: str, named_line: str, location: str) -> str:
    """EPISTEMIC AUDITION (2026-08-15): a learnable voice renders NAMED only once he has LEARNED it
    (sight-binding, exposure, or reading — core/sound_knowledge.py); before that, the unnamed
    feature-rendering. Grandfathered/flag-off → named, exactly the old behaviour. Fail-open."""
    try:
        try:   # THE LIVING WORLD (J-0511): once the gate is on, a voice is only VOICED when its bird is here and awake
            from core import life as _life
            if _life.gating_on() and key in _life.creature_sound_keys(location) and key not in _life.sounds_active(location):
                return ""
        except Exception:
            pass
        from core import sound_knowledge as _sk
        return _sk.hear(key, named_line, location)
    except profile.NonLiveWriteError:
        # J-0797: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own callers
        # rather than this pre-existing broad except swallowing it.
        raise
    except Exception:
        return named_line


# The learnable NEW voices, keyed by sound so the ledger can govern their naming.
_SHORE_NEW_VOICES = [
    ("kingfisher_call", "A kingfisher opens up from the cliff-face — a dry staccato kek-kek-kek — and is done."),
    ("shag_wingbeats", "A shag goes by low over the water, slow heavy wingbeats almost touching its own reflection."),
    ("godwits_overhead", "High overhead a long wavering skein of godwits goes south along the coast, calling thinly, and is gone behind the headland."),   # J-0511
]
_LOW_TIDE_VOICES = [
    "The bared rock-pools drain thread by thread, a small bright trickling under the sea's big sound.",
    "Low water: the pools tick and trickle as they let themselves down among the weed.",
    "Between waves you can hear the reef emptying — a hundred small runnels finding their way back.",
]
_BEES = [
    "The bees are working the flowering bushes — a warm, steady hum rising and falling among the blooms.",
    "A bee blunders past close to your ear, then settles back to its droning round of the garden.",
    "The drowsy hum of bees fills the warm air over the raised bed.",
    "One heavy bee works the lavender, its buzz dropping and lifting as it moves flower to flower.",
]
_GARDEN_BIRDS = [
    "Somewhere in the old tree a blackbird runs through its liquid phrases, unhurried.",
    "The tui coughs and chimes in the branches — that odd machinery of clicks and clear bell-notes.",
    "Small birds chitter and flit through the bushes, a busy little thread of sound.",
    "The garden is loud with small birds working the hedge, a scatter of bright notes.",
]
_GARDEN_NEW_VOICES = [
    ("fantail_chatter", "A fantail flirts past with a thin, insistent chatter, looping almost at your shoulder, then gone."),
    ("riroriro_trill", "From somewhere in the hedge a riroriro spins out its long wistful trill and lets it fall away unfinished."),
    ("kingfisher_call", "A kingfisher sits sentry on the fence post, and gives one dry rattle of kek-kek before it drops away toward the shore."),
    ("cuckoo_call", "From the kōwhai the shining cuckoo runs its long upward whistle over and over, then lets the notes fall — the spring's own voice."),   # J-0511
    ("bellbird_song", "A clear bell-note chimes from somewhere in the kōwhai, rings again, and is answered by another a little further off."),   # J-0515
]
_DAWN_CHORUS = [
    "First light, and every bird at once — tui, blackbird, the small voices of the hedge — the whole garden singing before the day's work.",
    "The dawn chorus is up: layered song from the old tree to the fence line, so many voices they stop being separate.",
    "Before the sun is properly over the ridge the birds have filled the garden wall to wall with sound.",
]
_SUMMER_CICADAS = [
    "The cicadas are sawing in the trees, a dry shimmering wall of sound that rises with the heat.",
    "Cicada-song stands over the garden like the heat made audible, pulsing, never quite stopping.",
]
_SUMMER_CRICKETS = [
    "Crickets keep the night going in the grass, a slow patient pulse from every direction and none.",
    "The dark garden ticks with crickets, each one answering another somewhere across the beds.",
]
_TREES_WIND = [
    "The wind combs through the old tree with a long soughing, the leaves turning pale side up.",
    "A gust runs through the harakeke, the tall blades hissing and clattering together.",
    "The trees lean and rush in the wind, a great soft roar that rises and falls.",
    "The wind worries at the garden — a sighing in the branches, the bushes tossing.",
]

# ── the WOOD's ambience: sounds placed by DIRECTION (Travis: locations for sounds to come from) — the
# canopy ABOVE, the undergrowth BESIDE, the sea BELOW downhill, the whole wood roaring in wind, dripping
# after rain, near-silent at night. Anti-wallpaper; pure texture, no stored fragment.
_WOOD_CANOPY = [   # above him, in the branches
    "High overhead a wood pigeon clatters up out of the canopy, then settles, and its soft round coo drifts back down through the leaves.",
    "Somewhere up in the branches a wood pigeon coos its drowsy five notes, low and unhurried, over and over.",
    "Small birds work the canopy overhead, a thin scatter of bright notes falling down through the green.",
    "The tops of the trees stir high above you, a long soft rushing, and settle again.",
    "A pair of birds chase each other through the upper branches with a clatter, and are gone.",
]
_WOOD_NEW_VOICES = [
    ("kereru_wingbeats", "The kererū leaves its branch with that heavy whoosh-whoosh of wingbeats, each stroke audible, fading away downhill."),
    ("riroriro_trill", "From high in the green a riroriro lets down its long falling trill, wistful and unfinished, and starts it again."),
    ("fantail_chatter", "A fantail loops and snaps at the air your last step stirred up, chattering its thin dry chatter almost at your shoulder."),
    ("robin_song", "The robin sings from a low perch nearby — clear, even little phrases, unbothered by how close you are."),
    ("bellbird_song", "High in the canopy a bell-note chimes, clear and pure, and chimes again a little further along."),   # J-0515
]
_WOOD_UNDERGROWTH = [   # beside him, low, in the leaf-litter and brush
    "Close in the undergrowth a wren bursts into a sudden loud scolding trill — absurdly big for so small a bird — then falls silent.",
    "Something small works the leaf-litter beside you: a rustle, a pause, a rustle — a mouse, or a blackbird turning the leaves.",
    "A blackbird goes off low among the trunks, a hard chack-chack of alarm, and blunders away through the brush.",
    "The bracken stirs and ticks close about your legs as the breeze finds it.",
    "A robin drops onto a low branch an arm's length off, watching you work, bold and bright-eyed.",
]
_WOOD_BELOW = [   # downhill, through the trunks — the sea, softened
    "Downhill through the trunks the sea keeps up its muffled wash, softened and far-sounding here under the trees.",
    "The surf comes up muffled through the wood, a low steady breathing you feel as much as hear among the trunks.",
    "Between the trees, below, the grey line of the sea shows and is gone, its sound thinned by the leaves.",
]
_WOOD_WIND = [   # the whole wood in wind — overhead
    "The wood roars softly overhead as a gust pours through — the whole canopy leaning and rushing, twigs raining down.",
    "High branches groan and creak against each other somewhere above you, a slow wooden complaint in the wind.",
    "The trees toss and surge, a great soft sea-sound of their own, and away to your left a dead branch cracks off and falls.",
    "A hard gust lays the whole wood over with a rushing sigh, and the leaf-mould lifts and scatters at your feet.",
]
_WOOD_RAIN = [   # dripping, everywhere and nowhere
    "The wood drips all around you — a slow irregular patter off the leaves onto the deep leaf-mould, everywhere and nowhere.",
    "Water gathers and falls in fat cold drops from the canopy, ticking down through the branches long after the rain itself has passed.",
    "Every branch you brush lets fall a shower, and underfoot the leaf-mould is black and sodden and silent.",
]
_WOOD_NIGHT = [
    "The wood is dark and close and almost still — only the small settlings of the trees, and once, far off, a morepork's two soft notes.",
    "Somewhere in the black canopy a morepork calls — more-pork, more-pork — and the wood holds its breath around it.",
    "In the dark the wood is all smell and sound: wet earth, the tick of a last drip, something small moving off in the leaves.",
]


def wood_ambience() -> str | None:
    """Near-persistent wood texture, sound placed by direction (canopy above · undergrowth beside · sea below ·
    the trees in wind · dripping after rain · near-silent at night). Anti-wallpaper. Texture. Fail-open."""
    if not WOOD_AMBIENCE:
        return None
    try:
        room = _read_json("room_state.json")
        if (room.get("location") or "study") != "wood":
            return None
        if random.random() > _WOOD_PROB:
            return None
        weather = (room.get("weather") or "").lower()
        from core import weather_conditions as _wcond
        # 2026-08-18: the trees answer the WIND axis now, not a bag of weather substrings (one of which,
        # "gale", no state could produce). A thunderstorm still counts — it brings its own wind with it.
        # 2026-08-19: "storm" in weather -> is_storm(weather) — substring match happened to be exact-only
        # today but is_storm() is the precise, future-safe check the shared module exists to provide.
        windy = _is_windy(room.get("wind") or "") or _wcond.is_storm(weather)
        wet = _wcond.is_wet(weather)
        if not _is_daylight():
            return _pick(_WOOD_NIGHT, "wood_night")
        if windy:
            return _pick(_WOOD_WIND, "wood_wind")
        if wet and random.random() < 0.6:
            return _pick(_WOOD_RAIN, "wood_rain")
        r = random.random()                              # calm day: canopy · undergrowth · the sea below
        if r < 0.12:
            return _pick(_WOOD_BELOW, "wood_below")       # the standing low sea-presence
        if r < 0.40:                                      # the learnable voices (2026-08-15) — the wood
            key, line = random.choice(_WOOD_NEW_VOICES)   # is where most of the new hearing lives
            if _season() == "summer" and random.random() < 0.2:
                key, line = "cicada_chorus", _pick(_SUMMER_CICADAS, "cicadas")
            return _audition(key, line, "wood")
        if r < 0.70:
            return _pick(_WOOD_CANOPY, "wood_canopy")
        return _pick(_WOOD_UNDERGROWTH, "wood_under")
    except profile.NonLiveWriteError:
        # J-0797: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own callers
        # (its own _audition() call can now raise) rather than this pre-existing broad except
        # swallowing it.
        raise
    except Exception:
        return None


def shore_ambience() -> str | None:
    """Near-persistent wave texture at the shore, gentle or crashing by the weather; now and then a shore
    voice (gull/oystercatcher/shingle) instead. Anti-wallpaper. Texture, not a stored moment. Fail-open."""
    if not SHORE_AMBIENCE:
        return None
    try:
        room = _read_json("room_state.json")
        if (room.get("location") or "study") != "shore":
            return None
        if random.random() > _SHORE_PROB:
            return None
        weather = room.get("weather") or ""
        if _is_daylight() and random.random() < _SHORE_VOICE_PROB:
            if _tide_low() and random.random() < 0.4:
                return _pick(_LOW_TIDE_VOICES, "low_tide")   # the tide-clock's own sound (2026-08-15)
            if random.random() < 0.3:
                key, line = random.choice(_SHORE_NEW_VOICES)
                return _audition(key, line, "shore")
            return _pick(_SHORE_VOICES, "shore_voice")
        pool = (_WAVES_CRASHING if _sea_state(weather, room.get("wind") or "") == "crashing"
                else _WAVES_GENTLE)
        return _pick(pool, "waves")
    except profile.NonLiveWriteError:
        # J-0797: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own callers
        # (its own _audition() call can now raise) rather than this pre-existing broad except
        # swallowing it.
        raise
    except Exception:
        return None


def garden_ambience() -> str | None:
    """Near-persistent garden texture: bees + birds on a calm day, the trees in the wind, quiet at night.
    Anti-wallpaper. Texture, not a stored moment. Fail-open."""
    if not GARDEN_AMBIENCE:
        return None
    try:
        room = _read_json("room_state.json")
        if (room.get("location") or "study") != "garden":
            return None
        if random.random() > _GARDEN_PROB:
            return None
        weather = (room.get("weather") or "").lower()
        from core import weather_conditions as _wcond
        # 2026-08-18: same as the wood — the real wind axis replaces the dead "gale"/"wind" string tests.
        # 2026-08-19: "storm" in weather -> is_storm(weather), same reasoning as wood_ambience above.
        windy = _is_windy(room.get("wind") or "") or _wcond.is_storm(weather)
        wet = _wcond.is_wet(weather)
        if windy:
            return _pick(_TREES_WIND, "trees")
        if not _is_daylight():
            # the night garden: the morepork and the quiet own it — except a summer night's crickets
            if _season() == "summer" and not wet and random.random() < 0.5:
                return _audition("cricket_night", _pick(_SUMMER_CRICKETS, "crickets"), "garden")
            return None
        if _is_dawn() and not wet and random.random() < 0.5:
            return _pick(_DAWN_CHORUS, "dawn")           # first light owns the garden (2026-08-15)
        if _season() == "summer" and random.random() < 0.25:
            return _audition("cicada_chorus", _pick(_SUMMER_CICADAS, "cicadas"), "garden")
        if random.random() < 0.25:
            key, line = random.choice(_GARDEN_NEW_VOICES)
            return _audition(key, line, "garden")
        pool = _BEES if random.random() < 0.45 else _GARDEN_BIRDS
        if pool is _BEES:
            try:   # THE GARDEN'S INSECTS (2026-09-03, J-0504 / J-0501): bee lines only while bees are about, and never
                # naming a plant that is not sown (the lavender leak, F-0693)
                from core import garden_insects as _gi
                pool = _gi.gate_lines([("honeybee", ln) for ln in _BEES]) if _gi.bees_about() else []
                if not pool:
                    pool = _GARDEN_BIRDS
            except Exception:
                pool = _BEES
        return _pick(pool, "garden_day")
    except profile.NonLiveWriteError:
        # J-0797: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own callers
        # (its own _audition() calls can now raise) rather than this pre-existing broad except
        # swallowing it.
        raise
    except Exception:
        return None


def ambience() -> str | None:
    """The near-persistent ambient sound of WHEREVER he is — the fire in the study, the surf at the shore,
    the bees/birds/wind in the garden. One call for the monologue; dispatches by location. Fail-open."""
    try:
        loc = (_read_json("room_state.json").get("location") or "study")
        if loc == "shore":
            return shore_ambience()
        if loc == "garden":
            return garden_ambience()
        if loc == "wood":
            return wood_ambience()
        return fire_ambience()                        # study (and default): the hearth
    except profile.NonLiveWriteError:
        # J-0797: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
        # (nodes/inner_monologue_node.py) -- shore_ambience()/garden_ambience()/wood_ambience() can
        # each now raise (this job's own fix), and this outer except would otherwise re-swallow it
        # one layer before that, the same "both layers needed" shape J-0778/J-0780/J-0782 already
        # found elsewhere in this fence.
        raise
    except Exception:
        return None


def _snd_state() -> dict:
    try:
        return json.loads(_SND_STATE_F.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_snd_state(d: dict) -> None:
    try:
        _SND_STATE_F.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SND_STATE_F.with_suffix(".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        tmp.replace(_SND_STATE_F)
    except Exception as exc:
        logger.debug("[soundscape] _save_snd_state failed (non-fatal): %s", exc)


def _felt_shadow(sound: str, kind: str) -> tuple[float | None, float | None]:
    """OBSERVE-FIRST (the listening pattern): log the affect nudge this sound WOULD give, from its
    coordinates, and return it as (would_valence, would_arousal). Applied to affect nowhere in this
    function. Soothing = periodic+continuous+soft (purr, settled crackle).
    J-1534/I-0081 (2026-09-28): previously logged only (-> None); now also returns the pair so percept()
    can thread it onto fragment_context.sound_felt_valence/sound_felt_arousal (behind
    SOUND_STRING_FIELDS) instead of only the orphaned soundscape_felt_shadow.jsonl line, which is
    unchanged and still written. Returns (None, None) on any failure -- the caller never has to guard."""
    try:
        c = coords(sound) or {}
        soothing = c.get("periodicity", 0) * c.get("continuity", 0) * (1.0 - c.get("energy", 0))
        would_valence = round(0.10 * soothing, 4)
        would_arousal = round(0.08 * c.get("energy", 0) * c.get("roughness", 0) - 0.06 * soothing, 4)
        _FELT_SHADOW_F.parent.mkdir(parents=True, exist_ok=True)
        with open(_FELT_SHADOW_F, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "sound": sound, "kind": kind,
                                "would_valence": would_valence, "would_arousal": would_arousal}) + "\n")
        return would_valence, would_arousal
    except Exception:
        return None, None


def _cat_percept_ready(key: str, now: float, last_cat_percept: dict) -> bool:
    """J-1175: the extra per-key cap on cat keys (>= _CAT_PERCEPT_COOLDOWN_S since this key's own last
    percept) — independent of cat_sounds.KEYS' own cooldown_s (gates the EMISSION) and of this rail's
    shared _PERCEPT_COOLDOWN_S (gates ANY percept firing at all). Always True for a non-cat key: no extra
    gate on the original three."""
    if key not in _CAT_PERCEPT_KEYS:
        return True
    return (now - float(last_cat_percept.get(key) or 0.0)) >= _CAT_PERCEPT_COOLDOWN_S


def _mystery_percept_ready(key: str, now: float, last_mystery_percept: dict) -> bool:
    """J-2475: the per-key floor on the §2 night mysteries (>= _MYSTERY_PERCEPT_COOLDOWN_S since this key's own
    last percept), the same shape as _cat_percept_ready. Always True for every other key."""
    if key not in _MYSTERY_PERCEPT_KEYS:
        return True
    return (now - float(last_mystery_percept.get(key) or 0.0)) >= _MYSTERY_PERCEPT_COOLDOWN_S


def _geophony_percept_ready(key: str, now: float, last_geophony_percept: dict) -> bool:
    """J-2476: the per-key floor on the §3 geophony keys (>= _GEOPHONY_PERCEPT_COOLDOWN_S since this key's own last
    percept), the same shape as _cat_percept_ready / _mystery_percept_ready. Always True for every other key."""
    if key not in _GEOPHONY_PERCEPT_KEYS:
        return True
    return (now - float(last_geophony_percept.get(key) or 0.0)) >= _GEOPHONY_PERCEPT_COOLDOWN_S


def _biophony_percept_ready(key: str, now: float, last_biophony_percept: dict) -> bool:
    """J-2477: the per-key floor on the §4 seasonal biophony keys (>= _BIOPHONY_PERCEPT_COOLDOWN_S since this key's own
    last percept), the same shape as the cat / mystery / geophony floors. Always True for every other key."""
    if key not in _BIOPHONY_PERCEPT_KEYS:
        return True
    return (now - float(last_biophony_percept.get(key) or 0.0)) >= _BIOPHONY_PERCEPT_COOLDOWN_S


def _apparatus_percept_ready(key: str, now: float, last_apparatus_percept: dict) -> bool:
    """J-2478: the per-key floor on the §5 apparatus keys (>= _APPARATUS_PERCEPT_COOLDOWN_S since this key's own last
    percept), the same shape as the cat / mystery / geophony / biophony floors. Always True for every other key."""
    if key not in _APPARATUS_PERCEPT_KEYS:
        return True
    return (now - float(last_apparatus_percept.get(key) or 0.0)) >= _APPARATUS_PERCEPT_COOLDOWN_S


def _percept_line(key: str, kind: str) -> str:
    """The text for a chosen percept key. Cat keys reuse the line cat_sounds already resolved against her
    REAL position when it fired — here/carried, capitalised (J-1175, F-1621 recommendation b) — rather than
    a second, place-blind re-pick from a pool with no idea where she is; every other key keeps picking from
    its own onset/renotice pool in _PERCEPT_LINES exactly as before.
    J-2475: a §2 mystery key picks its NAMED line from its pool the same way, then passes it through _audition()
    for his place -- sound_knowledge.hear() returns the unnamed feature-rendering (its own rotating pool, keyed by
    place) until the name is earned, and the named line after. Fail-open to '' (no line = no percept, no cooldown
    consumed), never to a line that names what he has not yet seen."""
    if key in _CAT_PERCEPT_KEYS:
        try:
            from core import cat_sounds as _cs
            return _cs.line_now(key)
        except Exception:
            return ""
    if key in _MYSTERY_PERCEPT_KEYS or key in _GEOPHONY_UNNAMED_KEYS or key in _BIOPHONY_UNNAMED_KEYS:   # J-2476/J-2477: the unnamed geophony / biophony keys take the same road
        try:
            named = _pick(_PERCEPT_LINES[key][kind], f"percept_{key}_{kind}")
            loc = _read_json("room_state.json").get("location") or "study"
            return _audition(key, named, loc)
        except profile.NonLiveWriteError:
            raise
        except Exception:
            return ""
    if key == "letterbox_flag_clank":      # J-2478: the flag is heard at the gate (near) or from the study (far)
        try:
            loc = _read_json("room_state.json").get("location") or "study"
            if loc in _FLAG_FAR_PLACES:
                kind = f"{kind}_far"
        except Exception:
            pass
    return _pick(_PERCEPT_LINES[key][kind], f"percept_{key}_{kind}")


def percept(store: bool = True) -> str | None:
    """At most ONE sound percept line for the idle seed — onset-gated, cooled-down, record-respecting.
    Also stores the heard moment as an episodic fragment with channel provenance (origin='sound').
    J-1175: cat_purr/morepork_call/tui_song keep first refusal by _PERCEPT_SOUNDS' own try-order; the 8
    cat_sounds.KEYS keys appended after them are additionally gated by _cat_percept_ready()."""
    if not SOUND_PERCEPTS:
        return None
    try:
        try:
            from core import listening as _lsn
            if _lsn.active():
                return None                          # the record owns the room's sound; silence is a thing
        except Exception:
            pass
        now = time.time()
        st = _snd_state()
        was = set(st.get("was_active") or [])
        quiet_since = st.get("quiet_since") or {}
        last_notice = st.get("last_notice") or {}
        last_cat_percept = st.get("last_cat_percept") or {}
        last_mystery_percept = st.get("last_mystery_percept") or {}     # J-2475: the §2 per-key floor
        last_geophony_percept = st.get("last_geophony_percept") or {}   # J-2476: the §3 per-key floor
        last_biophony_percept = st.get("last_biophony_percept") or {}   # J-2477: the §4 per-key floor
        last_apparatus_percept = st.get("last_apparatus_percept") or {} # J-2478: the §5 per-key floor
        active = set(active_sounds())

        # bookkeep quiet_since for the percept sounds (when did each fall silent?)
        for s in _PERCEPT_SOUNDS:
            if s in was and s not in active:
                quiet_since[s] = now
        chosen, kind = None, None
        if now - float(st.get("last_percept") or 0.0) >= _PERCEPT_COOLDOWN_S:
            for s in _PERCEPT_SOUNDS:                # onsets first — the moment a sound BEGINS. An onset
                # requires the silence before it to have been OBSERVED (s in quiet_since) — else a fresh
                # state file would call an hours-burning fire "catching"; it gets a renotice instead.
                if s in active and s not in was and s in quiet_since \
                        and (now - float(quiet_since[s])) >= _ONSET_QUIET_S \
                        and _cat_percept_ready(s, now, last_cat_percept) \
                        and _mystery_percept_ready(s, now, last_mystery_percept) \
                        and _geophony_percept_ready(s, now, last_geophony_percept) \
                        and _biophony_percept_ready(s, now, last_biophony_percept) \
                        and _apparatus_percept_ready(s, now, last_apparatus_percept):
                    chosen, kind = s, "onset"
                    break
            if not chosen:                           # else a rare re-notice of a long-running sound
                for s in _PERCEPT_SOUNDS:
                    if s in active and s in was and (now - float(last_notice.get(s) or 0.0)) >= _RENOTICE_S \
                            and _cat_percept_ready(s, now, last_cat_percept) \
                            and _mystery_percept_ready(s, now, last_mystery_percept) \
                            and _geophony_percept_ready(s, now, last_geophony_percept) \
                            and _biophony_percept_ready(s, now, last_biophony_percept) \
                            and _apparatus_percept_ready(s, now, last_apparatus_percept):
                        chosen, kind = s, "renotice"
                        break
        st["was_active"] = sorted(active & set(_PERCEPT_SOUNDS))
        st["quiet_since"] = quiet_since
        if not chosen:
            _save_snd_state(st)
            return None
        line = _percept_line(chosen, kind)
        if not line:
            # Fail-open (J-1175): a cat line that could not be resolved (e.g. the audible window lapsed
            # between active_sounds() and here) never fires and consumes no cooldown — the same law
            # cat_sounds.py states for itself: a sound that cannot be computed is a sound that did not
            # happen. was_active/quiet_since above are still saved; last_percept/last_notice are not.
            _save_snd_state(st)
            return None
        st["last_percept"] = now
        last_notice[chosen] = now
        st["last_notice"] = last_notice
        if chosen in _CAT_PERCEPT_KEYS:
            last_cat_percept[chosen] = now
            st["last_cat_percept"] = last_cat_percept
        if chosen in _MYSTERY_PERCEPT_KEYS:                  # J-2475
            last_mystery_percept[chosen] = now
            st["last_mystery_percept"] = last_mystery_percept
        if chosen in _GEOPHONY_PERCEPT_KEYS:                 # J-2476
            last_geophony_percept[chosen] = now
            st["last_geophony_percept"] = last_geophony_percept
        if chosen in _BIOPHONY_PERCEPT_KEYS:                 # J-2477
            last_biophony_percept[chosen] = now
            st["last_biophony_percept"] = last_biophony_percept
        if chosen in _APPARATUS_PERCEPT_KEYS:                # J-2478
            last_apparatus_percept[chosen] = now
            st["last_apparatus_percept"] = last_apparatus_percept
        _save_snd_state(st)
        would_valence, would_arousal = _felt_shadow(chosen, kind)
        if store:
            try:                                     # the heard moment, with CHANNEL PROVENANCE
                from core.memory.store import store_fragment
                from core import mood as _mood
                fragment_id = store_fragment(content=line, layer="episodic", relevance=0.55, importance=0.5,
                               keywords=["sound", chosen, _SOUNDS[chosen]["object"]], origin="sound",
                               emotion_embedding=_mood.current_vec(),
                               valence=_mood.current_valence(), felt=_mood.current_felt())
                # J-1534/I-0081 (fragment_carries_the_string.md sec2/sec3): live-mood valence=/felt= above
                # is the same convention 17 other origins already follow (was 0/425 populated for
                # origin='sound'). The block below is the SEPARATE coordinate-derived signal, gated by
                # SOUND_STRING_FIELDS (off = byte-identical to today). A follow-up UPDATE only -- never a
                # new store_fragment() kwarg/signature change (core/memory/store.py has 19 real CONTRACT
                # dependents per udms_get_change_dossier, re-confirmed this job, F-2091) -- and never an
                # INSERT (~11% of sound fragments have no fragment_context row yet; the UPDATE then
                # matches zero rows and no-ops, the same "an empty answer must be true, not silent"
                # discipline evidence_recall.py already states for itself).
                if SOUND_STRING_FIELDS and fragment_id:
                    from core.memory.store import _connect
                    c_json = json.dumps(coords(chosen) or {})
                    with _connect() as _conn:
                        _conn.execute(
                            "UPDATE fragment_context SET sound_key=?, sound_onset=?, sound_peak=?, "
                            "sound_tail=?, sound_felt_valence=?, sound_felt_arousal=? WHERE fragment_id=?",
                            (chosen, c_json, c_json, c_json, would_valence, would_arousal, fragment_id))
                        _conn.commit()
            except Exception:
                pass
        return line
    except Exception:
        return None


def propagate_historical_acoustic_event(
    event_id: str,
    origin_pos: list[float],
    sound_description: str,
    observer_pos: list[float] = [0.0, 0.0, 0.0],
    max_audible_dist: float = 60.0
) -> dict | None:
    """
    Phase 3 — Acoustic Causality & Sensory Uncertainty.
    Propagates a 3D acoustic event originating from an authoritative physical state transition.
    Calculates distance decay, 3D compass bearing, and audibility without revealing the underlying physical cause.
    """
    dx = origin_pos[0] - observer_pos[0]
    dy = origin_pos[1] - observer_pos[1]
    dz = origin_pos[2] - observer_pos[2]
    
    dist = round((dx**2 + dy**2 + dz**2) ** 0.5, 1)
    if dist > max_audible_dist:
        return None  # Sound decayed before reaching sensory boundary
        
    # Compute compass bearing
    import math
    rad = math.atan2(dx, dy)  # N=0, E=90
    deg = (math.degrees(rad) + 360) % 360
    
    directions = ["N", "N-NE", "NE", "E-NE", "E", "E-SE", "SE", "S-SE", "S", "S-SW", "SW", "W-SW", "W", "W-NW", "NW", "N-NW"]
    idx = int((deg + 11.25) / 22.5) % 16
    compass_str = directions[idx]
    
    percept_text = f"You hear a sudden, {sound_description} from the {compass_str} (approx {dist}m away). The source remains off-camera and unknown."
    
    return {
        "event_id": event_id,
        "origin_pos": origin_pos,
        "observer_pos": observer_pos,
        "dist_meters": dist,
        "bearing_deg": round(deg, 1),
        "compass": compass_str,
        "audible": True,
        "percept_text": percept_text
    }

