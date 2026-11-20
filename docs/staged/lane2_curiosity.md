# Lane 2 Curiosity — the Witness as a question source (staged, 2026-09-26)

**Status:** 🟡 SHADOW BUILT (2026-09-26, J-1374) — restart-gated; the 7-day read against §4's metric sheet
is pending a live Du restart plus real accrual (see the dated Current State note below). Promoted this
session from idea I-0069 (raised 2026-09-15, founder + Claude conversation) at the founder's direction
(T-0064, "let's look at lane 2 … we really need to expand on this").
**Parent plan:** [docs/plans/lane2_the_witness.md](../plans/lane2_the_witness.md) §8.6 — this is one of
its three 2026-09-26 expansion tracks, kept as its own doc because it adds a new *direction* (Lane 2 →
frontier) rather than a new read of an existing one.
**Roadmap:** [docs/ROADMAP.md](../ROADMAP.md), staged cluster (bullet added 2026-09-26).
**Memory:** `project_nascence_lane2_curiosity.md`.
**Decisions:** **D-0282** ruled (a), 2026-09-26, by travis — build the shadow-first design, not the
cheaper break-born variant. See `decide.py show D-0282` for the exact ruling and defeater.
**Related, not the same:** `docs/staged/curiosity_librarian_route.md` (how frontier questions get
*researched*; this doc is about where one more kind of question is *born*), and
`docs/archive/loop_wiring_matrix.md` wire 5 (whose second half — "a broke prediction with a named cause →
frontier question, source `witness`" — this doc specifies).

```plan-state
stage: shadow
phase: Wonder field shadow-built and code-verified via J-1374/F-1974; real 7-day live read is restart-gated
verified: 2026-11-14
evidence_read: 2026-10-15
gate: data/lane2_would_ask.jsonl live days >= 7, not before 2026-10-03, J-1409
next: Wait for J-1409; needs a live Du restart onto this schema change plus real deepseek-seat accrual, not before 2026-10-03
cluster: 6
```


## Current State — verified 2026-11-14
- **2026-11-14** (F-4701): J-3965: D-0429(b) wonder prompt-side avoid-list built (A/B armed, shadow-only, flag WONDER_AVOID_LIST); live after merge+restart; 7-day A/B read queued.

- **2026-10-16** (F-2894): J-2173 (D-0429 b): wonder anti-repeat gate built shadow-only in core/lane2.py (commit da401a5d on the lane2_core worktree branch, restart-gated, kill switch WONDER_ANTI_REPEAT). would_ask now suppressed on lexical-repeat (Jaccard >= 0.5 vs 7d) and topic-asked-today; new log keys lexical_sim_max/lexical_repeat/topic_asked_today; metric sheet gains w1_lexical_distinct_share_7d and w4 topic/suppressed counts. Prompt untouched (echo risk). Replay: 7d lexical distinct share 0.153, would_ask 28 -> 6. Generation-side distinct/anchored shares are unchanged by design.
- **2026-10-15** (F-2817): 2026-10-15 J-1951 7-day read: W-1 distinct share 0.590 (<0.8, D-0282 defeater fired), W-2 0.997 pass, W-3 0.459 (<0.9), would-ask cap saturated 4/day; decide opened to reopen D-0282; weekly read respawned.

### What we have
- D-0282 ruled (a) shadow-first (2026-09-26); the `wonder` field is CODE-COMPLETE in `core/lane2.py`
  (J-1374): `_SYSTEM` contract law 5, habituation via `lane2_break_habituation.observe_wonder()`, rows
  to `data/lane2_would_ask.jsonl`, `wonder_metrics` (W-1..W-4) in `status()`.
- Verified with a sandboxed unit/logic pass only — no live model call yet (F-1974): `out_fields`
  back-compat, the world-question boundary, habituation growth/decay, the daily cap, and the W-1..W-4
  formulas all passed.
- F-1975 (in passing): W-4's cap is 4/HOUR by code (`HINT_MAX_PUSH_PER_WINDOW`), not 4/day as the doc's
  own symmetry framing implied — the briefed 4/day number itself was still implemented correctly.

### What we need
- The real 7-day read against §4's metric sheet — needs a live Du restart onto this schema change plus
  real deepseek-seat accrual. Deferred to **J-1409**, not-before 2026-10-03, not fabricated.

### What we're doing next
Nothing until J-1409's window opens; `frontier.note_question()` stays uncalled (the flip is a separate,
later ruling).

