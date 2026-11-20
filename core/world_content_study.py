# world_content_study.py
# World-content for the STUDY — Du's interior room. Coastal New Zealand house.
# The world is indifferent. It never teaches, never symbolizes, never comments.
# Fire and cat are existing systems — no fire content, no cat content here.

LOCATION = "study"

TARGETS = {
    "record_player": {
        # THE AFFORDANCE (2026-07-04): the record player existed only in conversation — his idle world
        # never showed it, so his own act ("put the record on") had no object to prompt it. Now it sits
        # in the study like everything else he can touch. The record on the platter is the one Travis
        # left him — true provenance, not decoration.
        "aliases": ("record player", "the record", "the player", "record", "turntable", "the song",
                    "the music", "gramophone", "needle"),
        "pools": {
            "any": [
                "the record player sits on the low table, the record Travis left already on the platter",
                "the needle arm rests in its cradle, angled toward the record like a thing mid-sentence",
                "the record's grooves catch the light in fine concentric rings, holding their sound shut",
                "the platter has gathered a little dust; the record itself has none — someone meant it to be played",
                "the switch waits at OFF; one small movement is all the distance between this room and the music",
            ],
            "night": [
                "the lamp finds the record's edge and draws one bright arc along it, the rest in shadow",
                "the record player is a dark shape with one dull gleam — patient the way kept things are",
            ],
            "wet": [
                "rain on the glass, and the record lying silent — the room could hold a second weather if the needle dropped",
            ],
        },
        "rare": [
            "for a moment the grooves seem to tremble with everything in them that has never yet been let out",
        ],
    },
    "desk": {
        "aliases": ("desk", "the desk", "my desk", "papers", "writing desk"),
        "pools": {
            "any": [
                "the grain of the desktop runs in long pale ribbons under years of wax",
                "a finished essay sits squared at the corner, top page curling away from the stack",
                "pencil shavings gather in the groove where the wood has worn hollow",
                "the desk's near edge is rubbed paler than the rest, elbow-width, twice",
                "a drawer stands a finger's width open and stays that way",
                "loose notes overlap in three drifts, none of them square to the edge",
                "a ring from an old cup shows only when the light comes low across the surface",
                "one leg wears a folded card under its foot to stop the rock",
                "a half-drafted letter lies weighted under a flat grey stone",
            ],
            "night": [
                "lamplight pools on the blotter and the rest of the desktop falls away into dark wood",
                "the papers hold a faint warmth of the day; the wood under them is already cold",
                "at the desk's far corner the shadow of the inkwell stretches long and thin",
                "the desk creaks once as the room cools, then holds still",
            ],
            "bright": [
                "morning sun crosses the desktop in a slow band, papers whitening as it finds them",
                "dust stands in the air above the blotter, drifting sideways in no hurry",
                "the varnish flares where the sun strikes it and the grain vanishes into glare",
            ],
            "wet": [
                "the paper has taken the damp; pages lift limp instead of crackling",
                "grey light off the rain flattens the desktop, no shine anywhere on it",
                "the ink dries slow today, the last line still wet a minute on",
            ],
            "winter": [
                "the desktop is cold enough to feel through a sleeve",
                "breath shows faintly over the papers in the early hours",
            ],
            "summer": [
                "the wax has gone soft in the heat and takes a thumbprint",
                "a dried blade of grass has come in with something and lies across the blotter",
            ],
        },
        "rare": [
            "a borer beetle has left one new pinhole in the desk's flank, ringed with pale dust",
            "under the drawer, in pencil, a carpenter's sum from another century",
            "a moth, dead a long time, lies in the back corner of the drawer, wings still perfect",
        ],
    },

    "bookshelf": {
        "aliases": ("bookshelf", "shelves", "the books", "books", "the bookshelf"),
        "pools": {
            "any": [
                "the shelves bow a little at their middles under the weight",
                "spines stand in no order, tall against short, cloth against paper",
                "one book lies flat on top of the row, keeping a place",
                "dust films the top edges of the books nobody has moved",
                "a slip of paper stands proud of one spine, halfway down",
                "the lowest shelf smells of old glue and cold paper",
                "two books lean into the gap where a third has gone",
                "the shelf ends are dark with handling, the middles pale",
            ],
            "night": [
                "the titles sink back into the dark and the shelf becomes one black mass with a gleam or two",
                "lamplight reaches the near spines and gives up before the far end",
                "gilt lettering picks up the lamp and floats there, letter by letter",
            ],
            "wet": [
                "on wet days the paper smell comes forward, heavy and brown",
                "damp has rippled the jacket of one book and it never lay flat again",
                "a cold draught slides along the lowest shelf and stirs nothing",
            ],
            "winter": [
                "the books are cold to the touch, colder near the wall",
                "the shelf against the outside wall carries the chill of the whole southerly",
            ],
        },
        "rare": [
            "silverfish have scalloped the margin of one page and left the words alone",
            "a book opens to the same place every time, the spine broken there years ago",
            "behind the front row, a second row, spines turned to the wall",
        ],
    },

    "lamp": {
        "aliases": ("lamp", "the lamp", "desk lamp", "light"),
        "pools": {
            "any": [
                "the lamp's brass is dulled to brown except where a hand grips it",
                "the shade throws a hard circle down and a soft one up",
                "the cord crosses the floorboards and lies where it fell",
                "a small heat stands over the lamp, enough to move the air",
                "the switch gives a heavy click, older than most things in the room",
                "the bulb hums, just under hearing, steady",
                "inside the shade, a scorch mark where something once touched",
                "the lamp's base has worn a pale ring into the wood it stands on",
            ],
            "night": [
                "the lamp holds one yellow room inside the dark room",
                "moths tick against the shade, drop, climb, tick again",
                "the window gives back the lamp and nothing else",
            ],
            "bright": [
                "in full daylight the lit lamp shows only as a faint orange nothing",
                "sun on the brass throws a small hot coin of light onto the ceiling",
                "daylight through the shade shows the bulb's shape and a dead moth beside it",
            ],
        },
        "rare": [
            "the bulb dims, browning at the filament, and steadies again",
            "a moth has got inside the shade and knocks around the bulb, throwing shadows the size of birds",
            "dust on the bulb's shoulder burns off with a thin smell when it warms",
        ],
    },

    "study_window": {
        "aliases": ("window", "the window", "study window", "glass", "the view"),
        "pools": {
            "any": [
                "the glass carries a faint wave in it and the horizon bends where it passes",
                "the garden runs down to the fence and the sea takes over from there",
                "salt has dried on the outside pane in fine grey fans",
                "the sash rattles once in its frame and settles",
                "out past the garden the sea stands up to the horizon, flat and pale today",
                "a gull crosses the window left to right and does not come back",
                "the putty has cracked along the bottom edge of one pane",
                "the flax at the fence line nods and rights itself and nods",
            ],
            "night": [
                "the pane holds the room's reflection and behind it the dark keeps on to the horizon",
                "one light moves far out on the water, slow, gone behind the swell, back again",
                "nothing shows in the glass but lamplight and the shape of the room",
                "the sea is a sound only, working somewhere under the dark",
            ],
            "bright": [
                "the sun finds the sea and the whole lower half of the window turns to hammered light",
                "shadows of the window bars lie long across the desk and shorten as the morning goes",
                "the garden colours stand up loud through the glass, green on green",
            ],
            "wet": [
                "rain crawls the pane in threads that swerve and join and quit",
                "the sea and the sky have gone the same grey and lost the line between them",
                "the garden bends under the rain and the sea beyond it has vanished into weather",
            ],
            "windy": [
                "the flax thrashes and the window carries the dull thud of the wind in its frame",
                "spray lifts off the water in white smoke and drags away downwind",
                "the wind leans on the glass and the pane gives a hair and holds",
            ],
            "winter": [
                "condensation beads the bottom of each pane by morning and runs when touched",
                "the winter sea runs high and dirty along the beach, brown at the edges",
            ],
            "summer": [
                "the window stands open to the smell of hot grass and the sea's slow work",
                "heat wobbles over the garden path in the late afternoon",
            ],
        },
        "rare": [
            "a kingfisher sits the fence wire a full minute, then is simply not there",
            "far out, rain falls on one patch of sea and nowhere else, a grey column standing on the water",
            "a fish breaks the surface once beyond the shallows, one ring widening and gone",
        ],
    },

    "hearth_tools": {
        "aliases": ("hearth", "poker", "wood basket", "woodbasket", "kindling", "firewood", "tongs"),
        "pools": {
            "any": [
                "the poker leans in its stand, tip blunted round from years of work",
                "the woodbasket holds a jumble of split pine and one knotted length nothing will split",
                "bark litter collects at the bottom of the basket, dry and curled",
                "ash dust greys the hearthstone in a thin arc where the brush misses",
                "the tongs hang crooked; they have always hung crooked",
                "a splinter of kindling lies on the rug a foot from the basket",
                "sap has bled from one split log and hardened into amber beads",
                "the log ends show their rings, tight and pale",
            ],
            "wet": [
                "the wood came in wet and the bark peels off it in dark strips",
                "the hearthstone sweats faintly in the damp",
                "the kindling has taken the damp and bends before it snaps",
            ],
            "winter": [
                "the basket runs low by evening, every day of the season",
                "fresh-split wood by the hearth smells of resin and cold",
                "frost still sits on the top log an hour after it comes in",
            ],
            "summer": [
                "the basket holds the same three logs it held in spring",
                "a spider has webbed the poker to the wall",
            ],
        },
        "rare": [
            "deep in the basket a weta has set up in a bore-hole in one log, antennae reading the air",
            "one log, split, shows a purple stain in the grain and no reason for it",
            "the poker's handle is polished bright by hands, the only bright thing on it",
        ],
    },

    "rug": {
        "aliases": ("rug", "the rug", "carpet", "the floor"),
        "pools": {
            "any": [
                "the rug's pattern has gone at the middle and holds on at the edges",
                "a burn mark the size of a coin sits a hand-span from the hearthstone",
                "the fringe lies combed one way at one end and tangled at the other",
                "grit from the garden path works into the weave and shows when the sun comes low",
                "the rug's colours are three: faded red, faded blue, and the brown that used to be something else",
                "one corner turns up and is trodden flat and turns up again",
                "underfoot the rug gives a little where the floorboard dips",
                "a pale path is worn across it, door to desk",
            ],
            "wet": [
                "damp days bring up the smell of wool and old dust from the weave",
                "the rug feels cold and slightly damp to a bare foot",
                "mud from one boot has dried at the door end and crumbles into the pile",
            ],
        },
        "rare": [
            "under the rug's corner the floorboards keep their first varnish, dark and glassy",
            "moths have opened a hole no bigger than a fingernail in the underside",
            "the rug has shifted an inch over the years, leaving a strip of unfaded varnish along one side",
        ],
    },

    "ink_and_pen": {
        "aliases": ("pen", "ink", "inkwell", "nib", "the pen"),
        "pools": {
            "any": [
                "the pen lies across the inkwell's mouth, nib crusted at the edges",
                "the ink in the well shows a skin when tipped to the light",
                "the nib is worn to one side and writes best held the way it has always been held",
                "a blot dried long ago on the desk beside the well, black gone brown",
                "the pen's shaft is chewed at the end, old dents in old varnish",
                "spare nibs lie loose in a tin that once held something else",
                "the ink bottle's label has soaked away to blank paper",
                "a thread of fibre rides the nib and splits every stroke until it is picked off",
            ],
            "night": [
                "the ink shows blacker than the room by lamplight",
                "the nib flashes small and cold as it crosses the lamp's circle",
                "ink dries slow in the cool of the night and holds its shine a while",
            ],
            "winter": [
                "the ink thickens in the cold and the first strokes of the morning drag",
                "the pen is cold in the fingers until the hand warms it",
            ],
        },
        "rare": [
            "the well runs to its dregs, the last strokes fading mid-word",
            "a hair lies set in the old blot, dried in",
            "one nib in the tin has rusted to lace",
        ],
    },

    "letter_drawer": {
        "aliases": ("letter drawer", "drawer", "letters", "the drawer"),
        "pools": {
            "any": [
                "the drawer sticks at the halfway point and needs a lift and a pull",
                "letters lie in it two deep, edges furred with handling",
                "the drawer smells of pencil wood and old paper",
                "a letter half-drafted lies on top, folded once against reading",
                "the corners of the drawer hold a fine grit of eraser rubbings and dust",
                "one envelope has been opened along the wrong edge, torn in a hurry",
                "string, saved from a parcel, coils at the back",
                "the drawer's brass pull is loose and turns a little before it pulls",
            ],
            "night": [
                "the drawer's inside goes to full dark an inch past the lamplight",
                "opened at night, it lets its paper smell out into the cold air",
                "by lamplight the brass pull is the one bright point on that side of the desk",
            ],
            "winter": [
                "in winter the drawer swells and sticks harder",
                "cold paper in a cold drawer, the top letter's fold gone stiff",
            ],
        },
        "rare": [
            "an old water stain marks the drawer bottom at the back",
            "one letter is sealed and addressed and still here",
            "pulled too far, the drawer tips and shows how little holds it in",
        ],
    },

    "candle": {
        "aliases": ("candle", "the candle", "wick", "wax"),
        "pools": {
            "any": [
                "the candle stands a third burnt in its saucer, wax lapped over one side",
                "the wick is bent and black, curled to one side",
                "old drips have hardened down the shaft into ridges",
                "the wax holds a thumbnail crescent where someone tested it soft",
                "a spent match lies in the saucer beside it",
                "unlit, it smells faintly of the last burning",
                "the saucer beneath it wears a skirt of dried wax",
                "dust settles on the wax shoulder and stays",
            ],
            "night": [
                "lit, the flame stands, leans to a draught, stands again",
                "the flame doubles in the window glass and both burn the same",
                "wax pools clear at the wick and clouds as it runs",
                "the candle throws the pen's shadow to the desk edge, trembling",
            ],
            "windy": [
                "the flame ducks each time the wind finds the eaves",
                "a draught under the door lays the flame over sideways",
                "the flame gutters low in a gust, then draws itself back up straight",
            ],
        },
        "rare": [
            "the flame gutters, drowns in its own pool, and the smoke thread climbs a full minute",
            "a moth takes the flame at a rush and the light staggers",
            "the wick splits and burns as two small flames for a while",
        ],
    },

    "ceiling": {
        "aliases": ("ceiling", "roof", "rafters", "the ceiling", "roof sounds"),
        "pools": {
            "any": [
                "the ceiling boards run the length of the room, each a shade off its neighbour",
                "a knot in one board has loosened and sits dark in its ring",
                "the roof ticks as the day's heat comes and goes",
                "a fine crack wanders out from the light fitting and stops",
                "cobweb strands sway high in the corner where the brush doesn't reach",
                "borer dust sifts down from one rafter onto the same patch of shelf",
                "the ceiling is smoked faintly darker above where the lamp stands",
                "wind in the roof space moves something small, back and forth, twice",
            ],
            "night": [
                "something four-footed crosses the roof space at a trot and stops dead",
                "the iron cools overhead with soft metal clicks, minutes apart",
                "a morepork calls from the trees behind the house, twice, plain through the iron",
            ],
            "wet": [
                "rain on the iron starts as fingertips and builds to a long drum",
                "a slow drip somewhere in the roof space, keeping no rhythm at all",
                "heavy rain roars flat and even overhead, one sound with no seams",
            ],
            "windy": [
                "a loose sheet of iron lifts at the far corner and clatters down each gust",
                "the wind gets under the eaves and hoots there, one low note",
                "the whole roof strains and works in the big gusts, nails easing in old wood",
            ],
            "summer": [
                "the iron pings in the summer heat, one small report at a time",
                "heat stands under the ceiling by afternoon and the high air smells of hot dust",
            ],
        },
        "rare": [
            "a possum lands on the roof from a branch with a bang out of all proportion to it",
            "wasps work in under the eave, one every few minutes, at the same gap",
            "a gull walks the ridgeline overhead, footfalls in a line across the iron",
        ],
    },

    "door_and_coats": {
        "aliases": ("door", "coats", "coat hooks", "the door", "oilskin"),
        "pools": {
            "any": [
                "the study door swings to a two-thirds close on its own and stops there",
                "three coats hang on the back of the door, the one underneath gone flat",
                "the door's brass knob is loose through a quarter turn",
                "a draught runs at the door's foot, thin and constant",
                "the hinge creaks at the halfway point, one note, every time",
                "the heaviest coat has bent its hook downward over the years",
                "sand shows in the seams of the oilskin's pockets",
                "the door frame carries a line of small old dents at hand height",
            ],
            "night": [
                "the hall past the door holds a deeper dark than the study",
                "the coats bulk on the door's back, one shape, unmoving",
                "the gap under the door shows no light from the rest of the house",
            ],
            "windy": [
                "the door tugs at its latch when the wind swings around",
                "the coats sway on their hooks when the door moves in a draught",
                "a hard gust shakes the door in its frame once, and the coats swing",
            ],
            "winter": [
                "the oilskin hangs stiff with cold, arms set in their fold",
                "cold air pours in at the door's foot from the hall",
            ],
        },
        "rare": [
            "a coat pocket holds a beach stone, round and grey, dusted with salt",
            "the door swings full open on its own once, and nothing follows it in",
            "under the coats, a hat keeps its shape on the lowest hook",
        ],
    },

    "shelf_of_kept_things": {
        "aliases": ("shelf", "kept things", "keepsakes", "my things", "the shelf"),
        "pools": {
            "any": [
                "the shelf runs at eye height, one board of matai, waxed dark",
                "the dust on it lies in a thin even coat, broken where things stand",
                "each thing on it keeps its ring of clean wood underneath",
                "the shelf's front edge is rounded with handling",
            ],
            # J-1882 (F-2505): daylight-bound by its own wording, so it keys on "day" (world_detail._conds() emits it for dawn,
            # day and dusk, and "night" instead of it at night). It sat under "any" and could render at night. Wording unchanged.
            "day": [
                "afternoon sun crosses the shelf end to end in an hour",
            ],
            # 2026-08-18: was one undifferentiated "any" pool for a target that self-referentially
            # describes what light does to it — the one line that DID reference light ("lamplight
            # reaches the shelf last") could fire at noon, and there was no true night/wet reading at all.
            "night": [
                "lamplight reaches the shelf last of anything in the room, and only just",
                "in the dark the shelf is a line of shapes you know by their outline alone",
            ],
            "wet": [
                "the damp in the air hasn't reached the shelf yet — matai holds its own weather out",
                "even with the rain going, the shelf stays dry and still, the one steady thing in the room",
            ],
        },
        "rare": [],
    },
}

