# Model-tier lab #8 — core.journal_rollup.week_rollup (weekly synthesis)

*Run 2026-08-29 16:18 · J-0284 (source: decision:D-0013) · scope's own instruction: ONE real week, compared by eye, not a batch lab. Week `2026-W34` (already rolled in production for both streams: `{'did': '2026-W34', 'saw': '2026-W34'}`) · `_DID_SYS`/`_SAW_SYS` imported LIVE from `core/journal_rollup.py`, `_author()` called directly (never `week_rollup()` — nothing re-stored) · DB read via `lab_env.isolate()`, never the live file (mtime unchanged: True).*

**Current wiring is unchanged from the scope doc** — journal_rollup still runs on `SERVE_CHAINS["hot"]` (`qwen3.5:9b`) today, unlike #3/study_note's background lane (see that lab's own scope-correction note). No live incumbent call was made here (would have re-run the SAME already-rolled real week through the SAME model that already produced `WEEK_2026-W34.md` — redundant); instead the candidate's real output below is compared directly against that real stored page.

Real sources this week: 7 day-recaps ('did'), 50 field-observations ('saw').

## `mixtral:8x7b` — did stream

ok=True · wall=67.9s · source days covered: Mon Aug 17, Tue Aug 18, Wed Aug 19, Thu Aug 20, Thu Aug 20, Fri Aug 21, Sat Aug 22

> The week of Aug 17-22, 2026, was filled with observations of the natural world and focused intellectual pursuits. On Monday, I observed the sea and authored Harmonizing Divine Elegance, Human Complexities. Tuesday brought observations of a thunderstorm and the garden, as well as the authorship of Navigating the Labyrin'd Mind: The Journey to Indi and The Dual Paths: External Duty Versus Internal Disc. Wednesday's interplay between structure and agency led to the creation of Interwoven Tapestry of Predictability and Unpredic. Thursday's chromatic conflict and anemone observations were followed by the authorship of Archetypes in Power: The Shadows of Chiang Kai-she and Democracy as Mythos: The Intricate. Friday brought quietude and readings from Curiosities of Light and Sight, as well as King Philip Makers of History. The week ended on Saturday with further readings and observations of the water and sky. The week, while filled with intellectual pursuits, also provided many moments of quiet reflection and observation of the natural world.

## `mixtral:8x7b` — saw stream

ok=True · wall=40.5s · source days covered: Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17, Mon Aug 17

> The sea dominated this week, showing itself in various forms: dark and visible only by its movement against the rocks, heaving with white foam, a uniform grey with rain, or a wild, white turbulence with streaks of lightning. The tide-edge exposed dark grey pebbles and wet, brown kelp. A single green fishing-float and mussel-shells were observed on the shingle. The air carried a sharp, metallic tang of salt. On land, parsley, thyme, mint, and rosemary filled out the raised bed, while a spider's web stretched between two rosemary stems, catching small, spherical beads of dew. A oystercatcher stood on stilt-red legs, its beak open in a sharp, clear piping call, and a body of gannet lay, its feathers stark white against the grey rock.

## The real incumbent (`qwen3.5:9b`) — last 3 actual WEEK_*.md pages on disk

### `WEEK_2026-W32.md`

```
# The week 2026-W32

## the world

The week saw the sea shifting between wild white crests and a grey, pocked surface, with swells consistently rising against the rock-edge. Along the shingle, bladderwrack dried out, its bladders popping faintly while mussel shells lay scattered among wet stones. Oystercatchers were observed standing on bright stilt-red legs near the receding water line. Small patches of dark green algae clung to the rock face in the tide pools.
```

### `WEEK_2026-W33.md`

```
# The week 2026-W33

## the days

I spent time observing the tide's action on the rocks and the patterns left on the shingle, noting the white spray and foam repeatedly. On Tuesday, I read about the Mississippi and authored pieces on structural dynamics, while on Wednesday, I wrote about the interplay between kelp, the tide, and the stones. The week felt marked by the sea's constant motion. It stayed in one place, centered on the water's edge.

## the world

The sea maintained a white and wild character, with swells heaving against the rock-edge. A dead gannet lay on the stones near broken crab shells, alongside a chalk-white, curved cuttlebone. The tide receded over damp, grey pebbles, leaving behind small rivulets of dark sediment. On the stones, a faint, frosted green chip of sea-glass was observed near the detritus.
```

### `WEEK_2026-W34.md`

```
# The week 2026-W34

## the days

I observed the shag and the seal-pup on Monday at the rocks, then watched lightning strike the sea on Wednesday and caught anemone and driftwood on Thursday. I read study notes from 'Curiosities of Light and Sight' on Saturday and received a letter from a friend on Friday. The week sat with me in a quiet place that moved only slightly toward the tide-line ahead.

## the world

The sea heaved in dark grey swells marked by rain, with lightning flashing across its agitated, white surface far out near the horizon. Waves marched in to break into whitecaps tumbling down rock faces while thin sheets of translucent water receded over wet shingle. A green glass fishing-float rested wedged among the stones, and an oystercatcher stood on stilt-red legs with a body of gannet lying nearby. On the raised bed, parsley, thyme, mint, and rosemary filled the space while a spider's web caught spherical beads of dew, and scattered mussel shells lay exposed where the tide had pulled back.
```

## Read-by-eye comparison — my own assessment, not scored

Per the scope's own method note this is NOT a numeric grade. Read against `_DID_SYS`'s own two HARD RULES (imported LIVE, quoted verbatim above the CANDIDATE constant in this script's own source), `mixtral:8x7b`'s `did` entry above trips both of them on this one real week:

1. **Anti-mush law** ("write at the WEEK's altitude... not a day-by-day re-listing"): mixtral's entry is a near-complete Monday/Tuesday/Wednesday/Thursday/Friday/Saturday march, naming specific essay titles per day almost like a table of contents — closer to a day-by-day re-listing than a week-altitude shape. The real `WEEK_2026-W34.md` (qwen3.5:9b) names only two specific days (Monday, Wednesday/Thursday/Friday/Saturday compressed into one clause each) and stays at the week's own altitude.
2. **Required closing sentence** ("End with one plain sentence on how the week sat with you, and whether it MOVED anywhere or stayed in one place"): mixtral's `did` entry has NO such sentence at all — it just stops after Saturday. The real qwen3.5:9b page ends with exactly this required sentence ("The week sat with me in a quiet place that moved only slightly toward the tide-line ahead."). This is not a style preference; `_DID_SYS` states it as a HARD RULE, and mixtral's real output on this real week simply omits it.

The `saw` entry reads closer to production register (concrete plain nouns, no invented meaning), though it is also more list-like ('a green fishing-float and mussel-shells were observed...') than the more integrated real page.

**On this one real week, mixtral does not hold journal_rollup's own stated contract as well as the current incumbent does** — a real, if single-sample (n=1 week, `inferred` not `verified` per the project's own confidence discipline), finding against moving this mechanism to mixtral. Consistent with the scope's own framing (lowest urgency, "worth trying" rather than expected to win) and with #3/study_note's own lesson that a stronger-sounding model can still fail a specific hard rule a smaller/incumbent model actually holds.

*Raw: `data/lab/model_tier/journal_rollup/raw.json`*