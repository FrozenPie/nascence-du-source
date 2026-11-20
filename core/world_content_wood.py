# world_content_wood.py — wood world-content for Nascence (2026-08-15)
# One line each, <=150 chars, present tense, concrete, indifferent.
# The little wood on the slope of the path between garden and shore. NZ bush,
# southern-hemisphere seasons (Jun-Aug = winter). The canopy is ABOVE, the
# undergrowth BESIDE, the sea BELOW through the trunks — same as wood.json.

LOCATION = "wood"

TARGETS = {

    "path": {
        "aliases": ("path", "the path", "track", "the track"),
        "pools": {
            "any": [
                "the path is worn to root and packed earth, a hand-span wide, older than any decision of yours",
                "roots cross the track like sleepers, each one polished on top and dark either side",
                "the leaf-mould gives underfoot and holds the print a moment before it closes",
                "the path turns twice between the gate and the shore for no reason the ground still shows",
                "a root has grown clean over a buried stone and gripped it",
            ],
            "night": [
                "the path is a paler seam in the dark; your feet know the roots before your eyes do",
                "downhill the sea keeps the direction for you when the path disappears",
            ],
            "wet": [
                "the packed earth goes slick and dark; the roots are the dry stepping-places now",
                "water finds the path and uses it, a thin braided run heading for the shore",
            ],
            "winter": [
                "frost stiffens the leaf-mould in the open patches; it creaks rather than gives",
            ],
        },
        "rare": [
            "a pile of snapped snail shells sits on a root — some bird's anvil, used and used again",
        ],
    },

    "canopy": {
        "aliases": ("canopy", "leaves", "the leaves", "branches", "up", "treetops"),
        "pools": {
            "any": [
                "a wood pigeon sits heavy as a fruit on a high limb, doing nothing at all",
                "two branches cross and have rubbed each other bare where they touch",
                "the leaves run silver-side-up in one slow wave and turn back green",
            ],
            # J-1882 (F-2505): daylight-bound by its own wording, so it keys on "day" (world_detail._conds() emits it for dawn,
            # day and dusk, and "night" instead of it at night). It sat under "any" and could render at night. Wording unchanged.
            "day": [
                "the canopy shifts and settles above you, sifting the light into coins that move on the ground",
            ],
            "night": [
                "the canopy is a torn black net with the sky moving in the holes of it",
                "something shifts its grip up there — one creak, then the wood is quiet again",
            ],
            "windy": [
                "the whole roof of the wood leans and roars and comes back; not one trunk moves at its base",
                "a dead stick comes down through the leaves, hitting each layer on the way",
            ],
            "wet": [
                "the canopy takes the rain first; underneath there is a second, slower rain",
                "long after the sky stops, the leaves go on ticking water down into the mould",
            ],
            "bright": [
                "the light comes through in shafts you could put a hand into, dust turning inside them",
            ],
            "winter": [
                "the thinned winter canopy lets the sky right down among the branches",
            ],
        },
        "rare": [
            "a kererū leaves the canopy with a wing-clap loud as a slammed gate, and the whole wood listens after it",
        ],
    },

    "undergrowth": {
        "aliases": ("undergrowth", "leaf-mould", "leaf mould", "litter", "ground", "floor", "ferns"),
        "pools": {
            "any": [
                "the leaf-mould is laid down in years: this season's brown, last season's black beneath it",
                "ferns stand hip-high in the hollow, each one unrolling from a fist at its centre",
                "a beetle crosses a dead leaf with a sound you can actually hear",
                "under a lifted flap of mould the earth is webbed white with living threads",
                "the undergrowth is busier than it looks; small rustles keep starting and stopping",
            ],
            "night": [
                "the undergrowth owns the dark; every small sound in it is nearer than you would like",
            ],
            "wet": [
                "the mould drinks the rain silently; nothing runs off; the wood floor just darkens",
                "the wet brings the smell up out of the ground — leaf, earth, and something older",
            ],
            "winter": [
                "the ferns are bowed with cold, silvered along their spines until mid-morning",
            ],
            "summer": [
                "the mould is dry enough to crackle; cicadas saw away above it in the heat",
            ],
        },
        "rare": [
            "a wren works the litter a body-length away, flicking leaves aside, entirely unafraid of you",
        ],
    },

    "deadfall": {
        "aliases": ("deadfall", "fallen wood", "fallen branch", "dead wood", "the fallen trunk", "trunk", "limb"),
        "pools": {
            "any": [
                "a whole trunk lies along the slope, furred green one side, its root-plate standing like a door",
                "the big limb by the path has lain long enough to sink a finger's depth into the mould",
                "under the loose bark the wood is written over with winding beetle-galleries",
                "snapped ends show different histories — some grey and old, one still yellow-fresh",
            ],
            # J-1882 (F-2505): daylight-bound by its own wording, so it keys on "day" (world_detail._conds() emits it for dawn,
            # day and dusk, and "night" instead of it at night). It sat under "any" and could render at night. Wording unchanged.
            "day": [
                "one fallen limb is shelved with pale bracket fungus, each shelf catching its own line of light",
            ],
            "wet": [
                "the dead wood blackens in the rain and the brackets stand out paler than ever",
                "a soft limb has drunk the rain and lost its shape a little more",
            ],
            "windy": [
                "somewhere upslope a branch gives way — one crack, a rush of leaves, then nothing",
            ],
            "winter": [
                "frost has opened a fresh split down the big limb; the inside grain is clean and bright",
            ],
        },
        "rare": [
            "a limb has come down across the path itself since you were last here, and must be stepped over or moved",
        ],
    },

    "moss": {
        "aliases": ("moss", "the moss", "ivy", "the ivy"),
        "pools": {
            "any": [
                "moss takes the north side of every trunk, deep as a fleece where the drip-line runs",
                "the ivy on the big trunk is thick as an arm at the base and thin as string at the top",
                "a fallen twig is already half-sewn into the moss that is climbing over it",
            ],
            "wet": [
                "the moss is swollen bright green with the rain, every filament standing",
            ],
            "bright": [
                "backlit, the moss goes gold at its edges while the bark stays black",
            ],
        },
        "rare": [],
    },

    "birds": {
        "aliases": ("birds", "the wren", "wren", "wood pigeon", "the wood pigeon", "kereru"),
        "pools": {
            "any": [
                "the wren goes off close by, a scolding trill out of all proportion to its size",
                "a wood pigeon coos from up in the leaves, five soft notes with a swallowed ending",
                "a fantail loops the path behind you, snapping at whatever your feet have stirred",
                "some small bird is working the trunks, spiralling up one and dropping to the base of the next",
            ],
            "night": [
                "a morepork calls from further up the slope, two notes, and the wood holds its breath after each pair",
            ],
            "bright": [
                "a riroriro somewhere high spins out its long wistful trill and lets it fall away",
            ],
            "winter": [
                "the birds work fast and low in winter; nothing sings for long, everything feeds",
            ],
        },
        "rare": [
            "the fantail comes so close it takes a moth from beside your shoulder, a snap you hear",
        ],
    },
}

