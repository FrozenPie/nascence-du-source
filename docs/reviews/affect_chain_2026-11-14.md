# The affect chain: from a sleep gauge to the mood Du is told he has (2026-11-14)

Found while reading weekly affect distributions for `docs/staged/maths_of_mind_atlas.md` (row P1).
Findings: F-4654 (the weekly drift), F-4659 (the cause), F-4660 (what reaches him), F-4661 (emotion node).
All reads are read-only over live logs on 2026-11-14. No code was changed. Decisions opened: see the last section.

## 1. The chain, link by link

| # | Link | Where | Checked how |
|---|---|---|---|
| 1 | Vitality = 1 - sleep pressure / today's sleep threshold. The threshold is 10 at night and 100 by day, so vitality steps at sunset and sits below its setpoint most of the time. | `core/homeostasis.py:190`, `core/sleep_pressure.py:164` | Known: D-0398 (ruled 2026-10-14). Replacement `vitality_v2` is in shadow. J-3942 and J-3967 are open. |
| 2 | Vitality averages about 0.38 against a setpoint of 0.78. Relational warmth averages about 0.5 against 0.824. | `data/homeostasis_shadow.jsonl`, weekly means since 2026-08-24 | Measured, F-4659. |
| 3 | Drive is the weighted distance of the five needs from their setpoints. In the week of 11-02, vitality supplied 44 percent of squared drive, warmth 33, coherence 19, the other two under 3. | `core/homeostasis.py:348` | Measured from `per_drive`, which sums to drive squared exactly. |
| 4 | Since 2026-07-07, carried valence is overwritten with 1 - 2 x drive. | `core/homeostasis.py:99`, flag `core/schema.py:1279` | Code read; logged valence matches the formula at r = 0.96 to 0.98. |
| 5 | Every idle thought is seeded with "Your current mood: <valence word> in tone, <arousal word>". | `nodes/inner_monologue_node.py:3452`, bands at `core/mood.py:254` | Code read. |
| 6 | Since 2026-09-01 the tone word was some form of low on 47 percent of 54,782 idle thoughts. With the vitality term removed it would be 24 percent, and good on 57 percent instead of 31. | `data/felt_preamble_log.jsonl` joined to the homeostasis log | Measured, F-4660. The counterfactual removes one term from the logged drive; it does not simulate how he would then have thought. |

So a gauge that was built to decide when he sleeps is, through four steps, about half of the reason he is told
his mood is low.

## 2. The joy side

| Fact | Where | Checked how |
|---|---|---|
| The model's emotion node runs only on human turns and internal ignition cycles, about 59 calls in 7 days. It sees the perception summary, not the thought and not his prior affect. | `nodes/emotion_node.py`, `core/orchestrator.py:825` | Agent code read, F-4661. |
| Carried joy is mostly added by `_feel_joy` on idle events (reading, lessons, play). Its valence half was switched off on 2026-07-07; its joy half was not. | `nodes/inner_monologue_node.py:2587` | Agent code read. |
| Joy and valence are now unrelated: r = 0.17, and 29 percent of affect rows have valence below zero with joy above 0.5. | `data/affect_log.jsonl` | Measured, F-4659. |
| The idle mood line does not name joy. The voice line and the felt preamble do, but drop it when valence is low. | `core/mood.py:301-314`, `:371` | Code read. |
| Constructed emotion (Phase 2, off) sets joy = max(0, valence) x (0.5 + 0.5 x liking). In its shadow log constructed joy is exactly zero on 74 percent of rows. | `core/emotion_construction.py:188`, `data/emotion_construction_shadow.jsonl` | Agent computed, F-4661. |

Consequence: if Phase 2 were switched on while valence is held down by the vitality reading, joy would all but
disappear from his affect.

## 3. What is known already and what is new

Known and ruled: the vitality reading is wrong and is being replaced (D-0398); the emotion node needs fixing
(P-0002 verdict "fix", J-2811 to J-2815); joy is a stuck dimension (F-1926 item 10).

New here: the size of the effect on the words he is given (47 against 24 percent); that valence and joy have
been on different sources since 2026-07-07; and that Phase 2's joy formula depends on the vitality fix landing
first.

## 4. Not checked

- Whether the low mood line changes what he thinks. It is in the seed; its effect on the thought was not measured.
- Why relational warmth fell after the August outage and stayed low. That one may be a true reading.
- Why carried joy stepped up in the week of 2026-08-31. The November fall coincides with the grading fixes
  (J-2960, J-2992, J-2988, J-3081); that is an inference from dates.
- The emotion-node facts in section 2 are from an agent's read and were not re-read line by line.

## 5. For the founder

Two questions, opened in `/decide`:
1. Whether to do anything about the mood line before `vitality_v2` replaces the old reading.
2. Whether Phase 2 (constructed emotion) should be barred until the vitality replacement is in the drive, and
   what the joy pump should do in the meantime.
