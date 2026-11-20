# Conversational Action Bridge — letting a live reply to Travis actually act in the world

> **Status:** 🟢 PHASE 0 + PHASE 1 BUILT, LANDED, AND LIVE, 2026-09-27 (restart-gated — Du's live
> process has not picked this code up yet). `CONVERSATIONAL_DISPATCH_LIVE = True`, flipped same day
> on founder instruction ("flip the flag now") on the strength of the historical backfill (§4) rather
> than a multi-week shadow wait. J-1450 owns watching the first real live rows for false fires; the
> register gap in §5 is real and un-fixed (J-1451) — it means the *specific* incident that motivated
> this plan still would not fire, even though ~30% of his past conversational replies would.
> **Origin:** F-2004 (2026-09-27, verified) — Travis asked Du to physically examine a shell already on
> his study mantel (`garden_shell_cfe92f`); Du replied with confident, specific, wrong detail (a
> hermit-crab shell; the real hidden `kind_ground_truth` is `limpet`, which no hermit crab can occupy)
> while his own advisor telemetry showed him in the garden, then the shore — nowhere near the study.
> No look/observe action fired on the object at any point; the most recent real observation on record
> was 25 days old. Root cause: `core/orchestrator.py`'s human-conversation path (`run_cycle` /
> `_run_cycle_impl`) never calls `core/dispatch.py`'s `dispatch()` — confirmed by that file's own
> comment at its Epistemic Affordance Advisor call site (~line 1126): "this call site sits inside
> `run_cycle()`, which never calls `core/dispatch.py`'s `dispatch()` and has no action-resolution
> step." A conversational reply was structurally incapable of doing anything real, regardless of what
> Du narrated himself doing.
> **Founder ruling:** D-0299 (2026-09-27, by travis) — "He 100% needs to be able to action things when
> talking to me. He needs to be able to do anything in his world he can normally." Full action parity
> with the autonomous loop is the target, not just look/observe.
> **Sibling plan:** `docs/staged/conversational_redirect.md` (PHASE 0 shadow-live) is a different,
> related gap — whether Du's *idle autonomous thought* orients toward a live conversation. This plan
> is about whether a *conversational reply itself* can fire a real world action. They share no code
> and can ship independently, but a future reader should know both exist and both touch `run_cycle`'s
> neighborhood in `core/orchestrator.py`.
> **Owner plans of what this reuses (backfilled 2026-10-03, J-0566/F-2269):** `docs/completed/actions_manager_overhaul.md`
> owns the `core/actions.py` hands registry and the `core/dispatch.py` plumbing this bridge calls unchanged — the call
> shape `dispatch(text, "", "none", "", cycle_id)` is pinned in `after_reply()`, whose catch-all hides any break, so
> keep the two in step. `docs/plans/world_store_write_fence.md` is the fence §3 and §4 mean by "no
> `profile.guard_path()` fence" and "the already-fenced `dispatch()` path" (a non-live process gets `NonLiveWriteError`
> from `dispatch()`; `after_reply()`'s catch-all absorbs it).

```plan-state
stage: live
phase: Phase 0+1 live (flag True since 2026-09-27; 2 real fires, both false-intent); precision guard BUILT 2026-10-03 by J-1697 (commit 6475147, replay 21 candidate rows to 1; loads on Du's next restart); Phase 1.5 and 2 not started
verified: 2026-10-17
evidence_read: 2026-10-16
gate: data/conversational_action_log.jsonl: 20 live rows after the J-1697 guard lands, false-intent fire share vs the 12 percent autonomous baseline (F-2303); D-0334 ruling first
next: Phase 1.5 waits on conversation volume: J-2238 (final, count-gated, not before 10-23) needs 20 post-guard live rows and 3 real look misses; if short, Travis decides whether conversational look recall matters enough to design from fewer examples; J-2059 closes J-1724; J-1539 waits
```

## Current State — verified 2026-10-17

