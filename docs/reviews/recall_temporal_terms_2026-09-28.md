# Recall's Existing Temporal Terms — a file:line map (J-1475, T-0072 prerequisite)

**Job:** J-1475 · **Plan tag:** memory_as_a_service · **Real subject:** T-0072 / `docs/staged/golden_spiral_recall.md`
**Date:** 2026-09-28 · **Scope:** read-only; no code changed. **Author:** claude (job-run session J-1475).

**Why this doc exists.** `docs/staged/golden_spiral_recall.md` (written 2026-09-27) already contains a
provisional §1 table splitting the founder's spiral picture into three mechanisms — **R** (radius = age,
log-spaced), **L** (level of detail falls with radius), **Θ** (angle = phase) — and says outright: *"this
doc's Current State is provisional until J-1475 lands, and its §2 verdicts are marked as such."* This is
that landing: every claim below is either **VERIFIED** (a specific file:line I read myself, this session)
or **INFERRED** (a reasoned conclusion from that evidence), never assumed. Section 7 is the direct
replacement for that doc's provisional §1 column.

---

## 1. `core/memory/store.py` — an architecture of separate mechanisms, not one clock

`store.py` (2,887 lines, read in full) has **no single "decay" or "recency" function** — it has at least
six independent temporal mechanisms, serving different subsystems, with different shapes. None is
log-spaced.

| # | Mechanism | File:line | Decays what | Window | Shape | Status |
|---|---|---|---|---|---|---|
| 1 | Seed accessibility weight | `store.py:334-343` (`_SEED_WEIGHT_START/_FLOOR/_DECAY_DAYS`, `_seed_weight()`) | how much a `origin='seed'` fragment counts in tier scoring | 180 days from the fragment's own storage timestamp | **linear**, 0.9 → 0.3 floor | LIVE — read inside `_score_tier()` (`store.py:757-760`) |
| 2 | Tier recency multiplier, "recent" bias | `store.py:748-750`, inside `_score_tier()` (726-765) | the score of every non-archive fragment when `retrieve(time_bias="recent")` (the default) | first 7 days only, then **flat** forever | **linear** ramp 1.0→1.2, saturates | LIVE — `retrieve()`'s default path |
| 3 | Tier recency multiplier, "distant" bias | `store.py:751-752` | same, opposite direction (older favoured slightly) | first 7 days, then flat | **linear** ramp 1.0→1.1, saturates | LIVE, gated behind a caller passing `time_bias="distant"` — I did not trace which callers use this branch; flagged as not verified this pass |
| 4 | Resolution-credit half-life | constant `store.py:367`; formula `store.py:2146-2172` (`get_resolution_drain()`), decay line `2171` | how much a "clean re-encounter" credit still counts against a shadow tension | 30-day half-life, no floor (asymptotic to 0) | **exponential**, `0.5 ** (age / 30d)` | LIVE — confirmed caller `core/tension_ledger.py:207` |
| 5 | Procedural-skill proficiency decay | `store.py:1532-1554` (`decay_procedural_skills`) | a learned skill's `proficiency` once unused past `stale_secs` | caller-supplied `stale_secs` (test harness uses 14 days); floor 0.15 → pruned | **step-multiplicative** (`× factor=0.9` per call where stale), not continuous | LIVE — confirmed caller `nodes/subconscious_node.py:2612` |
| 6 | Read-count importance bonus | `store.py:2709-2759` (`read_count_importance_shadow`) | proposed (never applied) importance bump | none — keyed by **read count**, not age | **log** — `min(0.25, 0.05·log1p(read_count))` | **SHADOW ONLY** — the function's own docstring and body confirm `importance` is never written to the DB here, only logged to `data/read_count_importance_shadow.jsonl` |

Mechanism 6 is the **only literal logarithm applied to anything memory-related in `store.py`**, and it is
a log of **usage count**, not of **age** — it answers "how many times was this read back", never "how old
is this."

**`store_fragment()`'s own PHASE stamp** (not a decay — a coordinate write) is covered separately in §6.

### 1.1 A per-kind rate table exists, but it is age-blind and shadow-only

