# world_content_shore.py — shore world-content for Nascence
# One line each, <=150 chars, present tense, concrete, indifferent.
# NZ coast, southern-hemisphere seasons (Jun-Aug = winter).

LOCATION = "shore"

TARGETS = {

    "driftwood": {
        "aliases": ("driftwood", "the log", "log", "wood", "the driftwood log"),
        "pools": {
            "any": [
                "the log lies where the last big tide left it, silvered grey, sand banked against its seaward side",
                "salt has opened the grain into long ridges you can follow with a thumbnail",
                "a knot has fallen out and left a clean round socket, damp at the bottom",
                "sandhoppers burst from under the log and rain back onto the shingle",
                "the roots at one end are worn to blunt fists, the bark long gone",
                "someone's old fire has blackened one flank; the char flakes off under a finger",
                "the wood is cold on the shadow side and holds a little warmth where the light has been",
                "barnacle scars pit the underside — this tree floated a long time before it landed",
                "a copper nail stands proud of the wood, crusted green",
                "dry sand has drifted into the split at the thick end and sits there in a smooth tongue",
            ],
            "night": [
                "the log is a low black bar; you find it with your shin before your eyes",
                "dew stands on the silvered wood, cold under the flat of a hand",
                "something small moves along the underside and stops when you stop",
            ],
            "bright": [
                "the grain throws hard little shadows; every ridge has its dark line",
                "the silvered wood goes almost white in full sun",
                "flies stand about on the dry wood, lifting and settling",
            ],
            "wet": [
                "rain darkens the log from the top down; the underside stays pale and dry",
                "water beads on the salt-hardened grain and runs off in one line",
                "the char smells of old fires again once the rain gets into it",
            ],
            "windy": [
                "sand streams past the log ankle-high and builds against the seaward side while you watch",
                "the log does not move; everything smaller than it is moving",
                "dry weed caught along the top rattles and tugs but stays snagged",
            ],
            "winter": [
                "frost sits in the grain hollows on the shadow side until mid-morning",
                "the winter storms have shifted the log a body-length up the beach since last month",
            ],
            "summer": [
                "dry weed lies caught the whole length of the log, bleached and rattling",
                "the sand around the log is loose and hot on top, cool a knuckle down",
            ],
            "high_tide": [
                "the biggest swells send water up to the log's seaward side and no further",
                "foam collects against the log and shivers there before the shingle drinks it",
                "the sea's sound stands closer; the log marks how far the water means to come",
            ],
        },
        "rare": [
            "a blue rope-end is jammed deep under the log, sun-bleached nearly white",
            "a skink flicks off the warm wood and is gone into the dune grass",
            "fresh sawdust at one end — someone has taken a piece with a handsaw",
            "a karoro stands on the highest root on one foot and does not move for you",
        ],
    },

    "kelp": {
        "aliases": ("kelp", "wrack", "seaweed", "weed", "rimurapa", "the kelp heaps"),
        "pools": {
            "any": [
                "rimurapa lies in heaps at the last high-water mark, straps thicker than a thumb",
                "the wrack pops under a boot — bladderwrack, its little floats still tight",
                "kelp flies rise in a cloud when you turn a strap, and settle again behind you",
                "neptune's necklace drapes a stone in olive strings, cool and full of water",
                "under the wrack the shingle is dark, wet, and busy with hoppers",
                "a holdfast still grips its fist-sized stone; the stone came ashore with it",
                "sea lettuce, bright green, gone thin and papery where it has dried",
                "the smell is iodine and rot, strongest where the heap lies deepest",
                "one strap reaches out of the heap and down the shingle, pointing at the water it came from",
            ],
            "night": [
                "the kelp heaps are blacker than the shingle; the smell finds you before they do",
                "something rustles deep in the wrack and stops",
                "the heap holds the day's damp; a hand laid on it comes away cold and salt",
            ],
            "bright": [
                "dried kelp straps have curled into hard brown scrolls",
                "the necklace weed still shines full of water where the shade holds",
                "flies stand thick on the sunny side of the heap and thin on the other",
            ],
            "wet": [
                "rain fills the bladderwrack cups and the whole heap glistens",
                "the kelp goes glossy and slick; the straps slide off each other underfoot",
            ],
            "windy": [
                "the light dried weed goes end over end up the beach; the wet heaps hold their ground",
                "the top straps lift and slap back down in the gusts",
                "flies stay deep in the lee of the heap and will not rise",
            ],
            "winter": [
                "the winter heaps are the biggest of the year, storm-torn and half a leg deep",
                "the newest kelp still has its colour, amber-brown; the old heaps have gone to black",
            ],
            "low_tide": [
                "the living kelp lies down flat off the low rocks, streaming seaward",
                "the kelp beds show offshore, dark slicks on the water",
                "necklace weed and wrack sit exposed on the boulders, waiting the tide out",
            ],
            "high_tide": [
                "the swell works the kelp bed; straps roll and slap at the rock edge",
                "loose weed rides the swash line, in and out, going nowhere",
            ],
        },
        "rare": [
            "a whole holdfast, stone and all, thrown a good ten paces above the tideline",
            "a dried bladder float gone hard as a bead, holed clean through",
            "a horned egg case, dry and black, caught deep in the wrack",
            "a strap of rimurapa longer than the driftwood log, laid out straight",
        ],
    },

    "shells": {
        "aliases": ("shells", "shell", "the shell drift", "pupu", "pūpū"),
        "pools": {
            "any": [
                "cat's eye shells scatter the tideline, most broken, a few with their green door still in place",
                "a pāua fragment turns blue, then green, as you turn it",
                "a perfect pūpū, whole and unchipped, heavier than it looks — it fits in a pocket",
                "limpet shells lie open-side up, little dishes holding sand",
                "a tower shell wound tight, its point unbroken",
                "most of what looks whole turns up broken on the underside",
                "purple half-shells of kūtai, the hinged pairs long since parted",
                "the shell drift runs thickest in one band, where the last spring tide dropped it",
                "a worn white disc that was once a shell, ground past naming",
            ],
            "bright": [
                "the pāua chips fire blue-green out of the grey shingle; you see them at ten paces",
                "sun through a held limpet shell shows the thin worn place at its peak",
                "the whole drift glitters once, when you move, then goes back to being stones",
            ],
            "night": [
                "the shells are all one colour now; the fingers do the sorting",
                "a whole shell underfoot gives that hollow crack the broken ones don't",
            ],
            "wet": [
                "rain wakes the colours; every wet shell shows more than it did dry",
                "the drift stops crackling underfoot and goes quiet and slick",
            ],
            "low_tide": [
                "fresh shell comes up shining at the water's edge, still wet from the sea",
                "hermit crabs drag borrowed pūpū across the sand between the pools",
                "a live cushion star holds a broken cockle against the rock, unhurried",
            ],
            "winter": [
                "winter storms bring up deep-water shells the summer never shows",
                "the drift is coarser now — heavy shell, thrown hard, half of it new since the last blow",
            ],
        },
        "rare": [
            "a whole pāua shell, palm-sized, its inside all lit blue-green, barnacles crusting the back",
            "a violet sea-snail shell, whole, so light the wind could take it",
            "a fan scallop with both halves still hinged",
            "a shell drilled by something with one neat round hole, ready-strung",
        ],
    },

    "headland": {
        "aliases": ("headland", "the point", "point", "the headland rocks"),
        "pools": {
            "any": [
                "the headland shoulders out into the sea and takes the swell first; the white burst shows before the sound arrives",
                "spray hangs over the point after each set, drifts inland, and is gone",
                "the rocks at its base stay black and wet even at low water",
                "a track of paler rock runs up the headland face and stops at the grass",
                "gulls ride the updraft along its face, hanging still, then sliding off sideways",
                "at its foot the water runs deeper and greener and moves in slow bulges",
                "each swell wraps the point and arrives on the beach at a changed angle",
                "the grass on its top leans inland, grown that way",
            ],
            "windy": [
                "the wind splits on the point and the water beyond it runs two ways at once",
                "spray goes right over the headland top in the gusts",
                "the gulls quit the updraft one by one and go low along the beach",
            ],
            "night": [
                "the headland is a black shape against a lesser black; the white at its foot shows where it stands",
                "the point's boom carries up the beach on its own beat, out of time with the surf",
            ],
            "low_tide": [
                "low tide bares a boulder causeway toward the headland — weed-slick, and gone again in six hours",
                "the base shows an undercut you never see at high water",
                "pools at the headland's foot hold anemones the beach pools never get, dark red and fat",
            ],
            "high_tide": [
                "the causeway is under; swell breaks white the whole way along the base",
                "each set sends water up the paler track on the face and back down it",
            ],
            "winter": [
                "winter swell explodes on the point and the spray drifts half the length of the beach",
                "the headland disappears into each squall first and comes out of it last",
            ],
        },
        "rare": [
            "kawau stand on the headland rocks with their wings held wide open, drying, dead still",
            "a kekeno, a fur seal, hauled out on the flat rock at the base — asleep or near it",
            "dolphins round the point, three fins, then more, working an arc offshore",
            "a fishing boat holds close under the headland for an hour, then goes",
        ],
    },

    "dune_grass": {
        "aliases": ("dune grass", "grass", "dunes", "the dunes", "spinifex", "marram", "pīngao", "pingao"),
        "pools": {
            "any": [
                "the marram bends and recovers, bends and recovers, every stem drawing its own circle in the sand",
                "spinifex runners go out across the open sand, rooted down at every span",
                "each grass clump stands on its own small hill of caught sand",
                "the dune edge is cut clean where the last spring tide bit it; roots hang in the scarp",
                "pīngao, orange-gold, holds the steepest face",
                "a beetle's track stitches between two clumps and ends at a small hole",
                "wind-cut sand ripples run right up to the first grass and stop",
                "the sand in among the stems is finer than anywhere else on the beach",
            ],
            "windy": [
                "sand smokes off the dune crest and the grass lies hard over, all one way",
                "a spinifex seed head goes bowling down the beach, all spokes, big as two fists",
                "the scarp sheds a steady trickle of dry sand in every gust",
            ],
            "night": [
                "the grass hisses; you hear the dune before you see it",
                "the dune stands paler than everything around it, holding the last of the light",
            ],
            "bright": [
                "each stem's swept circle shows sharp in the sand",
                "the pīngao goes copper in full sun",
            ],
            "summer": [
                "spinifex seed heads gather in the dune hollows, dozens together, ticking against each other",
                "the open sand between clumps is too hot to stand on barefoot by noon",
            ],
            "winter": [
                "the winter grass is dull and salt-burnt on the seaward face",
                "rain has firmed the dune sand; the rabbit tracks in it hold their shape for days",
            ],
        },
        "rare": [
            "a pipit works the dune edge, tail going, closer than most birds come",
            "kororā tracks — a straight seam of small prints from the water to the dune, and none coming back",
            "a rabbit sits up in the grass, holds a moment too long, and is gone over the crest",
        ],
    },

    "birds": {
        "aliases": ("birds", "gulls", "the gulls", "karoro", "tōrea", "torea", "oystercatchers", "terns", "tara"),
        "pools": {
            "any": [
                "karoro, the big black-backs, stand spaced along the tide's edge, all facing the wind",
                "red-billed gulls squabble over something small; then it's gone, and so is the quarrel",
                "tōrea work the wet sand in pairs, red bills going down and up",
                "white-fronted terns hang over the shallows, tip, and drop; some come up with silver",
                "a kōtare sits dead still on the outermost rock, all head and bill",
                "the gulls all lift at once for no reason you can find, wheel once, and settle again",
                "a tōrea pipes, sharp and doubled, and its mate answers from up the beach",
                "one young karoro, brown and patchy, follows an adult and gets nothing",
            ],
            "night": [
                "a single karoro calls somewhere down the dark beach, twice, and stops",
                "wings pass overhead unseen, one beat, gone seaward",
            ],
            "windy": [
                "the terns give up the hover and slide away downwind, fast and low",
                "gulls stand bill to the wind, feathers lifting along their backs",
                "a red-billed gull tries the air, is put back down twenty paces along, and stays down",
            ],
            "low_tide": [
                "the tōrea follow the tide out, working the fresh wet flats as they drain",
                "shags fish the low channel — up for a breath, under again",
                "every bird on the beach has moved down to the new water line",
            ],
            "high_tide": [
                "the waders crowd the last dry band of shingle, packed close, facing out",
                "the terns fish tight against the swash now, where the small fish have come in",
            ],
            "winter": [
                "winter brings more birds, not fewer; the low-tide flats are all working backs",
                "the gulls sit hunched and rounded, twice their summer size",
            ],
        },
        "rare": [
            "kawau in a line low over the water, wingtips almost touching the swell",
            "a gannet folds and strikes offshore, a white pole of splash standing a moment",
            "a kōtuku — white heron — alone and upright in the stream-mouth shallows",
        ],
    },

    "stones": {
        "aliases": ("stones", "shingle", "pebbles", "gravel", "the stones", "the shingle"),
        "pools": {
            "any": [
                "the shingle sorts itself: big stones up the beach, pea gravel at the water, sand between",
                "each backwash rattles the pebbles down the slope, a long drawn-out clatter",
                "a worn sea-glass nub, green, frosted all over — it sits well in a pocket",
                "a pumice knuckle, grey and light; it floats when you drop it in a pool",
                "one stone in a thousand is banded, and once you see one you keep seeing them",
                "the stones are wet-dark to a line and dry-pale above it, and the line moves with the day",
                "greywacke, most of it, rounded smooth; the odd red one stands out a long way",
                "a stone with a hole worn straight through it",
                "underfoot the dry shingle gives and rolls; the wet sand below it holds firm",
            ],
            "wet": [
                "rain brings every stone's colour up at once",
                "the dry rattle goes out of the beach; footsteps land soft",
            ],
            "night": [
                "the shingle gives your position away with every step",
                "the stones are all one blackness; the pale ones show first as the eyes settle",
                "a wave pulls back and the rattle runs off into the dark both ways",
            ],
            "windy": [
                "sand hisses across the stone tops, ankle-high, going somewhere else",
                "the smallest gravel creeps downwind in fits, a few grains at a time",
            ],
            "low_tide": [
                "low tide bares the boulder band below the clean shingle, weeded and slick",
                "the pea gravel at the water's edge is rinsed and bright, none of it dry",
            ],
            "high_tide": [
                "the swash runs up the shingle, stalls, and drags the small stones back down with it",
                "the steep top berm is all that's left dry, and the sea is working on the base of it",
            ],
            "winter": [
                "a winter storm has rebuilt the whole berm a step higher; last month's beach is gone",
                "frost binds the top stones together until the sun gets to them",
            ],
            "summer": [
                "by late summer the sand has come back and buried half the winter stones",
                "the top stones are warm right through by mid-afternoon",
            ],
        },
        "rare": [
            "an obsidian chip, black glass, its edges still sharp after all that rolling",
            "a perfectly round white quartz stone, the one in ten thousand",
            "a fist of pumice big enough to see the old bubbles in, light as bread crust",
        ],
    },

    "horizon": {
        "aliases": ("horizon", "the horizon", "offshore", "out to sea", "the line"),
        "pools": {
            "any": [
                "the horizon is a clean rule today; a ship would show for hours",
                "the offshore island sits on the line, blue-grey, flattened by the distance",
                "weather stands out at sea in columns; some of it is coming, most of it is not",
                "the sea changes colour in bands out to the line — green, grey-green, then a blue that is nearly grey",
                "gannets work a patch far out; you would miss it but for the white flickering",
                "the swell lines show far out as long shadows, counting themselves in toward the beach",
                "the island's near end drops clean; the far end tails off into the sea in steps",
            ],
            # J-1882 (F-2505): daylight-bound by its own wording, so it keys on "day" (world_detail._conds() emits it for dawn,
            # day and dusk, and "night" instead of it at night). It sat under "any" and could render at night. Wording unchanged.
            "day": [
                "a container ship crosses left to right, hull-down, taking the whole morning about it",
            ],
            "night": [
                "the horizon is gone; sea and sky meet somewhere that will not be fixed",
                "far out, the cloud base carries a faint glow off some town across the water",
                "the island shows only as a missing piece of the lower stars",
            ],
            "bright": [
                "the line runs hard and dark under the light; the island shows detail it never shows",
                "shimmer lifts the horizon and lays a thin second water on top of the first",
            ],
            "windy": [
                "whitecaps run in ranks out to the line",
                "spray-haze eats the horizon; the island goes, then the line itself",
            ],
            "winter": [
                "a squall drags a grey curtain along the horizon, south to north",
                "the winter sea is dark to the line, and the sky sits low on it",
            ],
        },
        "rare": [
            "ship's lights on the line at night — two white, one red — taking half an hour to move a finger's width",
            "the island doubles: a mirage lifts a second island above the first, upside down",
            "a waterspout, thin and bent, hangs off a distant squall and is gone inside a minute",
        ],
    },

    "cliff": {
        "aliases": ("cliff", "the cliff", "cliff face", "strata", "the rock face"),
        "pools": {
            "any": [
                "the cliff shows its layers plainly: hard bands standing proud, soft bands eaten back",
                "one stratum runs tilted through the whole face and out the far end",
                "fresh fall at the base — raw clay-coloured rock lying on old grey rounds",
                "water seeps from a single seam, a dark stripe down the face that never dries",
                "welcome swallows loop in and out under the overhang, never once touching rock",
                "a band of packed shells runs through the cliff at head height, gone as hard as the rock around it",
                "the face is cool to a laid palm on the hottest day",
                "lichen takes the top third of the cliff and stops at a line the salt must draw",
            ],
            "wet": [
                "rain streaks the whole face dark; every seam becomes a small spout",
                "the clay bands go glossy and shed the rain in sheets",
                "the seep widens to a finger's width and you can hear it",
            ],
            "night": [
                "the cliff blanks the stars along its whole top edge",
                "the seep keeps its small sound going in the dark, under the surf",
            ],
            "windy": [
                "grit rains off the cliff top in the gusts; small stones tick down the face",
                "the wind pours over the top and falls dead at the base — the cliff's lee is the stillest place on the beach",
            ],
            "high_tide": [
                "high water works at the cliff toe; each swell slaps into the undercut with a flat boom",
                "spray off the toe wets the face a body-height up and the rock goes black",
            ],
            "low_tide": [
                "low tide opens the walk along the cliff base, past the seep to the fallen slabs",
                "the undercut shows its full depth, dry sand at the back of it that the sea rarely reaches",
            ],
            "winter": [
                "winter is when the cliff moves; every big rain leaves new rock at its foot",
                "the seep grows a beard of green through the wet months",
            ],
        },
        "rare": [
            "a whole fossil shell weathered proud of the face, standing on its own pedestal of stone",
            "a slab has come down since yesterday — the scar shows raw and bright, high up",
            "a kōtare works from a snag on the fallen slabs, dropping on things in the rubble",
        ],
    },

    "stream_mouth": {
        "aliases": ("stream", "the stream", "stream mouth", "creek", "the creek", "fresh water"),
        "pools": {
            "any": [
                "the stream crosses the beach in a braided fan, cutting little cliffs an inch high and abandoning them",
                "fresh water rides over the salt at the mouth — a smoothness on the ripple you can see from up the beach",
                "the stream's stones are different: brown, angular, not the sea's rounded grey",
                "leaves and pine needles come down the current, hang at the mouth, and go to the sea",
                "the water runs tea-coloured out of the hills and clear over the sand an inch deep",
                "small fish hold in the current above the sand, all facing upstream; a shadow scatters them",
                "the fan re-draws itself while you watch — one channel silts, another takes the water",
                "gulls stand in the fresh water and bathe, wings shuddering",
            ],
            "wet": [
                "the stream is up and brown and has cut itself a new channel overnight",
                "after rain the mouth runs loud enough to hear over the surf",
                "the fan is all one sheet of moving water, its braids drowned",
            ],
            "night": [
                "the stream keeps its own sound in the dark, higher and quicker than the sea's",
                "a pale seam of foam marks the mouth; the rest is dark",
            ],
            "low_tide": [
                "at low tide the stream runs the beach's whole width, thinning to a sheet of shine on the sand",
                "the fresh water braids among the sea's leavings — weed, shell, one stranded jellyfish",
                "the mouth cuts a small channel through the new sandbar and hurries there",
            ],
            "high_tide": [
                "the tide pushes into the mouth; the stream backs up, stalls, and pools behind its own bar",
                "salt water wedges upstream under the fresh; the current at the mouth can't decide its direction",
            ],
            "winter": [
                "winter keeps the stream full; the fan is cut deep and the little cliffs stand a hand high",
                "the fresh water comes down cold enough to ache a held hand",
            ],
            "summer": [
                "by late summer the stream barely makes the sea, soaking away into the shingle short of the water",
                "the shrunken channel is warm and slow, and the small fish crowd what is left of it",
            ],
        },
        "rare": [
            "two eels, long shadows, nose at the salt line and go no further",
            "whitebait shiver up the current's edge in a thin silver run",
            "a kōtuku stands in the mouth shallows, stiller than the water",
        ],
    },
}

