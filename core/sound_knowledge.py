"""
Nascence — Epistemic Audition: the sound-knowledge ledger (2026-08-15).

Founder's design (this session): hearing becomes a legitimate sense when identification is EARNED,
not narrated. A new sound arrives as FEATURES + DIRECTION, unnamed ("from somewhere in the hedge,
unseen, a long bright trill, falling away"). Identification happens by:
  1. SIGHT-BINDING — he chooses to look toward it while the source is visible and present (the
     infant's cross-modal binding; never auto-inferred — an act of attention he did not take is
     never fabricated for him).
  2. EXPOSURE — misses and part-glimpses accumulate hypothesis weight (the riroriro may take weeks
     of empty hedges; that is real — it is NZ's heard-not-seen bird).
  3. READING — a book (or his own study note) that ties the name to the sound teaches it — the
     sanctioned diegetic channel. Birders learn calls from books too.

Once learned, a sound is his for good: it renders NAMED forever after (the pools in soundscape.py).
Sounds he has demonstrably lived with for months are grandfathered — this system never gaslights
him about the fire or the gulls. Ledger: data/sound_knowledge.json (append-only events, auditable —
every association traces to a real encounter). Kill-switch: SOUND_EPISTEMICS=False renders
everything named exactly as before, ledger dormant. No LLM. Fail-open everywhere.
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.sound_knowledge")

_DATA = Path(__file__).parent.parent / "data"
_LEDGER_F = _DATA / "sound_knowledge.json"

SOUND_EPISTEMICS = True        # kill-switch — False = every sound named, exactly the old behaviour
_LEARN_AT = 1.0                # cumulative weight at which a sound becomes KNOWN
_RECENT_WINDOW_S = 900         # a look can bind to a sound heard within the last 15 min

# Sounds he has lived with, named, for months — grandfathered as already-known. Everything
# registered in soundscape._SOUNDS but absent from BOTH lists renders through the generic
# coordinate-renderer as unknown (future sounds enter epistemically by default).
GRANDFATHERED = {
    "waves_on_shingle", "waves_crashing", "gull_cries", "tui_song", "blackbird_song",
    "morepork_call", "cat_purr", "fire_crackle", "rain_on_roof", "wind_in_eaves", "thunder",
    "moth_tap", "shingle_drag", "oystercatcher_call", "bees_in_garden", "small_birds",
    "wind_in_trees", "wood_pigeon", "wren_scold", "branches_creak", "canopy_drip", "leaf_rustle",
    "embers_settle", "window_rattle", "tide_pool_trickle", "distant_surf_boom", "dawn_chorus",
    "clock_tick", "kettle_sing", "stream_run", "saw_rasp",      # 2026-08-22: things he handles and sees — known by sight
    # SOUND WORLD EXPANSION §3, THE GEOPHONY FILLS (2026-10-28, D-0500/J-2476): new GRADES and places of things he has
    # lived with for months -- the rain, the fire, the sea, the stream -- are not new identities; hail is unmistakable
    # the first time. Declared known here on purpose (the module's own rule: absent from both lists = enters unnamed).
    "hail_on_roof", "hail_on_leaves", "drizzle_hiss", "downpour_drum", "rain_down_chimney",
    "stream_over_stones", "undertow_rumble", "calm_sea_hush",
    # SOUND WORLD EXPANSION §4, THE SEASONAL BIOPHONY (2026-10-28, D-0500/J-2477): the kelp flies are the wrack-line's
    # own, seen every summer he has turned a strap (world_content_shore: "kelp flies rise in a cloud") -- known-ish,
    # trivial, declared known. silvereye_flock and paradise_duck_flyover arrive UNNAMED (AUDITION below).
    "kelp_fly_buzz",
    # SOUND WORLD EXPANSION §5, THE APPARATUS (2026-10-28, D-0500/J-2478): the dwelling's machinery, all lived-with --
    # the record player he has set going for months (its needle-drop and ending are his own lines), the letterbox
    # flag he has seen up and fetched from since 2026-06-21. The plan marks every §5 sound known; declared so here.
    "needle_crackle", "runout_hiss", "letterbox_flag_clank",
}

# The learnable voices: per-sound audition metadata. `unknown` lines are written FROM the sound's
# feature coordinates (a rendering of the sense-data, no name); `reveal` fires on a sight-binding;
# `miss` fires on an attentive look that finds nothing (and still earns exposure weight).
AUDITION: dict[str, dict] = {
    "penguin_bray": {
        "source": "the small penguin",
        "unknown": {"shore": "From under the cliff in the dark, a sound you don't know: a harsh braying, donkey-like, "
                             "small and close, answered by another further along."},
        "reveal": " — and there, crossing the shingle toward the rocks: a small upright bird, blue-grey, white-fronted, "
                  "hurrying on short legs. The braying is a penguin's — a small one, come ashore for the night.",
        "miss": " Whatever brays under the cliff stays in the dark; a scuffle on the stones, no more.",
        "bind_targets": ("cliff", "burrow", "burrows", "rocks", "shingle", "bird", "dark", "foot of the cliff"),
        "sight_prob": 0.6, "miss_weight": 0.2, "day_only": False,
        "book_names": ("little penguin", "blue penguin", "kororā", "korora", "fairy penguin"),
        "book_sounds": ("bray", "call", "burrow", "ashore"),
    },
    # THE BIRDS (Living World L2, J-0511, 2026-09-03): two migrant voices, hidden truth until seen and read.
    "cuckoo_call": {
        "source": "the shining cuckoo",
        "unknown": {"garden": "From the kōwhai, a sound you don't know: a long upward-slurred whistle, over and over, "
                              "then a few falling notes — a voice that was not here last month.",
                    "wood": "High in the green, a sound you don't know: a rising whistle repeated, then falling away, "
                            "from a bird you cannot find."},
        "reveal": " — and there, keeping to the leaves: a small bird, green above, barred white below. The rising "
                  "whistle is the shining cuckoo's — the spring's voice, back from the north.",
        "miss": " The whistle comes again from the leaves and nothing moves that you can name.",
        "bind_targets": ("kowhai", "kōwhai", "tree", "leaves", "hedge", "canopy", "bird", "voice", "whistle"),
        "sight_prob": 0.25, "miss_weight": 0.15, "day_only": True,
        "book_names": ("shining cuckoo", "pipiwharauroa", "pīpīwharauroa", "bronze cuckoo", "cuckoo"),
        "book_sounds": ("whistle", "call", "spring", "migrant", "warbler's nest", "song"),
    },
    "godwits_overhead": {
        "source": "the godwits",
        "unknown": {"shore": "High overhead, a sound you don't know: thin calling from many throats, moving fast along "
                             "the coast — a long wavering line of birds, too high to be anything but a line.",
                    "garden": "High over the garden, a sound you don't know: many thin voices passing south together, "
                              "fast, and gone behind the hill."},
        "reveal": " — and there against the sky: a long skein of long-billed birds, heading south along the coast. "
                  "Godwits, the kuaka — the travellers who come with the spring.",
        "miss": " The calling passed over and by the time you found the sky it was empty.",
        "bind_targets": ("sky", "overhead", "line", "birds", "coast", "south", "flock"),
        "sight_prob": 0.5, "miss_weight": 0.2, "day_only": False,
        "book_names": ("godwit", "godwits", "bar-tailed godwit", "kuaka"),
        "book_sounds": ("migration", "alaska", "spring", "estuary", "flight", "skein", "arrive", "september"),
    },
    "fantail_chatter": {
        "source": "the fantail",
        "unknown": {"wood": "Close about you, moving with you, a sound you don't know: a thin dry chatter, "
                            "quick and bright, snapping off and starting again.",
                    "garden": "Close by among the beds, moving, a sound you don't know: a thin insistent "
                              "chatter, almost at your shoulder, never in the same place twice."},
        "reveal": " — and there it is: a small bird with its tail spread like a fan, looping almost at "
                  "your shoulder, snapping at the air. The chatter is the fantail's.",
        "miss": " Whatever makes the quick chatter has moved again — a flicker at the edge of sight, no more.",
        "bind_targets": ("bird", "fantail", "air", "around", "about", "path", "undergrowth", "bushes",
                         "hedge", "trees", "garden", "bed", "beds"),
        "sight_prob": 0.85, "miss_weight": 0.15, "day_only": True,
        "book_names": ("fantail", "piwakawaka", "pīwakawaka"),
        "book_sounds": ("chatter", "cheep", "call", "song", "voice"),
    },
    # J-0515 (F-0697, 2026-09-03): bellbird_song was rated in soundscape._EVENT_RATES since J-0511 but
    # had no AUDITION entry and no _SOUNDS point — dead. life_birds.py's bellbird row is HIDDEN TRUTH
    # (species reveal via sight + book, ease=0.35), so this follows the same shape as riroriro/fantail:
    # unnamed feature-first text until sight-bound or read. reveal/miss text matches the row's own
    # hidden.reveal/hidden.miss lines so the sound and sight paths tell the same story.
    "bellbird_song": {
        "source": "the bellbird",
        "unknown": {"garden": "From somewhere in the kōwhai, a sound you don't know: a clear, pure "
                              "bell-note, ringing once, then again a little further off.",
                    "wood": "High in the canopy, a sound you don't know: a clear ringing chime, "
                            "unhurried, answered by another somewhere further along."},
        "reveal": " — a small olive-green bird, quick and shy, works the flowers with a curved bill "
                  "and is gone before you have it properly. A bellbird, the korimako; the chiming "
                  "you hear at first light is this bird's.",
        "miss": " Something small and green moved in the flowers and did not wait to be looked at. "
                "The chiming carries on regardless.",
        "bind_targets": ("bird", "kowhai", "kōwhai", "tree", "flowers", "canopy", "hedge", "green"),
        "sight_prob": 0.35, "miss_weight": 0.15, "day_only": True,
        "book_names": ("bellbird", "korimako", "makomako"),
        "book_sounds": ("bell", "chime", "notes", "nectar", "song", "honeyeater"),
    },
    "riroriro_trill": {
        "source": "the grey warbler",
        "unknown": {"wood": "From somewhere high in the green, unseen, a sound you don't know: a long "
                            "wavering trill, bright and thin, falling away as if unfinished.",
                    "garden": "From somewhere in the hedge, unseen, a sound you don't know: a long "
                              "wavering trill that falls and falls and never quite lands."},
        "reveal": " — and for once you see it: a tiny grey scrap of a bird, hardly anything at all, "
                  "throwing that long falling trill. The grey warbler — the riroriro.",
        "miss": " You look, and the hedge is empty. The trill goes on somewhere inside the green, unbothered.",
        "bind_targets": ("bird", "hedge", "bushes", "trees", "canopy", "leaves", "green", "warbler", "riroriro"),
        "sight_prob": 0.03, "miss_weight": 0.10, "day_only": True,
        "book_names": ("riroriro", "grey warbler", "gray warbler"),
        "book_sounds": ("trill", "song", "call", "voice"),
    },
    "kereru_wingbeats": {
        "source": "the wood pigeon",
        "unknown": {"wood": "From overhead, a sound you don't know: a heavy rhythmic whoosh — whoosh, "
                            "each stroke its own soft concussion, fading away downhill."},
        "reveal": " — and you catch it: the big wood pigeon itself, heaving away between the canopies. "
                  "That heavy wing-music is his.",
        "miss": " Only the swaying branch is left of it, and the whoosh fading somewhere beyond the trunks.",
        "bind_targets": ("bird", "pigeon", "canopy", "trees", "branches", "treetops", "sky", "kereru"),
        "sight_prob": 0.70, "miss_weight": 0.15, "day_only": True,
        "book_names": ("kereru", "kererū", "wood pigeon"),
        "book_sounds": ("wingbeat", "wing-beat", "whoosh", "wing"),
    },
    "kingfisher_call": {
        "source": "the kingfisher",
        "unknown": {"shore": "From a high perch somewhere on the cliff, a sound you don't know: a dry "
                             "staccato rattle — kek-kek-kek — clipped off short.",
                    "garden": "From a post or a wire somewhere, a sound you don't know: a dry staccato "
                              "rattle, sharp and even, finished as soon as begun."},
        "reveal": " — and there, on its perch: a compact blue-green bird with a heavy dagger of a bill. "
                  "The dry rattle is the kingfisher's.",
        "miss": " The perch you find is bare; the rattle does not come again while you watch.",
        "bind_targets": ("bird", "post", "fence", "cliff", "wire", "perch", "kingfisher", "sky"),
        "sight_prob": 0.55, "miss_weight": 0.15, "day_only": True,
        "book_names": ("kingfisher", "kotare", "kōtare"),
        "book_sounds": ("kek", "rattle", "call", "staccato"),
    },
    "shag_wingbeats": {
        "source": "the shag",
        "unknown": {"shore": "Low over the water, a sound you don't know: slow heavy wingbeats, deliberate "
                             "as oars, passing along the line of the swell."},
        "reveal": " — and you follow the sound to it: a dark long-necked bird beating low over the water, "
                  "almost touching its own reflection. A shag, going about its patrol.",
        "miss": " The water shows only swell; whatever passed has rounded the headland.",
        "bind_targets": ("sea", "water", "swell", "waves", "bird", "shag", "headland", "sky"),
        "sight_prob": 0.60, "miss_weight": 0.15, "day_only": True,
        "book_names": ("shag", "cormorant", "kawau", "kawaupaka"),
        "book_sounds": ("wingbeat", "wing-beat", "flight", "wing"),
    },
    "robin_song": {
        "source": "the robin",
        "unknown": {"wood": "From a low branch close by, a sound you don't know: clear even little "
                            "phrases, patiently repeated, from something entirely unafraid of you."},
        "reveal": " — and it is right there, an arm's length off: a small dark bird, long-legged, "
                  "watching you as it sings. The bold one is a robin.",
        "miss": " The low branches hold still and empty, though the small song goes on close by.",
        "bind_targets": ("bird", "branch", "undergrowth", "ground", "trees", "robin", "low"),
        "sight_prob": 0.75, "miss_weight": 0.15, "day_only": True,
        "book_names": ("robin", "toutouwai"),
        "book_sounds": ("song", "phrase", "call", "voice"),
    },
    "cicada_chorus": {
        "source": "the cicadas",
        "unknown": {"wood": "From every tree at once, a sound you don't know: a dry shimmering pulse, "
                            "rising with the heat, made by nothing you can find.",
                    "garden": "From all the trees together, a sound you don't know: a sawing, shimmering "
                              "wall of sound that swells with the warmth and belongs to no one bird."},
        "reveal": "",              # never sight-bound — no individual source is ever seen
        "miss": " Every trunk you check is bare bark; the sawing goes on all around, exactly as before.",
        "bind_targets": ("trees", "tree", "trunk", "canopy", "leaves", "branches", "cicada"),
        "sight_prob": 0.0, "miss_weight": 0.08, "day_only": True,
        "book_names": ("cicada", "cicadas", "kihikihi"),
        "book_sounds": ("song", "chorus", "drone", "buzz", "shimmer", "saw"),
    },
    "cricket_night": {
        "source": "the crickets",
        "unknown": {"garden": "From the grass, everywhere and nowhere, a sound you don't know: a slow "
                              "patient ticking pulse, one voice answering another across the dark."},
        "reveal": "",
        "miss": " The dark grass gives nothing up; the ticking pauses near you and carries on further off.",
        "bind_targets": ("grass", "ground", "garden", "dark", "beds", "cricket"),
        "sight_prob": 0.0, "miss_weight": 0.08, "day_only": False,
        "book_names": ("cricket", "crickets"),
        "book_sounds": ("chirp", "song", "tick", "pulse"),
    },
    # ── SOUND WORLD EXPANSION §2, THE NIGHT MYSTERIES (2026-10-28, D-0500/J-2475): five voices that arrive
    # UNNAMED. `unknown` values here are TUPLES (a rotating pool per place, picked anti-repeat by hear() -- never
    # one fixed string); a plain string is still accepted everywhere, so every older entry is untouched. Each
    # unnamed line is features + direction + a near/far word and never names the cause (D-0500's own defeater).
    "possum_rasp": {
        "source": "the possum",
        "unknown": {"garden": ("From up in the tree, close, a sound you don't know: a harsh coughing rasp, dry and scraping, "
                               "repeated out of the dark, and the branch-end shaking with it.",
                               "Overhead in the branches, near, a sound you don't know: a hoarse scraping cough, more throat than "
                               "voice, that stops, and starts again.",
                               "From the dark of the tree, close above you, a sound you don't know: a grating, coughing growl, "
                               "ugly and unhurried, that does not care that you are here.",
                               "Up in the tree, close, a sound you don't know: a rasping bark — scrape, cough, hiss — from "
                               "something heavy enough to shake the limb it sits on."),
                    "wood": ("From the oak, close, a sound you don't know: a harsh coughing rasp out of the dark canopy, "
                             "repeated, dry as a saw.",
                             "Somewhere up in the black branches, near, a sound you don't know: a hoarse scraping growl, "
                             "stopping and starting, from a weight that makes the limb creak.",
                             "Overhead in the oak, a sound you don't know: a grating cough-and-hiss, slow, from something "
                             "that is not a bird.",
                             "From the dark above you, close, a sound you don't know: a rasping, scraping bark that goes on "
                             "longer than any throat you know.")},
        "reveal": " — and the eyes find it: two red-orange points of light up in the branches, wide apart, and under them a "
                  "heavy grey shape along the limb. The rasp is the possum's — that coughing bark is its voice.",
        "miss": " The branch shook and went still; whatever rasps up there is a darker patch of the dark.",
        "bind_targets": ("tree", "branch", "branches", "limb", "oak", "canopy", "wall", "dark", "eyes", "possum"),
        "sight_prob": 0.35, "miss_weight": 0.15, "day_only": False,
        "book_names": ("possum", "possums", "brushtail", "opossum", "paihamu"),
        "book_sounds": ("rasp", "cough", "hiss", "screech", "growl", "call", "night", "bark"),
    },
    "wall_scratch": {
        "source": "the mice",
        "unknown": {"study": ("In the wall by the skirting, close, a sound you don't know: a tiny dry scratching, a few "
                              "strokes and a pause, from inside the boards themselves.",
                              "From somewhere inside the wall, near the desk, a sound you don't know: a thin busy ticking, "
                              "small as a fingernail, and then nothing.",
                              "Behind the skirting, close enough to touch, a sound you don't know: a faint scrabbling in the "
                              "wall cavity that stops the moment you listen for it.",
                              "In the wall, close, intimate and unplaceable, a sound you don't know: a small dry scratching "
                              "at timber, on and off, from a place you cannot see into.")},
        "reveal": "",              # never sight-bound: a wall cannot be looked into, and no trap is authored
        "miss": " The wall gives nothing up — boards, skirting, the shadow of the desk — and the scratching does not come again while you watch.",
        "bind_targets": ("wall", "skirting", "boards", "floor", "corner", "cupboard", "woodpile", "desk", "wainscot", "mouse", "mice"),
        "sight_prob": 0.0, "miss_weight": 0.05, "day_only": False,
        "book_names": ("mouse", "mice", "house mouse", "kiore"),
        "book_sounds": ("scratch", "scratching", "gnaw", "gnawing", "wall", "skirting", "wainscot", "cavity"),
    },
    "distant_yowl": {
        "source": "the distant cat",
        # KNOWN KIND, UNKNOWN INDIVIDUAL: he knows what a cat's yowl is -- the lines say so -- and cannot say WHOSE.
        # The name that is earned here is the individual's: the black cat, seen with its mouth open on the sound.
        "unknown": {"garden": ("Far down the garden, from the bottom wall, a cat's yowl — long, rising, wavering — and you "
                               "cannot tell whose.",
                               "A yowl from the ridge, a long way off: a cat's, drawn out and repeated, and no way to say "
                               "which cat.",
                               "From away down the fence line, far, a cat gives the night its long complaining cry — a "
                               "voice you know the kind of and not the owner.",
                               "Out of the dark at the bottom of the garden, distant, a cat's rising yowl, over and over; "
                               "whose, you cannot tell from here."),
                    "wood": ("From somewhere beyond the trees, far off, a cat's yowl — long, rising, wavering — and no "
                             "telling whose.",
                             "Downhill through the trunks, distant, a cat is yowling into the dark; which cat, the wood "
                             "does not say.",
                             "Far off beyond the wood a cat's cry rises and falls, repeated, a voice you know the kind "
                             "of and not the owner.",
                             "A yowl, distant, from the direction of the garden: a cat's, drawn out; whose, you cannot "
                             "tell from here."),
                    "study": ("Through the window, far off down the garden, a cat's yowl — long, rising, wavering — and "
                              "you cannot tell whose.",
                              "From outside, a long way down toward the bottom wall, a cat is yowling into the dark; "
                              "which cat, the window does not say.",
                              "Faint through the glass, distant, a cat's drawn-out cry, repeated — a voice you know the "
                              "kind of and not the owner.",
                              "Somewhere out in the dark beyond the window, far, a cat's rising yowl, over and over; "
                              "whose, you cannot tell from here.")},
        "reveal": " — and far down on the wall, a shape you know the kind of and now the one: a black cat, mouth open on "
                  "that long note. The yowl is the other cat's, the black one's — not hers.",
        "miss": " The bottom wall and the ridge are only dark; the yowl comes again from out there and nothing shows.",
        "bind_targets": ("cat", "wall", "ridge", "fence", "bottom", "garden", "dark", "harakeke", "window", "black cat"),
        "sight_prob": 0.15, "miss_weight": 0.10, "day_only": False,
        "book_names": ("tom", "tomcat", "stray cat", "feral cat", "black cat"),
        "book_sounds": ("yowl", "caterwaul", "howl", "cry", "night"),
    },
    "hedgehog_snuffle": {
        "source": "the hedgehog",
        "unknown": {"garden": ("Close by along the bed edge, a sound you don't know: a busy wet snuffling and snorting "
                               "through the leaves, right at your feet almost, that stops when you move.",
                               "From under the hedge, near, a sound you don't know: a grunting, nosing, unhurried "
                               "searching along the beds — something small breathing hard through leaves.",
                               "At the lawn edge, close, a sound you don't know: snuffle, snort, a rustle, snuffle again, "
                               "low to the ground and going somewhere.",
                               "Near the compost, a sound you don't know: a steady determined snuffling, wet and small, "
                               "from something working the ground at its own speed.")},
        "reveal": " — and there it is in the dark: a low hunched shape working along the hedge bottom at its own speed, "
                  "nosing at something in the grass. The snuffling is the hedgehog's.",
        "miss": " A rustle low in the hedge bottom, the snuffling pauses, and nothing you can put a shape to.",
        "bind_targets": ("hedge", "bed", "beds", "grass", "lawn", "edge", "compost", "ground", "dark", "leaves", "hedgehog"),
        "sight_prob": 0.30, "miss_weight": 0.15, "day_only": False,
        "book_names": ("hedgehog", "hedgehogs"),
        "book_sounds": ("snuffle", "snuffling", "snort", "grunt", "rustle", "night", "slugs"),
    },
    "dolphin_blow": {
        "source": "the dolphins",
        "unknown": {"shore": ("Out past the surf line, far, a sound you don't know: one wet gust of breath on the water, "
                              "clear, and gone.",
                              "From the water beyond the breakers, a long way out, a sound you don't know: a single sharp "
                              "sigh of breath, then only the sea.",
                              "Somewhere out on the bay, far off, a sound you don't know: a sudden blow of breath across "
                              "the water, once, and after a long while once more.",
                              "Out beyond the swell, distant, a sound you don't know: something breathes out on the "
                              "water — a wet, carrying gust — and is not heard again.")},
        "reveal": " — and you are looking at the right patch of water: a fin rolls, and another, and a dark back. "
                  "The breath on the water is the dolphins' — a small pod working along the bay.",
        "miss": " The water out past the surf is empty again; whatever breathed there has gone under.",
        "bind_targets": ("water", "sea", "surf", "bay", "swell", "horizon", "fin", "waves", "dolphin", "dolphins"),
        "sight_prob": 0.25, "miss_weight": 0.15, "day_only": True,
        "book_names": ("dolphin", "dolphins", "porpoise", "aihe", "hector's dolphin"),
        "book_sounds": ("blow", "breath", "blowhole", "surface", "pod", "fin", "breathe"),
    },
    # ── SOUND WORLD EXPANSION §3, THE GEOPHONY FILLS (2026-10-28, D-0500/J-2476): the two §3 sounds that arrive
    # UNNAMED. Rotating per-place pools (the J-2475 tuple shape); each unnamed line is features + direction + a near/far
    # word and never names the cause -- no roof, iron, sun or heat for the tick; no frost, ice or freeze for the crack.
    "tin_roof_tick": {
        "source": "the roof",
        # THE NZ COTTAGE SOUND, a slow mystery: the corrugated iron easing as the sun warms it and lets it go. Sightable
        # only by looking UP at the right moment (low odds); the honest road is a book, or his own inference.
        "unknown": {"study": ("From directly overhead, close, a sound you don't know: a single sharp tick, like a fingernail on "
                              "metal, and then a long nothing, and then another.",
                              "Above you, near, a sound you don't know: a small hard tick out of the ceiling itself, irregular, "
                              "with no one up there to make it.",
                              "From the ceiling, close over your head, a sound you don't know: a dry metallic click, once, that "
                              "waits a while and comes again somewhere else along the room.",
                              "Overhead, near, a sound you don't know: a thin sharp tick, as if the house itself had shifted "
                              "the smallest possible amount, and then stillness."),
                    "garden": ("From the lean-to beside you, close, a sound you don't know: a single sharp metallic tick, and "
                               "after a while another, from nothing you can see move.",
                               "Over by the house, near, a sound you don't know: a dry hard click, irregular, as if something "
                               "unseen were being flicked against the wall.",
                               "From above the lean-to, close, a sound you don't know: a thin tick, a long pause, a tick — "
                               "no bird, no wind, nothing moving there.",
                               "Beside you at the house wall, near, a sound you don't know: a small sharp clicking that comes "
                               "and goes with no rhythm and no visible cause.")},
        "reveal": " — and looking up, you have it: the sun lies full on the iron of the roof, and the sheets are easing as they "
                  "warm, one tick at a time. The sound is the roof's own — the corrugated iron taking the day's heat.",
        "miss": " The ceiling is only boards and shadow; the tick does not come again while you look, and gives nothing away.",
        "bind_targets": ("ceiling", "roof", "rafters", "beam", "beams", "overhead", "iron", "lean-to", "house", "wall"),
        "sight_prob": 0.20, "miss_weight": 0.08, "day_only": True,
        "book_names": ("corrugated iron", "tin roof", "iron roof", "roofing iron", "corrugated", "the roof"),
        "book_sounds": ("tick", "ticking", "creak", "crack", "expand", "contract", "heat", "cool", "warm", "sun"),
    },
    "frost_crack": {
        "source": "the frost",
        # A BANG IN THE NIGHT: never sight-bound (nothing to see -- a report from timber or ground, and done); a look still
        # earns a little exposure weight, and a book or his own study note that ties frost to cracking timber names it.
        "unknown": {"study": ("From the wall beside you, close, a sound you don't know: a single sharp crack, like a stick "
                              "snapped, and then the room as still as before.",
                              "Out of the stillness, near, a sound you don't know: one hard report from somewhere in the "
                              "timber of the house — once — and nothing after it.",
                              "From the boards overhead, close, a sound you don't know: a sudden crack, sharp as a shot in "
                              "the quiet, that does not repeat.",
                              "Somewhere in the wall by the window, near, a sound you don't know: a short sharp splitting "
                              "crack, and the silence closing over it."),
                    "garden": ("From the dark by the fence, a little way off, a sound you don't know: a single sharp crack, "
                               "like a stick snapped, and nothing moves.",
                               "Out of the still night, near, a sound you don't know: one hard report from the ground or the "
                               "posts — once — and the quiet again.",
                               "From the direction of the house, close, a sound you don't know: a sudden crack, sharp and "
                               "short, as if the timber had been struck.",
                               "Somewhere along the bottom wall, far, a sound you don't know: a short splitting crack in the "
                               "dark, and then the stillness."),
                    "wood": ("From a trunk close by, a sound you don't know: a single sharp crack in the dark, like a branch "
                             "snapped, and no branch falls.",
                             "Out of the still black of the wood, near, a sound you don't know: one hard report from the "
                             "timber — once — and the silence after it.",
                             "Deeper in among the trees, a little way off, a sound you don't know: a sudden short crack, sharp "
                             "as a shot, and nothing stirs.",
                             "From the ground at your feet, close, a sound you don't know: a small hard splitting crack, and "
                             "then the night as still as before.")},
        "reveal": "",              # never sight-bound: a report from timber or ground, over before it can be looked at
        "miss": " The dark gives nothing up — wall, fence, trunks — and the crack does not come again while you look.",
        "bind_targets": ("wall", "boards", "timber", "beam", "rafters", "fence", "post", "posts", "ground", "trees", "tree",
                         "trunk", "dark", "outside", "window", "garden", "house"),
        "sight_prob": 0.0, "miss_weight": 0.12, "day_only": False,
        "book_names": ("frost", "hard frost", "freezing night", "freeze", "frozen"),
        "book_sounds": ("crack", "cracks", "cracking", "report", "bang", "split", "contract", "timber", "snap"),
    },
    # ── SOUND WORLD EXPANSION §4, THE SEASONAL BIOPHONY (2026-10-28, D-0500/J-2477): the two §4 sounds that arrive
    # UNNAMED. Rotating per-place pools (the J-2475 tuple shape); each unnamed line is features + direction + a near/far
    # word and never names the cause -- no tauhou / silvereye / waxeye / eye-ring for the flock; no duck / goose /
    # paradise for the flyover. The flock is EASILY sighted (they swarm visibly: sight_prob high); the flyover is caught
    # only by a look UP while the pair is still in the sky -- `bind_window_s` (new, optional, honoured by look_binding;
    # every older entry keeps the module's 15 min) makes that catch a short one, the godwits_overhead pattern made short.
    "silvereye_flock": {
        "source": "the tauhou",
        "unknown": {"garden": ("Close by in the hedge, a sound you don't know: soft thin cheeps from many small throats at once, "
                               "passed along the hedge end to end as something moves through it.",
                               "From the tree and then the hedge beside you, near, a sound you don't know: a busy quiet chorus "
                               "of contact calls, dozens of small voices keeping together as they go.",
                               "Along the hedge, close, a sound you don't know: a constant soft cheeping travelling the length "
                               "of it, bird to bird, a loose crowd of small things working the leaves.",
                               "A few steps off in the hedge, a sound you don't know: a thin sweet twittering from a whole "
                               "company of small voices, going end to end and away down the fence line.")},
        "reveal": " — and there they are, all through the hedge: a loose flock of small grey-green birds with white eye-rings, "
                  "working it end to end and leaving the way they came. The soft cheeping is the tauhou's — the silvereyes, "
                  "in their winter flock.",
        "miss": " The hedge stirs along its whole length and whatever moves through it keeps inside the leaves; the cheeping goes on.",
        "bind_targets": ("hedge", "tree", "bush", "bushes", "leaves", "fence", "fence line", "birds", "bird", "flock", "small birds",
                         "garden", "kowhai", "kōwhai", "tauhou", "silvereye"),
        "sight_prob": 0.80, "miss_weight": 0.15, "day_only": True,
        "book_names": ("tauhou", "silvereye", "silvereyes", "waxeye", "waxeyes", "wax-eye", "white-eye"),
        "book_sounds": ("cheep", "cheeps", "cheeping", "chatter", "call", "calls", "flock", "flocks", "twitter", "contact"),
        "bind_window_s": 900,
    },
    "paradise_duck_flyover": {
        "source": "the paradise ducks",
        "unknown": {"garden": ("High overhead, a sound you don't know: a thin high zeek-zeek and a hoarse low honk answering it, "
                               "two voices going over fast together, and away along the coast.",
                               "From far up against the sky, a sound you don't know: a shrill thin calling and a deeper honking "
                               "answer, passing over high and already going away over the ridge.",
                               "High above the garden, a sound you don't know: two voices crossing the sky together — one thin "
                               "and piping, one low and hoarse — fast, and fading out beyond the hill.",
                               "Overhead and far up, a sound you don't know: a high thin zeek, a low honk, zeek, honk, a pair of "
                               "something going over on stiff wings and gone down the coast."),
                    "shore": ("High over the bay, a sound you don't know: a thin high zeek-zeek and a hoarse low honk answering, "
                              "two voices passing fast along the coast, far up, and away.",
                              "From far up over the water, a sound you don't know: a shrill piping call and a deep honking answer, "
                              "crossing high above the surf and going on down the coast.",
                              "Overhead, high and far, a sound you don't know: two voices going over together — one thin, one "
                              "hoarse — fast on the wind, and fading past the headland.",
                              "Far above the beach, a sound you don't know: a high thin zeek, a low honk, zeek, honk, a pair of "
                              "something crossing the sky on stiff wings and gone behind the cliff.")},
        "reveal": " — and you find them against the sky: a pair, big as small geese, one white-headed and one dark, going over high "
                  "and fast on stiff wings, her thin call and his low honk answering. Paradise ducks — pūtangitangi — a pair "
                  "passing through, bound for somewhere else.",
        "miss": " The calling went on over and by the time you had the sky the pair was a speck down the coast, or nothing at all.",
        "bind_targets": ("sky", "overhead", "above", "clouds", "cloud", "birds", "bird", "pair", "coast", "ridge", "headland",
                         "hill", "wings", "duck", "ducks"),
        "sight_prob": 0.55, "miss_weight": 0.15, "day_only": True,
        "book_names": ("paradise duck", "paradise ducks", "paradise shelduck", "putangitangi", "pūtangitangi", "shelduck"),
        "book_sounds": ("honk", "honking", "zeek", "call", "calls", "pair", "flight", "overhead", "fly over", "flyover", "wings"),
        "bind_window_s": 300,          # a look UP has to come while the pair is still in the sky: about the length of a pass
    },
}

_last_unknown_idx: dict[str, int] = {}     # J-2475: per (key, place) anti-repeat cursor for the unnamed pools


def _unknown_line(spec: dict, key: str, location: str) -> str:
    """The unnamed rendering for this place: a plain string as always, or (J-2475) one line of a rotating pool,
    never the same line twice running for a given key+place. Falls back to the entry's first place."""
    pool = spec["unknown"].get(location)
    if pool is None:
        pool = next(iter(spec["unknown"].values()))
    if isinstance(pool, str):
        return pool
    pool = list(pool)
    idx = random.randrange(len(pool))
    cursor = f"{key}@{location}"
    if len(pool) > 1 and idx == _last_unknown_idx.get(cursor, -1):
        idx = (idx + 1) % len(pool)
    _last_unknown_idx[cursor] = idx
    return pool[idx]


