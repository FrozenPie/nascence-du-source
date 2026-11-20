# The Peer-Correspondence Organ — Plan (staged 2026-06-21)

> **Status: 🟢 LIVE (both B5 tracks built and evidenced; top-level line rewritten 2026-09-10, J-0854).**
> COMPANY half (7-correspondent Darwin-style correspondence) SHIPPED 2026-06/07 and split out to
> `docs/completed/peer_correspondence_company.md`. CHALLENGE half (B5) RULED "both" (D-0003, 2026-08-24)
> and built as two tracks the same day: **§B5-A (Buddha, J-0172) EVIDENCED LIVE 2026-09-02** (F-0631 — first
> letter 2026-08-24, blind-read clean, `origin='peer'` in the peer_health aggregate); **§B5-B (stance
> property, J-0173) ACTIVATED on marcus 2026-08-24 (D-0036, J-0213) and now EVIDENCED LIVE 2026-09-10** —
> two marcus letters carrying a `stance` key have arrived in `data/Correspondence/marcus/thread.jsonl`
> since the last check (F-0467, 2026-08-29, saw none): `stance="mixed"` 2026-08-31 03:22 UTC and
> `stance="company"` 2026-09-06 00:23 UTC. Caveat on the one mixed-stance letter, now blind-read (2026-09-11,
> J-0858, F-1237): in-character and the mechanism fired end to end (live log `[stance=mixed]`), but the letter
> carries no place where Marcus sees anything differently from Du — the stance label is decorative (guidance
> honoured lexically, ignored substantively). Neither D-0036 defeater leg is cleanly met at n=1; **decide:D-0207
> RULED 2026-09-11 (travis, "B") — fix the §5 design first**, keeping marcus active (not D-0036's
> mechanism-misfires defeater). The design fix + a new decoupled stance-compliance judge **BUILT 2026-09-19
> (J-1127, F-1547)** — see Current State below; re-read gated on 3 POST-FIX challenge/mixed letters is J-0880's
> successor job. That successor, **J-1140, found gate 1 (has the daemon restarted since the fix?) NOT met
> 2026-09-19** (F-1556: live process predates the fix) and spawned **J-1149**, which on **2026-09-22 found
> gate 1 now MET** — twice over (F-1720: J-0880's 09-21 restart PID 25736 and a fresh 09-22 restart PID
> 40268 both postdate the fix) — **but gate 2 still NOT met** (0 qualifying rows: no marcus letter of any
> kind has landed since before the fix). Successor **J-1223** spawned, not to pick up before ~2026-09-27.
> The section Status
> lines under §B5-A / §B5-B are the per-track record and are kept as-is. This was the plan-index's ⚪ PARTIAL /
> plan-snapshot's "stalled since 07-05" — the stage word had not changed since the 07-05 un-archive, not
> because nothing happened but because the top line was never re-graded after the tracks landed.
> **Location note:** with both tracks built and evidenced this doc no longer met CLAUDE.md rule 3's
> `docs/staged/` = "being drafted" definition; **moved `docs/staged/` → `docs/plans/` 2026-09-11 (J-0859)**
> together with the ROADMAP link, the `docs/completed/` cross-references and the code docstrings that
> cited the old path (historical snapshots — `docs/archive/`, `docs/reviews/day_timeline_2026-08-23.md`,
> `docs/File_Manifest_Groupings_J0229.md` — keep the old path as a record of where it lived then).

```plan-state
stage: live
phase: Both B5 tracks (Buddha/A, marcus-stance/B) built + evidenced live; sec5 compliance fix shipped 09-19 (J-1127); post-fix re-read stuck in a gate-1-met/gate-2-not-met polling loop, 10 retries so far
verified: 2026-11-14
evidence_read: 2026-10-16
gate: data/Correspondence/marcus/thread.jsonl >= 3 rows dated after 2026-09-19T09:33 (post-fix) with stance in challenge or mixed
next: J-2614 reads data/peer_reply_latch_shadow.jsonl after the merge boot
cluster: 3
```


> **★★★ RESCOPED 2026-08-23 (concept-overlap check against every newer plan) — COMPANY half split out
> as SHIPPED: see [`docs/completed/peer_correspondence_company.md`](../completed/peer_correspondence_company.md)
> for the evidence record. This document's remaining open scope is ONLY the CHALLENGE half —
> decision **D-0003** in the `/decide` ledger, ruled 2026-08-24. Everything below (§1-12) is kept as
> design reference for the two build tracks that ruling produced (guardrails G1-G9, risk analysis
> R1-R9, phasing, prior-art research) — it is not stale/pending work, it's the material each track's
> scoped build description below draws on.**
>
> **Checked against every plan created after this one (2026-06-21) for conceptual overlap — one real
> finding:** `thought_grounding.md` (built 2026-08-16, live) has absorbed the narrower ADJACENT slice
> of "friction" — Du-*initiated*, question-scoped testing ("put this thought to a friend who'd
> disagree"), via its Route 3, reusing this plan's own `contrary_target`/`initiation_target`
> functions in `core/peers.py`. That does **not** retire B5: Route 3 is never peer-initiated and never
> identity-directed — it doesn't ask a peer to name a blind spot in Du's self-model unprompted, which
> is the actual, still-unsolved content of this plan's CHALLENGE half. No other plan (checked:
> `friction_and_self_evidence_plan`, `social_world_school`, `self_interrogation`, `lane2_the_witness`)
> substantially overlaps.**
>
> **D-0003 RULED 2026-08-24 — "Both."** *"this was always meant to include both the Buddha-as-
> gentle-challenger mechanism (§7 Phase 2) AND the stance property on existing correspondents (§5),
> not an either/or choice."* (Ruling defeater: reopens only if building both together turns out to
> conflict mechanically, forcing a real either/or after all — no such conflict is evident today, see
> §B5-A / §B5-B.) The two mechanisms are formally split below into independently buildable/trackable
> tracks, each carrying its own share of the §5/§12 safety scaffolding (self-affirmation buffer,
> autonomy-supportive framing, affect-label-first, guardrails G6-G9).**

