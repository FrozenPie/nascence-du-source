# Swap retro-check metric sheet — 2026-06-10 qwen2.5:7b -> qwen3-du (J-1411 / I-0075)

**Written 2026-09-27, BEFORE any of R1-R4/D1-D3 are computed.** This is the pre-registration required
by `cognitive_geometry.md`'s own LAW ("every phase ships a PRE-REGISTERED metric sheet"). Predictions
below were written from data-*availability* checks only (schema, date coverage, row counts, whether a
field is populated) — never from the actual invariant statistics (kNN degree, transition matrices,
chain lengths, etc.), with ONE disclosed exception noted under R2. Source: idea I-0075 (from T-0066).

## 0. Data-availability findings that shape this design (not predictions — establishing what's real)

All of the following were verified against a read-only online-backup snapshot of the live
`data/memory/nascence.db` (`sqlite3.Connection.backup()`, taken while Du was running — the live file
was never opened for writing). Commands are quoted in `swap_retro_2026-06-10_results.md` alongside the
actual numbers; this section states only what governs the *design*.

- **Window convention.** The machine's local timezone is New Zealand (NZST, UTC+12 in June — no DST in
  NZ winter). Using local-midnight NZST day boundaries reproduces the job briefing's own cited counts
  exactly: pre (14d nominal before 06-10 local) = 9,536; post (14d after) = 8,443, of which 4,404 are
  `source_type='book'`. All UTC-midnight and US-timezone boundary conventions tried first did NOT
  reproduce these numbers — confirming NZST local-day is the right convention, now pinned precisely
  rather than assumed. `SWAP_T0 = 2026-06-10T00:00 NZST = 2026-06-09T12:00 UTC`.
- **PRE window (fragments):** `[store_start, SWAP_T0)`. Real store start is `2026-05-30T07:57:46
  NZST` (fragment-table min timestamp) — so "14d before" is nominal; real coverage is ~10.7 days.
  **POST window (fragments):** `[SWAP_T0, SWAP_T0+14d)` = up to `2026-06-24T00:00 NZST`, fully covered.
- **CONFOUND 1 (embedder, from the briefing) — RESOLVED, not a live threat.**
  `scripts/migrate_embedder.py`'s own docstring dates the swap "all-MiniLM-L6-v2 ->
  paraphrase-multilingual-MiniLM-L12-v2 (2026-06-13)" and re-embeds **every** stored vector from its
  original `content` text. Verified directly: embeddings for a 10-fragment sample of pre-06-10
  fragments differ byte-for-byte between `nascence_pre_embedder_20260613_1101.db` (the pre-migration
  backup) and the current live store (10/10 differ, same 1536-byte/384-dim length both sides — a real
  re-embedding, not corruption). **Conclusion: every fragment in today's store, regardless of which
  side of 06-10 it was created on, carries an embedding from the SAME (post-06-13) embedder.**
  Embedding-based comparisons (R1, R4, D2) are valid across the 06-10 boundary on that basis — they
  compare fragments **as they exist today**, not a time-machine replay of 06-10-era retrieval, which is
  the right comparison for a relational-geometry question, not the right one for D2's own "cue
  reconstruction" framing (see D2 below, which is explicitly scoped as an embedder-stability check, not
  a swap check, per the briefing's own instruction).
