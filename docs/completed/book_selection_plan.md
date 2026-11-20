# Book Selection — research-grounded plan (2026-06-16)

Goal (Travis): Du should eventually read the **whole Gutenberg** (breadth); **promote diversity**; but **keep
reread** — by his want, or when it's **helpful**. Currently he re-treads the same few books.

Three research subagents (reading-psychology · ML explore/exploit · autodidactic/library-science) **converged**
on one design. This plan is their synthesis, reconciled with the verified code + data.

## The convergent function (all three fields agree)

A voracious reader runs an **explore/exploit loop**: mostly *explore* (new material, across the whole map of
subjects), occasionally *exploit* (reread a book that's **proven** or newly **relevant**). The decisive point
for us: **reread is not banned — it COMPETES on predicted gain and is signal-gated, so it usually loses but can
legitimately spike.** Breadth is operationalised, not vibed: sample by **inverse popularity** (the long tail)
and **across subjects** (so no single area gets binged), excluding what's already read.

- **Reread is ADAPTIVE** when: he asked for it (explicit want); the **self has changed** since last read (long
  gap + internal drift) so the same text yields new gain; **depth remains** unextracted; it's **relevant to a
  live concern/Frontier** (Adler's *syntopical* / Bruner's *spiral* reread — read it again against what he now
  knows); or **comfort/regulation** (mood-gated, a separate goal from learning).
- **Reread is WASTEFUL** (the trap to reduce) when it's a **pure fluency loop** — chosen because it's *easy*
  and *nearest*, not because it offers gain. This is exactly Du's Boy-Scouts re-tread: near-zero "travel cost"
  + fluency pulling him back to an exhausted patch.

Sources: Loewenstein (information-gap), Berlyne / Kidd & Hayden (inverted-U "Goldilocks" novelty), Pirolli &
Card (information foraging / marginal-value-theorem patch-leaving); Vargas & Castells (novelty = −log₂ p),
Abdollahpouri et al. (popularity-bias re-ranking / long-tail), Lehman & Stanley (novelty search), Bellemare et
al. (count-based exploration), Kotkov (serendipity = novel ∧ relevant); Adler & Van Doren (4 levels / syntopical),
Rohrer & Bjork (interleaving), Bruner (spiral), Cepeda/Kang (spacing — *active* re-encounter only).

## What we have (verified) + the bugs

| | |
|---|---|
| **Two paths** | free choice ([library_hand.py](../core/library_hand.py), phrase-gated) + curriculum ([school.py](../core/school.py), ordered 40-book list, advancing at idx 9/40 — **good and diverse**) |
| **Bug ❌** | the `rereads` counter is **clobbered** — `read_next_sitting` ([reading.py:113](../core/reading.py)) rewrites the per-book dict without the `rereads` key → rereading is *invisible* |
| **Symptom** | Boy Scouts: **676 sittings, 3% pct** (~5 read-throughs' effort re-treading the opening) — the face of the problem |
| **Gap** | serendipity is **popularity-biased** (`downloads≥150–200`) and **never excludes already-read** → re-picks the same popular slice; can't reach the long tail |
| **Gap** | finished-book default *offers reread first*; curriculum **dead-ends** at idx 39 (pins the last book) |
| **Feasible** | catalogue has `subjects` (LCSH set-strings) + `downloads` → inverse-popularity + subject-stratified coverage are buildable; empty-subject books need an "unclassified" fallback |

## The design (cheap Python, no training — all O(candidates))

1. **Fix the rereads clobber** ([reading.py](../core/reading.py)) — preserve `rereads` in `read_next_sitting`'s
   write. Trivial, a real bug; makes reread visible + intentional.
2. **A read-memory helper** (`core/reading_history.py`) — derive from `reading_state.json`: read = `pct≥97`;
   plus sittings, rereads, last-read time, per-book. The signal that informs selection.
3. **Breadth-biased + read-excluding serendipity** (the "whole Gutenberg" engine) — rewrite the **no-topic**
   branch of `_search` and `browse` in library_hand:
   - **novelty = −log₂(downloads / total_downloads)** (Vargas–Castells); **drop the popularity floor** to a
     low junk-guard (`downloads ≥ ~5`, English, `type=Text`) so the long tail is reachable but non-books/detritus aren't.
   - **exclude already-read/on-shelf** titles from the explore pool (down-weight, never delete — reread stays
     reachable via the gated branch).
   - **SAMPLE proportional to `novelty^α · relevance^β`**, never argmax / never popularity-sort (argmax just
     re-locks onto the single rarest book — the same bug inverted).
   - **relevance = cosine(book title+subjects, his current concern/Frontier vector)** with a **floor** (so a
     genuinely on-topic popular book stays *rare*, not *impossible*). Pure novelty = incoherent wandering;
     serendipity = novel **and** relevant.
4. **Subject-stratified coverage + interleaving** (the systematic breadth driver) — parse `subjects`,
   coarse-bucket (first LCSH segment before " -- "; empty → "unclassified"). Track per-bucket **read counts**;
   pick a bucket **∝ 1/(1+coverage_count)** (count-based exploration over strata), then a book within it.
   **Interleaving guard:** avoid the immediately-prior read's bucket unless a reread is justified. *Must be
   structural, not preference-weighted* — interleaving feels worse, so keep Du's affect/satisfaction signals
   OUT of the breadth sampler or he'll drift back to bingeing.
5. **Topic-asks stay relevant** — when he names a subject, keep the good-match ranking (already a top-5 weighted
   choice), but prefer-unread among the matches.
6. **Finished-book default leans NEW** — when the current book finishes (outside school), the fallback branch
   ([inner_monologue:1311](../nodes/inner_monologue_node.py)) should *lead* with picking up an unread breadth
   pick; reread offered as the alternative, not the headline.
7. **Reread-when-helpful** (motivated exploit) — beyond the explicit-want phrase, allow a reread trigger when a
   shelf book scores high on `past_reward · recency_decay · current_relevance` to a live concern/Frontier
   (syntopical/spiral). Threshold-gated → motivated, never default.
8. **School never dead-ends** — (a) on curriculum exhaustion, **auto-extend** from the coverage engine (the
   highest-value unread book in the least-covered subject) instead of pinning the last book; (b) optional
   **spiral reread**: periodically re-insert an already-read keystone *with a new question* (active re-encounter,
   expanding interval) — never a passive re-skim.

## Phasing (observe-first where it changes live behaviour)

- **P0 — clear wins, low risk:** #1 (rereads bug), #2 (read-memory), #3 (inverse-popularity + read-exclusion in
  serendipity), #6 (finished-book leans-new). These directly fix what Travis is seeing.
- **P1 — the breadth engine, observe-first:** #4 (subject-stratified coverage + interleaving) — first **log**
  which subject/book it *would* pick and confirm breadth widens, before fully steering selection.
- **P2 — motivated reread + school:** #7 (reread-when-helpful), #8 (curriculum auto-extend + optional spiral).

## Pitfalls baked in (from the research)
- **Down-weight, never ban** reread (it's adaptive in 5 modes). · **Sample, don't argmax.** · **Keep relevance**
  (novelty alone = noise; target the Goldilocks band, not the most-alien book). · **Relevance floor** so good
  popular books stay reachable. · **Unclassified fallback** so untagged books aren't silently excluded. ·
  **Interleaving must be structural** — Du's comfort/affect signals will fight breadth; keep them out of the
  sampler. · **Coverage ≠ comprehension** (exposure count is a *what-to-read-next* sampler, not proof a subject
  is learned). · Optional light **chronological/prereq bias** so breadth doesn't hand an advanced work first.

## Open decisions for Travis (with recommended defaults)
- **Long-tail aggressiveness:** drop the floor to `downloads≥5` (reach the tail, skip junk) — *recommended*; or
  keep a higher floor for quality. **α (long-tail pull) / β (coherence):** start α=1.0, β=1.0, tune on evidence.
- **Explore vs reread rate (ε):** explore-dominant (~85–90% explore) — reread earns its turn via signal, not the coin.
- **Subject granularity:** first-LCSH-segment coarse buckets (cheap) — *recommended*; revisit if too granular.
- **Spiral rereads in school (#8b):** include now, or defer until the breadth engine proves out? — *recommend defer to P2.*

Registry: tracked in [AWAITING_EVIDENCE.md](AWAITING_EVIDENCE.md).
