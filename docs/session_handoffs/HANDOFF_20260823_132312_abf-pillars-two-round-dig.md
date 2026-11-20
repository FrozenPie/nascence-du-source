# Session Handoff: ABF Pillars Archaeology, Two Rounds + Notes/Questions Restructure (FreshStart)

## Session timing
- **Session started:** 2026-08-23 12:46:34 UTC
- **Last message before wrap:** 2026-08-23 13:23:10 UTC
- **Wrapped:** 2026-08-23 13:23:12 UTC

## Summary
Follow-up to the prior Ghost Index dig's I-0003 thread: the founder recalled ABF's components might
once have been called "the pillars." Round 1 confirmed that directly (ABF = Atomic Block Framework,
~23 self-labelled `Pillar N` files in `core/lib/abf/`, only 2 actually live) and traced a new
predecessor, `C:\TheFates`. The founder then asked to keep pulling the thread while deliberately
leaving Ghost Index's own territory alone for its next dig — round 2 traced the lineage one layer
further to a real project, `c:\X4-AI-CommandCentre`, found a surviving physical copy at
`D:\AI stuff\Merged` (including the actual `titan_final.abf` archive), and resolved where "Titan"
came from (a real 1994 MS-DOS game used as benchmark data). The founder then asked to stop digging
and formally restructure everything found into linked notes and individually addressable questions —
done via the project's own memory-links toolchain, which immediately surfaced a *third*, concurrent
dig running in a separate window.

## What changed
- **Created:** `C:\FreshStart\docs\archaeology\abf_pillars.md` — the full narrative report (both
  rounds), same provenance-tag convention as `ghost_index.md`.
