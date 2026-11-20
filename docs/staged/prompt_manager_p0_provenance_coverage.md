# prompt_manager P0 provenance coverage map (J-4309, F-5085)

> Status: analysis only; no Du code edited. Parent plan: `docs/staged/prompt_manager.md`.

## Finding
`data/prompt_provenance.jsonl` holds 1838 rows, all `source = inner_monologue.idle_thought`. This matches the plan's own scope, not a bug.

## What the plan intends
- Section 6.2 (line 189): Level 1 provenance "every call", per station, with the stated aim of covering "the hottest stations".
- Section 10b (line 359) and Q7 (line 385, "proposal", no D-id filed): "Level 1 on the idle station only until overhead is measured." Line 14 lists "wire more sources into _provenance" as a next step.
- Line 362: execution fingerprint (model digest, sampling params) is not in P0; deferred to P1.
- So P0 intentionally covers idle thought only. Widening is gated on an overhead measurement. I found no overhead result recorded in the plan.

## Mechanism and the real gap
- `_provenance` (`core/prompt_budget.py:217`) is called only from `observe_assembly` (`:118`, call at `:185`). It runs only when `user_prompt` is truthy, and `PROVENANCE_ON = True` (`:62`).
- `observe_assembly` has exactly ONE caller in `core/` or `nodes/`: `nodes/inner_monologue_node.py:4386`, hard-coded `source="inner_monologue.idle_thought"`. It takes a list of `parts`.
- Other stations do not assemble `seed_parts`. Their prompts are single strings built inline. So wiring them means adding a call per site (or hooking `core.model_client`), not flipping a flag.
- `_provenance` also depends on `core.phrasing.drain_picks()`, whose ring is drained once per idle assembly. Other stations would get empty or wrong `pool_picks` unless the ring is keyed by station.

## Uncovered stations, by registry `calls_7d` (docs/prompt_registry.jsonl)
| P-id | calls_7d | status | code key | note |
|---|---|---|---|---|
| P-0022 | 3098 | LIVE | inner_monologue idle | COVERED |
| P-0035 | 1991 | LIVE | `core.deliberation:_deliberate_run` | uncovered |
| P-0036 | 1366 | WRITE-ONLY | `core.self_implication:scan_shadow` | uncovered; low value |
| P-0038 | 1134 | LIVE | `core.commitment_ledger:_scan_shadow_body` | uncovered; T0 scan |
| P-0013 | 999 | LIVE | `core.node_base:NodeBase.run`, `run_best_of.one` | uncovered; one hook would cover all 12 nodes |
| P-0039 | 737 | SHADOW | `core.condensed_thought:shadow_tick` | uncovered |
| P-0054 | 332 | LIVE | `nodes.subconscious_node:_active_imagination` | uncovered |
| P-0044 | 289 | LIVE | `core.follow_line:_gen_json` | uncovered |

Coverage by calls: about 3098 of roughly 10,000 registry-window calls on the top stations, roughly 30%.

## Options for the founder (needs a plan ruling before any code)
1. Add a thin `observe_call(station, system, user, lane)` Level-1 hook in `core.model_client` or `NodeBase`. This gives a hash-only row with no parts or labels, and covers most stations at once. It is the cheapest route and matches the section 6.2 aim.
2. Per-site `observe_assembly` calls for deliberation and `NodeBase.run` only (about 3000 more calls a week).
3. Stay idle-only until the P0 overhead measurement is recorded (the plan's current position).

## Open items
- No overhead measurement for P0 appears in the plan. Gate for widening: record that first.
- Q7 has no D-id; it needs one filed via `/decide`.
- Any new prompt call or hook must pass `prompt_registry.py check`. No prompt was touched here.
