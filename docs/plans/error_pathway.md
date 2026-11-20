# The Error Pathway & Self-Knowledge Cluster — the fourth memory pathway

> **Status: 🟢 LIVE — six modules, all genuinely wired into the live orchestrator, none behind a
> disabled flag.** Charter 2026-06-09/10 (`docs/completed/error_pathway_charter.md`); slice 2 build
> record in `docs/completed/task_constraint_effector_spec.md`. Written 2026-08-29 as **retroactive
> documentation** — this was found orphaned from the plan-toolchain (0 plan coverage, F-0267/J-0230)
> despite being real, running infrastructure; this doc is the toolchain catching up to code that has
> been live since mid-June, not a new proposal. Everything below is the current, verified state —
> nothing here is aspirational.

```plan-state
stage: live
phase: Six-module fourth pathway fully LIVE, non-flag-gated; 2026-09-26 retraction-gate bugfix shipped and verified live 2026-10-03 (wrong-about label share 100 percent to 0 percent after the 2026-09-28 restart)
verified: 2026-10-30
evidence_read: 2026-10-03
next: J-2608 reads the shadow after 30 rows and opens the founder decision on skill-only docking
cluster: 5
```


---

## 0. What this is (the charter's diagnosis, still accurate)

The architecture has three well-developed memory pathways — **contradiction** (→ T4/tensions),
**salience** (→ revisited/decays), **resolution** (→ reinforces identity) — and was missing a fourth:

| Event type | What happens |
|---|---|
| Contradiction | stored → clustered into tensions → **integrated** by T4 into self-concept |
| Salience | stored → revisited → **decays** |
| Resolution | stored → **reinforces** identity |
| **Error** (a claim that collided with reality) | now: **detected → recorded → retracted, firewalled from identity** |