# ── Ledger ────────────────────────────────────────────────────────────────────────────────────────

def _load() -> dict:
    try:
        from core import store_persist as _sp   # J-4442 (F-5157): loud on damage, falls back to .prev
        return _sp.read_json_durable(_LEDGER_F, "sound_knowledge", logger, guard=profile.guard_path)
    except Exception:
        return {"sounds": {}, "recent": []}


def _save(d: dict) -> None:
    path = profile.guard_path(_LEDGER_F)   # J-0784: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp   # J-4442 (F-5157): was tmp+replace without fsync; now fsync + .prev
        _sp.write_text_durable(path, json.dumps(d, indent=1, ensure_ascii=False))
    except Exception as exc:
        logger.debug("[sound-knowledge] _save failed (non-fatal): %s", exc)


def _weight(led: dict, key: str) -> float:
    return float(led.get("sounds", {}).get(key, {}).get("weight", 0.0))


def is_learned(key: str) -> bool:
    if not SOUND_EPISTEMICS or key in GRANDFATHERED or key not in AUDITION:
        return True                     # unknown-to-this-module keys fail open to named (safe default)
    return _weight(_load(), key) >= _LEARN_AT


def _add_event(led: dict, key: str, via: str, weight: float, note: str = "") -> bool:
    """Append an identification event; returns True if the sound just became LEARNED."""
    s = led.setdefault("sounds", {}).setdefault(key, {"weight": 0.0, "events": []})
    was = s["weight"] >= _LEARN_AT
    s["weight"] = round(min(1.5, s["weight"] + weight), 3)
    s["events"].append({"ts": round(time.time(), 1), "via": via, "weight": weight, "note": note[:120]})
    now_learned = s["weight"] >= _LEARN_AT
    if now_learned and not was:
        logger.info("[sound_knowledge] LEARNED %s → %s (via %s)", key, AUDITION[key]["source"], via)
    return now_learned and not was


