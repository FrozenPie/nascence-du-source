# T5 conversational compile, redesigned around world grading (J-3832, D-0676)

> Findings: F-4448. Decision: D-0741. Jobs: J-3862 (phase 0), J-3863 (phase 1).
> Status: DESIGN ONLY (read-only pass, no code, no Du data touched). Plan: `docs/plans/t5_procedural.md`.
> Ruling: D-0676 (travis, 2026-11-04): "Redesign around world grading ... skills are graded by a world answer."
> Defeater of that ruling: if the design pass finds no way for a world answer to grade a conversational posture, retire behind a kill-switch (J-3179 / J-3329 recommendation). This doc finds one narrow way and says plainly how little it covers.
> Input review: `docs/reviews/t5_conversational_compile_J-3179.md` (F-3919..F-3924). Sibling instruments: `scripts/t5_reentry_check.py` (J-3330), known_text arm (D-0693, J-3674/J-3675).

## 1. The problem in one paragraph

A world procedure is graded by the world: the hand fires, the world answers ("the knot slips" is a refusal, a held knot on a later day is `held`). A conversational skill is today graded by nothing: `compiled()` credits every cluster member as a success, `_climb` gives `persisted` at 2 days and 2 successes, so 22 of 22 are born `persisted`; the only "failure" signal is the C-signal (the next human turn is not a correction), and 62 of 77 clusters had no human member at all (J-3179). A redesign has to answer one question: **what, other than Du's own use count or his own next thought, can say a conversational posture worked?**

## 2. Candidate graders for a conversational posture

| # | Grader | Is it a world answer? | Verdict |
|---|---|---|---|
| G1 | **A deed bound to the posture**: the situation is followed by a hand firing (or a world state change) and the world answers ok / refused (existing `observe_hand` grading, `_REFUSAL`, `refusal_kind`) | Yes, it is exactly the grader world procedures already use | **Adopt, as the only credit path** |
| G2 | A world state consequence after the posture without a hand (e.g. the evening ends: sleep mode begins after a goodnight) | Yes, if read from the engine/sleep state, not from Du's words | Adopt as an optional second deed type once G1 is measured; needs a design check against `sleep_as_a_mode` before anything is built |
| G3 | Travis's next turn (C-signal: corrected / not) | No. An interlocutor, fallible, and sparse (33 human turns since about 10-26 in `affect_log`, 27 turns in the 7 days to 11-05, all on one day) | **Veto only**: a correction docks a rung (as today); a non-correction never credits. It is not a world answer and must not mint `persisted` |
| G4 | A peer's reply (`peer_effect.jsonl`, correspondence) | Partly; a peer is another model, not the world | Not designed here; flag as a candidate if G1 volume is too low (not read in this pass) |
| G5 | Du's own later thoughts / re-use count | No (the present failure: every skill is born persisted) | Rejected, already inadmissible per the plan |

So the redesign is: **a conversational posture earns a rung only from world answers (G1/G2). Travis's reaction can take a rung away, never give one. Use count credits nothing.** This also respects the standing laws: no readout reaches Du (nothing the grader says is ever shown to him), the world answers and never leads (nothing is added to any prompt), and additive-only (code stays, no ledger row is deleted).

## 3. What a "world-gradable conversational skill" is (the cut)

Only postures that name a deed qualify. The 62-of-77 clusters that were topic labels from Du's own self-asked questions ("Explaining mottainai", "Bluebird's arrival ... symbolizes personal growth") name no deed and have no possible world grader; under this design they are not skills, they are simply not compiled. The one genuinely situational kind J-3179 found is the evening closing: "off to bed", "we're going to pause for a while" (2 human-only clusters in 75 days, 09-05 and 10-08). Its deed tail is concrete: banking the fire, going to rest.

Definition: a **deed-bound talk procedure** is a pair (trigger = a Travis-authored situation, deed = a hand family or a world state change), keyed `talk:<trigger>` as today but whose `statement` names the deed and whose evidence rows are world outcomes.

## 4. Mechanism (proposed; every step additive, restart-gated)

