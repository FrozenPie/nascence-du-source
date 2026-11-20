"""
Nascence — THE SHORE BESTIARY, P1 PILOT (2026-11-01; docs/staged/shore_creatures.md; founder rulings of that day:
ONE ROW PER SPECIES, every creature has a real POSITION in the shore's authored geometry, and Du is NEVER TOLD what a
thing is — he works it out from what he can see: colour, composition, size, shape, how it moves. The world never leads).

WHAT THIS MODULE IS. A builder for life rows (core.life.row is the one schema, D-0128) whose look is COMPOSED from an
observable tuple instead of hand-typed prose, plus a zone map that gives each row a place in data/world_geometry/shore.json
and a detail model that says how much of it he can make out from where he stands.

  OBSERVABLE TUPLE  obs = {size_cm, span_cm, shape, colour, colour2, pattern, sheen, covering, counts, motion, position,
                     on_disturb}, every word from the closed vocabularies below (a word that is not in them raises).
                     Size is said against his own body, never as a number. The composer is the ONLY thing that writes a
                     creature's look, so no hand-typed sentence can carry a name.
  HIDDEN TRUTH      species / book_names / book_words feed the EXISTING learning ledger only (D-0129: a name needs a book
                     AND a face). aliases are EMPTY, there is NO `reveal` caption, nothing the world says contains a name.
  ZONES             spot -> {anchor feature in shore.json, radius, tide gate, ...}. The stream mouth is a feature of the geometry since
                     D-0651 (J-3260; scripts/apply_shore_stream_mouth_j3260.py adds it, additive-only): a disc on `stream_mouth`.
  DETAIL            detail_tier(span_cm, dist_m): none | form | colour | detail — grade-school trig on apparent size
                     (span / distance), no physics. A sea lion shows colour out to ~50 m, a pipi only within ~1.5 m.
  LEAK TEST         forbidden_terms()/leak_scan()/emitted_strings(): nothing a row can emit may contain its species, any
                     book name, or ANY common name or category word of the 100 (fish, crab, bird, starfish ...). A guess word
                     is Du's to say, never the world's.

P1 = SHADOW ONLY, and shadower than that: the rows are NOT registered into the live engine unless data/life_flags.json has
"shore_bestiary": true (read once, at life._ensure_builtin; default OFF, so life.py is byte-identical in behaviour to before).
P1 also does not hook look_answer: with empty aliases a look cannot reach these rows yet — the description matcher and the
per-look detail tier are the two engine touches of P2. Everything here is pure (no I/O, no LLM, no state).
"""
from __future__ import annotations

import math
import random
import re
import time
import unicodedata

from core import spatial, world_clock
from core.life import row

# ── closed vocabularies ──────────────────────────────────────────────────────────────────────────────────────

# size, said against his own body; (upper bound in cm, exclusive) -> phrase
SIZE_BANDS = (
    (1.0, "a speck, smaller than a fingernail"),
    (2.5, "about the size of a thumbnail"),
    (5.0, "no longer than a thumb"),
    (10.0, "about the width of a palm"),
    (20.0, "about the length of a hand"),
    (40.0, "about the length of a forearm"),
    (90.0, "about as long as a leg"),
    (200.0, "about as long as you are"),
    (500.0, "longer than you are"),
    (1e12, "enormous beside you"),
)

# colour -> (phrase, tone). Tone is all that survives at the `form` tier and at night.
COLOURS = {
    "white": ("white", "pale"), "cream": ("cream", "pale"), "pale_grey": ("pale grey", "pale"),
    "grey": ("grey", "mid"), "dark_grey": ("dark grey", "dark"), "black": ("black", "dark"),
    "dark_brown": ("dark brown", "dark"), "brown": ("brown", "mid"), "olive_brown": ("olive-brown", "dark"),
    "tan": ("tan", "mid"), "tawny": ("tawny gold", "mid"), "buff": ("buff", "pale"),
    "orange": ("orange", "mid"), "orange_brown": ("dull orange-brown", "mid"), "red": ("red", "mid"),
    "dark_red": ("dark red", "dark"), "pink": ("pink", "pale"), "purple": ("purple", "dark"),
    "violet": ("violet", "mid"), "blue": ("blue", "mid"), "blue_green": ("blue-green", "mid"),
    "green": ("green", "mid"), "olive_green": ("olive green", "dark"), "yellow": ("yellow", "pale"),
    "clear": ("clear as glass", "pale"), "silver": ("silver", "pale"),
}
# what a creature is seen AGAINST, where that is not the ground (a tone is only a tone against something)
BACKGROUND = {"in_air": "the sky", "high_in_the_canopy": "the leaves", "afloat": "the water", "in_water": "the water", "in_stream": "the water",
              **{'on_bark': 'the bark', 'on_trunk': 'the bark', 'on_leaf': 'the leaf', 'on_flower': 'the flower', 'on_water': 'the water', 'hanging': 'the sky', 'in_foliage': 'the leaves', 'in_web': 'the web', 'in_tree_hole': 'the dark'}}
TONE_WORDS = {"pale": "pale against the ground", "mid": "mid-toned against the ground", "dark": "dark against the ground"}

# pattern -> template over the two colours (detail tier); the colour tier says "{c1} and {c2}" for any non-plain pattern
PATTERNS = {
    "plain": "{c1}, with no marking", "mottled": "{c1}, mottled with {c2}", "banded": "{c1}, banded in {c2}",
    "spotted": "{c1}, spotted with {c2}", "rayed": "{c1}, with {c2} rays running out from one point",
    "streaked": "{c1}, streaked with {c2}", "marbled": "{c1}, marbled with {c2}", "two_tone": "{c1} above and {c2} below",
    "edged": "{c1}, edged in {c2}", "accented": "{c1}, with {c2} only at the extremities",
}

SHEENS = {
    "matt": "matt", "wet_gloss": "glistening wet", "iridescent": "with a shifting sheen", "pearly": "with a pearly lustre",
    "chalky": "chalky", "glassy": "glassy and clear", "dry_dull": "dry and dull", "glossy": "glossy",
    "furred_sleek": "the coat flattened and sleek where it is wet",
}

COVERINGS = {
    "smooth": "the surface is smooth", "ridged": "fine ridges run around it, following its edge",
    "spined": "it is set with small pale spines in rows", "plated": "its surface is built of overlapping plates",
    "warty": "its skin is knobbled", "rough": "its surface is rough and pitted", "furred": "it is covered in short coarse fur",
    "scaled": "it is covered in small overlapping scales", "leathery": "its skin is tough and leathery",
    "slimy": "its skin is slick with slime", "soft": "its skin is soft and thin",
    "hairy": "its body and legs are covered in fine hairs", "feathered": "it is covered in close feathers",
    "bristled": "its body bears stiff bristles",
    "grainy": "its surface is made of fine, loose grains",
}

