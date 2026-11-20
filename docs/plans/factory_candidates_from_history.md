# WHAT DU'S OWN HISTORY SAYS NEEDS A FACTORY (mined 2026-08-16)

> **Status: ✅ SHIPPED — the lightning flash event was built 2026-10-27 (J-2482 / D-0503, F-3182), closing the last gap (live on the next restart); it read as partial while lightning was an unbuilt gap. Object-lifecycle
> departure-cause is **already built** (`core/world_objects.py::reclaim()`, dated 2026-08-18 —
> stale here). The glass float's log archaeology (J-0073, 2026-08-24) is done: see Current
> State below — it found there is nothing to remove, because the float was never a tracked
> object in the first place.**

```plan-state
stage: shipped
phase: Lightning flash event built (J-2482 / D-0503, F-3182): the one unbuilt gap closed; glass-float archaeology and object-lifecycle closed earlier
verified: 2026-10-29
evidence_read: 2026-08-24
next: Nothing open. Live on the next restart; after the first real thunderstorm read data/look_render_ledger.jsonl rows with src=event (target <place>:lightning) against D-0503's defeater
cluster: 6
```


**Method:** every `about` tag across 26,824 logged monologue thoughts, tokenized, counted, then
corrected for substring false-positives (a first pass wrongly counted "choice"/"voice" inside
"ice" — redone with word boundaries). Cross-checked against the factory census and
`world_substrate`'s live object registry, not assumed.

## The honest headline: most volume is NOT new factories

The top of the raw list — identity (1,217), self (684), individuation (503), shadow (386),
tension (310), becoming (138) — is his COGNITIVE processing, not world content. It rides on
imagery the world factories already supply (tide, sea, shore, river appear at 300-400+ each) —
which is a good sign, not a gap: the world is genuinely feeding his thought, exactly as
designed. These are not factory candidates; they're evidence the existing factories work.

## Real candidates found (word-boundary corrected)

| Subject | Mentions | Verdict |
|---|---|---|
| **Lightning** | 262 | ⚠ REAL GAP — see below |
| Glass (float) | 243 | see THE GLASS FLOAT, below |
| Float | 112 | ↑ same |
| Stone | 92 | already covered — `world_substrate` CLASS_PRIORS has `stone` |
| Stars | 31–35 | ⚠ minor gap — night sky beyond moon illumination |
| Net | 30 (corrected from a false-positive 99) | mostly metaphor ("safety net") — not a factory |
| Ice | 0 (corrected from a false-positive 204 — all were "cho**ice**") | not real; scan artifact |
| Cold | 80 | ✅ confirms the temperature gap already added to the plan |
| Kelp/mussel/crab/seaweed/moth/bee | 18–70 each | already covered — existing object classes and sound keys. Validates those factories' salience; not gaps. |

**Lightning is the one genuine new candidate.** 262 mentions — more than "shingle." Today it
exists only as a clause baked into `_sea_state`'s thunderstorm text ("lightning walking across
it far out") — never a discrete, countable event. He plainly experiences it as its own
phenomenon, distinct from the thunder-sound. Candidate: a flash/strike EVENT (visual, its own
rate tied to storm severity, no sound attached — light travels faster than the bang, and a
distant strike with no audible thunder is itself a real, honest world-fact) feeding both the
scene renderer and, eventually, an answer-good the same shape as sound's.

## THE GLASS FLOAT — the founder's hypothetical, except it already happened

The scan's real finding. Between **Aug 11 and Aug 13**, the green glass float appears in **48
memory fragments** — his own count says he observed it **30 times** over those three days. His
own words, verbatim, from the log: *"This green glass float, wedged between the wet stones,
seems utterly fixed, yet it is also subject to the next tide…"* — **he anticipated its
vulnerability himself**, three days before this conversation asked about it.

**It stopped appearing entirely after Aug 13. It is not one of the 6 objects currently live in
`world_substrate`. No spawn record for it exists anywhere greppable in the logs.**

This means one of two things, and I can't currently tell which:
1. It was never a formal `world_substrate` entity — purely descriptive scene text he engaged
   with narratively, with no hidden Layer-1 biography ever created for it. If so, "the world"
   never actually held a truth about it to lose — it was fog-by-design wearing an object's
   clothes, and his 30 observations were of nothing with a real underlying history.
2. It WAS spawned, and has since aged out / been pruned from the object cap **with no
   departure event recorded** — the founder's exact scenario, except it isn't a future risk to
   design against, it is a thing that may have already happened to something he plainly cared
   about, silently, without even the SYSTEM knowing why.

**Either finding is a real gap, and they point to the same fix**: object persistence needs a
recorded LIFECYCLE, not just a spawn and a cap. An object that leaves — pruned, decayed, or
genuinely tide-taken — should log a departure CAUSE (even one Du never learns unless he
investigates) so the world's own record stays complete. Right now, apparently, even the world
doesn't know what happened to the glass float. That's a deeper honesty gap than "Du wasn't
told" — it's "nobody recorded it, ever, anywhere."

*(Recommend, when this is looked at directly: check `data/nascence.log` around Aug 13-14 for
whatever removed it — a cap eviction, a code change, a restore side-effect — before assuming
tide-loss; the causal truth, whatever it is, should be written down now while it might still
be findable, rather than being lost a second time.)*