## 1. The honest constraint first — the frontier is oversupplied

Read this morning from `data/frontier.json` (9,440 questions, all time):

| | count |
|---|---|
| open | 346 |
| faded | 8,908 |
| resolved | 186 |
| born of `curiosity` / `intention` / `dream` / `prism` / `study` | 4,680 / 4,075 / 373 / 283 / 29 |
| ever attached a finding, by source | curiosity 1,154 · prism 32 · study 5 · intention 1 |

`pending_pursuit()` (`core/frontier.py:235`) researches one question per curiosity firing (~17/day), and
ranks grounded sources (`_GROUNDED_SOURCES = study, reading, curiosity, prism`) ahead of self-leaning
ones — which is why `intention` questions, 43% of all births, have been answered exactly once. **A new
producer therefore earns its place only by being few and grounded-ranked, never by volume.** Every number
in §4 is sized against that, and "Lane 2 asks more" is explicitly not a success metric.

## 2. What already exists that this reuses (no new mechanism)

- **The percept set and the boundary.** `core/lane2.py gather_percepts()` — the experienced tuple at his
  standpoint, body, somatic; never Lane 1's thoughts, memory or axiom. The question is generated from
  exactly this and nothing else. (§8.4 of the parent plan may widen the set with `light_band`/`smells`
  under D-0280; that widens what can be wondered about, nothing here depends on it.)
- **The output schema and its instruments.** Lane 2 already returns four JSON fields per tick —
  `notice`, `uncertain`, `expect_next`, `horizon` (`_SYSTEM`, `core/lane2.py:544`) — each checked by
  `_grounding_check`, `_invention_check`, `_metaphor_flags` + the decoupled metaphor judge. A fifth field
  inherits all of them. Note `uncertain` is *not* this: it names what the percepts cannot settle ("the
  exact time of the kingfisher call is unknown"), an epistemic gap, not a question about the world.
- **The birth door.** `frontier.note_question(question, source)` — dedups by token overlap, applies
  `is_world_question()` (length > 15, no self tokens, not procedural), fades the stalest beyond
  `MAX_OPEN`. A `witness` question goes through the same door as every other.
- **The dose gate.** `core/lane2_break_habituation.py` (J-1161) — per-topic squishy-spring weights keyed
  on `_topic_of()`'s canonical topic (vocabulary extended 2026-09-26, J-1370, now resolving 96% of break
  texts). The same gate that decides whether a break rides to the idle-thought seed decides whether a
  wonder on that topic is still novel.

## 3. Two birth mechanisms, and which one this is

**A. Percept-born (the idea itself, recommended).** A fifth field, `wonder`: *one* question about *one*
concrete percept named in this tick's own `notice`, world-facing, answerable in principle by someone who
knew the world (botany, tides, bird behaviour, how embers cool) — never by looking inward. Prompt law
added: the question must name a field present in the PERCEPTS; it must not be about the observer.
This is a change to `_SYSTEM`'s JSON contract — the parent plan's own echo history (2026-08-20: worked
examples and prior-feedback both lock deepseek into verbatim repetition) means the field is added with
*no* worked example and read for template lock exactly as `expect_next` is (§4 W-1).

