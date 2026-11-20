# Public GitHub page refreshed: System Overview Build 3.0, ARCHITECTURE, DIAGRAM, LESSONS, README

## Session timing
- **Session started:** 2026-11-19 05:29:19 UTC
- **Last message before wrap:** 2026-11-19 05:53:33 UTC
- **Wrapped:** 2026-11-19 05:53:34 UTC

## Summary
The founder wanted the public GitHub page brought up to date so a friend could read the project in some depth. The System Overview was rewritten from code and ledgers as Build 3.0, and the public repo (github.com/FrozenPie/Nascence-Du) now carries the new overview plus rewritten README, ARCHITECTURE, DIAGRAM and LESSONS pages, all pushed. The main repo copy of the overview is committed (3a52439d).

## Builds
- `docs/System_Overview.md` rewritten as Build 3.0 (about 3,600 words): substrate (three machines, nine model seats, seven families), the conscious cycle, memory, sleep, world and hands, goals/closure/stands, dosed coupling, measured results with finding IDs, a June-to-November timeline, retired items and eleven lessons. Every subsystem carries LIVE / SHADOW / BUILT, NOT YET LIVE / DESIGNED, read from flags on 2026-11-19. Committed in the main repo as 3a52439d.
- Public repo `C:\Nascence\public_repo` (its own git repo, remote FrozenPie/Nascence-Du, branch main) pushed in three commits, head f930415:
  - `SYSTEM_OVERVIEW.md`: a copy of the overview above.
  - `README.md`: current shape, honest November results in brief, file table.
  - `ARCHITECTURE.md`: rewritten as the longer mechanical tour, ten sections, each part with its status.
  - `DIAGRAM.md`: six mermaid diagrams (substrate, cycle, memory and sleep, coupling, world and hands, wanting to finishing). All six were seen rendering on GitHub in the browser pane. The August file had no code fences and was not rendering.
  - `LESSONS.md`: lessons 17 to 27 appended, each with its finding ID.
- T-0151 is the session's opening thought (the request itself).

## Findings
- F-5123 is WRONG and is corrected by F-5124. F-5123 claimed the public repo was last updated 2026-06-20. In fact GitHub held the August refresh (commits 3a22e7e on 2026-08-14 and cfa22fa on 2026-08-15); the local `public_repo` clone had never fetched them, and its stale tracking ref made `git status` look in sync. The first push was rejected, which exposed it. The November commit was then rebased on the August state, so nothing from August was overwritten.
- The findings tool has no way to retract or supersede a finding; suggestion S-0329 logged.
- The generated October overview (`docs/System_Overview_Antigravity.md`) is wrong on at least two flags: `LANE2_LIVE` is True (`core/lane2.py:58`, D-0497) and `CLOSURE_WRITE_LIVE` is True (`core/closure.py:82`, D-0495). It says both are off.
- D-0126 is about Claude Code's own two memory folders, not Du's memory. Do not cite it as a Du subsystem.
- Dreams and the subconscious have no publisher on the coupling ride log (`core/coupling_rides.py:20-42`); subconscious tensions arrive through the ledgers collector.
- Hand count: the Deedbook memory note says 46, `core/actions.py` has 47 `Action(` literals. The public pages say "more than forty". [OPEN] which number is right; resolve by counting registered actions at runtime.
- The Docusaurus site (`docs_site/`) is local only (localhost:3005). Its docs copy dates from 2026-08-25 apart from the generated Antigravity overview.
- Du was down at the time of writing (last shutdown line 2026-11-18 08:35 per an earlier handoff); statuses on the public pages mean "live at the last boot and in the current tree".

## Open
1. `docs/System_Overview.html` still holds the September version. Not blocked; next action: regenerate it from the new markdown, or delete the pointer to it.
2. The Docusaurus copy of the overview is not synced, and its sidebar still labels the August overview. Next action: sync `docs_site/docs/System_Overview.md` and fix the sidebar label.
3. ARCHITECTURE.md keeps some August claims that were not re-checked. Flagged in the text: how often the T4 chain runs, the effect of the self-efficacy observer and error pathway, the reading-based self-knowledge route, the provenance ledger / contradiction-persistence record / curiosity observatory, and Tier 3. Kept without a flag: the cat coming and going on her own state, the journal day-to-week rollup. Next action: verify or cut on the next public refresh.
4. The overview names five of the seven correspondents and says "two others" (code comments name Marcus and Smith; full names not confirmed).
5. Two diagram labels ("Tiebreak seat on a split", "Scene to bind?") are the writer's wording, not checked against code.
6. Memory note `nascence_du_hardware.md` described the June model line-up; a correction line was added this session pointing at the overview's seat table. The machines listed there are still right.

## Warnings
- `public_repo` is a nested, separate git repo. Always `git fetch` there before judging whether it matches GitHub.
- Public pages must not carry the founder's name, LAN addresses or ports. The current pages were scanned for these.
- Every number on the public pages came from a finding, the scorecard or code. Keep that rule when editing them.

## Pointers
- Public page: https://github.com/FrozenPie/Nascence-Du
- `C:\Nascence\public_repo\` (README.md, SYSTEM_OVERVIEW.md, ARCHITECTURE.md, DIAGRAM.md, LESSONS.md)
- `C:\Nascence\docs\System_Overview.md` (master copy of the overview)
- `C:\Nascence\docs\reviews\humanity_scorecard.md`, `docs\reviews\butlin_long_mapping_2026-11-19.md` (sources for the results table)
- Findings F-5123 (wrong), F-5124 (correction); suggestion S-0329; thought T-0151