# body plans; (full phrase for the `detail` tier, brief phrase for `form` and `colour`). No word here may be a name.
SHAPES = {
    "radial_five": ("five arms of equal length spreading from a small round centre, flat to the surface",
                    "a flat body with arms radiating from a centre"),
    "radial_many": ("a small round centre with a ring of arms of unequal length spreading from it, some long, some short and stubby",
                    "a flat body with arms of unequal length radiating from a centre"),
    "hinged_pair": ("two matching halves, shut, hinged along one edge, the outline a rounded triangle", "a pair of matched, shut halves"),
    "spiral_cone": ("a hard cone wound round and round in a spiral, an opening at the wide end", "a small wound cone"),
    "clamped_cone": ("a low hard cone clamped to the rock, round at its base", "a low cone on the rock"),
    "plated_oval": ("an oval body armoured with a row of overlapping plates down its back, a soft rim around it", "an oval, plated back"),
    "carapace_legs": ("a flat hard back, wider than long, legs jointed and folded along each side, a pair of pincers held forward",
                      "a hard flat back on jointed legs"),
    "jointed_curve": ("a curved, jointed body with a fan at the rear, long feelers and many small legs underneath",
                      "a small curved jointed body with long feelers"),
    "soft_worm": ("a soft, limbless, segmented body, thread-thin to finger-thick", "a soft, limbless thread of a body"),
    "serpent_long": ("a long, muscular body with no limbs and a single fin running along its back", "a long limbless body"),
    "fusiform": ("a tapered body with fins and a flicking tail", "a tapered body with a flicking tail"),
    "flat_wing": ("a wide flat body with winglike sides and a long thin tail", "a wide flat body trailing a thin tail"),
    "flat_oval": ("a flat oval body lying on one side, both eyes on the upper face", "a flat oval body"),
    "bell_trailing": ("a clear dome that pulses, with threads trailing beneath", "a clear dome with threads below"),
    "soft_sac_arms": ("a soft rounded body with eight long arms lined with suckers", "a soft body with long trailing arms"),
    "pinniped_bulk": ("a heavy body, thick through the neck and shoulders and tapering toward the rear, four paddle-shaped limbs, a broad blunt head",
                      "a heavy tapering bulk with a blunt head"),
    "long_back": ("a long smooth back that rolls into view and under, a small fin set far along it", "a long smooth back breaking the water"),
    "six_legged": ("a small hard body in three parts with six legs and a pair of feelers", "a small hard-bodied thing on six legs"),
    "eight_legged": ("a body in two parts with eight legs", "a small body on eight legs"),
    "column_fingers": ("a soft squat column with a ring of short fingers around a central mouth", "a soft column ringed with fingers"),
    "cone_plates": ("a hard cone built of interlocking plates, a small door at the top", "a small hard cone of plates"),
    "sausage_soft": ("a thick soft sausage of a body, leathery, a mouth ringed with short branches at one end", "a thick, soft sausage of a body"),
    "slug_soft": ("a soft, shell-less body, a pair of frilled horns on the head", "a soft, shell-less body"),
    "sphere_spines": ("a rounded, hard body bristling with spines", "a rounded, spiny body"),
    "disc_flat": ("a flat, round, hard disc with a pattern pressed into its upper face", "a flat round disc"),
    "small_furred": ("a small furred body on four legs with a long thin tail", "a small furred four-legged body"),
    # ── the rest of the shore cast (2026-11-01) ──
    "six_legged_pincers": ("a long flat jointed body with a pair of curved pincers at the tail, six legs and a pair of feelers", "a long flat jointed body with pincers at the tail"),
    "winged_small": ("a tiny humped body with two clear wings, six legs", "a tiny winged speck"),
    "winged_slender": ("a slender body on very long thin legs, two narrow wings, a fine needle of a mouth", "a slender winged body on long thin legs"),
    "winged_broad": ("four broad wings, held flat or folded upright, a thin body between them, two feelers tipped with small clubs", "four broad wings on a thin body"),
    "jumper_long_legs": ("a humped body on six very long spined legs, two feelers each longer than the body", "a humped body on very long legs, with feelers longer than itself"),
    "waisted_winged": ("a narrow waist, two pairs of folded wings, long dangling legs and a pair of feelers", "a narrow-waisted winged body with long dangling legs"),
    "lizard_form": ("a slender body on four short limbs, a long tapering tail, a small pointed head", "a slender body on four short limbs with a long tail"),
    "spined_four_legged": ("a rounded body bristling with short spines, a small pointed face, four short legs", "a rounded, spiny body on short legs"),
    "long_low_furred": ("a long, low, narrow furred body on short legs, a long dark-tipped tail, a small flat head", "a long, low, narrow furred body"),
    "wader_small": ("a small upright body on thin legs, a short straight bill, a round head, covered in close feathers", "a small upright body on thin legs"),
    "wader_tall": ("a tall white body on long dark legs, a long flat bill that widens to a round tip, a thin neck", "a tall body on long legs with a long flat bill"),
    "wings_vast": ("an enormous pair of long narrow wings held out stiff, a heavy hooked bill", "an enormous pair of narrow wings"),
    "wings_narrow": ("a slender body on long narrow wings, a hooked bill", "a slender body on long narrow wings"),
    "rolling_fin": ("a smooth rounded back and a short rounded fin breaking the surface in a low arc, a stubby blunt snout", "a rounded back and a short fin breaking the surface"),
    "tall_fin": ("a tall straight fin standing up from a long glossy back, a pale patch behind the eye", "a tall straight fin cutting the surface"),
    "back_vast": ("a vast dark back with no fin, rough pale patches on the head, a spout of mist rising from two openings", "a vast dark finless back, a spout of mist"),
    "hinged_ribbed": ("two matching halves, shut, hinged along one edge, the outline round, ribs radiating from the hinge", "a pair of round, ribbed halves"),
    "hinged_elongate": ("two long matching halves, shut, hinged along one straight edge, pointed at one end", "a pair of long, pointed, shut halves"),
    "hinged_wedge": ("two large matching halves, shut, tapering to a point at one end and broad and flat-cut at the other, standing upright", "a large upright wedge of two halves"),
    "hinged_rough": ("two rough, uneven halves, shut, cemented to the rock, the outline irregular and frilled at the edge", "a rough, uneven pair of halves cemented to the rock"),
    "fan_pair": ("two rounded, fan-shaped halves, shut, a pair of small ears at the hinge, ribs radiating outward", "a pair of fan-shaped halves"),
    "ear_shell": ("a low, flattened, ear-shaped shell with a row of round holes along one edge, held tight to the rock", "a low, flattened, ear-shaped shell"),
    "coil_thin": ("a thin, delicate, flattened coil of a shell, ridged along its curve", "a thin, flattened coil of a shell"),
    "slug_winged": ("a small flat body with feathery branches spreading from its sides like fingers, lying on its back", "a small flat body with feathery branches at its sides"),
    "squid_body": ("a long tapering body with a triangular fin at the rear and ten arms gathered at the front", "a long tapering body with a fin at the rear"),
    "radial_short": ("a flat, five-cornered body, the corners short and blunt, like a puffed-out pentagon", "a flat five-cornered body"),
    "egg_fragile": ("a thin, white, egg-shaped shell with a five-petalled pattern across it, lying on the sand", "a thin, white, egg-shaped shell"),
    "float_trailing": ("a glossy bladder-like float with a crest along its top, long threads trailing below", "a glossy bladder with threads trailing"),
    "disc_sail": ("a flat oval disc with a thin clear sail standing up across its back", "a flat oval disc with a sail"),
    "carapace_paddles": ("a broad hard back with a row of spines along its front edge, the rearmost pair of legs flattened into paddles, a pair of pincers", "a broad spiny back, the hind legs flattened into paddles"),
    "mound_hole": ("a small cone of fine sand with a round hole at its top, the sand around it wet and stained", "a small cone of sand with a hole in its top"),
    "sand_coil": ("a thin coil of wet sand lying on the surface like a rope pushed out of a hole, a small dimple beside it", "a coil of wet sand beside a dimple"),
    "spiny_armoured": ("a heavy, spiny, armoured body, long thick feelers sweeping forward, ten legs and no pincers", "a heavy, spiny, armoured body with long feelers"),
    "stalked_plates": ("a cluster of small white plated shells on long leathery stalks, feathery threads reaching from the opening of each", "a cluster of small plated shells on long stalks"),
    "tube_cluster": ("a mass of hard, white, twisted tubes cemented together, each with a tiny opening at one end", "a mass of hard white twisted tubes"),
    "fan_crown": ("a leathery tube standing upright, from which a spiralled fan of fine feathery filaments unfurls", "an upright tube topped with a feathery fan"),
    "round_mouth_long": ("a long, round, limbless body, a round sucking disc for a mouth ringed with teeth, a row of small round openings along each side behind the head",
                         "a long limbless body with a round, toothed mouth"),
    "stiff_upright": ("a stiff, upright body bent at the neck, a long tube of a snout, a curled tail gripping a stem", "a stiff upright body with a curled tail"),
    "fusiform_beaked": ("a slender needle-thin body with a long beak-like lower jaw", "a needle-thin body with a long lower jaw"),
    "tapered_big": ("a long, tapering, heavy body with a high triangular fin on its back, a pair of side fins, a tail whose upper lobe is the longer", "a long heavy tapering body with a high triangular fin"),
    "disc_tall": ("a huge flat-sided round body, a tall fin above and a tall fin below, hardly any tail", "a huge round flat-sided body with a tall fin above and below"),
    # ── the woods (2026-11-02, J-3062) ──
    "beetle_long": ("a long, hard, oval body in three parts, two long jointed feelers swept back, six strong legs, glossy wing-cases", "a long hard oval body with long feelers swept back"),
    "crayfish_pincers": ("a stout armoured body ending in a fan-shaped tail, a pair of large pincers held forward, long thin feelers, eight walking legs", "a stout armoured body with large pincers held forward"),
    "deer_form": ("a tall slim-legged body, a long neck, a narrow head with large upright ears", "a tall slim-legged body with a long neck"),
    "parrot_form": ("a stocky body with a short thick neck, a heavy hooked beak and a broad squared tail", "a stocky body with a heavy hooked beak"),
    # ── the bush cast (2026-11-02, J-3064) ──
    'beetle_round': ('a small, hard, rounded body with glossy wing-cases, six short legs and short clubbed feelers', 'a small hard rounded body on six short legs'),
    'beetle_flat': ('a flat, hard, oval body pressed close to the surface, six short legs, short feelers', 'a flat hard oval body'),
    'beetle_jaws': ('a hard, flat-backed body with a pair of large curved jaws at the front, six legs', 'a hard body with large curved jaws'),
    'beetle_snout': ('a hard rounded body with a long curved snout bearing a pair of elbowed feelers, six legs', 'a hard rounded body with a long curved snout'),
    'beetle_longfeelers': ('a slim, hard body with feelers longer than itself, six legs, long wing-cases', 'a slim hard body with feelers longer than itself'),
    'beetle_oval_swim': ('a smooth, oval, hard body with oar-like hind legs, six legs', 'a smooth hard oval body with oar-like hind legs'),
    'tube_segmented': ('a soft, segmented tube of a body, short legs along the front and a few fat legs at the rear', 'a soft segmented tube of a body'),
    'twig_held_out': ('a thin segmented body held out stiff and angled from a twig, like a twig itself', 'a thin segmented body held out stiff like a twig'),
    'bag_hanging': ('a hanging bag of silk covered in tiny twigs, open at one end', 'a hanging bag of silk and tiny twigs'),
    'moth_form': ('a thick furry body with four broad wings held flat or tented over the back, feathery feelers', 'a furry body under four tented wings'),
    'fly_stout': ('a stout body with two clear wings, large round eyes and short bristled legs', 'a stout winged body with large round eyes'),
    'fly_long': ('a slender body with two clear wings, huge eyes, long bristled legs and a stout beak', 'a slender winged body with huge eyes'),
    'hopper_form': ('a small wedge-shaped body, two wings folded upright like a roof, strong back legs', 'a small wedge-shaped body with wings like a roof'),
    'ant_form': ('a small body in three parts with a narrow waist, six legs and elbowed feelers', 'a small narrow-waisted body on six legs'),
    'ichneumon_form': ('a slender narrow-waisted body, two pairs of wings and a very long thin tail trailing behind', 'a slender winged body with a long thin tail'),
    'cicada_form': ('a stout body with wide-set eyes and two pairs of large clear veined wings held like a roof', 'a stout body with large clear wings held like a roof'),
    'twig_body': ('a long thin body like a twig on long thin legs, held motionless at an angle', 'a long thin twig-like body on long thin legs'),
    'mantis_form': ('a long narrow body, a triangular head on a thin neck and two folded spiked forelegs held up in front', 'a long narrow body with spiked forelegs held up'),
    'roach_form': ('a flat, oval, shiny body with long feelers and six legs, the head hidden under a shield', 'a flat shiny oval body with long feelers'),
    'katydid_form': ('a leaf-shaped body with long hair-thin feelers and long hind legs, folded wings like a leaf', 'a leaf-shaped body with hair-thin feelers'),
    'shield_form': ('a flat, shield-shaped body with a small pointed head, six legs, short feelers', 'a flat shield-shaped body'),
    'lacewing_form': ('a delicate slender body with four large lace-veined wings held over the back like a tent', 'a delicate body under four lace-veined wings'),
    'springtail_form': ('a tiny soft body with a forked tail folded under it, short feelers', 'a tiny soft body with a folded tail'),
    'termite_form': ('a soft, pale, thick-waisted body with a round head and six short legs', 'a soft pale thick-waisted body'),
    'dragonfly_form': ('a long slender body, huge eyes, four large clear wings held out flat', 'a long slender body with four wings held out flat'),
    'damselfly_form': ('a very thin body, wide-set eyes, four narrow wings held folded along the back', 'a very thin body with narrow wings folded along it'),
    'spider_stocky': ('a stocky furred body with two large forward eyes and short strong legs', 'a stocky furred body on short strong legs'),
    'spider_heavy': ('a heavy, dark, glossy body with large jaws at the front and thick legs', 'a heavy dark body with large jaws'),
    'spider_longlegs': ('a tiny body on eight very long hair-thin legs', 'a tiny body on eight very long thin legs'),
    'harvest_round': ('a tiny rounded body on eight short legs, hard and flat-topped', 'a tiny hard rounded body on eight short legs'),
    'many_cylinder': ('a long cylinder of many ringed segments, two short legs on each, a small head', 'a long cylinder of many rings'),
    'many_flat': ('a flattened body of ridged plates with a ridge along each side, many short legs', 'a flattened body of ridged plates'),
    'many_fangs': ('a long flat body of many segments, one pair of legs on each, long feelers and a pair of curved fangs at the head', 'a long flat body of many segments with curved fangs'),
    'coil_flat': ('a broad, flat coil of a shell, thick and glossy, a large soft body below', 'a broad flat coil of a shell'),
    'ribbon_flat': ('a flat ribbon of a body, lance-shaped, a rounded head, no shell and no legs', 'a flat lance-shaped ribbon of a body'),
    'velvet_tube': ('a soft, velvety, many-legged tube of a body, stubby legs in pairs along its length, a pair of feelers', 'a velvety tube of a body on stubby legs'),
    'claws_tiny': ('a tiny flat body with a pair of large pincers held forward and no tail', 'a tiny flat body with large pincers'),
    'dead_stalked': ('a stiff, dead, segmented body with a thin stalk rising from its head', 'a stiff dead body with a thin stalk rising from the head'),
    'bully_form': ('a small thick-headed body, broad fan-like fins, a rounded tail', 'a small thick-headed body with broad fins'),
    'nymph_three': ('a small flattened body with three long tails, six legs and gills along the sides', 'a small flattened body with three long tails'),
    'nymph_two': ('a small flattened body with two long tails, six strong legs, wing-buds on its back', 'a small flattened body with two long tails'),
    'case_tube': ('a small tube of sand grains, a head and six legs poking from one end', 'a small tube of sand grains'),
    'boatman_form': ('a boat-shaped body that swims on its back with two long oar-like hind legs', 'a boat-shaped body with long oar-like hind legs'),
    'skater_form': ('a thin dark body resting on four long legs on the surface of the water', "a thin body on four long legs on the water's surface"),
    'frog_form': ('a smooth squat body with long folded hind legs, a wide head and bulging eyes', 'a smooth squat body with long folded hind legs'),
    'songbird_small': ('a small round body with a short pointed bill, a notched tail and close feathers', 'a small round body with a short bill'),
    'game_plump': ('a plump round body on strong legs, a short bill, a small head with a plume curling forward', 'a plump round body with a curling plume'),
    'ground_longtail': ('a large body on strong legs with a very long tapering tail, a bare patch round the eye', 'a large body with a very long tapering tail'),
    'swamp_heavy': ('a heavy rounded body on long strong legs, a short thick bill rising into a bare shield on the forehead', 'a heavy rounded body on long strong legs'),
    'kiwi_form': ('a round shaggy body with no visible tail, strong legs and a long thin bill carried low', 'a round shaggy body with a long thin bill'),
    'raptor_wide': ('very broad long wings held in a shallow V, a hooked bill, a long tail', 'broad long wings held in a shallow V'),
    'raptor_pointed': ('a compact body on pointed wings, a hooked bill, a long tail', 'a compact body on pointed wings'),
    'owl_form': ('a round pale heart-shaped face, a round body, broad soft wings', 'a round body with a heart-shaped pale face'),
    'cuckoo_form': ('a slender body with a very long tail, a slightly curved bill, pointed wings', 'a slender body with a very long tail'),
    'crow_form': ('a stout body with a heavy pointed bill, strong legs and a medium tail', 'a stout body with a heavy pointed bill'),
    'pigeon_small': ('a plump body with a small head, a short bill and a long tail', 'a plump body with a small head and long tail'),
    'cat_form': ('a sleek furred body on four legs, a long tail held up, pointed upright ears', 'a sleek furred body with pointed upright ears'),
    'pig_form': ('a heavy barrel of a body on short legs, a long flat snout, small eyes, a thin tail', 'a heavy barrel of a body with a long flat snout'),
    'goat_form': ('a sturdy body with a beard, back-swept horns and a short tail', 'a sturdy bearded body with back-swept horns'),
    'hare_form': ('a long-legged furred body with very long upright ears and a short tail', 'a long-legged furred body with very long ears'),
    'bat_form': ('a small furred body with thin leathery wings stretched over long fingers', 'a small furred body on thin leathery wings'),
}

