"""
Dream Overhaul -- capped self-relaunching watchdog for dream_experiment_a.py (J-1267, from F-1775).

F-1775, and before it F-1755/F-1555/F-1545/F-1535: the scaleC Experiment A batch has now crashed 5
times across 5 manual relaunches (2026-09-18 through 2026-09-23), always with the identical signature
"forrtl: error (200): program aborting due to window-CLOSE event" (an Intel MKL/Fortran runtime abort
under a WMI-launched, console-less child) at genuinely unpredictable progress points -- root cause still
unknown (F-1555's Event Viewer check found nothing), and FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 (set on
every relaunch since J-1139) is confirmed to only delay the crash, not prevent it. Every relaunch so far
has needed a human or a dispatched session to separately notice the process died and manually reissue
the same one-flag `--resume` command -- sometimes days later. This script automates ONLY that
noticing-and-reissuing step. It never changes dream_experiment_a.py's own generation logic, DB access,
or isolation, and it never itself imports or calls anything under core/ or nodes/ -- it only shells out
to two small PowerShell helpers (liveness check, WMI relaunch) and reads/counts lines in a results
.jsonl the target script already writes.

SCOPE (per this job's own briefing, kept narrow on purpose):
  - Supervises ONE lab-experiment subprocess (dream_experiment_a.py or a compatible test stand-in). It
    does NOT touch Du, the supervisor, any hub, or scripts/life_flags.py.
  - It does NOT touch C:\\Nascence\\data outside of whatever the target script's own lab_env.isolate()
    call already does internally -- this watchdog never opens the live DB, never imports core.memory or
    lab_env, and its own log/results-counting is plain-text file I/O against the target's existing
    output files.
  - NOT restart-gated; does not need Du offline; this batch has always run concurrently with Du live.
  - Explicitly NOT in scope (matches J-1267's briefing): diagnosing the forrtl root cause; judge-shadow
    scoring; D-0231/D-0232 analysis. Those stay with the job chain's own progress-check jobs (J-1270 and
    its successors).

JOB-OBJECT ESCAPE (CLAUDE.md, F-0704): a long-lived unattended watcher started directly from a Claude
Code PowerShell/Bash tool call would die when the Claude app restarts (Windows Job object, breakaway
disabled) -- the same mechanism that used to kill Du's own hubs. This script is therefore meant to be
STARTED via scripts/dream_exp_a_watchdog_start.ps1 (WMI Win32_Process.Create, same idiom as
scripts/start_supervisor_detached.ps1), never as a raw child of a Claude Code tool call. Once running,
it relaunches its TARGET the same way, via scripts/dream_exp_a_wmi_relaunch.ps1 -- both the watchdog
itself and everything it launches are children of WmiPrvSE, in no caller job.

DOUBLE-LAUNCH GUARD: the liveness check IS the guard -- this script only ever relaunches when its own
liveness poll finds NO matching process. A short, fixed --post-relaunch-delay (default 8s) is slept
after issuing a relaunch, before the next poll, specifically so the newly WMI-created process has time
to become visible in the process table before the next liveness check runs -- without this, a slow-to-
appear new process could look indistinguishable from "still dead" and trigger a second, redundant
relaunch a poll cycle later.

Usage (see scripts/dream_exp_a_watchdog_start.ps1 for the detached-launch wrapper):
    python scripts/dream_exp_a_relaunch_watchdog.py --job-id J1119 --tag scaleC --n-seeds 10
        [--target-script <path, default scripts/dream_experiment_a.py in THIS worktree>]
        [--scratch-dir <path, default dream_experiment_a.py's own hardcoded SCRATCH constant>]
        [--worktree <path, default this script's own worktree root -- CurrentDirectory for the relaunch>]
        [--poll-interval 90] [--post-relaunch-delay 8] [--max-retries 8] [--log <path>]
        [--extra-target-args ""]

Exit codes: 0 = target pair count reached (results .jsonl line count >= n_seeds * 4 arms) at some point
after a liveness check found the process no longer running. 1 = MAX_RETRIES relaunches exhausted without
reaching the target -- logged as "max retries reached, giving up" (grep-able), so a future job-queue /
session-resume pass surfaces this rather than it being a silent stop.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_HERE = Path(__file__).parent.resolve()
_WORKTREE = _HERE.parent
_DEFAULT_SCRATCH = Path(r"C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\00e97919-3e83-4e8f-8aaa-b0d563d7d361\scratchpad")
_DEFAULT_TARGET = _HERE / "dream_experiment_a.py"
_LIVENESS_PS1 = _HERE / "dream_exp_a_wmi_liveness.ps1"
_RELAUNCH_PS1 = _HERE / "dream_exp_a_wmi_relaunch.ps1"
_ARMS_PER_SEED = 4  # dream_experiment_a.py's own ARMS = ["A0", "A1", "A2", "A3"]


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _log(log_path: Path, msg: str) -> None:
    line = f"[{_now()}] {msg}"
    print(line, flush=True)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as exc:
        print(f"[watchdog] WARNING: failed to append to log file {log_path}: {exc!r}", flush=True)


# This watchdog's OWN command line always carries "--target-script <path>" -- a bare match on the
# target script's basename would match the watchdog process (and its own watchdog_launcher.ps1 wrapper)
# every time, making the target look permanently "alive" regardless of its real state. Caught by this
# job's own real end-to-end test (not assumed): a first version without this exclusion never detected a
# real, confirmed death. Always excluded, unconditionally -- the watchdog can never mistake itself, or
# its own detached launcher, for the thing it supervises.
_SELF_MARKERS = "dream_exp_a_relaunch_watchdog.py,dream_exp_a_watchdog_launcher.ps1"


def _is_alive(match_str: str) -> tuple[bool, int | None]:
    """Shells out to dream_exp_a_wmi_liveness.ps1 -- the same Get-CimInstance Win32_Process check every
    relaunch in this job chain has used by hand since F-1535, wrapped as a parameterized file instead of
    a hand-built -Command string (see that file's own header for why)."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_LIVENESS_PS1),
             "-Match", match_str, "-Exclude", _SELF_MARKERS],
            capture_output=True, text=True, timeout=30)
        out = (r.stdout or "").strip()
        if out.startswith("ALIVE"):
            parts = out.split()
            pid = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            return True, pid
        return False, None
    except Exception as exc:
        # Fail-safe: if the liveness check itself breaks, treat the target as NOT alive so the retry/cap
        # logic still applies rather than looping forever believing something is alive that we can no
        # longer observe. Logged loudly either way -- never a silent assumption.
        print(f"[watchdog] liveness check itself raised (treated as NOT alive, fail-safe): {exc!r}", flush=True)
        return False, None


