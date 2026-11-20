# Ramses :11441 stalls: diagnosis so far and the deploy-and-measure plan (2026-11-03)

Written after Travis suspected the 3070's command-r7b hub goes slightly over VRAM and spills to system RAM. This is a plan, not a ruling. Nothing on Ramses has been changed. Evidence is in findings F-3872 and F-3873, and the older diagnosis in F-2466, F-2494, F-2556, D-0354 and D-0388. Follow-up job for the Ramses-side steps: J-3278.

## 1. What is known (measured) and what is not

**Measured**
- The 3070 hub is healthy in steady state. A live probe gave 64 to 65 tok/s free text on :11441 (three runs), which is a fully-on-GPU speed for a 7B Q4 on a 3070. JSON mode gives 13 tok/s on the same hub; on granite (small vocabulary) JSON mode shows no such penalty, so command-r7b's JSON slowness is probably grammar sampling over a 256k vocabulary (inference).
- The problem is intermittent total stalls, not slowness. 2,407 of 25,622 calls (9.4%) since 2026-08-28 ended at the 120 s ceiling; in the current run (since 10-29) 145 of 2,903 (5.0%); 10.7% on 11-01 and 14.6% on 11-02. Stall windows start abruptly after normal 2 to 3 s calls and run from 12 minutes to 6.7 hours; inside them no call finishes.
- In the three recent windows (11-01 17:16 to 20:21, 11-02 13:20 to 17:16, 11-02 21:02 to 23:08) the failing :11441 calls were the no-grammar kind (g=0: 52 calls; 13 without the flag), so the old explanation (CPU-bound JSON grammar starved by the i9 hubs, F-2466) is not the whole story now.
- The rest of Ramses stayed up during them: the Lane 2 deepseek hub on :11444 logged 209 ok, 5 timeouts and 1 empty inside the windows; the hot lane and falcon3 were unaffected. Mixtral (:11438) had only 5 calls in the windows and all 5 failed (too few to read). Granite had no calls in the windows.
- Ramses runs the 2026-08-23 hub server, not the 2026-10-07 one: GET /api/status is 404 on :11436, :11437, :11438, :11441 and :11444; the share copy is 11 KB dated Aug 23 against 27 KB in the repo. The old server runs every request to completion after the caller has gone, and its [chat] log lines time from before the lock, so hub_11441.log shows durations up to 42,590 s that are queue waits (or Ramses sleeping). The local hubs (:11439, :11440, :11442) also answer 404 on /api/status.
- The earlier diagnosis (F-2466) found the same stall shape from 2026-09-07 (the day Lane 2 moved onto the same i9), and the lane went clean on 10-07 after D-0354 (no JSON grammar on the first attempt) and the J-1832 breaker went live (F-2556: 220 of 220 ok). D-0388 parked the Ramses-side fixes with the defeater "un-park if :11441 120 s timeouts exceed 5 percent of calls in any run, or a hub-wide wedge". The current run sits at 5.0% overall and above 10% on two days, so the defeater is at or past its line.

**Not established**
- Whether the 3070 runs out of VRAM. The hub log cannot say (verbose is off, the old log lines carry no timestamps). Arithmetic estimate (inference): weights about 5 GB, full-size SWA KV cache about 0.5 GB at ctx 4096, compute buffers about 0.5 to 1 GB with the 256k vocabulary, plus the Windows desktop on the same card (the 3070 was the primary display adapter on 08-23), about 7 to 7.5 GB of 8 GB. Close to the limit, not proven over it.
- What wedges the hub. Candidates in the table below.

## 2. Hypotheses and the measurement that separates them