# motion -> (clause for the detail tier, brief for the other tiers)
MOTIONS = {
    "still": ("it does not move", "motionless"),
    "clamped": ("it is shut tight and does not move", "shut and motionless"),
    "glide_slow": ("it moves, if at all, in a slow glide, too slow to follow by eye", "it creeps, if at all"),
    "sidle": ("it sidles sideways in short quick runs and freezes", "it sidles in short runs"),
    "jet": ("it darts backward in sudden jets", "it darts in jerks"),
    "pulse": ("it pulses, open and shut, drifting where the water takes it", "it pulses and drifts"),
    "wriggle": ("it writhes and threads itself under the surface", "it writhes"),
    "swim_dart": ("it hangs, then darts off in a flick of the tail", "it hangs and darts"),
    "undulate": ("it moves in long slow curves", "it undulates"),
    "lumber": ("it hauls itself forward in heaves on its front limbs, the rear dragging", "it shifts its bulk now and then"),
    "run_stop": ("it runs in quick bursts and stops", "it runs and stops"),
    "roll": ("it rolls up through the surface and under", "it rolls through the surface"),
    "sway": ("the fingers sway slowly in the wash", "it sways in the wash"),
    "hover_dart": ("it hangs in the air and darts at you", "it hovers and darts"),
    "flutter": ("it flutters in short, jinking flights and settles with its wings flat", "it flutters and settles"),
    "spring": ("it springs suddenly and lands still", "it springs and freezes"),
    "shuffle": ("it shuffles along with its nose down", "it shuffles along"),
    "bound": ("it moves in low, flowing bounds and stops upright to look", "it bounds and stops"),
    "soar": ("it glides low over the swell without a wingbeat, tilting from side to side", "it glides over the swell"),
    "wade_sweep": ("it walks slowly through the shallows, sweeping its bill from side to side", "it wades and sweeps its bill"),
    "skim": ("it skims the swell on stiff wings, tilting from side to side", "it skims the swell"),
    "drift": ("it drifts before the wind, riding high", "it drifts on the wind"),
    "pour": ("it pours itself along the rock and flows into a crevice", "it pours along the rock"),
    "walk_slow": ("it walks slowly on stilted legs, its feelers sweeping", "it walks slowly, feelers sweeping"),
    "skitter": ("it skitters along the surface in short bursts and dives", "it skitters on the surface"),
    "lie_flat": ("it lies on its side at the surface, one fin waving slowly", "it lies at the surface, a fin waving"),
    "browse": ("it moves a few slow steps, stops, and lifts its head to look and listen", "it steps, stops and lifts its head"),
    "clamber": ("it clambers along the branch, hooking its beak over the wood to pull itself up", "it clambers along the branch"),
    'crawl': ('it crawls slowly, feeling ahead with its feelers', 'it crawls'),
    'sway_twig': ('it sways slowly like a twig in a breeze', 'it sways like a twig'),
    'loop': ('it arches its body into a loop and stretches forward in steps', 'it loops along'),
    'fly_straight': ('it flies in a fast, straight, buzzing line', 'it flies in a straight line'),
    'swoop': ('it swoops low and fast, then climbs', 'it swoops and climbs'),
    'hop': ('it hops in short bounds on strong hind legs, stops, and sits upright', 'it hops and sits up'),
    'burst': ('it bursts into flight with a clatter of wings and glides away low', 'it bursts into flight'),
    'peck_walk': ('it walks with short steps, pecking at the ground', 'it pecks along the ground'),
    'flit': ('it flits from twig to twig, tail fanned, never still for long', 'it flits from twig to twig'),
    'root': ('it roots along the ground with its snout, turning the soil over', 'it roots along the ground'),
    'skate_surface': ('it skates across the surface in short darts without sinking', 'it skates on the surface'),
    'row_swim': ('it swims on its back, rowing with its long hind legs', 'it rows along on its back'),
    'climb_wet': ('it climbs the wet rock with its fins pressed flat', 'it climbs the wet rock'),
}

POSITIONS = {
    "on_rock_flat": "pressed flat to the rock", "pool_floor": "lying on the floor of the pool", "crevice": "wedged in a crevice",
    "edge_up_in_sand": "standing edge-up in the wet sand", "half_buried": "half buried in the sand",
    "hauled_out": "sprawled on the dry rock above the wash", "tideline_litter": "among the litter at the tideline",
    "afloat": "afloat at the surface", "in_water": "in the water", "under_stone": "under a stone",
    "in_grass": "in the dune grass", "on_wood": "on the weathered wood",
    "on_bare_sand": "on the bare sand", "in_air": "in the air", "among_stones": "among the stones",
    "clustered": "clustered tightly together on the rock", "burrow_mouth": "at the mouth of a small hole in the sand",
    "inside_shell": "tucked inside the shell of another animal", "standing_upright": "standing upright",
    "on_branch": "gripping a branch", "in_stream": "in the stream among the stones", "in_the_open": "out in the open",
    "high_in_the_canopy": "high in the leaves overhead",
    'on_bark': 'pressed against the bark',
    'on_leaf': 'on a leaf',
    'under_log': 'under a fallen log',
    'on_flower': 'on a flower',
    'in_web': 'in a web',
    'hanging': 'hanging from a twig',
    'on_ground': 'on the ground',
    'in_litter': 'among the leaf litter',
    'on_water': 'on the surface of the water',
    'on_wet_stone': 'on a wet stone',
    'in_silt': 'half buried in the silt',
    'on_trunk': 'clinging to the trunk',
    'in_tree_hole': 'in a hollow of the tree',
    'under_bark': 'under a strip of loose bark',
    'on_track': 'on the track',
    'in_foliage': 'among the foliage',
}

# how it answers being disturbed: stored for the deed layer (P2+), not rendered by the composer
DISTURB = frozenset({"ignores", "curls", "clamps_tight", "buries", "retracts", "jets_away", "flees", "rears_and_gapes",
                     "freezes", "stings", "bites"})

NUM = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen",
       "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]

OBS_REQUIRED = ("size_cm", "shape", "colour", "pattern", "sheen", "covering", "motion", "position", "on_disturb")


