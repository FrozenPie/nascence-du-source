# J-4350 dreamer RAM guard (D-0761 B/C) - staged plan, restart-gated

Status: 🟡 PARTIAL BUILD (supervisor starved rule built; hub load-deferral patch written, not applied; restart-gated). Founder 2026-11-18 (chat, on J-3961): (a) supervisor treats read timeout under ~2 GB ram_avail as starved not wedged; (b) dreamer hub defers a yi:34b load while ram_avail is low.

```plan-state
stage: built
phase: patch written, not applied; restart-gated
verified: 2026-11-20
next: apply patch in worktree, add RAM-guard test, launch dreamer hub in shadow at next restart
```


## (a) Already built
J-3979 (commit 03d601ee): `HOST_STARVED_RAM_GB = 2.0`, `HOST_STARVED_MAX_SKIPS = 8`, `_host_starved()` in scripts/supervisor.py. No change needed here.

## (b) Patch: docs/staged/J-4350_dreamer_ram_guard.patch (touches deploy/ramses/nascence_cpu_server.py only)
Adds `_ram_guard_before_load()` called before `Llama(...)`; flags `--min-ram-load-gb`, `--ram-wait-s` (30), `--ram-guard-shadow`. Default off. Polls psutil every 2 s; defers by raising (caller fail-opens); fail-open on any error.

## Thresholds from data (data/supervisor.log, 25 host snapshots)
- All slow/starved probes: ram_avail 0.4-1.1 GB (hot_ollama x5, dreamer x1 at 0.8). Healthy snapshots 30-42 GB.
- yi:34b-v1.5 is ~20 GB resident; judges ~8 GB (gemma4:12b) / ~5 GB.
- Threshold: --min-ram-load-gb 24 for dreamer only (load size + ~4 GB headroom); gap between starved (<1.5) and healthy (>29) means exact value is not sensitive.
- Idle-unload: dreamer 60 s already; judges 300 s -> proposed 120 s (supervisor.py SERVERS tuple, third-from-last field). Separate small change.

## Rollout
1. Restart-gated (Du is live). Apply patch in a worktree, run scripts/test_supervisor_host_starved.py pattern for a new test: fake `psutil.virtual_memory` returning 0.5 GB -> expect RuntimeError after --ram-wait-s; 40 GB -> loads.
2. Step 1 launch with `--min-ram-load-gb 24 --ram-guard-shadow` on dreamer_hub (supervisor.py `_launch` args, near the `--idle-unload` line ~604): log-only.
3. After a week read hub logs for `RAM-GUARD(shadow)` lines vs hot_ollama slow probes; if they coincide, drop `--ram-guard-shadow`.
4. Judge idle-unload 300 -> 120 last, independently.
Defeater: D-0761's (restart seen with box under 2 GB, or two weeks with no starved cluster).

## Current State — verified 2026-11-20
### What we have
- Part (a) built: `HOST_STARVED_RAM_GB = 2.0` in scripts/supervisor.py (J-3979).
- Part (b) patch exists as docs/staged/J-4350_dreamer_ram_guard.patch; checked 2026-11-20: `RAM-GUARD` / `_ram_guard_before_load` do NOT appear in deploy/ramses/nascence_cpu_server.py, so it is not applied.
### What we need
- Apply the patch in a worktree, add a fake-psutil test (0.5 GB defers, 40 GB loads), then restart-gated shadow launch on the dreamer hub.
### What we're doing next
- Nothing until the next planned restart; the judge idle-unload change (300 -> 120 s) is separate and last.
