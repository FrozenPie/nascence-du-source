# Du Recall Lens Upgrades — Three Proven Techniques Awaiting Wiring (2026-08-27)

> Status: 🟡 SHADOW — all three lenses built. Lens 1 (spectral diffusion) 2026-08-29 (D-0070,
> J-0345). Lenses 2 (fact anchoring) and 3 (counterfactual-ensemble re-ranking) built 2026-09-05
> (D-0170, founder-direct un-park) — shadow-only, additive to `core/associative_recall.py`. Effect
> sizes for Lenses 2-3 remain UNCITED (F-0399) pending real shadow-log accumulation; see the Lens
> 2/3 build note below for why that accumulation now stands in for the offline rolling-window
> harness this doc originally called for.

```plan-state
stage: shadow
phase: All 3 lenses built shadow-only (Lens1 08-29, Lens2/3 09-05); accruing comparisons toward the >=200-each stability bar
verified: 2026-11-14
evidence_read: 2026-11-06
gate: J-3507's usage proxy field present on >=200 energy_norm=minmax rows in each of data/associative_recall_lens{1,2,3}_shadow.jsonl (D-0684's defeater)
next: D-0684 ruled A (travis, 2026-11-06): HOLD all three lenses shadow-only. Build J-3507 (usage proxy on the lens shadow rows, restart-gated), then a >=200-proxy-rows-per-lens read re-asks promote/hold/tighten/retire per lens
cluster: 0
```


## What this is

The UDMS research program (now split out to `C:\UDMS`) began as an attempt to improve Du's memory
recall on similar subjects. Its 35-script "cognitive substrate" cluster ran real experiments against
Du's real telemetry (`data/geometry_tuples.jsonl`, 22,091 tuples; `data/memory/nascence.db`). A
full 12-agent verification pass (2026-08-27, see `C:\UDMS\docs\plans\udms_lens_atlas.md` and
`udms_orphan_scripts_master_catalog.md`) separated what actually worked from narrative. **Three
lenses are proven on Du's real data and were never wired into Du.** This plan parks them properly.

## Current State — verified 2026-11-14

- **2026-11-14** (F-4535): J-3507 built lens usage proxy (kind lens_usage rows in each lens shadow log, restart-gated, commit 3c5c5101 in worktree). Read needs >=200 usage rows per lens.
- **2026-11-06** (F-4118): J-2289 done 2026-11-06 (F-4118): D-0170 direction-stability gate read on 342 minmax rows per lens; every lens changes the trail stably in every run (L1/L2 100% of rows, L3 93%, L1-vs-L2 jaccard 0.60 as offline), so the defeater does not fire on what the logs measure, but the logs carry no usage/quality signal; lenses replace ~3/4 of the 10 non-seed slots (ceiling hit 23-30%), walled new ids 37-41%. D-0684 opened for the founder's promote-or-hold call; J-3507 spawned to add the m2_usage-style proxy to the lens rows.

- **2026-11-06** (F-4099): 2026-11-06: J-2356 read DONE. D-0472's defeater does not fire: top1_changed 40/295 = 13.6% on the seed_blend_v1 rows (offline expected 35-45%), every change an existing trail item, 0 brand-new candidates at #1; retrieve got faster across the same restart (J-2275 fast path), lens compares run off-loop, so no measurable re-rank cost. Breadth cost live is -1.06 new_vs_greedy (8.36 -> 7.30) vs -0.3 offline, walled_new 1.57 -> 2.99. Du down since 2026-11-05 19:10.
- **2026-11-06** (F-4093): 2026-11-06: J-2356's gate is MET (295 rerank==seed_blend_v1 rows in lens3_shadow, 10-18 to 11-05; top1_changed 40/295 = 13.6%, below F-3041's 35-45% offline expectation, not ~0). The read has not been run.

- **2026-10-17** (F-3041): J-2350 (D-0472 A): Lens 3 now re-ranks trail items by leave-one-out support, shadow-only; offline top1_changed 0/40 -> 15-17/40, breadth kept; live path byte-identical; worktree commit ab798d0c, restart-gated
- **2026-10-17** (F-2983): J-2257 10-17: fix merged and live, but only 16 energy_norm rows per lens (~1.2/h); read deferred to successor not-before 10-23 (F-2983).

- **2026-10-16** (F-2943): J-2208 fixed the F-2907 lens energy-scale bug (worktree commit 2ee40d51, restart-gated): min-max energy normalisation in the shared diffusion helper plus a Lens 3 consensus fix; offline 37-40 of 40 trials now add real local neighbours per lens; lens rows carry energy_norm so the D-0170 200-row read restarts at the first post-fix boot; Lens 3 top1_changed is structurally always false (design question)
- **2026-10-16** (F-2907): First read of the >=200-row gate: all three lenses are a no-op -- 3010/3010 shadow rows identical to the greedy trail because diffusion energy (~0.01) times peak activation never clears ACT_THRESHOLD 0.13. D-0170's direction-stability read cannot be made from this log; J-2208 fixes the energy scale, then the 200-row clock restarts from the first post-fix boot.