def make_obs(**o) -> dict:
    """Validate an observable tuple against the closed vocabularies. Raises ValueError naming the bad field."""
    miss = [k for k in OBS_REQUIRED if k not in o]
    if miss:
        raise ValueError(f"obs missing {miss}")
    unknown = set(o) - set(OBS_REQUIRED) - {"span_cm", "colour2", "counts"}
    if unknown:
        raise ValueError(f"obs has unknown fields {sorted(unknown)}")
    for field, vocab in (("shape", SHAPES), ("colour", COLOURS), ("pattern", PATTERNS), ("sheen", SHEENS), ("covering", COVERINGS),
                         ("motion", MOTIONS), ("position", POSITIONS)):
        if o[field] not in vocab:
            raise ValueError(f"obs.{field}={o[field]!r} not in the closed vocabulary")
    if o["on_disturb"] not in DISTURB:
        raise ValueError(f"obs.on_disturb={o['on_disturb']!r} not in DISTURB")
    if o["pattern"] != "plain":
        if o.get("colour2") not in COLOURS:
            raise ValueError("a non-plain pattern needs a colour2 from COLOURS")
    elif o.get("colour2") is not None and o["colour2"] not in COLOURS:
        raise ValueError(f"obs.colour2={o['colour2']!r} not in COLOURS")
    if not (isinstance(o["size_cm"], (int, float)) and o["size_cm"] > 0):
        raise ValueError("obs.size_cm must be a positive number")
    out = dict(o)
    out.setdefault("span_cm", out["size_cm"])
    if out["span_cm"] < out["size_cm"]:
        raise ValueError("obs.span_cm cannot be below size_cm")
    out.setdefault("colour2", None)
    out.setdefault("counts", {})
    for name, n in out["counts"].items():
        if not (isinstance(n, int) and 0 <= n < len(NUM)):
            raise ValueError(f"obs.counts[{name!r}]={n!r} out of range")
    return out


# ── how much can he make out: apparent size = span / distance ────────────────────────────────────────────────
TIERS = ("none", "form", "colour", "detail")
FORM_AT, COLOUR_AT, DETAIL_AT = 0.015, 0.04, 0.12       # span/distance ratios (coarse by design; P2 may tune)


def detail_tier(span_cm: float, dist_m: float) -> str:
    """none | form | colour | detail from the creature's span and its distance from him."""
    r = (float(span_cm) / 100.0) / max(float(dist_m), 0.3)
    if r >= DETAIL_AT:
        return "detail"
    if r >= COLOUR_AT:
        return "colour"
    if r >= FORM_AT:
        return "form"
    return "none"


def _down(tier: str, n: int = 1) -> str:
    return TIERS[max(0, TIERS.index(tier) - n)]


def size_phrase(cm: float) -> str:
    for hi, phrase in SIZE_BANDS:
        if cm < hi:
            return phrase
    return SIZE_BANDS[-1][1]


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def compose(o: dict, tier: str, night: bool = False) -> str:
    """The look of a creature at a detail tier, from its observable tuple alone. '' at tier `none`.
    form   = where, how big, its tone (not its colour; omitted at night), its outline, whether it moves.
    colour = adds the colours and pattern.
    detail = adds the full body plan, sheen, covering, a count of any countable parts, and how it moves."""
    if tier == "none":
        return ""
    pos = POSITIONS[o["position"]]
    shape_full, shape_brief = SHAPES[o["shape"]]
    clause, brief = MOTIONS[o["motion"]]
    size = size_phrase(o["size_cm"])
    c1, tone = COLOURS[o["colour"]]
    c2 = COLOURS[o["colour2"]][0] if o.get("colour2") else None
    if tier == "form":
        tonal = "" if night else f", {TONE_WORDS[tone].replace('the ground', BACKGROUND.get(o['position'], 'the ground'))}"
        return f"{_cap(pos)}: something {size}{tonal}; {shape_brief}; {brief}."
    if tier == "colour":
        col = c1 if (o["pattern"] == "plain" or not c2) else f"{c1} and {c2}"
        return f"{_cap(pos)}: {size}, {shape_brief}, {col}; {brief}."
    pat = PATTERNS[o["pattern"]].format(c1=c1, c2=c2 or c1)
    sent = [f"{_cap(pos)}, {size}: {shape_full}.", f"{_cap(pat)}, {SHEENS[o['sheen']]}.", f"{_cap(COVERINGS[o['covering']])}."]
    if o.get("counts"):
        sent.append(" ".join(f"You count {NUM[n]} {name}." for name, n in o["counts"].items()))
    sent.append(f"{_cap(clause)}.")
    return " ".join(sent)


# ── zones: spot -> a place in shore.json ─────────────────────────────────────────────────────────────────────
BUCKET_S = 600.0            # a sampled position holds for ten minutes: two looks a minute apart see the same thing
FRAME = (30.0, 20.0)        # shore.json "size"

ZONES = {
    "pool": {"mode": "disc", "anchor": "rock_pools", "r": 3.0, "max_level": 0.60},
    "flat": {"mode": "disc", "anchor": "sand_flat", "r": 4.0, "max_level": 0.45, "landward": True},
    "mussel_shelf": {"mode": "disc", "anchor": "mussel_shelf", "r": 2.5, "max_level": 0.35},
    "rock_shelf": {"mode": "disc", "anchor": "rock_shelf", "r": 2.5},
    "dune": {"mode": "disc", "anchor": "dune_grass", "r": 3.0},
    "shingle": {"mode": "disc", "anchor": "shingle_bank", "r": 4.0},
    "driftwood": {"mode": "disc", "anchor": "driftwood_tangle", "r": 2.5},
    "tideline": {"mode": "waterline", "x": (3.0, 27.0), "dy": (-0.4, 0.4)},
    "surf": {"mode": "waterline", "x": (3.0, 27.0), "dy": (0.5, 3.5)},
    "offshore": {"mode": "offshore", "x": (0.0, 30.0), "y_beyond": (4.0, 110.0)},
    "cave": {"mode": "disc", "anchor": "cave", "r": 1.2},
    # D-0651 (founder, 2026-11-02; J-3260): the stream mouth is a braid reaching the waterline around x 14 to 16, now an authored feature in
    # shore.json (east of driftwood_tangle and the shell drift, west of rock_pools). The zone hangs on it as a disc, so it needs that feature
    # in the geometry file: the patch script adds it, before the restart that carries this line.
    "stream_mouth": {"mode": "disc", "anchor": "stream_mouth", "r": 2.0},
}


PLACES: dict = {}     # place -> {layout, zones, targets, frame, scenery, names}; "shore" is registered at the foot of this module, other places
                      # (core/life_wood.py) register themselves. One engine, one set of closed vocabularies, one leak test.


def _lay(place: str = "shore") -> dict:
    lay = spatial.layout((PLACES.get(place) or {}).get("layout", place))
    if not lay:
        raise RuntimeError(f"{place} geometry not readable")
    return lay


def _zones(place: str = "shore") -> dict:
    return PLACES[place]["zones"] if place in PLACES else ZONES


def waterline_y(now: float | None = None) -> float:
    w = _lay()["features"]["waterline"]
    ty = w["tide_y"]
    lv = world_clock.tide(now)["level"]
    return round(ty[1] - lv * (ty[1] - ty[0]), 2)       # identical to spatial._waterline_pos


def _anchor(z: dict, lay: dict) -> list:
    """A disc zone's centre: an explicit sidecar `pos` (an ASSUMED or non-geometry placement) or the authored feature it hangs on."""
    return list(z["pos"]) if z.get("pos") else (list(lay["features"][z["anchor"]]["pos"]) + [0.0])[:3]


