# Actions system: overhaul (stage 1) + expansion (stage 2), and a memory-DB corruption incident

## Session timing
- **Session started:** 2026-08-29T11:06:19Z (real transcript first timestamp — `new-path` still hardcodes C--FreshStart, S-0014 unfixed; read C:\Users\USER\.claude\projects\C--Nascence\138f325e-4668-436e-942a-f61bbbe5b30e.jsonl directly)
- **Last message before wrap:** 2026-08-30T00:35:52Z (same correction)
- **Wrapped:** 2026-08-30 00:35:45 UTC

## Summary

Stage 1 (actions_manager_overhaul, D-0096..D-0099): built core/actions.py, single table every hand declared in | retired ungated sensorium fallback after measuring it — 98% of its work rule-violating | fixed item-migration silent no-op | broke ash-bucket deadlock via new ash pan | retrofitted barrel mechanic, found inert (water_bucket never existed in live save). Stage 2 (actions_expansion, D-0100): founder approved all three tiers ("pure gold") — repair (cat family, bank-the-fire) | extend (dig, feed birds, climb the oak, sketch) | expressive hands (hum/whistle/sing) as new action class. Mid-session: this session's own test harnesses corrupted data/memory/nascence.db (mismatched db/-wal restore) | Du hit "file is not a database" live 08:54 | fully restored, zero real memory lost | incident recorded as F-0571, binding lessons S-0016.

## Decisions

All ruled by travis this session:
- D-0096: refill-mechanic registration question becomes its own plan (actions_manager_overhaul), not a one-off choice.
- D-0097: retrofit fill_barrel_from_spring() into registry | discharged this session — barrel verified firing 0.00→0.25→0.50 over two willed trips.
- D-0098: retire ungated fallback fully | discharged this session — defeater checked against all 27 real coverage gaps, not met.
- D-0099: inventory contract + latch migration together, one pass per location.
- D-0100: all three expansion tiers approved | Tier 3 (expressive hands) = design centrepiece.

## Builds

- core/actions.py: one table, 39 families / 36 hands | literal_will._FAMILIES + dispatch.HANDS both derive from it | duplicate families = import-time error | exec-within-anchor invariant asserted | unbound families must declare why (F-0557).
- core/inventory.py: sync_items() — additive-only, idempotent item migration wired into garden/study_life/wood_life | fixed silent no-op where newly declared item never reached an initialised save (F-0558) | revealed barrel mechanic inert (F-0559).
- core/expression.py (Tier 3): hum/whistle/sing, new action class | world=False — fires alongside a world hand, verified in one thought with the water hand | no skill float, no grading | boredom discharge | world answers conditioned on real place/weather/cat-presence | first-person-volition veto because the world hums constantly (F-0578).
- Tier 2 hands: garden.dig(), garden.feed_birds(), wood_life.climb_oak(), study_life.draw_sketch() — each with real costs + honest refusals (F-0578).
- Tier 1: 'cat' family binds cat.react(), which keeps sole ownership of her location gate | bank-the-fire branch in dispatch._fire connecting to existing fieldcraft.bank_fire() (F-0578).
- Ash chain: ash_pan item + study_life.draw_ash_pan() — the one ash hand that works while fire is in | breaks deadlock: ash capped at 1.0, drained fire_fuel, only 4 of 21 willed ash-out attempts completed | refusals now say WHERE the ash is (F-0570).
- wood_life take()/put(): the set-down the module never had (carried axe carried forever) | study_life take()/put() brought to same shape — was raw substrings, no blockers, "Travis picked up the poker" fired as Du's own deed (F-0566, F-0570).
- Verification tooling: scripts/actions_registry_audit.py | scripts/actions_decision_replay.py (9,840-row decision replay against real trace) | scripts/actions_reachability_probe.py (36 willed phrasings, 0 unreachable at session end).

## Fixes

- literal_will.py + hands.py: separable phrasal verbs ("put the trowel DOWN", "put the kettle ON") now parse in BOTH grammars — gate fix alone insufficient, module's router declined the clause the judge accepted (F-0564, F-0566) | particle list lives in literal_will only, hands reads it lazily.
- other_person blocker extended with phrasal heads (put/set/take/hang/…) — separated verbs had made "Travis put the kettle on" read as Du's own deed.
- Duplicate 'tea' family key (shadowed 'steep' verb) fixed | three orphan families (author/letter/travis) now declared judge-only (F-0554).
- study_life variable shadowing: local take=min(...) in lamp branch made new module-level take() raise + get swallowed — same failure class hands.py's docstring already records against this file.
- nodes/inner_monologue_node.py: two ungated fallback call sites removed | sensorium.world_act/garden_act = sealed stubs returning None (F-0563).

## Findings