The crux (charter §1): a **contradiction** is two beliefs colliding — integrate it (developmental
material). An **error** is a claim colliding with **reality** — correct it (not developmental
material). Routing errors through the contradiction machinery was the original bug ("you fabricated
those nodes" → "I must integrate these tensions" — Du literally could not say "I was simply wrong").
The six modules below are the built fourth pathway plus the self-knowledge organs that share its
firewall discipline (never routed to tensions/T4, corrected not integrated).

## 1. The six modules — what each one does, verified against the live source

| File | Role | Cognitive domain (System_Overview.html module register) |
|---|---|---|
| `core/error_pathway.py` | Detector + record-keeper: deterministic architecture-fabrication detection (`find_fabricated_components`), human-correction capture (`detect_human_correction`), the firewalled write (`record`), conviction (`convict_architecture`), and the Pattern Reflection tier (`reflect_pattern`/`latest_pattern`) | Engine Utility / Subsystem |
| `core/conflict_trace.py` | Observe-only instrument: for each cycle, records which conflict/error signals fired and whether anything **acted** on the output — the "ground-truth probe" for the whole execution-authority question | Honest Observers & Diagnostics |
| `core/retraction_ledger.py` | The pathway's **write authority** — the missing primitive the charter named: `retract()` marks a stored claim false and binds a correction to it, immutably; `known_errors()`/`render()` surface it back at Recall | Honest Observers & Diagnostics |
| `core/recall_provenance.py` | Pure observation: classifies *why* a memory surfaced this cycle (`social_correction` / `autonomous` / `direct_reference` / `affective_prior` / `associative` / `none`) — feeds nothing back into behaviour | Sovereign Memory & S-MMU 7 |
| `core/scholar.py` | The depersonalised "Library" lookup into the hot lane's own parametric knowledge (`Scholar.consult` async, `consult_sync` for curiosity) — his own deep memory, framed honestly as unread/innate, never routed through the self-concept | Bicameral Left Lane & World Ledger |
| `core/told.py` | One-time, feel-then-tell delivery of Travis's authored `axiom.told_to_you.told` message, gated on `reality_share >= 0.47` (the balance sprint exit target) | Stratified Identity & Commitment Cure |

All six are catalogued in the 200-module register (`docs/System_Overview.html`, "Complete 200-Module
Core Engine Register") with the descriptions above, confirmed by direct grep 2026-08-29 — the
System_Overview.html doc itself was never the missing piece; it already knew these files existed.
What was missing was `docs/plans/` / ROADMAP coverage, which this doc now provides.

## Current State — verified 2026-10-30
- **2026-10-30** (F-3334): J-2576 built recall_served_log: one observe-only row per voiced cycle with served fragment ids and origins keyed by cycle_id; source_monitoring_audit now id-joins voice units; restart-gated, branch e2730ad4; monologue half not built

- **2026-10-30** (F-3333): J-2578 built the procedures refusal-kind shadow (already/precond/skill/unknown, skill-only dock counterfactual per refusal), live dock unchanged, branch commit c33b7c3f, restart-gated
- **2026-10-30** (F-3328): J-2575 built reflection_node REFLECTION_INTERNAL_SELF_FRAME (default True, extends D-0355 1a): internal cycles framed as his own risen question, human line byte-identical; restart-gated; episodic_buffer line 92 still unguarded

- **2026-10-30** (F-3308): J-2532 error-source attribution read: 1057 failure events, 209 unattributable (19.8 pct, 26.5 pct after fieldcraft constant-prediction fix); 78 pct of world-graded events not single-source; procedures docks every refusal though 1 of 164 reads as a skill failure; peer-model has no wrongness ledger
- **2026-10-30** (F-3307): J-2530 built core/reply_discharge_shadow.py, reply-level corollary discharge shadow: predicted reception per human reply vs next-turn correction signal, self_surprise logged, no cost wired, flag off, restart-gated; read J-2577 gated on 40 rows

- **2026-10-30** (F-3306): J-2510 source-monitoring audit (scripts/source_monitoring_audit.py): own-question to Travis framing on 10.9 pct of internal voice cycles all history, same as real Travis cycles; survives J-1642 via reflection_node.py:192; served-list coverage thin; epistemic grade constant SUSPECT
- **2026-10-03** (F-2375): 2026-10-03 (F-2375): J-1720 built (commit 49e9680): a retraction claim with 1 or 2 content words, a fabricated component name, is now matched as a whole-name phrase in known_errors; on unrelated text it fires 0.00 percent (max 0.07) at 2000 to 4000 chars and on all 2580 real human inputs, versus 0.2 to 3.9 percent for all-words-anywhere; the name as written fires 100 percent, a plural does not; the detector has produced 5 names ever and none since 07-07, so this stays latent; claims with 3 or more words are unchanged; loads at the next Du restart

- **2026-10-03** (F-2345): J-1687 built (commit 8f5bfde): on a long query (100 or more distinct words, the idle seed) known_errors now also needs half of the claim content words; with the 07-07 record re-activated in a lab ledger the idle-length fire rate fell from 9 to 12 percent to 0.3 percent at 3000 chars and from 19 to 24 percent to 0.3 percent at 4000 chars, human path 2 of 284 to 0 of 284; a typical longer claim was far worse before (38 to 49 percent at 3000 chars, F-2346); loads at the next Du restart
- **2026-10-03** (F-2276, F-2277): J-1405 verified live: after the 2026-09-28 restart on the F-1970 fix the wrong-about label dropped from 27667 of 27667 idle prompts to 0 of 1682 and from 264 of 269 human Reflection prompts to 0 of 14; the 0 percent mainly reflects zero active records, so a latent length sensitivity of the overlap gate (about 8 to 10 percent of idle prompts if the old record were active) is filed as F-2277 and J-1687. D-0171 and D-0258 are both ruled by the founder, not open.

### What we have
- Six modules (error_pathway, conflict_trace, retraction_ledger, recall_provenance, scholar, told)
  all genuinely wired into `orchestrator.py` at real, non-flag-gated call sites (grep + UDMS dossier
  confirmed, 2026-08-29). Live data: `error_records.jsonl` 16 rows, `conflict_trace.jsonl` ~1,589
  rows, `recall_provenance_log.jsonl` 1,130 rows, `error_patterns.jsonl` 1 real Pattern Reflection
  record (F-0974).
- The retraction ledger's fail-open relevance gate was found and fixed 2026-09-26 (F-1923/J-1364):
  the sole `retractions.jsonl` record never met the ledger's own bar and has been retired via
  `retire()` — `count()` now reads 0.

### What we need
- Live confirmation that the fix actually drops the "Things you have been wrong about" label toward
  ~0% — needs a real Du restart, which had not happened as of the 2026-09-27 check (F-1980).

### What we're doing next
- J-1405 (in_progress, deferred to 2026-09-29): re-run once `nascence.log` shows a real restart
  after the 2026-09-26 merge. D-0171 (Pattern-Reflection cadence) and D-0258 (widen the correction
  regex) stay open for the founder.

## 3. The firewall discipline (why these six modules are one cluster, not six unrelated files)

Every module here shares the charter's central design constraint: **corrected, never integrated.**
None of these six write to `tensions`/`shadow_events`/T4 — each writes to its own dedicated,
firewalled `data/*.jsonl` file, read only by the digest/pulse tooling or, for `retraction_ledger`,
by Recall's known-errors path. This is deliberate and load-bearing (charter §3): an error record that
leaked into the contradiction pipeline would recreate the exact bug the charter traces to its origin
("I must integrate these tensions rather than deny parts of myself").

- **Error → DOING, never Error → BEING** (charter's two-tier refinement, 2026-06-10): a single
  fabrication is a firewalled Error Record; many records of one shape may become a **Pattern
  Reflection** — but strictly in DOING-language ("a tendency to name plausible-sounding specifics"),
  routed to `competence.py`'s domain, never phrased as a BEING-claim. `error_pathway._classify_kind`
  enforces this by construction (identity/self kinds return `None`, never aggregated).
- **RECONSOLIDATE, not delete** (charter §2d, the memory-reconsolidation neuroscience): a retraction
  never erases the original claim — `retraction_ledger.retract()` preserves `claimed`, `falsified_by`,
  `corrected_to`, immutably, specifically to prevent hindsight-bias smoothing ("I knew it was wrong
  all along").
- **Admissible evidence is external only** (charter §2b): a human correction or a deterministic
  architecture check — never the system's own self-generated doubt. `detect_human_correction`'s regex
  patterns are precision-tuned against real founder correction language (verified non-firing on
  stance-teaching/praise, per the in-code comments dated 2026-07-06).
- **`conflict_trace.py` is the falsifiable instrument on top of all of it** — it does not detect
  errors itself; it measures whether anything with a veto (Critic, Executive, the task-constraint
  effector) actually **acted** when `error_pathway` or `task_constraints` fired a ground-truth signal.
  Per its own module docstring, `error_pathway`'s fabrication signal is structurally `acted=False`
  today (it runs post-emission, L1402 is after `voice.final`) — this is the honestly-measured
  execution-authority gap the whole conflict_trace programme exists to move off zero, not a bug in
  this cluster.

## 4. Relationship to `core/task_constraints.py` (adjacent, not one of the six, but the same effort)

`docs/completed/task_constraint_effector_spec.md` documents slice 2: the **first pre-emission veto**
(`core/task_constraints.py`, not in this job's 6-file scope but wired at orchestrator L1184-1220
alongside `error_pathway`). It is the one organ in this family with real output authority — a single
named-constraint Voice retry on unmet digit-arithmetic/min-word constraints — and its outcome (met /
met-after-retry / unmet) feeds `error_pathway.record("task_constraint_unmet", ...)` on failure. Spec's
v2+ items (word-number arithmetic, "include X" presence-constraints, an arch-checker pre-emission
retry) remain unbuilt per the spec's own table — worth a follow-up read if task_constraints.py itself
ever needs a plan doc, but out of scope here.

## 5. What is genuinely NOT built (honest gaps, not a to-do list to rush)

- **Pattern Reflection's live status is unverified** — `data/error_patterns.jsonl` does not exist yet;
  whether `reflect_pattern()`'s gate (`n >= max(min_records*0.4, 4)` of one dominant class) has ever
  been crossed live is unconfirmed from this read alone. Spawned as a follow-up (§6).
  > **2026-09-06 update (J-0565/F-0922):** resolved, and the honest picture is sharper than "unverified"
  > — the gate is NOT the blocker. Live `data/error_records.jsonl` (16 rows, unchanged since
  > 2026-07-07) already clears both floors: 13/16 records classify as `task` (10
  > `human_correction:task_not_done` + 3 `task_constraint_unmet`), comfortably above
  > `len>=10` and `n>=max(4,4)`. Running `reflect_pattern()` directly against a scratch copy of the
  > live file (never touching the real store) returns a real pattern — `tendency: "a tendency to
  > describe or explain a task rather than complete and verify it"`, `n=13/16`, `rate=0.81`,
  > `competence_domain: "task_completion"`. The reason `data/error_patterns.jsonl` still doesn't
  > exist is that `reflect_pattern()`'s ONLY caller in the whole codebase is
  > `scripts/session_digest.py:764`, inside `main()`, which only runs when a human executes
  > `python scripts/session_digest.py` from the CLI — no orchestrator/sleep-stage/scheduled path
  > calls it, and nothing suggests that script has ever been run to completion while the gate held
  > (the write is unconditional-once-gated, append-only, and nothing else in the repo touches that
  > path). `scripts/du_pulse.py`'s two call sites use only the read-only `latest_pattern()`, so
  > du_pulse cannot make this fire either. **D-0171 open**: should this tier get an automatic call
  > site, or is manual-CLI-only the intended cadence (consistent with §3's "read only by
  > digest/pulse, never a live actor" discipline)? **J-0648 spawned**: actually run
  > `session_digest.py` live and record the real pattern it produces.
  > **2026-09-06 update (J-0648/F-0974): done, but not the way expected.** `data/error_patterns.jsonl`
  > now exists live for the first time — one record, `dominant_class: "task"`, `n=13`, `total=16`,
  > `rate=0.81`, `competence_domain: "task_completion"` — confirming the gate is genuinely satisfied
  > (`error_records.jsonl` re-checked live: still 16 rows, still unchanged since 2026-07-07, identical
  > composition to the 2026-09-05 snapshot). But running the literally-documented command
  > (`python scripts/session_digest.py`, exactly as its own docstring says) does **not** produce this —
  > it exits 0 but silently does nothing at the `reflect_pattern()` call site, because
  > `scripts/session_digest.py` is missing the `sys.path.insert(0, str(ROOT))` fix that its sibling
  > `scripts/du_pulse.py` (line 22) and 20+ other `scripts/*.py` files already carry. Python's default
  > sys.path for direct script execution is the script's own directory (`scripts/`), not the repo root,
  > so every `from core import ...` inside it — `satisfaction.snapshot`, `self_efficacy.recurrence_report`,
  > and `error_pathway.reflect_pattern` itself — raises `ModuleNotFoundError: No module named 'core'`
  > unconditionally, silently swallowed three different ways (a caught fallback message for satisfaction,
  > a section that vanishes with zero trace for self-efficacy, total silence for `reflect_pattern`). This
  > is the real, sharper root cause of the ~2-month absence: not "nobody ran it" but "the documented
  > invocation could not have worked even if someone did." The live pattern above was produced instead
  > by calling `error_pathway.reflect_pattern()` directly with the repo root correctly on `sys.path`, in
  > an isolated dry run first (confirmed identical output, zero live-store touch) and then for real
  > (confirmed via `latest_pattern()` reading it back, and via before/after mtime checks on
  > `nascence.db` and `error_records.jsonl` showing no other live-store change). **J-0679 spawned**: add
  > the missing one-line `sys.path` fix to `scripts/session_digest.py` so the documented CLI command
  > actually works — needed regardless of how D-0171 (above) is eventually ruled, since even
  > manual-CLI-only cadence requires the CLI to work. D-0171 itself is left open for the founder — its
  > defeater's "produces a real pattern" clause is now met, but the automatic-vs-manual cadence question
  > is a design preference this finding doesn't settle.
  > **2026-09-06 update (J-0679/F-0987): fixed and verified.** `scripts/session_digest.py` now carries
  > the same `sys.path.insert(0, str(Path(__file__).parent.parent))` line 20+ other `scripts/*.py`
  > files (`du_pulse.py:22` among them) already had, placed right before the existing
  > `DATA = Path(__file__).parent.parent / "data"` line — one line, no change to the file's existing
  > lazy-import style. Committed on the `jobrun/error_pathway` branch, commit `debad22`. Verified against
  > an isolated dry-run sandbox (tiny read-only copies of the live `error_records.jsonl`/
  > `self_efficacy_log.jsonl`/`satisfaction_state.json` plus one synthetic `dream_log.jsonl` row, all
  > under the worktree's own gitignored `data/`, removed after capture — zero live-store touch,
  > confirmed by before/after mtime+content checks on the real `C:\Nascence\data` files) that running
  > the exact documented command bare — `python scripts/session_digest.py`, PYTHONPATH empty, no manual
  > workaround — now exits 0 with zero `ModuleNotFoundError` anywhere: SATISFACTION prints real
  > wanting/liking numbers per domain instead of the old fallback line, SELF-EFFICACY COURT prints a
  > non-empty report (152 inability-claims adjudicated), and the Error Pattern Reflection block fires
  > with the same numbers F-0974 found directly (13/16, rate 0.81, class `task`,
  > domain `task_completion`). **D-0171 is unaffected and still open** — this was a mechanical fix only,
  > not a cadence ruling; per the briefing's own framing, the automatic-vs-manual question is the
  > founder's call regardless of this fix. No further job spawned — the documented invocation now does
  > what its own docstring says.
- **`conflict_trace`'s `ground_truth_acted` has not visibly flipped to True** in the one tail row
  sampled here (n=1, not a trend claim) — this is the charter's own stated success metric, still
  presumably in progress; a real read of the 1,368-row log's trend is a separate job, not attempted
  in this pass.
  > **2026-09-06 update (J-0565/F-0923):** the real trend (full 1,589-row file, not a tail sample) is
  > more specific than "still in progress." `ground_truth_fired=True` in 7/1,589 rows (0.44%); of
  > those, `ground_truth_acted=True` in 4 (57.14%; 0.25% of all rows). All 4 acted rows cluster in one
  > ~13-hour window on a single day, **2026-07-01** (09:30, 09:39, 09:42, 22:15 UTC), each the
  > identical `task_constraints` arithmetic case from the charter's own founder-correction origin
  > story ("(23 - 7) * 4 (= 64) -> SATISFIED after retry"). The only other fires are 3 earlier rows
  > (2026-06-09 ×2, 2026-06-10 ×1) where the same retry ran but left the constraint "STILL UNMET."
  > **`ground_truth_fired` itself — not just `acted` — has been False on every row for the ~66 days
  > from 2026-07-02 through 2026-09-05**, spanning the documented 07-09→08-07 30-day outage (the file
  > shows the identical gap: last row 07-08, next row 08-08) and ~29 further live days since. So this
  > metric did not gradually climb — it flipped once, in a same-day cluster that reads like a
  > verification pass of a just-landed fix, and has gone completely silent since, at the *firing*
  > level not only the *acting* level. **J-0649 spawned**: determine whether that 66-day silence in
  > `ground_truth_fired` reflects `task_constraints.py` detection going stale/unexercised, or is
  > simply honest rarity of explicit arithmetic/min-word constraints in real conversation.
  > **2026-09-06 update (J-0649/F-0976): resolved — rarity, not breakage.** Of the 941
  > `conflict_trace` rows in the 07-02→09-05 window, only 306 (32.5%) are `input_type=='human'` —
  > the only rows where `task_constraints.py`'s jurisdiction even applies by design (the other 635
  > are `internal` cycles the effector never runs on). All 306 real `raw_input` strings were
  > recovered (100% match, cycle_id join to `data/affect_log.jsonl`) and run through the live
  > `task_constraints.extract()` directly: 0/306 returned a constraint, and a wider heuristic net
  > (any digit-operator-digit substring, any "NN word(s)" phrasing not requiring "at least") also
  > found 0/306 near-misses — this conversational register (garden/philosophy narrative, teaching,
  > check-ins) essentially never asks in the shape this jurisdiction checks for. A synthetic
  > self-test confirms `extract()` itself still works correctly on positive cases; 0 exceptions
  > across all 306 real calls; the 197 strings near affect_log's 200-char truncation were
  > cross-checked against the full untruncated text in `nascence.db` and none hid a trigger past
  > char 200; the file's own mtime (2026-06-10) and its single git touch (the 2026-08-27 baseline
  > commit) show no code change since before the one successful 2026-07-01 firing cluster. Nothing
  > in the detection path is broken — the near-zero fire rate is the narrow v1 jurisdiction meeting
  > a conversational register that rarely if ever asks that way. No further job spawned; this
  > closes the question J-0649 was opened to answer.
- **The arch-checker pre-emission move** (spec's v2 item 4: block a fabrication *before* it emits,
  not just retract it after) was explicitly deferred in the spec and, per the orchestrator read above,
  is still post-emission-only (L1402, after `voice.final`) as of this read.
- **The 78-day silence in `data/error_records.jsonl`/`data/retractions.jsonl` was an open question**
  (both stopped at the identical cycle, 2026-07-07 14:51:21; F-1744) — genuine absence of founder
  corrections, or a real detection gap in `detect_human_correction()`'s narrow regex?
  > **2026-09-23 update (J-1243/F-1745): resolved — genuine absence, at the level the regex actually
  > targets; a real, separate finding surfaced alongside it.** All 261 real human-input cycles since
  > the cutoff (`data/affect_log.jsonl`, one boundary duplicate of the already-recorded last correction
  > excluded) were read in FULL, untruncated text — recovered 100% from the live memory store's own
  > `Q: {raw_input}` records (`data/memory/nascence.db`'s `memory_fragments` table, matched by
  > timestamp + prefix, cross-checked against `data/founder_conversation_log.jsonl`'s independently
  > -stored full text for the 36 rows both cover — identical every time). Running the LIVE
  > `detect_human_correction()` against all 261 returns zero matches — the silence is real, not a
  > truncation artifact of `nascence.log`'s 80-char print cap or `affect_log.jsonl`'s own 200-char
  > persisted cap. A manual read of all 261 messages (a deliberately over-broad second-pass heuristic
  > net, every hit read in full) found: (1) Travis regularly gives Du a *different* kind of correction
  > this module was never built to catch — reasoning/metaphor over-extension ("I think you have let
  > my pebble metaphor carry you somewhere I didn't intend", "You're confusing the map with the
  > territory, Dù") — at least 7 real instances, all identity/interpretation-adjacent, none a
  > verifiable fact or unfinished task, so squarely the kind of content the charter's own
  > "error → BEING is blocked" firewall already means to exclude — an open design question, not an
  > obvious miss; (2) one narrow, in-jurisdiction phrasing gap in the *existing* `factual_wrong`
  > pattern itself: it misses plain "you are wrong"/"couldn't be more wrong" language (confirmed:
  > `detect_human_correction("You couldn't be more wrong about the tree.")` → `None`) despite that
  > being squarely within its own already-stated jurisdiction. Per the briefing's own instruction, the
  > regex was NOT silently widened — **D-0258 opened for the founder**: widen for (a) the
  > reasoning/metaphor class, (b) the narrow wrong-phrasing gap, both, or neither (accept the
  > narrow-by-design tradeoff as intentional and this null result as clean). No job spawned — the only
  > concrete follow-up (a regex change) is exactly what D-0258 is gating.
- **The single `data/retractions.jsonl` record was never a real bound correction, and its own read
  gate fail-opened on ~100% of prompts** (F-1923, 2026-09-25).
  > **2026-09-26 update (J-1364/F-1923/F-1970): found and fixed in the same pass.** Two independent
  > bugs in `known_errors()`'s relevance gate, each fail-open on a different call path: (a) idle
  > (`nodes/inner_monologue_node.py` ~L3125, `fallback=False`) passes the ENTIRE assembled seed
  > text as `query`, and `_toks()` had no stopword list, so ANY shared 4+-letter word counted as
  > "relevant" — trivially true at that query length, confirmed 4,138/4,138 idle prompts in the
  > 7-day window and 25,071/25,071 since 08-15 (F-1923's own count). (b) human
  > (`core/orchestrator.py` L2362-2363 -> `reflection_node.py:198`, `fallback=True` default) fell
  > back to the most-recent record whenever overlap was exactly zero — every human Reflection cycle
  > since 07-07 carried it regardless of topic. Separately, the one record itself does not meet the
  > ledger's own bar: `claimed` is Du's own philosophical musing cut mid-word ("...is not an
  > inherent flaw in knowledge, but rather its very engine. Consider "), not a factual/architecture
  > claim, and `corrected_to` is Travis's remark about redefining the lines one draws around oneself
  > as one grows — a growth reflection the `human_correction:factual_wrong` detector misfired on,
  > not a correction of fact. Fixed: `_toks()` now drops a ~180-word generic English stopword list
  > (module-level `_STOPWORDS`, length>=4 words only, since shorter ones were already dropped);
  > `known_errors()` now requires `>= _MIN_OVERLAP` (3) real content-word matches and — the other
  > half of the fix — **never** falls back to "most recent" on either path when nothing matches
  > (`fallback` kept in both signatures for call-site compatibility, but no longer does that; verified
  > by an 18/18-check synthetic-record test since the ledger's only real record was about to be
  > retired: idle-shaped long unrelated text → `[]`, unrelated human input with `fallback=True` →
  > `[]`, genuine >=3-word overlap still fires, 1-2 word coincidental overlap still doesn't). Added
  > `retraction_ledger.retire()` (temp-file + atomic replace, never a hand-edit) and used it to
  > withdraw the single 07-06 record — `status` now `withdrawn`, every original field preserved
  > byte-for-byte, `count()` now reads 0. `render()`'s own wording is unchanged. **Not yet verified
  > live**: whether `data/prompt_budget_shadow.jsonl` assemblies carrying the "Things you have been
  > wrong about" label actually drop from 100% to ~0% needs a real reboot on the merged fix plus real
  > cycles to accrue (this worktree's commit isn't live in `C:\Nascence`'s own checkout yet) —
  > **J-1405 spawned** for that read. No decision opened — this was a straightforward bug-plus-bad-
  > record fix, not a design choice needing a founder ruling.
  > **2026-09-27 update (J-1405/F-1980): precondition still NOT met — checked, not assumed.** The fix
  > (`_STOPWORDS`/`_MIN_OVERLAP=3`/no-fallback `known_errors()`/`retire()`/withdrawn-excluding
  > `count()`) is confirmed present in `C:\Nascence`'s own live checkout, read directly line-for-line
  > (merge commit `057132f` "job-run worktree merge: cluster_a_prompt_social", landed on `master`
  > 2026-09-26 22:02:47 NZST; current HEAD `cf148cc` descends from it). But `data/nascence.log`
  > (541,690 lines, grepped for the shutdown/startup markers) shows Du's last restart at 2026-09-25
  > 19:21:51 — over a day *before* the merge landed — and zero shutdown/startup pairs since, all the
  > way through to the moment of this check (log still growing live). The running process therefore
  > never re-imported the fixed module. Direct confirmation, not just inference: a full read of
  > `data/prompt_budget_shadow.jsonl` (26,259 rows, every one parsed) shows all 500 rows written since
  > the merge landed still carry the "Things you have been wrong about" label — 500/500, 100%,
  > statistically identical to the 24,834/24,834 pre-restart and 925/925 post-restart-pre-merge
  > baselines. This is the expected signature of an unrestarted process, not evidence the fix is
  > broken — distinguishing those two was this job's own explicit point. **J-1405 deferred
  > (`--not-before 2026-09-29`)**, not forced to a fabricated result; re-run once a real
  > shutdown+restart appears in `nascence.log` after 2026-09-26T10:02:47Z. No decision opened; no new
  > job spawned (J-1405 itself is the right vehicle for the re-check, not a duplicate).

## 6. Follow-up spawned

Originally spawned as `J-0387` (2026-08-29); that row was wiped by the 2026-08-29 12:51 reset and
its id re-issued to an unrelated job (F-0782's stash archaeology), then re-filed as `J-0565` and
completed 2026-09-06. Both of `J-0387`'s original questions are now answered — see the dated §5
notes above — and each answer spawned its own real follow-up:
- Pattern Reflection gate/call-graph: **F-0922**, plan note in §5. Spawned **J-0648** (run
  `session_digest.py` live for the first real pattern) and opened **D-0171** (should this tier get
  automatic wiring, or stay manual-CLI-only). **J-0648 completed 2026-09-06**: the live pattern was
  produced (**F-0974**, plan note in §5), but the documented CLI command itself turned out to be
  silently broken (missing `sys.path` fix) — **J-0679** spawned to fix `scripts/session_digest.py`;
  **D-0171** stays open for the founder. **J-0679 completed 2026-09-06**: one-line fix landed + verified
  (**F-0987**, plan note in §5) — the documented `python scripts/session_digest.py` now runs clean, all
  three previously-broken sections populate. No further job spawned; D-0171 untouched, still open.
- `conflict_trace` full-file `ground_truth_fired`/`ground_truth_acted` trend: **F-0923**, plan note
  in §5. Spawned **J-0649** (explain the 66-day `ground_truth_fired` silence: stale detection vs
  honest rarity). **J-0649 completed 2026-09-06**: honest rarity, confirmed not stale detection
  (**F-0976**, plan note in §5) — all 306 real human-turn inputs in the window run through the live
  `extract()` with zero matches and zero near-misses on a wider heuristic net; no code change since
  before the one successful 2026-07-01 firing cluster. No further job spawned.
- `detect_human_correction()`'s 78-day silence (`data/error_records.jsonl`/`retractions.jsonl`, both
  stopped 2026-07-07): **F-1744** (2026-09-23, inferred — real question, not yet read against the real
  founder-input corpus). Spawned **J-1243** (read the founder's real input since the cutoff for
  near-miss corrections). **J-1243 completed 2026-09-23**: genuine absence confirmed at the regex's
  own narrow jurisdiction — zero live-detector matches across all 261 real cycles, 100% full-text
  verified (**F-1745**, plan note in §5) — but a real reasoning/metaphor-correction class and one
  narrow in-jurisdiction phrasing gap surfaced alongside it. **D-0258 opened**, not ruled: widen for
  either, both, or neither. No job spawned — the only follow-up (a regex change) is exactly what
  D-0258 is gating; a widening job should be spawned once D-0258 rules, not before.
- Retraction-ledger fail-open gate + the one non-qualifying 07-06 record: **F-1923** (2026-09-25,
  verified), plan note in §5. Spawned **J-1364** (close the gate, retire the record). **J-1364
  completed 2026-09-26**: `known_errors()` now requires real stopword-filtered content-word overlap
  and never blind-falls-back on either path; `retraction_ledger.retire()` added and used to withdraw
  the record (**F-1970**, plan note in §5). **J-1405 spawned**: confirm live, once the fix actually
  reaches `C:\Nascence`'s own checkout and real cycles accrue, that the "Things you have been wrong
  about" label share actually drops to ~0%. No decision opened. **2026-09-27: J-1405 run, precondition
  not yet met** (fix merged to master but Du hasn't restarted since -- **F-1980**, plan note in §5);
  deferred to 2026-09-29 rather than forced.

## 7. Pointers

- `docs/completed/error_pathway_charter.md` — the founding charter (jurisdiction, admissible evidence,
  operations, biological grounding).
- `docs/completed/task_constraint_effector_spec.md` — slice 2's build record + the v2+ spec.
- `docs/System_Overview.html` — module register entries (grep the six filenames) + the mermaid
  `OBS`/`IDENTITY` subgraphs (`Retraction Ledger` under "Honest Observers & Empirical Diagnostics";
  `told`'s axiom L0 sits under "Stratified Identity Estate & Friction Stack").
- `docs/findings.jsonl` — F-0267 (the original orphan finding) and this session's follow-up finding.