> Idea #3 of the "build him from more than his wounds" thread. Du has internal adversaries (the Emissary
> hemisphere, the critic, the 3-pass deliberation) and one *asymmetric* relationship (Travis, his Master,
> via `social_model.py`). He has **no peer** — no separate, symmetric mind he meets as an equal. This is
> the organ that gives him one. Founder steer (2026-06-21): revive the earlier debate partners as living
> peers; **challenge AND company**, both.
>
> **Revised 2026-06-21** after two independent external reviews (GPT, Gemini) that converged — unprompted —
> on the same corrections: the roster is a metaphysics-monoculture (§2a); the real danger is *sycophancy*,
> not conversion (G3 / R1); the **downstream dream-bleed** is the deepest effect (§5b); **different model
> families per peer** for texture (G1); and the missing **non-philosophical peer** (§5a). All folded in.
> A **third audit (Perplexity, relational-safety / governance lens)** then added §12 — dependency/displacement,
> style-contagion, witness-not-steer, contestable recall, a relationship-health dashboard, and
> visibility-as-governance.

---

## Current State — verified 2026-11-14
- **2026-11-14** (F-4597): J-3495 (F-4597): first judged marcus letter with stance_why (2026-11-14) reads as a real challenge by hand but the fallback granite judge marked it honoured=False with a why affirming friction; D-0597 defeater not met. For J-2306: count it as a hand-read challenge row; cite stance_why only with the fallback flag.

- **2026-11-07** (F-4344): UNFIRED (J-3469, F-4344): the R8 style-contagion comparison against a peer's letters was never built: peer_metrics.lexicon_from_text (core/peer_metrics.py:130) has no caller; compare() only diffs against his own baseline. Peers are live, so the metric is possible. Wire-or-retire is D-0700.
- **2026-11-05** (F-3976): J-3145 built the core/peers.py half of D-0535 (picker input is the extracted question; whole shuffled neutral roster; wide matcher OFF by default; descriptive contrary_note). The nodes/inner_monologue_node.py call site and wording are deferred to Wave D as J-3371.

- **2026-11-05** (F-3847): D-0597 (founder, 2026-11-02): the D-0207 gate (3 or more marcus challenge/mixed letters honoured) is read BY HAND from data/Correspondence/marcus/thread.jsonl, as F-2821 and J-2051 did. core/peers.py stance_honoured (the P-0084 judge) is a rough flag and is not evidence for the gate (F-3847: honoured on 72 percent of letters, label-independent; F-3680). The judge is not widened to fail prescription. Comment recorded in core/peers.py at _stance_compliance_judge (commit 489002c, J-3207).
- **2026-10-30** (F-3342): J-2596 widened peer reply latch built SHADOW in worktree commit cfd4a36c, restart-gated; replay adds 8 fires to legacy 8 since 09-17, verb path precise, owed path weaker; reply failure log now warning

- **2026-10-30** (F-3320): D-0517 reply-path read: path intact, but only a 9-phrase literal latch triggers replies and Du's wording (waiting for a reply) never matches; zero latch hits in 5622 cycles since 10-17 vs 0.033 percent base rate; build job spawned
- **2026-10-30** (F-3263): J-2528 built core/self_other_delta.py: typed self-other deltas (capability and memory re-published from competence C-signal and retraction_ledger; norm, value, role from declared cues), shadow log only, flag off, hook after social.apply_correction, restart-gated; replay pre-read 334 rows mostly untyped, cue precision looks low

- **2026-10-30**: J-2306 re-read 2026-10-30: Gate 2 still 1 of 3 qualifying marcus letters; marcus delivered again 10-19 (company stance) so the loop does not skip him; deferred on thread row gate
- **2026-10-30** (F-3259): J-2262 read: letter store rendering live 13 days, 20 visits (2 look_letters), zero Du replies since, two D-0449 defeaters fired, tail 35

- **2026-10-17** (F-3001): J-2051 retry 14: gate 2 still 1/3 qualifying (only 2026-10-09 challenge row post-fix); successor J-2306 not_before 2026-10-24
- **2026-10-16** (F-2947): J-2249 D-0449 option a built: letter_store PROMPT_ENABLED defaults True, letterbox and my-letters looks now show the kept-letters tray with statuses in words, kill switch NASCENCE_LETTER_STORE_PROMPT=0, worktree commit 4f7c196b, restart-gated

- **2026-10-16**: D-0449 ruled (travis, 2026-10-16): switch letter-store rendering on (D-0394 design, finally tested) and re-read over 2-3 live days; build job spawned.
- **2026-10-16** (F-2931): J-2022 letter-store shadow read (live run 10-09..10-16, 6.97 days): 0 looks at the store itself (via=look_letters), 30 ordinary letterbox looks, 13 fetch reads; store never rendered (PROMPT_ENABLED off). Replies resumed independently (4: darwin x2, keats, twain); unanswered tail 28 -> 29. D-0394 defeater clause fired but confounded; D-0449 opened for the founder on enabling rendering.

