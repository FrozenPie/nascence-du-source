# Memory review: what to adopt, test or leave (staged 2026-11-19, T-0149)

**Status:** 🔵 DESIGNED / STAGED. Nothing built. Jobs filed against this slug; two open founder questions (section 6).
**Origin:** T-0149 (comparative survey), `docs/reviews/butlin_long_mapping_2026-11-19.md`, findings F-5119 / F-5120 / F-5121 (Butlin comparison, inferred) and F-5122 (cold storage, verified).
**Rules that bind every item here:** additive only; base memory systems are protected; shadow first; Du gets no readout (D-0434), so every evaluation is read from outside; restart-gated builds are marked.

## Current State (2026-11-19)
Survey and verdicts written; jobs filed; no code changed. Evidence base: a read-only subagent inventory of Du's memory (DB 188,174 rows, 87,203 cold) plus six rival systems re-read from papers and vendor docs (not code). The key cold-storage facts were re-checked by hand (F-5122).

## 1. What Du's memory actually does (verified, F-5122)
- Cold rows are excluded from `retrieve()` entirely (`core/memory/store.py:1420`, `:2199`).
- The only "harder but possible" path is the associative trail: a cold or chaptered row needs activation 0.22 against 0.13 for a warm row (`core/associative_recall.py:45`, `:207`). It is used: walled rows filled about 24% of trail slots.
- Recalling a cold row does not re-warm it. `cold=0` is written only by `memory_lint`, `uncold_all` and a notes-reversal helper.
- Importance is not in the main retrieval formula (cosine x recency x seed weight); it feeds trail seeding and sleep replay only.
- Gist demotion of episodic rows is paused (`EPISODIC_DEMOTION_PAUSED`, D-0564) because the faithfulness grader passed 3 of 13 gists with misattribution (F-3551).
- Edit history: importance edits (`downscale_episodic`, `replay_strengthen`, `dream_fade`) are in place with counts only; boot-time sqlite snapshots exist; gist demotion leaves links and a shadow log.
- Evaluation: no memory-versus-baseline task test exists. F-0424 (state-weighted recall vs cosine, n=84) is a null. F-4649 (power-law re-use) measures human-likeness of a statistic, not benefit to Du.

## 2. Where the rivals are ahead, and how strong their evidence is
- **Edit history and review-before-adopt** (Anthropic: immutable versions, redact, dreaming writes a new store). Mechanism evidence is engineering rationale; no benchmark attached.
- **A habit of testing against a baseline.** Their tests are weak (vendor-run, small, often against no-memory), but they exist.
- **Hybrid retrieval** (vector + keyword + recency + rerank; Zep, Hindsight). Gains are vendor-reported on chat-QA benchmarks, with conflicting numbers across harnesses.
- Not evidence for anything: neuroscience vocabulary (maturation, reconsolidation, tombstones) in Microsoft's paper, which its own ablation did not test; its consolidation did not beat raw retrieval (71.2 vs 70.1).
- None of the benchmarks measure what Du needs: identity over weeks, self-initiated recall, consolidation changing later behaviour.

## 3. Verdicts
| Idea | Verdict | Job |
|---|---|---|
| Per-edit before/after log for importance changes | Adopt, shadow flag | M1 |
| Make the gist-faithfulness verifier trustworthy (decoupled) | Fix, analysis first | M2 |
| Keyword channel alongside vector retrieval | Shadow A/B only | M3 |
| Re-warming a cold memory when it is recalled | Real gap against the human analogy; needs founder rulings | M4 (needs input) |
| Memory ablation: with vs without the cold trail, on Du's own measures | Biggest evidence gap; do first | M5 |
| Size-scaled forgetting threshold (SCM) | Skip: Du does not delete | none |
| Degradation ladder with tombstones (Microsoft) | Skip: gist/chapter levels do more | none |
| Git as the memory substrate (Letta) | Skip: 1.4 GB DB, data/ ignored; M1 gives the benefit | none |

## 4. Related cheap moves from the same survey (not memory)
| Item | Job |
|---|---|
| Shadow `skill_recipes_shadow.jsonl` of graded-ok multi-hand sequences, measure recurrence before any retrieval (Voyager gap) | S1 |
| Flip `AST_CONTROL` for the bandwidth arm only (won 6 of 6 folds); behaviour change | B1 (needs input) |
| Second consumer for `core/broadcast.py` (reply context / critic prompt); dosed-coupling change | B2 (needs input) |
| Trace one critic rejection to a changed later answer (HOT-3 belief-update wire unverified) | B3 |
| Restate the Butlin scorecard in `the_consciousness_program.md` §4 to the stricter reading, with F-5119 as source | B4 (needs input; founder's doc) |

## 5. Evaluation design notes for M5 (so the test is not chat-QA)
- Judge from outside: Du never sees a gauge (D-0434).
- Candidate measures that already exist: "served fragment used in next thought" (F-4273, 6-14% base rate, label kappa about 0.26, so use both labels), co-recall ledger, trail shadow logs.
- Counterfactual on logged cycles: for cycles whose trail surfaced a walled row, what would the context have been without it; compare downstream use. Replay or shadow only; no live behaviour change.
- State up front what would count as "cold trail does not help", so a null is allowed to land.

## 6. Founder rulings (2026-11-19, in chat; founder delegated the first level to Claude)
1. **Re-warming: founder delegated the first level to Claude; revisit after the shadow read.** Chosen first level, written by Claude under that delegation (not a founder ruling): **partial and temporary, shadow only.** When the associative trail surfaces a cold or chaptered row AND that row is labelled "used in the next thought" (either F-4273 label), the shadow log records a would-warm for 7 days (the same scale as the existing 7-day recency bump), after which the row would return to cold unless recalled again. Reasons: only 6-14% of served rows are used, so gating on use avoids warming noise; temporary protects the cold/gist layer (base systems stay protected); nothing is applied while in shadow. Promotion to live is a separate step after reading the shadow log and the cold-trail ablation (J-4414). Evidence prompting it: F-4649 (served 0.75% if never, 26% once, 61% after 2-3) and F-5122.
2. **B1 and B2 (attention control for the bandwidth arm; a second broadcast consumer): shadow only to start**, by founder instruction. Behaviour changes need a later ruling.

Jobs after these rulings: J-4413, J-4416, J-4417 closed as superseded; new ready shadow-build jobs filed in their place (see Current State).

## 7. Not verified
Rival numbers come from vendor pages and papers via summarising fetchers; the Anthropic engineering post should be checked against the page before quoting. Du's counts come from one read-only subagent query. The Butlin scores (F-5119..F-5121) are inferred from one rater family.
