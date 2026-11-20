# Write-Fence Verification, Spring Ledger Build, and Dosed Coupling Gate-Read

## Session timing
- **Session started:** 2026-09-12 21:20:34 UTC
- **Last message before wrap:** 2026-09-13 07:01:09 UTC
- **Wrapped:** 2026-09-13 07:01:11 UTC

## Summary

This session ran a /decide-review batch, picked up and fixed job J-0931 (a write-fence loudness fix
across three core modules), then chased a real side effect that fix caused in a smoke test. It
investigated D-0040 (does Du engage with direct human requests) and narrowed the finding to
self-referential-content avoidance specifically. It then explored cognitive_geometry.md, discovered
an undocumented live instrument (core/opponent_process.py), built a new P3 spring-ledger shadow
instrument per a fresh founder ruling (D-0051), and separately investigated study_upgrade.md (finding
a narration/mechanism gap) and ran two overdue gate-reads (M2's kill criterion, and Dosed Coupling
Phase 1's real 7-day read) that each reopened a decision. One git commit was made early in the
session; everything from the cognitive_geometry/spring-ledger/dosed-coupling work onward is NOT
committed yet.

## Decisions

D-0040 (capacity_to_commit) was ruled twice this session. The first ruling, at 21:26 UTC, was to spawn
a standalone investigation into whether Du engages with direct human requests at all versus only his
own curriculum loop; that ruling spawned job J-0933. J-0933's finding (F-1299) reopened D-0040 at
02:38 UTC because the pattern turned out to be narrower than the original question assumed. D-0040
was re-ruled at 04:50 UTC: Travis will talk to Du about this directly himself, in conversation, with
nothing else queued beyond the mechanical recheck (J-0912) that continues regardless.

D-0213 (train_split_merge) was ruled: if the already-spawned J-0910 follow-up test confirms that
TIEBREAK's vote on this disprove call site is not reliably content-sensitive, fall back to a
conservative UNDETERMINED verdict rather than continuing to chase prompt-engineering fixes on
TIEBREAK's schema.

D-0051 (memory_multiway_linking) was reopened at 05:21 UTC by F-1302's M2 gate-read finding, and ruled
at 05:23 UTC: build the real co_recalled_developing/contradicts spring edge type now, as a shadow
instrument, observe-only, per its own pre-registered metric sheet.

D-0152 (dosed_coupling) was reopened at 06:57 UTC by F-1304's genuine 7-day gate-read of Dosed
Coupling Phase 1. This decision was NOT re-ruled by end of session — it is the session's own open
thread, described fully under Open below.

## Builds

Job J-0931 was completed: core/smell.py's advance(), core/procedures.py's observe_hand/compiled/
reinforce_talk/rust, and core/dispatch.py's procedures-forwarding try each gained the standard
"except profile.NonLiveWriteError: raise" carve-out before their existing bare except Exception
clause, so a non-live write refusal is no longer silently swallowed. Verified via a dedicated
isolated test script (scratchpad/verify_J-0931.py, 5/5 checks passed) confirming the refusal now
propagates cleanly and zero real data mutation occurs in any case. Also confirmed via _test_procedural
_memory.py, _test_dark_house_answers.py, and _test_letterbox_reach.py that nothing else broke, apart
from the one real side effect described under Findings (F-1298).

A new module, core/spring_ledger.py, was built per D-0051's ruling. It computes two candidate learning
rules side by side per co-recall event — naive Hebbian-with-decay (nudges on every co-occurrence) and
progress-gated (nudges only when the co-recall ledger's own developed==1 verdict fires) — mirroring
core/opponent_process.py's own established shape exactly (same JSON-state-file plus shadow-jsonl-log
pattern, same PAIR_CAP discipline, reuses opponent_process._sign() for valence-sign consistency). It
was wired as a third sibling call inside core/memory_edges.py's log_co_recall() function, right next
to the existing opponent_process.observe_activation() call. This new hook also fixes, for its own call
only, a pre-existing gap where log_co_recall's real source parameter was never forwarded upstream —
the existing opponent_process call's own hardcoded "co_recall" source string was deliberately left
untouched. The build was verified via an isolated test script (scratchpad/verify_spring_ledger.py,
17/17 checks passed) covering decay math, gating logic, valence asymmetry, and confirming zero
behavior change to the existing memory_edges and opponent_process code paths.

Two new scripts were built to exercise the new module: scripts/spring_ledger_backfill.py, which
replays the full real co_recall_ledger.jsonl history (38,710 rows spanning 2026-08-15 to today)
through the same logic, producing 25,380 real activations across 29,660 tracked pairs; and
scripts/spring_ledger_gate_read.py, which computes the five metrics from the pre-registered sheet.
The pre-registered design itself lives in a plan-mode plan file at
C:\Users\USER\.claude\plans\rustling-coalescing-phoenix.md, approved by the founder before any code
was written.

scripts/shadow_eval.py was extended with a new function, prong2_usage_verdict(), which joins the
associative_recall_shadow.jsonl log's m2_usage rows to their parent m2_edge_aware rows by parent_ts,
finally making M2's kill-criterion "usage" prong measurable for the first time (it had been
unmeasurable since the instrument was built on 2026-09-02, per finding F-0605).