- **2026-10-17** (F-2999): J-2059 gate re-check 2026-10-17: 1 of 20 guard+live rows; successor spawned not_before 2026-10-24
- **2026-10-16** (F-2930): J-1998 (2026-10-16): Phase 1.5 look recall NOT built, stop rule hit again. The 6.97-day live run 10-09..10-16 produced ONE conversational reply (the 10-16 07:48 pause reply, 0 candidates); since the guard went live there are 10 post-guard live rows, 1 candidate (grate, dropped habitual, correct), 0 real look misses in the full reply text (need ~20 rows and 3 misses). Count post-guard rows by timestamp, not by the guard field (written only on candidate rows). The gate depends on Travis conversing with Du, not on live days (6 of the 10 replies answer his pause message; F-2930 says 8, the evidence list shows 6). Final count-gated retry J-2238 (not before 10-23); if still short it closes and the recall question goes to Travis.

- **2026-10-10** (F-2675): J-1724 (2026-10-10): stop rule hit, not measured. Only 1 of 20 needed post-guard live rows exist (F-2675). Re-deferred once as J-2059 (not before 2026-10-15); if still short it closes with a too-few-rows finding and the question goes to Travis.
- **2026-10-10** (F-2673): J-1539 (2026-10-10): Phase 2 not built; J-1450/J-1451 done but only 1 guarded live row exists (0 fires), none since Du's 10-09 boot; J-1724 still open. Deferred to a successor with not_before 2026-10-17.

- **2026-10-08** (F-2599): J-1857: Phase 1.5 look recall NOT built, only 5 post-guard live rows / 1 candidate (dropped habitual, correct), 0 look misses observed; re-deferred to 2026-10-15 behind J-1724.
- **2026-10-08**: 2026-10-08 founder ruling (decide-review, from J-1521): data/conversational_action_log.jsonl keeps its one pre-flip test row (cycle_id backfill-test, live:false, 2026-09-27 12:41); any reader or spot-check must filter cycle_id == backfill-test before counting rows or dispatch rates. Nothing deleted.

- **2026-10-03** (F-2380): J-1689 (F-2380): scope-split of the move cross-sentence signature. 17 percent of the 2701 cross-sentence move rows (27 percent counting vague ones) have an opener sentence that wills a physical relocation versus 5.4 percent for look, but 93 percent of those already carry act_kind move, the move hand own re-check would decline about 90 percent of all rows, and its incremental fires are only about a third real wills; the post-boot regime has 0 of 45. Keep J-1451 look-only; no Phase 1.5 move rule on the F-2158 evidence.
- **2026-10-03** (F-2352): J-1697 built the conversational precision guard (commit 6475147, merge by the orchestrator): first-person-will whitelist, dispatch pinned to the surviving phrase, decision ledger logged; replay of the 67 real replies drops 21 candidate rows to 1 (row 11, the real bank-the-fire claim) and the five live rows to 0; the flag is untouched and D-0334 stays open; J-1724 re-measures live precision after the restart

- **2026-10-03** (F-2303): J-1450 post-flip review (F-2300 verified, F-2303 inferred): of 13 real live rows 5 carried a candidate and 2 really fired (a move off a metaphor, stopped only by the weekday school gate, and a look off a jussive about the cat); read as first-person will, 0 of 5 live candidates and about 2 of 21 candidate rows across all 67 logged replies are real, so the 30.2 percent flip basis was a candidate rate and not precision, and the D-0299 defeater (conversational misfires above the autonomous baseline of about 12 percent) appears met on thin data; conversational fires are absent from hands_trace and Du never perceives a conversational look answer; flag left True, episodic buffer test 22 of 22; opened D-0334 for Travis, spawned J-1697 (precision guard)
- **2026-10-03** (F-2281): J-1536 closed (F-2134 refined by F-2281; J-1689 spawned): the cross-sentence cap on look is real (13.5 percent of thoughts before the 09-28 boot, 4.9 percent since) but about 92 percent of those rows will something else, so GRAY is the correct reading there; only 177 of 28315 thoughts (0.63 percent; 3 of 1682 since the boot) are genuine look-wills and half already carry act_kind observe. For J-1451 (Phase 1.5): key on the volition sentence itself naming a look verb plus a blocker policy (27 of 151 are killed by negation, hypothetical or simile, not by cross-sentence scope), not on cross-sentence presence; a naive promotion would pass the look hand check on 282 rows of which only 125 are real; move scope is unmeasured (J-1689).