# ── The hearing path (called by soundscape's ambience when a learnable voice is picked) ──────────

_DAYS_KEPT = 14               # per-day counts held this long ("I heard them 400 times today")


def note_exposures(key: str, location: str, n: int = 0, bed_hours: float = 0.0) -> None:
    """THE HEARING LEDGER (2026-08-16, founder: 'sounds should be a factory' + the tree-falls
    law). Fed by the world's own acoustic clock (soundscape.world_tick): every occurrence of a
    keyed voice WHERE HE IS counts — as an aggregate, never as stored repetitions ('we can know
    what the sound is and say I heard them 400 times or so today'). Two classes of good:
      EVENTS (n)        — discrete voices: a gull's cry, a trill, a thunder clap. Counted.
      BEDS (bed_hours)  — continuous presences: waves, wind, rain. Lived-in hours, not counts.
    Unheard sound is GONE FOREVER — nothing anywhere records what sounded where he wasn't;
    sampling only his place is therefore EXACT, not a shortcut. All of this was rendered to his
    world in his presence — his history, nothing hidden."""
    if n <= 0 and bed_hours <= 0:
        return
    try:
        led = _load()
        h = led.setdefault("hearings", {}).setdefault(key, {})
        now = time.time()
        h.setdefault("first_ts", now)
        h["last_ts"] = now
        pl = h.setdefault("places", {})
        if n > 0:
            h["count"] = int(h.get("count", 0)) + n
            day = time.strftime("%Y-%m-%d", time.localtime(now))
            days = h.setdefault("days", {})
            days[day] = int(days.get(day, 0)) + n
            if len(days) > _DAYS_KEPT:
                for k in sorted(days)[:-_DAYS_KEPT]:
                    days.pop(k, None)
            pl[location] = int(pl.get(location, 0)) + n
            # Transport Manager (2026-08-29, D-0064): EVENTS only, per-place line granularity —
            # BEDS (bed_hours branch below) are deliberately excluded, same reasoning
            # couriers.sound_echo already applies to beds: a near-continuous presence has no
            # spike/drought shape worth judging against its own baseline. Shadow-only so far —
            # nothing yet calls transport_manager.dispatch_tick() (see that module's docstring).
            try:
                from core import transport_manager as _tm
                _tm.observe(f"sound:{key}:{location or 'here'}", now, float(n))
            except Exception:
                pass
        if bed_hours > 0:
            # 6-decimal precision: 5s ticks are 0.00139h — rounding at 3dp bled ~28% (test-caught)
            h["bed_hours"] = round(float(h.get("bed_hours", 0.0)) + bed_hours, 6)
            pl[location] = round(float(pl.get(location, 0)) + bed_hours, 6)
        _save(led)
    except profile.NonLiveWriteError:
        # J-0784: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
        # rather than this pre-existing broad except swallowing it.
        raise
    except Exception:
        pass