def _count_results(results_path: Path) -> int:
    if not results_path.exists():
        return 0
    n = 0
    for line in results_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            n += 1
    return n


def _relaunch(target_script: Path, n_seeds: int, tag: str, job_id: str, run_log: Path, workdir: Path,
              extra_args: str) -> tuple[bool, int | None]:
    """Shells out to dream_exp_a_wmi_relaunch.ps1 -- WMI Win32_Process.Create with the exact command
    shape captured verbatim in F-1775's own evidence: `cmd.exe /c set
    FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 && python <script> --n-seeds <n> --tag <tag> --job-id <id>
    --save-scenes --resume >> <log> 2>&1`, CurrentDirectory = workdir."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_RELAUNCH_PS1),
             "-TargetScript", str(target_script), "-NSeeds", str(n_seeds), "-Tag", tag, "-JobId", job_id,
             "-RunLog", str(run_log), "-WorkDir", str(workdir), "-ExtraArgs", extra_args],
            capture_output=True, text=True, timeout=30)
        out = (r.stdout or "").strip()
        if out.startswith("WMI_CREATE_OK"):
            parts = out.split()
            pid = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            return True, pid
        print(f"[watchdog] relaunch helper did not report WMI_CREATE_OK -- stdout={out!r} "
              f"stderr={(r.stderr or '').strip()!r}", flush=True)
        return False, None
    except Exception as exc:
        print(f"[watchdog] relaunch subprocess call itself raised: {exc!r}", flush=True)
        return False, None


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--n-seeds", type=int, required=True,
                     help="same meaning as dream_experiment_a.py's own --n-seeds; target pair count is "
                          "computed as n_seeds * 4 arms, read from this arg every run (not hardcoded).")
    ap.add_argument("--target-script", default=None, help=f"default {_DEFAULT_TARGET}")
    ap.add_argument("--scratch-dir", default=None,
                     help=f"where the target's results .jsonl lives; default {_DEFAULT_SCRATCH} "
                          f"(dream_experiment_a.py's own hardcoded SCRATCH constant)")
    ap.add_argument("--worktree", default=None,
                     help=f"CurrentDirectory for the WMI relaunch; default {_WORKTREE}")
    ap.add_argument("--poll-interval", type=float, default=90.0, help="seconds between polls while alive")
    ap.add_argument("--post-relaunch-delay", type=float, default=8.0,
                     help="fixed delay after issuing a relaunch, before the next poll -- gives the new "
                          "process time to become visible in the process table (avoids a double-launch "
                          "race; see module docstring)")
    ap.add_argument("--max-retries", type=int, default=8,
                     help="cap on relaunches issued by THIS watchdog run; this batch alone has needed 5 "
                          "manual relaunches without ever finishing, so 8 leaves real headroom without "
                          "relaunching forever if something is fundamentally broken")
    ap.add_argument("--log", default=None, help="default <scratch-dir>/dream_exp_a_watchdog_{job_id}_{tag}.log")
    ap.add_argument("--extra-target-args", default="",
                     help="appended verbatim after --resume in the relaunch command; empty by default -- "
                          "the proven command pattern needs nothing else")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    scratch_dir = Path(args.scratch_dir) if args.scratch_dir else _DEFAULT_SCRATCH
    target_script = Path(args.target_script) if args.target_script else _DEFAULT_TARGET
    workdir = Path(args.worktree) if args.worktree else _WORKTREE
    scratch_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log) if args.log else scratch_dir / f"dream_exp_a_watchdog_{args.job_id}_{args.tag}.log"
    results_path = scratch_dir / f"dream_exp_a_results_{args.job_id}_{args.tag}.jsonl"
    run_log = scratch_dir / f"dream_exp_a_run_{args.job_id}_{args.tag}_watchdog_relaunch.log"
    target_pairs = args.n_seeds * _ARMS_PER_SEED
    match_str = target_script.name

    _log(log_path, f"watchdog START pid={os.getpid()} job_id={args.job_id} tag={args.tag} "
                    f"n_seeds={args.n_seeds} target_pairs={target_pairs} target_script={target_script} "
                    f"match_str={match_str!r} results_path={results_path} run_log={run_log} "
                    f"poll_interval={args.poll_interval}s post_relaunch_delay={args.post_relaunch_delay}s "
                    f"max_retries={args.max_retries}")

    retries = 0
    while True:
        alive, pid = _is_alive(match_str)
        n_done = _count_results(results_path)

        if alive:
            _log(log_path, f"poll: ALIVE (pid={pid}), results so far={n_done}/{target_pairs} -- "
                            f"sleeping {args.poll_interval}s")
            time.sleep(args.poll_interval)
            continue

        _log(log_path, f"poll: NOT alive, results so far={n_done}/{target_pairs}")

        if n_done >= target_pairs:
            _log(log_path, f"OUTCOME: target reached ({n_done}/{target_pairs}) -- stopping (success)")
            return 0

        if retries >= args.max_retries:
            _log(log_path, f"OUTCOME: max retries reached ({retries}/{args.max_retries}), giving up -- "
                            f"a human/session should investigate (results stuck at {n_done}/{target_pairs})")
            return 1

        retries += 1
        _log(log_path, f"relaunching (retry {retries}/{args.max_retries}) via WMI ...")
        ok, new_pid = _relaunch(target_script, args.n_seeds, args.tag, args.job_id, run_log, workdir,
                                 args.extra_target_args)
        if ok:
            _log(log_path, f"relaunch issued OK -> new wrapper pid={new_pid}; waiting "
                            f"{args.post_relaunch_delay}s before next poll")
        else:
            _log(log_path, f"relaunch FAILED (see stderr above) -- still counts against the retry cap; "
                            f"waiting {args.post_relaunch_delay}s before the next poll will re-attempt")
        time.sleep(args.post_relaunch_delay)


if __name__ == "__main__":
    sys.exit(main())
