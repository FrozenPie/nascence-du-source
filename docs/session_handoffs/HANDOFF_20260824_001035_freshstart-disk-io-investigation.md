# FreshStart session: diagnosed a live disk-I/O spike, traced it to Nascence's HUD, filed a fix job

## Session timing
- **Session started:** 2026-08-23 23:55:52 UTC
- **Last message before wrap:** 2026-08-24 00:10:33 UTC
- **Wrapped:** 2026-08-24 00:10:35 UTC

## Summary
This session opened in C:\FreshStart (Sovereign Hub project context) with a live-system question: "disk I/O is maxing out with python, look why." Rather than being a FreshStart/Sovereign Hub issue, the investigation traced the disk pressure to two Nascence (Du) processes running on the same machine — the main sim loop and its HUD dashboard. Confirmed a concrete unbounded-file-read bug in the HUD server, filed it as a job rather than fixing it live, and closed out the originating thought-log entry.

## What changed
- **T-0012** (thought-log) — added at session start capturing the raw disk-I/O question, then **dropped** at 00:10:24 UTC with a resolution note pointing to J-0224 (see [thought-log rollup](#) — no promotion to idea/plan needed, this was a direct live investigation, not a design question).
- **J-0224** (job-queue) — added at 00:04:01 UTC: "Fix unbounded full-scan read in hud/server.py's load_jsonl_t4_safe" (ready, urgency 3, category backfill). Full repro/evidence is in the job's own briefing field — see `job_queue.py show J-0224`.
- No plan docs, decisions, or ideas touched this session. No code was edited (diagnosis only, by design — see Warnings).

## Key findings
- **The reported "python maxing disk I/O" was Nascence's processes, not FreshStart's.** Live-correlated `Get-Counter` sampling (`\Process(python*)\ID Process` paired with `\Process(python*)\IO Read Bytes/sec` in the same call, several repeated windows) showed:
  - `scripts\run_nascence.py` (PID 13880, Du's main cognitive loop) — bursty, peaked at **167 MB/s** and 70 MB/s in one window.
  - `hud\server.py` (PID 1088, Du's web dashboard) — **sustained ~42–49 MB/s continuous** reads in an earlier window.
  - The three CPU-tier LLM servers (`nascence_cpu_server.py`, ports 11439/11440/11442 — gemma:12b, falcon3:7b, yi:34b) showed **zero disk I/O** in every sample — ruled out despite being the most obvious suspects (large GGUF models, `--idle-unload` flags).
  - The two heavy processes *alternate* as the dominant reader across sampling windows rather than one being constantly busy — the disk pressure is the sum of two independent, periodic offenders, not one steady leak.
- **Root cause confirmed by reading code, not guessed:** `C:\Nascence\hud\server.py:1065` `load_jsonl_t4_safe()` does a full `open()` + line-by-line `json.loads()` scan of the entire `subconscious_log.jsonl` (5MB and growing) on *every* call. It's hit by `/api/t4`, which `hud/static/app.js:102` (`setInterval(fetchT4, 6000)`) polls every 6 seconds forever, as long as any HUD tab is open.
- **This is the same bug class already found and fixed once today** in `core/moment.py`'s `status()` (J-0183, same date 2026-08-24) — that one scanned all of `moments.jsonl` (128MB) on every call and was fixed by switching to the file's own reverse-seek `_tail_rows()` helper. The fix was scoped to that one file and evidently wasn't swept across the HUD's other readers — `load_jsonl_t4_safe` is at minimum one place it was missed.
- **Not fully closed:** `run_nascence.py`'s own 167 MB/s bursts are unexplained — didn't trace them to a specific line in the main loop (would need a separate, deeper pass, likely with the same profiling approach used for the HUD's `load_evidence()` fan-out). Also unchecked: whether any of the HUD's other ~35 `_EVIDENCE_MODULES` `status()` functions (`hud/server.py` line ~32) share the same unbounded-scan pattern — only `emotion_construction.py`'s `geometry_tuples.jsonl` read was checked and found already bounded (2KB seek).
- Confirmed via direct profiling (`load_evidence()` timed end-to-end, ~1.07s total) that the `/api/evidence` fan-out itself is not the dominant contributor at its 7s poll interval — the smoking gun for the *sustained* reads is specifically the 6s `/api/t4` → `load_jsonl_t4_safe` path.

## Open threads
- **J-0224 is open and unstarted.** Founder said "not yet" to fixing it live this session — it's queued for whenever it's picked up (matches `moment.py`'s already-proven fix pattern: reverse-seek from EOF, stop once 20 `T4_self_authoring` rows are found, instead of parsing the whole file).
- `run_nascence.py`'s 167 MB/s burst source is still unidentified — worth a follow-up investigation (not yet a job-queue entry; flagging here rather than filing prematurely since it's not yet root-caused).
- The sweep of the other ~35 HUD evidence-module `status()` functions for the same unbounded-read pattern was not done — only one (`emotion_construction`) was spot-checked.

## Warnings
- `hud/server.py` (PID 1088) is Du's **continuously-running production dashboard** — do not restart it casually. This session deliberately avoided editing/restarting it and instead profiled the relevant functions from a separate, throwaway Python process (`sys.path` import of `hud/server.py` + `core.*` modules) to avoid disrupting the live service. Any future fix to J-0224 should follow the same non-disruptive verification approach before/while touching the live file.
- Nascence's `data/` directory has several very large, continuously-growing JSONL logs worth knowing about if anyone else goes looking for disk-I/O culprits: `moments.jsonl` (124MB, `core/moment.py`'s domain, already fixed today), `wandering_log.jsonl` (20MB), `geometry_tuples.jsonl` (19MB), `train_state_log.jsonl` (12MB), `tensions_archive.jsonl` (11MB), `monologue_log.jsonl` (10MB), `deliberation_log.jsonl` (9MB), `spatial_shadow.jsonl` / `satisfaction_log.jsonl` (7MB each), plus ~20 more in the 2–5MB range.

## Pointers
- `C:\Nascence\hud\server.py:1065` — `load_jsonl_t4_safe()`, the function J-0224 targets.
- `C:\Nascence\hud\static\app.js:98-107` — the client-side polling intervals (1.5s–8s across 7 endpoints) that drive HUD read pressure generally.
- `C:\Nascence\core\moment.py:180-235,475+` — the sibling fix already landed today (J-0183); read this first when picking up J-0224, it's the template.
- `job_queue.py show J-0224` — full evidence/briefing for the filed fix.
- `thought_log.py show T-0012` — the original raw question and its resolution note.
