# world_content_garden.py — garden lookables, ambient scene lines, and events.
# Voice: concrete, present tense, indifferent. One line each, <=150 chars.

LOCATION = "garden"

TARGETS = {
    "lawn": {
        "aliases": ("lawn", "the lawn", "grass", "the grass"),
        "pools": {
            "any": [
                "the lawn runs downhill and stops at the fence, and past the fence the sea takes over",
                "the grass is longer at the bottom where the mower turns",
                "a blackbird's tug leaves a small torn patch in the turf",
                "the shade side of the lawn stays damp long after the rest has dried",
                "worm casts stand in small coils across the low corner",
                "the clover keeps to the dry patch near the path",
                "a flat stone shows through where the grass never quite takes",
                "the ground gives a little underfoot at the bottom of the slope",
            ],
            "night": [
                "the hedgehog crosses the lawn at its own speed, stopping to work at something in the grass",
                "the lawn holds a grey sheen under the half moon",
                "your steps leave dark prints in the dew and the prints close slowly behind you",
            ],
            "wet": [
                "the low corner ponds and the water sits, going nowhere",
                "rain flattens the long grass at the fence all in one direction",
                "worms lie out on the surface after the rain, pale and stranded",
            ],
            "bright": [
                "the mown stripes still show from last time, one shade apart",
                "the lawn is two greens in the full sun, dry rise and damp hollow",
                "the tī kōuka's shadow lies across the grass and moves with the hours",
            ],
            "winter": [
                "the lawn stays wet all day now; the sun never gets over the hedge far enough",
                "moss is taking the shaded strip and the grass is letting it",
            ],
            "summer": [
                "the grass browns off on the dry rise first, in the exact shape of last year's brown",
                "cicadas start up in the grass before the day is properly hot",
            ],
        },
        "rare": [
            "a field mushroom stands in the middle of the lawn, white and full-grown, overnight",
            "the hedgehog is out in daylight, going somewhere along the fence without stopping",
            "a pūkeko walks up from the low ground, jerking its tail at every step, and works the wet corner",
        ],
    },

    "fence": {
        "aliases": ("fence", "fence line", "the fence", "gate", "the gate"),
        "pools": {
            "any": [
                "the fence leans out where the ground has slipped a little, and stays there",
                "lichen crusts the top rail, grey-green and dry to the touch",
                "the gate swings shut on its own weight and clacks against the post",
                "one wire runs slack between two posts and the others are tight",
                "the bottom rail is soft with rot on the sea side",
                "grass grows tall along the fence where the mower can't reach",
                "the gate latch is bright metal where hands go and dull everywhere else",
                "past the fence the ground drops away and there is only air and then water",
            ],
            "night": [
                "the fence posts stand darker than the dark behind them",
                "the gate clacks once in the night and then nothing",
                "from the fence at night the sea is all sound and no edge",
            ],
            "wet": [
                "rain darkens the posts from the top down",
                "drops line the bottom wire, evenly spaced, each holding a bend of grey light",
                "the gate is heavier to swing in the wet and the hinge says so",
            ],
            "windy": [
                "the loose wire hums one note that changes as the gusts change",
                "the gate strains against the latch and knocks in its frame",
                "grass along the fence lies flat, all pointing inland",
            ],
        },
        "rare": [
            "a shed cicada shell grips the fence post, split down the back, hollow",
            "a wētā backs into the gap under the top rail, all legs and spines",
            "a white-faced heron picks its way along outside the fence at dusk, lifting each foot clear",
        ],
    },

    "compost": {
        "aliases": ("compost", "compost heap", "the compost", "the heap"),
        "pools": {
            "any": [
                "the heap sags on one side where the last load went on",
                "eggshells show pale through the dark of the heap",
                "a fork stands upright in the compost, left where it was last used",
                "the smell is wet and brown and only strong when the heap is turned",
                "small flies rise in a column when anything touches the top layer",
                "the bottom of the heap has gone black and fine, nothing left of what it was",
                "grass clippings sit in a pale layer, still holding the catcher's shape",
                "the boards holding the heap have bowed outward and hold anyway",
            ],
            "night": [
                "something rustles inside the heap and stops when you stop",
                "the hedgehog noses along the base of the compost boards",
                "the heap gives a faint warmth to a hand held over it in the dark",
            ],
            "wet": [
                "rain sinks straight into the heap and never pools",
                "the heap darkens in the rain a shade at a time",
                "worms come up under the wet sacking, knotted together, fat and red",
            ],
            "winter": [
                "the heap steams in the cold morning air where the fork went in yesterday",
                "frost on the grass everywhere except a thawed ring around the heap",
            ],
            "summer": [
                "a pumpkin seedling volunteers out of the flank of the heap, two leaves already wide",
                "the flies on the heap are quick and green in the heat",
            ],
        },
        "rare": [
            "a skink flows off the warm compost boards into the grass in one motion",
            "turning the heap uncovers a knot of pink worms and one beetle the size of a thumbnail",
            "a rat's tunnel opens into the base of the heap, smooth-walled, in use",
        ],
    },

    "bench": {
        "aliases": ("bench", "the bench", "seat", "the seat"),
        "pools": {
            "any": [
                "the bench faces the sea because that is how it was put down",
                "the seat boards are silvered and split along the grain",
                "one leg sits on a flat stone to keep the bench level on the slope",
                "the wood is warm or cold exactly as the day is",
                "a knot in the second board has fallen through and left a clean hole",
                "lichen makes small grey circles along the armrest",
                "the grass under the bench grows thin and long, unreached by the mower",
                "salt has dulled the last of whatever paint the bench had",
            ],
            "night": [
                "the bench is wet with dew before the dark has fully come down",
                "from the bench at night the sea is a sound and a darker band, nothing more",
                "the moon lays its path on the water and the bench faces straight down it",
            ],
            "wet": [
                "rain stands in the grain of the seat in thin lines",
                "the bench drips from its front edge onto the flattened grass",
                "the wood goes almost black in the rain and the grain stands out",
            ],
            "bright": [
                "the seat is too hot to sit on by mid-afternoon",
                "the bench throws a hard clean shadow onto the grass",
                "from the bench you can watch the swell arrive in sets, three big, then a long pause",
            ],
        },
        "rare": [
            "a skink suns itself on the far arm of the bench, throat pulsing",
            "an old mug-ring marks the armrest and no weather has shifted it",
            "a pīwakawaka lands on the back of the bench an arm's length away and looks at you sideways",
        ],
    },

    "rain_barrel": {
        "aliases": ("barrel", "rain barrel", "the barrel", "water barrel"),
        "pools": {
            "any": [
                "the rain barrel stands at the corner of the house, catching what the roof sends down",
                "the water in the barrel is dark and still and shows the sky when you look in",
                "a fine green film rings the waterline inside the barrel",
                "the downpipe elbow into the barrel is furred with old moss",
                "the tap at the base drips once a minute, no more, no less",
                "mosquito larvae hang under the surface and jackknife down when your shadow crosses",
                "the overflow hole is rimmed with rust stain down the barrel's side",
                "the barrel sounds different when you knock it, high at the top, dead low down",
            ],
            "wet": [
                "the downpipe runs loud into the barrel and the surface churns",
                "the barrel fills to the overflow and a thin stream finds the grass",
                "rain rings the surface faster than the rings can clear",
                "the overflow starts, and its sound joins the rain's",
            ],
            "night": [
                "the barrel holds one star on its surface until the wind takes it",
                "something drinks at the barrel's base after dark and is gone when the light comes on",
                "the drip from the tap keeps its slow count in the dark",
            ],
            "bright": [
                "the waterline shows as a cool band on the barrel's sunny side",
                "light off the water in the barrel wobbles on the underside of the eave",
                "the water level is down a hand's width from last week",
            ],
        },
        "rare": [
            "a drowned huhu beetle turns slowly in the middle of the barrel",
            "a tauhou dips at the barrel rim, drinks twice, and is gone",
            "the barrel is empty enough to boom, and the tap gives one cupful and stops",
        ],
    },

    "harakeke": {
        "aliases": ("harakeke", "flax", "the flax", "flax clump", "the harakeke"),
        "pools": {
            "any": [
                "the harakeke fans out in stiff blades at the bottom corner of the lawn",
                "the dead outer blades of the flax hang down, pale and split into ribbons",
                "the harakeke's old flower stalks stand black and bare above the leaves",
                "each flax blade carries a fine dry edge that rasps when you draw a finger along it",
                "the base of the flax is a dense dark thicket the mower gives a wide margin",
                "a snail-track dries in a glaze down one broad blade",
                "the flax holds the fence corner in permanent shade",
                "rain from two days ago is still pooled deep between the flax fans",
            ],
            "windy": [
                "the harakeke clatters, every blade moving a different way",
                "the wind gets a low creak out of the flax's old flower stalks",
                "the flax leans hard, springs back, leans again, all afternoon",
                "torn ribbon-ends of flax stream out level in the gusts",
            ],
            "winter": [
                "the flax stands at full size while the rest of the garden has drawn in",
                "tauhou work through the flax fans, small sounds, hardly a blade moving",
                "winter rain runs the flax blades in bright lines to the ground",
            ],
            "summer": [
                "the flax sends up new flower stalks, fat and green, taller by the week",
                "tūī come down to the flax flowers and leave with yellow-dusted heads",
            ],
        },
        "rare": [
            "one flax blade shows an old clean cut low down, healed grey along the edge",
            "a green gecko lies along a flax blade, matching it, only the eye separate",
            "a nest of dried grass sits wedged deep in the flax base, cold, last year's",
        ],
    },

    "kowhai": {
        "aliases": ("kōwhai", "kowhai", "the kōwhai", "kōwhai tree", "the tree"),
        "pools": {
            "any": [
                "kōwhai seed pods hang in strings, knuckled and dry, rattling only when touched",
                "the kōwhai's bark is grooved and grey, warm-toned even on dull days",
                "hard yellow kōwhai seeds lie in the grass beneath, whole after years",
                "the kōwhai's shade is thin; grass grows right up to the trunk",
                "a low kōwhai branch dips and rises whenever anything lands or leaves",
                "small paired leaflets lie scattered on the ground under the kōwhai",
                "lichen takes the south side of the kōwhai's trunk and stops there",
            ],
            # J-1882 (F-2505): daylight-bound by its own wording, so it keys on "day" (world_detail._conds() emits it for dawn,
            # day and dusk, and "night" instead of it at night). It sat under "any" and could render at night. Wording unchanged.
            "day": [
                "the kōwhai stands mid-slope, small-leaved, letting light through in flecks",
            ],
            "winter": [
                "the kōwhai is thinning its leaves before flowering, going sparse at the tips",
                "the first kōwhai buds show at the branch ends, green and shut",
                "by late winter the first yellow shows in the kōwhai and a tūī has already found it",
            ],
            "spring": [
                "the kōwhai is fully out, hung with yellow, and the tūī traffic is constant",
                "spent kōwhai flowers lie in a yellow ring on the grass below",
                "the kōwhai drips nectar and the tūī work it branch by branch",
                "a kererū sits in the kōwhai eating the new leaves whole",
            ],
            "windy": [
                "the kōwhai's fine branches stream and cross and never quite tangle",
                "wind strips the loose kōwhai flowers and rolls them across the lawn",
                "the seed pods clatter drily in the gusts",
            ],
        },
        "rare": [
            "a kōwhai seedling stands in the lawn a mower-width from the trunk, two leaves old",
            "a case moth's bag hangs from a kōwhai twig, shingled with its own small sticks",
            "the kōwhai holds a tūī, a korimako, and a riroriro at once, each at a different height",
        ],
    },

    "ti_kouka": {
        "aliases": ("tī kōuka", "ti kouka", "cabbage tree", "the cabbage tree", "the tī kōuka"),
        "pools": {
            "any": [
                "the tī kōuka stands above the fence line on one bare trunk, heads of blades at the top",
                "dead tī kōuka leaves skirt the trunk, dry and downward, rustling at a touch",
                "fallen cabbage tree leaves lie on the lawn, tough and stringy, and the mower leaves them",
                "the trunk of the tī kōuka is corky and criss-crossed and takes a fingernail without marking",
                "the tī kōuka's shadow is a thin pole with a burst at the top of it",
                "the head of the cabbage tree moves before anything else in the garden does",
                "the kōtare sometimes swaps the powerline for the tī kōuka's highest spike",
                "dead tī kōuka leaves collect in the fence angle and stay all year",
            ],
            "windy": [
                "the tī kōuka rattles all its blades at once, the loudest thing in the garden",
                "the whole head of the cabbage tree streams to leeward and the trunk barely moves",
                "in the gusts the tī kōuka gives a hard dry hiss",
                "one dead leaf lets go of the tī kōuka, planes across the lawn, and lands still",
            ],
            "night": [
                "the tī kōuka stands black on the last light, blades printed on the sky",
                "the moon puts the cabbage tree's shadow across half the lawn",
                "the rattle of the tī kōuka carries after dark when nothing else does",
            ],
            "summer": [
                "the tī kōuka's flower heads have gone over to white berries and the birds have found them",
                "cicadas keep to the tī kōuka's trunk, breaking off when a shadow crosses",
            ],
        },
        "rare": [
            "a second head is starting low on the tī kōuka's trunk where the old damage was",
            "the tī kōuka is in full flower, one huge cream spray, and the bees have taken it over",
            "starlings prospect the head of the cabbage tree for a nest site, arguing the whole time",
        ],
    },

    "birds": {
        "aliases": ("birds", "the birds", "bird", "birdlife"),
        "pools": {
            "any": [
                "a blackbird works the lawn edge, head cocked, then stabs and comes up with something thin and fighting",
                "the pīwakawaka loops around your head and snatches whatever your feet have stirred",
                "a riroriro sings somewhere in the hedge, the song climbing and falling away unfinished",
                "the kōtare sits on the powerline, dead still, watching the grass",
                "two sparrows argue in the hedge and one leaves fast",
                "a starling probes the lawn, opening its beak in the ground to prise the turf apart",
                "a gull crosses high over, saying nothing, heading down the coast",
                "the blackbird stops mid-run and stands one-legged, listening at the ground",
                "a song thrush hammers a snail on the path stone and eats what falls out",
                "the kōtare drops off the wire, hits the lawn, and is back on the wire with something in its bill",
                "a magpie walks the fence top rail with slow deliberate steps",
                "the pīwakawaka never sits longer than a breath; the tail fans and the branch is already empty",
            ],
            "night": [
                "a ruru calls from the gully, two notes, and waits a long time before the next",
                "something small shifts in the hedge and the dark holds its shape",
                "the ruru calls once more, farther off now",
            ],
            "bright": [
                "the kōtare's back flares blue-green when it turns on the wire",
                "a sparrow dust-bathes in the dry patch by the fence, shivering the ground up over itself",
                "a tūī crosses the sun-gap with that heavy whirring flight",
            ],
            "wet": [
                "the blackbird feeds on through the rain, drops beading its back",
                "sparrows sit fluffed and dark under the hedge, waiting the shower out",
                "a thrush sings from the top of the tī kōuka into the drizzle",
            ],
            "windy": [
                "the gulls hang over the fence line, riding the updraft without a wingbeat",
                "small birds keep low, hedge to hedge, nothing crossing open ground",
                "the kōtare grips the jumping wire and rides it out",
            ],
            "winter": [
                "tauhou come through in a loose flock, stripping the hedge of something too small to see",
                "a tūī works the camellia next door, upside down half the time",
                "four blackbirds space themselves across the winter lawn, each working its own strip",
                "the silvereyes pass through twice a day now, hedge to flax to gone",
            ],
            "spring": [
                "a tūī bosses the kōwhai, chasing off two others between mouthfuls",
                "the blackbird sings from the chimney at first light and doesn't stop for an hour",
                "a riroriro nest hangs in the hedge, a grey pouch with a side door",
            ],
            "summer": [
                "young sparrows beg along the fence, wings shivering, mouths wide",
                "the kōtare takes cicadas off the air now, one clatter at a time",
                "a pīpīwharauroa calls from somewhere high and the riroriro in the hedge goes quiet",
            ],
            "autumn": [
                "the starlings gather on the powerline in the evenings, more each week",
                "a thrush strips the hedge berries and is gone before you get close",
            ],
        },
        "rare": [
            "a kererū lands in the kōwhai and the whole branch dips under it",
            "a kāhu circles high over the slope behind, and every small bird goes quiet at once",
            "the kōtare misses, hits the grass, and sits a moment in the open looking exactly nowhere",
            "a white-faced heron crosses the garden at head height, slow wingbeats, legs trailing",
            "two tūī fight over nothing visible, all clatter and wing-noise, up over the roof and gone",
        ],
    },

    "hedge": {
        "aliases": ("hedge", "the hedge", "shrubs", "the shrubs", "bushes"),
        "pools": {
            "any": [
                "the hedge holds its trimmed shape loosely now, new growth standing off the top",
                "the hedge is one solid dark bulk with small deep entrances low down",
                "spider lines run between hedge tips and the light finds them and loses them",
                "the leeward side of the hedge carries more leaves than the sea side",
                "the hedge takes the edge off the wind for everything below fence height",
                "small dry twigs lie stacked inside the hedge where nothing has disturbed them",
                "the hedge's shade keeps a strip of bare earth along its base",
                "one branch in the hedge has died and stands paler than the rest",
            ],
            "night": [
                "the hedge at night is one black wall with small movements inside it",
                "the hedgehog works along the hedge base, snuffling, unhurried",
                "moths lift from the hedge as the dark settles",
            ],
            "wet": [
                "the hedge drips long after the rain has stopped",
                "the hedge goes glossy in the rain, every leaf beading and shedding",
                "sparrows deep inside the hedge stay dry, chirping through the shower",
            ],
            "winter": [
                "tauhou flocks strip along the hedge in winter, in one side and out the other",
                "the hedge keeps its green while the lawn goes to moss and mud",
            ],
        },
        "rare": [
            "a thrush's old nest shows in the hedge now the growth has thinned, the mud cup cracked",
            "a stick insect stands on a hedge twig, being a twig until it moves",
            "the hedge has swallowed a fence batten; the wood shows deep inside, grown around",
        ],
    },
}