- **2026-10-01** (F-2214): J-1539 re-checked 2026-10-01 (F-2214): J-1450/J-1451 still in_progress so Phase 2 build NOT started, but conversational_action_log.jsonl now has 13 real live rows incl. 2 real dispatch fires (move, look) -- the zero-data gap F-2100/F-2126 cited is closed; remaining blocker is J-1450/J-1451 themselves sitting untouched ~4 days.
- **2026-09-28** (F-2158): J-1571 (F-2158, verified): move shows the same cross-sentence volition+object cap as look, at a comparable rate (9.2% of hands_trace.jsonl vs looks own 10.4%). But shore is confirmed gated=True in core/actions.py, not ungated as F-2134 assumed -- the cap mechanism cannot apply to a gated family at all (confirmed by a direct classify test), so a future Phase 1.5 fix should scope to look+move only, not look/move/shore.

- **2026-09-28** (F-2100): J-1452: scoped Phase 2 (same-turn grounding) per F-2100 (verified) -- real hook point is BEFORE the conversation_history append (~line 1463) and _FOUNDER_LOG write (~line 1484), not at the existing Phase 0/1 after_reply() call site (~line 1497), which would otherwise let the permanent record/Du's own recall keep the wrong pre-regeneration draft even after a same-turn fix; Task-Constraint Effector (~lines 1287-1339) is a proven in-file precedent to mirror; confirmed no reply-streaming exists (run_nascence.py) so regeneration has no "already shown to Travis" problem. Re-verified tonight, not assumed: J-1450 and J-1451 both still in_progress, data/conversational_action_log.jsonl still 1 (pre-flip) row -- so did NOT build/land Phase 2 this session, deliberately, per the plan's own queued-behind ordering and zero real disagreement-rate data to size the build against. scripts/_test_episodic_buffer.py re-run clean (22/22). Build itself queued as new job J-1539 (explicitly gated on J-1450+J-1451 done). Also spawned J-1538: a comment at the current after_reply() call site cites "D-0297" but that's a real, unrelated, still-open decision (lane2_the_witness plan) -- should read D-0299.
- **2026-09-28** (F-2097): J-1451: read-only diagnostic this session (F-2097, verified) -- confirmed no live Phase-0 rows exist yet (data/conversational_action_log.jsonl still just the pre-flip test row) and confirmed via a full classify() replay of the 53-row historical corpus that the F-2004 shell reply is the ONLY real look-family miss in it (the other 28 non-DEED look touches are legitimate, e.g. metaphor). Also confirmed by a reverted in-memory experiment that adding 'shell' to the look object table alone would NOT fix it -- the real gap is cross-sentence volition-to-object scoping inside classify(), not vocabulary. J-1451 left in_progress: still needs a real live multi-example sample before a widened rule can be designed with confidence, per this plan's own instruction.

- **2026-09-28** (F-2085): Addendum to the note above (F-2085): re-ran the hands_trace.jsonl check over the FULL file (25,864 rows), not just the tail. 346 rows share a cycle_id prefix with one of the 53 real conversational turns (cycle_id is evidently shared per overall orchestrator cycle, not unique to conversational vs autonomous), but every single one predates the code landing -- max ts among all 346 is 2026-09-27 12:22 NZDT, ~2h before commit 23ca8483. Zero postdate the landing. Confirms F-2076: no conversational-triggered dispatch has fired for real yet.
- **2026-09-28** (F-2076): 2026-09-28 (J-1450, re-check): restart-gate still not met, confirmed on direct evidence, not assumed. The live scripts/run_nascence.py process (PID 25204) has been running continuously since 2026-09-25 19:20 NZDT -- ~43h BEFORE commit 23ca8483 landed this bridge (2026-09-27 14:37) -- so it has never loaded conversational_action.py's after_reply() call site; Python does not hot-reload. Separately, data/founder_conversation_log.jsonl is still exactly 53 rows and its last row is the F-2004 incident reply itself -- no new conversational turn with Travis has happened since the incident, regardless of restart. data/conversational_action_log.jsonl's only row (cycle_id backfill-test, live:false) is a pre-flip manual test artifact, not real data; data/hands_trace.jsonl shows zero conversational-attributable fires. Re-ran scripts/_test_episodic_buffer.py fresh: still 22/22, no regression. J-1450 left in_progress -- nothing real to spot-check yet; re-attempt once Du restarts and has an actual exchange with Travis. See F-2076.