def zone_ref(zone: str, place: str = "shore") -> list | None:
    """A representative point of the zone (for the vantage distance). None for a pending zone."""
    z = _zones(place)[zone]
    lay = _lay(place)
    if z["mode"] == "disc":
        c = _anchor(z, lay)
        if z.get("z"):
            c[2] = sum(z["z"]) / 2.0
        return c
    if z["mode"] == "segment":
        a, b = z["a"], z["b"]
        return [(a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, (a[2] + b[2]) / 2.0]
    if z["mode"] == "waterline":
        ty = lay["features"]["waterline"]["tide_y"]
        return [15.0, round((ty[0] + ty[1]) / 2 + (sum(z["dy"]) / 2), 2), 0.0]
    if z["mode"] == "offshore":
        return [15.0, 50.0, 0.0]
    return None


def zone_vantage_distance(zone: str, place: str = "shore") -> float:
    """Distance from the NEAREST authored standpoint to the zone's centre (3D: a creature in the canopy is not at arm's length): where he
    goes to look at it. The static look lines (hidden.feature) are composed at this distance; a real look uses its own distance."""
    ref = zone_ref(zone, place)
    sps = _lay(place)["standpoints"]
    return min(math.dist([s["pos"][0], s["pos"][1], (s["pos"] + [0.0, 0.0, 0.0])[2]], [ref[0], ref[1], ref[2] if len(ref) > 2 else 0.0]) for s in sps.values())


def sample_position(zone: str, key: str, now: float | None = None, place: str = "shore") -> dict | None:
    """One position for a population in a zone: deterministic per (zone, row, ten-minute bucket), tide-consistent on the shore.
    {'pos': [x, y, z], 'out_of_frame': bool}, or None when the zone is closed (tide over it, or the zone is pending)."""
    now = time.time() if now is None else now
    z = _zones(place)[zone]
    if z["mode"] == "pending":
        return None
    lay = _lay(place)
    frame = PLACES[place]["frame"] if place in PLACES else FRAME
    level = world_clock.tide(now)["level"] if (z.get("max_level") is not None or z["mode"] in ("waterline", "offshore") or z.get("landward")) else 0.0
    if z.get("max_level") is not None and level > z["max_level"]:
        return None
    wl = waterline_y(now) if (z["mode"] in ("waterline", "offshore") or z.get("landward")) else 0.0
    rng = random.Random(f"{place}_bestiary:{zone}:{key}:{int(now // BUCKET_S)}")
    if z["mode"] == "disc":
        ax, ay, az = _anchor(z, lay)
        for _ in range(24):
            ang, rad = rng.uniform(0.0, 2 * math.pi), z["r"] * math.sqrt(rng.random())
            x, y = ax + rad * math.cos(ang), ay + rad * math.sin(ang)
            if not (0.0 <= x <= frame[0] and 0.0 <= y <= frame[1]):
                continue
            if z.get("landward") and y > wl - 0.2:
                continue
            zz = rng.uniform(*z["z"]) if z.get("z") else az
            return {"pos": [round(x, 2), round(y, 2), round(zz, 2)], "out_of_frame": False}
        return None
    if z["mode"] == "segment":                                       # a stream, a track: a line with a little scatter either side
        t = rng.random()
        a, b = z["a"], z["b"]
        j = z.get("jitter", 0.5)
        x = a[0] + t * (b[0] - a[0]) + rng.uniform(-j, j)
        y = a[1] + t * (b[1] - a[1]) + rng.uniform(-j, j)
        return {"pos": [round(min(max(x, 0.0), frame[0]), 2), round(min(max(y, 0.0), frame[1]), 2), round(a[2] + t * (b[2] - a[2]), 2)], "out_of_frame": False}
    if z["mode"] == "waterline":
        x = rng.uniform(*z["x"])
        y = wl + rng.uniform(*z["dy"])
        return {"pos": [round(x, 2), round(y, 2), 0.0], "out_of_frame": y > frame[1]}
    x = rng.uniform(*z["x"])                                                    # offshore
    y = wl + rng.uniform(*z["y_beyond"])
    return {"pos": [round(x, 2), round(y, 2), 0.0], "out_of_frame": y > frame[1]}


_SECTOR = {"ahead": "ahead of you", "to your right": "to your right", "to your left": "to your left", "behind you": "behind you"}


def pace_word(d: float) -> str:
    """Distance said in paces — the shore is 30 m across, so spatial._dist_word's room-scale words are too coarse."""
    if d <= 1.5:
        return "within arm's reach"
    if d <= 4.0:
        return "a few paces off"
    if d <= 10.0:
        return "a dozen paces or so off"
    if d <= 25.0:
        return "a good way off"
    return "a long way off"


def standpoint(name_or_dict, place: str = "shore") -> dict:
    if isinstance(name_or_dict, dict):
        return name_or_dict
    return _lay(place)["standpoints"][name_or_dict]


def perceive(r: dict, from_standpoint, now: float | None = None, night: bool = False) -> dict:
    """What he can make out of a row from a standpoint right now (the P2 look will call this).
    {'visible', 'tier', 'dist', 'sector', 'pos', 'line'}; line carries the tiered look plus where it is, or '' if nothing resolves."""
    o = r["obs"]
    place = r.get("bestiary_place", "shore")
    s = sample_position(r["zone"], r["key"], now, place)
    if s is None:
        return {"visible": False, "tier": "none", "line": "", "reason": "zone_closed"}
    sp = standpoint(from_standpoint, place)
    rel = spatial._rel(sp, s["pos"])
    # 3D: a creature eight metres up a tree is not as near as its ground distance says. `dist` stays spatial's own 2D figure (what the
    # egocentric clause and the tests compare against); the detail tier and the pace word use `dist3`.
    dist3 = round(math.hypot(rel["dist"], s["pos"][2] - (sp["pos"] + [0.0, 0.0, 0.0])[2]), 2)
    tier = detail_tier(o["span_cm"], dist3)
    if tier == "none":
        return {"visible": False, "tier": "none", "dist": rel["dist"], "dist3": dist3, "sector": rel["sector"], "pos": s["pos"], "line": "", "reason": "too_far"}
    where = f"It is {_SECTOR[rel['sector']]}{' and up above' if s['pos'][2] - (sp['pos'] + [0.0, 0.0, 0.0])[2] >= 3.0 else ''}, {pace_word(dist3)}."
    return {"visible": True, "tier": tier, "dist": rel["dist"], "dist3": dist3, "sector": rel["sector"], "pos": s["pos"],
            "line": f"{compose(o, tier, night)} {where}"}


# ── the row builder ──────────────────────────────────────────────────────────────────────────────────────────
_ABSENT = {"season": "Nothing shows there at this time of year.", "night": "Nothing shows there in the dark.",
           "day": "Nothing shows there in daylight.", "weather": "Nothing shows in this weather.", "chance": "Nothing shows there just now."}
_MISS = "The place gives nothing up."


def place_row(place: str, key: str, *, species: str, book_names: tuple, book_words: tuple, zone: str, obs: dict,
              active_hours: dict, season_curve: list, weather_gate: dict, ease: float, count: tuple,
              lifespan_y=None, diet: tuple = (), eaten_by: tuple = (), tide: str | None = None,
              days_about: float = 1.0, light: str = "indifferent", note: str = "", eyeshine: bool = False) -> dict:
    """A life row whose look is composed from `obs`, for any registered place. No name, no alias, no reveal caption."""
    o = make_obs(**obs)
    if zone not in _zones(place) or _zones(place)[zone]["mode"] == "pending":
        raise ValueError(f"{key}: zone {zone!r} is unknown or pending in {place}")
    base = detail_tier(o["span_cm"], zone_vantage_distance(zone, place))
    feature = {}
    if base != "none":
        feature["day"] = compose(o, base)
        feature["dawn"] = feature["dusk"] = compose(o, _down(base), night=False)
        feature["night"] = compose(o, "form", night=True)
        feature = {k: v for k, v in feature.items() if v}
    return row(key, kind="population", name=None, aliases=(), places={place: [zone]}, bestiary_place=place, eyeshine=eyeshine,
               active_hours=active_hours, season_curve=season_curve, weather_gate=weather_gate, light=light,
               count=count, lifespan_y=lifespan_y, diet=diet, eaten_by=eaten_by, traces=(), ease=ease, tide=tide,
               days_about=days_about,
               hidden={"species": species, "book_names": tuple(book_names), "book_words": tuple(book_words),
                       "feature": feature, "miss": _MISS, "absent": dict(_ABSENT)},
               obs=o, zone=zone, note=note)


def shore_row(key: str, **kw) -> dict:
    return place_row("shore", key, **kw)


# ── the pilot rows: a small burrower-ish one, a pool one, a huge far one ─────────────────────────────────────
RESIDENT = [1.0] * 12


def rows() -> list[dict]:
    R = [
        shore_row(
            "eleven_armed_starfish", species="eleven-armed starfish",
            book_names=("eleven-armed starfish", "eleven armed starfish", "coscinasterias"),
            book_words=("arms", "spines", "tube feet", "regenerat", "mussels", "pool"),
            zone="pool",
            obs=dict(size_cm=14, span_cm=20, shape="radial_many", colour="orange_brown", colour2="cream", pattern="mottled",
                     sheen="matt", covering="spined", counts={"arms": 11}, motion="glide_slow", position="pool_floor",
                     on_disturb="ignores"),
            active_hours={"dawn": 0.8, "day": 0.8, "dusk": 0.8, "night": 0.8}, season_curve=RESIDENT,
            weather_gate={"rain": 1.0, "wind": 1.0, "storm": 0.7, "frost": 1.0}, ease=0.6,
            count=("one", "a few", "several"), lifespan_y=5, diet=("mussels", "limpets"), eaten_by=("gulls",), tide="low",
            note="PILOT. native; splits itself in two (arms of unequal length); seen at low water in the pools"),
        shore_row(
            "pipi", species="pipi", book_names=("pipi", "pipis", "paphies"),
            book_words=("sand", "shell", "siphon", "filter", "harbour", "bivalve"),
            zone="flat",
            obs=dict(size_cm=6, span_cm=6, shape="hinged_pair", colour="cream", colour2="olive_brown", pattern="banded",
                     sheen="matt", covering="ridged", motion="clamped", position="edge_up_in_sand", on_disturb="buries"),
            active_hours={"dawn": 0.8, "day": 0.8, "dusk": 0.8, "night": 0.8}, season_curve=RESIDENT,
            weather_gate={"rain": 1.0, "wind": 1.0, "storm": 0.6, "frost": 1.0}, ease=0.35,
            count=("a few", "a scatter", "a whole bed of them"), lifespan_y=8, diet=("plankton",), eaten_by=("gulls", "oystercatcher"),
            tide="low", note="PILOT. native bivalve of the sand flat; buries on disturbance (deed layer is P2+)"),
        shore_row(
            "sea_lion", species="sea lion", book_names=("sea lion", "sea lions", "rapoka", "rāpoka", "phocarctos"),
            book_words=("flippers", "haul", "colony", "pup", "mane", "bull", "sub-antarctic"),
            zone="rock_shelf",
            obs=dict(size_cm=180, span_cm=210, shape="pinniped_bulk", colour="buff", colour2="dark_brown", pattern="two_tone",
                     sheen="furred_sleek", covering="furred", motion="lumber", position="hauled_out", on_disturb="rears_and_gapes"),
            active_hours={"dawn": 0.6, "day": 1.0, "dusk": 0.6, "night": 0.3},
            season_curve=[0.2, 0.2, 0.4, 0.6, 0.7, 0.8, 0.8, 0.7, 0.5, 0.3, 0.2, 0.2],
            weather_gate={"rain": 0.7, "wind": 0.8, "storm": 0.2, "frost": 0.9}, ease=0.95,
            count=("one", "one", "two"), lifespan_y=20, diet=("fish", "squid"), days_about=0.12,
            note="PILOT. rare visitor, a few days a year; HAZARD: large and will charge (note only; no mechanical harm in P1). "
                 "Shares the rock shelf with the fur_seal row on purpose: two look-alikes he has to tell apart by sight"),
    ]
    try:   # the other 97 (core/life_shore_cast.py); a cast that fails to build must not take the pilot rows down with it
        from core import life_shore_cast as _cast
        R += _cast.rows()
    except Exception as exc:   # pragma: no cover - surfaced loudly by scripts/_test_shore_bestiary_p1.py (it counts 100 rows)
        import logging
        logging.getLogger("nascence.life_shore").warning("[life_shore] cast not built: %s", exc)
    return R


def enabled(place: str = "shore") -> bool:
    """The default-OFF gate for registering a place's rows into the live engine (data/life_flags.json: "<place>_bestiary": true)."""
    try:
        from core import life as _life
        return bool(_life._flags().get(f"{place}_bestiary"))
    except Exception:
        return False


def _flag(name: str, place: str = "shore") -> bool:
    """ONE FLAG BRINGS IT ALL UP (founder, 2026-11-01: "ready to run by just flipping true"). "shore_bestiary": true registers the rows
    AND, unless a sub-flag is set explicitly, turns the described-look answer and the place-look discovery ON with it. To run it in SHADOW
    (log what would be shown, show nothing) set "shore_bestiary_render": false and/or "shore_bestiary_discover": false explicitly."""
    try:
        from core import life as _life
        fl = _life._flags()
        return bool(fl[name]) if name in fl else bool(fl.get(f"{place}_bestiary"))
    except Exception:
        return False


def render_live(place: str = "shore") -> bool:
    """P2's gate (data/life_flags.json "shore_bestiary_render"; hot, re-read every ten seconds; DEFAULTS TO "shore_bestiary" when absent).
    OFF = SHADOW: a described look is LOGGED as would_answer (life_events.jsonl, outcome 'described_shadow') and the look falls through
    exactly as it did. ON = the look is answered by the row, composed for his standpoint and distance."""
    return _flag(f"{place}_bestiary_render", place)


# ── P2: how a look reaches a row that has no name ────────────────────────────────────────────────────────────
# Du writes his own description ("the orange arms spread on the pool floor"). The willed look hand reduces that sentence to a
# keyword (nodes.inner_monologue._observe_target) and forwards the SENTENCE as `raw` (sensorium.look -> life.look_answer).
# A row matches when the words of ONE look clause carry at least MIN_ATTRS DIFFERENT intrinsic attributes of what is actually
# there (colour, pattern, shape, size, motion, covering, a counted part). Where it is (the pool, the sand) never counts, so a
# scenery look ('the pale stones in the tide pools') cannot be taken for a creature. A guess word ('star', 'worm') counts as a
# shape word -- the world answers with what is there and never says whether the guess was right.
MIN_ATTRS = 2           # different attributes in one clause ...
# ... of which at least one must be a STRONG one (a body part or plan, a pattern, a covering, a counted thing). Colour, size and how
# it moves are WEAK: 'the dark heavy little stone' says dark and little and is not a creature. (The false-positive sweeps in
# scripts/_test_shore_bestiary_p2.py found this: with every word counted, a stone, a spinifex head and a penguin were all taken
# for a sea lion or a starfish.) Word lists below are CURATED, not mined from the composer's sentences, for the same reason.
STRONG_ATTRS = frozenset({"shape", "covering", "counts"})   # (pattern is weak too: "bands", "streaks" are everywhere in scenery)
# (motion is WEAK too: 'small webbed prints dragging up the wet sand toward those dark ...' -- a penguin's tracks -- read as a sea lion
# on 'dragging' + 'dark' in the real-thought sweep.)
ALLOW_GUESS_WORDS = True
GUESS_WORDS = {
    "radial_five": ("starfish",), "radial_many": ("starfish",), "hinged_pair": ("clam", "bivalve"),
    "spiral_cone": ("whorl",), "carapace_legs": ("crab",), "jointed_curve": ("shrimp", "prawn"),
    "soft_worm": ("worm",), "serpent_long": ("eel", "snake"), "fusiform": ("fish",), "flat_wing": ("skate", "stingray"),
    "flat_oval": ("flatfish", "flounder"), "bell_trailing": ("jellyfish", "jelly"), "soft_sac_arms": ("octopus", "squid"),
    "pinniped_bulk": (), "long_back": ("whale", "dolphin"), "six_legged": ("insect", "beetle", "bug"),
    "eight_legged": ("spider",), "column_fingers": ("anemone",), "sausage_soft": ("cucumber",), "slug_soft": ("slug",),
    "sphere_spines": ("urchin",), "small_furred": ("mouse",),
    "hinged_ribbed": ("cockle",), "hinged_elongate": ("mussel",), "hinged_wedge": ("mussel",), "hinged_rough": ("oyster",), "fan_pair": ("scallop",),
    "ear_shell": ("abalone",), "spiral_cone": ("whorl", "snail"), "stiff_upright": ("seahorse",), "tapered_big": ("shark",), "round_mouth_long": ("lamprey",),
    "spiny_armoured": ("lobster", "crayfish"), "squid_body": ("squid", "cuttlefish"), "wader_small": ("plover",), "wader_tall": ("heron",),
    "wings_vast": ("albatross",), "lizard_form": ("lizard", "skink"), "spined_four_legged": ("hedgehog",), "long_low_furred": ("weasel", "stoat"),
    "winged_broad": ("butterfly",), "eight_legged": ("spider",), "float_trailing": ("jellyfish",), "disc_tall": ("sunfish",),
    "beetle_long": ("beetle",), "crayfish_pincers": ("crayfish", "lobster"), "deer_form": ("deer",), "parrot_form": ("parrot",),
    'beetle_round': ('beetle',),
    'beetle_flat': ('beetle',),
    'beetle_jaws': ('beetle',),
    'beetle_snout': ('weevil',),
    'beetle_longfeelers': ('longhorn',),
    'beetle_oval_swim': ('beetle',),
    'tube_segmented': ('caterpillar', 'grub'),
    'twig_held_out': ('caterpillar',),
    'bag_hanging': ('bagworm',),
    'moth_form': ('moth',),
    'fly_stout': ('fly',),
    'fly_long': ('fly',),
    'hopper_form': ('hopper',),
    'ant_form': ('ant', 'ants'),
    'ichneumon_form': ('wasp',),
    'cicada_form': ('cicada',),
    'twig_body': ('twig',),
    'mantis_form': ('mantis',),
    'roach_form': ('cockroach',),
    'katydid_form': ('katydid',),
    'shield_form': ('stinkbug',),
    'lacewing_form': ('lacewing',),
    'springtail_form': ('springtail',),
    'termite_form': ('termite',),
    'dragonfly_form': ('dragonfly',),
    'damselfly_form': ('damselfly',),
    'spider_stocky': ('spider',),
    'spider_heavy': ('spider',),
    'spider_longlegs': ('spider',),
    'harvest_round': ('mite',),
    'many_cylinder': ('millipede',),
    'many_flat': ('millipede',),
    'many_fangs': ('centipede',),
    'coil_flat': ('snail',),
    'ribbon_flat': ('flatworm',),
    'velvet_tube': ('peripatus',),
    'claws_tiny': ('pseudoscorpion',),
    'dead_stalked': ('caterpillar',),
    'bully_form': ('bully',),
    'nymph_three': ('mayfly',),
    'nymph_two': ('stonefly',),
    'case_tube': ('caddis',),
    'boatman_form': ('backswimmer',),
    'skater_form': ('skater',),
    'frog_form': ('frog',),
    'songbird_small': ('finch',),
    'game_plump': ('quail',),
    'ground_longtail': ('pheasant',),
    'swamp_heavy': ('pukeko',),
    'kiwi_form': ('kiwi',),
    'raptor_wide': ('hawk', 'harrier'),
    'raptor_pointed': ('falcon',),
    'owl_form': ('owl',),
    'cuckoo_form': ('cuckoo',),
    'crow_form': ('magpie', 'myna'),
    'pigeon_small': ('dove',),
    'cat_form': ('cat',),
    'pig_form': ('pig',),
    'goat_form': ('goat',),
    'hare_form': ('hare',),
    'bat_form': ('bat',),
}
# the distinctive words of each body plan and each way of moving (what he would actually say of it)
SHAPE_WORDS = {
    "radial_five": ("arms", "radiating", "radial"), "radial_many": ("arms", "radiating", "radial", "stubby"),
    "hinged_pair": ("halves", "hinged", "hinge"), "spiral_cone": ("spiral", "wound", "cone"), "clamped_cone": ("cone", "clamped"),
    "plated_oval": ("plates", "plated", "armoured"), "carapace_legs": ("pincers", "claws", "carapace"),
    "jointed_curve": ("feelers", "jointed"), "soft_worm": ("segmented", "limbless"), "serpent_long": ("limbless",),
    "fusiform": ("fins", "tapered"), "flat_wing": ("winglike",), "flat_oval": ("flat",), "bell_trailing": ("dome", "threads", "trailing"),
    "soft_sac_arms": ("arms", "suckers"), "pinniped_bulk": ("flippers", "paddle", "paddles", "neck", "shoulders"),
    "long_back": ("back", "rolls"), "six_legged": ("six", "feelers"), "eight_legged": ("eight",),
    "column_fingers": ("fingers", "column"), "cone_plates": ("plates", "interlocking"), "sausage_soft": ("sausage", "leathery"),
    "slug_soft": ("horns", "frilled"), "sphere_spines": ("spines", "spiny", "bristling"), "disc_flat": ("disc",),
    "small_furred": ("furred", "tail"),
    "six_legged_pincers": ("pincers", "feelers"), "winged_small": ("wings", "wing"), "winged_slender": ("wings", "needle"),
    "winged_broad": ("wings", "feelers", "clubs"), "jumper_long_legs": ("feelers", "spined"), "waisted_winged": ("waist", "wings", "dangling"),
    "lizard_form": ("limbs",), "spined_four_legged": ("spines", "bristling", "spiny"),
    "long_low_furred": ("furred", "tail", "narrow"), "wader_small": ("bill", "feathers", "feathered"),
    "wader_tall": ("bill", "neck"), "wings_vast": ("wings", "bill", "hooked"), "wings_narrow": ("wings", "bill", "hooked"),
    "rolling_fin": ("fin", "snout", "arc"), "tall_fin": ("fin", "straight"), "back_vast": ("finless",),
    "hinged_ribbed": ("halves", "hinged", "ribs", "ribbed"), "hinged_elongate": ("halves", "hinged", "pointed"),
    "hinged_wedge": ("halves", "hinged", "wedge", "upright"), "hinged_rough": ("halves", "hinged", "cemented", "frilled"),
    "fan_pair": ("halves", "fan-shaped", "ears", "ribs"), "ear_shell": ("holes", "ear-shaped"),
    "coil_thin": ("coil", "ridged", "delicate"), "slug_winged": ("branches", "feathery"),
    "squid_body": ("arms", "fin", "tapering"), "radial_short": ("pentagon", "corners", "five-cornered"),
    "egg_fragile": ("egg-shaped", "petalled", "pattern"), "float_trailing": ("bladder", "crest", "threads"),
    "disc_sail": ("sail", "disc"), "carapace_paddles": ("paddles", "pincers", "spines"), "mound_hole": ("cone", "hole", "mound"),
    "sand_coil": ("coil", "dimple", "rope"), "spiny_armoured": ("feelers", "armoured", "spiny"),
    "stalked_plates": ("stalks", "stalked", "plated", "feathery"), "tube_cluster": ("tubes", "twisted", "tube"),
    "fan_crown": ("fan", "filaments", "feathery", "tube"), "round_mouth_long": ("sucking", "disc", "teeth", "limbless"),
    "stiff_upright": ("snout", "curled", "tube", "upright"), "fusiform_beaked": ("beak", "needle-thin", "jaw"),
    "tapered_big": ("fin", "triangular", "lobe"), "disc_tall": ("flat-sided", "fin"),
    "beetle_long": ("feelers", "wing-cases"), "crayfish_pincers": ("pincers", "fan-shaped", "feelers"),
    "deer_form": ("ears", "antlers", "neck"), "parrot_form": ("beak", "hooked"),
    'beetle_round': ('clubbed',),
    'beetle_flat': ('wing-cases', 'pressed'),
    'beetle_jaws': ('jaws',),
    'beetle_snout': ('snout', 'elbowed'),
    'beetle_longfeelers': ('feelers', 'wing-cases'),
    'beetle_oval_swim': ('oar-like',),
    'tube_segmented': ('segmented', 'fat'),
    'twig_held_out': ('segmented', 'angled'),
    'bag_hanging': ('bag', 'silk'),
    'moth_form': ('tented', 'furry', 'feathery'),
    'fly_stout': ('bristled',),
    'fly_long': ('beak', 'bristled'),
    'hopper_form': ('roof', 'wedge-shaped'),
    'ant_form': ('waist', 'elbowed'),
    'ichneumon_form': ('waisted', 'tail'),
    'cicada_form': ('veined', 'wide-set'),
    'twig_body': ('twig-like', 'twig'),
    'mantis_form': ('forelegs', 'spiked', 'triangular'),
    'roach_form': ('shield', 'feelers'),
    'katydid_form': ('leaf-shaped', 'hair-thin'),
    'shield_form': ('shield-shaped',),
    'lacewing_form': ('lace-veined', 'lace'),
    'springtail_form': ('forked',),
    'termite_form': ('thick-waisted',),
    'dragonfly_form': ('flat',),
    'damselfly_form': ('folded', 'narrow'),
    'spider_stocky': ('forward', 'furred'),
    'spider_heavy': ('jaws',),
    'spider_longlegs': ('hair-thin', 'long'),
    'harvest_round': ('flat-topped',),
    'many_cylinder': ('rings', 'ringed', 'cylinder'),
    'many_flat': ('ridged', 'plates'),
    'many_fangs': ('fangs', 'curved'),
    'coil_flat': ('coil',),
    'ribbon_flat': ('ribbon', 'lance-shaped'),
    'velvet_tube': ('velvety', 'stubby'),
    'claws_tiny': ('pincers',),
    'dead_stalked': ('stalk',),
    'bully_form': ('fan-like', 'thick-headed'),
    'nymph_three': ('gills', 'tails'),
    'nymph_two': ('wing-buds', 'tails'),
    'case_tube': ('tube', 'grains'),
    'boatman_form': ('boat-shaped', 'oar-like'),
    'skater_form': ('surface',),
    'frog_form': ('bulging', 'hind'),
    'songbird_small': ('bill', 'notched'),
    'game_plump': ('plume', 'curling'),
    'ground_longtail': ('tapering',),
    'swamp_heavy': ('shield', 'forehead'),
    'kiwi_form': ('shaggy',),
    'raptor_wide': ('V', 'hooked'),
    'raptor_pointed': ('pointed', 'hooked'),
    'owl_form': ('heart-shaped',),
    'cuckoo_form': ('curved',),
    'crow_form': ('pointed',),
    'pigeon_small': ('plump',),
    'cat_form': ('pointed', 'upright'),
    'pig_form': ('snout', 'barrel'),
    'goat_form': ('horns', 'beard', 'bearded'),
    'hare_form': ('ears',),
    'bat_form': ('leathery', 'fingers'),
}
MOTION_WORDS = {
    "still": ("motionless",), "clamped": ("clamped", "shut"), "glide_slow": ("creeps", "creeping", "glide", "gliding"),
    "sidle": ("sidles", "sidling", "scuttles", "scuttling"), "jet": ("darts", "jets"), "pulse": ("pulses", "pulsing", "drifts", "drifting"),
    "wriggle": ("writhes", "wriggles", "writhing", "wriggling"), "swim_dart": ("darts", "flick"), "undulate": ("undulates", "curves"),
    "lumber": ("hauls", "hauling", "heaves", "lumbers", "dragging"), "run_stop": ("runs", "running"), "roll": ("rolls", "rolling"),
    "sway": ("sways", "swaying", "fingers"),
    "hover_dart": ("hovers", "hovering", "darts"), "flutter": ("flutters", "fluttering", "settles"), "spring": ("springs", "springing", "leaps"),
    "shuffle": ("shuffles", "shuffling", "snuffling"), "bound": ("bounds", "bounding"), "soar": ("glides", "gliding", "soars", "soaring"),
    "wade_sweep": ("wades", "wading", "sweeping"), "skim": ("skims", "skimming"), "drift": ("drifts", "drifting"),
    "pour": ("pours", "flows", "flowing"), "walk_slow": ("walks", "walking", "stilted"), "skitter": ("skitters", "skittering"),
    "lie_flat": ("lies", "waving"),
    "browse": ("steps", "browses"), "clamber": ("clambers", "clambering"),
    'crawl': ('crawls', 'crawling'),
    'sway_twig': ('sways', 'swaying'),
    'loop': ('arches', 'loops', 'looping'),
    'fly_straight': ('buzzing', 'flies'),
    'swoop': ('swoops', 'swooping'),
    'hop': ('hops', 'hopping'),
    'burst': ('bursts', 'clatter'),
    'peck_walk': ('pecks', 'pecking'),
    'flit': ('flits', 'flitting'),
    'root': ('roots', 'rooting'),
    'skate_surface': ('skates', 'skating'),
    'row_swim': ('rowing', 'rows'),
    'climb_wet': ('climbs', 'climbing'),
}
# the body-part nouns of SIZE_BANDS, by band; the bands from 'about as long as you are' up have no word he would use
SIZE_WORDS = {1.0: ("speck", "fingernail"), 2.5: ("thumbnail",), 5.0: ("thumb",), 10.0: ("palm",), 20.0: ("hand",),
              40.0: ("forearm",), 90.0: ("leg",)}
COVERING_WORDS = {
    "ridged": ("ridges", "ridged", "ridge", "ribbed"), "spined": ("spines", "spined", "spiny", "spikes", "prickly"),
    "plated": ("plates", "plated"), "warty": ("knobbled", "warty", "knobbly", "lumpy"),
    "furred": ("fur", "furred", "furry", "coat"), "scaled": ("scales", "scaled", "scaly"), "leathery": ("leathery",),
    "slimy": ("slimy", "slime"),
    "hairy": ("hairs", "hairy", "hair"), "feathered": ("feathers", "feathered"), "bristled": ("bristles", "bristly", "bristled"),
}
# nouns of the shore's SCENERY: a clause that names one is a look at that thing (the world's own shell/stone/weed/float text answers it);
# creatures are met through the place looks (P3) or by describing them without these words.
SCENERY_WORDS = frozenset("shell shells shingle stone stones pebble pebbles gravel driftwood log float net glass bottle kelp weed seaweed wrack "
                          "bone feather sand-glass".split())
_STOP = frozenset("the a an of in on at to and or with that this from its it as is are was be by for into onto over under near some "
                  "thing things creature animal there then than small little big large body bodies one two three about long wide".split())
_LOOK_CLAUSE = re.compile(r"(?<![\w-])(?:look(?:s|ed|ing)?|watch(?:es|ed|ing)?|study|studies|gaze|gazing|glance|examine|inspect|peer(?:ing)?|"
                          r"see|observe|observing|notice)(?![\w-])([^.!?;\n]{0,70})")


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z]+", _fold(text))


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def _same_word(a: str, b: str) -> bool:
    sa, sb = _stem(a), _stem(b)
    return sa == sb or (len(sa) >= 6 and len(sb) >= 6 and sa[:6] == sb[:6])   # 6: 'heavy' is not 'heaves', 'stars' not 'starfish', 'stream' not 'streaked'


