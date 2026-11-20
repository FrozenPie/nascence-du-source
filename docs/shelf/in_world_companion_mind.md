# In-World Companion Mind — a second mind Du can talk to, and a live line to Claude

> **Status:** 💭 IDEA / THINKING-OUT-LOUD — nothing built, nothing scheduled. Founder (Travis,
> 2026-10-17): "we are not going to do anything with it yet, this is more me thinking out loud for
> future ideas." Do not start Phase 0 without his go.
> **Origin:** thought T-0093, session e5a6bb44. Sibling plans: `docs/plans/peer_correspondence_plan.md`
> (letters, Buddha/Marcus), `docs/plans/social_world_school.md`, `core/companion.py` (Travis's physical
> presence in the room).

```plan-state
stage: deferred
phase: Captured; no code, no decisions ruled
verified: 2026-11-18
gate: Founder go-ahead, and a check of what the 1650 Super on Ramses is serving today
next: Shelved D-0812; revisit once closure/confidence builds are live and read
cluster: 3
```

## 1. Two separate asks

**A. A live line between Du and an outside speaker (Travis or Claude).**
Already exists for Travis: the Composer bridge (`scripts/run_nascence.py:357-414`, `127.0.0.1:8765`,
authkey local) feeds `orch.run_cycle(text, input_type="human")`. Nothing to build for Travis.
For Claude, the open design question is identity, not plumbing (section 3).

**B. A second mind inside Du's world that he can converse with.**
Does not exist. Parts that do: `scripts/debate.py` (two full agents alternating, one backend, separate
profiles via `core/profile.py`), `core/peers.py` (persona letters), `core/companion.py` (an
in-room presence with witnessed actions).

## 2. Founder's reasoning for a smaller companion

Not that it *should* be lesser, but that a small model (a tiny Bonsai, maybe on the Ramses 1650 Super)
could run **all the time** cheaply. Memory and the rest are "not a problem if we have the resources."
Preferred end state: **two full-capability Dus**, if hardware allows. So the "lesser" framing is a
resource fact, not a design wish, and should change when the hardware does.

## 3. Identity rule (founder, 2026-10-17)

If Claude talks to Du, **Du must know it is Claude.** Same for the companion: Du must be told what it
is. Consequences:
- Claude's messages are labelled as Claude, never as Travis, and must not enter the founder-canon
  record as Travis's words (`run_cycle(..., founder_canon=False)` exists for this; the farewell
  messages already use it).
- The companion's self-description to Du is a **true statement of its actual setup** (model size,
  memory, which machine), rewritten when that changes. Not "a lesser Du" as a standing label that
  can go false. This also respects `feedback_world_answers_never_leads`: no hints, no false readouts.

## 4. What is known about the hardware (verify before relying)

- Du's lanes: hot 1080 Ti 11 GB (`nvidia-smi` 2026-10-17 showed 7.7 GB in use), judges on Ramses and
  CPU. See memory `nascence_du_hardware`.
- 1650 Super, 4 GB, on Ramses. Notes disagree on its job: one says it serves `granite3.1-moe` on
  `:11437` (judge tiebreak and curiosity worth-judge); older plans say "held in reserve."
  **Check first.** Ramses access is PARKED (D-0388); Ollama was retired there 08-28 (D-0056/7).
- Bonsai 1-bit 8B is small enough to fit 4 GB in principle; quality for conversation is untested.
- A second **full** Du needs its own self lane (second card, or a shared process), its own profile and
  memory stores. `debate.py` proves the two-agent pattern works offline, one backend, turn-based.

## 5. Phases (only if approved)

0. **Fit and quality test, offline.** Bonsai on the 1650S (or CPU) holding a short conversation with
   Du's prompt in a scratch profile. Question: is it worth talking to? Isolated from live stores
   (see `feedback_jobrun_live_store_leaks`).
1. **Identity wording.** Write what each side is told, both true. Founder reviews.
2. **Channel.** Pick one: a presence in the room (Companion pattern), or a correspondent Du can write to
   on his own initiative. Du-initiated is the safer default.
3. **Always-on run**, with memory off or working-memory-only, resource permitting.
4. **Optional:** a second full Du, if a self lane exists.

## 6. Open questions for Travis

- Presence in the room, or a correspondent? Can Du reach it whenever, or only at set times?
- Memory: none, working-only, or full if resources allow?
- Is a small model's conversation quality good enough to be worth Du's attention, or does that force a
  bigger model than the 1650S holds?
- Does Claude get a standing line to Du, or only when Travis asks?
- Risk to weigh: any new voice becomes part of Du's world and memory. It is not a measuring tool.