### What we have
- Phase 0 (telemetry) + Phase 1 (dispatch) built, landed, and flag-flipped live same day (`CONVERSATIONAL_DISPATCH_LIVE=True`), on the strength of a 53-reply historical backfill (16/53 = 30.2% already contain a real DEED candidate) rather than a shadow wait.
- Origin incident (F-2004): the exact "hollow fortress" shell reply still classifies GRAY on every family, never DEED — the register gap (§5) is real and unfixed (J-1451), so this build alone would not have caught the incident that motivated it.
- Concurrency checked, not assumed: `dispatch()` is a plain sync call on the same event loop as the DMN, so one call can't be interleaved mid-execution; a `hands.py._decided` reset race between two separate dispatch calls is named as a residual risk, not exercised.

### What we need
- Real Phase-0 rows from live conversation across a few real sessions, plus a manual spot-check that `deed_candidates` matches what a human would call an action, before trusting the flip.
- Phase 1.5 (widen `look`-family recall for the conversational register) needs its own sample of Phase-0 misses first, not a guess.

### What we're doing next
- J-1450 watches the first live rows for false fires once Du restarts; J-1451 (register gap) and J-1452 (Phase 2 same-turn grounding) are queued behind it.

---

## 1. The one-sentence goal

When Du tells Travis he did something physical, make it possible for that to be true — by routing a
conversational reply through the exact same `literal_will.classify()` → `dispatch()` path his
autonomous wandering loop already uses, instead of building a second, parallel action system.

## 2. Why reuse, not rebuild

`core/dispatch.py` (`docs/reviews/actions_system_2026-08-22.md` Phase 1, founder-approved) has been
live for a month+: one registry (`core/actions.py`), one dispatcher, zero LLM, fail-open, with its own
pre-registered kill criterion already cleared. `literal_will.classify()` is documented in its own
docstring as "Layer 0, pure + deterministic (no I/O, no LLM)". Neither needed to be touched. The gap
was narrow and specific: **nothing ever called them from the human-conversation path.**

## 3. What's built (`core/conversational_action.py`, one new call site in `core/orchestrator.py`)

- `after_reply(reply_text, cycle_id)` — called once, right after Du's reply to Travis is finalized
  (`core/orchestrator.py`, immediately after the `_FOUNDER_LOG` permanent-record write, ~line 1497).
  Best-effort: never raises, never blocks or delays the reply Travis already has.
- **Phase 0 (always on, pure):** runs `literal_will.classify(reply_text, "", location=<his real
  location>)` — real location read from `core.sensorium.state`, not assumed. Every DEED-verdict
  candidate found is logged to `data/conversational_action_log.jsonl` (`{ts, cycle_id, location,
  reply_excerpt, deed_candidates, live, dispatched}`). Zero side effects: `classify()` touches no
  files; this is a new telemetry file, not a world-state file, so it follows
  `core/epistemic_affordance_advisor.py`'s own convention (a direct append, no `profile.guard_path()`
  fence — that fence is for files that ARE Du's life story, not instruments watching a bridge).