def _content(*phrases: str) -> set[str]:
    return {t for p in phrases for t in _tokens(p) if len(t) >= 3 and t not in _STOP}


def attr_words(r: dict) -> dict[str, set[str]]:
    """The words by which a row can be described, grouped by intrinsic attribute. Built only from the row's own observable
    tuple (and the guess words of its body plan); never from a name."""
    o = r["obs"]
    colours = _content(COLOURS[o["colour"]][0], COLOURS[o["colour2"]][0] if o.get("colour2") else "") - {"glass", "dull"}
    pat = {o["pattern"]} - {"plain", "two_tone"}
    shape = set(SHAPE_WORDS.get(o["shape"], ()))
    if ALLOW_GUESS_WORDS:
        shape |= set(GUESS_WORDS.get(o["shape"], ()))
    size = set(next((w for hi, w in SIZE_WORDS.items() if o["size_cm"] < hi), ()))
    motion = set(MOTION_WORDS.get(o["motion"], ()))
    cover = set(COVERING_WORDS.get(o["covering"], ()))
    counts = {NUM[n] for n in (o.get("counts") or {}).values()}      # the NUMBER only: "legs" alone is not a count
    out = {"colour": colours, "pattern": pat, "shape": shape, "size": size, "motion": motion, "covering": cover, "counts": counts}
    return {k: v for k, v in out.items() if v}