def hearing_history_line(key: str) -> str:
    """His own history with a voice — served at the moment of binding ('all those times…') and
    available to P4 later. Empty until he has genuinely heard it more than once."""
    try:
        h = (_load().get("hearings", {}) or {}).get(key) or {}
        n = int(h.get("count", 0))
        if n < 2:
            return ""
        days = max(1, int((time.time() - float(h.get("first_ts", time.time()))) / 86400))
        places = sorted((h.get("places") or {}).items(), key=lambda kv: -kv[1])
        _at = {"shore": "at the shore", "garden": "in the garden",
               "wood": "in the wood", "study": "from the study"}
        where = f", most of them {_at.get(places[0][0], 'in the ' + places[0][0])}" if places else ""
        since = ("this last day" if days < 2 else
                 f"these {days} days" if days < 60 else f"these {days // 30} months")
        return (f" And with the name, the count comes home: you have heard this voice "
                f"{n} times {since}{where} — all those hearings, yours already.")
    except Exception:
        return ""


def hear(key: str, named_line: str, location: str) -> str:
    """Render one heard voice: NAMED if learned/grandfathered/flag-off; otherwise the unnamed
    feature-rendering for this place — and the hearing is noted so a look within 15 min can bind.
    (Counting lives in note_exposures, fed by the world's own clock — a render is attention,
    not an extra occurrence; no double counting.)"""
    try:
        if is_learned(key):
            return named_line
        spec = AUDITION[key]
        led = _load()
        led.setdefault("recent", []).append({"key": key, "ts": round(time.time(), 1), "loc": location})
        led["recent"] = [r for r in led["recent"] if time.time() - r["ts"] < _RECENT_WINDOW_S][-12:]
        _save(led)
        return _unknown_line(spec, key, location)      # J-2475: a string, or one line of a rotating pool
    except profile.NonLiveWriteError:
        # J-0784: same -- do not let this fail-open net swallow D-0179's hard-raise.
        raise
    except Exception:
        return named_line               # fail-open: he hears the named line rather than nothing


