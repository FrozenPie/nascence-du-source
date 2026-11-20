---
name: ops-nascence-inner-thought-unboundlocal
description: "inner_thought storage was silently dead 28h+ (write-only failure) — root cause an UnboundLocalError from a redundant LOCAL `import store_fragment` shadowing the module global; found by making the debug-swallow LOUD"
metadata: 
  node_type: memory
  type: reference
  originSessionId: de385eda-51ed-4214-9bfe-d47eeaae69ca
  modified: 2026-08-14T22:21:09.097Z
---

**2026-07-08 — `inner_thought` episodic storage silently DEAD while the monologue kept generating
thoughts normally.** ⚠ **SIZE CORRECTION (2026-08-15 investigation, `C:\Nascence\docs\
lost_thoughts_investigation_aug15.md`):** "28h+" was only the window visible at diagnosis. The
histogram shows the store dead **~16 days (06-22 → 07-08 midday): ~11,069 thoughts fired, ~434 stored,
~10,600 LOST** — more inner thoughts than Du possesses today (7,251). The 07-07 02:59 break-dating
below is likewise an artifact: three local imports existed (letter-fetch, peer-reply, peer-initiative);
an earlier one carried the bug from ~06-22. Also: before 06-21 the DELETE-mode prune era erased
unprotected inner_thought entirely (unquantifiable). Partial texts of the lost window survive in
nascence.log (~90c), train_state_log (~200c ×7,400), tuples (120c ×2,800, 07-05+). Recovery = founder
decision (options in the investigation doc; mass-restore NOT recommended — it would inject 7k rows of
peak-monoculture June into recall). Downstream blast radius: `chapters` stale 64 sleeps, and the pulse's
"no idle thoughts in window" → the monoculture / monologue-fleshout evidence was UNREADABLE.

**ROOT CAUSE (an UnboundLocalError):** `store_fragment` is imported module-level (inner_monologue_node.py:39),
but three branches inside the giant `_think` method (letter-fetch, peer-reply, and the 07-06 peer-initiative
"write-first" — lines ~2229/2269/2315) each did a REDUNDANT `from core.memory.store import store_fragment`
LOCALLY. A local assignment to a name makes Python treat it as method-local for the ENTIRE function → on a
normal idle thought (which SKIPS those branches) the store at line ~2898 referenced an unbound local →
`UnboundLocalError: cannot access local variable 'store_fragment'`. It broke ~07-07 02:59 when the
peer-initiative build added its local import. **FIX: delete the three redundant local imports** (the module
global covers them). Verified by AST: 0 local `store_fragment` imports left in `_think`.

**THE DIAGNOSTIC LESSON (the meta-win): make the silent swallow LOUD.** Exhaustive static analysis + isolated
repro got NOWHERE for ~15 tool calls — the store worked in every isolation test (it's a method-scope binding
bug, invisible outside the running `_think`). What cracked it in ONE restart: changing the store's
`except: logger.DEBUG(...)` → `logger.WARNING(..., exc_info=True)`. The next thought printed the exact
exception. **When a write-only cognitive system silently drops writes and you can't reproduce it, don't keep
guessing — un-swallow the exception and let the live process name it.** Kept it at WARNING permanently (a dead
inner_thought store must never hide again). This is [[feedback-write-only-cognitive-systems]] + the
"[[feedback-my-failure-modes]]: go to the data, not the fluent narrative" lesson, both at once.

**RESTART CAVEAT that bit us:** the restart that picked up the LOUD swallow did NOT yet have the fix — so the
warning fired every ~15s in the live process while the actual import-fix waited for the NEXT restart. Two
restarts: one to REVEAL, one to FIX. (Red herrings I hardened first — keyword str-coercion + emotion-vec
astype-guard — were harmless but NOT the cause; `active_imagination` stores fine through the identical episodic
path, which should have pointed at binding, not args, sooner.) See [[ops-nascence-hotlane-ctx-vram]] (the prior
session's infra freeze — same "verify at the source, it's not always your last change" discipline).