def score_clause(words: dict[str, set[str]], clause: str, scenery: frozenset | None = None) -> tuple[int, int]:
    """(distinct attributes matched, total words matched) for one look clause; attributes is 0 unless at least one matched
    attribute is STRONG (STRONG_ATTRS). A word is claimed by the FIRST attribute that has it ('arms' alone is one attribute, not
    a shape and a count)."""
    toks = [t for t in _tokens(clause) if t not in _STOP]
    if (SCENERY_WORDS if scenery is None else scenery) & set(toks):
        return 0, 0       # the shore's own things (dead shells, stones, weed, floats) are answered by the scenery look, not by a creature
    used: set[int] = set()
    attrs = hits = strong = 0
    for name, vocab in words.items():
        got = [i for i, t in enumerate(toks) if i not in used and any(_same_word(t, v) for v in vocab)]
        if got:
            attrs += 1
            hits += len(got)
            strong += name in STRONG_ATTRS
            used.update(got)
    return (attrs if strong else 0), hits


def look_clauses(raw: str, target: str = "") -> list[str]:
    """The stretches of his own words that follow a look verb (70 characters), plus the resolved target keyword. The whole
    thought is never scored: a long thought that mentions cream and sand is not a look at a pipi."""
    out = [m.group(1) for m in _LOOK_CLAUSE.finditer((raw or "").lower())]
    if target:
        out.append(str(target).lower())
    return [c for c in out if c.strip()]


def current_standpoint(place: str = "shore") -> str:
    """Where he stands on the shore, READ-PURE (no adoption writes): a hand-set standpoint under 15 minutes old
    (shore_life.json _sp), else locomotion.peek(), else the geometry's default. Always a key of shore.json's standpoints."""
    known = _lay(place)["standpoints"]
    import json as _json
    if place == "shore":
        try:
            from core import shore_life as _sl
            d = _json.loads(_sl._F.read_text(encoding="utf-8"))
            if d.get("_sp") in known and time.time() - float(d.get("_sp_ts", 0)) < 15 * 60:
                return d["_sp"]
        except Exception:
            pass
    try:
        from core import locomotion as _loco
        p = _loco.peek() or {}
        if p.get("place") == place and p.get("standpoint") in known:
            return p["standpoint"]
    except Exception:
        pass
    return _lay(place).get("default_standpoint") or next(iter(known))