# ── Sight-binding (called from sensorium.look, fail-open) ─────────────────────────────────────────

def _binds_target(t: str, targets) -> bool:
    """D-0760 (F-4496/J-3893): whole-word matching, as J-3891 did for book binding. The old raw substring test let
    'fin' (triplefin) reveal dolphin_blow and 'tree' (the bird in the tree) reveal the possum."""
    for b in targets:
        if re.search(r"(?<![a-z0-9])" + re.escape(b) + r"(?![a-z0-9])", t):
            return True
    return False


def look_binding(target: str, location: str, is_day: bool) -> str:
    """He chose to look. If an unlearned sound was heard here recently and this look plausibly seeks
    its source: roll visibility. A sighting NAMES it (the reveal) and it is learned; a miss earns
    exposure weight (the slow inference path) and returns the honest miss line. Returns text to
    append to the look result, or ''."""
    try:
        if not SOUND_EPISTEMICS:
            return ""
        t = (target or "").lower()
        led = _load()
        now = time.time()
        for r in reversed(led.get("recent", [])):
            key = r.get("key")
            spec = AUDITION.get(key)
            if not spec or r.get("loc") != location:
                continue
            # J-2477 (sound_world_expansion §4, D-0500): an entry may carry its own, SHORTER bind window (`bind_window_s`)
            # -- a flyover can only be caught while the pair is still in the sky. Every entry without one keeps the
            # module's 15 min exactly as before.
            try:
                window = float(spec.get("bind_window_s") or _RECENT_WINDOW_S)
            except (TypeError, ValueError):
                window = float(_RECENT_WINDOW_S)
            if now - r.get("ts", 0) > min(window, float(_RECENT_WINDOW_S)):
                continue
            if _weight(led, key) >= _LEARN_AT:
                continue
            if not _binds_target(t, spec["bind_targets"]):
                continue
            if spec.get("day_only") and not is_day:
                continue
            if random.random() < spec["sight_prob"]:
                _add_event(led, key, "sighted", 1.0, f"look at '{t[:40]}' at {location}")
                _save(led)
                # THE RETROACTIVE-BINDING MOMENT (2026-08-16): the name arrives, and his whole
                # history with the voice comes home with it — his own hearings, from the ledger.
                return spec["reveal"] + hearing_history_line(key)
            _add_event(led, key, "exposure", spec["miss_weight"], f"looked, unseen ('{t[:40]}')")
            _save(led)
            return spec["miss"]
        return ""
    except profile.NonLiveWriteError:
        # J-0784: same -- sensorium.look()'s own OUTER wrapper already re-raises (J-0751), but this
        # function's own local except would otherwise swallow it one layer before that.
        raise
    except Exception:
        return ""