`core/memory_dynamics.py` (145 lines, read in full) holds `KIND_DYNAMICS` — a static `cold_horizon` /
`gist_drift` / `gist_retention` triple per `kind` (procedural/episodic/semantic/affective/self/social/
symbolic), and `effective_cold_horizon()` (`memory_dynamics.py:109-145`), a formula:
`rate = base[kind] / recall_pressure / grounding_anchor × charge_factor × stage_factor`.
**This formula takes no timestamp as input at all** — "faster/slower" here is about kind, recall
pressure (a proxy: `1+replay_count`), grounding and stage, never elapsed time directly. Confirmed
SHADOW-ONLY by both the module's own docstring and a full read of `core/memory_levels.py` (989 lines):
only `phase2_status()`/`phase2_dynamics_shadow()` (`memory_levels.py:356-470`) ever call it, purely for
reporting. `store.py`'s own comment block (`store.py:230-236`) independently confirms the live cold-gating
paths (`prune_episodic`, `core/refinery.py`'s cooling `UPDATE`) are "kind-blind" — they never read this
table.

### 1.2 A third, unrelated exponential-age formula exists — shadow, unreferenced by the spiral plan

`core/euclidean_recall.py` (161 lines, read in full; docstring dated 2026-06-15, "OBSERVE-ONLY P0") is a
**wholly separate, never-live** recall re-ranker: a memory is a 6-dim point (`semantic_sim, recency,
affect_match, salience, abstraction, provenance`), scored by weighted Euclidean distance. Its `recency`
feature (`euclidean_recall.py:52-54`):

```python
recency = math.exp(-max(0.0, now - ts) / (tau_days * 86400.0))   # tau_days=14.0 default
```

— a genuine **continuous exponential decay over age**, distinct in shape from every mechanism in §1's
table, and distinct in half-life from mechanism 4. It also computes its own crude `abstraction` feature
(`euclidean_recall.py:20-22, 33-35`) from `layer` + an origin bump — **not** the real `abstraction_level`
column, and not kept in sync with Memory Levels' ladder (§2). `shadow_log()` (96-161) writes comparisons
to `data/euclidean_shadow.jsonl`; nothing calls this module from any live retrieval path (confirmed:
`retrieve()`/`_score_tier()`, read in full, §1's table, never import it). **`docs/staged/
golden_spiral_recall.md`'s own pointers section does not mention this file at all** — see §8.

### 1.3 No log-spaced age bucketing exists anywhere in the repo (grep-confirmed, not inferred)

A repo-wide `grep -r "math\.log"` over `core/` returned 35 files. The two that touch anything
memory-adjacent besides §1.2/§1's mechanism 6 are: `core/ghost_tuples.py:211` (`1.0/math.log(2+df)` —
**tag document-frequency rarity weighting**, live, nothing to do with age) and mechanism 6 above
(usage-count, not age). The remaining ~32 files are habituation/arousal/curiosity/stimulus-response
modules (e.g. `core/arousal.py`, `core/curiosity_habituation.py`, `core/transport_habituation.py`) — a
different domain (habituation to a repeated *stimulus*), not memory-age weighting; **not read this
pass**, flagged as out of this job's scope rather than silently assumed irrelevant. **Verdict: zero
log-of-age uses found anywhere.**

---

## 2. Memory Levels — promotion is by EVIDENCE, not age (verified against running code)

**The ladder** (structure, confirmed to exist): `raw(0) → gist(1) → theme/chapter(2) → identity/
worldview(3)`, column `abstraction_level` — `store.py:204-208`'s own comment, and
`docs/memory_levels_plan.md:155` word-for-word.

**Level 0→1 (the only rung with a live, running promotion mechanism).** `core/memory_levels.py`'s
`shadow_distill()`/`_commit_gist()` (`memory_levels.py:226-259`, `655-802`, both read in full). The gate,
verbatim (`memory_levels.py:742-746`):

```python
if (PHASE1_ENABLED and isinstance(faithful, (int, float)) and faithful >= FAITHFUL_FLOOR
        and not _genuine_invention and out["demoted"] < MAX_DEMOTE_PER_RUN):
```

`FAITHFUL_FLOOR = 0.75` (a decoupled-judge faithfulness grade). **No age or timestamp term appears
anywhere in this gate** — verified by reading the whole function (655-802): the only timestamp use is
`_last_ts()`/`newest_ts`, a high-water mark for *which rows to fetch next run*, never a promotion
criterion. **CONFIRMED: evidence-gated, not age-gated** — exactly the law `MEMORY.md` already states
("Memory Levels compresses by EVIDENCE, keep that law"), now with a file:line citation instead of a
standing rule.

**Level 1→2, world material (a separate module).** `core/world_consolidation.py` (271 lines, read in
full). `file_book_notes()` (159-205) gates on **(a)** a gist already exists (`170-177`, gist-first) and
**(b)** `_completed_passes_for(book_title) >= 1` (`183-184`, the finished-gate — a book mid-read is never
filed). Both are evidence conditions (a distillation exists; a reading pass completed), not an elapsed-day
count. No age check anywhere in the file.

**Level 2, self material.** Populated by chaptering, a module this job's briefing did not name and I did
not read — flagged as **not directly verified**, inferred only from `store.py`'s own `_ORIGIN_LEVEL =
{"chapter": 2, ...}` mapping (`store.py:409-412`).

**Level 3 ("identity/worldview") has no live writer at all.** `store.py`'s `_ORIGIN_LEVEL` dict
(`409-412`) maps origins only to levels 1 and 2; nothing in the 989-line `memory_levels.py` ever assigns
`abstraction_level=3`. Identity instead lives in a **wholly separate, parallel structure** — the Identity
Estate (`core/identity_estate.py`, 388 lines; `core/identity_projection.py`, 193 lines; both read in
full) — with its own JSON node registry (`data/identity_estate.json`) and its own promotion-like step,
`_cluster_values()` (`identity_estate.py:48-122`, cosine-medoid clustering of belief text into
parent/leaf tiers), which never touches `memory_fragments.abstraction_level`. **So the plan doc's own
stated level 3 is a documentation bridge to a different subsystem, not a populated rung of the same
column.**

**The "claim"/"model" vocabulary this job's own briefing used is design-only, not live.** §12 of
`docs/memory_levels_plan.md` (lines 2504-2547, read in full) proposes a richer per-level *type* —
`evidence | gist | claim | model | identity` — for a future "ledger overlay" (its own Phase 2, not the
Phase 2 that shipped as the `kind`/`grounding` columns). Confirmed no such `type` column exists: the full
`memory_fragments` schema (`store.py:141-306`, read in full) has only `abstraction_level`/`kind`/
`grounding`/`cold`/`temp` — no enum column carrying "claim" or "model" anywhere, and neither term appears
as a live value in `memory_levels.py`, `store.py`, or `memory_dynamics.py` (checked by targeted grep).
**Notably, the plan's own stated target rule for this promotion (§12, `docs/memory_levels_plan.md:2594
-2602`) is itself evidence/usage-based — "when its confidence crosses a threshold and it's used
repeatedly as if true"** — consistent with, not contradicting, what is actually built at the one live
rung.

**Verdict for L:** the ladder (structure) exists; the mechanism that moves a memory up it is **evidence**
(faithfulness grade, or gist-exists + completed-pass), never elapsed time, at every rung with a live
writer. `docs/staged/golden_spiral_recall.md`'s own provisional §1 line — *"exists, on a different law...
Memory Levels compresses by evidence, not age"* — is now verified, not provisional.

---

## 3. The M2 edge-aware trail — no time-based weighting in the edge layer itself

`core/memory_edges.py` (984 lines, read in full) + `docs/plans/memory_multiway_linking.md` (315 lines,
read in full):

- The `memory_edges` schema (`memory_edges.py:79-92`) carries a static `weight` and a `created` stamp,
  but **nothing reads `created` to discount an edge by age.** `edge_aware_neighbors()` /
  `edge_aware_neighbors_multihop()` (`834-943`) decay only by **hop distance** (`decay=0.6` per hop
  beyond the first, `891, 929`) — a graph-distance decay, a different axis from time entirely.
- `memory_multiway_linking.md` §3 (lines 198-200) *proposes* "chosen forgetting curves... fast for
  `co_recalled`... none for `distilled_from`... slow for `resolves`" as a **design freedom**, explicitly
  a future intent. I found **no code implementing a per-edge-type time decay** anywhere in
  `memory_edges.py` — this is aspirational text, not a built mechanism.
- The one genuine wall-clock term the M2 machinery has: `co_recall_status()` /
  `downstream_read_counts()` (`memory_edges.py:669-704, 707-744`) window their read by a `days` parameter
  (default 7.0 / 14.0) — a **hard cutoff** (rows before `now − days·86400` excluded), not a decay curve.
  This is a reporting-window, not a recall-weighting mechanism.
- `associative_recall.py` (spreading activation, "hop-decay 0.6" per `memory_multiway_linking.md:148
  -150`) is named but **not read this pass** — outside the briefing's explicit file list, flagged rather
  than assumed.

**Verdict:** M2/multiway-linking contributes **nothing** to R or Θ (no age or phase term anywhere in it)
and nothing new to L beyond Memory Levels — its only "decay" concept is hop-distance, a different axis.

---

## 4. Identity Estate / projection — genuinely silent on R/L/Θ (a real negative result)

`core/identity_estate.py` (388 lines) + `core/identity_projection.py` (193 lines) + `docs/plans/
identity_estate.md` (263 lines) — all read in full.

- No node's projection weight decays by elapsed time. `_node()` (`identity_estate.py:42-45`) stores
  `first_ts`/`last_ts` for provenance display only — nothing reads them back to age a node down.
- The one "recency" concept here (`identity_projection.py:40-41, 106, 126-132`) is a **call-count-indexed
  anti-repetition penalty**: `_recency[node_id] *= _RECENCY_DECAY (0.55)` **per projection call**, not per
  elapsed second/day — used only to rotate which estate node surfaces next (anti-monoculture), unrelated
  in kind to R/L/Θ. Flagged explicitly so it is not mistaken for a fourth age-decay mechanism.
- Two plain elapsed-time gates exist (`identity_estate.py:324-325`): a 600s re-check cooldown and a
  24-hour reseed-staleness trigger — both throttle the **seeding process itself**, not any per-memory
  weighting.

**Verdict:** the briefing's instruction to check identity_estate turned up a genuine, verified negative —
it neither ages nor phase-tags anything, worth recording as a real answer rather than an unexamined gap.

---

## 5. Felt recall (`memory_as_a_service.md` §3) — coordinate-matched, hard age FLOOR, no decay

**Verified against the actual shipped code**, not just the design doc: `core/felt_recall.py` (450 lines,
read in full from the `wt_memory_as_a_service` worktree, branch `jobrun/memory_as_a_service`, commit
`a97e82c` — **this file does not exist yet on the `C:\Nascence` checkout I read everything else from**,
since it has not been merged to that branch as of this read; flagged so this citation's provenance is
honest).

- `MIN_AGE_S = 86400.0` (`felt_recall.py:64`) — matched fragments must have `tuple_ts < now − MIN_AGE_S`.
  This is a **floor** (exclude only the newest day), exactly as `memory_as_a_service.md:125` states in
  prose — now confirmed in real code.
- `_build_prior()` (`219-276`) scores every candidate purely by **coordinate-match count**
  (`_coord_match_count`, `193-203`) against the current tuple (weather/fire/light_band/cat_at/place).
  **No age-based weight or decay is applied to the match score at all.** The only place `tuple_ts`
  enters scoring is a **tie-break** for equal-scoring candidates (`259`: `-sr[1]["tuple_ts"]`, most-recent
  first) — recency breaks ties, it does not weight the mean valence/arousal that becomes the affect tug.
- `FELT_RECALL_COOLDOWN_S = 600.0` (`58`) is a per-trigger-dimension habituation timer ("his reaction
  time, once per happening") — a temporal term, but about **trigger rate-limiting**, not memory-age
  weighting.
- `FELT_RECALL_LIVE = False` (`54`), confirmed still shadow-only, matching `memory_as_a_service.md`'s own
  Current State claim exactly.

This module is the **declared consumer** of the golden-spiral's Θ ray
(`docs/staged/golden_spiral_recall.md` §3: *"A recall triggered by a world change (D-0289's felt
recall)... reads the current `tod`/`season`/`daylight`"*) — confirmed it does **not** read those columns
today (no reference to `tod`/`season`/`daylight`/`phase` anywhere in the 450 lines).

---

## 6. The PHASE field itself — where it's built, where it's read

`core/memory/store.py:659-714` (`store_fragment()`, read in full as part of §1's file). On every write
with `context_stamp=True` (the default):

```python
ph_tod = round((_lt.tm_hour*3600 + _lt.tm_min*60 + _lt.tm_sec) / 86400.0, 4)          # store.py:675
ph_season = round((_lt.tm_yday - 1 + ph_tod) / 366.0, 4)                              # store.py:676
ph_daylight = _wclk.daylight(ts)                                                      # store.py:677
```

— computed from the fragment's **own** timestamp via `core/world_clock.py` (117 lines, read in full;
`daylight()` at `106-117`), stored as additive `tod`/`season`/`daylight` columns on **both**
`world_context` and `fragment_context` (columns added `706-712`, inserted `713-714`). Built 2026-09-27.

**Confirmed zero readers anywhere I looked:** the full `retrieve()`/`_score_tier()` path
(`store.py:726-948`), all of `core/memory_edges.py` (984 lines), and all of `core/ghost_tuples.py` (280
lines) — none references `tod`, `season`, `daylight`, or `phase` as a filter or weight. This matches
`docs/staged/golden_spiral_recall.md`'s own "Phase 0 BUILT today... no reader yet" claim exactly — I
independently confirmed the "no reader" half, not just the "built" half.

**One small, non-bug nuance worth flagging:** `store.py:662` (`phase = _sens._daylight()`) and
`store.py:677` (`ph_daylight = _wclk.daylight(ts)`) call the **same underlying pure function**
(`core/world_clock.py:106-117`) twice in the same write — once for *now* (a transient variable that only
gates whether `moon_illum` enters the experienced tuple, `core/experienced_tuple.py:110`), once for the
fragment's *own* `ts` (the new durable `daylight` column). They can only differ when `store_fragment` is
called with a backdated timestamp far from wall-clock now — not a defect, just worth a future reader
knowing it's one function, called twice, for two different purposes.

---

## 7. Summary table — the three mechanisms, verified (replaces `golden_spiral_recall.md` §1's provisional column)

| # | Mechanism | Verdict | Real evidence |
|---|---|---|---|
| **R** | Radius = age, **log-spaced** | **Log-spacing: ABSENT.** Age-weighting in some form: **partial**, three unrelated, non-log formulas | Linear 180-day seed decay (`store.py:334-343`); linear-then-flat 7-day tier bump, both directions (`store.py:748-754`); exponential 30-day half-life (`store.py:367,2171`); a 4th, shadow-only exponential τ=14d term (`euclidean_recall.py:52-54`), never wired to live `retrieve()`. Repo-wide `math.log` grep (35 files): zero log-of-age uses anywhere (§1.3). No per-band budget of any kind exists. |
| **L** | Level of detail falls with radius | **EXISTS, but governed by EVIDENCE, not age** (verified, not inferred) | Ladder: `store.py:204-208`, `docs/memory_levels_plan.md:155`. Level 0→1 gate = `faithful>=0.75` (`memory_levels.py:742-746`), no age term (full function read). Level 1→2 (world) gate = gist-exists + completed-pass (`world_consolidation.py:170-184`), no age term. Level 3 has no live writer (`store.py`'s `_ORIGIN_LEVEL` only maps to 1, 2) — identity lives in a separate parallel structure (§2). |
| **Θ** | Angle = phase, the cross-arm ray | **Field EXISTS at write (2026-09-27); NO reader anywhere**, including its own declared consumer | `tod`/`season`/`daylight` computed `store.py:671-679`, written `700-714`. Confirmed zero reads: `retrieve()`/`_score_tier()` (726-948), `memory_edges.py` (984 lines), `ghost_tuples.py` (280 lines). Declared reader `core/felt_recall.py` (450 lines, read from the worktree) confirmed **not yet reading it either** — felt-recall's own match logic (§5) uses coordinate-count + a plain age floor, no phase term at all today. |

---

## 8. What a spiral would add vs. what would be a re-skin — INFERRED (not verified; reasoned synthesis)

*Everything in this section is a conclusion drawn from §1-7's evidence, not a new fact — marked
`inferred` in the findings-log entry for exactly this reason. This job was not asked to, and does not,
design the spiral.*

- **Θ is the only genuinely new capability.** Nothing today casts a same-phase ray across ages — every
  existing "recency" or "match" mechanism (§1, §5) either ignores age past a short window or floors it
  out entirely. Building Θ would be additive, not a re-skin of anything found.
- **R (log-age bands with a per-band retrieval budget) would be a real behavioural change**, not a
  re-skin, even though "age affects retrieval" already exists in weak form. The current 7-day
  linear-then-flat bump (§1, mechanisms 2-3) has no memory of *how* old past a week — a true log-band
  budget would, for the first time, guarantee representation from old material rather than letting
  recent volume crowd it out (the exact failure mode `golden_spiral_recall.md` §2 names).
- **L (a read-side lower-detail default for un-promoted far-out fragments) would be additive, not a
  re-skin — but only if it is built as a read-time rendering choice** that never touches
  `abstraction_level`/`cold` (as `golden_spiral_recall.md` §2 already scopes it). Memory Levels' own
  evidence ladder (§2 above) must stay the sole write-side authority; L's proposed behaviour operates at
  a different point in the pipeline (read/render time) than the existing evidence-gated demotion
  (consolidation time), so the two are complementary rather than competing, as long as that boundary
  holds.
- **The concrete re-skin risk worth naming:** `core/euclidean_recall.py` (§1.2) already implements a
  shadow-only exponential age-decay feature *and* its own crude "abstraction" feature, sitting unused
  since comments dated 2026-06-15/07-03/08-19/08-20 — a real prior attempt at exactly this kind of
  age-weighted, multi-feature recall re-ranking. `docs/staged/golden_spiral_recall.md`'s own pointers
  section (its final "code:" line) does not mention this file at all. Before golden_spiral_recall.md's
  own §3 Phase 2/3 shadow builds start, it is worth a deliberate call on whether this module is
  superseded scaffolding to retire or a component to fold in — otherwise the project risks two parallel,
  unreconciled "age + detail" feature spaces. (Spawned as J-1547 — see §9.)

---

## 9. Follow-up spawned

**J-1547** (spawned this session, kind=analysis, plan=golden_spiral_recall): read `core/euclidean_recall.py`'s
shadow log (`data/euclidean_shadow.jsonl`, if it has accrued rows) and `docs/euclidean_memory_plan.md`
(not read this pass), and recommend fold-in vs. retire, before `golden_spiral_recall.md`'s own Phase 2/3
shadow builds start. See job-queue for the full briefing.

---

## 10. What I read, precisely (for the record — the no-sampling discipline)

**Read in full, this session:** `core/memory/store.py` (2,887 lines, 3 chunked reads covering every
line), `core/memory_levels.py` (989 lines, 2 chunked reads), `core/world_consolidation.py` (271),
`core/ghost_tuples.py` (280), `core/memory_dynamics.py` (145), `core/world_clock.py` (117),
`core/experienced_tuple.py` (149), `core/euclidean_recall.py` (161), `core/memory_edges.py` (984),
`core/identity_estate.py` (388), `core/identity_projection.py` (193), `core/felt_recall.py` (450, from
the worktree — see §5), `docs/staged/golden_spiral_recall.md` (200), `docs/staged/memory_as_a_service.md`
(228), `docs/plans/memory_multiway_linking.md` (315), `docs/plans/identity_estate.md` (263).

**Read substantially, targeted by section (not a tail sample — grep-located sections read in full):**
`docs/memory_levels_plan.md` (2,704 lines total; read in full: lines 1-283 [§0-§7 intro through Phase 3],
2401-2430 [§10 decisions], 2495-2549 [§11 tail + §12 object taxonomy in full]; the remaining ~2,150 lines,
mostly dated Phase-0/1 findings entries and §13-14 ported-ideas sections, were located via a full-file
grep for `claim|ladder|abstraction_level|promot` and their surrounding lines inspected, but not read
end-to-end).

**Named by the briefing but deliberately not opened this pass** (flagged, not silently skipped):
`core/associative_recall.py` (the trail engine's own hop-decay implementation — cited only via
`memory_multiway_linking.md`'s own description); the chaptering module that populates `abstraction_level=2`
for self-material (cited only via `store.py`'s `_ORIGIN_LEVEL` mapping); `docs/euclidean_memory_plan.md`
(the source design doc for §1.2 — handed to the spawned follow-up job, §9).

**Also called:** `udms_get_change_dossier` on `core/memory/store.py` — confirmed 20 real (CONTRACT-layer,
static-AST) dependents, headed by `nodes/inner_monologue_node.py` (PMI 2.19 bits) and
`core/orchestrator.py` (PMI 4.11 bits); the full dependent list is in this job's findings-log entry.
