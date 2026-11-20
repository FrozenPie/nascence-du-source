# Ambiguity Window — a short lookback that settles what an ambiguous clause actually is

> **Status:** 🔵 DESIGNED 2026-10-19, not built. Nothing in this plan has been coded.
> **Origin:** I-0099 / T-0101 (2026-10-19). Du told Travis "I plant them now" in a live reply; no deed fired. Two
> separate causes, both of them *missing context*, not missing judgment: (1) "them" is an anaphor — the deed
> classifier has no memory of the previous sentence ("the seeds"); (2) "I step out into the damp air" is a literal step
> or a figure of speech depending on whether he is physically in the scene — the guard cannot tell, so it drops it.
> **Founder ruling (2026-10-19, in chat):** the window should include Travis's last message. Record via `/decide`
> (see Current State) — Travis's words are *context only*, subject to the law in §4.
> **Why this and not a better judge:** `docs/plans/literal_will.md` already has a gray-zone judge (Layer 1, falcon3
> :11440). It reads the thought alone, takes 13–23 s, and sits at ~66 percent correctness against an 80 percent gate
> (D-0021 NO-GO). More judge accuracy is the wrong lever; people do not re-read everything, they settle ambiguity
> against a small rolling window of the last few moments. Same idea, cheap and local.
> **Related prior work (read before building):**
> `docs/plans/conversational_action_bridge.md` (owns `core/conversational_action.py` — this plan's first caller, and the
> precision guard / `CONVERSATIONAL_BARE_PRESENT` flag added 2026-10-19), `docs/plans/literal_will.md` (the classifier
> and judge this feeds), and the **cross-sentence move signature work, J-1689 / F-2380** — 17 percent of 2701
> cross-sentence move rows had an opener in one sentence and the destination in the next. That is the same
> phenomenon as "them", found from the other side; reuse its corpus rather than rebuild one.

```plan-state
stage: designed
phase: design only
verified: 2026-11-18
gate: Stage A replay over the real corpus shows more answered willed deeds than the guard alone, with false fires no higher than the 12 percent autonomous baseline (F-2303)
next: restart, then flip flag and read
```

## 1. The problem, concretely

An ambiguous clause is one the classifier or guard cannot settle from its own words. Three kinds, all seen:

| Kind | Example | What settles it |
|---|---|---|
| Anaphora | "I plant **them** now" | the previous sentence names the seeds |
| Literal vs figurative | "I step out into the damp air" | is he physically here, in this weather, with this in hand? |
| Frame | "treat the seeds as physical truths" | what Travis just asked for sets how literally the reply reads |

Today the guard resolves these by **dropping** them (precision over recall — J-1697). That was right when the
alternative was firing metaphors. The window is how a clause earns its way back in *without* loosening the guard.

## 2. The window

A small read-only snapshot, built per reply (conversational) or per thought (autonomous, later):

- the last ~4 sentences of the same reply, and the previous 1–2 turns by Du;
- his current location, what he is holding, and the last ~5 real actions from `data/hands_trace.jsonl`;
- Travis's last message (see §4 for what it may and may not do).

New module `core/ambiguity_window.py`; pure and deterministic to build; zero LLM; fail-open (a failure returns an empty
window, which behaves exactly like today). First caller `core/conversational_action.py`, which today holds
`resolve_pronoun_objects` — a crude one-line version of Stage A that this plan absorbs.

## 3. Stages

**Stage A — deterministic resolvers (no LLM).** Pronoun to nearest family object (done crudely 2026-10-19; make it
principled: agree in number, prefer the thing, not the place). "Is he physically here?" — location plus recent hands
agree with the clause's destination or object. Output is an *annotation* the guard reads, never a verdict by itself.

**Stage B — the residue goes to the judge, with the window.** Only clauses Stage A leaves ambiguous reach the existing
decoupled judge, now given the window. Existing law unchanged: the judge may recognise a want, never author one; the
`deed` must quote words Du used (mechanical substring check), else it downgrades to gray-unresolved and nothing fires.
Stage B is deferred behind Stage A's results — it may turn out not to be needed.