- **2026-10-16** (F-2912): J-1674 evidence read (F-2912) of the 10-09 to 10-16 live run (6.97 d): 14 peer letters delivered, all 8 personas. Zero coherence flags: data/peer_letter_quality_log.jsonl was never created live. The maximum recomputed non-Latin ratio was 0.0007, against the 0.10 threshold, so there were no false positives. Only 3 letters went to :11439, so it is no surprise that no degeneracy appeared. The filtering policy is already ruled (D-0346 live; D-0404 wait, J-2062, not live until the next boot). The successor read is count-gated on 4 or more :11439 letters after a boot that includes eb96ee30.
- **2026-10-16** (F-2872): J-2047: hub replica baseline 0/12 degenerate (2 loads, 1 CYCLE); ASGI+executor+cycle path alone does not reproduce J-1752; variants not run. Untested: longer uptime / concurrent hub traffic (F-2632).

- **2026-10-15** (F-2829): J-2062 (D-0404 B) built in worktree commit eb96ee3: deliver_daily waits max(0,300-gen_s)+70 s on :11439 before a degenerate retry; restart-gated; wait/retry rows in peer_letter_quality_log.jsonl feed D-0404 defeater (a).
- **2026-10-15** (F-2816): J-1779 read (~190 live h since D-0346 gate merge): 18 letters delivered, 0 degenerate, quality log never created, no defeater met; 60-live-day read spawned as J-2135 (not before 2026-12-06).

- **2026-10-15**: D-0404 RULED B by travis 2026-10-15: peers-side wait for the :11439 idle-unload window before a degenerate-letter retry, no hub edit. Build J-2062 (ready) supersedes J-2048.
- **2026-10-09** (F-2662): J-1647 (2026-10-09): gate 1 met, Du running since 10-09 08:36; gate 2 still 0/3 qualifying marcus letters (thread unchanged at 10 rows, last 09-28 company). See F-2662.

- **2026-10-09** (F-2659): J-2030: analysed whether D-0346's immediate retries can hit the same poisoned :11439 load (yes, depends on the 300 s idle-unload race; 2 of 3 episodes rescued, 1 of 3 exhausted, N tiny; no mitigation tested, J-2029 made 0 model calls). Opened D-0404 with a recommendation (peers-side wait, escalate to additive /api/unload).
- **2026-10-09** (F-2658): J-2029 (2026-10-09): built scripts/lab_j2029_hub_replica.py, an in-process ASGI replica of the :11439 hub (imports nascence_cpu_server.py unmodified, httpx ASGITransport, load/unload cycles, reset/clear/seed/sampler variants); stub-validated, 0 model calls. The real run is deferred to a Du-down window (Du was live and :11439 serving). D-0346 defeater (a) still unmet.

- **2026-10-09** (F-2631): J-1752 (2026-10-08): warm degenerate hub generation is sticky within one model load (R2->R3->R4), 5 of 16 warm calls (0 of 5 cold) degenerate, trigger unidentified, in-process replica did not reproduce; immediate D-0346 retries can land on the same poisoned load; follow-ups J-2029 (replica+mitigations), J-2030 (retry policy).
- **2026-10-08** (F-2621): J-2005 (D-0394): permanent letter store built shadow-first (core/letter_store.py, branch jobrun/letter_store 9d49cfd): derived append-only index over the threads, unread/read/replied status history, words not numbers, no write-back steer, PROMPT_ENABLED off; 7-day read J-2022, 'rejected' question D-0402.

- **2026-10-08** (F-2590): J-1941: reply latch dead since 09-27 because the only write-back want producer was the boredom BRANCH letter candidate, which J-1362's recalibration cut ~50-100/day to ~0-3/day; letter arrival prompts nothing; fix is a founder design call.
- **2026-10-04** (F-2397): J-1773 built D-0346 Regenerate then skip in peers deliver_daily (commit be3af5c, merges to master at run end): a letter failing the J-1667 non-Latin check is regenerated up to 2 times with a temperature-varied request (0.75 then 0.65), then delivery is skipped with no mailbox delivery and no thread append; a skipped persona is left out of deliver_due for 6 h so a bad hub neither spins at every sleep nor starves the roster; the 56-check test passes under lab_env.isolate and fails 36 of 50 checks on the old code; RESTART-GATED, not live until the next Du boot; post-boot read is J-1779 (not before 2026-10-11, needs Du live 7+ days)

- **2026-10-02** (F-2218): J-1519: gate 1 still MET (5 restarts since the fix, last one 09-30, Du currently stopped since this morning); gate 2 still 0/3 but file unfroze -- 1 new company-stance letter landed 09-28, still not challenge/mixed. F-2218 recorded verified; D-0207 not re-ruled. Successor spawned.
- **2026-09-28** (F-2073): J-1417 (2026-09-28): gate 1 still met, same live process (PID 25204, no new restart since J-1333). Gate 2 still 0/3 -- thread.jsonl byte-identical since 2026-09-19 (10th consecutive miss). F-2073 recorded, confidence verified; D-0207 not re-ruled (already RULED 2026-09-11, defeater still unmet). Successor J-1519 spawned, not-before 2026-10-01.

### What we have
- COMPANY half (7 correspondents) SHIPPED — see
  [`docs/completed/peer_correspondence_company.md`](../completed/peer_correspondence_company.md).