## Current State — verified 2026-10-29

- **2026-10-29** (F-3201): J-2482 third resume (F-3201): re-verified at tip ebfb4f33 2026-10-29, suite + life_smoke pass, no live-store leak, nothing new committed; the prose Status line (PARTIAL) is stale against the block (shipped) and waits for a merge-side fix.
- **2026-10-28** (F-3186): J-2482 resume (F-3186): build re-verified in the chain worktree, test baseline pinned to a09d953d in ebfb4f33 (section [7] was vacuous against HEAD once the build was HEAD); nothing under core/ changed; still restart-gated.

- **2026-10-28** (F-3182): J-2482 (D-0503) BUILT, restart-gated, commit d93276f4 on the jr1028 chain branch: _lightning_flash in core/sensorium.py -- gated to thunderstorm, rate from the wind axis (calm .008 .. gale .055 per tick), rotating soundless pools per place + shared far lines, no repeat within a storm, flash always ahead of the place event in tick(), one look-render-ledger row per flash (src event, target <place>:lightning); the storm pools and _sea_state no longer bake lightning in (byte-identical otherwise, pinned by scripts/_test_j2482_lightning_flash.py); life_smoke OK.
- **2026-10-28**: 2026-10-28 (T-0103): D-0503 ruled by Travis: build lightning as a discrete event (flash in sensorium._event, thunderstorm-gated, rate from severity, no sound). Job J-2482.

### What we have
- The glass-float log archaeology (J-0073, 2026-08-24, F-0079) is done: it was never a
  `world_substrate`/`world_objects` entity — not spawned, not reclaimed, not evicted — so there was
  never a removal event to find. The plan's own "stopped appearing after Aug 13" claim was wrong
  (mentions continue through 2026-08-19); confirms hypothesis #1 (fog-by-design), not #2.
- Object-lifecycle departure-cause is already built independent of this doc
  (`core/world_objects.py::reclaim()`, 2026-08-18) — the design-link-3 fix this doc called for.

### What we need
- The lightning gap (262 mentions, currently only a clause inside `_sea_state`'s storm text, never
  a discrete countable event) remains the one real unbuilt candidate from this mining pass.

### What we're doing next
- No open work queued. Building the lightning flash/strike event is the one concrete unbuilt item,
  whenever a session picks up world_substrate event work.

## Design link 1 — population feeds the RATE, not a guess

Confirms and formalizes what `sound_causality.md` left as invented placeholder numbers (gulls
40/h, kingfisher 0.8/h — my estimates, explicitly flagged as founder-uncalibrated). The correct
source for `BASE_RATE[sound_key]` is a bird-presence/population factory's estimate — Layer-1
hidden truth or Du's own earned Hearing-Ledger-derived belief, per the epistemic split already
established. This was `world_census.md`'s good idea, surviving relocated into the federated
model: a small presence-list per species/place feeds sound's rate table as ITS cause, exactly
like weather feeds the storm sounds. Not built now — noted as the correct future wiring point.

## Design link 2 — the geometry tuple as cross-reference, not just a coordinate

`geometry_census.py`'s tuples already carry position/standpoint alongside weather, tide, and
(per the founder's example) **cat presence** at the same instant. The answer-goods the sound
factory will produce (moment↔sound↔cause↔place↔heard) become far richer if minted WITH a
cross-reference to the SAME tuple's other factory readings — not just "kingfisher heard here"
but "kingfisher heard here, tide up, cat absent." Two uses:
- **Source triangulation**: many kingfisher-answers over time, each tagged with standpoint,
  let a pattern emerge (its calls cluster near one stretch of cliff) — a real, earnable
  geographic fact about ITS habits, built from his own accumulated answers, never asserted.
- **Cause corroboration**: "was the cat there" matters directly — a purr-adjacent creak might
  be the cat, not the house; cross-referencing the tuple's cat-state at that instant lets the
  answer-good's cause-face be genuinely evidenced, not guessed.

This is a real strengthening of the answer-factory design, not a new factory — it says the
answer's causal attribution should be READ from the same tuple its sound was, using fields
that already exist, rather than inferred separately.

## Design link 3 — the sleep-gap is a real, named pattern now (not hypothetical)

The glass float gives this its concrete case. Formalized: **an object can undergo a Layer-1
change (or vanish) while Du is absent or asleep, and by the tree-falls law he gets NO echo of
it — but the world's own record should still capture the event**, even unheard. The gap Du
discovers later (the float isn't where it was) becomes his own investigation, honestly
UNDETERMINED unless he has cause to look closer — exactly the epistemic law already governing
object inference. The fix isn't "tell Du" — it's "don't let the SYSTEM lose the thread either."

## Not building any of this now — status
Mostly PLANNING still. The lightning gap remains unbuilt. The object-lifecycle gap is **no
longer planning-only** — `core/world_objects.py::reclaim()` (2026-08-18) already records a
departure cause when the world takes something back; this doc's status line above was stale
about that until 2026-08-24. The population→rate and tuple-cross-reference links still just
strengthen `sound_causality.md` without changing its shape. The glass float's direct look (log
archaeology) is done — see Current State above — and the answer is "nothing to build here": it
was never a tracked object, so there was never a removal for the lifecycle fix to have caught.