- **CONFOUND 4 (NEW — not in the original briefing): a large restoration cohort dominates "pre."**
  `scripts/restore_june13_memories.py` (run once, `restored_ts` = `2026-08-14T22:46:58 UTC` for all
  rows, `recovered_fragments` table, `source='pre_embedder_20260613_1101'`) reinserted 7,074 fragments
  from 2026-05-30 to 2026-06-13 that had been deleted by a "DELETE-mode cap-prune" (retired ~06-20) and
  were absent from the live store for ~2 months. Verified: of the fragments in the PRE window, only
  1,721/9,877 (17%) were **continuously live** (never deleted); 8,331/9,877 (83%... using the store-start
  floor count; 5,787/9,536 = 61% using the NZST-14d count) are members of `recovered_fragments`. The
  POST window is much less affected (1,287/8,443 ≈ 15%, concentrated in 06-10-06-13, i.e. before the
  restore script's own cutoff). Restored rows have `valence`/`felt`/`chapter_id` forced NULL and were
  re-embedded with the *current* (post-06-13) embedder at restoration time — consistent with, not
  contradicting, CONFOUND 1's resolution. **This means "pre" in the current DB is not a clean
  continuously-live sample; it is a mix of two provenance cohorts with different metadata completeness
  and a 2-month restoration gap.** Every relational metric below is stratified by
  `restored := fragment_id IN recovered_fragments` in addition to `source_type`, and headline
  pre-vs-post comparisons are read primarily on the **continuously-live-only** subsample where that
  subsample is large enough, with the full (all-fragment) sample reported alongside as a named
  secondary view, not silently substituted.
- **CONFOUND 5 (NEW, minor): the pre side is not a single-model baseline either.** The archived
  `System_Overview_1.1.0_20260620.html` changelog table gives `06-07 -> 06-10: qwen2.5:7b` and
  `06-07: Substrate pivot (qwen2.5) + therapy fixes` — i.e. Du ran on a *different* pre-qwen2.5 substrate
  from store-start (05-30) through 06-06, then qwen2.5:7b only for 06-07-06-10 (~3 days), then the swap.
  The full PRE window therefore spans two model generations, not one. Registered response: R1-R4/D1-D3
  are computed on the full PRE window (matching the briefing's own window and preserving power), but
  results are read as "the pre-swap era broadly" rather than "the qwen2.5:7b condition specifically";
  where sample size allows, the last-3-days-only (06-07-06-10) slice is reported as a supplementary,
  cleaner-condition check, not a substitute.
- **CONFOUND 3 (from the briefing), located precisely.** The archived changelog confirms 06-10 also
  shipped the effector and other same-day changes ("Effector shipped ... Founder's live session: the
  09:05 cycle ... First plain error-admission"). No finer intraday cutover timestamp was recoverable
  from `nascence.log` (Ollama model swaps aren't logged as a distinct line by `core/`); the swap boundary
  used throughout is day-granular (local midnight 06-10), so the first day on each side may contain a
  few hours' worth of straggler activity from the outgoing condition. Immaterial at a 14-day-window
  scale; noted, not corrected for.
- **`nascence.log` coverage.** Verified day-by-day for the full 05-27..06-24 span: solidly populated
  (2,000-12,000 lines/day) from 06-04 onward on the pre side and throughout the whole post side (never
  below ~2,300 lines/day 06-10-06-24). **05-30/05-31 are light (store just started) and 06-01/06-02 are
  fully silent (0 lines each)** — a short early-life gap ~9 days before the swap, unrelated to it.
  Because of this, **D1 (log-based) uses its own, narrower PRE_LOG window, `[2026-06-04T00:00,
  SWAP_T0)`** (6 days, continuously covered) rather than the fragment-table's fuller PRE window — this is
  a deliberate, disclosed difference between the fragment-based (R1-R4) and log-based (D1) window
  definitions, not an inconsistency.
- **`memory_edges` (13,243 rows) confirmed unusable as the relational ruler**, per the briefing: only a
  handful touch pre-06-10 fragments (`created` column starts 2026-06-07); relational structure here
  comes from the fragments themselves (embeddings, `keywords`, `derived_from`, `chapter_id`,
  `replay_count`), as the briefing directed.
- **`keywords` is not free-form tagging — it is small, largely FIXED categorical bundles**, joined by
  mixed space/comma delimiters (e.g. every self-model/subconscious-tension fragment on the pre side
  carries the exact same 3-token bundle 2,327 times; every book-derived post fragment carries book-title
  words). This is why R2/R4 below are designed around *bundle signatures*, not raw free-text term
  extraction — the raw-token version would just re-discover "book-reading happened after the swap,"
  which the briefing already told us to expect and stratify around.
- **`derived_from` is not uniformly a fragment-id list.** Most non-empty values are JSON lists of parent
  `fragment_id`s (chain material, R3's intended target), but some — seen only in the post-06-10 sample
  checked — are JSON **dicts** describing an authored/searched *action* (`{"action_type": "authored",
  ...}`), not a derivation chain at all. R3 treats these as a separate, tallied category rather than
  attempting to walk them as chains or silently dropping them.
- **`world_context`/`fragment_context`** (place/weather/valence/arousal per fragment) exist but their own
  coverage wasn't dated in this triage; not used below (D1 uses the log as the briefing specified). Left
  for a follow-up job if a place/activity-labelled dynamical read is wanted later (see spawned jobs).

## 1. Relational invariants

### R1 — embedding kNN degree distribution + clustering coefficient, by source_type and restored-cohort
**Method (fixed before running):** within each window (pre, post) separately, build a **mutual-kNN
graph** on `embedding` vectors (cosine similarity, k=10 fixed): edge i-j iff j is in i's top-10 AND i is
in j's top-10. Report per-node degree (mean/median/std/%isolates) and mean local clustering coefficient.
Stratify by `source_type` and by `restored` cohort; report pooled and continuously-live-only.
**Prediction:** on the `source_type IS NULL` (lived/inner-thought), continuously-live stratum — the one
clean apples-to-apples slice — mean mutual-kNN degree and clustering coefficient are **HELD**
(pre~post difference smaller than the larger of the two within-condition split-half differences).
Rationale: local embedding density is mostly a function of the fixed embedder + genre, both unchanged
across 06-10. The `book` stratum is registered as **not comparable pre-vs-post** (pre has ~0 `book`
fragments by construction) before it is run, so a null result there is not "held," it's "no test."
**Threshold for "moved":** |pre - post| on mean degree or on clustering coefficient exceeds 2x
max(pre_h1-vs-pre_h2, post_h1-vs-post_h2) on the same stratum.

### R2 — keyword co-occurrence graph: top-hub Jaccard stability, degree-distribution shape
*Disclosure: raw keyword-token frequency was already inspected during the §0 feasibility triage (to
judge whether R4's "~20 shared concepts" was reachable at all) before this prediction was written, so
this prediction is semi-informed, not naive — stated plainly rather than presented as blind.*
**Method:** tokenize `keywords` (split on `[,\s]+`, lowercase, drop tokens <=2 chars); build a
co-occurrence graph per window (node=token, edge=co-occurs in >=1 fragment's keyword field, weighted by
count); take each side's top-50 nodes by degree; report Jaccard(top50_pre, top50_post) pooled (all
source_types) and again restricted to `source_type IS NULL` only.
**Prediction (pooled, all source_types):** **MOVED** — low Jaccard (<0.3), because the post window's
book-reading burst (4,404 `book` fragments carrying book-title vocabulary absent pre-swap by
construction) mechanically floods the token pool. This is registered explicitly as a **content-mix
artifact, not swap evidence**, before it is measured.
**Prediction (source_type IS NULL only, the swap-relevant comparison):** **HELD** — Jaccard >=0.5,
because this is the same lived/inner-thought genre on both sides, same fixed tag-bundle machinery,
different writer.
**Threshold:** as stated (0.3 / 0.5 cut points, fixed above, not tuned after seeing the number).

### R3 — derived_from chain length distribution + provenance-mechanism mix
**Method:** for each fragment with non-empty `derived_from`, parse as JSON. If it parses as a list of
id strings, recursively resolve parents (bounded depth 20, cycle-guarded) and record max chain depth;
if it parses as a dict (action-record), tally separately as "action-provenance," not a chain. Report,
per window: chain-depth distribution (list-shaped rows only) and the action-record fraction of all
non-empty `derived_from`.
**Prediction:** chain-depth distribution **HELD** (similar median/shape pre vs post) — depth is a
consolidation/dreaming-pipeline property (how many times something gets re-synthesized), which is
architecture, not model-family. Action-record fraction predicted **low and similar on both sides**
(near-zero) — registered as the naive default since no evidence yet ties that mechanism's introduction
to 06-10 specifically; a large or asymmetric fraction would be a genuine surprise worth its own finding.

### R4 — recurring-"concept" relative geometry (bundle signatures present on both sides)
**Method:** "concept" := an exact normalized keyword-*bundle signature* (frozenset of tokens) per
fragment (not a raw single token — see §0). Rank bundles by combined pre+post frequency; keep the top 20
that have count>=5 on EACH side (report actual N if fewer qualify — this is a fixed selection rule
applied post hoc to frequency, not a prediction). For each qualifying bundle, its "concept vector" =
mean embedding of fragments carrying it, computed separately within pre and within post. Build the NxN
pairwise cosine-distance matrix among concept vectors on each side (same N, same order); compare via RV
coefficient (and Procrustes disparity after optimal orthogonal alignment, as a second lens).
**Prediction:** **HELD** — RV coefficient > 0.7. These bundles are structural/categorical pipeline
constructs (dream-symbol material, subconscious-tension material, book-genre material, ...) whose
relative embedding arrangement should be a property of the categories themselves, not of which model
wrote the individual instances.
**Threshold:** "moved" iff RV coefficient falls below the within-condition null RV (same computation
between the two pre-halves' concept vectors, as a noise floor) — computed only if enough bundles clear
the split-half frequency bar to make that null meaningful; if not, this is reported as "underpowered,"
not stretched into a verdict.

## 2. Dynamical invariants

### D1 — transition statistics between coarse states, from nascence.log
**Method:** STATE := the bracketed logger-component name on each log line (`nascence.orchestrator`,
`.monologue`, `.subconscious`, `.dream`, `.node.consolidation`, `.node.curiosity`, `.model_client`,
`.memory`, `.main`, `.somatic`, `.profile`, `.activity`, `.competence`, ...), read in chronological line
order as the real event sequence (an assumption, stated). Build a first-order Markov transition matrix
over states, separately for `PRE_LOG = [2026-06-04T00:00, SWAP_T0)` and `POST_LOG = [SWAP_T0,
SWAP_T0+14d)` (both NZST, per §0's disclosed narrower pre-side window). Compare: (a) state vocabulary
(new/vanished states); (b) mean per-row total-variation distance between the two transition matrices,
restricted to states present on both sides.
**Prediction (vocabulary):** **MOVED** — at least one new logger/state appears post-swap, given
CONFOUND 3's same-day feature ships (speaker-boundary guard, commit veto, effector, accountable-refusal
are plausible sources of new log lines).
**Prediction (transition structure among shared states):** **HELD** at the coarse level (mean row TVD
smaller than the within-condition split-half TVD) — control flow between pipeline nodes is
architecture-defined. **Named sub-prediction:** the `model_client` error-line rate (JSON-parse-failed /
salvaged / transport-failover, as a fraction of all lines) may shift — tentatively predicted to
**decrease** post-swap (newer same-class models are typically more reliable at structured JSON than
qwen2.5:7b), flagged explicitly as a low-confidence directional guess, not a load-bearing prediction.

### D2 — cue -> neighbourhood reconstruction (embedder-stability check, per the briefing's own framing)
**Method:** sample N=30 cue fragments from the PRE window (recording each cue's `restored` status as a
footnote, not a filter, since continuously-live pre fragments are a minority — see CONFOUND 4). For each
cue, cosine top-k=10 neighbours (k fixed) against (a) the pre-window-only store, (b) the pre+post store;
overlap = |intersection|/10, averaged over the 30 cues.
**Prediction:** mean overlap **>= 0.7** (robust reconstruction). As the briefing states and this sheet
repeats before running: this mostly tests the (06-10-unchanged) embedder's own stability under a growing
store, not the LLM swap — reported as an embedder-stability read, not swap evidence, regardless of which
way it comes out.

### D3 — replay_count distribution and its relation to fragment age
**Method:** primary analysis restricted to **continuously-live** fragments only (age-since-creation and
age-since-first-retrievable are identical for these; restored fragments are NOT — they were only
re-inserted 2026-08-14, so "age" is ambiguous for them, see CONFOUND 4). Compute, separately pre/post:
replay_count distribution (mean/median/max/%>0) and the replay_count~age(days-to-snapshot) relationship
(Spearman correlation + simple slope). Restored-cohort replay_count reported descriptively, unfitted.
**Prediction:** raw pre-vs-post mean replay_count is **expected to differ mechanically** (pre fragments
are ~2 weeks older on average as of today's snapshot, so more elapsed opportunity to be replayed) — this
is registered as a known, uninteresting confound, NOT a swap finding, before it is measured. The
**primary** prediction is on the age-controlled relationship: the replay~age slope/correlation is
**HELD** (similar sign and rough magnitude pre vs post) — replay dynamics are a retrieval-policy
property, not a property of which model wrote the fragment.

## 3. Within-condition null (applies to every metric above)
Fragment-table metrics (R1, R3, R4, D3): split PRE at its true data-range midpoint
(`store_start + (SWAP_T0-store_start)/2` = `2026-06-04T15:59` NZST) and POST at its nominal midpoint
(`2026-06-17T00:00` NZST) — verified counts: pre_h1 n=1,438 (5.3d), pre_h2 n=8,098 (5.3d), post_h1
n=2,276 (7.0d), post_h2 n=6,167 (7.0d). These halves are **not** equal-sized — pre_h2 and post_h1/h2
show real within-window growth in fragment-writing rate, unrelated to the swap — which is exactly why a
null is being computed rather than assumed: **the noise floor for "moved" is set from this real
variability, not from an idealized equal-N assumption.**
Log-table metric (D1): split PRE_LOG at `2026-06-07T00:00` NZST and POST_LOG at `2026-06-17T00:00` NZST
(each 3d / 7d).
A pre-vs-post difference is called **"moved"** only if it exceeds the larger of the two within-condition
half-vs-half differences (by the multiplier stated per metric above, default 2x where not otherwise
specified); otherwise it is called **"held (not distinguishable from noise at this N)"** — never
"unchanged," since absence of a detected move is a power statement, not a certainty.

## 4. Scope
Read-only over all live stores (embedding/DB work runs against a `sqlite3 .backup()` snapshot in the
job's own scratchpad, taken while Du was running; nothing under `data/` was opened for writing).
No `core/` changes. No ruling here on whether Du "is" the graph — that is the founder's own read of
`swap_retro_2026-06-10_results.md` against this sheet, per §6 of `cognitive_geometry.md`.