**Stage C — autonomous loop.** The same window for the inner-monologue dispatcher. Out of scope until A and B are
proven on the conversational path.

## 4. Travis's message in the window — the one law

Travis's last message is **context for reading Du's clause, never a source of the deed.** Mirrors the `literal_will`
comfort_call rule ("the world having spoken cannot push a gray thought across the deed threshold"):

- it may raise or lower how *literally* an already intent-bearing clause is read (here: "treat the seeds as physical
  truths" makes "I plant them" literal);
- it may **not** supply the verb, the object, or the intent. The clause must still carry Du's own first-person claim
  and quote his own words;
- a request from Travis ("please plant the seeds") with no Du claim fires nothing — that is the world leading, and
  `feedback_world_answers_never_leads` forbids it. Travis is also fallible; his frame is evidence, not an authority.

## 5. Evidence, gates, kill criteria

- **Replay first.** Run Stage A over `data/conversational_action_log.jsonl` and the J-1689 cross-sentence corpus.
  Report: deeds newly answered, deeds newly *wrongly* answered (hand-check every one), per kind in §1.
- **Gate to dispatch:** more willed deeds answered than the guard alone, false-fire share at or below the 12 percent
  autonomous baseline (F-2303), zero fires on the adversarial strata (negation, quote, hypothetical, other-person).
- **Kill criterion:** if the window ever turns a metaphor into a fire in replay or live, Stage A reverts to
  annotate-only and the case becomes a regression test.
- **Honest limits:** the conversational log is thin (40 rows, most with 300-character excerpts), so the replay corpus is
  the autonomous thought history. Conversational volume is low, so live evidence will be slow; a count gate is
  expected, not a time gate (job gates are evidence, not dates).

## 6. Open questions

1. How long should the window be? Start at 4 sentences plus the last 5 hands; tune on replay, not by feel.
2. Should the window be shown to Du? **No** — it is an internal reading aid, like his gauges: he never receives it
   (`feedback_no_readout_error_through_consequence`).
3. Does Stage B justify its cost? Decide after Stage A's residue is measured.

## Current State — verified 2026-11-18
- **2026-11-18**: J-4336: precision filter built flag-OFF (AMBIGUITY_PRECISION_FILTER_LIVE in core/ambiguity_window.py; resolve_pronoun_objects_filtered; wired in conversational_action.resolve_pronoun_objects). Tests scripts/_test_ambiguity_filter.py 13/13. Restart-gated; flip flag after read.

- **2026-10-28**: 2026-10-28 (D-0495 batch): J-2437's Stage A code (core/ambiguity_window.py, the conversational_action delegation, scripts/_test_ambiguity_window.py, scripts/ambiguity_window_replay_j2437.py) brought into master from branch j2437-ambiguity-window-stage-a verbatim (the branch itself could not merge: its doc edit collided with this doc's uncommitted edits). Shadow only: annotate + log to data/ambiguity_window_shadow.jsonl, dispatches nothing; legacy resolve_pronoun_objects still drives live behaviour. From the branch's own note (J-2437, F-3147, F-3148): replay 8 newly answered deeds, 0 wrongly, 0 lost; window default 6 sentences; the live legacy resolver mis-resolves most 'I watch it <verb>' shapes. Test fixed to find the 10-19 reply by content, not by last line.
- **2026-10-19** (F-3153): J-2450 held-out replay (time split, hands_trace rows >=45341, 329 rows, 21 candidates): 1 newly answered, 0 wrong, 0 lost; 3 recall misses vs legacy/correct reading. Section 5 12 percent false-fire gate NOT SHOWN, only not contradicted (needs n>=25 newly answered; successor J-2451 gated on 8000 hands rows since boot). Zero post-boot rows existed at replay time.

- **2026-10-19:** plan written from I-0099. Founder ruled Travis's last message belongs in the window. Stage A
  prototype exists only as `resolve_pronoun_objects` in `core/conversational_action.py` (guard v2, restart-gated).