SCENE = {
    "any": [
        "tōrea work the tideline while the karoro stand higher up, spaced out, facing the sea",
        "kelp heaps mark the last big tide, a dark rope laid the length of the beach",
        "the headland takes a set of three; spray drifts inland over the dune grass",
        "shell drift crackles underfoot between the log and the stream",
        "the cliff seep has drawn one green stripe down through the grey face",
        "the swell drops away down the beach; off the headland it still stands up white",
        "a spinifex head rolls from the dunes clear down to the wet sand and stops there",
        "the stones are wet-dark to one line and pale above it, the whole beach ruled in two",
    ],
    # J-3258 (D-0649, F-3628): three lines that are daylight-bound by their own wording (a gull bathing in the stream mouth, the
    # driftwood log's shadow, terns working the shallows) moved here from "any"; _conds() emits "day" for dawn, day and dusk, never
    # at night. Wording unchanged. The two "low_tide" lines with the same fault could not take a bare "day" key (it would drop their tide
    # gate); J-3484 gives them the composite key "day+low_tide" below (core/world_detail._cond_ok: every part must hold).
    "day": [
        "the stream mouth flashes where it crosses the sand; a gull is bathing in the fresh water",
        "the driftwood log throws the beach's only shadow",
        "terns hang over the shallows off the stream mouth, where the small fish are",
    ],
    "night": [
        "surf, stream, shingle — three sounds, and the wind moving between them",
        "the cliff and the headland stand as two blacks; the beach runs pale between them",
        "one karoro calls from the direction of the log",
        "the tideline is findable by smell — kelp and iodine on the cold air",
        "the only white anywhere is at the headland's foot, arriving and arriving",
    ],
    "windy": [
        "the beach is on the move — sand streaming, weed tumbling, gulls hanging on the cliff updraft",
        "spray goes over the headland; the dune grass lies flat and shivers back up between gusts",
        "everything loose on the beach has fetched up against the driftwood log",
        "the tōrea have quit the open sand for the lee of the boulder band",
        "sand hisses past ankle-high from the dunes to the water and out onto it",
    ],
    # J-3484 (D-0649 follow-up, J-3355; founder 2026-11-06): the two low_tide lines that are also daylight-bound (night-wrong in
    # F-3628: 4 and 3 night renders). Wording byte-identical; they keep the tide gate AND gain the day gate. Present only when the tide
    # leans low (low / rising) AND it is dawn, day or dusk.
    "day+low_tide": [
        "wet flats shine from the stream mouth to the headland; every bird on the beach is working them",
        "fresh shell glitters along the new tideline the sea has just left",
    ],
    "low_tide": [
        "the low tide gives up the whole boulder causeway and the shags move in",
        "the kelp beds lie down offshore; the rock pools sit open to the sky",
        "the stream runs thin and wide across sand the sea only just gave back",
    ],
}