SCENE = {
    "any": [
        "the lawn runs down to the fence and the sea lies flat and pale beyond it",
        "wind off the sea combs up the slope and the tī kōuka moves first",
        "the gate stands shut and the grass along the fence line barely moves",
        "the swell breaks somewhere out of sight and arrives as sound a moment later",
        "smell of cut grass near the compost, salt over everything else",
        "the harakeke, the bench, the barrel — everything holds still except the sea",
    ],
    # J-1882 (F-2505): daylight-bound by its own wording (cloud shadow needs sun), so it keys on "day" (_conds() emits it for
    # dawn, day and dusk, never at night). It sat under "any" and could render at night. Wording unchanged.
    # J-3258 (D-0649, F-3628): three more daylight-bound lines (the kingfisher on the powerline, the blackbird crossing the lawn, the
    # fantail that finds you) moved here from "any" for the same reason; the live ledger showed them in 15 of 74 garden night renders.
    # Wording unchanged. Order within this list follows their old order in "any".
    "day": [
        "cloud shadow crosses the lawn, takes the bench, and slides over the fence and out to sea",
        "the kōtare is on the powerline again, facing the grass",
        "a blackbird crosses the lawn low, from hedge to compost, without stopping",
        "a pīwakawaka finds you the moment you step off the path",
    ],
    "night": [
        "a ruru calls from the gully and nothing in the garden moves",
        "the sea is louder than anything the garden has after dark",
        "dew is already down; the bench and the gate latch are wet to the touch",
        "the hedgehog is out, crossing between the hedge and the compost on its rounds",
        "the tī kōuka stands against the stars, blades quite still",
    ],
    "wet": [
        "rain comes in off the sea in a grey wall you can watch arriving",
        "the downpipe runs, the barrel fills, the lawn takes the rest",
        "everything drips at its own rate — the hedge fast, the bench slow, the flax in single beads",
        "the fence posts have gone dark and the sea and sky are one colour",
        "a thrush sings through the rain from the top of the tī kōuka",
    ],
    "bright": [
        "the sun finds a gap and lays hard shadows behind the bench and the barrel",
        "the sea glitters to the horizon and the lawn is warm underfoot",
        "every spider line in the hedge shows in the low bright light",
        "light off the sea reaches the underside of the kōwhai's leaves",
        "the sea lies out flat and silver and the fence line stands black against it",
    ],
}