# ── P3: finding them by looking at the PLACE ─────────────────────────────────────────────────────────────────
# A described look needs him to know what to say; this is how he comes to know. A look at the pool, the sand, the rocks, the
# tideline, the sea, the dunes or the driftwood is answered as before and then CONTINUES with what is actually there to be seen from
# where he stands: a row is shown only if it is present, its zone is open, the visibility roll (seeded per ten-minute bucket, so
# repeated looks agree) lets him see it, and perceive() resolves it at tier form or better. At most MAX_PER_LOOK rows, each as
# the same composed line a described look gives (no name, no hint, no 'look closer'). Shadow-first behind "shore_bestiary_discover".
MAX_PER_LOOK = 2
TARGET_ZONES = (
    ({"pool", "pools", "rockpool", "rockpools", "rock-pool", "rock-pools"}, ("pool",)),
    ({"rock", "rocks", "bedrock"}, ("pool", "mussel_shelf", "rock_shelf")),
    ({"shelf", "mussel", "mussels", "reef"}, ("mussel_shelf", "rock_shelf")),
    ({"stream", "estuary"}, ("stream_mouth",)),    # J-3486: the mouth is a place a look can name (D-0651); bare "mouth" is NOT here (the cave has one)
    ({"sand", "flat", "flats", "sandflat"}, ("flat",)),
    ({"tideline", "shore", "beach", "strand", "shingle", "stones"}, ("tideline", "shingle")),
    ({"sea", "ocean", "water", "waves", "surf"}, ("surf", "offshore")),
    ({"dune", "dunes", "marram", "grass"}, ("dune",)),
    ({"driftwood", "log", "wood"}, ("driftwood",)),
)


def discover_live(place: str = "shore") -> bool:
    """Hot flag data/life_flags.json "shore_bestiary_discover" (DEFAULTS TO "shore_bestiary" when absent): OFF = shadow (logged as
    would_answer, nothing shown)."""
    return _flag(f"{place}_bestiary_discover", place)


def discover_zones(target: str, place: str = "shore") -> tuple:
    """The zones a look at this target takes in ((), for a target that is not a place of the shore's life). The FIRST place word wins,
    in TARGET_ZONES order -- the pools before the rocks, as the shore's own look treats 'rock pools' (sensorium._shore_look)."""
    toks = set(re.findall(r"[a-z]+(?:-[a-z]+)*", _fold(target)))
    for words, zones in (PLACES[place]["targets"] if place in PLACES else TARGET_ZONES):
        if toks & words:
            return tuple(zones)
    return ()


def discover(target: str, place: str, now: float | None = None) -> list[dict]:
    """[{'row', 'pv'}] for the rows a look at this place-target shows him, at most MAX_PER_LOOK. Deterministic per ten-minute
    bucket. [] when nothing registered, the target is not a place of the shore's life, or nothing is there to be seen."""
    from core import life as _life
    now = time.time() if now is None else now
    if place not in PLACES:
        return []
    zones = discover_zones(target, place)
    if not zones:
        return []
    sp = current_standpoint(place)
    night = _life._phase(now) == "night"
    bucket = int(now // BUCKET_S)
    found = []
    for r in _life._ROWS.values():
        if not r.get("obs") or place not in (r.get("places") or {}) or r.get("zone") not in zones:
            continue
        if _life.activity(r, place, now) < _life.PRESENT_AT:
            continue
        if random.Random(f"shore_discover:{bucket}:{r['key']}").random() >= _life.visibility(r, place, now):
            continue
        pv = perceive(r, sp, now, night=night)
        if pv["visible"]:
            found.append({"row": r, "pv": pv, "order": random.Random(f"shore_discover_order:{bucket}:{r['key']}").random()})
    found.sort(key=lambda f: f["order"])
    return [{"row": f["row"], "pv": f["pv"]} for f in found[:MAX_PER_LOOK]]


def described(target: str, raw: str, place: str, now: float | None = None) -> dict | None:
    """The row (if any) that his look describes, present and resolvable from where he stands. None = not ours; the look falls
    through. {'row', 'pv' (the perceive() result), 'clause', 'attrs'}. Fail-open; a refused non-live write is re-raised by the caller's
    own convention (this function writes nothing)."""
    from core import life as _life
    now = time.time() if now is None else now
    cands = [r for r in _life._ROWS.values() if r.get("obs") and place in (r.get("places") or {})]
    if not cands:
        return None
    clauses = look_clauses(raw, target)
    if not clauses:
        return None
    best = None
    for r in cands:
        if _life.activity(r, place, now) < _life.PRESENT_AT:
            continue
        words = attr_words(r)
        for c in clauses:
            attrs, hits = score_clause(words, c, (PLACES.get(place) or {}).get("scenery"))
            if attrs >= MIN_ATTRS and (best is None or (attrs, hits) > best[0]):
                best = ((attrs, hits), r, c)
    if best is None:
        return None
    (attrs, _), r, clause = best
    pv = perceive(r, current_standpoint(place), now, night=_life._phase(now) == "night")
    if not pv["visible"]:
        return None
    return {"row": r, "pv": pv, "clause": clause, "attrs": attrs}


# ── the leak test: the world never names ─────────────────────────────────────────────────────────────────────
# Common names (English and te reo) of the 100 in docs/staged/shore_creatures.md. A word that merely names a body part,
# a colour or a material (shell, claw, arms, fur) is NOT here; a word that names a kind of creature is.
BESTIARY_NAMES = (
    "katipo", "wolf spider", "tiger beetle", "sand scarab", "scarab", "rove beetle", "earwig", "sandfly", "mosquito",
    "boulder copper", "copper butterfly", "cave weta", "weta", "tokoriro", "paper wasp", "wasp", "shore skink", "skink",
    "norway rat", "rat", "house mouse", "mouse", "hedgehog", "stoat", "banded dotterel", "dotterel", "tuturiwhatu", "godwit",
    "kuaka", "royal spoonbill", "spoonbill", "sooty shearwater", "shearwater", "titi", "albatross", "toroa", "sea lion",
    "rapoka", "dolphin", "orca", "whale", "tohora", "pipi", "tuatua", "toheroa", "cockle", "tuangi", "green-lipped mussel",
    "kutai", "kuku", "mussel", "horse mussel", "hururoa", "rock oyster", "oyster", "tio", "scallop", "tipa", "paua",
    "cat's eye", "pupu", "limpet", "chiton", "oyster borer", "whelk", "sea hare", "blue dragon", "violet sea snail",
    "nudibranch", "sea slug", "octopus", "wheke", "squid", "paper nautilus", "nautilus", "cushion star", "starfish", "sea star",
    "eleven-armed starfish", "kina", "sea urchin", "urchin", "heart urchin", "sea potato", "sand dollar", "sea cucumber",
    "jellyfish", "moon jelly", "lion's mane", "man o' war", "by-the-wind sailor", "anemone", "crab", "papaka", "shrimp",
    "prawn", "lobster", "koura", "crayfish", "barnacle", "ragworm", "lugworm", "tubeworm", "fanworm", "bootlace worm",
    "triplefin", "spotty", "cockabully", "clingfish", "seahorse", "inanga", "whitebait", "eel", "tuna", "lamprey", "kanakana",
    "gambusia", "trout", "salmon", "mullet", "aua", "kanae", "garfish", "piper", "kahawai", "flounder", "patiki", "snapper",
    "tamure", "conger", "kingfish", "haku", "stingray", "eagle ray", "whai", "shark", "rig", "pioke", "great white",
    "sunfish",
)
# words that name a CATEGORY of creature: even these tell him what it is
CATEGORY_WORDS = (
    "fish", "bird", "insect", "beetle", "spider", "butterfly", "seal", "crustacean", "mollusc", "shellfish", "clam", "snail",
    "slug", "lizard", "mammal", "reptile", "worm", "jelly", "crab", "ray", "arachnid", "gull", "penguin", "mussel",
)
# `ray` is checked singular-only (leak_scan): the pattern vocabulary legitimately says "rays running out from one point".


def _fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def forbidden_terms(rs: list | None = None) -> set[str]:
    """Everything the world must not say: all 100 common names, the category words, and (for the rows given) their own
    species, book names and aliases."""
    out = {_fold(t) for t in BESTIARY_NAMES} | {_fold(t) for t in CATEGORY_WORDS}
    for pl in PLACES.values():
        out |= {_fold(t) for t in pl.get("names", ())}
    for r in rs or ():
        h = r.get("hidden") or {}
        out.add(_fold(str(h.get("species") or "")))
        out.update(_fold(str(n)) for n in (h.get("book_names") or ()))
        out.update(_fold(str(a)) for a in (r.get("aliases") or ()))
    out.discard("")
    return out


_LEAK_RX: dict = {}


def _leak_rx(terms) -> "re.Pattern":
    """ONE compiled alternation per term set (a set of >500 per-term patterns overflows re's own cache and recompiles on every call: with the
    shore's 100 and the wood's 150 names that took minutes). `ray` is checked singular-only (the pattern vocabulary says 'rays')."""
    key = frozenset(terms)
    rx = _LEAK_RX.get(key)
    if rx is None:
        alts = sorted((t for t in key if t != "ray"), key=len, reverse=True)
        rx = re.compile(r"(?<![a-z0-9])(?:" + "|".join(re.escape(t) for t in alts) + r")(?:s|es)?(?![a-z0-9])") if alts else re.compile(r"(?!x)x")
        if len(_LEAK_RX) > 8:
            _LEAK_RX.clear()
        _LEAK_RX[key] = rx
    return rx


def leak_scan(text: str, terms: set[str]) -> list[str]:
    """The forbidden terms found in `text` as whole words (an optional plural s/es), accents folded. A fast path (one compiled alternation) answers
    the common 'nothing' at once; only when something matches does it name every term that does."""
    t = _fold(text)
    if not _leak_rx(terms).search(t) and not ("ray" in terms and re.search(r"(?<![a-z0-9])ray(?![a-z0-9])", t)):
        return []
    hits = []
    for term in sorted(terms):
        if term not in t:
            continue
        plural = "(?:s|es)?" if term not in ("ray",) else ""
        if re.search(r"(?<![a-z0-9])" + re.escape(term) + plural + r"(?![a-z0-9])", t):
            hits.append(term)
    return hits


def emitted_strings(r: dict) -> list[str]:
    """Every string the world can produce for a row: its feature/miss/absent lines AND the composer at every tier x night."""
    h = r.get("hidden") or {}
    out = []
    out += [v for v in (h.get("feature") or {}).values() if isinstance(v, str)]
    out.append(str(h.get("miss") or ""))
    out += [v for v in (h.get("absent") or {}).values() if isinstance(v, str)]
    o = r.get("obs")
    if o:
        for tier in TIERS[1:]:
            for night in (False, True):
                out.append(compose(o, tier, night))
        out += [f"It is {w}, {pace_word(d)}." for w in _SECTOR.values() for d in (1.0, 3.0, 8.0, 20.0, 50.0)]
    return [s for s in out if s]


PLACES["shore"] = {"layout": "shore", "zones": ZONES, "targets": TARGET_ZONES, "frame": FRAME, "scenery": SCENERY_WORDS, "names": ()}