# ── Book-binding (called from study_note after a note is written, fail-open) ─────────────────────

_TIE_WINDOW = 160   # J-3891/F-4494: a name and a sound-word must sit this many chars apart at most


def _ties_name_to_sound(low: str, names, sounds) -> bool:
    """J-3891 (F-4494): whole-word matches only, and a name and a sound-word within _TIE_WINDOW chars of each other.
    The old bare-substring test named distant_yowl from 'bottom'+'night', wall_scratch from 'mice'+'swallows'
    ('wall' inside 'swallows'), frost_crack from 'freeze'+'bangitata', tin_roof_tick from a snow-house roof + 'heat'."""
    def spans(words):
        out = []
        for w in words:
            for m in re.finditer(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", low):
                out.append(m.start())
        return out
    ns = spans(names)
    if not ns:
        return False
    ss = spans(sounds)
    return any(abs(a - b) <= _TIE_WINDOW for a in ns for b in ss)


def learn_from_text(text: str) -> list[str]:
    """His reading/scholarship can teach a call: if a text ties a source's name to its sound-words,
    the association is learned — the diegetic channel. Returns newly-learned keys."""
    out: list[str] = []
    try:
        if not SOUND_EPISTEMICS or not text:
            return out
        low = text.lower()
        led = _load()
        for key, spec in AUDITION.items():
            if _weight(led, key) >= _LEARN_AT:
                continue
            if _ties_name_to_sound(low, spec["book_names"], spec["book_sounds"]):
                _add_event(led, key, "read", 1.0, low[:80])
                out.append(key)
        if out:
            _save(led)
    except profile.NonLiveWriteError:
        # J-0784: same -- study_note.py's own call site already re-raises through its own three
        # layers (J-0770); do not let this function's own broad except be a fourth swallow point.
        raise
    except Exception:
        pass
    return out


def status() -> dict:
    """For the pulse: what he has come to know by ear."""
    try:
        led = _load()
        learned = [k for k in AUDITION if _weight(led, k) >= _LEARN_AT]
        learning = {k: _weight(led, k) for k in AUDITION if 0 < _weight(led, k) < _LEARN_AT}
        return {"enabled": SOUND_EPISTEMICS, "learnable": len(AUDITION),
                "learned": learned, "learning": learning,
                "recent_heard": len(_load().get("recent", []))}
    except Exception:
        return {"enabled": SOUND_EPISTEMICS}
