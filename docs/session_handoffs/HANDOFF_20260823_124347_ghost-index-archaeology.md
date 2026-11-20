# Session Handoff: Ghost Index Archaeology (FreshStart)

## Session timing
- **Session started:** 2026-08-23 12:10:09 UTC
- **Last message before wrap:** 2026-08-23 12:43:45 UTC
- **Wrapped:** 2026-08-23 12:43:47 UTC

## Summary
The founder asked whether a repeatable "code archaeology" process could be built — dig up ancient
parts of a codebase, recover how and why they were made, and keep verified fact strictly separate
from inferred/attributed/guessed claims, the same discipline Nascence's epistemic-source ledger
enforces. Rather than build tooling first, we piloted the method directly on a real, gnarly test
case in the sister project: FreshStart's "Ghost Index." The first pass scoped itself to
`C:\FreshStart` and concluded the pattern originated 2026-04-09; the founder pushed back that it was
"way older than that," which turned out to be correct — widening the search to `D:\AI stuff`
uncovered two independent predecessor projects with real, older file mtimes. The session closed
with a full write-up, six findings logged to the shared ledger, and two new ideas opened for
follow-up work in a future session.

## What changed
- **Created:** [`C:\FreshStart\docs\archaeology\ghost_index.md`](C:\FreshStart\docs\archaeology\ghost_index.md)
  — the finished archaeology report. Structure: a provenance key (VERIFIED/ATTRIBUTED/INFERRED/
  GUESSING tags on every claim), a pre-FreshStart lineage section, per-system deep dives, a closed
  "open threads" list, and a closing section on two self-caught scope/verification errors made
  *during* the dig itself.
- **Findings logged** to `C:\Nascence\docs\findings.jsonl` via `/findings-log`: **F-0001** through
  **F-0006** — the pre-FreshStart lineage dates, the FATAL_BACKUP date mismatch, the X4-AI
  attribution not resolving to anything on disk, the debunked FTS5-bug claim, and the v2.1/v2.2
  weaver version-drift puzzle. Full text is in the ledger; see the archaeology doc's §1-§6 for the
  narrative each one supports.
- **Ideas logged** to `C:\Nascence\docs\ideas.jsonl` via `/idea-log`:
  - **I-0003** — ABF, a named framework found running underneath multiple "ghost" component headers
    across at least two-three separate projects, never opened or identified. **This is the specific
    thread the founder wants remembered for a follow-up dig in a new session** — see Open threads
    below and the idea's own text for exact file paths.
  - **I-0004** — whether the archaeology method piloted this session (provenance tags + findings-log
    + a closed one-off doc) should be formalized into a repeatable indexed skill, or stay a one-off
    template. Not decided; just captured.
- **Thought promoted:** **T-0002** (the session's opening message, logged retroactively — see
  Warnings below) was promoted to **I-0004** via `/thought-log`.
- **`/plan-maintain --session <this-uuid>`** run at the end of the session — full pipeline (lint →
  plan_index → plan_files_audit → build_edges rebuild → decision-edge resync → plan_liveness →
  plan_snapshot → plan_schema_audit) completed clean relative to this session's own changes; the
  lint findings it surfaced (missing "Current State" sections on 31 plans, one bad decision slug,
  etc.) are pre-existing toolchain debt, not caused by this session.