EVENTS = [
    ("any", "a set of larger swells arrives out of nothing; the beach's whole sound changes for a minute, then goes back"),
    ("any", "the karoro all lift at once, wheel once above the beach, and put back down almost where they were"),
    ("any", "a wave runs up further than the last twenty and re-draws the tideline at your feet"),
    ("day", "a tern folds and hits the water off the stream mouth; it is up again before the splash settles"),
    ("day", "a cloud shadow crosses the whole beach in under a minute, the stones going grey and then bright again"),
    ("night", "something out on the water blows a breath — once, clearly — and is not heard again"),
    ("night", "a stone comes off the cliff, ticks twice on the face, and lands soft in the sand"),
    ("windy", "a gust flattens the stream fan sideways and freckles the near pools with sand"),
    ("windy", "a whole dried kelp strap goes past at head height, end over end"),
    ("wet", "the rain reaches the beach as a visible line coming over the water, and everything sounds different behind it"),
    ("wet", "the rain flattens the shingle's colour to one grey, and the sea keeps working under it regardless"),
    ("low_tide", "the sea pulls back off a new sandbar and the tōrea are on it before it has fully drained"),
    ("low_tide", "a channel you've never seen shows itself in the wet sand, and is gone again within the hour"),
    ("high_tide", "a swell slaps into the cliff undercut with a flat boom and the spray comes back out of the shadow"),
    ("high_tide", "the last dry line of shingle disappears under a run of water and doesn't come back this pass"),
    ("winter", "hail comes through fast and whitens the tideline; five minutes later only the kelp heaps still hold it"),
    ("winter", "the cold off the water gets into your hands before you've noticed you've stopped to look at anything"),
    ("bright", "the light finds a pāua chip far up the beach and it burns blue-green until you move your head"),
    ("bright", "the water goes hard and bright all the way to the horizon, too much to look at straight on"),
]
