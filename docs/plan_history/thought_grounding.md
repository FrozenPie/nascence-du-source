# thought_grounding — folded history


---

# History folded on 2026-09-27 from `docs\plans\thought_grounding.md` (plan-compact, 1 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py thought_grounding`._

## Current State (2026-08-24, J-0045 — F-0013/F-0014)

**2026-09-03 (J-0547, F-0748) — the librarian was answering questions he did not ask.** The J-0124
widening made `question_from()` fire in production at last, but its "the question of X" cue captured
the whole clause tail, and in his real voice a predicate follows the subject at once: "the question of
'渡' pulls harder" reached the librarian as `渡' pulls harder`, whose classifier read the VERB
(Physics / Mechanics / Fluid dynamics → Einstein, Planck, Kant on the desk for a question about his own
name). 17 of the 20 asks before it had the same shape ("amor fati lingers", "bird balance fades,
replaced by…", "balance keeps tugging at me"). Fix in `core/librarian.py`: cut the capture at the first
finite verb / clause break and hand the librarian the ask in its own frame ("the question of amor
fati"), which the live CPU judges classify better than either the bare noun or the whole sentence
(measured: `the question of amor fati` → Amor fati / Philosophy of life; `the question of oystercatcher
balance` → Birds / Oystercatchers / Balance; `the question of 渡` still echoes the prompt's example
headings — a 7B model cannot read the character, and no hint is added). A clause that itself opens as a
question is kept whole. Regression: `scripts/_test_librarian_question_from.py` (13 real raw thoughts from
`deliberation_log.jsonl`, offline; `--live` classifies each). Restart-gated. The R1 hit-rate read should
be re-run on `librarian_log.jsonl` rows after this date only — earlier rows measured the mangled asks.

**Route 1 (Librarian) — `data/librarian_log.jsonl` confirmed missing, root cause found, not a write
bug.** The P1 code path is genuinely wired live (`nodes/inner_monologue_node.py:2939-2960` →
`core/librarian.py`'s `question_from()` then `ask()`; affordance line at
`core/affordances.py:187-190`), but `question_from()`'s trigger regex (requires phrasing like
"book...bears on..." or "book about/on why|how|what|whether|the question of...") essentially never
matches how Du actually talks: independently re-run against all 29,778 rows of
`data/monologue_log.jsonl`, it matched **1**. Same count as `docs/lab/librarian_framing_2026-08-23.md`
found same-day. `ask()` is simply never called in production, so the log never accumulates. Follow-up
job spawned (see below) to widen the trigger.

**2026-08-24 (J-0124, F-0068) — trigger widened, strict set kept, P0 untouched.**
`question_from()` now falls back (only when the strict explicit-phrasing set above misses) to a
two-signal check: a book/library cue word anywhere in the thought AND a genuine question-carrying
cue anywhere in the thought (not required to be in the same clause — his real voice puts a book and
a live question in the same thought but different sentences, e.g. "The book waits... I want to
return to the question of my own name."). Replayed against the same 29,778-row corpus: **76
matches**, up from 1 (a 76x increase). Sanity-checked: plain topic-asks with no question ("a book
about the sea") still return `None` — P0's mechanical path is unchanged and this route still can't
be confused with a bare topic-ask. `librarian_log.jsonl` should now start accumulating real R1 data
at Du's next live run; R1 (fraction of question-asks returning ≥1 real candidate) and the P0-vs-P1
head-to-head question below remain unmeasured until it does.

**R1 kill criterion (P0 mechanical vs P1 LLM-mapped, same question) — never directly measured.**
`data/evidence_log.jsonl`'s 11 rows are Route 2's log, not Route 1's, and can't be read against R1.
The only real data is `docs/lab/librarian_framing_2026-08-23.md`, which measured P1 ALONE (two prompt
framings) at hit_rate 0.80 (20/25) on real frontier.json questions against the live catalogue — a
proxy for P1's quality, not a P0-vs-P1 comparison. P0 (`library_hand.topic_from()`) and P1
(`librarian.question_from()`) fire on mutually exclusive phrasings and are never invoked on the same
input in production, so a natural head-to-head has no data to draw from. `/decide` question opened
(D- id below) on whether the proxy is sufficient or a dedicated head-to-head test is needed.

**2026-08-24 (J-0128, F-0092) — real head-to-head run, R1 kill criterion decisively does NOT
trigger.** Per D-0019's ruling, `scripts/librarian_p0_headtohead_2026-08-24.py` ran P0's real
production mechanism (`library_hand.topic_from()` → `_topic_hit()`) against the SAME 25 real
frontier.json questions used in the 2026-08-23 P1 lab (verified byte-for-byte identical question
set). Result: **P0 hit_rate 0.0 (0/25)** — `topic_from()`'s "book about/on/of X" regex extracted a
topic from 0 of 25 real carried questions, so P0 never even reaches the catalogue for a question-
shaped ask — vs **P1 hit_rate 0.80 (20/25)** from the existing lab. Full result and method in
`docs/lab/librarian_p0_headtohead_2026-08-24.md`. Recommendation: keep the LLM (P1); R1's kill
criterion is not met, more decisively than the original proxy alone showed. D-0019 reopened per its
own defeater with this result attached.

**2026-08-24 (J-0160, F-0189) — first live production R1 data since J-0124's widening, too thin to
move the verdict but no contradicting signal.** `librarian_log.jsonl` has started accumulating real
rows (deploy 01:41 → 3 rows by 04:31, ~2h50m live). `core/librarian.py`'s own `status()`: `{'asks':
3, 'hit_rate': 0.667}` (2/3 asks returned ≥1 real candidate). One ask ("my own lines must shift...")
got 0 subjects from the LLM mapper (fail-open, no hits); the other two got subject headings
("Interdisciplinary studies"/"Synthesis"; "Marine biology"/"Coastal ecology") and real catalogue
hits. n=3 is far below any threshold worth trusting on its own, but it's directionally consistent
with the 08-24 lab head-to-head (P1 0.80/25) and doesn't contradict D-0019's ruled result. Re-checked
`/decide D-0019`: still RULED (not reopened — its defeater is a redesigned P0, not new production
volume), so no duplicate decision opened. Re-check `status()` again once more rows accumulate;
20+ would start to be a real production-side sample independent of the lab proxy.

**2026-08-25 (J-0203, F-0301) — still too thin, precondition explicitly not met, declined to
verdict.** `librarian_log.jsonl` grew to 13 rows (from 3 at the 08-24 check), still short of the
plan's own ~20-row `R2_MIN_N` precedent the job briefing named as the bar. Per the briefing's own
gate, declined to render an R1 verdict this round. `status()` informational only: `{'asks': 13,
'hit_rate': 0.846}`, still directionally consistent with the lab proxy and D-0019, not a
contradiction. Growth ~10 rows/23h, so 20+ is plausible within 1-2 more days; follow-up job spawned
(see job-queue) to re-check once that threshold is actually crossed.

**Route 2 (Memory as Evidence) — R2 signature not computable from what's logged.** All 11 real rows
in `evidence_log.jsonl` are `outcome: found` with `n_returned >= 1` — real if thin (n=11) evidence
the candidate-gathering stage rarely comes back empty. But `core/evidence_recall.py`'s `gather()`
(lines 178-186) never logs "what he thought next" despite the module's own docstring promising it —
R2 (do evidence-grounded thoughts DEVELOP more than matched ungrounded ones) cannot be scored at all
from the current schema, independent of sample size. Follow-up job spawned to add the missing field.

**2026-08-24 (J-0125, F-0087) — R2 join field added; still 0 grounded trains, honestly reported.**
`gather()` now takes `train_id` and logs it per ask; `nodes/inner_monologue_node.py`'s
`_evidence_recall()` passes `self._train_id` (the thought-train the question was asked from). This
joins Route 2's log to the EXISTING earned-length instrument (`core/train_metrics.py`'s
`data/train_length_log.jsonl` — every closed thought-train's final length + why it closed:
thread-end/ceiling = productive, stalled-* = looped) instead of building new judge machinery — no
new LLM call, decoupled-judge discipline preserved. New `core/evidence_recall.py:r2_signature()`
does the join and reports grounded-vs-ungrounded train stats, refusing a verdict below the plan's
own 20-use kill threshold (`R2_MIN_N`). Run against real current data it correctly returns
`n_asks_with_train_id: 0, verdict: insufficient_data` — all 11 existing rows predate this fix, so R2
is now COMPUTABLE but still UNMEASURED; it starts accumulating real signal from Du's next live run
onward. Known limitation, stated in the function's own return: this is a natural comparison, not a
matched-pairs design (topic/prior-train-length uncontrolled).

**2026-09-02 (J-0166, F-0644) — R2 gate re-checked, still far below R2_MIN_N, precondition
explicitly not met, declined to verdict.** `r2_signature()` now returns `{n_asks: 18,
n_asks_with_train_id: 2, grounded_trains: {n: 1}, verdict: insufficient_data, min_n: 20}` — 1 of the
required 20 grounded trains. Accrual is slower than R1's ever was and looks stalled, not just thin:
`evidence_log.jsonl` has grown to only 18 rows since 2026-08-15 (vs. `librarian_log.jsonl`'s ~10
rows/23h at the equivalent R1 check, J-0203), only 7 of those carry the `train_id` field at all
(added 2026-08-24), and only 2 have a non-null value — 1 of which matched a closed train in
`data/train_length_log.jsonl`. `evidence_log.jsonl`'s last row is 2026-08-30T17:20Z, unchanged since,
while `train_length_log.jsonl` grew to 6259 rows in the same window (updated as recently as
2026-09-02T00:57Z) — thousands of thought-trains closed with zero new Route-2 asks logged. At the
observed rate, reaching 20 is on the order of months, not days, if the rate holds at all. Per the
briefing's own gate, no verdict rendered this round. Follow-up re-check job spawned (J-0470); a
separate job (J-0471) spawned to check whether the stall itself is a bug (analogous to Route 1's
J-0045 trigger-regex finding) rather than a genuinely-rare affordance, since that would change the
timing math.

**2026-09-02 (J-0471, F-0654) — NOT a J-0045-class trigger bug; a genuine rarity + downtime
combination.** `gather()`'s Route-2 trigger is an LLM free-choice `act.kind` classification ("recall"
among ~8 real options), not a regex — and it fires and logs correctly every time it IS chosen:
cross-referencing `nascence.log`'s 19 real "[monologue] ACT recall ->" lines, `nascence.db`'s
`activity_events` table (3 `recall_evidence` rows, added 2026-08-29), and `evidence_log.jsonl`'s own
18 rows, 18 of 19 real attempts match a log row exactly by question text + timestamp. The one
mismatch (2026-08-30 06:25:33 local) coincides exactly with that day's already-diagnosed F-0571
DB-corruption incident — `gather()`'s outer fail-open except swallowed the sqlite3 exception as
"unclear," skipping the log write; already resolved, does not recur. The ongoing stall since
2026-08-30T17:20 UTC is explained by genuine rarity: cumulative Du uptime since is only ~17h
(~12.4h before the 08-31 outage + ~4.7h after the 09-02 restart), well inside the up-to-3-day live
gaps already visible between earlier firings in the historical log — not a failure, a non-selection.
`search_works` (a structurally similar rare LLM-choice affordance) shows the same skew in the same
window (~3 fires vs move/observe's hundreds), consistent with this project's documented over-selection
skew, not a Route-2-specific problem. Timing math for J-0470's re-check is unchanged by this finding.