| # | Hypothesis | For | Against / unknown | Discriminating measurement |
|---|---|---|---|---|
| H1 | Another VRAM user (a browser, a game, the desktop, a second CUDA context) pushes the 3070 over 8 GB; the NVIDIA driver silently spills to system RAM (CUDA Sysmem Fallback) and generation collapses | Travis's idea; the stalls hit only the 3070 hub (deepseek on the i9 kept working); the card is tight by arithmetic; 08-23 showed it 96.6% full | Free-text speed is healthy between stalls; collapse should still finish eventually | `nvidia-smi` memory.used logged every 5 s across a stall; Task Manager Shared GPU memory for the python process; set Sysmem Fallback to Prefer No Sysmem Fallback so overflow fails loudly |
| H2 | The old hub server wedges on its single generation lock (a runaway or abandoned request keeps running; callers queue behind it; the 120 s client timeout abandons each, the old server still runs every one) | Documented in F-2466 and J-1830; hub logs show multi-hour lock waits; stalls end abruptly | Does not say what starts one | Deploy the Oct-7 server; /api/status then shows in-flight time, tokens and queue depth, and the log shows wait and gen separately |
| H3 | CPU contention on the Ramses i9 (mixtral, deepseek, falcon share 14 threads; JSON grammar is single-thread CPU) | F-2466 measured 33.9 s alone against 123.6 s with two CPU hubs generating | The recent failing calls are no-grammar; deepseek worked inside the windows | Per-process CPU during a stall; thread caps (J-1831) |
| H4 | The GPU or driver hangs (TDR, thermal or power event), or Ramses sleeps or loses the network | Matches abrupt starts and ends; CLAUDE.md lists Ramses sleep as a known failure | deepseek and others on the same box kept answering, so not whole-machine sleep | `nvidia-smi` utilisation and temperature during a stall; Windows Event Viewer (Display, nvlddmkm); power plan standby timeout |

H1 and H2 are not exclusive: H1 could start a stall and H2 is why it lasts hours.

## 3. The plan

Order is cheapest and safest first; each phase stands alone.

**Phase 0: a read-only monitor from this box (no Ramses change; I can build it now)**
- `scripts/ramses_hub_monitor.py`: every 30 s, per Ramses hub (:11436, :11437, :11438, :11441, :11444), TCP connect, GET /api/tags, and on :11441 a one-token free-text probe with a 20 s timeout (it queues behind the lock, so its latency is the lock wait). Append to `data/ramses_hub_monitor.jsonl`. Once the new server is deployed, also record /api/status (in-flight, queue depth).
- Result: exact start and end times of each stall from outside Du's workload, usable with any Ramses-side log. Cost: negligible load.

**Phase 1: Ramses-side measurements (Travis or Antigravity, about 30 minutes, then leave running)**
1. Log the cards: `nvidia-smi --query-gpu=timestamp,index,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw --format=csv -l 5 > D:\Du\gpu_log.csv`
2. Log memory and CPU: `Get-Counter '\Memory\Available MBytes','\Memory\Pages/sec','\Processor(_Total)\% Processor Time' -SampleInterval 10 -Continuous | Export-Counter -Path D:\Du\mem_log.csv -FileFormat CSV` (or Task Manager Details, adding Dedicated and Shared GPU memory for python).
3. Note what else uses the 3070 (the Windows desktop, any browser, a game, Steam) and whether Ramses is used interactively during the day.
4. Power: `powercfg /change standby-timeout-ac 0` and confirm the 3070 and Ramses never sleep (the known silent-freeze cause).
5. Optional H1 test: NVIDIA Control Panel, Manage 3D settings, CUDA - Sysmem Fallback Policy = Prefer No Sysmem Fallback. If the hub then fails to load or OOMs, the card is over budget; reversible.

**Phase 2: rehearse the Oct-7 server locally (a lab, this box, no Ramses)**
- Start `deploy/ramses/nascence_cpu_server.py` with a small GGUF on a spare port using exactly the Ramses flags (including `--host 0.0.0.0`, `--lazy --idle-unload 900`, `--log`). Check GET /api/status; repeat F-2466's abandon test (a 300-token job abandoned after 3 s must not delay the next call); show a deadline cut with `--max-gen-seconds 5`; confirm the JSON and free-text calls Du makes still parse (the response only adds `done_reason`, and nothing in core/ reads it).
- The local hubs also run the old file; this is its first live exercise anywhere, so do not skip it.