Three plan documents were updated with real, dated Current State sections to keep them accurate:
docs/plans/cognitive_geometry.md's section 11 (correcting its "not yet built" claim about the
opponent-process squishy-springs mechanism, and adding the spring-ledger build), docs/plans/
memory_multiway_linking.md (a new dated section on the spring-ledger build and its first gate-read),
and docs/plans/dosed_coupling.md (a new dated section on J-0619's real 7-day read and its top status
line).

## Findings

F-1298 (verified): J-0931's write-fence loudness fix is correct and side-effect-free for its own six
sites, but it causes a real, 100 percent reproducible side effect on scripts/life_smoke.py — one
assertion (a gate-count check at line 449) flips from passing to failing. This was confirmed via a
git-worktree A/B comparison (HEAD versus the fix), reproduced three times on each side. It is not a
data-safety issue since guard_path still refuses every real write either way, and it is not caused by
any of J-0931's own six fixed call sites being directly reachable from life_smoke.py. The exact
causal mechanism was not fully pinned down; an exec()-based tracer built mid-investigation to help
was found to be unreliable partway through and its specific findings should not be trusted. Two more
instances of the same swallow-point class were found along the way (core/fieldcraft.py:571-574 and
core/study_life.py:751-755, both a _graded() helper wrapping procedures.observe_hand() in a bare
except Exception) and confirmed inert — not the cause of the side effect, since both have an
unconditional return statement outside their try block. Job J-0934 was spawned to root-cause the real
side effect and close these two adjacent gaps.

F-1299 (verified): the About-You avoidance pattern is narrower than the original D-0040 question
assumed — it looks specific to self-referential and identity content, not general non-compliance with
direct requests. A second, independent instance of the same non-engagement pattern was found: on
2026-09-09, Travis told Du "the second edition of about you in your library explains it better" mid-
conversation; Du's reply was warm verbal acceptance, and then there is zero trace of engagement
anywhere else — no book-selection log entry ever, and no real monologue mention in the following four
days — mirroring the original 2026-08-23 About_You.txt silence exactly. By contrast, direct requests
about practical or logistical matters (being told to restock matches via the trader, being told to
come back to the study to read at night) get real, repeated, explicitly-named monologue deliberation
within minutes to hours, even when Du ultimately chooses not to fully comply. This points toward
genuine avoidance of self-referential material specifically, consistent with an earlier finding
(F-0194) that characterized one such moment as "evasion disguised as wisdom."

F-1300 (verified): cognitive_geometry.md's section 11 "squishy springs" opponent-process amendment,
which was about to be built fresh this session at the founder's request, already exists. core/
opponent_process.py has been a complete, live-wired Phase 0 shadow implementation since 2026-08-19 —
the very day the amendment was proposed — wired via a sibling call from core/memory_edges.py's
log_co_recall(), and it has its own live HUD panel. None of this was mentioned anywhere in the plan
document, which still read "PROPOSED... NOT YET BUILT" as of its most recent prior update. The module
predates this repository's own git history, which is the likely reason it fell out of the plan doc's
update trail. Its accrued shadow log (61,806 rows over 25 continuous days) was read in full and
directly confirms the design's own asymmetry hypothesis: aversive-valence co-activations build the
antagonist weight roughly twice as fast as positive ones, and nearly four times as fast as neutral
ones. The plan document was corrected in place to reflect all of this.