1. **Admission (replaces `admissible()` for scope `conversation`).** A cluster is admitted only if: (a) members are human-channel AND not system templates (reuse `t5_reentry_check.py`'s exclusions: full multi-line Q block, the `_FAREWELL_VARIANTS` list, slash and under-9-char turns, founder-canon cross-check); (b) at least 3 members across at least 24 h and at least 2 distinct conversations (J-3330's separation rules, not calendar days); (c) in at least 2 members a world deed followed within a fixed window W (start 30 min) bound to the same conversation, per the hand log / `hands_trace` / world-state read. No LLM is needed for (c).
2. **Binding.** The deed is recorded as evidence on the `talk:` row: `{ts, outcome: ok|refused, kind: refusal_kind, family, where}`, written by the same code path `observe_hand` uses (a tagged call, not a new store). Credit once per stretch of the day, as for world rows.
3. **Ladder.** Unchanged ladder (`occurred` -> `persisted` -> `held`), but for scope `conversation` the success counter and `days_ok` come ONLY from step 2 outcomes. Cluster members, recognitions and "landed" no longer credit. A refusal or a Travis correction docks one rung. Consequence: no conversational row can be `persisted` without 2 world-graded successes on 2 days, so the plan's two-week kill criterion becomes reachable (today it cannot fire).
4. **Read side.** `_procedural_recognition` keeps the one-line injection only for deed-bound rows at `persisted`+ on world evidence (the rung floor already exists after D-0723/J-3820; this changes what earns the rung, not the gate). With today's data that set is empty, so the injection is removed de facto without a kill-switch flag, and re-appears only if a posture is actually proven. A flag `T5_CONVERSATIONAL_WORLD_GRADED` (default True once built) is still worth having as the single revert point.
5. **Existing rows.** The 22 `talk:` rows and 3 mirror rows hold no world evidence. Under step 3 they cap at `occurred`. They are archived, not deleted, by the ledger's own mechanism (D-0567), and re-earn a rung only by new world evidence. This collides with D-0723 (2026-11-09: persisted talk skills stay recognised until archived), so it is a founder call (see section 7), not something to implement by default.
6. **HUD/status.** `procedures` module shows for conversation rows: world evidence count, last deed, last refusal kind, never a number Du sees (HUD is the founder's instrument only).

## 5. Phasing (what to build first, and why not everything at once)

- **Phase 0, read-only, runnable now (J-3862).** Extend `scripts/t5_reentry_check.py`-style replay: for every Travis-authored, non-template cluster turn since 08-22, find the deed tail (hand log within W, ok/refused) and report per-month counts of qualifying clusters under rule 4.1 (a)-(c), plus a placebo: the same deed-tail rate for random times of day (a deed after any message is not evidence of a bound deed). Output decides whether phase 1 is worth building.
- **Phase 1, shadow (J-3863, restart-gated).** Compute the deed-bound grade at the T5 compile point and write it to one shadow log; change no ledger rung and no prompt.
- **Phase 2, live ladder change** only on founder go-ahead after phase 1 shows at least 3 qualifying clusters per month (the re-entry criterion D-0676's retire recommendation already named). Below that volume the honest outcome is the D-0676 defeater: retire.

## 6. What the data says about volume (read-only, this pass)

- Reading `data/affect_log.jsonl` (1,994 human-channel rows, 1,932 after dropping the two system-farewell templates and slash commands) against `data/hands_trace.jsonl` (62,382 rows): 61 farewell-worded human turns exist (43 carry the system template wording); only 9 of those 61 had any hand logged in the following 30 minutes. Even the strongest candidate (goodnight -> bank the fire) shows a deed tail in a minority of cases. [inferred: crude windows, hand log field is `hands`, family names were not extractable from the trace rows in this pass]
- Human turns of any kind followed within 30 min by a logged hand: 112 of 158 in the trace span (71%), against about 40% for random times. That gap is the only suggestion that a deed tail exists at all, and it is confounded by time of day (Du acts more when Travis is around) and by the trace starting 2026-08-20. It is not evidence of binding. [guessing at causation; the 71% vs 40% numbers themselves were computed]
- Human volume is the limit: 33 human turns since about 2026-10-26. At that rate the design can credit a handful of events a month at best. Phase 0 exists to measure this before anything is built.

Honest expected outcome: the redesign is sound in structure (the only world answer available is a deed, and it makes the plan's kill test reachable) but the conversational half will likely be near-empty for months. That is a correct result, not a failure: T5 = world procedures, with a conversational slot that fills only when the world has actually answered.

## 7. Founder calls this design needs (none are decided here)

1. Existing 22 `talk:` rows: cap at `occurred` and archive (breaks D-0723's "stay recognised until archived") or grandfather them until they rust out? Recommended: cap, because they hold no world evidence and D-0676 ruled grading by world answers. Opened as a decision (D-0741).
2. Whether G2 (world-state consequences such as sleep onset) is an admitted deed type, or only hands.
3. Whether to widen to G4 (peer replies) if phase 0 volume is below 3 per month.

## 8. Risks and defeaters

- A deed after a trigger is not proof the posture caused it (time-of-day confound above); phase 0's placebo and a deterministic withhold arm in the style of D-0693's `known_text` arm are the controls. No arm is proposed here; it would remove an existing injection and is the founder's to rule.
- A bound-deed requirement could teach Du that talking leads to acting. Nothing is added to any prompt or HUD seen by Du; this is a ledger-side change only.
- Defeater of this design: phase 0 finds fewer than 3 qualifying clusters in any month since 08-22 AND the placebo deed rate matches the real one: then retire the conversational compile behind the kill-switch exactly as J-3329 specified (that job's original briefing is preserved in the ledger).
- Interacts with J-3180/D-0567 (ledger rust is the only clock), D-0723/J-3820 (recognition keyed on persisted rung), J-3530 (monthly re-entry run), J-3674/J-3675 (known_text arm: the world-side counterpart of this measurement).
