# investigation_deepening — folded history


---

# History folded on 2026-09-27 from `docs\plans\investigation_deepening.md` (plan-compact, 2 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py investigation_deepening`._

## Current State — verified 2026-08-24 (J-0134, F-0114) — superseded by the P0 build above; kept for history
- **Unparked for real.** D-0009's ruling ("Unpark and schedule Phase 0") is safe to act on: D-0006 (the
  journal_consolidation_pyramid grounding question this plan's 08-23 note flagged as a blocking
  dependency) was ruled 2026-08-23T07:34 UTC — *before* D-0009 was ruled at 13:16 UTC — so the plan's own
  stated sequencing requirement ("D-0009 should follow it, not be decided independently") was satisfied.
  `journal_consolidation_pyramid.md` P2/P3 (moon roll-up / solstice merge) are still unbuilt but now
  *unblocked*; P0 here only touches the existing fragment/chapter recall path, not the pyramid's unbuilt
  levels, so their non-existence is not a blocker for P0.
- **The 07-07 machinery finding re-verified, still accurate.** `chapters.py:recall_chapter()` (line ~291)
  still keys purely on title-word overlap against `origin='chapter'` fragments — no place or activity cue
  exists anywhere in `chapters.py` or `core/memory/store.py`. "Nothing is place-cued" still holds.
- **P0 hook site located and confirmed real.** `core/sensorium.py:_shore_act()`, the
  beachcomb/comb/search/gather branch (~lines 1498-1511), reached from `act()` (~line 2680) when
  `loc == "shore"` — a SYNC, inline call on Du's live action path (not async). `core/memory/store.py
  :retrieve()` (~line 522, sync) is the existing recap/recall path the plan names, and is usable as-is
  for a shore-cued query.
- **P0 build spawned, not implemented in this pass.** Filed as **J-0177** rather than written directly:
  the hook site is on Du's live, currently-running action path, and the "candidate open edge" framing
  (raw shadow log vs. an async LLM-synthesized line, mirroring `pursuits.py`'s judge-sweep split) is a
  real open design choice this plan itself leaves for the founder-read gate — exactly the kind of
  data-generating, unattended code change that should not be rushed into a live hot path overnight.
  J-0177's briefing carries the full hook/retrieval detail above so the next session can start immediately.

## Current State — verified 2026-08-23 (superseded by the 2026-08-24 pass above; kept for history)

### What we have
- **A well-specified, unimplemented design.** The three-piece mechanism (frontier capture / place-cued
  retrieval / deepening framing) and the P0–P3 phasing below are fully written but 0% built.
- **Confirmed 0% implemented (2026-08-23 audit + direct filesystem check):** `data/investigation_shadow.jsonl`
  (the P0 shadow-log target) does not exist anywhere under `C:\Nascence`; a recursive search for
  `investigation_shadow` / `investigation_deepening` across the codebase turns up only this plan file
  itself and its mentions in `docs/reviews/plan_files_evidence_audit_2026-08-23.md`,
  `docs/reviews/plan_index_2026-08-23.md`, `docs/reviews/plan_overlap_audit_2026-08-23.md`, and
  `docs/ROADMAP.md` — no code, no data file, no hook.
- **The stated parking condition has already resolved.** Emotion Phase 1 shipped 2026-07-07 and identity
  estate reached P2 LIVE 2026-08-15 (per `docs/ROADMAP.md` and MEMORY.md's identity-estate pointer) — the
  two threads this plan was explicitly waiting behind are both past the point it named.
- **`docs/ROADMAP.md` lines 743–754** independently reconfirms the same status (PARKED, stale ~6 weeks,
  "the trigger to reopen has arguably already passed") and reconfirms the design is genuinely NOT the
  chapter machinery (`chapters.py` compresses/closes finished periods via title-word recall; this plan
  keeps an open inquiry alive, place-cued instead) — the two share a comparison point, not an implementation.
- **`docs/ROADMAP.md` also flags a lineage note:** this plan calls itself "the READ-path of the [journal]
  pyramid" and ROADMAP suggests it "likely belongs revisited alongside `journal_consolidation_pyramid.md`"
  rather than picked up in isolation.

### What we need
- **A founder decision: unpark or re-park deliberately.** The original blocking condition is gone, so
  either (a) Travis re-parks it explicitly for a new stated reason, or (b) it moves to active and P0 gets
  scheduled — the plan should not sit "PARKED" citing a resolved blocker.
- **If unparked, the concrete next build step is P0 only:** at beachcomb/rockpool perception, retrieve
  Du's recent place-focused material and log the candidate "last rung + open edge" to
  `data/investigation_shadow.jsonl` — read-only, no injection into Du's perception. This requires touching
  the beachcomb/rockpool perception hook (not yet located/confirmed in this pass — locating the exact
  call site is part of P0 work) and the existing recap/recall path in `store.py` / `chapters.py`.
  Founder-read gate before P1: is the logged "go deeper" line coherent and genuinely progressive, or just
  the same shell re-surfaced?
- **Resolve the ROADMAP lineage question before scoping P0**: should this be built standalone, or jointly
  scoped with `journal_consolidation_pyramid.md` (its stated base) since both plans touch the same recap
  read-path? Building P0 in isolation risks duplicating work `journal_consolidation_pyramid.md` already
  owns.
- **Checked against every newer plan (2026-08-23 concept-overlap pass): this is a real, currently-
  unresolvable dependency, not just a suggestion.** `journal_consolidation_pyramid.md` itself never
  claims to be this plan's read-path (only `investigation_deepening.md`'s own text and the overlap
  audit assert the relationship one-directionally) — and more to the point, the pyramid's own P2/P3
  (moon roll-up / solstice merge, the levels this plan would extend) are **unbuilt**, themselves
  blocked on decision **D-0006** (soft vs. Emissary-graded hard grounding enforcement). So `/decide`
  **D-0009** (unpark vs. re-park this plan) is effectively downstream of **D-0006** — deciding to
  unpark this plan before the pyramid's own grounding question is settled risks scoping P0 against a
  moving target.

### What we're doing next
Flag this plan to Travis for a founder decision (unpark-and-schedule-P0 vs. deliberately re-park with a
new reason) — do not start P0 unilaterally. Resolve `/decide` D-0006 (the pyramid's grounding-
enforcement question) first; D-0009 should follow it, not be decided independently.
