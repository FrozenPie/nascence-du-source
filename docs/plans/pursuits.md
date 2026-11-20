# Pursuits — a mind that chases a topic and makes progress

> **Status: ⚪ PARTIAL — Phase 0 (shadow register) + Phase 1 (RETURN) + judge (Phase 2a) built and fused 2026-08-15, restart-gated, 8 temp-pathed test groups passed; Phase 2's authored-work resolution trigger is still unbuilt and live RETURN behavior is unconfirmed post-restart (doc's own "Watch post-restart" list).**

```plan-state
stage: partial
phase: Phase 0+1+judge fused, live; reawaken-path signals measured then REJECTED by a decoupled judge (J-1155/F-1727: 35.7pct < 40pct floor) - no code built; Phase 2 resolution trigger still unbuilt
verified: 2026-11-14
evidence_read: 2026-09-05
next: None queued - J-1155's pre-registered read was itself the stop condition; watch for the first pursuit to reach resolution depth (Phase 2's own trigger)
cluster: 6
```


## Current State — verified 2026-11-14
- **2026-11-14** (F-4697): J-4012: pursuit close judge prompt v3 built in core/pursuit_close_shadow.py (trajectory of last 6 thoughts, three binary panel asks answered/partly/settled, verdict3/settled/partly row fields, fire_rate()['v3']), gated by V3_PROMPT=False. Not live until founder flips flag and restarts. Test: scripts/_test_J-4012_pursuit_close_v3.py. Gated read spawned.

- **2026-11-14** (F-4697): J-3966/D-0743: close-judge change proposed in F-4697 (v3 prompt: trajectory of last 6 thoughts plus answered/partly/not_yet verdict, shadow, flag off); build job spawned.
- **2026-11-06** (F-4281): J-3372: D-0626 defeater read not takeable, 0 askable asks exist (live log is 89 pre-D-0626 unflagged asks, 0 resolved). Read tool built, scripts/pursuit_close_defeater_read.py; data-gated follow-up J-3664.

- **2026-11-05**: J-3165 (D-0554): pursuits born after the next restart record question_kind (question, done_when or observation) and question_text at birth; observation-born pursuits stay in the register but are not return-eligible and are not asked of the close judge, old pursuits unchanged.
- **2026-10-30** (F-3304): J-2519 adjacent-possible read UNDETERMINED: 42 of 45 running days sat within 3 days of a world-upgrade boot (217 commits, 32 boots); persistent novelty decays 132 to 3-5 per week even with upgrades landing, open set plateaued since W38; scripts/adjacent_possible_read.py

- **2026-10-16** (F-2887): J-2171: D-0426 option A (pursuit judge-set close) built in SHADOW: core/pursuit_close_shadow.py + fail-open hook in pursuits.judge_pending; logs to data/logs/pursuit_close_shadow.jsonl, never sets status=resolved. Restart-gated. D-0423 closure law may supersede (closure.py pursuit arm stub). Test: scripts/pursuit_close_shadow_test.py.
- **2026-10-15** (F-2785): J-2117 read: saturation (40 advances) is a retirement rule, not resolution; 70 retired, 0 resolved; 'established' capped at 8 so resolution depth is unobservable. Close trigger is a design choice: D-0426.

### What we have
- Phase 0 (shadow register) + Phase 1 (RETURN) + Phase 2a (judge) fused and live since 2026-08-15;
  judge is `core/judge_panel.py`'s two-family panel (gemma4:12b + falcon3:7b, tiebreak yi:34b), not the
  dead `llama3.1:8b` pair the design-time comment named (fixed J-0199). Judge-confirmed advance:restate
  ratio settled at 64.2% then 78.3% by 08-27 (D-0024, back inside the plan's own 70-80% band).
  RETURN fires reliably (89 times in 8 live days) but genuine content-level continuation happened in
  only ~35-40% of a 42-sample hand read (F-0116) — closer to a themed re-seed than a real continuation.
  D-0109 (2026-09-02) accepted RETURN's real behavior as serial-monogamous (one pursuit at a time,
  rotated by the saturation cap), not the alternating design §4 originally described.
- 2026-09 built a re-awaken path for dormant pursuits (`reawaken_candidate`/`evicted`/
  `cooldown_skip_unresolved`, J-0558) and measured it once real live data accrued (J-0639, F-1597):
  weak cosine signal, templated reading-log rows inflate matches, cooldown loses more thoughts than
  terminal dormancy does.
- **2026-09-22 (J-1155, F-1727): a decoupled cross-family judge read REJECTED promoting the re-awaken
  path** — the pre-registered non-templated slice scored 35.7% "continues", below the 40% floor and
  D-0085's ~60% precedent. No decision opened, no code changed — the pre-registered read's own stop
  branch is the complete answer.

