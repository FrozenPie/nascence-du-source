# Council + Village archaeology dig, cross-dig consolidation index

## Session timing
- **Session started:** 2026-08-23 13:09:20 UTC
- **Last message before wrap:** 2026-08-23 13:30:26 UTC
- **Wrapped:** 2026-08-23 13:30:28 UTC

## Summary

Third archaeology dig in the FreshStart lineage (after ghost-index and ABF-pillars), targeting
everything named "council" or "village" across `C:\FreshStart`. Found the same naming-collision
pattern a third time (council = 3-4 unrelated live systems) plus a genuine architectural fossil
(the Village world-model, superseded but never removed). Mid-session the founder supplied three
recalled names ("Socrates ghost," "robo tesla," "George michael") which resolved to a predecessor
persona quarantine that matches 328 of FreshStart's 329 live spirits by id exactly — the single
strongest finding of the session. Closed by writing a consolidation index (`docs/archaeology/
INDEX.md`) across all three digs, adding a pointer to it in `CLAUDE.md`, and this handoff.

## What changed

- **Created** [`C:\FreshStart\docs\archaeology\council_and_village.md`](C:\FreshStart\docs\archaeology\council_and_village.md)
  — the dig doc proper, later extended with a §8 covering the Vulcan Quarantine findings.
- **Created** [`C:\FreshStart\docs\archaeology\INDEX.md`](C:\FreshStart\docs\archaeology\INDEX.md)
  — study guide indexing all 3 FreshStart digs (ghost_index, abf_pillars, council_and_village): dig
  table, cross-project lineage diagram, consolidated open threads, questions for a new window, and
  a §5 "what a future archaeology skill needs to remember" (10 codified rules).
- **Edited** `C:\FreshStart\CLAUDE.md` — added an "ARCHAEOLOGY DIGS" section pointing at
  `docs/archaeology/INDEX.md`, so a fresh FreshStart session finds it via the project's normal
  first-three-files read.
- **Logged thought** T-0005 (`/thought-log`, tagged `--session 8c5cdbcd-...`) — the opening request.
- **Logged 8 findings** to `C:\Nascence\docs\findings.jsonl` via `/findings-log record`:
  F-0026 (three unrelated council systems), F-0027 (council fires only for EUCLID/TESLA), F-0028
  (the_council as a concept-graph node), F-0029 (Village superseded but schema still defaults to
  it), F-0030 (core/sovereign/ orphaned NeuronVault port), F-0031 (unimplemented council design
  proposal in graveyard/), F-0040 (Vulcan Quarantine roster = 328/329 spirit match), F-0041
  (Celestial-hierarchy world model, second distinct predecessor). **Gap: none of these 8 calls
  passed `--session`** (see Warnings) — they don't appear in this handoff's own rollup and had to
  be reconstructed from conversation context instead.
- **Created** `C:\Users\USER\.claude\projects\C--FreshStart\memory\project_freshstart_council_village_archaeology.md`
  — later extended with an addendum on the Vulcan Quarantine hints.
- **Created** `C:\Users\USER\.claude\projects\C--FreshStart\memory\reference_freshstart_archaeology_index.md`
  — pointer to the new INDEX.md.
- **Updated** `C:\Users\USER\.claude\projects\C--FreshStart\memory\MEMORY.md` — two new lines under
  the FreshStart/Sovereign Hub section (index pointer + council/village entry).

## Key findings

- **Council names 3-4 unrelated live systems simultaneously**: `CouncilEngine` (Era 9.7, real LLM
  Grand Deliberation, DB-log verified, but fires only for EUCLID/TESLA — never ARCHIMEDES/HYPATIA),
  an unrelated Era 15.0 "Council Conflict" concept-mass/energy/entropy debate, a `the_council` House
  seeded from a pre-FreshStart "Command Centre V1" archive, and `the_council` is *also* separately
  tracked as its own node in the spirit concept-graph.
