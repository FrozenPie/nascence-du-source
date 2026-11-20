---
name: feedback-decide-review-scope
description: "When asked to \"start the decide-review pass,\" extend beyond decide.py's own open list to every unfiled founder question a portfolio audit surfaced — don't limit to pre-existing /decide entries"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4595f5ad-65f2-480a-8d83-32786682d18c
  modified: 2026-09-27T23:24:54.806Z
---

When the founder says "start the decide-review pass" (or similar) after a broad plan-portfolio audit
has already identified plans with real, unfiled founder-level questions (a question named in a plan
doc's own prose — an "Open founder decisions" section, a "What we need" bullet — with no formal
`/decide open` ever run against it), don't limit the pass to `decide.py list --open`'s existing
entries. Open real `/decide` entries for the audit-identified plans too (grounded in the plan doc's
own quoted question text and evidence), then present ALL of them through the skill's normal batched
`AskUserQuestion` + immediate-log-with-`--by travis` pattern.

**Why:** 2026-08-29 — a [[project-plan-portfolio-audit]] found 22 of 72 plans blocked purely on
"nobody has had one conversation with the founder yet," but `decide.py list --open` only tracked 3
of those as formal entries. Confirmed by the founder proceeding through 16 total decisions (3
pre-existing + 13 newly opened from audit findings) in one sitting without pushback on the expanded
scope — this was the actual ask, not scope creep.

**How to apply:** After any `/plan-index`-family audit that surfaces founder-question plans with no
`/decide` entry, treat "run decide-review" as license to `decide.py open --plan <slug> --question
"<quoted from the doc>" --source "portfolio-audit:<date>"` for each one before presenting — not just
to work the pre-existing queue. Still follow every other skill rule unchanged: batch <=4 per
`AskUserQuestion` call, log each ruling immediately (never batch to the end), resync `plan-index`
after each batch, spawn a follow-up job whenever a ruling unlocks real work.

A secondary, lower-confidence signal from the same session: across 16 rulings, the founder picked
the option marked "(Recommended)" 12 times, picked a middle/alternate option 3 times, and asked for
a stronger version once ("un-park now, proceed in parallel" instead of the more cautious "wait for
M2" framing I'd expected him to prefer given D-0055's own tie-in). Read as: well-evidenced
recommendations grounded in real numbers (CIs, row counts, audit findings) are usually followed, but
don't assume agreement — write honest, non-leading option descriptions for the alternatives too, and
expect the founder to sometimes want the bolder option once the evidence is solid.

**Update 2026-09-22 (the same pattern, again):** a `/decide-review` over 1 formal decision plus 7 founder-shaped
`needs_input` jobs (the queue's `needs_input` list IS the unfiled-founder-question set now; open a `/decide` entry
for each at logging time, one at a time, verify the ID with `show` before ruling) — he picked my "(Recommended)"
option on 7 of 8. The one he didn't (D-0217, cat cries): I recommended tuning the symptom (episode-onset dosing);
he chose the ROOT-CAUSE world fix (empty larder) instead. Read: when evidence shows a cue is announcing something
the world gives him no way to act on, he'd rather fix the world than dose the cue. Also: a "Not yet" answer is a
real ruling only with a defeater naming the revisit read (I used the pending post-restart read job); and when a
question's numbers are stale (J-1150's outage count), re-measure from the live log before asking — the Ramses
Judge1 outages had gone from 2 to 3 since the job was written.

**Update 2026-09-28 (largest batch yet — all 25 open decisions in one sitting, 7 batches of ≤4):**
followed my "(Recommended)" option 21 of 25 times. Of the 4 he overrode, 3 were "go bigger, not smaller":
D-0298 (swap the tiebreak model outright, not my cheaper hardcode-to-unsettled), D-0312 (curiosity's new
memory call defaults descend=ON, not my cautious off-by-default matching sibling systems), D-0319 (build
the sub-place-standpoint move for all four places at once, not my shore-first pilot). Same shape as
D-0217's root-cause-over-symptom pick above — when I hedge toward the cheaper/narrower option and the
evidence is solid, expect him to take the fuller build instead. The 4th override (D-0305, golden_spiral_recall)
went the OTHER way: I synthesized a specific 3-part answer (elevation=evidence, ray=signature, no cull) from
the job's own recommendation text, he chose "needs more design work first" instead — read: when a question
offers a synthesized answer across genuinely distinct architectural readings rather than a clear best-evidenced
pick, don't over-trust a job's own "recommendation" framing as settling it; he may still want to defer.

**New process lesson, same session (D-0273):** in a heavily-concurrent multi-session project, a decision sitting
in `decide.py list --open` can have already been answered by OTHER work between when it was opened and when you
get to it in the batch — here, a concurrent session's job (J-1494) had run the exact read-only reconciliation
D-0273 asked about, the day before, with a real number, but the decision itself was never closed. Ruling it
anyway (I did, since the founder's own answer was still the right call to make) is fine, but check
`findings_log.py`/`job_queue.py` for anything referencing the decision's own plan slug BEFORE presenting a
decision that's phrased as an open question about current state — if the state has already changed, say so in
the option text (or record a separate finding after ruling, as I did here) rather than letting the founder
answer a question whose premise already moved. Also confirmed again: [[feedback_file_findings_as_jobs]]'s
"spawn a follow-up job whenever a ruling unlocks real work" scaled fine to volume — 12 jobs spawned in one
sweep after the 25 rulings, cross-checked against `job_queue.jsonl` first so none duplicated already-queued work.
