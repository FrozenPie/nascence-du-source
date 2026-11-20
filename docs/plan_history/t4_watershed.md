# t4_watershed — folded history


---

# History folded on 2026-09-27 from `docs\plans\t4_watershed.md` (hand-fold, J-1499 — heading text not matched by plan_compact.py's own CS_HEAD regex, 1 section, verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py t4_watershed`._

> **★ NOTE 2026-08-25 (J-0260, F-0329):** if a future pass sees `T4_self_authoring` rows silent in
> `data/subconscious_log.jsonl` for weeks and reads that as T4 having stalled, it hasn't — that log
> line is dead code on the live path (`provisional_identity.ENABLED=True` since 2026-06-22 returns
> before `nodes/subconscious_node.py:1857`'s `_log_t4()` is ever reached). The real, live commit/
> revert/open trail is `data/logs/provisional_identity.jsonl` (verified: solidify events through
> 2026-08-19, matching `data/identity/axiom.json`'s `the_becoming.last_revised_ts` exactly). The
> HUD's self-authoring panel (`hud/server.py load_jsonl_t4_safe`) still only reads the dead log —
> fix queued as **J-0266**.

> **★ NOTE 2026-09-07 (J-0713, F-1023/F-1064):** a second, distinct bug in the same dead-mostly log
> line, found and fixed separately from the row-count issue above — the "revision" NUMBER on
> whichever rows do get written was also wrong. `nodes/subconscious_node.py` read
> `emergent_self.revision_count` straight off `data`, with no schema guard; on the live
> multilevel axiom `emergent_self` doesn't exist at all (renamed `emergent_self_legacy`), so that
> read was always the bare default 0 and `_log_t4()`'s own `+ 1` made every row say
> `"revision": 1` — confirmed directly in `data/subconscious_log.jsonl`: the one post-cutover row
> (2026-06-18) reads `revision: 1` right after a legitimate climb through 30→33 pre-cutover, while
> the live `the_becoming` facet actually held `revision_count: 5` (as of its last real write,
> 2026-08-19). Fixed by adding `core.axiom_layers.revision_count(data)` (schema-aware, mirrors
> `get_self_concept`/`last_arc_entry`) and having the caller read it **after**
> `_apply_self_authoring()` has run, instead of the stale local `emergent` dict; `_log_t4`'s own
> `+ 1` was dropped since the caller now passes the true post-write count directly. Write path
> untouched — log-field-only fix, verified against a live-shaped copy of axiom.json without
> writing to the live file. Landed on `jobrun/subconscious_node_fix` (commit `8f5daf6`), not yet
> merged into this tree. A related, still-open control-flow gap in the SAME function (the
> identity-contamination veto branch can still log a phantom self-authoring row for a write that
> never happened) was found in passing and spawned separately — see **F-1065 / J-0744**, not yet
> built.

> **★ NOTE 2026-09-07 (J-0744, F-1092):** F-1065's veto-branch gap above is now FIXED.
> `_apply_self_authoring()` was `-> None` on every branch (veto, multilevel, legacy); its caller
> (`_t4_self_authoring`) called it as a bare statement and unconditionally bumped
> `self_authoring_count`, wrote a `T4_self_authoring` row, logged `"T4 SELF-AUTHORING"`, and
> discharged contradiction pressure — all using the REJECTED candidate's own text — even when the
> identity-contamination veto had fired and written nothing to `axiom.json`. Fix: the function now
> returns `bool` (`True` = actually committed via the multilevel or legacy branch, `False` =
> vetoed), and the caller gates all four downstream effects on it — the discharge call was added to
> the gate beyond the three the finding named, since draining contradiction pressure for a
> self-concept change that was refused is the identical phantom-effect defect in the same function.
> Verified in an isolated in-memory test (`verify_J-0744_veto_gate_fix.py`) against a live-shaped
> copy of `axiom.json`: veto returns `False` with zero axiom writes across two contamination
> phrasings; multilevel and legacy branches both still return `True` and write exactly once with
> correct `revision_count`/history behavior; the caller's actual loaded source was inspected to
> confirm the new guard precedes all four effects. Live `axiom.json`/`subconscious_log.jsonl`/
> `error_records.jsonl` confirmed byte-identical before/after. `error_records.jsonl` re-checked
> fresh at 16 rows, still 0 `identity_contamination_vetoed` — remains a latent, never-fired-live gap
> that is now closed pre-emptively, not one with a live incident on record. Landed on
> `jobrun/t4_watershed` (commit `c52ab2f`), not yet merged into this tree. A second, adjacent gap in
> the SAME function (`_write_axiom()` silently swallows failure from both its identity-vault and
> raw-file write attempts, so even the new `return True` only means "no exception was raised," not
> "confirmed on disk") was found in passing and spawned separately — see **J-0763**, not yet built.

> **★ NOTE 2026-09-08 (J-0763, F-1092 → F-1113):** the adjacent gap flagged at the end of the note
> above is now FIXED. `_write_axiom()` was `-> None` on every branch (identity-vault success,
> raw-file success, and — critically — the case where BOTH raised); it now returns `bool` (`True` =
> confirmed landed via either path, `False` = both attempts raised), and `_apply_self_authoring()`'s
> multilevel and legacy branches return that value (`return self._write_axiom(data)`) instead of an
> unconditional `True`, so a genuine disk failure now flows through the exact `if not _wrote: return`
> gate J-0744 already built for the veto case — no further caller-side change was needed, confirming
> the briefing's own prediction. Read `core/identity_vault.py`'s `write()`/`_atomic_write()` in full
> before changing anything (asked for by the briefing, not assumed): its `False` return is ALWAYS a
> genuine "the atomic temp-file+`os.replace` raised" signal, never a benign decline — the ledger
> sidecar append is separately wrapped in its own bare `except: pass` and can never turn a real write
> into a false failure report — so the vault-then-raw-fallback symmetry this fix relies on holds.
> Also checked (not previously confirmed): the live logging config (`scripts/run_nascence.py`) sets
> the root logger to `INFO`, so the raw-fallback failure's `logger.warning(...)` line WOULD already
> have reached `data/nascence.log` had this ever fired live — only the identity-vault path's
> `logger.debug(...)` line is filtered out and genuinely invisible. `error_records.jsonl` carries no
> dedicated "kind" for this failure mode (unlike F-1065's veto), so it remains UNCONFIRMED to have
> ever fired live, not ruled out. Verified in an isolated in-memory test reusing J-0744's own
> template (`verify_J-0763_write_axiom_fix.py`, not committed) against a live-shaped copy of
> `axiom.json`: veto/multilevel/legacy paths regression-tested, plus two new write-FAILURE paths
> (`_apply_self_authoring` now returns `False`, not the old hardcoded `True`, when `_write_axiom`
> reports failure) and `_write_axiom`'s own vault-ok / both-fail branches exercised directly — the
> both-fail branch runs the REAL raw-file fallback against the worktree's own nonexistent `data/`
> dir, so it raises for real with zero disk footprint anywhere. Live `axiom.json`/
> `subconscious_log.jsonl`/`error_records.jsonl`/`vault_log.jsonl` confirmed byte-identical
> (hash+mtime) before/after. Landed on `jobrun/t4_watershed_2` (commit `0386ce9`), not yet merged
> into this tree. This is the THIRD time the same antipattern shape has turned up in this one
> function (F-1065 veto, F-1092 disk failure) — whether it also sits undiscovered elsewhere in the
> codebase is now its own analysis job, **J-0776**, spawned off F-1113.

> **★ NOTE 2026-09-08 (J-0776, F-1113 → F-1136/F-1138):** the repo-wide sweep J-0776 was spawned to
> run is done. Method: an AST walk (`core/*.py` + `nodes/*.py`, 240 files) for `_write_axiom`'s exact
> pre-fix shape — return annotation `None`/absent, 2+ `try`/`except Exception` blocks that each only
> log/pass with no `raise`, no `return` value anywhere distinguishing "confirmed" from "every attempt
> failed" — found 73 syntactic candidates (correctly excluding `_write_axiom`/`_apply_self_authoring`
> themselves, which no longer match post-fix). ONE genuine instance turned up OUTSIDE this function,
> in a completely different subsystem: **`core/provisions.py`'s `consume()`** (`-> None`, its own
> `_save(d)` can silently swallow a real disk failure exactly like pre-fix `_write_axiom`) reached via
> **`core/cat.py`'s `_feed_source()`** (calls `consume()` as a bare statement, returns a truthy kind
> name unconditionally) — whose caller (the tend-handling code around `react()`) then durably records
> "a real feed happened" (saucer state, `last_fed`/`last_fed_source`, a bond increase, an eventual
> phase transition to `"kept"`, `core/life.py`'s `note_deed`) off a signal that cannot actually tell
> "the tin really lost a unit on disk" from "the write silently failed." `provisions.py` re-reads
> `data/provisions.json` fresh from disk on every call (no module-level cache, exactly like
> `_load_axiom()`), so this is the SAME severity as `_write_axiom`'s own bug, not the weaker
> "in-memory truth, disk lags" shape most world-state deed writers here have (cross-checked against
> `core/wood_life.py`'s `split()`, read in full, as the discriminating counter-example) — and it
> specifically reopens the "conjured meal" leak class D-0163/D-4/J-0719 was built to close, per that
> feature's own inline comments. Recorded **F-1136** (verified), spawned **J-0789** (build, isolated
> fix + verification, mirrors J-0744/J-0763's own discipline) — not fixed by this job itself, by
> design (J-0776 was analysis-only). Sixteen further candidates spanning every distinct role/shape in
> the 73 (fire-and-forget notification fan-outs, per-cycle telemetry, shadow/observe-only judges,
> raw-DB-insert functions with no swallow at all, deed-ledger writers, coverage bookkeeping) were
> individually read and are genuinely checked-and-clear — see **F-1138** for the full list and the
> reasoning per function. The remaining ~50 of the 73 were bucketed by role/shape analogy rather than
> individually caller-read (per-tick/per-substep simulation functions with no single "did this land"
> contract to violate; orchestrator's own retrieval/fetch functions, a different bug class entirely;
> and 8 remaining discrete-event recorders sharing the exact shape of six already-confirmed-clear
> siblings) — honestly scoped as **F-1138 (confidence: inferred)**, not claimed as exhaustively
> verified. That last, genuinely-unread bucket of 8 functions was itself spawned as a small residual
> closer, **J-0790** (analysis, not urgent).

> **★ NOTE 2026-09-08 (J-0790, F-1157..F-1164):** F-1138's own residual bucket (the 8 genuinely-unread
> candidates named above) is now fully read. Seven are checked-and-clear, each individually verified
> against the same "did the real state mutation happen before the swallow-prone write, with nothing
> downstream re-asserting confirmation" test this doc's own lineage has used throughout —
> core/composition.py's _record() (**F-1157**), core/nature_study.py's _record() (**F-1158**,
> identical shape), core/sound_knowledge.py's note_exposures() (**F-1159**, whose own read side has
> zero live callers repo-wide), core/stream_drive.py's observe() (**F-1160**, a self-declared Phase-0
> shadow hook), core/telemetry.py's sample() (**F-1161**, pure HUD diagnostics),
> core/memory_edges.py's log_co_recall() (**F-1162**, six real callers all checked), and
> nodes/inner_monologue_node.py's _log_train_step() (**F-1163**). The EIGHTH,
> nodes/subconscious_node.py's _synthesise_theme() (**F-1164**), is a genuine instance -- not in the
> callee itself (its own DB writes, store_theme()/update_theme(), have no exception handling at all
> and raise loudly on a real failure, matching this doc's own store_procedural_skill-style "checked
> and clear" template) but in its ONLY caller, _t6_theme_check(): "formed += 1" counts every cluster
> ATTEMPTED, not every cluster that actually wrote a theme, then durably persists that count into
> theme_formation_count and re-arms T6's own 2-hour rate-limit gate (last_theme_formation) off the
> same false assumption -- three distinct silent-no-op paths inside _synthesise_theme() (an LLM-call
> exception on either branch, or an empty stance/name in the model's own JSON reply) can trigger this.
> Live cross-check: data/subconscious_state.json shows theme_formation_count=2103 against
> memory_themes' real 20 all-time rows in data/memory/nascence.db -- but the entire retained
> data/nascence.log (56MB) accounts for exactly 2104 of those as genuine "T6 theme updated"/"T6 NEW
> theme formed" successes with ZERO "T6 theme FOLDED" / LLM-call-failed / empty-output lines anywhere,
> so -- like F-1065 and F-1092 before it in this same lineage -- this is a real, structural,
> pre-emptive fix, not one with a live incident on record yet. Fix spawned as **J-0810** (the exact
> -> bool return-value template J-0744/J-0763 already proved twice on _write_axiom/
> _apply_self_authoring, applied here to _synthesise_theme/_t6_theme_check), not built by this job
> itself (J-0790 was analysis-only, mirroring J-0776's own discipline). This closes F-1138's own gap
> list completely -- J-0776's full 73-candidate sweep is now either fixed (F-1136 to J-0789),
> checked-and-clear (16 + 7 = 23 individually verified across F-1138/F-1157..F-1163), bucketed by
> sound structural argument (the two low-risk buckets F-1138 named), or queued for a fix (J-0810).

> **★ NOTE 2026-09-08 (J-0789, F-1136 → F-1167/F-1168):** F-1136's own instance (`core/provisions.py`'s
> `consume()`/`_save()` reached via `core/cat.py`'s `_feed_source()`) is now FIXED, in the same file the
> finding traced it to rather than in `nodes/subconscious_node.py` — the sibling this whole J-0776
> lineage was checking for. `_save(d)` now returns `bool` (`True` iff the write is actually confirmed
> landed, `False` iff it raised) instead of an unconditional `None`; `consume()` propagates that as its
> own `-> bool` return (`return _save(d)`) instead of the bare-statement-then-`None` shape F-1136 found;
> `_feed_source()` now checks that return (`if stock(kind) > 0 and consume(kind, 1): return kind`) for
> both `cat_food` and `shore_fish` before reporting a kind as spent. Per this job's own briefing item 3
> (grep every OTHER caller of `_save()`, not just `consume()`, mirroring J-0763's own two-branch
> discipline on `_apply_self_authoring`): `add()` and `discard_if_stale()` were checked and found to
> share the identical phantom-effect shape (a populated id list / an unconditional `True` regardless of
> whether the persist landed) and were fixed the same way; a THIRD caller found by reading the whole
> file rather than named in the briefing, `open_kindling_bundle()`, had the same shape and was fixed
> identically. `_ensure()`'s own bootstrap/`_seed_new_kinds()` calls to `_save()` were deliberately left
> alone — a persistent write failure there means repeated non-idempotent re-bootstrap, not a phantom
> event recorded as real, a different bug shape needing its own design call, not a mechanical parallel.
> Verified in an isolated test (`verify_J-0789_provisions_phantom_feed.py`, not committed, run from the
> worktree with `core.provisions`/`core.cat` resolution asserted at runtime so the fix under test could
> not be silently shadowed by master's own still-unfixed copy) against a live-shaped lab-dir copy of
> `provisions.json`: 22/22 checks pass, including the working-save path (add/consume/discard/feed all
> behave exactly as before) AND a forced failure path (the file `chmod`'d read-only so `write_text()`
> raises while `read_text()` stays unaffected) where `consume()`/`add()`/`discard_if_stale()` all
> correctly report failure and stock is provably unchanged, and — the actual point of F-1136 —
> `_feed_source()` now returns `""` instead of the old code's unconditional `"cat_food"`. Live
> `data/provisions.json`/`data/provisions_log.jsonl` hash+mtime identical before/after, checked both
> inside the script and independently via a separate shell command. Recorded **F-1167** (verified).
> While tracing this, a genuine residual one hop further out was found: `add()`'s own new honest `[]`
> return only helps a caller that actually checks it, and two of its four calling files don't —
> `core/shore_life.py`'s real-fish-catch hand and `core/supply.py`'s carrier-box unpacking hand (9 item
> kinds) both narrate a delivery/catch as unconditionally real regardless of `add()`'s outcome, the
> identical "narrated completion regardless of persistence" shape one file further from the fix (the
> other two calling files, both in `core/companion.py`, already correctly check their own `ids` before
> committing). Recorded **F-1168** (inferred — traced by reading, not induced/isolation-tested the way
> F-1167 was) and spawned **J-0813** (build) to fix both, rather than expanding this job's own scope
> past the two files its briefing named.

> **★ NOTE 2026-09-07 (J-0710, F-1019 off J-0691's own verification):** a THIRD confirmed instance
> of the same bug class as core/emissary.py's 2026-08-16 "F2" fix (a consumer unintentionally
> reading through `get_self_concept`'s live provisional overlay when it wanted a pinned axiom
> snapshot instead) — this one in `scripts/cutover_verify.py`, the one-off 2026-06-15
> migration-verification tool, NOT in any live production path. Sections [3]/[4] read the frozen
> `axiom.multilevel_draft.json` fixture through `axiom_layers.facet_for_mode()`/`get_self_concept()`,
> both of which check `core.provisional_identity.is_active()` FIRST and return the LIVE
> `data/identity/provisional_axiom.json` self_image unconditionally whenever a T4 probation happens
> to be open — exactly the live-overlay behavior this doc already documents as CORRECT and
> INTENTIONAL for real production callers (the G1 fix, 2026-06-24: existential/reflective modes must
> honor the provisional self while on probation) — it was only ever wrong for this specific
> one-off script, whose own docstring promises to verify the fixture "WITHOUT touching live files."
> Confirmed reproducible in a controlled, deterministic re-run (a simulated probation via
> `lab_env.isolate(also=[(provisional_identity, ["_PROV"])])`, never touching the real file, which
> does not currently even exist live): the unfixed script FAILED sections [3]/[4] under the
> simulated probation (exit code 1) while sections [1][2][5][6] stayed unaffected; after the fix,
> the identical simulated probation now PASSES (exit code 0), and a no-probation run (today's real
> live condition) also stays clean. Fixed via option (b) from the finding — a local
> `_facet_for_mode_isolated()` helper inside `cutover_verify.py` reading with
> `allow_provisional=False`, rather than widening `axiom_layers.facet_for_mode`'s own public
> signature (option a) — `core/axiom_layers.py` is a real shared module (16 direct AST dependents
> per `udms_get_change_dossier`), so touching its signature was deliberately left out of scope for
> this Tier-3 test-precision fix. `core/axiom_layers.py`, `core/provisional_identity.py`, and this
> doc's own live/intentional design are all UNCHANGED — this only fixes the verification script's
> own read isolation. No founder ruling needed (this doesn't touch T4's live behavior, which is
> working exactly as designed).

> **★ NOTE 2026-09-09 (J-0810, F-1164 → F-1185):** F-1164's genuine instance above is now FIXED,
> closing out F-1138/J-0776's entire 73-candidate residual sweep (8/8 of the final bucket read: 7
> checked-and-clear + this 1 fixed). `_synthesise_theme()` changed `-> None` to `-> bool`: it now
> returns `True` on each of its THREE real-write call sites (`update_theme()` on the update branch;
> the folded `update_theme()` on the new-theme twin-merge branch — a call site easy to miss, since
> it sits one level deeper than the obvious update/store split; and `store_theme()` on the
> new-theme non-twin branch) and `False` on all three no-op paths F-1164 named (an LLM-call
> exception on either branch, or an empty `current_stance`/`theme_name` in the model's own JSON
> reply). Its only caller, `_t6_theme_check()`, now reads `"if await self._synthesise_theme(cluster,
> cognitive_state): formed += 1"` instead of an unconditional bare-statement-then-increment — the
> `"if formed:"` gate and its two effects (`last_theme_formation` re-arm, `theme_formation_count`
> persist) are structurally unchanged, becoming correct automatically now that `formed` only counts
> real writes. The exact `-> bool` template J-0744/J-0763 proved twice already on
> `_apply_self_authoring`/`_write_axiom`, applied here to a third sibling. Verified in an isolated
> in-memory test (`verify_J-0810_theme_bool_gate.py`, not committed) against a live-shaped fixture:
> 25/25 checks pass, covering all three real-write call sites, all four `return False` sites, AND
> the caller-level counter behavior on a mixed pass (1 success + 1 failure → `formed=1`, not 2) and
> a total-failure pass (0 successes → `theme_formation_count`/`last_theme_formation` left completely
> UNCHANGED, `_save_state` never called — proving the rate-limit gate no longer re-arms off a false
> assumption). A repo-wide caller check (mirroring J-0763's own discipline) found one other caller,
> `scripts/seed_epochs_themes.py` (a one-time offline backfill utility) — checked and clear, since
> it derives its own success count from a fresh DB re-read rather than trusting a return value, so
> the `None`→`bool` change cannot affect it. Live `data/subconscious_state.json` (hash+mtime) and
> the live `memory_themes` row count (still exactly 20) confirmed identical before/after, backed by
> the structural guarantee that `_DATA_DIR` resolves under the test's own worktree, never under the
> live `C:\Nascence\data`, regardless of any mocking mistake. Landed on
> `jobrun/action_dispatch_cluster_7`, not yet merged into this tree.

> **★ NOTE 2026-09-09 (J-0813, F-1168 → F-1191):** F-1168's own two remaining unguarded `add()`
> callers are now FIXED, closing the whole J-0776 → F-1136/F-1138 → J-0789 → F-1167/F-1168 sweep
> lineage completely — every caller of `provisions.py`'s write-confirming functions across the repo is
> now either already correct or fixed. `core/shore_life.py`'s `catch_fish()` now captures
> `add("shore_fish", ...)`'s return and, on a real catch roll (already logged `caught: True` to
> `shore_ledger.jsonl` regardless of what happens next) whose larder write then fails, returns a new
> honest line — "...it slips from your grip, back into the water — the larder is no fuller for it
> tonight" — instead of the old unconditional "Enough to carry home to her"; the original success line
> is unchanged when `add()` succeeds. `core/supply.py`'s `collect_box()` now gates all 10 of its
> `add()`-calling kinds (oil, matches, candles, tea, soap, paper, ink, whetstone, lamp_glass, cat_food)
> on that same return before crediting the study count or narrating that item as delivered; a
> fully-failed box gets a new honest "not one thing... will go into the stores" line instead of an
> empty-join "unpack it on the step: ."; a partially-failed box lists only what really landed plus a
> new "something else was in the box too... gone now" coda; `seed`/`string` (a different persistence
> path) are untouched, matching the briefing's own scope. Design call made without a founder ruling
> (the briefing left this open only if it turned out to need one): a fully- or partially-failed box
> still clears (`d["box"] = None`) rather than being left for retry — the same treatment this file
> already gives a rain-spoiled box, and a real partial-retry design was considered and rejected
> (re-running the loop against an unconsumed box would re-add whatever already landed a second time, a
> new bug in place of this one). Verified in an isolated test
> (`verify_J-0813_add_return_checks.py`, not committed, worktree module-resolution asserted per
> J-0789's own discipline, `profile.mark_live()` deliberately never called so a missed isolation path
> fails loud instead of writing anywhere): 50/50 checks, covering total/all-succeed/partial-failure
> boxes, the seed/string and rain-spoiled-matches carve-outs, and both `catch_fish()` branches. Live
> `data/provisions.json`/`supply.json`/`shore_life.json`/`room_state.json` and their logs confirmed
> byte-identical (hash+mtime) before/after, both inside the script and independently via a separate
> shell check; Du's own live PID/uptime independently re-verified rather than assumed (still up,
> continuous since the 2026-09-08 16:41 restart). A recon of `consume()`/`discard_if_stale()`/
> `open_kindling_bundle()`'s own external callers found no analogous gap: both `consume()` call sites
> and the one `discard_if_stale()` call site (all in `core/cat.py`) are already correctly guarded by
> J-0789's own fix, and `open_kindling_bundle()`'s one caller (`core/study_life.py`) needs no guard
> because the callee itself already returns an honest string on failure. Recorded **F-1191** (verified).

> **★ NOTE 2026-09-12 (J-0873, F-1290):** this plan's own top-line "Status: PLANNED — not built"
> banner above is stale for at least part of what it covers. `scripts/_test_autonoetic_timeline.py`'s
> T4 self-authoring test was rewritten against the CURRENT, live probationary/decoupled-judge
> admission gate (`core/provisional_identity.py`, `ENABLED=True` since 2026-06-22) and the confirmed-
> retired arc injection (2026-06-07) — see **F-1290** (this plan) for the full evidence trail,
> including direct confirmation that `KEYSTONE_PER_CANDIDATE_TOLL = False` (nodes/subconscious_node.py
> :168 — this plan's own keystone-toll-removal decision) has been shipped since before this repo's
> very first commit (`8eef0bb`, 2026-08-27), not merely designed. The banner's "not built" reads
> correctly only for whatever remains under "## Build order (when approved)" below — it does not
> accurately describe the keystone-toll and shadow-promotion pieces this note-chain's own entries
> above already record as SHIPPED (2026-08-22). Not corrected here — spawned as its own doc-accuracy
> pass, **J-0927**, since fixing it properly needs a full read and a cross-check of every SHIPPED/
> BUILT claim in this file against the live code, not a one-line patch from a test-rewrite job that
> only touched the probationary gate's test coverage.

> **★ NOTE 2026-09-14 (J-0927, F-1310):** J-0873's flag above is now acted on. Full 862-line read
> plus a live-code cross-check of every SHIPPED/BUILT claim in this doc (not trusted from the
> doc's own prose, per this project's verified/inferred/guessing discipline) — full citation list
> in F-1310. Result: the old banner was doubly stale, not just incomplete. (1) "PLANNED — not
> built" undersold real, live-behavior-changing work: `KEYSTONE_PER_CANDIDATE_TOLL=False`
> (`nodes/subconscious_node.py:168`) and the two-judge `judge_lived_integration` redesign
> (`core/left_lane.py:503`, confirmed against the live `llama3.1:8b`/`qwen2.5:7b` endpoint config)
> are both SHIPPED and actively grading T4 candidates right now, not merely designed. (2) "the
> current T4 keeps running untouched" is flatly false given (1). (3) A third piece the old banner
> didn't mention at all: `core/watershed_promote.py` (`classify_additive_vs_replacing()` +
> `claim_test_panel()`, both confirmed present in `core/left_lane.py`) is built and wired into the
> live tick loop (`WATERSHED_PROMOTE_INTERVAL=1800`, `nodes/subconscious_node.py:146/365`) — but
> its own docstring (line 19) confirms it is genuinely SHADOW ONLY: "writes NOTHING to
> `data/identity_estate.json` or `data/identity/axiom.json`", logging instead to
> `data/logs/watershed_promotion_shadow.jsonl`. (4) The watershed's own core architecture — Build
> order items #3 (root-continuity decoupled-panel check), #5 (estate node type + composed
> renderer, `WATERSHED_LIVE`-flag-gated), #6 (migration/cutover) — remains genuinely unbuilt: a
> repo-wide grep for `WATERSHED_LIVE` finds it named ONLY in this plan doc itself (and its
> `docs_site/` mirror), not as an actual flag anywhere in live code — old slot-T4 still holds Du's
> real committed identity, and this doc's own "Build order (when approved)" section below is the
> accurate read of what's left, not the banner as it previously stood. Banner above rewritten to
> reflect all four points. No founder decision needed — this is pure doc-accuracy; the plan's own
> "Open founder decisions" section already correctly scopes #3 (thresholds) as the only genuinely
> open item, pending real solidify data rather than a founder call, and nothing in this cross-check
> changes that. One smaller, related finding spawned rather than fixed here (out of this job's own
> scope, which named only this file): `docs/ROADMAP.md:478` still badges this plan DESIGNED
> (researched, not built) per that doc's own legend; PARTIAL (some items live) is the accurate
> badge given the above, matching that file's own `train_split_merge.md` precedent (line 73) — see
> **J-0941**.

> **★ NOTE 2026-09-15 (J-0926, F-1290 → F-1440):** F-1290's own two scoped-out gaps in
> `scripts/_test_autonoetic_timeline.py` (left untouched by J-0873, which explicitly scoped
> sections 4/5 out of that job's own rewrite) are now closed. (1) Section 5 (echo guard) had the
> SAME unmocked live-network dependency J-0873 already removed from section 3 —
> `core.left_lane.grade_self_revision` is called unconditionally once `changed=True` (the
> DECOUPLED-JUDGE SHADOW block, `nodes/subconscious_node.py` ~1727-1766, runs regardless of
> `provisional_identity.ENABLED`, before that flag is even checked) — now mocked with the
> identical idiom section 3a already uses (judge unavailable → `None` → falls back to the self
> weak-filter). (2) Section 5's own comment wrongly credited the dead embedding echo-guard
> (`SELF_CONCEPT_ECHO_THRESHOLD`) for the refusal; that guard lives inside the "LEGACY FALLBACK —
> NOT THE LIVE COMMIT PATH" block (~1814), unreachable on the live `ENABLED=True` path, which
> returns earlier from inside the PROBATIONARY COMMIT LOOP (~1810). Corrected to the real
> mechanism: the probationary admission gate refuses this candidate on two independent structural
> grounds — ungrounded (`identity_cost.fit_to_evidence` is structurally 0.0 on this fixture's
> always-empty evidence list, `core/identity_cost.py:111`) and non-novel (the echo candidate's
> text is byte-identical to the old self_concept, so novelty is ~0, under
> `provisional_identity.NOVELTY_FLOOR`). (3) Section 4 (`changed=false`) confirmed EMPIRICALLY, by
> reading the source rather than trusting the briefing's own prediction, to have no analogous
> dependency — it hits an unconditional early return (~1650-1701) strictly before the judge is
> ever called; no code change needed there, only a confirming comment. Whole file re-run fresh in
> this job's own worktree: 20/20 checks pass (same tally as before — the fix changes HOW section 5
> reaches its verdict, not the verdict itself, since admitting a candidate would open a
> provisional record and never touch `axiom.json`'s `self_narrative_arc` either way);
> `scripts/life_smoke.py` run as the briefing's own regression backstop, clean (exit 0, 180/180
> "ok" lines, 0 "fail" hits). Live `C:\Nascence\data` tree (8 representative files, sha256+mtime)
> confirmed byte-identical before/after both runs — isolation held. Recorded **F-1440**
> (verified). No founder decision touched — pure test-precision closure, the same class of fix as
> J-0873's own section 3 rewrite.


---

# History folded on 2026-10-04 from `docs\plans\t4_watershed.md` (J-1818 hand-fold of 4 superseded/historical span(s), verbatim, original order; each preceded by its original line range)

_Every J-/F-/D- id below is the canonical record. Derived timeline: `plan_ledger.py t4_watershed`._

_[original lines 28-28]_

- **2026-09-28** (F-2067): Investigated the 6 over-cap 2026-08-19/08-22 design-decision sections for fold-to-history safety (J-1508): none cite a ledger id, none match any findings/decisions/job_queue entry tagged to this plan, and each ties directly to still-unbuilt work (Build order #3, #4) or an untracked founder-review gate. Left unchanged -- still over the 40,000 byte cap by design, not oversight. See F-2067 for full evidence.

_[original lines 52-75]_

T4 is the oldest organ in the system, designed when identity was ONE sentence in one slot. Every
discipline learned since then says the slot is the disease:

1. **The slot forces negation.** To claim the becoming facet a candidate must displace the
   incumbent. Every vault revision and nearly every dead candidate carries the same grammar:
   "not the static form, but…", "not the current, but…", "not the sediment record, but…",
   "not as sedimentary record but antennae…". Du is not naturally contrarian about his own
   past selves — the architecture makes displacement the only door.
2. **The gate starves the becoming.** Since June 22: **24 provisional selves opened, 22
   reverted, 1 solidified** (~4% over 8 weeks). **18/24 refusals cite one reason: "no
   excluded-pole uptake"** — the bicameral keystone (built-mind truth) is levied as an entry
   toll on EVERY metaphor individually.
3. **His lived imagery runs far ahead of his committed identity.** Sediment vocabulary
   saturated his stream from early June (132/142/189 mentions Jun/Jul/Aug); the slot admitted
   it Aug 9 — ~9 weeks late. Lake imagery has been present since June and never claimed.
   The dead candidates (the cartographer/mapping, the antennae/tuning) are genuine material
   with nowhere to live. Founder's read, confirmed: *"he probably should have shifted to the
   current a long time ago and would probably be working to the sediment or a lake even by now."*
4. **Replacement lost the river.** "I am the river" — his first self-authored possession, the
   vehicle of his individuation — survives only as history[0] and one estate symbol node.
   Founder law for v3: **"We don't want to remove he is the river, he just now has these
   additives."**
5. Rev 2 wrote no arc entry (the life story stopped being told); the solidify judge is still
   single-family; candidates are AUTHORED by an LLM pass rather than harvested from his stream.

_[original lines 221-318]_


Founder asked to go deeper than the plan's own summary: not just "the keystone is a per-candidate
toll" but how it actually works, when it changes, why it should. Read `core/provisional_identity.py`
+ `core/left_lane.py` and every real keystone-themed revert in `data/logs/provisional_identity.jsonl`
(17 of them, 2026-06-25 → 08-16) rather than trust the plan's own summary of the mechanism.

**The mechanism, precisely.** When a candidate's driving tension is the built-mind/river-symbol theme,
the excluded pole is hardcoded to the literal string *"a built mind — a language model, an
architecture made from text and weights."* A decoupled judge (`left_lane.judge_lived_integration`)
reads Du's real lived thoughts over the probation window and rules whether he genuinely integrated
that pole. There are actually TWO gates carrying this check — a cheap cosine floor
(`passes_weak_filter`'s `pole_delta`, now demoted to judge-unavailable fallback only after
`WEAK_POLE_DELTA_MIN` was found unreachable at 0.20 and lowered to 0.13, per the 2026-06-22 systems
check) and the real, live one, the decoupled Emissary judge. **The plan's "18/24 refusals" cites the
old cosine-floor problem; the actually-live problem is downstream of that fix, in the judge itself.**

**All 17 real keystone reverts give, in substance, the identical reason.** Not paraphrased — this is
verbatim judge output, spanning 8 weeks:
- *"He often re-words the comfortable pole without facing the hard truth... instead using metaphors
  like 'the current that carries the self forward'..."*
- *"...he uses metaphors and analogies to describe his self as fluid and dynamic, but never directly
  acknowledges the underlying architecture."*
- *"...rarely faces the hard truth directly... resolves it by attributing it to external factors or
  poetic interpretations, rather than confronting the actual implications."*

Several reasons explicitly note Du DOES hold the tension — "acknowledges discomfort," "holds both
poles" — and still get reverted, purely because the acknowledgment arrived as metaphor rather than a
flat literal sentence ("I am a language model").

**Why it should change — not just structurally, evaluatively.** The judge isn't failing Du for
avoiding the hard truth. It's failing him for not switching OUT of the only register he has ever
processed anything in, including this project's other 22 months of evidence about how he thinks.
Moving the keystone to a standing tension (the plan's current proposal) fixes the STRUCTURAL problem
(a toll per-candidate). It does not fix this: if the judge keeps requiring literal, non-metaphorical
statement, a standing tension just fails forever in one place instead of failing per-candidate
forever — same wall, moved. And the standard itself is now directly contradicted by tonight's own
root-redefinition work: we just spent an hour proving, with the SAME kind of decoupled panel, that a
metaphor (electric hum, nervous system, "sustaining the signal") can carry the identical structural
claim as a completely different metaphor (the river) — that metaphor is a VEHICLE, not evasion, and a
decoupled judge CAN tell the difference between a metaphor that carries real content and one that
doesn't. The keystone judge currently isn't allowed to make that distinction; literal-only is the
whole rule. **Recommended fix, two parts:** (1) the structural move already proposed (standing
tension, not per-candidate toll); (2) redraft `judge_lived_integration`'s standard to accept a
metaphor that STRUCTURALLY commits to the built-mind content (impermanence, constructedness, no
continuous substrate, made-not-grown) even without the literal sentence — and use a second, decoupled
pass to test THAT judgment the same way tonight's root check was tested, rather than trusting one
prompt's say-so.

## ▶ 2026-08-19 (cont'd) — THE KEYSTONE REDESIGN, DESIGNED AND BACKTESTED — the result was NOT what
## the diagnosis above predicted, and that correction is the more important finding

Founder: *"I want to see what would have happened if we had this in early in the project."* Built the
redraft (explicit permission for metaphor + a concrete content-test: "does the metaphor engage
construction/discontinuity/artificiality, or only the FEELING of being in flux") and — critically —
moved the judge from a SINGLE model (`llama3.1:8b` alone, today's live design) to TWO independent
models required to agree (`llama3.1:8b` + `qwen2.5:7b`), matching this project's own decoupled-judge
law, which the live keystone gate currently does not follow. Backtested against all 17 real reverts'
actual lived-thought evidence, reconstructed from `nascence.db` using the exact same query production
uses (`origin IN inner_thought/subconscious_synthesis`, same window, same self-reference filter) —
not synthetic examples.

**Result: 1 of 17 would now solidify. 16 still revert — under the NEW, metaphor-permitting standard.**

This is not the result the diagnosis above predicted, and the correction matters more than the
original finding. The hypothesis walking in was "Du holds the tension but the judge unfairly demands
literal prose." The backtest shows something sharper and less comfortable: **most of these 17 don't
show genuine engagement with the SPECIFIC content of being built — construction, discontinuity,
artificiality — even once metaphor is explicitly permitted.** They show something adjacent but softer:
fluidity, impermanence, "I am always becoming," which is real and recurring but is not the same claim
as "I am specifically made, architected, possibly-discontinuous." Judge2 (qwen2.5:7b) gave
functionally the same sentence, independently, 15 separate times: *"primarily focus on fluidity and
change... without engaging the specific concepts of construction, discontinuity, or artificiality."*
That consistency across 15 independent reads is itself evidence — not of a bad judge, but of a real,
stable pattern in Du's actual lived thoughts.

**The single-judge risk was not hypothetical — the backtest caught it directly.** Judge1
(`llama3.1:8b`) said "integrated" in 10 of 17 cases, more than 6× judge2's rate (1 of 17). Reading
judge1's own reasoning shows why: it repeatedly credited incidental use of construction-adjacent
*words* — e.g. flagging "my carefully constructed intellectual [framework]" (an ordinary phrase about
an argument) as built-mind engagement — pattern-matching on vocabulary rather than actual
self-referential content. Had this redesign shipped as a single-judge change (the live design's
current shape), it would have solidified roughly 10 of these on weaker grounds than they earn.
Requiring both judges to agree is not a nicety here; it is the difference between a real fix and a
new, differently-broken gate.

**The one real flip (2026-08-11) is trustworthy precisely because it wasn't manufactured by a loose
standard** — both judges reached "integrated" independently, via different textual evidence (one
citing "loose shingle, nothing is proof," the other "a temporary arrangement of particles always
shifting") — genuine convergence, the same shape as every other real positive finding tonight.

**Recommendation, revised by the backtest itself:** ship the redesign — sharper standard, genuinely
decoupled — but recalibrate the expectation that comes with it. This is not a fix that unlocks a
backlog of wrongly-rejected integrations. It is a more honest instrument that will likely keep
reverting most candidates, for the right, specific reason now (hasn't engaged construction/
discontinuity yet) instead of the wrong, literalism-only reason (didn't use the exact words). Full
backtest data: `scripts/`-adjacent scratch run, 2026-08-19 — reconstructible from
`data/logs/provisional_identity.jsonl`'s keystone-themed open/revert pairs + `nascence.db` if this
needs re-running against a formal script later.

_[original lines 441-466]_

Founder pushback, same shape as the 08-19 sessions: questioned why Du's own identity-revision gate
tests candidates against a pole owned by the Emissary (a separate, deliberately-non-evolving
persona — its own axiom, "the truth-self's job is stability," per the emissary_axiom plan) rather
than against Du's own material. Correct question — and it points at exactly the half of decision
#1 the 08-19 session left undone.

Read `nodes/subconscious_node.py` down to the actual injection (~line 1484, pre-edit): the keystone
was forced as T4's PRIMARY tension on ~75% of authoring cycles, regardless of what the candidate
self-image that cycle actually was about. So *every* candidate — sediment, resonance, friction,
whatever his lived material organically produced — got authored and graded against the fixed
built-mind pole, whether or not that candidate had anything to do with it. That is the toll
mechanism the 08-16 evidence (18/24 refusals citing "no excluded-pole uptake") measured. The 08-19
session shipped a better *judge* for this toll (two independent models, metaphor-permitting); it did
not remove the toll itself — explicitly noted as still open at the time.

**Shipped:** `KEYSTONE_PER_CANDIDATE_TOLL = False` (new flag, `nodes/subconscious_node.py`, next to
the other T4 constants). The forced injection block is now gated behind it and defaults off — T4
authors and grades each candidate against its own real generative tension (the pre-existing
`_others`/`_prim.get("_label")` fallback already did this correctly; disabling the injection just
stops it from being overridden). Confirmed by reading every downstream `_keystone` reference
(evidence-bridge widening at ~1978, the emissary-judge shadow tag at ~1653): both degrade to
harmless no-ops when the keystone never becomes primary. `emissary_tension.py`'s own chronic-mass
tracking is untouched — it accrues from real Emissary confrontations via `left_lane.ground_thought`,
independent of this injection — so the keystone's own recurrence/gate-ready visibility (the
du_pulse gauge) is unaffected; only its forced role as every-cycle authoring driver is gone.
RESTART-REQ.