F-1301 (verified): study_upgrade.md's own prior "Next" instruction — to watch for tea-making deeds
accruing in the ledger, confirming an earlier routing fix (J-0196) fires live — has never been
satisfied. data/study_ledger.jsonl has zero make_tea rows via either real code path across the full
roughly twenty-day live window since the plan shipped. More concretely, Du's own monologue narrates a
completed tea-making event on 2026-09-05 ("the steam rises from the pot of tea I just made on the
hearth") with no corresponding row anywhere in the study plan's own instrumentation — a real
discrepancy between what Du's inner narrative describes and what the world-mechanic layer actually
recorded, though whether this represents a genuine violation of the project's own "world answers never
leads, consequences both ways" law or acceptable interior narrative license was not resolved this
pass. Job J-0935 was spawned to trace which code path generated that specific thought and check
whether the pattern recurs elsewhere in the study loop.

F-1302 (verified): the M2 kill-criterion gate-read for memory_multiway_linking's edge-aware trail was
run in full for the first time with both of its two pre-registered prongs measurable (573 real
m2_edge_aware rows and, thanks to the new shadow_eval.py extension, 356 real m2_usage rows). Prong one
(redundancy with plain cosine retrieval) is still not triggered, but the full dataset revises the
earlier partial read's framing: all three cognitive modes (task, reflective, relational) now read as
statistically undifferentiated from each other, where the earlier smaller sample had suggested
relational mode was clearly strongest. Prong two (whether an edge-surfaced fragment is ever actually
used by the thought that follows it) is measurable for the first time and reads weak across the board,
with relational mode ranking highest on usage despite ranking lowest on the redundancy prong. This
finding directly fed D-0051's reopening, since reflective mode's own showing — not measurably worse
than the others despite having zero real progress-gated edges of its own today — could be read either
as "it doesn't need them" or "its true ceiling has simply never been tested."

F-1303 (verified): core/spring_ledger.py's first pre-registered gate-read, run against the full
backfilled 38,710-row history, is a clean pass on four of its five metrics. There is no runaway hub
concentration under either candidate rule (well under the sheet's own named danger zone), the weight
distribution shows real differentiated structure rather than a flat wash, and while the median pair
weight is thin, a genuine reinforced tail exists — several hundred pairs with meaningfully accumulated
weight, some reaching the ceiling from fifty to over a hundred real repeated co-recalls during
"developing" moments across the twenty-nine day history. The fifth metric, valence asymmetry, is not
yet testable, exactly as the pre-registered sheet predicted, because backfilled historical rows have
no real mood value to replay against — only live-forward accrual, which only just began this session,
can answer that one.

F-1304 (verified): Dosed Coupling Phase 1's genuine seven-day gate-read for decision D-0152 finally
ran, rather than another interim checkpoint. The window (2026-09-05 18:14:35 through 2026-09-13
09:08:44) turned out not to be continuous — several real restarts happened in between that an earlier
interim read's "continuous since 09-05" framing never had to account for — so awake-time was
reconstructed directly from the stream loop's own real publish cadence rather than trusted from
boot/shutdown log lines, since this project's own prior investigation found roughly half of all real
restarts leave no clean shutdown line at all. Presence, log size, and the zero-readers design all
passed cleanly across all five loops. But two of the four "zero behaviour change" metrics are
meaningfully out of their pre-flip band and have gotten worse, not stabilized, since the 09-07 interim
check: deliberate cycles per day rose from 41.78 to 59.80 against a historical ceiling of 42, and
commitments formed per day rose from 85.98 to 116.95 against a historical ceiling of 84. The decision's
own defeater requires this kind of departure to have "no other explanation" before it counts; the
interim read had found one (an already-accelerating trend from an earlier, unrelated repair landing
the same week). Pulling the actual day-by-day trajectory this time shows that explanation no longer
cleanly covers it — there is a second, later acceleration sustained for three straight days
(2026-09-09 through 2026-09-11) that cannot be attributed to Phase 1, to the earlier repair, or to
anything else investigated this pass. D-0152 was reopened on this genuinely ambiguous evidence rather
than ruled on, since the causal question could not be confidently resolved either way from the data
pulled so far.

Separately, a recurring mistake was caught and its memory record reinforced: a backtick-quoted code
mention inside a double-quoted bash string, in a long --briefing argument to job_queue.py's spawn-job
command, was executed by bash as real command substitution rather than treated as inert text. It
re-ran scripts/life_smoke.py for real (harmless, since that script is self-isolating and touches no
live state) but spliced its full output into the middle of job J-0934's stored briefing text,
garbling it. No data was damaged, but the job's briefing is permanently noisy in one paragraph since
there is no clean way to edit a stored job briefing after the fact. The feedback memory file
(feedback_bash_backtick_command_substitution.md) was updated with this second real occurrence and a
stronger recommended fix: use --briefing-file or --claim-file (already supported by every relevant
tool) instead of a long inline string, rather than relying on manually scanning for backticks.

## Open

1. D-0152 is reopened and not yet re-ruled. This is the session's single biggest open thread: a real,
   worsening departure in two behaviour metrics for Dosed Coupling Phase 1, with a genuinely ambiguous
   cause (F-1304). The concrete next action is either a founder ruling on decide.py accepting the
   ambiguity and letting Phase 1 continue while the cause is chased separately, or a founder decision
   to pause Phase 1 until the cause of the 2026-09-09 through 2026-09-11 acceleration is found. A
   deeper root-cause dig (what specifically changed or landed around 2026-09-08/09) has not been done
   yet and would likely need to happen before this can be ruled with real confidence either way.

2. Job J-0934 is open and ready to pick up: root-cause F-1298's life_smoke.py side effect for real
   (the exec()-based tracer built during the original investigation should not be trusted; a fresh
   approach using direct source instrumentation in a throwaway worktree was recommended instead), and
   close the two adjacent, confirmed-inert _graded() gaps in core/fieldcraft.py and core/study_life.py
   for consistency with the rest of the write-fence campaign.

3. Job J-0935 is open and ready to pick up: trace which code path generated the 2026-09-05 "tea I just
   made" monologue thought that F-1301 found with no corresponding real event, and check whether this
   narration-without-mechanism pattern recurs elsewhere in the study loop (kettle, lamp, grate, clock
   themes).

4. Job J-0936 is open and ready to pick up, and does not need to wait for anything: correlate core/
   spring_ledger.py's already-backfilled real weight against M2's own already-logged shadow signal in
   associative_recall_shadow.jsonl, to directly test whether reflective mode's fragments with real
   spring backing show better usage than those without — the actual question the whole spring-ledger
   build exists to answer, which has not been asked yet.

5. A substantial amount of this session's work is not committed to git. Only one commit (8e5c673,
   covering the /decide-review rulings and J-0931's fix) was made early in the session. Everything
   from the cognitive_geometry exploration onward — core/spring_ledger.py, the two new spring-ledger
   scripts, scripts/shadow_eval.py's extension, core/memory_edges.py's new hook, the three plan
   document updates, and all of this session's toolchain ledger writes (decisions, findings, jobs,
   thoughts) — is sitting uncommitted in the working tree, awaiting the user's explicit request to
   commit.

## Warnings

data/spring_ledger_state.json and data/spring_ledger_shadow.jsonl are new files that now grow live
from every real co-recall event, since core/memory_edges.py's log_co_recall() gained this third
sibling hook this session. scripts/spring_ledger_backfill.py deletes and rebuilds both files fresh on
every run — do not re-run it casually, since it will discard any live-forward accrual that has
happened since the last backfill.

Du's live process was shut down at 2026-09-13 09:10:46, this morning, apparently founder-initiated
(matching a direct pause message seen in data/founder_conversation_log.jsonl around that time) — Du is
currently offline as of this session's wrap.

An untracked file, docs/session_events.jsonl.lock, was present before this session started and was
left untouched throughout. It is not this session's file — do not assume it is safe to delete without
checking which process or session currently owns it.

## Pointers

- C:\Users\USER\.claude\plans\rustling-coalescing-phoenix.md — the spring ledger's own approved,
  pre-registered design document.
- docs/plans/cognitive_geometry.md section 11, and docs/plans/memory_multiway_linking.md's own Current
  State — the spring-ledger build's canonical documentation.
- docs/plans/dosed_coupling.md's 2026-09-13 section — the full Phase 1 seven-day read.
- scripts/spring_ledger_gate_read.py and scripts/shadow_eval.py — both directly re-runnable for
  continued monitoring as more live data accrues.