### What we have
- All three lenses proven on real data and built shadow-only: Lens 1 (spectral diffusion, +2.69pp, reproduces at +3.08pp per F-0399's independent re-run) BUILT 2026-08-29 (D-0070, J-0345/F-0437); Lens 2 (fact anchoring) + Lens 3 (counterfactual-ensemble re-rank) BUILT 2026-09-05 (D-0170, founder-direct un-park).
- Lens 2/3's specific effect sizes are direction-stable but size-unstable across re-runs (F-0399) — D-0170 shipped them shadow-only against Du's real, growing trail instead of an offline rolling-window harness, specifically so the accruing shadow log substitutes for that harness.
- No ledger activity since the 2026-09-05 Lens 2/3 build (checked this pass) — nothing new to fold in.

### What we need
- >=200 real shadow comparisons each on Lens 2 (`data/associative_recall_lens2_shadow.jsonl`) and Lens 3 (`data/associative_recall_lens3_shadow.jsonl`) before D-0170's own named defeater (effect DIRECTION instability, not just magnitude) can be checked.

### What we're doing next
- Nothing dispatched — the plan is purely accrual-gated; the next real action is reading those two logs once the row counts clear the bar.

## How it would compose (design sketch, NOT a build commitment)

The three lenses compose naturally into one recall pipeline: **anchor** (add deterministic facts as
seed nodes) → **diffuse** (spectral propagation over the co-occurrence graph) → **re-rank**
(counterfactual consensus for the top slot). Natural wiring point: `core/associative_recall.py`.

**Composition constraints with active work — read before building:**
- `associative_recall.py` just gained the M2 edge-aware shadow trail (J-0263, D-0022, 2026-08-25).
  Any build here must compose with that shadow work, not race it — same file, same recall path.
- `docs/plans/memory_knowledge.md` Improvement 2 (seeded Personalized PageRank) is the same *family*
  of upgrade (principled graph propagation replacing the greedy walk). The UDMS diffusion evidence
  is the closest thing to empirical support that family has — a future build should treat PPR and
  heat-kernel diffusion as competing implementations of one slot, benched against each other, not
  two separate features. Cross-reference D-0005's "compose, don't duplicate" ruling.
- Everything here obeys the observe-first law: shadow log alongside the live trail before any flip,
  same discipline as M2's own kill-criterion sheet.

## Activation gate

Do not build until: (a) founder un-parks this via `/decide`, and (b) the M2 shadow read (J-0280)
has landed, so the composition question above is answered with real data rather than guessed.

**Lens 1 gate MET 2026-08-29** (D-0070 un-parked it explicitly, ahead of M2's gate landing, ruling
"proceed toward M2 in parallel rather than waiting serially").

**Lenses 2-3 gate MET 2026-09-05** (D-0170: founder un-parked both directly in a live session,
satisfying condition (a) explicitly; M2's shadow read had already landed well before this,
satisfying (b)). The separate rolling-window-harness requirement this section used to name is
addressed differently than originally sketched — see the Lens 2/3 build note below.

## Build note — Lens 1, 2026-08-29 (J-0345)

Built as `recall_trail_spectral_diffusion()` + `shadow_compare_lens1()` in `core/associative_recall.py`
— purely additive (147 insertions, 0 deletions; `git diff --stat` confirms zero lines touched in
`recall_trail_edge_aware`/`shadow_compare`, M2's own functions). Ported from
`C:\UDMS\core\math\spectral_diffusion.py`'s `SpectralDiffusionEngine` (the Lens 1 reference
implementation, same K_t = exp(-t*L) truncated-Taylor math) but reimplemented over a small LOCAL
embedding subgraph (seeds + each seed's `NEIGHBORS_PER` nearest neighbours) with plain dense numpy
instead of scipy.sparse — avoids a new hard dependency and any cost blow-up on the full fragment
store, unlike the UDMS script's global concept-cooccurrence graph.

Shadow-only, composed on top of `recall_trail`'s completed output (same additive pattern
`recall_trail_edge_aware` already established), logged to its own **separate** file
(`data/associative_recall_lens1_shadow.jsonl`, not M2's `data/associative_recall_shadow.jsonl`) so it
can never race or corrupt M2's in-flight shadow trail (J-0280). Wired into
`core/orchestrator.py`'s `_retrieve_memory` right after the existing M2 shadow-compare call, as its
own separate try/except block — the M2 call site itself is untouched.

Verified before landing: UDMS change dossier (`udms_get_change_dossier`, target
`core/associative_recall.py`) — CONTRACT-layer hits (imports) are `core/guidance_learning.py`,
`core/memory/store.py`, `core/memory_edges.py`, `core/orchestrator.py`, `core/schema.py`, plus the
dream/inner-monologue node backups; none of that set is touched by this build beyond the one
additive orchestrator.py call site. The dossier's CYCLIC_FEEDBACK_LOOP warning names
`core/heavens.py`/`core/world_clock.py`, unrelated to this file's own content — not a signal against
this change. Smoke-tested standalone (fabricated embedding matrix + monkeypatched `_embed`,
scratchpad script, not committed) confirming `recall_trail_spectral_diffusion` runs and
`shadow_compare_lens1` writes to its own isolated log file correctly. `data/associative_recall_shadow.jsonl`
row count checked before (64 rows) — this build never touches that file, so it is unaffected by
construction (confirmed no code path writes to `_LOG` from the new functions).

## Build note — Lens 2 & 3, 2026-09-05 (D-0170)

Built as `recall_trail_fact_anchoring()` + `shadow_compare_lens2()` (Lens 2) and
`recall_trail_counterfactual_consensus()` + `shadow_compare_lens3()` (Lens 3) in
`core/associative_recall.py` — purely additive (293 insertions, 0 deletions across the whole file;
`git diff --stat` confirms zero lines touched anywhere else, including Lens 1's and M2's own
functions). Both reuse Lens 1's `_local_spectral_diffuse` helper unchanged rather than
reimplementing diffusion a third time.

**Why this wasn't the offline rolling-window harness this doc originally asked for.** F-0399 found
Lenses 2-3's specific effect sizes swing hard across a single 70/30 chronological split on the same
static `geometry_tuples.jsonl` — a second offline script re-running the same static file with more
splits would still be measuring a finite, non-growing dataset. D-0170's ruling instead ships both
lenses shadow-only (zero live-cognition impact, identical safety profile to Lens 1) so they log a
comparison every real retrieval cycle, against Du's actual live, growing trail — a genuine rolling
window rather than a re-slice of the same historical file. The defeater is explicit: revisit before
either lens is ever considered for promotion if the accruing shadow logs show the effect DIRECTION
itself is unstable (not just magnitude) after >=200 comparisons each.

**Substrate adaptation (same kind Lens 1 already made).** Both reference scripts
(`test_p_deterministic_fact_anchoring.py`, `test_q_shape_constrained_prediction.py`) operate over a
discrete concept co-occurrence graph with named nodes ("diurnal_night", "rain_on_roof",
"cat_doorstep") that don't exist in Du's live embedding-based trail. Lens 2 reproduces the fact
node as one more embedded row in Lens 1's local subgraph (the diurnal day/night fact, embedded once
and cached since only two values ever exist), included as an extra seed and excluded from output by
the diffusion helper's own seed-exclusion. Lens 3 reproduces "several perturbed what-if seed-sets"
as leave-one-seed-out worlds (deterministic — no invented randomness) plus the Lens-2 fact-anchored
world, and boosts candidates whose diffusion energy recurs across >=2 worlds; original seeds are
never re-scored by it, only their neighbours.

Logged to their own files (`data/associative_recall_lens2_shadow.jsonl`,
`data/associative_recall_lens3_shadow.jsonl`) — separate from M2's and Lens 1's logs so none of the
four shadow instruments can race each other. Wired into `core/orchestrator.py`'s `_retrieve_memory`
as two more additive try/except blocks, right after Lens 1's own call, in the same place and shape.
Lens 3's shadow row specifically logs `top1_changed` (whether the #1 slot moved) since the source
finding's actual claim was about the top-1/top-3 trade-off, not just new-candidate counts.

Verified before landing: smoke-tested standalone (fabricated 14-fragment embedding space,
monkeypatched `_embed`, scratchpad script, not committed) — both recall functions run without
error, handle an empty base and a single-seed trail (no leave-one-out possible) without crashing,
and both shadow-compare wrappers write correctly-shaped JSON lines when redirected to scratch log
paths; confirmed the real `data/associative_recall_lens{2,3}_shadow.jsonl` files were not touched
by the smoke test. Not yet verified against the live embedding store (needs a live retrieval cycle
after Du's next restart — this build cannot take effect on the currently-running process).

## Pointers

- Evidence atlas: `C:\UDMS\docs\plans\udms_lens_atlas.md` (§1 = the proven lenses, §5 = the
  cite-numbers-not-prose warning list)
- Full per-script catalog: `C:\UDMS\docs\plans\udms_orphan_scripts_master_catalog.md`
- The runnable experiments: `C:\UDMS\scripts\test_{d,h,p,q,n}_*.py`
- Sibling active plans: `docs/plans/memory_multiway_linking.md` (M2), `docs/plans/memory_knowledge.md`
  (Improvement 2/PPR), `docs/staged/geometry_tuple_index.md` (the indexing side of the same program)
