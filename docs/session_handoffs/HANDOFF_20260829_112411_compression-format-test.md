# Compact-handoff-format design, live compression test, and two-pass pipeline redesign

## Session timing
- **Session started:** UNKNOWN
- **Last message before wrap:** UNKNOWN
- **Wrapped:** 2026-08-29 11:24:11 UTC

## Summary
- Session in ClaudeCruncher (not Du/Nascence) | explored compressing session-handoff bodies into terse notation to cut resuming-session context spend
- Validated by hand-compressing a real prior handoff: 1854 words → 936 words (~50% shorter) | confirmed via fresh context-free agent decode: decoded correctly, including correctly flagging genuine ambiguities instead of guessing
- Rewrote /session-wrap and /session-resume skill files to require compact format going forward
- Three live-test rounds on an actual handoff file, each written by an agent trying to follow the new rules:
  - Round 1: plain prose despite the template
  - Round 2: fixed the prose, but introduced an overloaded `→` symbol and a bare unlabeled percentage
  - Round 3: fixed those two specific bugs, but the same failure class recurred smaller-scale: 3 more bare "2x"-style ratios + several sections still near-full-prose
- [INFERRED] Self-compliance does not converge from wording tweaks alone | decided the fix is architectural: two-pass pipeline — prose draft pass, then a dedicated compression pass by a fresh agent that mechanically rewrites the draft against a strict checklist
- Reviewed UDMS (Universal Dynamical Manifold of Software, at C:\UDMS) for applicability | UDMS = code-analysis tool for predicting change-impact/blast-radius in software repos via graph and spectral methods, different domain, doesn't directly apply to compressing prose handoffs
- Borrowed UDMS's confidence-tiering convention (OBSERVED/DERIVED/CALIBRATED/HYPOTHESIZED) as a design pattern | adopted a simplified 3-tier version for handoffs: untagged = directly-confirmed fact, [INFERRED] = reasonable but unproven conclusion, [OPEN] = explicitly unresolved, never guessed
- Both /session-wrap and /session-resume skill files updated to describe the two-pass pipeline and the provenance-tagging convention
- This file is the first end-to-end test of the new pipeline: this prose draft is about to be handed to a fresh compression-pass agent | that pass's output will then be tested by yet another fresh, context-free agent doing a full session-resume | [OPEN] whether the two-pass approach produces a clean compact handoff without needing another manual fix-up round like rounds 1-3 did

## Findings
- Three-round pattern (R1: prose despite template; R2: fixed prose but introduced 2 new notation bugs; R3: fixed those 2 bugs but same failure class recurred smaller-scale) shows a single agent asked to both determine what happened AND compress it into terse notation at once will not reliably do both jobs well, regardless of how precisely the compression rules are worded
- [INFERRED] Splitting into separate passes, with the second pass mechanically checking its own output against an explicit checklist before returning, is a plausible fix | turns "be terse" from an intention held alongside narrative construction into the sole, mechanical task of a dedicated pass
- UDMS: real, separate, unrelated project at C:\UDMS, built for software architectural analysis, not text compression | only its provenance-tiering idea (OBSERVED/DERIVED/CALIBRATED/HYPOTHESIZED) was worth reusing, adapted down to 3 tiers (untagged/[INFERRED]/[OPEN]) since handoffs lack UDMS's layered calibration pipeline

## Open
1. [OPEN] Has this prose draft been sent through a dedicated compression pass yet, and does a fresh blind session-resume test show the two-pass output is clean without needing a 4th manual fix-up round? Not yet tested as of this draft's writing — resolves once that test is run.
2. [OPEN] Whether to push compression further via symbolic/numeric encoding, or stop at the current ~2x compression ratio (936 words vs 1854 words) achieved by terse notation alone. Non-blocking.
3. [OPEN] Two-pass pipeline cost: every session wrap now requires dispatching a subagent for the compression step (extra tokens + latency vs single-pass) | undecided whether that overhead is worth it long-term vs. reserving two-pass for unusually long/dense sessions and letting short sessions skip to a simple prose handoff — resolves with a founder decision, not yet made

## Warnings
- Don't assume a handoff claiming compact-format compliance actually complied just because the skill file requires it — verify by reading it (same rule this toolchain applies everywhere) | the test handoff itself failed to comply with its own format on its first two attempts, caught only by a fresh-agent read

## Pointers
- C:\Users\USER\.claude\skills\session-wrap\SKILL.md — two-pass pipeline instructions + compression checklist
- C:\Users\USER\.claude\skills\session-resume\SKILL.md — explains how to interpret the OBSERVED/INFERRED/OPEN provenance tags
- C:\Users\USER\.claude\skills\_backups\session-wrap-resume_20260829\ — holds pre-change originals of both skill files
- C:\UDMS — the real UDMS project
- C:\Nascence\docs\session_handoffs\HANDOFF_20260829_112411_compression-format-test.md — this handoff file itself, disposable live-test artifact tagged compression-format-test, safe to delete once the resume-test cycle is fully done