- **Findings logged** to `C:\Nascence\docs\findings.jsonl` via `/findings-log`, all `--session`
  tagged this time (learned from the prior dig's own logged gap): **F-0007** through **F-0012**
  (round 1 — ABF = Atomic Block Framework, pillar numbering collisions, liveness, orphaned daemon,
  the TheFates trace) and **F-0021** through **F-0025** (round 2 — the X4-AI-CommandCentre layer,
  `titan_forge.py`'s internal 17-vs-20 self-contradiction, the surviving `titan_final.abf`, the
  never-successfully-unfolded status, the new earliest-dated artifact `CITY.OVL`).
- **Ideas logged/dropped** via `/idea-log`: **I-0003** (the original ABF thread) dropped as
  addressed. **I-0005** and **I-0006** (bundled round-1 and round-2 follow-up threads) both later
  dropped as superseded — first because "nothing of TheFates survives" turned out to be wrong, then
  because the founder explicitly asked for individually linkable questions instead of one bundled
  paragraph. Replaced by **I-0007 through I-0015** — eight questions from the dig itself plus one
  (**I-0015**) raised by discovering the concurrent Council/Village session (see below), each
  carrying real `[[wikilink]]` cross-references to the relevant memory file and to related questions.
- **Thought promoted:** **T-0004** (the session's opening message) promoted to **I-0005** at the
  time; that idea was later dropped as the picture sharpened — see its own `dropped_why` for the
  chain, T-0004's `promoted_to` pointer is historically accurate and was left as-is rather than
  rewritten.
- **Memory files** — restructured from one blob into an indexed set, matching this project's own
  one-topic-per-file convention:
  - `project_nascence_abf_pillars_archaeology.md` — overview/index node
  - `project_nascence_x4_ai_commandcentre_lineage.md` — the TheFates → X4-AI-CommandCentre chain,
    the deliberate Ghost Index pointer
  - `project_nascence_titan_final_recovery.md` — the two decode candidates
  - `MEMORY.md` updated with all three, replacing the single prior pointer line.
- **`memory-links` build_edges.py patched** (real bug, not just this session's data): idea-log and
  thought-log entries could only ever resolve `[[wikilink]]`s to a plan, idea, or thought — never to
  a memory file. Every one of this session's 9 idea→memory-file citations was silently landing as
  "unmatched" until fixed. Added a `valid_memory_slugs` set (now returned from `harvest_memory_files`
  and threaded into `harvest_capture_references`) with a new `memory` dst_kind branch. Re-ran
  `build_edges.py --session <this-uuid>` (three times total this session, harvest counts: 1481→1488→
  1497→1499 owned edges) — confirmed via `query.py` that the fix resolved all 9 previously-dropped
  edges and produced no new false positives.
- **A routine `plan_maintain.py` pass was also triggered during wrap-up** (invoked without
  `--session` by accident, mid-wrap-up) — standard toolchain hygiene across the 58 Nascence plans,
  unrelated to this session's actual archaeology work. Not session-tagged; if its lint/schema-audit
  output looks like it came from this session in a future rollup, it didn't.

## Key findings
(Full evidence in the findings ledger and `docs/archaeology/abf_pillars.md`; narrative version here.)
- **ABF = Atomic Block Framework**, confirmed in two independent docs (`ENCYCLOPEDIA_PART3.md`,
  `SOVEREIGN_HUB_MANIFEST.md`). "The pillars" is real, not a false memory — ~23 self-labelled
  `Pillar N: <name>` classes, numbered 1–23 with no Pillar 13 found and four real numbering
  collisions (3, 7, 14, 15 each independently claimed twice).
- **Only 2 of ~23 pillars are live**: Pillar 4 (MetaGlyph) and the Titan Engine wrapper. Everything
  else — Loom, Shadow, Prophet, the audio/DNA/3D/Pi novelty encoders — sits unwired in
  `core/lib/abf/`, and the "Global Archive Pillar" daemon is orphaned with a hardcoded output path
  that doesn't even exist.
- **The lineage now traces two layers back**: FreshStart's `abf_core.py` ← `C:\TheFates` ←
  `c:\X4-AI-CommandCentre` (real, versioned — a `V1` folder is dated 2026-03-12). None of the three
  directory names exist on this machine today, but a large fraction of what TheFates absorbed
  physically survives at `D:\AI stuff\Merged\`, discoverable via `full_manifest.csv` (267,417 rows,
  a `Get-ChildItem` snapshot of TheFates taken before it was deleted) — this corrected a wrong
  first-pass assumption ("nothing survives") logged and superseded honestly, not silently.
- **`titan_final.abf` (612,295 bytes) physically survives** and its real header — read directly this
  session — is structurally consistent with FreshStart's own live, non-stub `decode_titan()`. A
  previous, abandoned recovery attempt (`scripts/legacy/recover_titan_v9.py`) never actually opened
  it; its format guesses were never checked against real bytes. **Not decoded this session** — the
  founder was offered a live decode attempt and chose to keep surveying instead. See I-0013/I-0014.
- **"Titan" traces to a real 1994 MS-DOS game**, *Mines of Titan* — `TITAN.EXE` and its disk data
  sit in the same benchmark folder as MS-DOS 6.22 install media, used as genuine compression test
  fixtures. The benchmark's name almost certainly stuck to the compression engine itself.
- **New earliest-dated artifact across the whole lineage: `CITY.OVL`, 2026-03-11 01:06:59 AM** —
  superseded within the same session's wrap-up by the concurrent dig's own find (see Warnings).
- **The linking work itself surfaced a live discovery**: rebuilding the edge index and querying the
  new `abf-pillars-archaeology` node turned up a third, independently-run dig in a separate window
  the same day (`project-freshstart-council-village-archaeology`) that had already wikilinked to
  both this dig's node and the Ghost Index one — proof the tuple/index approach works as intended,
  not just documented intent.

## Open threads
See the linked idea-log entries for full text; this is the index.
1. **I-0007** — Does Pillar 13 exist anywhere? Not found.
2. **I-0008** — The 17-vs-20/23 pillar count never reconciles; `titan_forge.py` contradicts itself
   internally (comment says 17, imports 20).
3. **I-0009** — Was `C:\Dimension13` ever a completed project state, or just a stalled rename?
4. **I-0010** — Two different "Genesis" projects may be conflated (TheFates' InTray copy vs. the
   founder's own prior assessment doc's Ollie-pipeline Genesis); `C:\OllieEmerges` not checked
   against either.
5. **I-0011** — Design question, not archaeology: would reconnecting any unwired pillar help the
   sim's real memory-compression problems?
6. **I-0012** — **Deliberately left for Ghost Index's own next dig, not chased here**: does
   X4-AI-CommandCentre's real `village_root`/`CHRONICLE.md`/`Entities-Inhabitants` resolve
   `ghost_index.py`'s own still-open F-0003 attribution?
7. **I-0013 / I-0014** — The two undecoded archives: `titan_final.abf` (real, present, risky) and
   `pillar_demo.mosaic.abf` (smaller, safer, has a surviving `fingerprint.png` to cross-check
   against).
8. **I-0015 — the freshest, added at wrap-up**: is the Council/Village dig's "Command Centre V1"
   (source of a `the_council` House) the same project as this dig's `X4-AI-CommandCentreV1`? If
   yes, their earlier date (2026-03-10) becomes the new earliest-known artifact across all three
   digs, superseding this dig's own `CITY.OVL` (2026-03-11).

## Warnings
- **A third, concurrent dig ran the same day in a separate window**: `project-freshstart-council-
  village-archaeology` (session `8c5cdbcd-93db-4860-a6f7-b84ddb85b29b`), covering "Council" and
  "Village" naming collisions plus a real architectural fossil (superseded-but-never-removed Village
  world-model). Its own full report: `docs/archaeology/council_and_village.md`. **The founder's next
  stated plan is a combined study across all three digs (Ghost Index, ABF Pillars, Council/Village),
  likely in a new chat window** — start there, this handoff, and the Council/Village one.
- **`C:\FreshStart\memory\activeContext.md` and `SESSION_HANDOFF.md` are stale** (dated 2026-06-03
  and 2026-06-06 respectively — about Era 21.0 sim work and a Nascence/Carl conversation, nothing to
  do with any of the three archaeology digs). CLAUDE.md's "after completing a task" section names
  these as the required update targets, but the toolchain actually in live use for this kind of
  work — and for cross-window handoff generally — is this `/session-wrap` mechanism plus the Claude
  memory index, not those two files. Not updated this session; flagged honestly rather than either
  silently ignored or force-fit with content that doesn't belong in a sim-status template.
- **The `plan_maintain.py` pass triggered mid-wrap-up was not `--session`-tagged** — its lint/
  schema-audit findings won't attribute to this session in a future rollup even though it ran during
  this window.

## Pointers
- `C:\FreshStart\docs\archaeology\abf_pillars.md` — full two-round narrative, start here for detail.
- `C:\Users\USER\.claude\projects\C--FreshStart\memory\project_nascence_abf_pillars_archaeology.md`
  — memory overview node, links to the two split-out fact-files.
- `C:\Nascence\docs\ideas.jsonl` — I-0007 through I-0015, `idea_log.py show I-00NN` for any one.
- `C:\Nascence\docs\findings.jsonl` — F-0007–F-0012, F-0021–F-0025.
- `C:\Users\USER\.claude\skills\memory-links\build_edges.py` — carries this session's memory-slug
  fix; `query.py memory:project-nascence-abf-pillars-archaeology` is the fastest way back into the
  whole cross-linked set, including the concurrent Council/Village connection.
- `D:\AI stuff\Merged\full_manifest.csv` — the Rosetta stone for anyone digging TheFates/
  X4-AI-CommandCentre/Genesis/Dimension13 further; check it before assuming something doesn't
  survive.