EVENTS = [
    ("any", "the kōtare drops from the powerline, takes something from the grass, and is back before the wire stops moving"),
    ("any", "a pīwakawaka loops in from nowhere and snatches an insect a hand-span from your face"),
    ("any", "the riroriro starts up in the hedge, runs its song twice, and stops mid-phrase"),
    ("night", "the ruru calls twice from the gully, then once, much closer"),
    ("night", "the hedgehog comes out from under the flax, freezes at your footfall, and goes on"),
    ("wet", "a squall crosses the water below, a grey column dragging its own shadow, and misses the garden entirely"),
    ("wet", "the rain finds the flax and runs off it in a single sheet, straight down, missing the bed"),
    ("windy", "a gust takes the tī kōuka's head and three dead leaves go planing over the fence, gone"),
    ("windy", "the gate slams, once, hard, and the sparrows leave the hedge in a single burst"),
    ("bright", "the sun clears the hedge and the dew smokes off the lawn in ten minutes flat"),
    ("bright", "the light comes up hard and sudden over the fence and every leaf throws its own shadow"),
    ("winter", "a tauhou flock arrives in the hedge all at once, works it end to end, and leaves the way it came"),
    ("winter", "a tūī lands in the kōwhai's first flowers and the branch tips under it"),
    ("spring", "two tūī fight through the kōwhai, out over the lawn, and back, clattering the whole way"),
    ("spring", "the first bumblebee of the year works the bed twice over before you've noticed it's there"),
    ("summer", "a cicada starts up on the fence post, deafening at arm's length, and cuts out when your shadow touches the wood"),
    ("summer", "the heat brings the bees out in numbers and the whole bed hums with them"),
    ("autumn", "the starlings lift off the powerline in one motion and the wire swings empty"),
    ("autumn", "a leaf lets go somewhere above you and turns the whole way down before it lands"),
]