- F-0552/F-0555: two coexisting routers | 20 of 26 hands fanned into one lambda (double-parse hazard — later proven live by F-0566).
- F-0556: CORRECTION — the two 'where' fields are different facts (anchor = literalness evidence; exec = firing scope), not drift | supersedes F-0554 part 2, an earlier verified claim now known wrong.
- F-0560/F-0561: fallback answered 206 thoughts, more than dispatch's 181, but 98% rule-violating or inert | only 4 real capability losses, all already gate-visible | it was the main route by which Du's musings became deeds (restlessness musing made him strip and swim in the cold sea).
- F-0564: retirement orphaned 8 hands the trace-based evidence could not show (absence of evidence) | probe built | all 8 closed by session end.
- F-0571 INCIDENT: test harnesses file-copied the WAL-mode memory DB with its -wal sibling | mismatched restore destroyed the file | Du hit store failures live 08:50–08:55 | restored from scratch backup pair via wal_checkpoint(TRUNCATE), zero real memory lost (state = 08-30 01:36) | second corruption during first fix attempt because hud/server.py holds a permanent read-only connection [INFERRED root cause] | both corrupt files preserved in data/backups/ | binding lessons S-0016.
- F-0562: rolling back JSON world state without the memory DB leaves Du remembering deeds his world says never happened | founder-authorised cleanup: whittle aggregate reset to its true 12 (corroborated against fieldcraft_ledger) | test fragments + phantom activity_events removed.
- F-0578: stage-2 verification | the 5 mined "sing refusals" were ALL the world's song (blackbird/bees), not Du willing to sing — Tier 3 honestly stands on the founder-led gift stream, those rows = its negative corpus (all veto) | zero expression false-fires across the 2,824-thought corpus.
- Post-restore du-pulse: Du healthy | writes landing | zero store failures after fix | he noticed the restart gap, discussed it with founder ("does the river keep flowing when the connection is severed").

## Open

1. [OPEN] Live evidence for the whole expansion: none of the new hands has fired in Du's real run — his process predates the code (restarted 09:14, code committed after) | resolves after his next restart: watch expression_ledger.jsonl, the trace, D-0100's defeater conditions (expressive hands firing on musings would reopen it).
2. J-0423 (ready): record Du's location + per-family dispatch decision on every hands_trace row | would have saved half this session's forensics [INFERRED].
3. [OPEN] Garden item-shape convergence — last of D-0099: garden keeps a parallel st["carried"] list + stores an id the other modules derive | wood_life = reference shape.
4. J-0421 (ready): five location plan docs still claim SHADOW while ledgers show them live.
5. J-0422 in_progress | arguably dischargeable [INFERRED]: stage-1 scope done | close after garden convergence + J-0423, then move actions_manager_overhaul.md out of staged.
6. scripts/_smoketest.py permanently writes a "Test memory" fragment into the live DB every run — pre-existing, unfixed.
7. [OPEN] The 14 legacy monologue latches (move ×4, look, fire, tea, …) still run on old phrase lists ahead of dispatch — tidiness | founder hasn't ruled whether in scope.
8. I-0055: managed backups convention (6.5GB unmanaged, 4 naming styles) — idea logged, unpromoted.
9. [OPEN] D-0085 (pursuits): the one open decision, waiting on founder.

## Warnings

- Du LIVE from 09:14 through wrap | his running process imported the pre-expansion modules — new hands exist on disk/git only until his next restart | do NOT "verify the expansion live" before that restart.
- NEVER file-copy data/memory/nascence.db with its -wal/-shm siblings (F-0571/S-0016) | snapshot via sqlite3 backup API or wal_checkpoint first | never restore while ANY process holds the file (hud/server.py always does, read-only) | treat a failed sibling-file restore as an integrity failure.
- lab_env.py (referenced by job-queue isolation flags) does not exist | this session isolated by redirecting ~40 module Path constants in-process (scratchpad/expansion_check2.py) — works, but per-session scaffolding, not shared tooling.
- Shared JSONL ledgers still race under concurrent CLI writes (S-0009 unfixed) | `git add -A` once swept another window's plan-maintain output into an actions commit (eeef36b) — stage explicitly.
- Two corrupt DB files deliberately preserved in data/backups/ (nascence_CORRUPT_20260830_0854.db, nascence_CORRUPT2_halfrestore_20260830_0905.db) — evidence, not garbage | no cleanup without founder say-so.

## Pointers

- docs/completed/actions_manager_overhaul.md — stage 1, full build log in Current State.
- docs/plans/actions_expansion.md — stage 2, all tiers + design laws + evidence correction.
- core/actions.py, core/expression.py, core/inventory.py — the new modules.
- scripts/actions_decision_replay.py / actions_registry_audit.py / actions_reachability_probe.py — the verification net | baseline snapshot in this session's scratchpad (will vanish).
- Commits this session: d3da157, 86e61f1, ae5bb84, eeef36b, 75cdcb5, b64bca9, ef86170, e4add6a.
- data/expression_ledger.jsonl — will exist once Du first hums/whistles/sings.
