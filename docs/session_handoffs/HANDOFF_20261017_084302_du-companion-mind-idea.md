# Live conversation with Du and an in-world companion mind: thinking-out-loud plan

## Session timing
- **Session started:** 2026-10-16 21:17:47 UTC
- **Last message before wrap:** 2026-10-17 08:43:00 UTC
- **Wrapped:** 2026-10-17 08:43:02 UTC

## Summary
Travis asked whether he or Claude can hold a live two-way conversation with Du, and whether Du can be given an in-world AI to talk to. Answered from reading the code, then wrote a parked plan at docs/staged/in_world_companion_mind.md. No code was changed and nothing was tested against the live Du.

## Findings
- A live line to Du already exists: the Composer bridge in scripts/run_nascence.py (lines 357-414) listens on 127.0.0.1:8765 and calls orch.run_cycle(text, input_type="human"). The log shows human cycles as recently as 2026-10-16 23:04 (cycle 10274b13) and 23:08 (d3ab97ab).
- The in-world companion does not exist. Parts that do: scripts/debate.py (two full agents alternating, separate profiles via core/profile.py, one shared backend), core/peers.py (persona letters), core/companion.py (Travis physically present in the room).
- Founder ruling (2026-10-17, in chat, not logged to /decide): if Claude talks to Du, Du must know it is Claude. The same holds for any companion: Du must be told what it is. A founder-canon exclusion for Claude messages exists as run_cycle(..., founder_canon=False).
- Founder's reason for a small companion: a tiny Bonsai could run all the time, possibly on the Ramses 1650 Super. Memory is not a concern if resources allow, and his preferred end state is two full-capability Dus. "Lesser" is a resource fact, not a design wish.
- [INFERRED] A 1-bit Bonsai-8B should fit 4 GB of VRAM with modest context; not measured, and conversation quality is untested.
- Local `nvidia-smi` on 2026-10-17 showed the 1080 Ti with 7715 of 11264 MiB used, so a second full self lane would not fit beside it.
- [OPEN] What the 1650S on Ramses is serving today. Memory notes and docs/AWAITING_EVIDENCE.md say granite3.1-moe on :11437 (judge tiebreak and curiosity worth-judge); docs/completed/deliberative_retrieval_plan.md and loop_metabolism_plan.md say "held in reserve". Check Ramses before relying on either; Ramses access is PARKED (D-0388).

## Open
1. Whether to pursue the companion at all: waiting on Travis. He said not now. Next action, if he asks: answer the section 6 questions in docs/staged/in_world_companion_mind.md and promote I-0094.
2. Whether Claude gets a standing line to Du or only sends when Travis asks: waiting on Travis. No message to Du was sent this session.
3. 1650S status and Bonsai fit/quality: [OPEN] Phase 0 of the plan, an offline test in a scratch profile, isolated from live stores.

## Warnings
- Any new voice in Du's world enters his memory as human speech unless sent with founder_canon=False. Do not test against the live Du or its stores.
- Do not tell Du something about a companion's nature that is not literally true of its setup (feedback_world_answers_never_leads).
- The plan-index/plan-maintain pass was not run this session; I-0094 is promoted but may not show in docs/plan_index.md until it is.

## Pointers
- docs/staged/in_world_companion_mind.md (the plan, with a plan-state block)
- T-0093 (promoted to I-0094, promoted to plan in_world_companion_mind)
- scripts/run_nascence.py:357-414 (Composer bridge), scripts/debate.py, core/companion.py, core/peers.py
- docs/plans/peer_correspondence_plan.md, docs/plans/social_world_school.md