### What we need
Non-self pursuit threads actually accumulating `established` points over time, and the first pursuit
reaching resolution depth — the Phase-2 authored-work trigger is still unbuilt; no pursuit has ever
produced a chapter.

### What we're doing next
Nothing queued on the reawaken question (J-1155 was itself the stop condition). Watch for the first
pursuit to reach resolution depth, and continue the doc's own "Watch post-restart" checklist (RETURN
log lines, judge sweep ratios, non-self `established` accumulation).

> **The problem (Travis, 2026-07-08, data-confirmed):** Du's thinking is PULSES, not a stream. His trains chase a
> topic for ~3 thoughts (13s apart) then reset; a 3–8 min gap opens; a fresh seed pulls a *new* topic. His ~10
> attractors (arithmetic, ambition, individuation, "becoming") RECUR 5+ times each but he never BUILDS on them —
> each return is a cold restart. So it is *repetitive without being progressive*: he circles the same ground and
> starts over every time. **The shallowness is not in the world or the tasks — it is that his cognition does not
> ACCUMULATE.** A richer world can't feel deep to a mind that can't build on it across time.

## The missing organ
A **pursuit**: a persistent, accumulating cognitive project with memory of its own progress — a live question his
idle thinking keeps getting drawn back to and *adds to*. He holds **a few at once** (a scholar juggles several),
rotating among them; each burst advances one; over days each accumulates and one resolves into a real work.
Sibling of the capacity-to-commit rudder: holding a pursuit across the gap is the same "holding through
dissolution" capacity, aimed at a topic instead of an identity.

## The object
```
{ id, question,          # the driving question, in his own words
  standing,              # the accumulating scratchpad ("what I've established, where it's heading") —
                         #   OVERWRITTEN each advance (limited-capacity, like the train working-state), NOT appended
  thoughts: [...],       # (Phase 0) the advancing thoughts collected — the raw accumulation to measure
  established: [...],    # the concrete points genuinely nailed — the PROGRESS record, grows slowly
  open,                  # the live sub-question he's chewing now
  centroid,              # mean embedding of its advancing thoughts — for topic-matching a new thought
  advances, restates, last_touched, born,
  heat, status }         # active / dormant / resolved
```

