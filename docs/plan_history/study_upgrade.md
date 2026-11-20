# study_upgrade — folded history


---

# History folded on 2026-09-27 from `docs\plans\study_upgrade.md` (plan-compact, 5 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py study_upgrade`._

## Current State — verified 2026-09-02 (§8, J-0421/F-0553 — live firing CONFIRMED, SHADOW caveat lifted)

The Status header's "not yet confirmed firing on its own inside the live continuous run" is no
longer true and has been updated. `data/study_ledger.jsonl` now holds **17 rows** of real deeds
spanning **2026-08-22 08:17 → 2026-08-30 01:17 UTC** — first row `door_open`, last row
`clear_grate`, with F-0553's read also citing `ash_to_garden` and `lamp_fill` among them —
accrued continuously by the live loop, not an isolated verification run. Read directly from the
ledger file for this update (J-0421). Note Du has been offline since 2026-08-31 17:47 (clean
shutdown), so accrual is paused, not broken.

## Current State — 2026-09-17 (§9, J-1056/F-1470 — two grammar bugs on the tea path fixed)

F-1442 (following up F-1301's 2026-09-05 "tea I just made" false-narration read) traced the tea
latch's dispatch grammar (core/hands.py `wants()` + core/literal_will.py) end to end and found two
separate, confirmed-by-direct-execution regex bugs, both now fixed and verified (F-1470, real
18,968-row `data/hands_trace.jsonl` replay, zero regressions): (1) `_B_RETRO`'s retrospective
blocker required "i" and its past-tense verb to sit exactly one word apart, so "i just made"/"i
already made" silently escaped the guard meant to catch retrospective narration — widened to allow
0-2 intervening words; (2) the tea latch's own bare noun-phrase triggers ("cup of tea"/"pot of
tea", `nodes/inner_monologue_node.py` ~line 3410-3412) were being silently killed by the
determiner-guard (`_NOT_NOUN`, added 2026-09-04 for a different, real noun/verb ambiguity) whenever
preceded by a/the/my — which is nearly always how they occur in real English — so a genuine,
present-tense, unambiguous tea want phrased without an explicit make/brew/boil verb ("I want a cup
of tea") never dispatched at all. Both fixed in `wants()`'s own matching loop; scope confirmed
tea-specific by grepping every `wants()` call site in the repo. One narrow, honestly-reported
residual found in the real-corpus check (1 new false-positive fire out of 18,968 rows, caused by a
separate pre-existing gap in `_B_OTHER`'s verb coverage, not by this fix) — follow-up spawned
(J-1076) to corpus-check that gap on its own evidence rather than guess at a fix.

## Current State — 2026-09-18 (§10, J-1076/F-1492 — `_B_OTHER` gap corpus-checked, real but rare)

J-1076 ran the real, shipped `core.literal_will.classify()` (ground truth, not re-derived) over the
FULL, unsampled `data/hands_trace.jsonl` (19,417 rows) + `data/monologue_log.jsonl` (47,901 rows) —
67,340 rows — to measure how often `_B_OTHER`'s closed verb list actually misses a real named-
other-person deed (F-1470's own follow-up question). Found exactly **2 more real historical hits**
(0.003% of the corpus), both in `monologue_log.jsonl`, zero more in `hands_trace.jsonl`: (1) ts
1780866620.76, family `woodwork` — "He saw them as sacred..." false-fires because "saw" is
simultaneously the woodwork family's own verb AND its own tool-object AND the past tense of "to
see"; (2) ts 1782379209.29, family `water_fill`, verb "get" — "...they get their due amount of
attention before spring" false-fires because "spring" (season) collides with the water_fill
family's own "spring" (water-source) object. Both are **verb/object HOMONYM collisions specific to
this grammar's own tables**, not simple missing-common-verb gaps like the tea case's "wait(s)" —
so naively broadening `_B_OTHER`'s verb list (adding "saw"/"get"/"see") would risk large new
over-blocking regressions on ordinary, unrelated uses of very common words. Combined with F-1470's
own 1 tea hit, that's 3 known real instances total across the whole corpus to date — genuinely rare,
matching the job's own "record honestly rather than force an unfounded fix" fork. No code change
made; see F-1492 for full method (3 passes of increasing precision) and both real examples.
Open, unresolved-in-this-job question: whether `monologue_log.jsonl` thoughts are actually run
through the live dispatch/`classify()` path (code strongly suggests yes; not independently
confirmed by timestamp cross-reference since the two logs don't overlap in time for either hit).

## Current State — 2026-09-18 (§11, J-1091/F-1499 — §10's open question resolved: dispatch reached, but not by these 2 hits)

J-1091 read `nodes/inner_monologue_node.py`'s `_think()` call graph end-to-end (no sampling) to
answer §10's open question directly. Result, **verified**: `_think()` is one linear function body
from thought/intention extraction (line 3061) to the `monologue_log.jsonl` write (`self._log()`,
line 4706, its only call site) with **zero early `return`** in between (confirmed by scanning every
line in that range) — so `core/dispatch.py`'s `dispatch()` (lines 3120-3135, which itself calls the
same `core.literal_will.classify()` F-1492 corpus-checked and fires a real hand on any `DEED`
verdict) and `core/hands.py`'s `trace()` (lines 3356-3362, "one row per thought") both run
unconditionally, in that order, before every `monologue_log.jsonl` write. **So yes: a
`monologue_log.jsonl` thought does reach real dispatch** — this is not a logging-only or
gating-only path.

But that does NOT give F-1492's own 2 `_B_OTHER` homonym hits (ts 2026-06-07, ts 2026-06-25) any
real-world consequence: `core/hands.py` and the `dispatch()` call site are both self-dated
"2026-08-22" in their own module/inline comments (founder: "investigate the actions system in depth
— it sounds half-baked"), and `data/hands_trace.jsonl`'s own earliest real row (2026-08-21T23:27:42
UTC) lands right at that birth date — the mechanism simply did not exist yet 46-76 days earlier when
those two thoughts were generated. They remain inert, shadow-only grammar artifacts of history, not
a live-consequence bug at the time they fired. The `_B_OTHER` homonym gap itself (the woodwork
"saw" / water_fill "spring" collisions) is still present in `core/literal_will.py` today and
unfixed — per this same read, if it recurs in a FRESH thought now, it WOULD reach real dispatch.
See F-1499 for full evidence (line numbers, the `_think()` linearity check, and the timestamp
cross-reference).

## Current State — 2026-09-18 (§12, J-1112/decision:D-0226 — the narrow "I just did X" grounding check is BUILT)

D-0226 ruled (2026-09-18, travis): add a narrow post-generation grounding check for the specific
"I just <verb>-ed <object>" completed-deed pattern only — the exact gap F-1442 found (the 09-05 "I
just made tea" thought) and F-1479's independent re-sweep confirmed still has no fix. Built this job,
in `nodes/inner_monologue_node.py`:

- New module-level `_deed_claim_verb(thought)` detects the narrow "I just <0-1 word> <verb>-ed"
  grammar, restricted to the same closed past-tense-verb vocabulary `core/literal_will.py`'s own
  `_B_RETRO` already uses for retrospective-deed detection, plus a small study-domain extension for
  this room's own ledger deed verbs. An unmapped (mental/emotional) verb never matches — scope stays
  exactly to completed-DEED framing, nothing broader, per the ruling.
- New module-level `_deed_ledger_grounded(verb, at_ts, window_s)` checks the real per-domain ledgers
  (`study_ledger.jsonl` — D-0226's own named example — plus garden/wood/shore/life ledgers) for a
  matching deed within a 300s window; fail-open on an unmapped verb or an unreadable ledger.
- `_think()`'s call site (right before its single `self._log()` persistence call, on the FINAL
  thought text): a real hand that fired THIS cycle (`_dispatched`/`_acted`, already computed earlier
  the same cycle) grounds the claim directly — the exact mechanism that would have caught the tea
  case (`wants()` returned False that cycle, so nothing ever dispatched). Only on a miss does it fall
  back to the ledger check.
- On a miss: logs `[monologue] UNGROUNDED DEED CLAIM (D-0226) — ...` and sets a new
  `ungrounded_deed_claim` field (default `False`) on the persisted `monologue_log.jsonl` row — **flag
  for review**, D-0226's own explicit choice of mechanism; the thought text itself is never rewritten
  or suppressed (additive-only, no behavior change to what he actually thinks or says).

**Verified** against the full real `data/monologue_log.jsonl` (47,944 rows, not sampled) plus the 5
real per-domain ledgers: the known 09-05 tea thought is correctly re-detected and flagged
(`ledger_grounded=False`); the whole corpus has exactly 2 rows matching the narrow grammar (confirms
F-1442/F-1479's own "this is rare" finding, now at a larger corpus size too) — the tea one (correctly
flagged) and one much older "I just poured water" garden thought (also flagged, but its timestamp
predates `garden_ledger.jsonl`'s own earliest row by ~51 days, so this one can't be resolved true/false
from ledger evidence alone — correctly left for a human to look at rather than asserted either way).
The two real F-1442-cited grounded "cold grate"/"stopped clock" thoughts use different phrasing ("I
will rake"/"I rake") that correctly does not even match this narrow grammar — confirms the check
doesn't reach past its own scope into other legitimate retrospective narration. A real bug (no upper
timestamp bound, so a ledger row from the far future could wrongly "ground" a much earlier claim) was
found and fixed during this same verification pass, before shipping — see F- (this job's own finding)
for full detail.

**D-0226's defeater, unchanged and still the thing that reopens this**: revisit if (a) a second
confirmed instance of an ungrounded "I just did X" claim turns up in a future sweep despite this check
now being live (would mean the grammar needs broadening beyond the closed verb list above), or (b)
`_build_system_prompt()`'s JSON schema/prompt is next revised for an unrelated reason (fold this
grounding language into that revision rather than leaving it standalone).
