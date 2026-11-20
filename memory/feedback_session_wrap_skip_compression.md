---
name: feedback-session-wrap-skip-compression
description: Skip session-wrap's two-pass compression dance (draft, then dispatch a compression agent) -- write the plain prose draft directly as the handoff.
metadata:
  type: feedback
  originSessionId: e5d16303-3702-4884-b7b3-3c7ec7dd4b4a
  modified: 2026-09-19T01:49:45.636Z
---

When running `/session-wrap`, do NOT dispatch the skill's own prescribed step-2b compression agent
(draft prose -> Agent tool rewrites it into terse `|`-joined notation with OBSERVED/INFERRED/OPEN
tags -> spot-check -> write). Write the plain prose draft from step 2a directly to the handoff path
instead.

**Why:** the founder interrupted this exact step mid-session (2026-09-13) and said to stop
"compressing (and uncompressing)" the handoff and just resume. The skill file's own "Known
limitations" section already documents four rounds of real testing (2026-08-29/30) where the
compression pass itself proved unreliable (arrow-overload, bare ratios, inconsistent provenance
tagging, terseness effort fading in later sections) even with a dedicated second agent pass and a
spot-check step -- the mechanism was never fully validated on a real multi-day session under normal
task pressure, only on constructed tests. The founder's correction here reads as a judgment that the
juice isn't worth the squeeze: an extra agent dispatch plus a verification read, to save context on a
document a resuming session reads once, for a compression pipeline whose own documented history is
"smaller residual failures still appear, this isn't write-it-and-trust-it yet."

**How to apply:** write the handoff in ONE pass -- full prose, the same content/rigor as step 2a
would produce (every ID/path/number cited, every section covered), skip 2b/2c entirely. If the
founder ever asks for the compact format back, that's a real ask to revisit, not something to
reintroduce unprompted. This doesn't change anything else about `/session-wrap` (the rollup pull,
the timing block, the companion memory file, the plan-maintain pass) -- only the compression step.

**Recurred 2026-09-19, then fixed:** a wrap dispatched the compression agent anyway, because session-wrap's
SKILL.md (steps 2a-2c) still prescribed it and this note was not checked before step 2. Caught and stopped
mid-run, output unused. Fixed the same day: SKILL.md step 2 is now one-pass plain prose with an explicit
"no compression agent" instruction, the old pipeline is archived in the skill's RETIRED_compact_format.md,
and session-resume's format note was updated to match (S-0156 applied). This note now stands as the
rationale, not a workaround.