**B. Break-born (the cheaper fallback, wire 5's literal wording).** On a judged BREAK with a resolved
topic — the same event that feeds the Phase 1 cup — a *template* question with no LLM call:
"Why did the {topic} not {expectation}, when what was observed was {percept lines, one line}?" Zero prompt
change, zero echo risk, but the question is about the Witness's own failed forecast, not about the thyme.
It answers "why was I wrong" rather than "what is that" — useful, but not what the founder described.

D-0282 offers (a) A only, (b) B only, (c) both on the same would-ask log for comparison, (d) not now.
Recommendation: **(a)**, with (c) as the honest way to settle it if the founder is unsure.

## 4. Pre-registered metric sheet (written before it runs, per the parent plan's convention)

Shadow phase: `data/lane2_would_ask.jsonl`, one row per generated wonder —
`{ts, wonder, topic, horizon_of_notice, grounded, invented, world_question, would_ask, w_topic}`.
`frontier.note_question()` is **not called** in shadow.

| # | Metric | Prediction | Decides |
|---|---|---|---|
| W-1 | Distinct share of `wonder` (7 d) | ≥ 0.8 — the bar `expect_next` lives under (0.906 today) | Below 0.8 the field has template-locked; drop it before it reaches anything |
| W-2 | `is_world_question()` pass rate | ≥ 0.95 | Below, the field drifts to self/procedure — the boundary failed in the generator, not the code |
| W-3 | Percept-anchored share (names a present field) | ≥ 0.9 | Below, wonders are about things not perceived — §2.8b's "the world's knowledge for free" leak, from the other side |
| W-4 | Would-ask rate after the habituation gate | low single digits/day; hard cap 4/day (`WONDER_MAX_PER_DAY`, `core/lane2.py`) | Tracking the raw tick rate (~280/day) means the gate is not gating |
| W-5 | Phase 0 kill metrics unchanged | metaphor leak < 5%, named-uncertainty ≥ 90%, question-shaped `expect_next` ≈ 0 | Any of them leaving its band after the restart that picks up the schema change means the fifth field is disturbing the four — revert the prompt |
| W-6 | *(after the flip only)* pursued and resolved share of `witness` questions vs `curiosity`-born | non-zero: `pending_pursuit()` picks at least one `witness` question per week; resolution rate not below curiosity's own | If never picked, the source is being out-ranked and the flip achieved nothing — a real finding either way |

## 5. What it explicitly does not do

- Lane 2 does not research, read the frontier, or see the answer. Questions leave; nothing returns to
  it. (The parent plan's boundary — no text ingestion path — is untouched.)
- No text reaches Du. A `witness` question, once flipped, reaches Du exactly the way every other
  frontier question does — through curiosity's own research and return path — never as Lane 2's voice.
- No new percept, no new judge call, no new store: the would-ask log is the only new file.

## 6. Build order (once D-0282 rules)

1. **Shadow — DONE (2026-09-26, J-1374).** the `wonder` field in `_SYSTEM`'s contract + `parse_json_loose`
   tolerance for its absence; run the three existing lexical checks on it; `_topic_of(wonder)` →
   habituation gate → `would_ask`; log the row; `status()` gains `wonder_metrics` (W-1..W-4 live;
   W-5 reads `status()`'s own existing top-level fields rather than duplicating them). Restart-gated —
   code shipped this job, but the **7-day read**, on the deepseek seat, against the sheet above, needs a
   real Du restart onto this schema change plus real days of accrual and has NOT happened yet (see the
   Current State note above and **J-1409**, the follow-up job spawned from F-1974, not-before 2026-10-03).
2. **Flip (separate, later, its own ruling):** `LANE2_ASK=True` (a new flag — deliberately *not*
   `LANE2_LIVE`, which gates the Phase 1 cup/bucket and should be readable on its own) calls
   `frontier.note_question(wonder, "witness")` when `would_ask`; `"witness"` is added to
   `_GROUNDED_SOURCES`. Both are one-line changes; both are the flip, not the build.

## 7. Open for the founder

D-0282 — see `decide.py show D-0282` for the exact question, options and defeater.