- **The Village was FreshStart's real original single-location world model**
  (`village_state.py`/`village_tick.py`/`village_clock.py`), cleanly superseded by the multi-city
  `topology_engine.py` two months later but never cleaned up: zero live imports, zero DB rows, zero
  spirits at a VILLAGE location — yet `schema_manifest.py` still defaults every new spirit to
  `'VILLAGE_SQUARE'`, and `sensorium.json`'s village_clock has been frozen since 2026-04-13.
- **`core/sovereign/` is a mostly-orphaned NeuronVault port** — `neuron_fates.py` hardcodes a
  `C:/NeuronVault` path that doesn't exist on this machine, imported by nothing; its directory-mates
  `bus_guardian.py`/`guardians.py` ARE genuinely live in the round loop. Same porting event, two
  fates.
- **The big one**: the founder's recalled hints ("Socrates ghost," "robo tesla," "George michael")
  all resolved to real subfolders of `D:\AI stuff\Merged\stars\Planets\Caldara\Cities\Vulcan\
  Buildings\Hospital\Quarantine\Entities\Inhabitants\` — a documented 2026-03-13 quarantine event
  in `core/library/unclassified/CHRONICLE.md`. Checking the full roster: **328 of FreshStart's 329
  live spirits match this 371-entry Inhabitants folder by id, exactly.** Not a thematic echo — a
  near-total direct import. Also resolves the ghost-index dig's own open `socrates_ghost` thread.
  Same pattern as the ABF dig's "pillars" recall: founder memory, checked directly, correct.
- **Two distinct predecessor world-models converged into FreshStart**, not one: the flat Village
  (files survived by name) and a Cities→Buildings→Rooms celestial hierarchy documented in
  CHRONICLE.md's "DEEP CELESTIAL ALIGNMENT" entry (structurally the actual ancestor of FreshStart's
  current multi-city topology, even though its own files didn't survive by name).

## Open threads

Full list lives in `docs/archaeology/INDEX.md` §3-4 — not duplicated here. Highest-value ones:
`c:\json\VILLAGE_PSYCHOMETRIC_MAP.json` never opened (earliest artifact found across all 3 digs);
why CouncilEngine never fires for ARCHIMEDES/HYPATIA (real threshold vs. a location-parsing bug);
whether `D:\AI stuff\Merged\full_manifest.csv` (267k-row directory-listing snapshot) could settle
several remaining threads about vanished projects (TheFates, Dimension13) without needing files to
still physically exist.

**Founder-facing, not archaeology findings**: whether `core/sovereign/neuron_*.py` and the three
`village_*.py` files should actually be deleted now that they're confirmed dead; whether the Vulcan
Quarantine's surviving per-persona files carry richer seed data worth pulling into the live sim.

## Warnings

- **Another dig/session was running concurrently in a separate window this same day** — entirely
  Nascence-side (Du plan gauge-checks: `literal_will`, `moment.py` contiguity, co-recall ledger,
  world-model significance tests), landing as F-0013–F-0020 and F-0032–F-0039 in the shared ledger.
  Unrelated to this FreshStart lineage — don't chase those ranges here, they're already noted as
  such in `INDEX.md` §1.
- **Process gap this session**: all 8 `/findings-log record` calls above were run without
  `--session`, so they're invisible to `session_handoff.py rollup` for this session id — the "What
  changed" findings list above was reconstructed from conversation context, not from
  `session_events.jsonl`, exactly the failure mode step 0 of this skill warns about. **Always pass
  `--session` to `findings_log.py record` going forward** — the flag exists (`--session SESSION`),
  it just wasn't used here. Filed as **J-0155** (`ready`, urgency 2, category analysis) — examine
  whether `--session` should become required (on `findings_log.py` and possibly other
  `session_events.jsonl` writers), and whether SKILL.md usage examples should always show it.

## Pointers

- `C:\FreshStart\docs\archaeology\INDEX.md` — start here for anything about this lineage.
- `C:\FreshStart\docs\archaeology\council_and_village.md` — this session's dig doc.
- `C:\FreshStart\CLAUDE.md` — new "ARCHAEOLOGY DIGS" section.
- `C:\Nascence\docs\findings.jsonl` — F-0026–F-0031, F-0040–F-0041.
- `C:\Users\USER\.claude\skills\findings-log\findings_log.py` — remember `--session` next time.