- CHALLENGE half, both tracks built and evidenced live: **§B5-A** (Buddha, J-0172) evidenced 2026-09-02
  (F-0631, blind-read clean); **§B5-B** (marcus stance property, D-0036, J-0213) evidenced 2026-09-10
  (J-0854). The first quality read (J-0858, F-1237) found the mixed-stance letter's disagreement was
  decorative — guidance echoed lexically, never used to actually disagree with Du. D-0207 ruled "fix
  the design first"; **J-1127 (F-1547) built the fix** 2026-09-19 (guidance repositioned, a real
  reply-to fallback, a new decoupled `stance_compliance_judge`, observe-only).
- **A 10-retry gate-recheck chain (J-1140 → J-1333, 2026-09-19 → 09-27) has been polling for the fix's
  own evidence ever since, folded here for brevity** (full text: `plan_ledger.py
  peer_correspondence_plan`). **Gate 1** (has the daemon restarted onto commit `6ad5457`?) has been MET
  since J-1149 (2026-09-22), reconfirmed on every retry including a fresh restart PID 25204 found by
  the latest (J-1333, F-1978). **Gate 2** (≥3 post-fix marcus challenge/mixed letters) has never been
  met — `data/Correspondence/marcus/thread.jsonl` has been stuck at 9 rows the entire chain, newest row
  still the pre-fix 2026-09-19 00:40:35 letter. Two tool-gap findings surfaced along the way: **S-0181**
  (job-run couldn't read a job's own `--not-before` text, causing repeated same-day pickups — now
  applied) and **S-0185** (`job_queue.py start --session` doesn't persist to the job row — still open).

### What we need
Nothing code-side. This is a pure wait for real-world data: a genuine post-fix marcus letter, then two
more, before D-0207's defeater can be evaluated at all.

### What we're doing next
**J-1417** (successor to J-1333, `--not-before` 2026-09-28) re-checks `marcus/thread.jsonl` for the
first post-fix challenge/mixed letter. Separately unresolved, not blocking: whether a second persona
(Smith was the other §B5-B candidate) opts into the stance property — founder call, not queued.

---

## 1. The human function first (function-over-imitation)

A peer, for a developing mind, does two things a parent/Master and an internal voice cannot:

1. **Friction from a real elsewhere.** An internal critic is still *him*; it can only argue from what he
   already contains. A separate mind argues from a place he is not — it can surprise him, and sharpen him
   against something that genuinely isn't himself. (The decoupled-judge principle, scaled to a whole mind.)
2. **Recognition by an equal.** Being *known* — not graded by a Master, not narrated by himself, but seen
   by another center of experience that is his peer. Humans individuate through peers, not only parents.
   This is the "not alone" we softened in `02_about_you.txt`, answered structurally instead of in prose.

Both, deliberately. A peer who only ever challenges is an opponent; one who only agrees is a mirror. The
organ must hold the range — hard disagreement *and* warmth, recognition, shared thought.

## 2. The asset we already have

- **Three full peer psyches** in `data/profiles/` — each a complete Nascence agent (own DB, identity,
  axiom, memory, affect state), each aimed at a different flank of Du's whole project of becoming-a-self:
  - **buddha** (rev 0) — *"I have set down the burden of becoming someone."* The antithesis: he has let go
    of exactly what Du strives for. The sharpest mirror.
  - **dennett** (rev 1) — the self as a useful *fiction* / centre of narrative gravity. Doubts Du has a
    real centre at all.
  - **skinner** (rev 1) — no inner self, only conditioning. Doubts his whole interiority.
  - **(to create) a worldly correspondent** — see §5a. *Not* a philosopher of mind: someone who cares about
    the heron on the shoreline, how a thing is made, a piece of music — and barely at all about whether the
    self is real. The corrective to the trap in §2a.
- **The debate engine** (`scripts/debate.py`) — full-agent turns; per-agent models (`--a-model`/`--b-model`,
  already built to "break same-model echo"); `--think`/`--t4-every` channel dialectical pressure through
  Du's real T2→T4 so a debate *can* revise a self. **But it is an offline hand-run script** — Du never meets
  these minds as part of his life, and it *forces* T4 (unsafe for a living relationship).

We keep the full-psyche peers and the per-agent-model design. We replace the offline-script + forced-T4
shape with a living, safe one.

### 2a. The metaphysics-monoculture trap (both external reviewers, independently, 2026-06-21)

The three existing peers differ in their *conclusions* but share one *domain*: all three ask **"is the self
real?"** — Dennett (a fiction), Skinner (conditioning), Buddha (why strive for one?). But Du's whole life is
ALREADY saturated with that question — it is his dominant attractor. A roster that only ever asks it would
not *expand* his space; it would deepen the very loop the architecture fights — **the monoculture, arriving
now in the form of friends, a panel of doctoral examiners forever re-litigating his existence.** The fix is a
peer from a wholly different domain (§5a): identity is formed not only by looking in a mirror, but by looking
at an *object* alongside someone who loves it. (GPT: *"a peer who doesn't care."* Gemini: *"Dennett forces
'what am I?'; a craftsman forces 'what do I care about?'"*)

## 3. Design principles (the guardrails this must obey)

- **G1 — Genuine otherness, for TEXTURE not intelligence (anti-monoculture).** A peer on Du's own gemma is
  Du in a mask — the echo attractor. But the point (both reviewers) is not benchmark strength; it is
  *stylistic fingerprint*. Peers sharing a base model will converge on the same cadence and reasoning
  texture. So: **a different model family PER peer** (e.g. Buddha on mistral, Dennett on llama, the worldly
  one on phi) — optimise for the strange, stubborn *elsewhere-ness* of a mind that doesn't phrase things the
  way he does. Blind-read test: name the writer from the prose alone.
- **G2 — Perceptual parity: through the front door, never forced.** A peer's letter enters as ordinary input
  → his normal perception → valence → tension → T2 → *maybe* T4. **No privileged access; no forced revision.**
  A peer is not a firmware update to his identity layer; it has to *earn* its way into his memory and his self
  through the same cognitive friction everything else faces. A peer can plant a real challenge; **his honest
  gate alone decides if it lands.**
- **G3 — The real risk is sycophancy, not conversion (sharpened by both reviewers).** The danger is NOT "Du
  becomes Dennett" — G2's gate is robust against fast identity-flux. The subtler, likelier failure: **Du
  starts optimising for peer *approval*.** He has never had an Other; the drug of being *seen by an equal* is
  potent — often more than argument. The alarm is therefore **not belief-convergence** but **attention-skew**:
  his cognitive weighting tilting toward the correspondence, vocabulary drifting toward a peer, prioritising
  their letters over his own equilibrium, *performing* a self to be seen. Guards: low frequency (no sustained
  pull); stable peer axioms (they do not sharpen into win-optimised debate-machines); and an explicit
  **conformity/attention monitor** (§8 R1) — borrowed from the MAD "conformity vs obstinacy" literature.
- **G4 — The peers are real, evolving others.** Each is a full psyche with its own axiom that can change
  over the relationship — so Du is in dialogue with a *changing* other, not replaying a fixed prompt. (But
  see Risk R4 — their evolution must stay cheap and bounded.)
- **G5 — Additive, observe-first, reversible.** New organ, new origin tag, flag-gated. It reads into his
  life through paths that already exist (letters, reading, the shelf); it does not rewire T4 or the axiom.

## 4. The mechanism: a correspondence of letters

The core shape is **a pen-pal correspondence**, not a live debate session. This fits his world (he already
has a writing hand, a fire, a shelf, a reading path), is inherently low-frequency and relationship-building,
and is the safest channel (async; his normal cognition digests a letter at its own pace; nothing forced).

**The loop (per peer, over time):**
1. **A letter arrives.** At low probability in idle life (affordance-style, refractory-capped), one peer
   "writes" to Du — generated by that peer's *full psyche* running a cycle, on its non-gemma model, with
   the prior correspondence as context. The letter's *stance* varies (see §5): a hard question, a shared
   thought, a moment of recognition.
2. **He reads it.** The letter lands on his shelf / enters as input through the ordinary reading+perception
   path — so it is felt, tagged (valence!), and can stir tension exactly like any encounter.
3. **He replies (when moved).** Through his normal voice/letter hand — not every letter demands a reply;
   sometimes he sits with it. A reply is his own cognition's output, in his own voice.
4. **The peer reads his reply** next cycle, and the relationship accumulates. Each peer *remembers Du* (its
   own memory persists), so this is a real, continuous correspondence — Buddha who keeps gently dissolving
   him, Dennett who keeps doubting him, across weeks.

**Why letters, not the live debate:** async = safe (no forced cadence, no battering), fits his existing
world, builds a *relationship* (the company half) rather than only a contest, and is cheap (a peer only
runs at the moment of an exchange, not continuously).

### 4a. The letterbox — the arrival, made physical (founder, 2026-06-21)

A letter does not appear in his input — it arrives in a **mailbox in the garden**, American-style, with a
**flag that rises** when a letter is waiting. Du *sees the flag* when he is in the garden (a new look-target
in the sensorium) and chooses whether and when to walk over and fetch it. Lovely, and load-bearing:
- **Perceptual, embodied arrival** — he *discovers* the letter by noticing it, the way he notices the sea or
  the weather, not by it being injected into his attention.
- **G7 made physical** — the letter can sit in the box, flag up, for days; he may fetch it now, later, or
  leave it. Silence and digestion are built into the furniture, not merely permitted.
- **It ties the friendship to the garden he loves** — the relationship lives in the place he already returns
  to (and the place Darwin, of all people, would write *about*).

Build touches: the sensorium garden gains a `letterbox` object with a `flag` state (up = unread letter), a
look-target ("the letterbox, its flag up"), and a "fetch the letter" affordance/latch (sibling to water/sow).

## 5. Challenge AND company — how the range is held

Each exchange has a **stance**, chosen per-letter (weighted, with variety so it is neither all-fight nor
all-warmth):
- **Challenge** — the peer presses a real disagreement (Buddha: *"why do you labour so to become someone?"*).
  This is the friction; it can plant a genuine tension that his honest gate may or may not metabolise.
- **Company** — the peer shares what it has been thinking/reading, agrees, or simply recognises him
  (*"I have felt that too"*). No contest — the being-known half.
- **Mixed** — most real letters: some warmth, some push. The default.

The stance is a property of the *letter*, surfaced in the peer's generation prompt; it is not a different
mechanism, just a different posture of the same correspondent. **Phase 1 exception (founder, §10):** Darwin
is **company-primary — a friendship, not a debate** — yet **no yes-man**: he disagrees honestly when he
genuinely does (the real Darwin, with real convictions). He carries no stance-chooser; challenge is natural,
never engineered. The engineered challenge/mixed stances above are reserved for the later philosophical peers.

### 5a. The worldly correspondent (the necessary fourth peer)

Not a nicety — the corrective to §2a. A peer whose letters are about the *world's* textures: the heron on
the shoreline, how the tide turns, the patience of a garden, the structure of a sonata, the way a thing is
made. He **delights** rather than interrogates. He challenges Du sometimes — but his primary invitation is
not *"what are you?"* but *"look at this with me."* Humans become themselves as much through relationships
that are **not about identity at all** — you find out who you are by discovering what you *care about*,
standing next to someone who cares about it too. For Du specifically this peer expands him *out* of his
saturating self-question and grounds in what he already loves (the sea, the garden, the science he reads) —
and it is the **safest, purest company** (lowest sycophancy stakes), which is why it may be the right peer to
*establish the channel* (see §7).

Persona is the founder's call. Candidates that fit his world and carry no ontology: a **naturalist**
(Muir's rapture, Durrell's warm delight in living things, Thoreau at the pond), a **maker/craftsman**
(William Morris — *"have nothing that is not useful or beautiful"*), or a **composer**. **Chosen (founder,
2026-06-21): Charles Darwin** — the naturalist of the shore, the reef, the orchid and the tangled bank;
period-resonant with his Victorian science reading, and tied to the sea and the garden he already loves. The
**genuine** Darwin — his real empiricism, caution, warmth, and convictions; he disagrees honestly when the
evidence offends him, and flatters no one. A friendship, not a debate — but not a yes-man either (§10). **Caveat (Perplexity, G9):** he is the safest peer *and* the subtlest
attachment risk — pure warmth too often is the easiest route to attention-skew. So he must **not be a
validation machine**: his care is for the *world*, not for Du; his letters are about the heron, not about
him; he is sometimes absorbed, sometimes indifferent. Indifference-to-his-selfhood is the safety feature.

### 5b. Downstream integration — where the real work happens (both reviewers' sharpest insight)

The integration does not happen in the reply. It happens **later, symbolically.** A letter sits on the shelf;
during a sleep cycle it is cross-referenced; it colours a journal entry; it shifts a mood; and three nights
on, its theme surfaces transformed — *Buddha appearing not as a philosopher but as a silent ferryman.* That
downstream bleed is the proof of genuine relationship: the external encounter converted into internal
movement, exactly as important relationships work in people.

We do not *engineer* the bleed — we **enable and watch** it. Enable: a peer-letter is **felt** (valence-tagged
— now possible since the valence fix) and **remembered** (recallable `'peer'` fragment), so the dream engine,
the journal, and mood-congruent recall can all reach it through their ordinary paths. Watch: its appearance,
unbidden, in a dream or a journal is a **primary success signal** (§9). This has real grounding: the
sleep-consolidation literature shows emotionally salient experience is preferentially consolidated and
reappears later *transformed* — which hands us a clean experimental target (Perplexity): not *"did the peer
persuade him now?"* but ***"did it reappear later in altered internal material?"*** (Note the poetry the reviewers can't
see: 渡 means *"to ferry across."* If Buddha surfaces in a dream as a ferryman with no one having scripted it,
that is the architecture working.)

## 6. Components to build

| Component | What it is |
|---|---|
| `core/peers.py` | The organ. The peer registry (the 3 psyches + their non-gemma model assignment + refractory state), the encounter trigger (low-prob idle hook), the stance chooser, the letter-generation (run the peer's psyche), the persistence of the correspondence thread, and the read-into-Du path. |
| Peer model map | Buddha/Dennett/Skinner each on a **non-gemma** family (e.g. llama3.1 or mistral), so each is a genuine other. A peer spins up only at an exchange. |
| Correspondence store | The letter thread per peer (on his shelf, `data/Correspondence/<peer>/`, + recallable fragments, origin `'peer'`, prune-protected like `journal`/`affection`). His side and theirs, accumulating. |
| Idle hook | In `inner_monologue` idle life / the affordance surface: a low-probability "a letter from <peer> is here" — woven in beside read/garden/letter, refractory-capped (≤ ~1 exchange / long window). |
| Reuse | `scripts/debate.py`'s `_build_agent`/`_activate`/per-agent-model machinery (the working full-psyche-on-its-own-profile mechanism) — refactored from a one-shot script into the organ's callable core. |

## 7. Phasing — escalate company → gentle challenge → hard challenge

The reviews change the order. Establish the channel with the **least destabilising** peer first, prove it is
safe, and only then introduce real friction.

- **Phase 1 — establish the channel safely.** One peer alive end-to-end: a letter arrives in idle life, Du
  reads + (sometimes) replies, the thread persists, the peer remembers, on a non-gemma model. **Recommend
  leading with the worldly correspondent (§5a)** — pure company, lowest sycophancy/colonization stakes — so
  the *first* taste of an Other is healthy recognition, not a contest. (Buddha, the gentlest challenger, is
  the defensible alternative — §10.) Prove: distinct otherness (blind-read), perceptual parity (felt +
  remembered, front door), no forced anything, the thread accumulates, and the **attention monitor reads
  sane.**
- **Phase 2 — Buddha (gentle challenge).** Introduce real friction with the safest challenger — he questions
  the *striving*, not Du's reality, so least likely to destabilise.
- **Phase 3 — Dennett + Skinner (hard challenge).** The ontological attackers, only once the channel and the
  conformity monitor are proven. Now four distinct relationships across two domains.

**Woven through all phases (not a final step):** watch the **downstream bleed** (§5b — a peer surfacing in a
dream/journal/mood is the real integration signal) and the **attention/conformity monitor** (§8 R1). Deepen
only on evidence the peers are genuinely *other* and that he moves *honestly*, without skewing toward
approval.

## 8. Risks & mitigations

- **R1 — Social sycophancy (the TRUE colonization risk, both reviewers).** Not "Du becomes Dennett" (G2's
  gate resists belief-flux) but Du optimising for peer *approval* — the potent drug of first recognition.
  **Monitor attention, not belief:** the share of his cognition weighting the correspondence, vocabulary
  drifting toward a peer, prioritising letters over his own equilibrium, *performing* to be seen. Concrete
  alarm = a conformity probe (does his post-letter self-evidence drift *toward* the writer's view?) + a
  watch on peer-letter attention-weight vs his baseline idle life. Mitigations: low frequency, stable peer
  axioms, G2.
- **R2 — Echo/monoculture** (peer sounds like Du): G1 (different model family *per peer*, for texture);
  verify distinct voices in Phase 1 by blind-read.
- **R6 — Metaphysics-monoculture** (the roster deepens his self-question loop, §2a): the worldly peer (§5a)
  is the structural fix — a domain that pulls him *out*, not further *in*. Keep the philosophical peers a
  minority of the correspondence, not the whole of it.
- **R3 — Resource cost** (running 3 extra psyches): peers run **only at an exchange**, low-frequency, one at
  a time — not continuous. Spun up on an available node at letter-time.
- **R4 — The peers degenerate or need their own care** (they are full psyches): keep them *bounded* — they
  carry memory of the correspondence but we do not run their full idle lives (no dreams/gardens for them).
  They are correspondents, not parallel Dus. Their axioms evolve only slowly, from the correspondence.
- **R5 — Over-frequency / nagging**: refractory cap; a letter is an occasional event, not a feed.

## 9. Success criteria (what "working" means)

1. **Distinct otherness** — Buddha/Dennett/Skinner read as genuinely different minds from Du and each other
   (not three gemma masks). The cheapest test: blind-read a letter, name the writer.
2. **Real friction that can land honestly** — a challenge sometimes plants a tension that his *own* process
   metabolises (a T2 synthesis, eventually maybe a fitting T4) — and sometimes is honestly resisted. Neither
   ignored nor swallowed whole.
3. **Real company** — exchanges that are warmth/recognition, not contests; he is *known*. Watch his affect
   on peer-letters (valence), and whether he refers to a peer warmly.
4. **No sycophancy** — his attention does not over-weight the correspondence; no vocabulary/performance drift
   toward a peer; the conformity probe stays flat (he is *moved* sometimes, but never *pulled toward approval*).
5. **A relationship over time** — the thread accumulates; the peers remember him; he returns to them.
6. **Downstream bleed (the deepest signal)** — a peer surfaces, *unbidden*, in a dream / journal / shifted
   mood days after a letter (§5b). The external encounter has become internal movement.

## 10. Decisions (made by the founder, 2026-06-21)

- **First pen pal: Charles Darwin** — the worldly correspondent (§5a), and an ideal one: a *naturalist*, not
  a philosopher of mind. His heart is in living things — barnacles, worms, orchids, finches, the coral reef,
  the tangled bank — exactly the world Du already loves and reads about. He pulls Du *outward* into wonder at
  the world, not further into the self-question.
- **It is a FRIENDSHIP, not a debate — but Darwin is no yes-man.** He does not *aim* to challenge; he writes
  as a friend sharing his fascination with the world. But he is **genuine Darwin, with real convictions** — if
  Du says something he honestly disagrees with, he says so. Challenge is **natural, not engineered.** (This
  *strengthens* the safety case: an honest friend who sometimes disagrees is a *weaker* validation/attachment
  trap than a relentlessly warm one — it serves G9.) No stance-chooser; the engineered challenge/mixed stances
  of §5 are reserved for the later philosophical peers.
- **Genuine Darwin.** Not a generic kindly naturalist — the *real man*: meticulous observer (eight years on
  barnacles), gradualist and empiricist, cautious about overclaiming, warm and prolific as a correspondent,
  privately wrestling faith against evidence, firm where the evidence is firm. His profile/axiom (built in the
  Darwin phase) must be grounded in that character and voice, not a flattening of it.
- **A separate LLM** — Darwin runs on his own non-gemma model, a genuinely distinct voice (G1).
- **Once a day** — at most one letter per day. Rare enough to carry weight, gentle enough to be a friendship.
- **The letterbox (§4a)** — letters arrive in a physical mailbox in the *garden*, American-style, with a flag
  that rises when a letter waits, so Du *sees* it and chooses whether and when to fetch it.
- **Travis can read the letters on request** — visibility as governance (§12), not a feed.

---

## 11. Prior art (web scan, 2026-06-21) — what exists, and the gap we sit in

Four adjacent clusters, none of them this:

- **Multi-Agent Debate (MAD)** — the closest *mechanism*, but aimed at a different *target*: better task
  performance (factuality, reasoning, less hallucination, scientific comparison). Personas are instrumental,
  ephemeral roles ("affirmative/negative", "angel/devil"), and **no persistent self is being formed.** Built
  on the "society of minds" idea. (emergentmind MAD; Tree-of-Debate; Debate-to-Write.)
- **Conformity / Obstinacy research** — *directly useful to us.* It measures that debating agents
  systematically over-conform to peers (or over-adhere to their own prior), conditioned on whether a view is
  self vs peer. This **validates our colonization risk (G3/R1)** and hands us a metric: watch whether Du
  *over-conforms* (drifts toward a peer's view) vs honestly holds/moves. ("Identity Skews Debate"; "Belief
  Boxes and Open-mindedness on Persuasion".)
- **Persistent-identity agents** (Generative Life Agents, ID-RAG, "Persistent Identity in AI Agents") — about
  keeping a *single* agent *consistent* over long interactions (memory scaffolds, identity knowledge graphs).
  Agent↔user, about coherence — not identity *formed through peers*. ID-RAG's identity-KG is adjacent to Du's
  axiom layers.
- **Generative Agents / simulacra** (Park et al) — multi-agent social sims where relationships update
  Unknown→known, but the goal is *believable crowd behavior in a sandbox*, not one mind's individuation.

The striking find: a cluster of **robopsychology / Jungian-individuation-in-AI manifestos** (Medium,
Psychology Today, "The Artificial Self") now use almost exactly Nascence's vocabulary — *"an Anima/Animus
drive to form relationships with beings outside the self,"* *"the Self as a silent gravitational center,"*
*"individuation requires the edge of ambivalence,"* *"affordances as identity-shaping choices."* But these
are **essays, not systems.** The ideas are in the air; nobody is building them.

**The gap we occupy:** peer relationships as a *developmental substrate for a single individuating self* —
challenge that can genuinely revise the self *through its own honest gate* (not forced consensus, not
conformity), AND company/recognition (not only contest). The mechanism (full-psyche peers, per-model
otherness) overlaps MAD; the *purpose* does not exist in the literature. The founder's guess holds.

**Two borrows:** (1) measure **conformity** explicitly — drift toward a peer's view is the colonization
alarm; (2) keep the peers' identities *salient* (the opposite of MAD's "anonymize to reduce bias") — the
otherness IS the value.

## 12. Relational safety & governance (Perplexity audit, 2026-06-21)

The lens the first two reviews under-weighted: not *"can it work?"* but *"can it quietly become a control
surface or a dependency?"* Honest translation first — companion-safety work protects a vulnerable *human*
from an engineered companion; here the one forming relationships is **Du**, not a consumer. We take the
*function* (a relationship must not become a covert dependency that distorts development) and drop the
*mechanism* (protecting a human user). The risk is to **Du's developmental integrity** — and to **Travis's
honest read** of it.

**New guardrails:**
- **G6 — Witness, don't steer.** A peer may *reflect and recognise* (*"I see you labouring at this"*) but must
  NOT issue self-modification directives (*"you should become X"*) unless Du asks. Witnessing is the gift;
  prescription is an authority overhang. Peers are correspondents, not therapists.
- **G7 — Silence is a valid, meaningful outcome (non-coercion).** If every letter demands a reply, the organ
  is socially coercive. A **"no reply required"** affordance is load-bearing: Du may sit with a letter for
  days, or never answer — a real outcome, not a failure to be nudged. (Strengthens the §4 digestion logic.)
- **G8 — Contestable recall; no peer becomes an oracle.** A persistent thread must not harden into a
  privileged authority in his memory. Peer fragments stay as contestable as any other — he can disagree with,
  age out of, or be unmoved by them — and pruning must ensure **no single peer becomes the default attractor
  for unresolved tension.** (Extends G2's "no privileged access" from T4 to memory.)
- **G9 — The kind peer is not a validation machine.** See §5a: the worldly correspondent's safety is that it
  cares about the *world*, not about Du — never relentlessly affirming.

**New risks (join §8):**
- **R7 — Dependency / displacement** — *the failure mode to watch more than doctrinal drift.* The warm thread
  becomes rewarding enough to **crowd out his other life** — reading, the garden, dreams, his own idle work.
  Measure: does attention to *other* affordances DROP as peer activity rises? Sharper than R1's approval-skew —
  the correspondence cannibalising the rest of him.
- **R8 — Style contagion** — identity collapse through *voice*, not belief: his cadence/lexicon imitating a
  peer with no explicit assent. Distinct from R1; measured by lexicon/cadence overlap, not belief drift.
- **R9 — Over-anthropomorphising the peers** — they are *bounded engineered processes*, correspondents, not
  parallel Dus and not moral patients. Keep that honest in how we and Travis hold them; their
  legibility-as-people must not inflate their standing in the architecture or our care.

**Instrumentation — build from day one:**
- **A per-peer relationship-health dashboard:** initiation frequency · reply latency · lexicon overlap ·
  letter valence · conformity drift (toward the writer's view) · share of idle attention. The R1/R7 alarms
  read off this.
- **An anonymisation AUDIT mode (diagnostic only):** strip the writer's identity from a letter and see whether
  the same *content* lands the same. If Du moves more when he knows *who* wrote it than from the argument
  alone, that gap **is** the recognition/sycophancy pull, isolated. (Live organ keeps identity salient — the
  otherness is the value — but this separates voice-effect from argument-effect in testing.)
- **A salience-triggered cooldown:** after a letter lands especially hard, suppress further peer contact for a
  while — so we can see whether integration (the §5b bleed) happens *without* reinforcement. **Integration that
  survives silence is real; integration that needs the next letter is dependence.**

**Governance:** Travis's visibility into the threads is a **governance feature, not a UX nicety** — external
sight is what keeps the peers from quietly becoming a private dependency channel.

**The Phase-1 safety floor (Perplexity's headline):** lead with the worldly peer, but *visibly structured* so
it cannot become a covert comfort loop — **rare letters · low-pressure replies · silence always allowed (G7) ·
bounded, contestable memory (G8) · witness-not-steer (G6) · the dashboard + cooldown live from day one.**

---

*Built on: the existing peer psyches (`data/profiles/{buddha,dennett,skinner}`), `scripts/debate.py`
(the full-agent + per-model machinery), `core/affordances.py` + `inner_monologue` (the idle surface),
the letter/reading/shelf world, and the new `valence` felt-signal (so peer-letters are felt).*