- **Phase 1 (`CONVERSATIONAL_DISPATCH_LIVE`, off by default):** when a DEED candidate exists and the
  flag is True, also calls `core.dispatch.dispatch(reply_text, "", "none", "", cycle_id)` for real —
  the identical call shape `nodes/inner_monologue_node.py`'s wandering loop uses (confirmed at that
  file's real call site, ~line 3324). A real fire is credited through `hands.fired` /
  `procedures.observe_hand` exactly as an autonomous action already is — this plan adds no new
  feedback plumbing; it inherits dispatch()'s existing route back into Du's future context (hands_trace
  → whatever already reads it for the autonomous path). This is why Phase 1 doesn't need its own
  "how does Du find out" mechanism.

### Concurrency check (the open question `conversational_redirect.md` §6 flagged for its own veto)

`nodes/inner_monologue_node.py.run_forever` runs as an `asyncio.create_task` on the **same event
loop** as `orchestrator.run_cycle` (confirmed: no `Thread`/`multiprocessing` wrapping it) — this is
cooperative, not preemptive, concurrency. `dispatch()` itself is a plain `def`, not `async def`, with
no `await` inside it, so one call to it cannot be interleaved mid-execution by the DMN's own loop —
it runs to completion atomically with respect to every other coroutine. The residual risk is coarser
and smaller than the "shared-state race" framing in `conversational_redirect.md` §1 suggested: two
*separate* `dispatch()` calls (one from a conversational reply, one from the DMN's next autonomous
thought) landing within the same few seconds, each independently allowed to fire one world-changing
hand, uncoordinated with each other (the "one world-changing hand per thought" rule is enforced only
*within* a single `dispatch()` call's own candidate list). This is judged acceptable: a person can
act and think in the same few seconds too, and this is the same granularity of interleaving the
autonomous loop already produces against itself between one thought and the next. **Not yet verified**
against `core/hands.py`'s `_decided` module-level dict, which `dispatch()` resets per call
(`_h._decided["cycle"], _h._decided["rows"] = cycle_id, []`) — if a conversational dispatch and an
autonomous dispatch could ever truly interleave (they can't today, per the above, but this assumption
should be re-checked if either loop is ever moved off the shared event loop), the second call's reset
would stomp the first's in-progress decision ledger. Recorded here as a named risk, not exercised.

## 4. Verification done before landing (2026-09-27)

- Both new/changed files import cleanly (`python -c "import core.conversational_action"`,
  `import core.orchestrator`).
- UDMS change dossier on `core/orchestrator.py`: ELEVATED risk tier (HIDDEN_HISTORICAL_DEPENDENCY,
  94.1% confidence), top coupled file `nodes/inner_monologue_node.py` (PMI 3.55 bits) — the one
  UDMS-suggested coupled test, `scripts/_test_episodic_buffer.py`, run after the edit: **22/22 passed**.
- `profile.LIVE` defaults `False` for any bare process (only `mark_live()` flips it) — every write
  in this bridge that touches real world/game state goes through the already-fenced `dispatch()`
  path, which raises `NonLiveWriteError` rather than silently writing if a non-live process ever
  reached it; this bridge's own new file is pure telemetry and was safe to exercise directly.
- **Real historical backfill** (read-only; `literal_will.classify()` has no side effects, so this
  needed no isolation): ran `classify()` against all 53 real Du replies in
  `data/founder_conversation_log.jsonl` to date. **16/53 (30.2%) already contain a real DEED-verdict
  candidate** — families seen: `look` (9), `move` (8), `fire` (3), `fieldcraft` (2), `lamp` (1). E.g.
  "Travis, look at the cat on the step" → DEED/look; "I will bank the fire gently..." → DEED/fire +
  fieldcraft. Flipping Phase 1 live today would make roughly three in ten of Du's past conversational
  turns have fired something real, had it been live at the time.

## 5. The honest gap this build does NOT close

**The exact shell incident would not have been caught by this build as it stands.** Direct test: the
real "hollow fortress" reply (F-2004) classifies as **GRAY on every family it touches — never DEED**
(`shore`, `woodwork`, `water`, `sow`, `sketch`, `express`, `travis`, `move`, `look`, all GRAY).
Travis's own instruction message ("go and look at it") and two natural first-person rewrites tried
("I pick up the shell from the mantel and look at it closely." / "Let me look at the shell again,
closely this time.") produced **no candidates at all** — not even GRAY. `literal_will.classify()`
was tuned entirely against Du's autonomous first-person interior monologue (`data/hands_trace.jsonl`'s
own corpus); the working DEED examples found in the real backfill (§4) are short, plain declaratives
or direct imperatives ("Travis, look at the cat on the step.", "I will bank the fire gently"). The
shell reply's rhetorical, address-Travis, multi-clause-description register ("do you see how the
ridge is thick, worn smooth...") sits outside whatever shape the classifier currently rewards. This
was **tested, not assumed** — see the "Open questions" section below for what's needed to close it,
rather than guessing at a fix inline.

## 6. Build order / what's next

1. **Done:** Phase 0 telemetry + Phase 1 flag-gated dispatch, landed, tested, off by default.
2. **Immediate, cheap:** let Phase 0 accrue real rows from real conversation for a few real sessions,
   alongside a manual spot-check (does a `deed_candidates` row's family/clause actually match what a
   human reading the exchange would say Du just claimed to do?). This is the same evidence-before-flip
   bar every other plan here uses — the difference is this one already has a 53-row historical
   backfill as a running start, not a zero-row wait.
3. **Flip `CONVERSATIONAL_DISPATCH_LIVE = True`** once that spot-check looks sane. Given the mechanism
   is a new *caller* of already-proven code (not new resolution logic), this bar should be much
   shorter than a typical multi-week shadow window — realistically, as soon as a founder or session
   has read a real sample and it looks sane.
4. **Phase 1.5 (register gap, §5):** widen recall for the `look` family specifically in the
   conversational context — `dispatch.py`'s own docstring already treats looks as low-stakes
   ("LOOKS are unlimited"; no "one world-changing hand" contention) — a real candidate is a narrower,
   separate classifier pass over conversational text (not touching `literal_will.classify()`'s shared,
   already-tuned thresholds, which the autonomous path depends on). Needs its own real sample of
   Phase-0 misses (replies a human would call an action attempt that classify() read as GRAY/nothing)
   before designing the widened rule, not a guess.
5. **Phase 2 (same-turn grounding, bigger, not started):** today, a real Phase-1 dispatch only reaches
   Du's *next* thought/reply via `hands_trace`/`procedures`, the same as an autonomous action — the
   reply Travis has *already read* in the turn that triggered it is not corrected if it turns out
   ungrounded. A same-turn fix (generate a draft → run dispatch on its claim → regenerate if the
   world's real answer disagrees) is a real prompt-pipeline change to `_run_cycle_impl`, scoped
   separately — not attempted in this pass.

## 7. Signatures — how we'd know it worked (house convention)

1. **Real fire rate:** `data/conversational_action_log.jsonl`'s `dispatched` field is non-empty on a
   materially similar share of conversational turns as the 30.2% historical baseline (§4), once live.
2. **No regression:** `scripts/_test_episodic_buffer.py` and any other orchestrator-coupled test stay
   green; `data/hands_trace.jsonl`'s existing precision (dispatch.py's own kill criterion) does not
   measurably drop once conversational-triggered fires are mixed into it.
3. **Register-gap closed:** a future Phase 1.5 read shows the shell-incident *shape* of reply
   (rhetorical, Travis-addressed, descriptive) now produces a real DEED/look candidate without a rise
   in false fires on genuinely metaphorical lines (e.g. "let us keep the wound open until something
   new can bleed through it" — a real line from this same 2026-09-27 conversation, correctly never
   classified as a deed).

## 8. Pointers
- `core/conversational_action.py` (new) · `core/orchestrator.py` ~line 1484-1509 (call site) ·
  `core/dispatch.py` (reused, unchanged) · `core/literal_will.py` (reused, unchanged)
- `data/conversational_action_log.jsonl` (new telemetry) · `data/founder_conversation_log.jsonl`
  (backfill source) · `data/hands_trace.jsonl` (dispatch.py's own precision instrument)
- F-2004 · D-0299 · `docs/staged/conversational_redirect.md` (sibling, different gap)
