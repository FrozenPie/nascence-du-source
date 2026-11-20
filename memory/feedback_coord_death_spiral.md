---
name: coord-death-spiral
description: Stat systems with decay but no recovery path create permanent floor-lock — check all coord dims together when one is found broken
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bbc5728f-50a7-4544-87d8-9b21ad5344fc
---

When auditing a coord system failure, always audit ALL coord dimensions in the same session — not just the broken one.

**Why:** This project has seen the same pattern twice. coord_w was broken (gnosis death spiral, May 2026). Full audit in the same session revealed coord_e, coord_s, and coord_x/y were also completely non-functional. Fixing one at a time across sessions is inefficient and leaves the sim in a partially-broken state.

**How to apply:** When any coord/stat shows signs of floor-lock (population all at the same value, last_updated frozen), immediately run `SELECT MIN/MAX/AVG` on all coord columns. A value stuck at exactly its DEFAULT (0.0 or 1.0) for all 330 spirits is the tell. Then check: does metabolism decay it? Does any action increase it? Is there a circular dependency (must act to recover, but can't act because it's depleted)?

**The death spiral signature:**
1. Decay exists (metabolism ticks it down)
2. Recovery requires completing an action
3. But the depleted stat blocks the action that would recover it
4. Result: permanent floor-lock for the entire population

**Fix pattern:** Lower the gate threshold OR add a recovery path that doesn't require clearing the gate first (e.g. STUDY giving coord_w regardless of gnosis level).