**Phase 3: deploy to Ramses (Ramses-side, about 20 minutes per hub set; do it before the Thursday marathon so the marathon's labs run on a measured lane)**
1. Back up: copy `//ramses/D/Du/nascence_cpu_server.py` to `nascence_cpu_server.py.aug23.bak`; record the SHA256 of both files.
2. Copy `deploy/ramses/nascence_cpu_server.py` over it; verify the SHA256 matches the repo file. Do not edit on Ramses (canonical files flow from the repo).
3. Check the launcher passes `--host 0.0.0.0` (the new server's default is loopback; the share's `start_ramses_tier.ps1` and the repo's `launch_ramses.ps1` both pass it explicitly; verify before restarting any hub).
4. Restart one hub at a time, least critical first: falcon3 :11436 (reserve), granite :11437, deepseek :11444 (Lane 2; a tick is 300 s), mixtral :11438 (judge 1 and dreams; loads in about 12 s), command-r7b :11441 last. For each: stop only that hub's process (match `nascence_cpu_server` and `--port NNNN` in the command line), start via `start_ramses_tier.ps1` (it skips running ports and spawns missing ones), then verify.
5. Per-hub check: GET /api/status returns JSON; one free-text and one JSON call return normally; the log line now carries a timestamp, `wait=`, `gen=` and `tok=`.
6. Deadline: the default `--max-gen-seconds 150` sits above Du's client timeouts (model_client 120 s, Lane 2 90 s); judge_panel's tiebreak asks granite with a 240 s timeout but granite answers in seconds. Leave the default; raise per hub only if /api/status counters show healthy calls being cut.
7. Du does not need a restart (client code unchanged, the J-1832 breaker will absorb the brief restart). Best done while Du is idle or down.
8. Rollback (5 minutes): stop the hub, copy the .bak back, start it again.

**Phase 4: watch for 72 hours and read the logs**
- Compare the Phase 0 monitor, the Ramses gpu and memory logs, and (after Phase 3) /api/status counters (`deadline_cuts`, `abandoned_before_gen`, `abandoned_during_gen`) against Du's own `llm_latency.jsonl`. Baselines to beat: 5.0% of :11441 calls at the ceiling in the current run, no stall over 30 minutes.

**Phase 5: act on what the measurements say**
- VRAM at or near 8 GB when a stall begins: shrink the footprint (smaller `n_batch`, a smaller context, a q8_0 KV cache: the hub would need a flag added in the repo), close whatever else holds VRAM, or move the Windows display to the 1650 (it is not driving a display) so the 3070 is compute-only. Keep Prefer No Sysmem Fallback on afterwards so an overflow is loud.
- VRAM fine, GPU utilisation at 0% with a generation in flight and rising time: a driver or hang problem: driver version, TDR settings (`TdrDelay`), temperature and power; Event Viewer.
- CPU saturated by other hubs: un-park J-1831 (thread caps so the sum stays under the physical core count and :11441 keeps a free core).
- Stalls gone after Phase 3 and the counters show cuts or abandons: the old server was the amplifier; keep the new one and the monitor.

## 4. Decisions this plan needs from Travis

1. Go ahead with Phases 0 to 3 (and who does the Ramses-side steps: Travis or Antigravity).
2. Whether D-0388's defeater counts as fired (5.0% in the current run, more than 10% on two days, a 4 hour window on 11-02), which would un-park J-1831, J-1871 and J-1643.
3. Whether the Windows display on Ramses can move to the 1650 if VRAM turns out to be the cause.

## 5. Risks and checks

- `--host`: the new server defaults to loopback; a hub started without `--host 0.0.0.0` becomes unreachable. Check before each restart.
- The new server is untested live (the local hubs run the old file): rehearse first (Phase 2).
- Restarting a lazy hub costs a first-call load (6 to 15 s; mixtral about 12 s); the breaker covers it.
- A 150 s deadline returns partial text with `done_reason=deadline`; watch `deadline_cuts`.
- The stall pattern may have more than one cause (H1 start, H2 amplifier); do not stop after the first improvement.

## 6. Pointers

- Findings: F-3872, F-3873, F-2466, F-2494, F-2556, F-2737; decisions D-0354, D-0388, D-0419, D-0057; jobs J-3278 (this follow-up), J-1830 (the Oct-7 server), J-1831 (thread caps, parked).
- Files: `deploy/ramses/nascence_cpu_server.py`, `//ramses/D/Du/` (hub logs, launcher, NASCENCE_NOTES.md), `data/llm_latency.jsonl`, `data/lane2_shadow.jsonl`.

## 7. Status log

- 2026-11-03: Phase 0 monitor built and verified (J-3279, commit 410277e2).
- 2026-11-05 06:52 NZDT: monitor started as a detached process (PID 30048, hidden, stdout and stderr in data/ramses_hub_monitor_stdout.log and _stderr.log). It does not survive a reboot or a Du Control Panel restart of Windows; restart it with python scripts/ramses_hub_monitor.py. Read it with python scripts/ramses_hub_monitor_read.py --hours 24 --du.
