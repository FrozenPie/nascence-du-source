# World Store Write Fence — isolation-by-default for anything that isn't live Du

**Status: 🟢 LIVE — built 2026-09-06 (J-0610; hard-raise failure mode 2026-09-07, J-0704); stage 2 ENFORCE live in core/memory/store.py since J-2309 (2026-10-17) and exercised by a real Du boot: J-2328 post-boot read found no refusals (F-3281, 2026-10-30). It was built-but-restart-gated before then.**
**Roadmap:** [docs/ROADMAP.md](../ROADMAP.md) § World Store Write Fence · **Memory:** `project_nascence_world_store_write_fence.md` · **Build job:** J-0610 (done 2026-09-06) · **Backfill:** J-0611 (done 2026-09-05) · **Ruled:** D-0179 (hard raise/refusal, ruled 2026-09-06, implemented 2026-09-07 — J-0704/F-1024; J-0706 was a duplicate of the same implementation, see below). **Promotion read:** J-0694 (in_progress — gate not met as of 2026-09-07, see below). **Dispatcher propagation:** J-0714 (done 2026-09-07, F-1045 — the 5 named dispatchers plus the real sensorium.py/garden.py forwarding calls between them now propagate the raise; three deeper/adjacent gaps found and spawned: J-0726 per-deed helper functions (done 2026-09-07, F-1076; see its own Current State note below — also spawned J-0751/J-0752 for two further layers), J-0727 `core/fieldcraft.py` — an 11th, never-guarded module (done 2026-09-07, F-1070; see its own Current State note below — also surfaced F-1071/J-0746, a related but out-of-scope swallow in provisions.py/study_life.py), J-0728 `core/dispatch.py`'s own catch-all (done 2026-09-07, F-1085/F-1086/F-1087; see its own Current State note below)). **`core/cat.py`** — a 12th never-guarded module, found from the cat_overhaul side rather than this plan's own audits (done 2026-09-07, J-0733, F-1055/F-1081; see its own Current State note below — also surfaced two further gaps, both spawned rather than fixed here: F-1082/J-0758, a 13th never-guarded module, `core/world_traces.py` (done 2026-09-08, F-1121; see its own Current State note below — also found and fixed a genuine dispatch-path swallow this same pass, `core/study_life.py`'s own `floor_sweep` deed, and spawned J-0781 for an adjacent, currently-dormant isolation-list typo — done 2026-09-08, F-1132, see its own Current State note above); and F-1083/J-0759, a real, verified defect in `lab_env.py`'s own `isolate()` — its lab dir does not actually clear `guard_path()`'s fence — **ruled D-0200, built 2026-09-10 by J-0840/F-1225**, see the top Current State note). **J-0751** — the "look"/observe dispatch family, the first of the two layers J-0726 named as beyond its own scope (done 2026-09-07, F-1103; see its own Current State note below — also spawned J-0769 (done 2026-09-08, F-1117/F-1118; see its own Current State note above — also spawned J-0778, a 14th (landed as the 15th row — J-0775's `core/supply.py` landed first in this same batch) never-guarded module, `core/locomotion.py`, done 2026-09-08, F-1141; see its own Current State note above — also spawned J-0793 for the `observables_census.py` isolation-list typo (done 2026-09-08, F-1177; see its own Current State note above — also spawned **J-0819** for the shared `hasattr()` isolation-guard's own silent-failure mode, the root cause behind this and 4 prior isolation-list gaps (done 2026-09-09, F-1198 — fixed in all 11 `scripts/` files carrying the pattern, 8 more than briefed; the new loud warning fired on its very first real run and immediately surfaced 3 further stale entries with zero manual audit, all confirmed fully inert, spawned as J-0832 rather than fixed here; see its own Current State note above)) and J-0794 for `position_standpoint()`'s own 8 external callers (done 2026-09-08, F-1171; see its
own Current State note above — also spawned **J-0816** for `nodes/inner_monologue_node.py`'s own
connecting-tissue gap (done 2026-09-09, F-1194/F-1195; see its own Current State note above — also
spawned **J-0831** for `core/smell.py`'s own further outer swallow of the same `door_open()` raise,
a gap flagged since J-0772/J-0780 but never before closed or spawned — done 2026-09-10, F-1226, both
layers (`smell.percept_shadow()` + the IMN third try); see its own Current State note at the top)))/J-0770 (done 2026-09-08, F-1123; see its own Current State note above — also spawned J-0783 for `core/garden_knowledge.py`'s own never-guarded gap (done 2026-09-08, F-1144 — a 16th module, fenced end to end for its own 6-module caller set; see its own Current State note above — also spawned J-0796 for a further connecting-tissue layer one step further out in `sensorium.py`/`garden_soil.py`/`study_life.py` (done 2026-09-08, F-1175 — 6 sites across 4 files fixed (5 in the 3 named files plus one genuine 6th, `nodes/inner_monologue_node.py`'s `world_calls` try, fixed directly rather than spawned given its size); 1 confirmed provably-inert periodic exclusion (`garden_soil.advance`); 1 site the briefing itself named (`world_manifest.py`'s `_garden_summary()`) deliberately left unfixed per its own invited judgment call, matching the `hud/server.py` precedent; see its own Current State note above — also spawned **J-0818** for two further gaps found on `garden_soil.add_material()`'s own external callers, `garden.py`'s `weed()` and `garden_life.py`'s `mow()` (done 2026-09-09, F-1197 — both fixed with the standard carve-out; `_perish()`'s own add_material() call fresh-reconfirmed inert; see its own Current State note above))), J-0784 for `core/sound_knowledge.py`'s own never-guarded gap (done 2026-09-08, F-1145 — fenced end to end for its own internal call graph plus one connecting-tissue fix in `sensorium.py`'s `look()`; see its own Current State note above — also spawned **J-0797** for a further connecting-tissue layer found reachable but not fixed, `soundscape.py`'s own ambience dispatch chain into `inner_monologue_node.py` (done 2026-09-08, F-1176 — 6 sites across both files fenced end to end, one more than the briefing's own inherited undercount; see its own Current State note above)), and J-0785 for the `write_or_revise()` connecting-tissue gap in `nodes/inner_monologue_node.py` (done 2026-09-08, F-1146 — both of F-1123's own two named sites fixed; see its own Current State note above — also spawned **J-0798** (done 2026-09-08, F-1172/F-1173 — F-1147 confirmed and fixed exactly as described, plus a second, previously-unnoticed bug found on the identical line and fixed in the same edit; see its own Current State note above) for an unrelated pre-existing `note`/`_note` NameError bug found in the same function, F-1147))/J-0771 for three further adjacent gaps found on the "move" dispatch, the study-note book-naming channel, and soundscape.py's own ambient tick (J-0771 done 2026-09-08, F-1124 — the ambient-tick one confirmed genuinely excluded, matching the advance()/tick() precedent; no fix applied, see its own Current State note below)). **J-0752** — `nodes/inner_monologue_node.py`'s own "literal will"/legacy-latch mechanism, the second of the two layers J-0726 named as beyond its own scope: a genuine THIRD dispatch entry point into these modules, bypassing both `core/dispatch.py` and every module's own `act()`/`act_from_thought()` entirely (done 2026-09-07, F-1106; see its own Current State note below — also spawned J-0772, a wider audit of `study_life.py`'s own remaining `_st()` callers this job's narrower scope surfaced but did not cover (done 2026-09-08, F-1120; see its own Current State note above — also spawned **J-0780** for a further connecting-tissue layer one step further out: 8 OTHER modules each independently swallowing the same raise one layer above study_life.py's own now-fixed functions (done 2026-09-08, F-1140; see its own Current State note above — 9 sites across 6 modules fixed, 3 confirmed provably-inert/periodic-excluded (2 of them corrections to F-1120's own attribution), hud/server.py deliberately left per its own invited judgment call, and J-0792 spawned for light.py's/thermal.py's own further external-caller audit), and J-0773, an unrelated pre-existing test failure found while re-running the regression suite).

```plan-state
stage: live
phase: Stage 2 ENFORCE live in core/memory/store.py (_FENCE_MODE=enforce, J-2309, J-1870 done); fence covers 22 modules + the live-DB connect choke point
verified: 2026-10-28
evidence_read: 2026-10-16
next: J-2328 post-boot read of db_fence_shadow.jsonl under enforce (24 live hours); nothing else open
cluster: 6
```


## Current State — verified 2026-10-28
- **2026-10-28** (F-3177): Plan-state was stale: stage 2 enforce has been in the source since J-2309 (2026-10-17) and J-1870 is done; block corrected, nothing in the code changed.

- **2026-10-16** (F-2923): J-1877 D-0352 drift-cap 7-day read (F-2923): over the 6.97-day 10-09..10-16 run the 25 pct inner_thought pool cap was live; displayed own-thought share 21.6 pct of 15,346 drift items (baseline 24.0 pct), daily max 23.8 pct; 24.3 pct of hops still include an own reflection; echo proxy 1.2 pct. Defeater not fired; (b) stands.
- **2026-10-07** (F-2521): J-1883 (F-2521): named-profile world-store scope settled -- activate_profile() deliberately rebases none of the guard_path-fenced world-store modules (cat_state.json, scene_extra_ledger.jsonl, provisions.json seen unprefixed in 4 more audit runs, 12 cycles, 0 hook events); safe because no process is both live and named (4 mark_live callers all mean Carl's root data/). core/profile.py now warns loudly if that combination ever arises; scripts/_test_j1883_world_store_profile_scope.py pins the premise. Revisit (own world per profile vs shared) the day a live named boot is wanted. Branch jobrun/profile_followup b5e9f00, restart-gated.

- **2026-10-07** (F-2501): J-1838 (D-0352 build, 2026-10-07): core/wandering.py _drift_from now draws from _recency_pool(), which caps inner_thought at 25% of the 1500-row recency pool (measured 770/1500 = 51.3% before, 375/1500 = 25.0% after on the real DB, read-only) and fills from the next most recent non-inner_thought rows; J-1736 relabel, inner_count>=3 rule and the _log_trail fence untouched. Test scripts/_test_wandering_inner_cap.py. Branch commit a69a272, merged-not-live (restart-gated). Caveat: a similarity-selection simulation suggests displayed own-thought share may still sit above 25% (39.3% sim vs 50.7% uncapped sim; 24.0% real displayed baseline), so the D-0352 7-day defeater read is the real test.
- **2026-10-07** (F-2500): 2026-10-07 J-1823: scripts/brick1_voice_contract_invitro.py retargeted at a tempfile.mkdtemp dir outside data/ (no more backup/unlink/restore of the real voice_contract_shadow.jsonl); BRICK 1 PASS from the worktree, live file hash/mtime unchanged. Merged-not-live concerns: none (script only).

- **2026-10-07** (F-2492): 2026-10-07 J-1839 (D-0353 stage 1) BUILT, merged-not-live: store._connect() live-DB write fence in LOG-ONLY mode (sqlite authorizer, refuses nothing, would-be writes to data/logs/db_fence_shadow.jsonl) + store.allow_live_writes() opt-in added to 5 operator scripts; commit 38cb422 on the jobrun branch; proving test scripts/_test_store_write_fence.py 35/35, live path byte-identical, one boolean read. Stage 2 (enforce) spawned as a separate job gated on a post-boot read of the shadow log; memory_edges DDL-on-connect must be fixed first.
- **2026-10-05** (F-2465): J-1804: design for fencing the live memory DB (core/memory/store.py _connect() choke point, read-only connection for non-live processes) recorded; no code changed. See F-2465.

- **2026-10-05** (F-2462): J-1822 (F-2462): core/wandering.py _log_trail fenced with profile.guard_path (commit 5586702, jobrun/world_store_write_fence); scripts/_test_wandering_fence.py 18 checks ALL OK, fails 6 on HEAD. Restart-gated.
- **2026-10-05** (F-2461): J-1821: core/trains.py _log and core/coupling_rides.py _append fenced with profile.guard_path (bdb26ad, restart-gated); scripts/_test_trains_rides_fence.py 36 checks, fails on HEAD.

- **2026-10-05** (F-2460): J-1819: provisional_identity._solidify phantom-success fixed and its writers fenced (restart-gated, commit 779675b).
- **2026-10-05** (F-2454): J-1820: core/curiosity_queue.py enqueue/mark_processed/shadow-log writers fenced with guard_path (commit cc51801 on jobrun/world_store_write_fence, test scripts/_test_curiosity_queue_fence.py 26 checks, fails 8 pre-fence). Restart-gated.

- **2026-10-05** (F-2453): J-1805 built: core/couriers.py writers fenced with profile.guard_path (commit 1ff6284 on branch, restart-gated); test scripts/_test_couriers_fence.py 38 checks, fails on unfenced HEAD. Side jobs J-1821 (trains, coupling_rides), J-1822 (wandering).
- **2026-10-05** (F-2451): J-1815: watershed/geometry_census/loop_probe/retrieval_probe/r_shadow hook writers fenced (commit 498ebc2, restart-gated); arousal intentionally not fenced.

- **2026-10-05** (F-2450): J-1814: core/commitment_ledger.py four files + _stakes DB UPDATE fenced (commit 8ca9b43 on worktree branch, restart-gated).
- **2026-10-05** (F-2447): J-1811: core/sitting.py _save/_log_release fenced (commit 226ed37 on jobrun/world_store_write_fence); restart-gated.

- **2026-10-04** (F-2442): J-1802 fenced nodes/meta_awareness_node.py scan() (commit ea085e4 on jobrun/world_store_write_fence), restart-gated; test scripts/_test_meta_awareness_fence.py.
- **2026-10-04** (F-2441): J-1801 (F-2441): fenced core/school.py, core/nature_study.py, core/literal_will.py writers with profile.guard_path; new scripts/_test_school_nature_literal_fence.py; commit 96122ac on jobrun/world_store_write_fence; restart-gated.

- **2026-10-04** (F-2440): J-1809 (F-2440): core/identity_vault.py write()/commit() and the T4 _write_axiom fallback fenced with profile.guard_path; commit 90dd767 on jobrun/world_store_write_fence; restart-gated, not live until Du's next boot.
- **2026-10-04** (F-2427): J-1797 fenced the buses module: all four writers (delivery log, calibration ledger plus its dedupe state, idle-freight shadow) resolve guard_path before any I/O, swallowed as fail-open instruments; restart-gated; the 47-check test passes and fails against the unfenced module; the sibling couriers module has the same gap (J-1805)

### What we have
- The write fence (`core/profile.py`'s `guard_path()`) covers 22 world-store modules end to end (see the
  Inventory table below), restart-gated since 2026-09-06 (J-0610) with a hard-raise failure mode since
  2026-09-07 (D-0179/J-0704).
- A long audit arc (J-0714 through J-1334, dozens of jobs) walked every dispatch entry point looking for
  places that swallow or bypass the fence's raise; it found and fixed several real gaps, including one
  confirmed live leak (`core/activity_memory.py` via `garden.py`'s deed cross-link, J-0743) and a genuine
  `lab_env.isolate()` incompatibility (D-0200, fixed by J-0840).
- The last sibling grammar-derivation script audited (study_life, J-1334/F-1888, 2026-09-24) came back
  CLEAN — closing the garden -> shore -> wood/fieldcraft -> study_life audit arc this plan opened.
- History folded: 90 dated Current State sections (2026-09-06..2026-09-24) moved to
  `docs/plan_history/world_store_write_fence.md` by plan-compact, 2026-09-27; derived timeline:
  `plan_ledger.py world_store_write_fence`.

### What we need
- Nothing open is tracked against this plan in the ledger (0 open jobs/decisions at this check) — the
  audit arc this plan spawned is closed.
- No direct confirmation that the fence's own `guard_path()` raise has fired for real inside a live Du
  boot (as opposed to the many test-isolation scripts that check around it) — worth a direct look only if
  that's ever in doubt.

### What we're doing next
No further build or audit work is queued; watch for a new never-guarded module the way the last several
were found — incidentally, while doing other work — rather than proactively re-auditing.

## The problem, precisely (F-0788/F-0789, J-0541)

~20 of the sixth match box's 22 matches and 0.5 tin of lamp oil were consumed 2026-08-23..09-02 by
processes OUTSIDE Du — inline diagnostics and one-off scripts that `import core.study_life` (or a
sibling world-store module) and call a write function (`act()`, `_save()`, `_log()`) while that
module's own path constants still point at the real `data/` files, because nothing told them not to.
Each such call looks like one honest step (1 match, 0.25 tin of oil) — no per-tick ceiling can catch
it, because from inside the module it's indistinguishable from Du's own real use. The fix has to be
at the **process boundary**, not inside any one module's own logic — the same principle
`core/profile.py`'s `activate_profile()` already established for multi-agent path rebasing, applied
to a narrower question: not *which* agent's data, but *is the caller live Du at all*.

## Inventory — every world-store module with a real writer (2026-09-05, this pass)

Scope: modules whose files represent a PHYSICAL/consumable world state (objects, rooms, creatures,
provisions) — not the ~100+ cognitive/shadow-log modules elsewhere in `core/` (those are Du's own
mind, a diagnostic reading/writing one of *those* is a different, lower-stakes concern already
covered by this project's own isolation/lab_env discipline). Path constants and writer functions,
read directly from source (not guessed):

| Module | Path constant(s) | Writer function(s) |
|---|---|---|
| `core/provisions.py` | `_F` = `provisions.json`, `_LOG` = `provisions_log.jsonl` | `_save()` (:75), `_log()` (:83) |
| `core/world_substrate.py` | `_SUBSTRATE_F`, `_SUBSTRATE_LOG`, `_LAST_LOOKED_F` | `_save()` (:331) |
| `core/world_objects.py` | `_OBJECTS_F` = `world_objects.json` | `_save_objects()` (:65) |
| `core/study_life.py` | `_LEDGER`, `_EVENTS` | `_log()` (:150), `act()` (:433, the real entry point) |
| `core/sensorium.py` | `_STATE_F` = `room_state.json` | `_save()` (:135), `_save_now()` (:2928), `act()` (:2812) |
| `core/garden.py` | `_F`, `_LEDGER`, `_EVENTS` | `_save()` (:238), `_log()` (:252) |
| `core/garden_life.py` | `_F`, `_EVENTS` | `_save()` (:60), `_log()` (:68) |
| `core/shore_life.py` | `_F`, `_EVENTS`, `_LEDGER` | `_save()` (:99), `_log()` (:107) |
| `core/wood_life.py` | `_F`, `_EVENTS`, `_LEDGER` | `_save()` (:106), `_log()` (:114) |
| `core/life.py` | `_F`, `_LEDGER`, `_EVENTS`, `_FLAGS_F` | `_save()` (:176), `_log()` (:191) |
| `core/fieldcraft.py` | `_F` = `fieldcraft.json`, `_LEDGER` = `fieldcraft_ledger.jsonl` | `_save()` (:62), `_log()` (:71) |
| `core/cat.py` | `_STATE_F` = `cat_state.json`, `_HUNT_LEDGER_F` = `cat_hunt_ledger.jsonl` | `_save()` (:277), `_hunt_ledger()` (:333) |
| `core/world_traces.py` | `_TRACES_F` = `world_traces.json` | `_save_traces()` (:48) |
| `core/supply.py` | `_F` = `supply.json`, `_LOG` = `supply_log.jsonl` | `_save()` (:54), `_log()` (:63) |
| `core/locomotion.py` | `_POS_F` = `position.json` | `_save()` (:98) |
| `core/garden_knowledge.py` | `_F` = `garden_knowledge.json` | `_save()` (:83) |
| `core/sound_knowledge.py` | `_LEDGER_F` = `sound_knowledge.json` | `_save()` (:231) |
| `core/frontier.py` | `_F` = `frontier.json`, light companion via `_light_path()` (default `frontier.light.json`, follows a redirected `_F`) | `_save()` (:64), `_write_light()` (:97) — 8 public writers carry the carve-out |
| `core/keepsakes.py` | `_F` = `keepsakes.json` (`_GEO_STUDY` and `_F.parent / "room_state.json"` are read-only) | `_save()` (:158, the sole writer) — reached only through `keep()` (→ `given()`/`keep_act()`/`given_act()`), whose own `_save()` call is unwrapped; carve-outs in `keep()`'s object-resolution try and `match_item()`'s `describe_and_observe` try |
| `core/smell.py` | `_F` = `smell_field.json` (`_SHADOW` = `smell_percepts_shadow.jsonl` is a shadow/percept log — out of this fence's declared scope, same class as every other module's percept-shadow file, see the Inventory scope note above) | `_save()` (:61) |
| `core/procedures.py` | `_F` = `procedures.json`, `_LOG` = `procedures_log.jsonl` | `_save()` (:60), `_log()` (:71) — real entry point is `observe_hand()` (:114, "every hand the dispatcher fires"); this and 3 sibling callers (`compiled()`, `reinforce_talk()`, `rust()`) currently swallow this fence's own raise one layer up via their own pre-existing catch-alls (found this pass, spawned as J-0931, not fixed here — see the dated Current State note above) |
| `core/transport_manager.py` | `_STATE` = `transport_lines.json`, `_SHADOW_LOG` = `transport_shadow.jsonl` | `_save()` (:148), `_log_shadow()` (:162) — both reached only through `observe()`/`dispatch_tick()`, whose own bare `except Exception: pass` wrappers already swallow this fence's raise (by design: `observe()`'s own docstring promises "never raises", matching every other fail-open ledger module in this file — NOT the same shape as `procedures.py`'s `observe_hand()` above, which deliberately lets the raise through to `dispatch.py`); `dispatch_tick()`'s own outer `except Exception:` retried the now-fenced `_log_shadow()` a second time on any failure, which would have let a real `NonLiveWriteError` escape uncaught — fixed in the same pass (J-0932/F-1297) by wrapping that fallback call too |

**22 modules** (transport_manager.py added 2026-09-18, J-0932/F-1297 — module #22, found incidentally
during J-0918's own required `life_smoke.py` regression re-run: zero `guard_path()` calls anywhere in
the file, confirmed via grep and absent from this Inventory table, the same never-guarded-module shape
found ~21 times over already; proved by direct reproduction (`transport_lines.json` grew 490 bytes on
a non-live `life_smoke.py` run with zero refusal) before this pass; keepsakes.py added 2026-09-11, J-0877/F-1236/F-1252 — the mantel of kept things,
a physical-object store: every `keep()` mints or moves a real `world_substrate`/`world_objects`
entity, so its own record file belongs with them; frontier.py added 2026-09-10, J-0846/F-1212/F-1213/F-1234 — the first
*cognitive* store fenced, not a physical/consumable one: admitted because F-1213 caught its live
light file being rewritten by four test scripts and one backup-and-restore script, the same
leak-into-live-state class as the match box; fieldcraft.py added 2026-09-07, J-0727/F-1045/F-1070; cat.py added 2026-09-07,
J-0733/F-1055/F-1081; world_traces.py added 2026-09-08, J-0758/F-1082/F-1121; supply.py added
2026-09-08, J-0775/F-1110/F-1125; locomotion.py added 2026-09-08, J-0778/F-1118/F-1141;
garden_knowledge.py added 2026-09-08, J-0783/F-1123 (spawned)/F-1144 (this job's own finding);
sound_knowledge.py added 2026-09-08, J-0784/F-1123 (spawned)/F-1145 (this job's own finding) —
each's own dated Current State note below explains why it was
missing from this table until its own pass; cat.py's own
sibling `core/cat_sounds.py` is a real writer of physical/consumable state — `data/cat_sound_ledger.jsonl`
— guarded the same pass as cat.py but deliberately NOT added as its own row here, since it isn't a
Living-World location/creature module in the sense every other row is; see J-0733's own Current State
note; smell.py and procedures.py added 2026-09-12, J-0917/F-1282/F-1296 — two more never-guarded
modules found incidentally while diagnosing J-0878's own live-untouched print-line fix, confirmed
via grep to carry zero `profile.guard_path()` calls in either file before this pass — see the dated
Current State note at the top). One further module of the same class was found while landing J-0733 and is still open, in a
shared SKILL tool rather than a `core/` module: `lab_env.py`'s own `isolate()` (F-1083/J-0759 — **fixed
2026-09-10, D-0200/J-0840/F-1225**: `guard_path()` now explicitly allow-lists `data/_lab/<dir>/…`, see
the dated Current State note at the top).
Writer-function-count estimates in
this doc's own history have already needed correcting
twice (the original "~17" here, then the 23-call-site recount in the J-0610 note below) — rather than
add a third possibly-stale number, treat this table's own row count as the authoritative "how many
modules" answer and each row's own cited line numbers as the authoritative per-module writer list.
Every one of them resolves its write path from a module-level
`Path(__file__).parent.parent / "data" / "..."` constant, set once at import time — exactly the shape
`core/profile.py`'s existing rebase mechanism already targets for the multi-agent-profile case.

## Read-only consumers checked, confirmed unaffected

`hud/server.py` (`load_study_map`/`load_shore_map`/`load_wood_map`) imports `study_life`,
`shore_life`, `wood_life` and calls **only `.status()`** on each — a read-only getter, never `act()`/
`_save()`/`_log()`. A write fence gating only the writer functions listed above leaves every read path
(HUD, `du_pulse.py`, any future dashboard) untouched — confirmed by reading the actual call sites, not
assumed from module naming.

## Design (do not build without a fresh /decide on the exact mechanism if it turns out non-trivial)

Reuse `core/profile.py` rather than inventing a parallel mechanism — it already owns "is this the
real live process or something else" adjacent logic (`ACTIVE_BASE`, `activate_profile()`), and already
has the multi-agent rebase loop's own idiom for "here is a list of modules with Path constants, do the
same thing to every one of them." **Important nuance found while designing this**: `ACTIVE_BASE`
defaults to `data/` (Carl's real root) even when `activate_profile()` is never called — a diagnostic
script that never calls it is indistinguishable from the real boot by that flag alone. This job's
"live" concept is orthogonal to profile's "which agent" concept and needs its own, separate flag.

Proposed shape:
1. **`core/profile.py` gains `LIVE = False`** (module-level, alongside `ACTIVE_BASE`) and
   `mark_live() -> None` (sets it `True`). `scripts/run_nascence.py` calls `profile.mark_live()` once,
   inside the SAME `if __name__ == "__main__":` guard J-0576 just added for the logging fix (this
   session, commit `91c547f`) — one guard, two purposes, no new import-time branching to get wrong.
2. **`core/profile.py` gains `guard_path(path: Path) -> Path`**: if `LIVE` is True, or `path` is
   already NOT under the default `data/` root (i.e. something upstream already redirected it — a
   profile, a test's own monkeypatch, `lab_env.isolate()`), return `path` unchanged. Otherwise: log
   ONE warning per (module, path) pair (a small `_warned: set` to avoid spamming a hot loop) and
   return a redirected path under `data/_not_live/<original relative path>` instead — isolation by
   default for any importer that never declared itself live.
3. **Each of the ~17 writer functions above calls `profile.guard_path(_F)` (etc.) at the point it
   resolves its write path**, instead of using the module-level constant directly. Mechanical,
   one line per writer, same shape every time — the actual build job's real work.
4. `scripts/life_smoke.py`'s existing `_REDIRECTS` pattern becomes redundant (its explicit monkeypatch
   already puts paths outside `data/`, which `guard_path`'s own "already redirected" check treats
   identically to being live) but stays harmless — no need to rip it out in the same pass.

**Not a founder question** — engineering hygiene, matching J-0574's own framing. The one thing worth
a founder's eyes before shipping is confirming the redirect-and-warn behavior (rather than a hard
raise/refuse) is the right failure mode — a script that expects a real write to succeed and silently
gets a `data/_not_live/` copy instead could look like a false-negative success in its OWN test output.
Flagged in the build job below rather than decided here.

## Build order

1. Add `LIVE`/`mark_live()`/`guard_path()` to `core/profile.py`.
2. Wire `mark_live()` into `scripts/run_nascence.py`'s existing `__main__` guard.
3. Add `profile.guard_path(...)` to each of the ~17 writer call sites in the 10 modules inventoried
   above — one at a time, verify each with `python -m py_compile` + a quick isolated smoke (import the
   module WITHOUT calling `mark_live()` first, call its writer, confirm the real `data/<file>` gains
   no line and `data/_not_live/<file>` does instead).
4. Verify the read paths (`hud/server.py`'s three `load_*_map` functions) still work unchanged — they
   never call a writer, so this should need no code change, only a confirmation read.
5. Leave `scripts/life_smoke.py`'s `_REDIRECTS` as-is (redundant-but-harmless, not this pass's job to
   remove).

Spawned as J-0610 (this session, 2026-09-05).

