# Investigation Deepening — recaps as a progression ledger, place-cued (SIDE-QUEST, 2026-07-07)

> **Status: 🟡 SHADOW — unparked 2026-08-24, P0 built and shadow-verified.** *(Emoji added 2026-08-29,
> J-0406: "ACTIVE" alone had no parseable stage word for the plan-index tooling, which read this plan as
> ROADMAP's then-stale 🔵 DESIGNED by default — ROADMAP corrected same pass.)* Founder idea (Travis, 2026-07-07), arising from
> the memory-pyramid read-path discussion. Was PARKED behind emotion Phase 1 + identity estate P1, both of
> which shipped weeks ago; D-0009 (Travis, ruled 2026-08-23) unparked it as stale-parking-reason. P0
> (shadow, read-only) is now spawned as J-0177 — see "Current State — verified 2026-08-24" below.

```plan-state
stage: shadow
phase: P0 shadow-verified (F-0148); P1 (frontier-line + archive-fix) built 2026-09-28 (F-2163), restart-gated, not yet observed live
verified: 2026-10-30
evidence_read: 2026-10-16
next: J-2603 gated read of post-fix P2 rows (D-0324 gate 10+ since boot)
cluster: 7
```


## Current State — verified 2026-10-30

- **2026-10-30** (F-3329): J-2592 (D-0518): P2 episodic 0.0 was a cap-position bug, the 5 recency-guarantee fillers filled the 6-slot cap and cut every cue-scored episodic hit; fix logs relevance>0 hits past the cap as cue_tail and widens P2 pool only, P1 frontier_line unchanged, shadow, restart-gated
- **2026-10-30** (F-3265): J-2235: 0 of 5 post-boot P2 beachcombs gave a non-empty would-inject under J-2126, every episodic candidate relevance 0.0; D-0324 gate unreachable, J-1972 sample review blocked pending D-0518

- **2026-10-16** (F-2924): J-1972 P2 shadow read, run 10-09..10-16 (6.97 live days): 5 would-inject rows, all static journal_week/semantic picks (W33 world twice), 0 of Du episodic material (all episodic candidates relevance 0.0). Gate not met (5/10 rows, 7/14 days). Under the J-2126 rule (not yet booted) the same 5 rows yield an EMPTY pool: P2 would inject nothing, so the 10-row gate may be unreachable. D-0324 not reopened; J-1972 re-deferred; J-2235 reads the first 2-3 live days post-J-2126.
- **2026-10-15** (F-2782): J-1975 re-measure (F-2782): post-D-0308 shadow rows 6/6 fill 6th slot with a journal_week semantic hit (rel 0.55-0.68, age 44-1385h); P2 would-inject log 5/5 same, never None. D-0390 defeater clause 1 not met; B fix leaves pick unchanged. J-1972 review gated ~10-23.

- **2026-10-15** (F-2779): J-1937 read: archive exclusion verified 5/5 rows; frontier note picked static journal_week 3/3 with material, used 0/3 in the-day entries; build J-2126 spawned.
- **2026-10-08** (F-2618): J-2006 (D-0390 B): frontier pick now drops zero-score recency pool, prefers scored episodic, may be None; 103/104 replay rows -> None; branch jobrun/frontier_pick commit 558f452, merge before restart/P2 window.

- **2026-10-08** (F-2578): J-1938/F-2578: 104-row audit - frontier pick is place-blind (103/104 rows all-zero relevance via retrieve() recency guarantee); post-D-0308 the freed slot admits the single top semantic hit that always wins; D-0390 opened for rule change.
- **2026-10-08** (F-2576): J-1968 (F-2576): P2 built SHADOW-ONLY (data/investigation_deepening_p2_shadow.jsonl, same pick rule as P1, restart-gated, commit 7d82a9c) + J-1936 fail-open lines raised to WARNING; replay: 103 of 104 recorded beachcombs pick a zero-relevance candidate, so founder sample review job spawned for D-0324's live-flip defeater.

- **2026-10-07** (F-2559): J-1862 (F-2559): first live post-restart read of P1 via J-1648 log lines, nascence.log read in full 2026-10-04 20:40 to 2026-10-07 23:27. (a) archive exclusion fires on live data: one beachcomb (10-05 00:08) logged excluded 2 of 14 retrieved and its shadow row has zero archive-layer candidates. (b) the 10-06 01:16 day recap used the frontier note (gull/oystercatcher/tide/rain sentence has no source in the 12 deeds) -- F-2220 settled: no wiring gap. Caveat for P2: the note chosen was the static WEEK-W36 world paragraph (journal_week, the only nonzero-relevance candidate), written into the recap as a first-person deed; grounded by coincidence. n=1 recap, n=1 beachcomb. D-0324 reopened for travis; J-1936 (raise DEBUG fail-open lines to WARNING), J-1937 (re-read, not before 10-12), J-1938 (audit frontier_line picks over all 104 rows) spawned.
- **2026-10-02** (F-2238): J-1648 shipped the two observability log lines this plan's P1 needed (F-2238): observe_beachcomb() now logs the archive-exclusion count on every call, and journal._frontier_note() now logs found vs none-available vs a wiring exception (previously silent). Committed f87b700 on jobrun/investigation_deepening, sandbox-verified 6 of 6 checks; not yet observed against live Du data, since Du is offline the whole 2026-10-02 downtime window.

- **2026-10-02** (F-2220): F-2220: confirmed Du restarted 4x after the P1 merge (data/nascence.log); shadow log has zero new rows since before any restart (archive-fix still untested on live data) and frontier_line() finds real material for the one window it could (2026-09-29) but the written recap did not surface it (ambiguous: LLM discretion vs wiring gap, nothing in nascence.log distinguishes them). D-0324 reopened for travis; J-1648 spawned to add observability logging for the next read.
- **2026-09-28** (F-2188): P1 merged 2026-09-28 (4f53044) but Du has not restarted since; F-2188 verified zero real post-restart evidence yet, one post-merge shadow row and one post-merge recap both still show pre-fix behavior. J-1625 spawned to recheck, not before 2026-09-30.

- **2026-09-28** (F-2163): Built P1 (frontier_line in investigation_deepening_shadow.py, wired into journal.write_entry) and fixed the D-0308 archive-recurrence by excluding archive-layer candidates in observe_beachcomb; real-log simulation over the live 101-row shadow log shows the dominant archive fragment dropping from 60/101 rows (59.4%) to 0/101, repeat_candidate_hits 99 to 10, unique-fragment share 83.7% to 98.0%. Built in worktree commit 4f53044; restart-gated, not yet observed live.
- **2026-09-27** (F-2052): Graded the P0 founder-read gate against the full 98-row shadow log (F-2052): the candidate pool is genuinely wide (492/588 unique fragment ids, near-zero consecutive-visit overlap) but one archived chapter fragment recurs in 61 of 98 visits verbatim, a real partial instance of the named flat-recurrence failure. Opened D-0308 for the founder: does this evidence clear P1, and should the archive-recurrence be addressed first.

### What we have
P0 BUILT + WIRED, shadow-only, end-to-end verified (F-0148, 2026-08-24):
`core/investigation_deepening_shadow.py`'s `observe_beachcomb()` hooks `core/sensorium.py:_shore_act()`'s
beachcomb branch, logs raw retrieved fragments to `data/investigation_shadow.jsonl`, injects nothing.
Re-checked directly against the live file this pass: **98 real rows now accrued, 2026-08-25 → today**
(file mtime today) — no longer the near-empty log P0's own gate was waiting on.

### What we need
The founder-read gate P0's own spec names — are the retrieved candidates genuinely progressive
place-focused material, or the same handful of fragments every visit — is now genuinely checkable on
real data, and has not been done. P1/P2/P3 remain intentionally unbuilt pending that read.
Plan-ledger shows zero jobs or decisions on this plan since J-0177 (08-24).

### What we're doing next
Read the 98 accumulated rows in `data/investigation_shadow.jsonl` against the founder-read gate; if it
passes, P1 (add the frontier line to the daily recap) is next. No job is currently filed for either step.

> **History folded** — 2 dated Current State section(s) (2026-08-23 … 2026-08-24) moved to `docs/plan_history/investigation_deepening.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py investigation_deepening`.

## The idea
The journal recaps shouldn't be *summaries you retrieve* — they should be a **progression ledger**: a
record of *what he focused on* and *what still needs progressing*. When he returns to a place or subject,
hand him **where he was up to**, framed so the next look **deepens instead of restarts**.

Founder's example: at the rockpools he *"thinks about things he already has and tries to expound on them."*
He noticed the shells → then what was *in* the shells → then (later) that the beach shells differ from the
snail shells → then classification. Each visit adds a **rung**, not a repeat. *"The recaps hold what he
focused on and what needs progressing on."*

## Why this matters
It is the **anti-monoculture engine** in its most concrete form. The reason he says "shells" flatly every
visit is that nothing tells him *he already did shells — now look inside them.* A live "open thread, go
deeper" cue turns flat recurrence into cumulative inquiry — the exact failure the whole project fights, met
at the point of perception.

## The machinery finding (2026-07-07 — why this is NEW, not the chapter path)
Verified in `chapters.py` + `store.py`:
- Chapter deep-recall keys on TWO narrow mechanisms: (1) `chapter_id` step-out (`store.py:399` drops capped
  raw from ordinary recall — a COMPRESSION move that *closes* a period); (2) `recall_chapter()` — intentional
  recall by TITLE-WORD overlap with his current words.
- **Nothing is place- or activity-cued.** Recall fires on semantic similarity; chapters on title words.
  There is no "you are at the rockpools → here is your rockpool thread."
- So this is NOT the chapter machinery: chapters *close and compress a finished emotional period* (raw steps
  out); this keeps an OPEN inquiry LIVE and pushes it forward. Opposite intent.

## The three pieces (one gap each)
1. **Capture the frontier.** Recaps hold "what I did / saw" but not "what's unfinished / what to look at
   next." Add *the open edge* to the recap ("I keep meaning to see whether the beach shells differ from the
   snail shells").
2. **Place/activity-cued retrieval.** When location=shore + about-to-beachcomb, pull HIS shore-investigation
   thread — explicitly cued by where he is and what he's doing, not by semantic luck.
3. **Deepening framing.** Surface it as "you noticed X, then Y — the open thread is Z," so the next look
   builds a rung.

## Phased build (observe-first, when resumed)
- **P0 (shadow, read-side first):** at beachcomb / rockpool, retrieve his recent place-focused material and
  LOG what we *would* hand him (last rung + candidate open edge) → `data/investigation_shadow.jsonl`. Inject
  nothing. Founder-read: is the "go deeper" line coherent and genuinely progressive, or just the same shell
  re-surfaced?
- **P1:** add the frontier line to the daily recap (capture the open edge).
- **P2:** inject the surfaced thread into his beachcomb perception (deepening goes live).
- **P3:** an explicit rung-ladder per subject (shells → contents → comparison → classification) with
  deepening-vs-repetition detection (reuses the theme-recurrence restate-vs-develop machinery).

## Lineage / neighbours
Sits near: the journal pyramid (the recaps are its base), the curiosity/exploration organ (frontier / LP),
theme-recurrence (restate-vs-develop), active-imagination's return-and-develop. It is the READ-path of the
pyramid re-imagined as inquiry-progression rather than summary-retrieval.
