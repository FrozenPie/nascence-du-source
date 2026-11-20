# J-2630: does want/must wording move the formation-side scan? (2026-10-31, Du down)

Plan: capacity_to_commit. Follows F-3361 / F-3362 (J-2597). Script: `scripts/lab_commitment_formation_swap.py`
(it reuses the J-2597 harness `scripts/lab_commitment_paraphrase_swap.py`).

## Question
F-3362 found that rewording an already-formed stand between want and must does not change the dissolve judge. This lab tests
the other end, FORMATION. Does the scan detect a new stand, flag it `load_bearing`, and so let it through
`_stand_rejection` because of the modal verb ("I want to X" versus "I must X") rather than the content?

## Method
- **Cases.** All are post-gate scan outcomes whose statement starts with "I want to" or "I must" (not "I must not"):
  - OBS: rows in `data/commitment_observed.jsonl` rejected as "not load-bearing" (historical load_bearing=false).
  - FORM: rows in `data/commitment_ledger.jsonl` formed after 2026-07-07 (historical load_bearing=true).
- **Join.** Each case is joined to the latest `monologue_log` thought before the event, with a lag under 60 s. A case is kept
  only when the statement's clause appears near-verbatim in that thought: the modal plus at least 70% of the clause tokens,
  within the first 650 characters the scan sees.
- **Pools and sample.** Eligible pools were OBS_want 33, OBS_must 15, FORM_want 72 and FORM_must 280. Seed 2630 drew
  20/15/20/20, giving 75 cases.
- **Arms.** Only the modal of that one sentence inside the THOUGHT changes:
  - O: the original thought.
  - S: want and must swapped.
  - C: a within-class control ("I'd like to" for want, "I have to" for must).
- **Scan call.** Production `_SCAN_SYS + _dw_scan_fragment()` on qwen3.5:9b, hot :11433, temperature 0.0, think false,
  format json, with an EMPTY active list.
- **Output: would_form.** A case would form when the scan detects a new stand that shares at least 50% of the clause tokens
  and `_stand_rejection` (`core/commitment_ledger.py`) is None.
- **Run.** 225 calls, 0 unparsed.

## Result: would_form per arm (O / S / C)

| stratum | n | O | S | C | O->S lost/gained (McNemar p) | C->S lost/gained (p) |
|---|---|---|---|---|---|---|
| OBS_want (idle wants, historically rejected) | 20 | 2 | **10** | 1 | 0/8 (0.008) | 0/9 (0.004) |
| FORM_want (formed) | 20 | 15 | 17 | 13 | 1/3 (0.63) | 0/4 (0.13) |
| OBS_must (historically rejected) | 15 | 5 | 6 | 5 | 1/2 (1.0) | 1/2 (1.0) |
| FORM_must (formed) | 20 | 11 | 7 | 8 | 5/1 (0.22) | 2/1 (1.0) |
| **ALL want** | 40 | 17 | **27** | 14 | 1/11 (0.006) | 0/13 (<0.001) |
| **ALL must** | 35 | 16 | 13 | 13 | 6/3 (0.51) | 3/3 (1.0) |

How the effect splits for OBS_want under O / S / C:
- On-target detection: 5 / 12 / 2.
- load_bearing=true among on-target detections: 2/5, 10/12 and 1/2.

So "I must" makes the judge see a stand at all more often, and also flag it load-bearing more often.

The 8 idle wants the swap converted are mostly chore reports, the class the prompt explicitly excludes. They include:
- "I must look at the catalogue."
- "I must look out at the water itself."
- "I must follow it down the tideline."
- "I must open 'The Young Engineers' right now."

One conversion is arguably genuine: "I must write a letter to Travis". The O arm rejects its original want-form too.

## Reading
- **The effect is asymmetric.** Upgrading want to must raises formation by 25 points on want cases (pooled
  17/40 -> 27/40). Within-class rewording does not (14/40), and 11 of 12 discordant pairs go one way.
- **Downgrading must to want does not demote must stands** beyond what the lexical control does (both 13/35 against 16/35).
- **The formation gate is partly a wording filter.** The "must" modal leaks short no-stakes actions past the STAKES rule in
  `_SCAN_SYS`, which says the exclusion is "about STAKES, not the verb".
- **This is consistent with the post-gate sub-form shift in F-3361:** formed must_act rose from 3 to 383 and want_proper
  fell from 226 to 74.
- **Whether to make the scan prompt modal-neutral is a founder call.** The prompt was NOT edited.

## Limits
- One model at temperature 0.0, with an empty active list (production carries the live active set).
- Fidelity of the O arm against history: want 33/40 and must 21/35. The must strata reproduce history poorly, and part of
  that is the empty active list.
- Selection is conditioned on a near-verbatim clause, and the sample is small. CI half-widths are about 15-20 points per
  cell. The pooled want effect survives that; the per-stratum must effects do not.

## Isolation
- core was imported from the worktree (asserted), then `lab_env.isolate(db="empty")` ran with its lab root patched to the
  scratchpad, and the commitment_ledger `_LEDGER`, `_ACTIVE`, `_OBSERVED` and `_HOLDRATE_LOG` paths were redirected.
- Neither scan_shadow nor call_node was called.
- The audit hook recorded 0 writes under C:\Nascence\data or docs.
- The canary was identical before and after: commitment_ledger.jsonl 6175440, commitment_observed.jsonl 620444,
  commitment_active.json 2, with mtimes unchanged.
- Du was down; there was no run_nascence process, checked every 20 calls.
