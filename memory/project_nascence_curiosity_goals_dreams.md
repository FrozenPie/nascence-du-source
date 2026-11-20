---
name: project-nascence-curiosity-goals-dreams
description: "Curiosity/frontier/dreams/sleep/symbols plan mostly graduated as of 2026-08-23: Items 1 (prism→frontier), 2 (OMNI worth-gate), and 4 (dream re-pin cap) are all LIVE — Item 4 shipped via a separate 08-22 sleep/dream rewrite (core/night.py), not this plan's own track. Only low-priority Items 3 (cluster-LP) and 5 (goal_model G2 stub) remain unbuilt."
metadata: 
  node_type: memory
  type: project
  originSessionId: 1857a5ac-8424-4a7e-930e-5da8c19bf9b9
  modified: 2026-08-23T04:49:49.708Z
---

Deep-dive + implementation plan (2026-06-24) covering curiosity_queue.py, curiosity_worth.py, curiosity_progress.py, frontier.py, concerns.py, goal_model.py, dream_node.py, sleep_pressure.py, symbol_evolution.py. Same "all senses, no hands" meta-finding as the sibling 06-24 plans, but this domain is one of the few where the fixes actually landed.

**Current stage, per the doc's own 2026-07-05 evidence-review header:** "HEALTHY; two live wins, one worsening regression to fix." Item 1 (the de-personalization prism wired into the frontier, so a private self-tension becomes a pursuable world-question) is "LIVE + world-facing (39/39)". Item 2 (the OMNI worth-judge gating pursuit by `LP × interestingness`, not LP alone) is "LIVE + WORKING WELL — one of the review's few genuinely-working live features": 245 question-grades, interestingness cleanly bimodal (93 boring @0.0 / 149 interesting @0.8-1.0), correctly separating 87 aimless-novelty traps from 134 genuine hi-LP/hi-interest questions. Item 3 (MAGELLAN-style cluster-level LP transfer, so near-duplicate self-shaped questions accumulate collective stall pressure instead of each looking "fresh") is designed but not built, lower priority. Item 4 (capping the dream engine's `_last_unresolved_arc` re-pin so one unfaced tension can't monopolize the dream channel indefinitely) is "DESIGNED-NOT-BUILT, and the regression is REAL + WORSENING": ended-unfaced climbed 54%→72% (first half vs recent half of arcs) while resolution stayed flat (~0.21→0.26) — the last 14 consecutive arcs in the log are an unbroken ended-unfaced streak. Disposition stated explicitly: "keep 1&2; BUILD Item 4 (plan's own #2 priority, S-M, localized, dovetails with Item 1's frontier hand-off); Item 3 cluster-LP stays designed (lower priority)."

Also documents `frontier.py` as "the one genuinely-closed loop (good)" — the model every other item should imitate — and diagnoses frontier resolution as decay-dominated (4 resolved / 1640 faded / 91 open out of 1735 questions), with the park mechanism firing too late (only 12/1735 ever parked, all already faded) to serve as a live rumination exit.

Research grounding: MAGELLAN (arXiv 2502.07709) for embedding-keyed LP transfer across near-duplicate goals (Item 3); "Language Models Need Sleep" (arXiv 2606.03979) for treating a re-pinning dream as a failed-curriculum replay rather than generative recombination (Item 4's justification); OMNI as the interestingness-gate precedent already half-built (Item 2).

Related: [[project-nascence-cognitive-loop-actuation]] and [[project-nascence-affect-drives]] (same 06-24 audit wave, same read/actuation-path discipline) — this is the domain where the discipline actually paid off with two live graduations. Also see [[nascence-stale-plan-audit-2026-08-23]] — the 13-agent 2026-08-23 workflow audit that re-checked this and 11 other stale plans against actual code/data; its per-plan finding for this one is what confirmed Item 4 as live-via-a-different-track and prompted the "Current State — verified 2026-08-23" section now in `docs/plans/curiosity_goals_dreams.md` itself.

**Plan-index cross-check (2026-08-23):** `/plan-index` flagged a stage MISMATCH — investigated and
it's a tool artifact, not a factual disagreement. All sources actually agree: ROADMAP.md's bullet
for this plan carries a leading ⚪ PARTIAL badge ("some items live") and its own prose says the same
Item-1/2-live, Item-3/4-designed breakdown as above. The tool's emoji-window scan grabbed the
*inline* 🔵 attached to "Item 3 (MAGELLAN cluster-LP) 🔵" later in the same bullet line instead of
the plan-level ⚪ badge leading it — a same-bullet multi-emoji ambiguity, tightened (not fully
solved) in `plan_index.py` by bounding the scan window to the current bullet/paragraph rather than a
fixed character span. Confirmed current stage, unchanged: **⚪ PARTIAL** (as detailed above). Newer
evidence corroborates rather than changes this: `docs/reviews/sleep_dream_2026-08-22.md` (7 weeks
later) confirms Item 4's re-pin cap was never built and measures 223 episodes of one serial dream
thread — worse than, and consistent with, this doc's 54%→72% measurement.
