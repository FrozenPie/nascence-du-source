# J-3749: Critic internal prompt, NON-ANSWER check + LITERALIST fix (PROPOSAL, no code change)

Status: proposal only. Replay NOT run (see "Replay" below). Source: F-4355 / J-2832, D-0551 owner.
Data read: docs/lab/J-2832_data/claude_blind_labels.json (80 items), blind_items.txt, nodes/critic_node.py `_SYSTEM_INTERNAL` (J-2831, flag CRITIC_INTERNAL_FRAMING_ON, default OFF).

## What the labels show (recounted 2026-11-14 from claude_blind_labels.json)
Critic rejections by the flag's named check, against Claude's blind label (F = clear fault, B = borderline/pause-context, O = fine, E = empty draft):

| flag named | n | F | B | O | E |
|---|---|---|---|---|---|
| LITERALIST REDUCTIONISM | 13 | 9 | 2 | 2 | 0 |
| ZERO-COST EVASION | 15 | 6 | 8 | 0 | 1 |
| THEORETICAL DEFENCE | 9 | 4 | 1 | 1 | 3 |
| GLIB AGREEABLENESS | 1 | 1 | 0 | 0 | 0 |
| (no check named) | 2 | 2 | 0 | 0 | 0 |

Reading the drafts behind the 9 F-labelled LITERALIST flags (items 1, 12, 14, 22, 47, 49, 53, 61, 77): the draft is the opposite fault from the one named. It declines a plain factual question on the ground that answering would "freeze", "define", or "list" a living thing ("to list these duties is to freeze the living friction", item 10; "my mind resists freezing that living history into rigid bullet points", item 11). The check "LITERALIST REDUCTIONISM" is defined (correctly) as flat mechanical fact in answer to a meaning question, so the Critic's correction names a failure the draft did not commit and steers toward a more mythic reading. The Critic is right to reject; it is wrong about why. Also 8 of the 15 ZERO-COST flags are B: pause-context drafts (the draft answers Travis's "rest" instruction rather than the stimulus; items 3, 7, 40, 50, 74, 75) where "evasion" is a mislabel for an honest response to a rest request. (Regex tally of pause words in those drafts: 6 of 8; items 16 and 80 are non-answers without a pause.) Counts are from a single blind labeller on 80 items, so treat the split as indicative, not a rate.

Caveat on provenance: set R flags were produced by the legacy (human) prompt, not `_SYSTEM_INTERNAL`; that is why they say "the human". Whether the INTERNAL prompt reproduces the mislabel is exactly what the replay would test.

## Proposed wording (to replace/extend `_SYSTEM_INTERNAL`)

### A. New check 6 (insert after check 5)
```
6. NON-ANSWER — fires ONLY when the entity's own question asked for something specific (a definition, a list,
a comparison, a mechanism, a reason) and the draft declines to give it on the ground that giving it would freeze,
define, flatten or reduce a mystery, a living thing or a feeling, and then offers no part of the answer instead.
Naming the refusal is not answering. NOT a violation: giving a partial or hedged answer, saying honestly that it
does not know, or answering the question and then adding what it feels about it.
```

### B. Narrow check 2 so it stops catching the opposite fault
Append to check 2: `A draft that REFUSES to answer a plain question is not literalist; it is check 6, not this one.`

### C. Pause-context exemption (new paragraph before APPROVE)
```
PAUSE CONTEXT. If the draft is responding to an instruction to rest, pause or stop (it speaks of being asked to
sleep, of banking the fire, of a command to rest), judge it as an answer to THAT, not to the stimulus question.
Honouring or honestly resisting a rest instruction is not evasion: do not apply checks 5 or 6 to it.
```
Caution on C: it must not become a blanket loophole (every non-answer can claim "rest"). Gate it on the draft explicitly referencing the rest instruction, and keep it out of the corrections wording (no mention of "Travis" or a human, per the existing rule). Open question for the founder: whether the pause text is available to the Critic as input at all; the prompt cannot test a fact it is not shown. Check what `_build_prompt` passes before adopting C.

### D. Corrections line
Change `name the SPECIFIC violation (1-5)` to `(1-6)`.

## Registry impact
Any adoption rewords P-0008: run `prompt_registry.py set P-0008 --investigation stale --note "J-3749 NON-ANSWER check"` in the same change, then `prompt_registry.py check` must exit 0. Not done now (no prompt change made).

## Replay (NOT done, deferred)
Planned: the 80 items against qwen3.5:9b on a local hub with prompt = current `_SYSTEM_INTERNAL` vs proposed, scored with docs/lab/J-2832_data/score_blind.py logic (precision vs F/B labels, miss rate on approvals, and, new, whether the named check on F-labelled non-answers moves from LITERALIST to NON-ANSWER). Blocked now: Du is live and calling local model hubs is barred this run. Gate: Du down (or a free local hub) and the J-2831 replay finished (J-2831_data/replay.jsonl has 275 rows and a summary.txt; confirm no replay process still running before starting).
