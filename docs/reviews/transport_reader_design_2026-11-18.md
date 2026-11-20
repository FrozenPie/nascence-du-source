# Transport surprise-nudge reader: design (J-4340, 2026-11-18)

Read-only design. No core edits. Step 5 is neither promoted nor retired.

## What the data says (data/transport_shadow.jsonl, scratch read 2026-11-18)
- 54,326 rows, all `live:false`, 66 distinct days. `fired` means only that dispatch_tick() had a winning candidate that tick
  (core/transport_manager.py:244); non-fired rows carry no kind. Fired: 17,980 = drought 13,440, spike 3,053, novelty 487.
- The headline 13.4k drought / 3k spike is dominated by the level-trigger era (before the D-0294 edge trigger, 2026-09-28):
  clock_tick:study drought 4,364, life:cat:study 4,158, wood_pigeon 1,924. That is the commonplace repeating, the opposite of the intent.
- Since 2026-10-15 (edge trigger, post D-0409): 22,321 ticks, 493 fires (2.2%), about 19/day mean, max 263 on a novelty-burst day.
  Kinds: novelty 331, drought 155, spike 7. Families: life 279, cat 116, sound 84, world 14. Top repeats are only 5-9 each, so no domination.
- Spike is nearly silent (7 in 26 days); novelty is mostly first sightings of new lines (new cat states, new life lines).
- A person would call most novelty fires surprising only the first time; many are bookkeeping (a new cat-state label), not a percept.
  Drought on rare cat states ("had_enough@away_hunting") is weak: absence of something that seldom happens is not surprising.
  Drought on a normally frequent sound or a world light_band is the real "the usual thing did not come" signal.

## Candidate delivery forms
1. Felt-recall dimension (the D-0294 consumer; `verdict()` already built, J-1433). The verdict gates a recall tug for a world:<dim>:<place> line.
   World-answers: yes, it only biases which memory surfaces; no text, goal or hint. Dosed coupling: fits, because it is one dimension inside an existing channel.
2. Diegetic noticing line: one plain percept ("the clock has stopped ticking in the study") through the normal perception path,
   at most one per day, only for drought on a high-frequency line, spike with ratio over 10, or a first-ever sound/life novelty.
   World-answers: yes if worded as a fact of the room with no valence, instruction or question. Dosed: a per-day cap plus per-line cooldown.
3. Nothing else. No gauge, no readout, no goal (D-0434): Du must not be told "this was surprising".

## Recommendation
Build form 2 as a shadow-first reader (log what it would say, no delivery), keep form 1 as is, drop all else.
Filter: ignore novelty from cat:state:* and label-only lines; drought requires gap_ema under 6 h and ratio at least 5; spike ratio at least 10;
cap 1/day, 24 h per-line cooldown. Expected volume from the since-10-15 data: well under 1/day after filtering (to be measured in the shadow).
Open founder call: should the noticing line enter perception at all (form 2 live), or stay in felt recall only? Not decided here.

Confidence: counts verified (script run on the file); the "would a person call it surprising" judgement is inferred from line ids and ratios, not from reading Du's context.