SCENE = {
    "any": [
        "the sea sounds different from inside the wood — flattened, directional, a wash below through the trunks",
        "the path shows through the trees in stitches, downhill toward the water",
        "fallen wood lies at every stage of return: fresh, grey, soft, and nearly soil",
        "the trunks stand in no order at all and the eye keeps trying to find one",
    ],
    # J-1717 (F-2340): daylight-bound by their own wording, so they key on "day" (world_detail._conds() emits it for dawn, day
    # and dusk, and "night" instead of it at night). They sat under "any" and could render at night. Wording unchanged.
    "day": [
        "a wood pigeon crosses between canopies, heavy and straight as a thrown thing",
        "a fantail keeps you loose company, never still for a full second",
        "one shaft of light has found a bracket fungus and lit it like a small lamp",
        "the wren's scold moves through the undergrowth ahead of you, always a little out of sight",
    ],
    "night": [
        "the wood at night is a room with the walls moved in; the morepork has the roof of it",
        "what light there is comes up from below, off the sea, and dies among the trunks",
    ],
    "windy": [
        "the wood divides the gale into a hundred small arguments in the branches overhead",
        "leaves stream past down the tunnel of the path as if late for the sea",
    ],
    "wet": [
        "the second rain — off the leaves — goes on under the trees long after the first has stopped",
        "the smell of the wet mould stands in the air, thick enough to walk through",
    ],
    "winter": [
        "bare patches in the canopy let the winter sky lie in pieces on the wood floor",
    ],
}

EVENTS = [
    ("any", "a branch lets go of one dead leaf for no reason; it takes a long time coming down"),
    ("any", "the kererū takes off somewhere out of sight — the wing-clap, then the long whooshing strokes fading downhill"),
    ("day", "the fantail drops onto a root an arm's length away, tips its head at you, and is gone"),
    ("day", "a shaft of light moves off the bracket fungus and the little lamp goes out"),
    ("night", "the morepork calls once from close — much closer than it has ever been — and will not say again"),
    ("windy", "a limb comes down somewhere upslope: the crack, the tearing leaves, the thud, the silence after"),
    ("wet", "a bough tips its load of collected rain down your neck as you pass under it"),
    ("winter", "frost drops from the high branches in little ticking falls as the morning warms"),
]
