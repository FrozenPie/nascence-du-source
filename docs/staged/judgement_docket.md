# The Docket — one silent queue for every judgement call (staged 2026-11-18, J-4349)

> **Status: STAGED, design only. Nothing built.** Plan A of two (I-0153 / I-0154 split by founder ruling 2026-11-14).
> Sibling: [[judgement_visitor]]. Not merged with Lane 2 ([[lane2_the_witness]]); see "Lane 2 boundary".

```plan-state
stage: staged
phase: design + measurement (Phase 0)
verified: 2026-11-18
gate: founder rules the docket questions (decide entries) before any code
next: Phase 0 read-only census (which per-thought calls must answer before his next thought)
cluster: judges
```

## What it is
Silent and invisible to Du. Every judgement call the code makes is written to ONE queue with its inputs (a docket
row), instead of each being a synchronous LLM call. Rulings happen later, in batches, by a cascade: a small model
first; a large CPU model (slow is fine) for rows the small one cannot settle. Du never sees a docket row or a
verdict (D-0434: no readout; a verdict he can see is a verdict he can write for). Aim: fewer calls on the 1080 Ti hot lane.

## Measurement (read-only; registry `calls_7d` only, no LLM calls, no log scans yet)
- `docs/prompt_registry.jsonl`: 132 rows, calls_7d recorded on 60, sum 13,010. The registry has NO per-row count for
  the judge panel / `judges_lanes` hubs; the 2026-10-31 inventory puts the panel at about 2,400 raw calls a day on
  the CPU hubs, invisible to the latency log. A count source for those is Phase 0 work.
- The four per-thought satellites (current registry): P-0035 deliberation pass 3 = 1,991 (LIVE, replaces the idle
  thought); P-0036 self-implication scan = 1,366 (WRITE-ONLY); P-0038 commitment scan = 1,134 (LIVE side effects);
  P-0039 condensed twin = 737 (SHADOW). Sum 5,228 = 40.2% of 13,010. The 2026-10-31 figure was 49.6% of 12,457;
  the difference comes from the registry summing only rows with counts and P-0034 (421) now being RETIRED. Both
  are approximate; not a verified trend.
- Classification by "must answer before his next thought":
  - MUST answer first: P-0035 (its output is the thought). Cannot enter the docket.
  - COULD wait: P-0036 (write-only; nothing reads it), P-0039 (shadow log), P-0040 stability loop (144), P-0045
    re-entry phase 2 (105). Docket candidates, about 2,350 calls a week, no behaviour change.
  - MIXED, needs a read of the code: P-0038 commitment scan. Shadow by charter but with live side effects (a stand
    taken or dissolved); whether the next thought reads the stand before the scan finishes is unmeasured.
- Honest limit: those deferrable rows are already shadow-only, so docketing saves hot-lane compute, not judgement
  quality, and only if the batch runs on a different lane (CPU hubs) than the hot one.

## Design sketch
1. Docket row: id, call site (registry P-id), inputs verbatim, timestamp, urgency class (blocking / deferrable).
2. Blocking calls stay synchronous. Only deferrable classes enter the docket.
3. Cascade: small model pass; rows below a confidence floor, or flagged hard, go to the large CPU model.
4. Result written to the existing consumer's store with a ruled_at stamp so a reader sees staleness.
5. The sealed-ruling experiment (below) checks that batching does not change rulings.

## Sealed-ruling experiment (write-up)
Question: does talking to a visitor change what a judge would have ruled, or only how it is justified?
1. Blind ruling: a judge rules on a labelled sample of docket rows with no conversation. Seal it (hash + timestamp).
2. Talk: the visitor ([[judgement_visitor]]) discusses the same items with Du.
3. Third blind judge: a different model family, given the row only, rules again with no sight of either earlier result.
4. Compare sealed vs third judge (baseline drift between blind judges) vs the post-talk ruling. If the post-talk
   ruling moves away from both blind judges by more than they differ from each other, the conversation is leaking in.
Needs: labelled sample (suggest 60 rows, stratified by call site), a pre-registered threshold, no LLM calls until the
founder rules. Du's explanation must never reach the third judge.

## Lane 2 boundary
Lane 2 (the Witness) perceives current reality, shadow-only, LANE2_LIVE False. The docket is a call queue. Shared
idea only: a slow CPU model. No shared store, no shared constitution. Merge is a founder question, default no.

## Phase 0 (no LLM calls)
Count judge-panel calls from logs per call site; read the consumers of P-0038 to see if the next thought reads its
output; produce a table. Exit: a list of rows safe to defer.

## Open founder questions
Opened as decide entries (not ruled); ids are in the J-4349 job note.

## Phase 0 result (2026-11-18, J-4404, F-5115)
D-0859 ruled (approve experiment; count from logs; separate from Lane 2). `scripts/docket_phase0_census.py` counts `data/judge_panel_log.jsonl` rulings: about 11,300/week over the last four weeks (11,870 in the week of 11-12). Defeater (under 1,000 deferrable/week) not triggered even counting only shadow-only families (lane2 + follow_line, about 2,800/week). `evidence|bears` (about 6,900/week) is unclassified blocking vs deferrable; P-0038 consumer read still open.
