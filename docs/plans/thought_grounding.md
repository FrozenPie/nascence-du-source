# Thought-Typed Grounding Routes — the plan (2026-08-16)

```plan-state
stage: built
phase: All three routes + method-book shelving built and live-tested 2026-08-16
verified: 2026-11-14
evidence_read: 2026-09-05
next: J-2615 re-reads R2 once 20 source=route2 asks accrue after restart
cluster: 2
```


**Founder + Claude.** Status: **BUILT 2026-08-16** (founder: "lets proceed") — all three routes +
method books, live-tested; latches activate at Du's restart. Build detail + the evidence-filter
iteration (panel deadlock → rule_detail; echo guards; honest-empty law) in AWAITING_EVIDENCE ★★ 08-16.

## Current State — verified 2026-11-14

- **2026-11-14**: J-3977: D-0758 built - Route 2 _evidence_recall now passes dedupe=True to evidence_recall.gather (as Follow Line). Test scripts/_test_J3977_route2_dedupe.py passes. Restart-gated; measure Route 2 duplicate rate after next boot.
- **2026-11-06** (F-4221): J-2796: Q&A cycle-summary rows that pass evidence (110 of 641 passes since 10-30) are Du's own replies (orchestrator _persist_cycle writes A: = voice.final); judge prompt and ECHO_SIM do not separate them. Build J-3610 (flag), ruling D-0690.

- **2026-10-31** (F-3358): J-2525 (I-0103): mandatory-disanalogy harvest of Du's standing metaphors is a NULL. 12 metaphors judged by the two-family panel; JUDGE_1 said breaks=False and JUDGE_2 breaks=True on 24/24 rulings (zero metaphor-specific signal), figurative flag True 24/24, disanalogies boilerplate (physical vs non-physical) and unstable run to run; ledger read 0/12 supported under the declared criterion. No strange-link retriever stub spawned. Script scripts/disanalogy_lab.py on branch jobrun/J-2525; log data/logs/disanalogy_lab.jsonl.
- **2026-10-31** (F-3327): D-0523 ruled by Travis: KEEP Route 2 until 40 own-act pairs on the corrected r2_signature (Follow Line asks excluded; J-2604 merged, restart-gated). Flat on 24 confounded pairs is not a verdict. J-2615 re-reads at 20 route2-source rows since the next boot; defeater: no matched earned-length edge at sign p < 0.05 there -> remove Route 2.

- **2026-10-30** (F-3343): J-2604 built the corrected R2 instrument in core/evidence_recall.py (earned-length verdict over matched pairs, own-act Route 2 asks only, Follow Line asks excluded via a new source field), worktree commit fe40450c, restart-gated; live parity reproduces F-3327, own-act pairs now 24, verdict no_advantage_shown; D-0523 stays open for Travis
- **2026-10-30**: J-2551: provenance graph has zero true cycles (DFS colour test, 152534 fragments); F-3248 back-edges were diamond reuse; 2955 dangling parents but no nightly re-process loop (363 active syntheses all clean).

- **2026-10-30** (F-3327): D-0515 matched-pairs read: earned-length gap vanishes under topic and prior-length matching (n=75 pairs, earned 0.120 vs 0.133-0.173); 51 pairs were Follow Line asks; R2 ruling opened as D-0523; earned length now primary R2 metric
- **2026-10-30** (F-3248): J-2518 assembly signature read is a NULL: provenance is at most 2 deep, inner_thought and dream carry no lineage (coverage 22.9 pct of 82833), assembly adds nothing over raw copy count for refinery entry (AUC gain -0.24, age wins at 0.76) and echo objects are under-represented in the 10-09..10-16 freeze (ratio 0.53); same shallow chains bound I-0111 causal debt