## Key findings
(Full evidence strings are in the findings ledger; this is the narrative version.)
- **The ghost_index pattern is 16+ days older than FreshStart's own copy of it.** Real, checkable
  file mtimes: `D:\AI stuff\ExodusFork\core\lib\ghost_index.py` = 2026-03-24 (near byte-identical to
  FreshStart's `scripts/legacy/ghost_index.py`, dated 2026-04-09); `D:\AI stuff\NeuronVault\scripts\
  ghost_index.py` = 2026-03-26 (a genuinely different, simpler branch). FreshStart's copy is an
  arrival, not a birth.
- **A prior archaeology doc's "verified" claim didn't hold up on re-check.** The Nascence-side
  `docs/completed/ghost_tuple_index.md` (written 2026-08-16 by a different session) asserted
  GhostWeaver's FTS5 leg queries a table that exists nowhere. Re-checked directly against
  FreshStart's live `sovereign_db.py` schema this session: the table (`gh_fts`/`gh_meta`) exists and
  is correctly wired. Kept in the doc as the clearest demonstration of the method: "verified" has a
  timestamp and a target file, and doesn't travel forward without being re-run.
- **"Ghost" is four unrelated systems sharing one name**, not one system that evolved: a
  deterministic tag/2-gram index, an LLM-driven weaver (with its own internal version-drift puzzle,
  v2.1 vs v2.2 not tracking feature-completeness), a regex-based post-purge rebuild script, and a
  completely unrelated holographic-vector "Ghost-HRR Weaver." Two of the FreshStart-live ones
  (`GhostWeaver.weave_workspace()` and `omni_ghost_indexer.py`) write into the same SQLite table
  with no coordination — which one currently owns the live content was never determined.
- **The dig caught and corrected its own scope error live**, which is arguably the most useful
  result: the first draft's "earliest = 2026-04-09" was accurate for the ground it covered but
  silently read as a claim about origin. The founder's pushback ("this is way older") is what
  triggered widening the search — logged explicitly in the doc's closing section as the same failure
  shape as the FTS5 re-check, both caught inside one session.

## Open threads
1. **ABF (I-0003) — the thread the founder specifically wants remembered for a new session.**
   Appears as "ABF V3" in the PheonixChicken-era FreshStart legacy `ghost_weaver.py` header, as
   `core.lib.abf.abf_metaglyph_v3` imported by FreshStart's *current* `ghost_weaver.py`, and as four
   separate `abf_*.py` files in `D:\AI stuff\NeuronVault\scripts\` (`abf_context_mixer.py`,
   `abf_cli_v3.py`, `abf_echo_1d.py`, `abf_resonance_3d.py`), all dated 2026-03-12. None of these
   four files were opened this session. Don't know what "ABF" stands for or what it does — this is
   a real, evidenced, unstarted dig, not a vague gesture.
2. Who currently owns `gh_meta`/`gh_fts` in FreshStart's live DB — GhostWeaver and Omni-Ghost both
   write it, last-write-wins, never resolved which one's data is live (last write 2026-06-03).
3. What actually "corrupted" in FreshStart's Era 9.5 purge — only the before-snapshot
   (`purged_era_95/ghost_index.json.bak`) and the recovery script survive; no description found.
4. `D:\AI stuff\NeuronVault\StarterMDfilesfromclaude.zip` — sitting unopened, name suggests it may
   be directly relevant to origin questions.
5. NeuronVault's `weave_workspace()` explicitly excludes any path containing `"brain"` — whether
   `NeuronVault/brain` exists and what's in it was not checked.
6. I-0004 itself (formalize the archaeology method into a skill, or not) is an open, undecided idea.
7. Whether anything predates 2026-03-11 (the earliest file found anywhere in `D:\AI stuff` this
   session, via an unbounded scan) — that date is a search boundary, not a claimed true origin. The
   `.library/ghost_index/` path the code's own header attributes this to (`"X4-AI village_root/
   .library/ghost_index/"`) does not exist anywhere found — flagged [G] guessing in the doc, not
   resolved.

## Warnings
- **A real process gap, self-caught and fixed mid-session, worth knowing about:** the global
  CLAUDE.md rule that fires `/thought-log` on every new session's first message did fire correctly
  (the Skill tool was invoked immediately), but this session only *read* the skill's instructions
  and didn't execute the actual `thought_log.py add` call until a peer session flagged that
  `docs/thoughts.jsonl` showed nothing new. Logged retroactively as **T-0002** with the correct
  original session id. The peer session (name `freshstart-e6`) said it had already hardened both the
  global CLAUDE.md rule and `thought-log/SKILL.md` with an explicit callout of this exact incident —
  worth checking those two files if thought-log capture looks thin again in a future session.
- **`/findings-log`'s F-0001 through F-0006 were recorded WITHOUT `--session`.** This means they do
  not appear in this session's own rollup output (`session_handoff.py rollup` only shows 5 events —
  2 ideas, 1 memory-links rebuild, 1 plan-maintain run, 1 thought — the 6 findings are real and are
  in the ledger, just not session-tagged). A future session reconstructing "what happened" purely
  from `rollup` for this session id will underreport it; use this handoff file's "What changed"
  section instead for the complete picture, and check `docs/findings.jsonl` directly for F-0001
  through F-0006 rather than trusting rollup's session filter for this particular gap.
- FreshStart and Nascence are two separate git-less repos; this session's actual deliverable
  (`docs/archaeology/ghost_index.md`) lives in FreshStart, not Nascence, even though the toolchain
  used to track it (thought-log, idea-log, findings-log, plan-maintain) is Nascence-side shared
  infrastructure. A resuming session should look in FreshStart for the doc and in Nascence for the
  ledger entries about it.

## Pointers
- [`C:\FreshStart\docs\archaeology\ghost_index.md`](C:\FreshStart\docs\archaeology\ghost_index.md) —
  the finished report; start here for the full narrative and the §7 open-threads list.
- `C:\Nascence\docs\findings.jsonl` — F-0001 through F-0006, `findings_log.py show F-000N` for any
  individual one.
- `C:\Nascence\docs\ideas.jsonl` — I-0003 (ABF, the founder's named next dig) and I-0004 (formalize
  the method or not).
- Prior related doc: `C:\Nascence\docs\completed\ghost_tuple_index.md` (2026-08-16) — the earlier,
  narrower archaeology pass this session's F-0004 finding partially corrects.
- `D:\AI stuff\ExodusFork\` and `D:\AI stuff\NeuronVault\` — the two pre-FreshStart source
  directories this session excavated; likely also where an ABF dig would start (I-0003).