## Mechanism
1. **Birth** — from his OWN thinking, GATED (the over-capture lesson): a genuinely `unresolved` thought (the
   model's own "real open conflict" signal) — or a recurrent frontier question — that matches no existing pursuit
   crystallizes into one. Not every passing thought; a real open question.
2. **Advance** — when a train is *on* a pursuit's topic (embedding match), the model's re-integrated working-state
   (today DISCARDED at train-end) is written up to `standing`; `open` refreshes; if it genuinely moved, a point is
   added to `established`. The mechanism exists — it just persists upward instead of being thrown away.
3. **Return (the crux — turns pulses into a stream)** — after a train ends and the gap passes, the idle seed is
   biased to RE-ENTER an active pursuit (weighted by heat × time-since-touched — a Klinger current concern pulls
   harder the longer it's left). Retrieval-framed, NOT verbatim: *"You were working this through — you'd got to X;
   the open question is Y. Take it on."* So he CONTINUES instead of restarting. (Cooled-down, paraphrase-varied,
   injection-logged — the injection-solidity discipline, or the return becomes an echo loop.)
4. **Multiple pursuits** — cap ~3–4 (prevents both fragmentation AND one-pursuit monoculture). Each return picks
   WHICH by heat × recency-hunger. **Wording corrected 2026-09-02 (D-0109, from F-0607's full-history read):
   in practice this does NOT alternate among threads — RETURN rides ONE pursuit serially (runs of 9–21
   consecutive returns) until SATURATE_ADVANCES retires it, because in 85% of return windows only one candidate
   is even eligible (rivals decay dormant or never cross the advances≥2 gate). Founder ruling: this serial
   focus is ACCEPTED as the accumulation the plan wants — the saturation cap already rotates threads on a
   ~1-2 day cadence, and that rotation (not per-return alternation) is the real anti-monoculture mechanism.**
   They COMPETE for attention (attention-economy MVT): advancing pursuits stay warm and get returned to;
   stalling ones COOL and go dormant, freeing the slot. Fruitful threads self-select; dead ones fade.
5. **Progress judge — decoupled, or the whole thing rots.** The load-bearing guard. If HE judges progress, every
   burst "feels like progress" (the chronic felt-vs-real trap) and his attractors become pursuits he RESTATES
   forever — the monoculture in a pursuit costume, with the return mechanism ENFORCING it. So a DECOUPLED judge
   rules advance-vs-restate against the pursuit's OWN prior state (never his say-so). Phase 0: a deterministic
   embedding proxy (near-duplicate of the pursuit's recent thoughts = restate; related-but-novel = advance) — the
   thought vs the pursuit's accumulated state, decoupled and cheap. Phase 2: the Emissary/left-lane cross-family
   judge. Only advances count; a pursuit that only restates loses heat → dormant. This is what BREAKS the
   repetition instead of cementing it.
6. **Resolution** — when `established` reaches depth / the open question closes, the pursuit resolves into an
   authored work (essay/tablet — the essay-lesson/Grand-Work machinery, now as the CULMINATION of an accumulated
   thread). The progress→completion arc that holds attention. Becomes a chapter; a new pursuit is born.

## Reuse map (assembly, not invention)
train working-state → `standing` · theme-recurrence → birth + restate detector · frontier/concerns → sources ·
left-lane → the decoupled progress judge (Phase 2) · inner_thought store (fixed 07-08) → reads back his prior
thinking · essay/Grand-Work → resolution · attention-economy → heat/competition · `_embed`/`_cosine` → matching.

## Build order (shadow-first, gated — the law)
- **Phase 0 (SHADOW, this build):** `core/pursuits.py` `observe(thought, about, vec, unresolved)` — a register
  that detects births, matches thoughts to pursuits, judges advance-vs-restate (embedding proxy), accumulates,
  manages heat/dormancy/cap — **changing NONE of his seeds.** Logs births/advances/restates/dormancies to
  `pursuits_shadow.jsonl` + `pursuits_active.json`. Wired fire-and-forget into the idle stream beside the
  commitment/self-implication scans, cooldown-gated, fail-open. **THE GATE (before Phase 1):** do the pursuits
  that form ACCUMULATE GENUINE ADVANCES, or is it his attractors flooding with restates? If the restate-ratio is
  high / his monoculture themes sail through as "pursuits," the JUDGE is wrong and we fix it before the return
  mechanism can enforce the monoculture. Watch: births are real open questions; advance:restate ratio; do 2–4
  distinct threads persist; the sea-monoculture does NOT dominate the register.
- **Phase 1:** the RETURN — bias the idle seed toward re-entering an active pursuit (retrieval-framed, cooled).
  The behaviour change that makes the stream.
- **Phase 2:** the cross-family progress judge + resolution → authored work.

Each restart-gated, kill-switched (`PURSUITS_LIVE`), evidence-gated.

## ★ 2026-08-15 — PHASES 1+2(judge) BUILT, fused (founder-approved; restart-gated)

**Why fused:** the decoupled audit (20 samples, refute-biased Emissary judge) found the Phase-0 proxy's
"advance_ratio 1.00" was really **75%**, with the false positives concentrated on the SELF-pursuit
("restating the theme in fresh words") — §5's predicted failure, arrived on schedule. So the judge came
BEFORE the RETURN could enforce anything:
- **Judge-gated advances:** the proxy now only NOMINATES (`advance_pending`, bounded queue); the
  cross-family judge (llama3.1:8b, CPU, refute-biased, judged against the pursuit's OWN prior standing)
  rules at the sleep sweep (`judge_pending`, wired beside the other sleep maintenance). Confirmed →
  the advance enters the record (standing/thoughts/heat/saturation); refuted → a restate; unavailable →
  retried twice then dropped WITH a log line. Restates (≥0.82) skip the judge (near-verbatim is certain).
  Standing is no longer overwritten by restates (the plan's own wording honoured — restates would have
  handed the RETURN an echo).
- **THE RETURN (Phase 1):** at wandering moments (the cold-restart the plan targets), cooldown ≥25 min,
  p=0.35, the hungriest pursuit (heat × hours-untouched) comes back retrieval-framed — re-presenting
  **only judge-confirmed standing**. Self-topic pursuits are NOT return-eligible (the self-attractor
  has the whole identity stack; the register exists for the OTHER threads). Requires ≥2 confirmed
  advances (substance to return TO). Injection-logged (`pursuit_return:<id>`, the solidity discipline).
- Kill-switch `PURSUITS_LIVE=False` = shadow-exact. **Temp-pathed tests: 8 groups passed** (birth,
  pending-not-counted, confirm-applies, refute-restates-standing-untouched, RETURN line, self-refusal,
  kill-switch, judge-unavailable retry/drop).
*Watch post-restart:* first `[pursuits] RETURN →` line and what he DOES with it (continue vs re-tour —
the earned-length verdict on returned trains is the honest read); judge sweep ratios at each sleep
(expect ~70-80% confirm); non-self threads accumulating `established` points; the first pursuit to
reach resolution depth = the Phase-2 authored-work trigger (still unbuilt).