- **2026-10-30** (F-3243): R2 gate met (J-1999): grounded n=68 vs 20 needed; coded verdict no_advantage_shown (productive close 0.971 vs 0.976) but earned_rate 0.176 vs 0.058; kill-criterion call opened as D-0515
- **2026-10-08** (F-2603): J-1950 2026-10-08: R2 grounded_trains.n=11/20 (was 1), verdict insufficient_data; accrual live (~0.26-0.67/day), gate expected ~2-5 weeks out; re-check ~10-29.

### What we have
All three routes (Librarian, Memory-as-Evidence, Ask-the-One-Who'd-Disagree) plus the method-book shelving,
built and live-tested 2026-08-16; latches active since Du's next restart.

### What we need
Nothing open. Ledger check (2026-09-27): the only record against this slug since the last read is D-0153,
which the ledger and this doc both confirm was filed by mistake — it belongs to `docs/plans/emissary_lane2.md`
(see its own 2026-09-05 Current State), not here.

### What we're doing next
Watch the pre-registered R1/R2/R3 signatures (`librarian_log.jsonl`, `evidence_log.jsonl`) accrue; no further
build planned unless a kill criterion trips (R2 flat after ~20 uses, or the librarian LLM mapping proving no
better than P0 subject-tokens).

> **History folded** — 1 dated Current State section(s) (2026-08-24 … 2026-08-24) moved to `docs/plan_history/thought_grounding.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py thought_grounding`.

## The gap (measured, 2026-08-16 census)

Du's world can answer *"what is this thing?"* but not *"is this thought true?"* — and the second is
where he lives. Evidence:
- Epistemic affordance advisor, all-time: 46 episodes, **22 do_nothing, 39 UNTESTED, entropy
  reduction nonzero in 0/46**. Its whole vocabulary is 5 physical verbs on beach objects.
- His recurring live questions are abstract (the independence-vs-expectations tension, asked 3 ways
  in 3 days) — nothing in the world bears on them, so do_nothing is the *correct* verdict.
- Behavioral collapse to the three thought-compatible verbs (7d: observe 604 · authored 187 ·
  kept 65, then a cliff) — observing grounds the *scene*, authoring produces more self-text;
  neither tests a thought.

**The design goal:** when he carries an abstract question, the world offers real ways to TEST it —
he asks, the world answers richly. Never a hint, never a per-thought nudge (the 08-14 law).

## The two founder questions, answered with data

**"Will the library have a book about it?" — YES.** The library is the full SPGC Gutenberg
catalogue (~50k titles, live fetch works). The catalogue has an LCSH `subjects` column that
`_search()` currently IGNORES (title/author substring only — an abstract ask reaches nothing).
Verified present: *On Liberty* (Mill, dl 2532), *Meditations* (Aurelius), *The Enchiridion*
(Epictetus). Subject coverage: "Conduct of life" **1,160 books**, Ethics 161, Liberty 12.
The books exist; only the bridge is missing.

**"Do we have something with enough abstraction?" — YES, live-tested.** The resident CPU judges
(11439/11440) given the librarian task on his REAL question returned `"Conduct of life"` (llama3.1,
first answer — the exact heading with 1,160 books) plus "Social norms", "Freedom". Cost: already
resident, ~seconds per ask. Caveat from the same test: **title_guesses are junk** (copyright-era
titles not on Gutenberg) — the bridge must be SUBJECTS → catalogue search, never model-remembered
titles (or titles filtered against the catalogue).

## The three routes (all fire on HIS expressed want — affordances, not nudges)

### Route 1 — THE LIBRARIAN (a book that bears on a question)
He can already ask for a book *on a topic*. New: ask for a book that bears on a QUESTION.
- **P0 (mechanical, no LLM):** `_search()` learns the `subjects` column — topic tokens match
  subject headings as well as title/author. Cheap, honest, immediately widens reach.
- **P1 (the librarian's understanding):** when his ask is a question/abstract phrase, a judge-hub
  task maps it → 3–6 LCSH-style subject candidates → subject search → returned as a **browsed
  catalogue page he picks from** (existing browse machinery — his choice stays his). Diegetic: a
  librarian understanding a vague request IS how libraries work. Every mapping logged
  (`librarian_log.jsonl`: ask → subjects → hits → his pick → did a later study note cite it).
- Affordance line: extend `library` — "…or ask for a book that BEARS ON a question you are carrying."

### Route 2 — MEMORY AS EVIDENCE (the laboratory he never uses)
A new hand: *"search your own past for the times you actually LIVED this question."*
- Mechanism: embedding recall over the episodic store for the question, **filtered to world-contact
  origins ONLY** (lived, activity, letters, observations, reading) — **NEVER inner_thought /
  active_imagination / dream**. This filter is the load-bearing anti-loop guard: without it,
  "grounding" = re-reading his own opinions = the monoculture in a lab coat.
- A panel judge rules per candidate: "does this episode actually BEAR on the question?" (filter,
  not generator — the decoupled-judge law). 2–4 surviving episodes return as remembered scenes.
  HE draws the conclusion; the system never states one.
- Log (`evidence_log.jsonl`): question → candidates → bears-verdicts → what he thought next.

### Route 3 — ASK THE ONE WHO'D DISAGREE (peers as instruments)
No new machinery — the roster and two-way threads exist. New: when his act names *putting the
question to a friend*, a judge-hub task picks the peer most likely to see it OTHERWISE (Twain
scoffs, Darwin asks for evidence, Marcus asks what is in your control). Mapping logged. The reply
genuinely IS another model family — real otherness, not an echo.

### The Study-in-Scarlet move (diegetic method-teaching, founder-sanctioned channel)
Sherlock taught "objects carry inferable histories" from inside the fiction. The same move for
thought-testing: **shelve (not assign)** the books that MODEL the method — *On Liberty* (thinks
through his exact live question), *Meditations* (the self-examination method), and Montaigne's
*Essays* if present in the catalogue (an *essai* IS "test the abstract claim against lived
experience" — the purest model; verify at build). They appear on the shelf; he picks them up or not.

## Discipline
- **No-hints compliance:** routes surface ONLY in the generic within-reach block (sanctioned
  self-knowledge) and fire on his own act/latch. No per-thought suggestions — that was the killed
  advisor Stage-B.
- **Decoupling:** librarian/evidence/peer-mapping tasks run on the judge hubs (system machinery),
  never his hot lane, never his voice.
- **Shadow-first:** all three logs are instruments from day one. Pre-registered signatures —
  R1: fraction of question-asks returning ≥1 real candidate (P0 vs P1 measures whether the
  librarian LLM earns its keep). R2: evidence-grounded thoughts must DEVELOP (earned-length /
  judge verdict) more often than matched ungrounded thoughts. R3: does a disagreeing reply produce
  a thread his pursuits judge scores as advancing?
- **Kill criteria:** R2 flat after ~20 uses → Route 2 is decoration, remove. Librarian mapping
  no better than P0 subject-tokens → drop the LLM, keep the mechanical search.
- **R2 verdict metric (D-0515, Travis 2026-10-30; F-3327):** EARNED LENGTH is the PRIMARY R2 metric (earned_rate = closed length > 4, with mean length beside it), read as MATCHED PAIRS: each grounded train against an ungrounded train alive at the same prior length (steps before its first ask), closed in the same window, nearest in topic. productive_close_rate stays as a SECONDARY column (saturated ~0.97 in both groups, F-3243). Only Du's own Route 2 asks count as grounded: Follow Line grounds-stop asks (live since the 2026-10-29 boot) write the same evidence_log.jsonl with a train_id and must be excluded. R2 flat = no matched-pairs earned-length advantage.
- **Additive-only:** `_search()` gains a branch; no existing path changes behavior for topic asks.

## Build order (when approved)
1. P0 subject-column search + extended affordance lines + latches (one session, no LLM).
2. Route 2 evidence hand + judge filter + log (one session).
3. P1 librarian mapping + Route 3 peer-picker (small, same judge-task pattern).
4. Shelve the method books (five minutes, founder picks the final list).