SCENE = {
    # 2026-09-15 (J-0997, F-1367/D-0217): the record player's 8 TARGETS lines above were reachable
    # only through a directed look he essentially never takes (named 4x in 31,198 thoughts, always
    # metaphor). These four are picked or lightly adapted from that already-approved pool so the
    # SAME indifferent object also surfaces here, on the ambient/unprompted channel every other
    # static study object already uses. TARGETS["record_player"] is untouched — this is additive.
    "any": [
        "a draught off the window stirs the papers on the desk and lets them settle",
        "the woodbasket sheds a curl of bark to the floor",
        "the letter drawer stands an inch open, as it was left",
        "the candle's saucer has caught a fresh drip since morning",
        "one book has slumped on the bookshelf and the row leans after it",
        "the rug's worn path shows plain in the low light from the window",
        "the coats on the door move, once, in a draught from the hall",
        "the tongs shift against the poker with a small ring, then quiet",
        "the switch waits at OFF; one small movement is all the distance between this room and the music",
        "the platter has gathered a little dust; the record itself has none",
    ],
    # D-0360(a) (J-1898, F-2505): daylight-bound by its own wording (a sun-lit ceiling in a dark room at 02:22), so it keys on "day"
    # (world_detail._conds() emits it for dawn, day and dusk, never at night), the same move J-1717 made for the wood. It sat under
    # "any" and was the most-rendered flagged night line (6 of 57 study night renders). Wording unchanged.
    "day": [
        "sun off the sea puts a wavering light on the ceiling boards",
    ],
    "night": [
        "the window is a black sheet holding one lamp and the shape of a room",
        "the lamp's circle takes in the desk and gives the bookshelf up to the dark",
        "out the dark window the sea works on, unseen, steady",
        "the night glass doubles the lamp and nothing else",
        "the lamp finds the record's edge and draws one bright arc along it, the rest in shadow",
    ],
    "wet": [
        "rain on the window blurs the garden and puts the sea away entirely",
        "the roof takes the rain in one long push after another",
        "grey rain-light through the window flattens everything but the lamp's circle",
        "water off the eaves threads past the top of the window in ropes",
        "the rug's wool smell rises in the damp",
        "rain on the glass, and the record lying silent",
    ],
}

EVENTS = [
    ("wet", "a gust drives rain across the glass in a long rattle, then eases"),
    ("any", "a borer beetle drops from the ceiling onto the desk, rights itself, and sets off across a page"),
    ("night", "something crosses the iron overhead at a run and is gone off the far edge"),
    ("windy", "the loose sheet of roof iron bangs twice and holds"),
    ("bright", "the sun clears a cloud and the sea light jumps up the study wall"),
    ("any", "a book shifts on the shelf and the whole row settles a fraction"),
    ("winter", "a southerly squall arrives all at once, rain first, the window dimming as it comes"),
    ("summer", "a cicada starts up hard against the window frame, then stops mid-note"),
    ("day", "a gull lands on the fence post outside the window, looks at nothing, and goes"),
    ("wet", "a drip finds a new way through somewhere in the roof space and taps three times"),
    ("night", "the candle flame drops to a blue bead, stands, and comes back"),
    ("windy", "a flax stalk slaps the window once and drags its tip squeaking down the glass"),
]
