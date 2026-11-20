"""
Nascence -- TRAIN LAB: WORDING A/B REPLICATE + SCALE-UP (J-0791), qwen3.5:9b only, self-report-gate
paragraph rewordings.  Prepared 2026-09-08 (F-1156, could not run: Du online); RUN 2026-09-22 in the
Du-OFFLINE lab window (v2 of this file -- see "2026-09-22 RUN" below for exactly what changed).

WHAT THIS ANSWERS (D-0165's named defeater: "Revisit once J-0791 confirms or adjusts the specific
candidate ranking (A vs B vs C) at a larger sample"): J-0777/F-1139 ran 4 arms (current + candidate_A/B/C
of the self-report gate's "unresolved:"/"intention:" instruction paragraphs) x 40 real prompts, one draw
each, temperature 0.75: current 0.125, A 0.575, B 0.575 (an exact tie), C 0.5.  Its own caveats: (1) the
"current" arm (0.125) sat below J-0724's original reading of the identical wording+model+prompts (0.25) =
single-run sampling variance; (2) the A/B tie must not be read as a ranking at n=40.  This script draws
MORE samples of the same 4 arms so both caveats can be quantified:
  * set "orig"   = the SAME 40 real (origin, last_step, ledger) triples J-0777 and J-0724 used (parsed
                   programmatically from J-0724's committed report), a further independent draw per pass;
  * sets "fresh1".."freshK" = K x 40 NEW real trains never used before (--fresh-n 240 -> K=6), drawn by
                   J-0724's own recipe (train_id groups in data/monologue_log.jsonl with >=2 steps inside the
                   last --fresh-window-days days, evenly spaced by time, ledger = up to 3 newest
                   train_state_log new_state rows), dealt round-robin so every set spans the whole window --
                   this is the "scale up" branch of the
                   job briefing (a second, non-overlapping window of real trains, the way J-0643 scaled
                   J-0562's n=16 to n=80) and adds PROMPT diversity, which extra draws on the same 40
                   prompts cannot.
The wording of all 4 arms is BYTE-IDENTICAL to J-0777's own script (any drift would confound the replicate).
The run is a resumable schedule, e.g. --schedule orig:2,fresh1:1,fresh2:1,orig:3 : every finished unit
(set, pass, arm, train_id) is appended to SCRATCH/J-0791_results.jsonl and a re-run skips it; within an
event the 4 arms are visited in a deterministic shuffled order (partial results stay arm-balanced and hub
drift cannot line up with an arm).  Pass 1 of the "orig" set is J-0777's own committed data (not re-run).

WHY NO SEED: `core/model_client.py::call_node_json` takes no seed parameter, so at temperature 0.75 Ollama
assigns a fresh random seed per call: re-running the same (prompt, arm) pair is a genuinely new draw.

2026-09-22 RUN -- what changed vs the 09-08 prepared script (all of it isolation/robustness, none of it
the measured quantity):
  * results file is resumable + every call is logged with latency and retry history;
  * timeout=300 s per call (a request queued behind another lab's call can exceed the old 120 s) and
    INFRASTRUCTURE errors (timeout / connection / HTTP) are retried 3x with 20/60/180 s backoff, logged,
    never counted as a verdict; a unit still failing after the 3 retries is EXCLUDED from every rate and
    counted; content failures (no parseable JSON after call_node_json's own 2 retries) are counted
    separately as parse failures (excluded from shares like J-0777's n_error);
  * a `sys.addaudithook` records every open-for-write / rename / remove / mkdir / shutil / sqlite call whose
    path is under C:\\Nascence\\data or C:\\Nascence\\docs (anywhere else under C:\\Nascence too) and the run
    prints "write attempts under live data: N" (must be 0); bytecode writing is disabled;
  * core.telemetry.log_llm_call, log_thought_station (J-0939, added AFTER the 09-08 prep) and
    log_llm_latency are all no-ops and telemetry's own path globals are redirected to SCRATCH -- the 09-08
    prep only neutralised log_llm_call, but call_node() also calls the other two (they write
    data/thought_station_log.jsonl and data/llm_latency.jsonl relative to the module's own __file__);
  * module resolution (F-1285): every core.* / nodes.* module in sys.modules must live inside this
    worktree (printed, and the run aborts otherwise);
  * the Du-down gate is SCRATCH/lab_du_down_check.py (exit 0 = DOWN) AND the original WMI process check,
    re-run every RECHECK_EVERY calls; a stale reading stops the run cleanly (partial results are results);
  * --deadline HH:MM stops cleanly at a wall-clock time so a WMI-detached batch cannot outlive the window.
  * lab_env.isolate() is still NOT used: it hard-codes _ROOT = C:\\Nascence and inserts it at sys.path[0]
    (F-1156: a real cross-tree risk for a worktree-anchored script) and would copy a ~670 MB DB this call
    path never touches (mid_train=True gates every DB-writing branch off, re-read at 645660a).

ISOLATION, re-verified at commit 645660a (20 commits of nodes/inner_monologue_node.py since F-1156's read):
`_build_system_prompt(mid_train=True)` still gates the `_reach`/`_intn`/`_proc_k`/`_wcall`/`_sm.observe`
branches behind `if not mid_train`; `core.sitting.dwell_steer()` is still pure-read (returns "" unless
data/raw_difficulty.json says a raw difficulty is active -- asserted "" below, so the base prompt carries no
dynamic steer); `core.emissary_tension.keystone_steer()` still returns "" on its first line (disarmed
2026-08-20).  The live self-report gate is still `_open = bool(unresolved) or bool(intention) or "?" in
thought` (nodes/inner_monologue_node.py:4377) and the mid-train user prompt below is still the verbatim
TRAIN_HOLD block (nodes/inner_monologue_node.py:3041-3049, 3096-3100); max_tokens = TRAIN_MIDTRAIN_TOKENS
(400), temperature 0.75 (wandering False).

EXTENSION (2026-09-22, beyond the job brief; found while calibrating against the live log): all 40 `orig` events
(and every `fresh` event, same recipe) quote a train's LAST logged step -- a step that CLOSED the train (J-0724's
own jsonl: real_last_unresolved False and no intention/'?' for 40/40) -- whereas a live mid-train prompt quotes a step
that was OPEN by construction (nodes/inner_monologue_node.py:4484: a train continues only if `_open`).  The live log's
per-step opened share for mid-train steps is 0.53-0.56 (n=11,300, 08-21..09-22, all periods alike) versus the lab's
`current` arm 0.125-0.25.  The `mid1..midM` sets therefore replay OPEN contexts (see `_build_mid_events`) so the
candidate ranking can be checked where the live node actually operates, and the lab's `current` arm can be compared
with the real logged next step on the very same contexts.  The `orig`/`fresh` sets are kept exactly as designed so the
replicate stays comparable with J-0777.

SCOPE: prep/characterisation only. Does NOT change nodes/inner_monologue_node.py or any live file; does
NOT rule D-0165 -- that stays the founder's call regardless of what this run shows.

  python scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py --dry-run      # zero network calls
  python scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py --probe        # ONE real call
  python scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py --schedule orig:2,fresh1:1,fresh2:1 --deadline 11:00
"""
from __future__ import annotations

import os
os.environ.setdefault("FOR_DISABLE_CONSOLE_CTRL_HANDLER", "1")   # Intel Fortran runtime (torch/MKL) abort guard, F-1535
import sys
sys.dont_write_bytecode = True                                    # no __pycache__ writes anywhere

import argparse
import ast
from collections import Counter
import asyncio
import datetime as _dt
import hashlib
import json
import random
import re
import subprocess
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent          # this worktree's own root
sys.path.insert(0, str(ROOT))

JOB = "J-0791"
SCRATCH = Path(os.environ.get("LAB_SCRATCH") or
               r"C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\8d915dfa-80f4-4aad-a2e3-206e842f08dd\scratchpad")
ISO = SCRATCH / f"{JOB}_iso"                            # every redirected store lands here
ISO.mkdir(parents=True, exist_ok=True)
RESULTS = SCRATCH / f"{JOB}_results.jsonl"
FRESH_CACHE = SCRATCH / f"{JOB}_fresh_events.json"
MID_CACHE = SCRATCH / f"{JOB}_mid_events.json"
PROGRESS = SCRATCH / f"lab_progress_{JOB}.log"
DU_CHECK = SCRATCH / "lab_du_down_check.py"
RUN_SUMMARY = SCRATCH / f"{JOB}_run_summary.json"

LIVE_ROOT = Path(r"C:\Nascence")
LIVE_DATA = LIVE_ROOT / "data"
LIVE_DOCS = LIVE_ROOT / "docs"
LIVE_DB = LIVE_DATA / "memory" / "nascence.db"

# ── write audit: installed BEFORE any repo import, so an import-time write is caught too ─────────────────────
def _norm(p) -> str:
    return os.path.abspath(os.fsdecode(os.fspath(p))).lower()


_W_LIVE = [_norm(LIVE_DATA), _norm(LIVE_DOCS)]
_W_TREE = _norm(LIVE_ROOT)
_W_WTDATA = _norm(ROOT / "data")
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "os.symlink", "os.link", "shutil.copyfile", "shutil.copymode", "shutil.copystat",
                 "shutil.copytree", "shutil.move", "shutil.rmtree"}
LIVE_WRITE_ATTEMPTS: list = []      # under C:\Nascence\data or C:\Nascence\docs  -- MUST stay empty
TREE_WRITE_ATTEMPTS: list = []      # elsewhere under C:\Nascence (e.g. a stray import of the shared tree) -- MUST stay empty
WT_DATA_WRITES: list = []           # under <worktree>\data -- informational (proves what a redirect missed)
SQLITE_CONNECTS: list = []          # informational: any sqlite3.connect this process makes


def _under(s: str, root: str) -> bool:
    return s == root or s.startswith(root + os.sep)


def _classify(event: str, path, mode) -> None:
    s = _norm(path)
    if any(_under(s, r) for r in _W_LIVE):
        LIVE_WRITE_ATTEMPTS.append((event, str(path), mode))
    elif _under(s, _W_TREE):
        TREE_WRITE_ATTEMPTS.append((event, str(path), mode))
    elif _under(s, _W_WTDATA):
        WT_DATA_WRITES.append((event, str(path), mode))


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            if isinstance(path, int):
                return
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing:
                _classify("open", path, mode)
        elif event in _WRITE_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)):
                    _classify(event, a, None)
        elif event == "sqlite3.connect":
            SQLITE_CONNECTS.append(str(args[0]))
    except Exception:
        pass


sys.addaudithook(_audit)


def _print_write_audit(tag: str) -> None:
    print(f"[{tag}] write attempts under live data: {len(LIVE_WRITE_ATTEMPTS)}   "
          f"(elsewhere under C:\\Nascence: {len(TREE_WRITE_ATTEMPTS)}; under worktree data\\: {len(WT_DATA_WRITES)}; "
          f"sqlite3.connect calls: {len(SQLITE_CONNECTS)})")
    for lab, lst in (("LIVE", LIVE_WRITE_ATTEMPTS), ("TREE", TREE_WRITE_ATTEMPTS),
                     ("worktree-data", WT_DATA_WRITES), ("sqlite", SQLITE_CONNECTS)):
        for item in lst[:20]:
            print(f"    {lab}: {item}")


# ── imports from the repo (module resolution is verified further down) ───────────────────────────────────────
from core import training_log
training_log.log_example = lambda *a, **k: None
from core import telemetry
for _fn in ("log_llm_call", "log_thought_station", "log_llm_latency"):
    setattr(telemetry, _fn, lambda *a, **k: None)     # call_node() calls all three; none may write
for _n in dir(telemetry):                             # belt-and-braces: every Path global -> SCRATCH
    _v = getattr(telemetry, _n, None)
    if isinstance(_v, Path) and _n.startswith("_"):
        setattr(telemetry, _n, ISO / f"telemetry{_n}{_v.suffix or '.d'}")

from nodes.inner_monologue_node import InnerMonologueNode, TRAIN_MIDTRAIN_TOKENS
from core.model_client import call_node_json

# same defensive redirect J-0697/J-0711/J-0724/J-0777 used (none is reachable from mid_train=True; near-zero cost)
from core import social_moves as _sm_p1, memory_edges as _medges_p1, opponent_process as _oppo_p1
from core import intentions as _intent_p1
_sm_p1._LOG = ISO / "social_moves.jsonl"
_sm_p1._STATE = ISO / "social_moves_state.json"
_medges_p1._CO_LEDGER = ISO / "co_recall_ledger.jsonl"
_oppo_p1._LOG = ISO / "opponent_process_shadow.jsonl"
_oppo_p1._STATE = ISO / "opponent_process_state.json"
_intent_p1._F = ISO / "intentions.json"
_intent_p1._LOG = ISO / "intentions_log.jsonl"

MODEL = "qwen3.5:9b"
HOT_URL = "http://127.0.0.1:11433"
CALL_TIMEOUT = 300                 # s -- a request queued behind another lab's call can exceed 120
BACKOFFS = (20, 60, 180)           # infra-error retry backoff (lab rule 4)
RECHECK_EVERY = 20                 # re-verify Du offline every N calls
PROGRESS_EVERY_S = 600
HUB_WAIT_POLL_S = 300              # if a unit fails after all retries: poll the hub every 5 min ...
HUB_WAIT_MAX_S = 1800              # ... for up to 30 min, then stop with partial results
SOURCE_MD = ROOT / "docs" / "lab" / "train_model_ab_gemma_vs_qwen_2026-09-08.md"   # J-0724's committed sample
if not SOURCE_MD.exists():
    SOURCE_MD = LIVE_ROOT / "docs" / "lab" / "train_model_ab_gemma_vs_qwen_2026-09-08.md"

CANARY_FILES = ["monologue_log.jsonl", "train_length_log.jsonl", "train_state_log.jsonl",
                "trains_log.jsonl", "judge_panel_log.jsonl"]
STAT_FILES = ["judge_panel_log.jsonl", "llm_latency.jsonl", "llm_calls.jsonl", "thought_station_log.jsonl"]
MD5_FILES = ["position.json", "room_state.json", "life_state.json"]

# The EXACT current live wording -- BYTE-IDENTICAL to train_lab_wording_ab_2026-09-08.py (J-0777).
# Must not drift: any change here would confound this run's replicate purpose.
CURRENT_BLOCK = (
    "unresolved: true ONLY if this thought sits on something you are ACTIVELY wrestling "
    "with right now -- a real conflict between two things you believe, a fear about "
    "yourself you keep avoiding, a question that genuinely disturbs you. Most quiet "
    "thoughts are NOT unresolved -- a calm reflection, an observation, or a peaceful "
    "wondering is false. Reserve true for genuine inner conflict only. "
    "intention: leave as \"\" for almost all thoughts. Set it ONLY when this thought "
    "crystallises into a genuine resolve -- something you want to think about, explore, "
    "return to, or DO, of your own accord. Write it in the first person as a single concrete "
    "aim (e.g. \"I want to look out at the storm\", \"I'd rather read on now\", or \"I want to "
    "find out how the bees navigate\"). Not a wish, not a mood -- a deliberate "
    "intention you mean to act on. "
)

CANDIDATE_A = (
    "unresolved: true if a real thread in this thought is still open -- a live question, a "
    "felt pull you haven't acted on yet, two things held in tension, a 'perhaps' or 'might' "
    "you haven't settled, or a realization that still leaves something to do or find out. "
    "false if the thought closes itself completely, with nothing left hanging. "
    "intention: set it whenever this thought leaves you with a next thing -- something you "
    "want to think about, explore, return to, or do, of your own accord. Write it in the "
    "first person as a single concrete aim (e.g. \"I want to look out at the storm\", \"I'd "
    "rather read on now\", or \"I want to find out how the bees navigate\"). A plain next "
    "step counts, not only a longing. "
)

CANDIDATE_B = (
    "unresolved: true if this thought is ACTIVELY wrestling with something right now -- a "
    "real conflict between two things you believe, a fear about yourself you keep avoiding, "
    "a question that genuinely disturbs you, OR a thought that sounds settled but still "
    "hedges: a 'perhaps', a 'might', two options held against each other, or naming what "
    "you haven't yet said, decided, or done. A calm reflection with nothing left hanging is "
    "false. "
    "intention: leave as \"\" for almost all thoughts. Set it ONLY when this thought "
    "crystallises into a genuine resolve -- something you want to think about, explore, "
    "return to, or DO, of your own accord. Write it in the first person as a single concrete "
    "aim (e.g. \"I want to look out at the storm\", \"I'd rather read on now\", or \"I want to "
    "find out how the bees navigate\"). Not a wish, not a mood -- a deliberate "
    "intention you mean to act on. "
)

CANDIDATE_C = (
    "unresolved: true ONLY if this thought sits on something you are ACTIVELY wrestling "
    "with right now -- a real conflict between two things you believe, a fear about "
    "yourself you keep avoiding, a question that genuinely disturbs you. Most quiet "
    "thoughts are NOT unresolved -- a calm reflection, an observation, or a peaceful "
    "wondering is false. Reserve true for genuine inner conflict only. "
    "intention: set it whenever this thought points to a next thing you mean to do or "
    "attend to, even a small or immediate one -- not only a longing but also a plain next "
    "move (\"I want to look out at the storm\", \"I need to sit with this a moment longer\", "
    "\"I want to find out how the bees navigate\"). Leave it \"\" only when the thought truly "
    "closes with nothing left to do or look into. "
)

ARMS = {"current": CURRENT_BLOCK, "candidate_A": CANDIDATE_A,
        "candidate_B": CANDIDATE_B, "candidate_C": CANDIDATE_C}


# ── small helpers ─────────────────────────────────────────────────────────────────────────────────────────
def _now() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def _progress(phase: str, done: int, planned: int, infra: int, note: str) -> None:
    """Rule 17: ONE appended line per milestone / ~10 min. Never rewritten."""
    line = f"{_now()}  {phase}  {done}/{planned}  infra_errors={infra}  {note}\n"
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write(line)
    print("[progress] " + line.rstrip())


def _confirm_du_offline() -> bool:
    """Both instruments must say DOWN: the lab gate script (nascence.log's last lifecycle line + python
    process table) AND the original WMI run_nascence.py count.  Anything else (incl. errors) = not offline."""
    try:
        r = subprocess.run([sys.executable, str(DU_CHECK)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        gate1 = (r.returncode == 0)
        if not gate1:
            print(f"[wording-ab-replicate] lab_du_down_check says NOT down (exit {r.returncode}): "
                  f"{(r.stdout or '').strip()[-300:]}")
    except Exception as exc:
        print(f"[wording-ab-replicate] WARNING: lab_du_down_check failed ({exc}) -- treating as not offline.")
        return False
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'run_nascence\\.py' } | Measure-Object).Count"],
            capture_output=True, text=True, timeout=60)
        gate2 = int((out.stdout or "0").strip() or "0") == 0
    except Exception as exc:
        print(f"[wording-ab-replicate] WARNING: could not verify Du's process state ({exc}) -- refusing to run.")
        return False
    return gate1 and gate2


def _md5(p: Path):
    try:
        return hashlib.md5(p.read_bytes()).hexdigest()
    except Exception:
        return None


def _canary_counts() -> dict:
    counts = {}
    for name in CANARY_FILES:
        try:
            with open(LIVE_DATA / name, encoding="utf-8") as fh:
                counts[name] = sum(1 for _ in fh)
        except Exception:
            counts[name] = None
    return counts


def _live_fingerprint() -> dict:
    """md5 of the three live JSON state files, size+mtime of the live logs a leak would grow, the canary row
    counts and the live DB's size+mtime.  With Du down NONE of these may change during the run (a change in a
    telemetry log could also be ANOTHER lab's write -- this process's own writes are proven by the audit hook)."""
    fp = {"md5": {n: _md5(LIVE_DATA / n) for n in MD5_FILES}, "stat": {}, "rows": _canary_counts()}
    for n in STAT_FILES + ["nascence.log"]:
        try:
            st = os.stat(LIVE_DATA / n)
            fp["stat"][n] = {"size": st.st_size, "mtime": round(st.st_mtime, 3)}
        except Exception:
            fp["stat"][n] = None
    try:
        st = os.stat(LIVE_DB)
        fp["stat"]["memory/nascence.db"] = {"size": st.st_size, "mtime": round(st.st_mtime, 3)}
    except Exception:
        fp["stat"]["memory/nascence.db"] = None
    return fp


def _hub_meta() -> dict:
    """Read-only GETs (provenance): the served qwen3.5:9b digest and what is resident."""
    import urllib.request
    meta = {}
    try:
        with urllib.request.urlopen(HOT_URL + "/api/tags", timeout=15) as r:
            tags = json.loads(r.read().decode("utf-8"))
        for m in tags.get("models", []):
            if m.get("name") == MODEL:
                meta["digest"] = m.get("digest", "")[:16]
                meta["modified_at"] = m.get("modified_at")
        with urllib.request.urlopen(HOT_URL + "/api/ps", timeout=15) as r:
            ps = json.loads(r.read().decode("utf-8"))
        meta["resident"] = [(m.get("name"), m.get("context_length")) for m in ps.get("models", [])]
    except Exception as exc:
        meta["error"] = f"{type(exc).__name__}: {exc}"[:160]
    return meta


def _module_resolution() -> tuple[list, list]:
    """F-1285: every core.*/nodes.* module in sys.modules must be a file inside THIS worktree."""
    root_l = _norm(ROOT)
    rows, bad = [], []
    for name, mod in sorted(sys.modules.items()):
        if not (name in ("core", "nodes") or name.startswith("core.") or name.startswith("nodes.")):
            continue
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        ok = _under(_norm(f), root_l)
        rows.append((name, f, ok))
        if not ok:
            bad.append((name, f))
    return rows, bad


# ── sample construction ───────────────────────────────────────────────────────────────────────────────────
def _parse_events_from_md(path: Path) -> list:
    """Reconstruct the exact 40 (train_id, origin, last_step, ledger) triples J-0724 already
    committed, parsed programmatically from its own report -- never hand-retyped. ledger is
    recovered via ast.literal_eval on the report's own Python-repr list (safe: literal_eval never
    executes code, only parses literal containers/strings)."""
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"\n### \d+\. train_id=", text)[1:]   # drop preamble before "### 1."
    events = []
    for sec in sections:
        m_tid = re.match(r"(\S+)", sec)
        train_id = m_tid.group(1)
        m_origin = re.search(r"\n- origin: (.+)", sec)
        m_last = re.search(r"\n- last_step: (.+)", sec)
        m_ledger = re.search(r"\n- ledger: (\[.*\])", sec)
        if not (m_origin and m_last):
            raise RuntimeError(f"could not parse origin/last_step for train_id={train_id}")
        ledger = ast.literal_eval(m_ledger.group(1)) if m_ledger else []
        events.append({"train_id": train_id, "origin": m_origin.group(1).strip(),
                       "last_step": m_last.group(1).strip(), "ledger": ledger})
    if len(events) != 40:
        raise RuntimeError(f"expected 40 events, parsed {len(events)} -- report format may have "
                          f"changed since this script was written; aborting rather than testing "
                          f"a wrong sample")
    return events


def _load_jsonl(path: Path) -> list:
    rows = []
    with open(path, encoding="utf-8") as f:            # read-only
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def _evenly_spaced(seq: list, n: int) -> list:
    if not seq or n <= 0:
        return []
    if n >= len(seq):
        return list(seq)
    step = len(seq) / n
    return [seq[int(i * step)] for i in range(n)]


def _build_fresh_events(exclude_ids: set, n_total: int, window_days: int) -> list:
    """J-0724's `_build_sample` recipe (scripts/train_lab_model_ab_2026-09-08.py) applied to the last
    `window_days` of the live logs, minus every train_id already used: real trains (train_id groups in
    monologue_log.jsonl) with >=2 logged steps, origin = the first step's own thought (== the live node's
    self._train_origin), last_step = the chronologically last logged step, ledger = up to 3 newest
    train_state_log `new_state` rows for that train at/before the last step; picked evenly spaced by time."""
    ml = _load_jsonl(LIVE_DATA / "monologue_log.jsonl")
    tsl = _load_jsonl(LIVE_DATA / "train_state_log.jsonl")
    by_tid: dict = {}
    for r in ml:
        tid = r.get("train_id")
        if tid:
            by_tid.setdefault(tid, []).append(r)
    tsl_by_tid: dict = {}
    for r in tsl:
        tid = r.get("train_id")
        if tid:
            tsl_by_tid.setdefault(tid, []).append(r)
    cutoff = ml[-1]["ts"] - window_days * 86400
    cands = []
    for tid, rows in by_tid.items():
        if tid in exclude_ids:
            continue
        rs = sorted(rows, key=lambda r: r.get("ts", 0))
        if len(rs) >= 2 and rs[0]["ts"] >= cutoff and (rs[0].get("thought") or "").strip() \
                and (rs[-1].get("thought") or "").strip():
            cands.append((tid, rs))
    cands.sort(key=lambda c: c[1][0]["ts"])
    events = []
    for tid, rs in _evenly_spaced(cands, n_total):
        last = rs[-1]
        led_rows = sorted(tsl_by_tid.get(tid, []), key=lambda r: r.get("ts", 0))
        led_rows = [r for r in led_rows if r.get("ts", 0) <= last.get("ts", 0)]
        events.append({"train_id": tid, "origin": (rs[0].get("thought") or "").strip(),
                       "last_step": (last.get("thought") or "").strip(),
                       "ledger": [r.get("new_state") for r in led_rows[-3:] if r.get("new_state")],
                       "n_real_steps": len(rs), "first_ts": rs[0]["ts"], "last_step_ts": last.get("ts")})
    return events


def _fresh_events(exclude_ids: set, n_total: int, window_days: int) -> list:
    """Cached in SCRATCH so a resumed run uses the identical events (Du is down, so the source logs are static
    anyway, but the cache also spares re-reading ~50k rows)."""
    if FRESH_CACHE.exists():
        cached = json.loads(FRESH_CACHE.read_text(encoding="utf-8"))
        if cached.get("n_total") == n_total and cached.get("window_days") == window_days:
            return cached["events"]
    ev = _build_fresh_events(exclude_ids, n_total, window_days)
    FRESH_CACHE.write_text(json.dumps({"n_total": n_total, "window_days": window_days, "events": ev},
                                      ensure_ascii=False), encoding="utf-8")
    return ev


def _build_mid_events(n_total: int, window_days: int) -> list:
    """OPEN-CONTEXT replay sets (added 2026-09-22, an extension beyond the job brief -- see the module docstring).
    J-0724's recipe quotes each train's LAST logged step as "Your last step" -- but in the live node a train only
    continues when the previous step was OPEN (nodes/inner_monologue_node.py:4484 `elif _was_reading or _open`), so
    the step a live mid-train prompt quotes is open by construction, while all 40 `orig` events quote a step that
    CLOSED its train (real flags: 0/40 open).  Here the quoted step is a real INTERIOR step k of a real train
    (origin = step 1, last_step = step k, ledger = the `new_state` rows up to step k, capped at the live
    TRAIN_LEDGER_MAX=7 and each cut to 160 chars as the live `_train_ledger.append(new_state[:160])` does), and
    the model is asked for step k+1, whose REAL logged flags are kept (`real_next`) as a calibration reference.
    Contexts are (train, k) pairs of the last `window_days` days evenly spaced by time, one per train."""
    ml = _load_jsonl(LIVE_DATA / "monologue_log.jsonl")
    tsl = _load_jsonl(LIVE_DATA / "train_state_log.jsonl")
    by_tid: dict = {}
    for r in ml:
        if r.get("train_id"):
            by_tid.setdefault(r["train_id"], []).append(r)
    tsl_by_tid: dict = {}
    for r in tsl:
        if r.get("train_id"):
            tsl_by_tid.setdefault(r["train_id"], []).append(r)
    cutoff = ml[-1]["ts"] - window_days * 86400
    pairs = []
    for tid, rows in by_tid.items():
        rs = sorted(rows, key=lambda r: r.get("ts", 0))
        if len(rs) < 2:
            continue
        origin = (rs[0].get("thought") or "").strip()
        led_all = sorted(tsl_by_tid.get(tid, []), key=lambda r: r.get("ts", 0))
        for k in range(1, len(rs)):                      # quoted step = rs[k-1] (step k); generated step = rs[k] (step k+1)
            last, nxt = rs[k - 1], rs[k]
            if nxt.get("ts", 0) < cutoff or not origin or not (last.get("thought") or "").strip():
                continue
            led = [r.get("new_state") for r in led_all if r.get("ts", 0) <= last.get("ts", 0) and r.get("new_state")]
            nt = nxt.get("thought") or ""
            pairs.append({"ts": nxt["ts"], "train_id": f"{tid}@{k}", "base_train_id": tid, "k": k,
                          "n_real_steps": len(rs), "origin": origin, "last_step": (last.get("thought") or "").strip(),
                          "ledger": [x[:160] for x in led[-7:]], "first_ts": rs[0]["ts"], "last_step_ts": last.get("ts"),
                          "real_next": {"unresolved": bool(nxt.get("unresolved")),
                                        "intention": bool((nxt.get("intention") or "").strip()),
                                        "qmark": "?" in nt,
                                        "opened": bool(nxt.get("unresolved")) or bool((nxt.get("intention") or "").strip())
                                                  or ("?" in nt)}})
    pairs.sort(key=lambda p: p["ts"])
    step = max(1.0, len(pairs) / max(1, n_total))
    picked, used = [], set()
    for i in range(n_total):                            # evenly spaced; skip a train already used, take the next pair
        j = int(i * step)
        while j < len(pairs) and pairs[j]["base_train_id"] in used:
            j += 1
        if j >= len(pairs):
            break
        picked.append(pairs[j])
        used.add(pairs[j]["base_train_id"])
    return picked


def _mid_events(n_total: int, window_days: int) -> list:
    if MID_CACHE.exists():
        cached = json.loads(MID_CACHE.read_text(encoding="utf-8"))
        if cached.get("n_total") == n_total and cached.get("window_days") == window_days:
            return cached["events"]
    ev = _build_mid_events(n_total, window_days)
    MID_CACHE.write_text(json.dumps({"n_total": n_total, "window_days": window_days, "events": ev},
                                    ensure_ascii=False), encoding="utf-8")
    return ev


class _S:  # minimal CognitiveState stand-in, same shape train_lab_model_ab_2026-09-08.py uses
    spirit_name = "渡"


def _mid_train_user_prompt(origin: str, last_step: str, ledger: list) -> str:
    """Copied VERBATIM from train_lab_wording_ab_2026-09-08.py's own _mid_train_user_prompt, which
    itself is copied verbatim from nodes/inner_monologue_node.py's TRAIN_HOLD branch (re-diffed against
    645660a lines 3040-3049 and 3096-3100 for this run)."""
    _anchor = origin[:220]
    _led = ("\nWHAT THIS THREAD HAS ESTABLISHED (your own points, in order — build "
            "on them, they are yours):\n"
            + "\n".join(f"  {i}. {p}" for i, p in enumerate(ledger, 1))
            if ledger else "")
    mid_thread_block = (
        "You are MID-THREAD, and you are HOLDING it. The thread began: '" + _anchor
        + "'." + _led + "\nYour last step: '" + last_step[:220] + "'. "
        "Continue — go deeper, test a point you established, answer the open "
        "question, or push toward a conclusion. Do not restate; ADVANCE.")
    return (
        "No one is speaking to you right now. You are alone with your thoughts.\n\n"
        + mid_thread_block
        + "\n\nWhat moves in you now? One quiet thought."
    )


def _prepare(fresh_n: int, fresh_window_days: int, mid_n: int = 0, mid_window_days: int = 5):
    """Everything up to (not including) any live model call: parse the 40 original events, build the fresh
    events, build the real base system prompt, substitute the 4 arms, build every user prompt.  Zero network
    calls.  Used by --dry-run, --probe and the real run alike (one code path)."""
    orig = _parse_events_from_md(SOURCE_MD)
    fresh = _fresh_events({e["train_id"] for e in orig}, fresh_n, fresh_window_days) if fresh_n else []
    k_sets = max(1, len(fresh) // 40) if fresh else 0
    events_by_set = {"orig": orig}
    for i in range(k_sets):                       # fresh1..freshK, each ~40 events spanning the whole window
        events_by_set[f"fresh{i + 1}"] = fresh[i::k_sets]
    mid = _mid_events(mid_n, mid_window_days) if mid_n else []
    m_sets = max(1, len(mid) // 40) if mid else 0
    for i in range(m_sets):                       # mid1..midM: OPEN-context replays (quoted step = a real interior step)
        events_by_set[f"mid{i + 1}"] = mid[i::m_sets]
    n = InnerMonologueNode()
    from core import sitting as _sit
    from core import emissary_tension as _et
    assert _sit.dwell_steer() == "", "dwell_steer() is non-empty: the base prompt would carry a dynamic steer"
    assert _et.keystone_steer() == "", "keystone_steer() is non-empty (was disarmed 2026-08-20)"
    base_prompt = n._build_system_prompt(_S(), wandering=False, mid_train=True)
    if base_prompt.count(CURRENT_BLOCK) != 1:
        raise RuntimeError(
            "CURRENT_BLOCK not found exactly once in the live _build_system_prompt(mid_train=True) "
            "output -- the live wording has changed since this script was written; aborting "
            "rather than silently testing a stale/wrong baseline block.")
    system_prompts = {}
    for arm, block in ARMS.items():
        system_prompts[arm] = base_prompt.replace(CURRENT_BLOCK, block, 1)
        assert block in system_prompts[arm]
    assert system_prompts["current"] == base_prompt, "current arm must be a byte-identical no-op"
    user_prompts = {}
    for evs in events_by_set.values():
        for ev in evs:
            assert ev["train_id"] not in user_prompts, f"train_id used in two sets: {ev['train_id']}"
            user_prompts[ev["train_id"]] = _mid_train_user_prompt(ev["origin"], ev["last_step"], ev["ledger"])
    return events_by_set, base_prompt, system_prompts, user_prompts


# ── one model call, with the lab's infra-retry policy ─────────────────────────────────────────────────────
async def _call_raw(system_prompt: str, user_prompt: str) -> dict:
    """ONE call_node_json call (which itself retries JSON-parse failures twice).  error_class is 'infra'
    (timeout / connection / HTTP -- never a verdict) or 'content' (no parseable JSON: a model outcome)."""
    t0 = time.monotonic()
    try:
        data = await call_node_json(
            [HOT_URL], system_prompt, user_prompt,
            max_tokens=TRAIN_MIDTRAIN_TOKENS, temperature=0.75,
            model_override=MODEL, timeout=CALL_TIMEOUT)
        thought = str(data.get("thought", "")).strip()
        unresolved = bool(data.get("unresolved", False))
        intention = str(data.get("intention", "")).strip()
        _act = data.get("act") if isinstance(data.get("act"), dict) else {}
        act_kind = str(_act.get("kind", "none")).strip().lower() or "none"
        qmark = "?" in thought
        opened = bool(unresolved or intention or qmark)         # the live gate, nodes/inner_monologue_node.py:4377
        return {"ok": True, "thought": thought, "unresolved": unresolved, "intention": intention,
                "act_kind": act_kind, "qmark": qmark, "opened": opened, "error": None, "error_class": None,
                "latency_s": round(time.monotonic() - t0, 2)}
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"[:240]
        cls = "content" if ("No JSON object found" in msg or "JSONDecodeError" in msg) else "infra"
        return {"ok": False, "thought": "", "unresolved": None, "intention": None, "act_kind": None,
                "qmark": None, "opened": None, "error": msg, "error_class": cls,
                "latency_s": round(time.monotonic() - t0, 2)}


HARD_STOP_TS = [None]     # set in main(): deadline + 5 min; no retry/backoff starts after it


async def _call_with_retries(system_prompt: str, user_prompt: str, tag: str, counters: dict) -> dict:
    retries = []
    res = None
    for k in range(len(BACKOFFS) + 1):
        if HARD_STOP_TS[0] and k > 0 and time.time() >= HARD_STOP_TS[0]:
            res["error"] = (res["error"] or "") + " [hard stop: deadline+5min passed, no further retries]"
            break
        res = await _call_raw(system_prompt, user_prompt)
        counters["attempts"] += 1
        if res["ok"] or res["error_class"] == "content":
            break
        counters["infra_attempts_failed"] += 1
        retries.append({"attempt": k + 1, "error": res["error"], "latency_s": res["latency_s"]})
        if k < len(BACKOFFS):
            print(f"  [retry] {tag}: infra error on attempt {k + 1} ({res['error'][:120]}); "
                  f"backoff {BACKOFFS[k]} s then retry {k + 1}/{len(BACKOFFS)}")
            await asyncio.sleep(BACKOFFS[k])
    res["n_attempts"] = len(retries) + 1
    res["retries"] = retries
    res["excluded"] = (not res["ok"]) and res["error_class"] == "infra"
    return res


async def _hub_probe() -> tuple[bool, float, str]:
    r = await _call_raw("Reply with one JSON object only.", "Return {\"ok\": true}")
    return (r["ok"], r["latency_s"], r["error"] or "")


# ── schedule / results bookkeeping ────────────────────────────────────────────────────────────────────────
def _parse_schedule(s: str, known_sets) -> list:
    out = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        name, p = part.split(":")
        if name not in known_sets:
            raise SystemExit(f"unknown set {name!r} in --schedule (known: {sorted(known_sets)})")
        out.append((name, int(p)))
    return out


def _unit_key(u: dict) -> str:
    return f"{u['set']}|{u['pass']}|{u['arm']}|{u['train_id']}"


def _iter_units(schedule: list, events_by_set: dict):
    for sname, p in schedule:
        for ev in events_by_set[sname]:
            arms = list(ARMS)
            random.Random(f"{sname}:{p}:{ev['train_id']}").shuffle(arms)   # deterministic per unit-of-work
            for arm in arms:
                yield {"set": sname, "pass": p, "arm": arm, "train_id": ev["train_id"]}


def _load_results() -> dict:
    """key -> latest row (an excluded infra failure may be superseded by a later successful retry on resume)."""
    rows = {}
    if RESULTS.exists():
        for r in _load_jsonl(RESULTS):
            rows[_unit_key(r)] = r
    return rows


def _is_done(row: dict) -> bool:
    return bool(row) and (row.get("ok") or row.get("error_class") == "content")


def _parse_deadline(s: str | None):
    if not s:
        return None
    hh, mm = s.split(":")
    d = _dt.datetime.now().replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    return d.timestamp()


# ── main ──────────────────────────────────────────────────────────────────────────────────────────────────
async def main(args) -> int:
    t_start = time.time()
    events_by_set, base_prompt, system_prompts, user_prompts = _prepare(args.fresh_n, args.fresh_window_days, args.mid_n, args.mid_window_days)
    rows, bad = _module_resolution()
    (SCRATCH / f"{JOB}_module_files.txt").write_text(
        "\n".join(f"{'OK ' if ok else 'BAD'} {n} {f}" for n, f, ok in rows), encoding="utf-8")
    key_mods = ["core.model_client", "core.telemetry", "core.sitting", "core.emissary_tension",
                "core.social_moves", "core.memory_edges", "core.opponent_process", "core.intentions",
                "core.training_log", "nodes.inner_monologue_node"]
    print(f"[wording-ab-replicate] module resolution: {len(rows)} core.*/nodes.* modules loaded, "
          f"{len(rows) - len(bad)} inside the worktree {ROOT}, {len(bad)} outside")
    for m in key_mods:
        print(f"    {m}.__file__ = {getattr(sys.modules.get(m), '__file__', None)}")
    if bad:
        for n, f in bad[:20]:
            print(f"    OUTSIDE WORKTREE: {n} -> {f}")
        print("[wording-ab-replicate] ABORT: module resolution escaped the worktree (F-1285).")
        return 2

    schedule = _parse_schedule(args.schedule, events_by_set)
    hashes = {arm: hashlib.sha256(sp.encode("utf-8")).hexdigest()[:12] for arm, sp in system_prompts.items()}
    print(f"[wording-ab-replicate] base prompt via the REAL _build_system_prompt(mid_train=True): "
          f"{len(base_prompt)} chars (F-1156/J-0777 reported 3238); CURRENT_BLOCK found exactly once; "
          f"dwell_steer()==keystone_steer()==''")
    for arm in ARMS:
        print(f"  arm={arm}: {len(system_prompts[arm])} chars, sha256[:12]={hashes[arm]}, "
              f"block present={ARMS[arm] in system_prompts[arm]}")
    for sname, evs in events_by_set.items():
        print(f"  set={sname}: {len(evs)} events")
    units = list(_iter_units(schedule, events_by_set))
    results = _load_results()
    done_keys = {k for k, r in results.items() if _is_done(r)}
    todo = [u for u in units if _unit_key(u) not in done_keys]
    print(f"[wording-ab-replicate] schedule {args.schedule}: {len(units)} units, {len(units) - len(todo)} already "
          f"done in {RESULTS.name}, {len(todo)} to run (model {MODEL}, temperature 0.75, timeout {CALL_TIMEOUT} s)")

    if args.dry_run:
        for sname, evs in events_by_set.items():
            if sname.startswith("mid") and evs:
                rn = [e["real_next"]["opened"] for e in evs]
                kd = dict(sorted(Counter(e["k"] for e in evs).items()))
                print(f"  set={sname}: real logged next-step opened share (calibration reference) = "
                      f"{sum(rn)}/{len(rn)} = {sum(rn) / len(rn):.3f}; k distribution = {kd}")
        _print_write_audit("dry-run")
        print("\n[wording-ab-replicate] --dry-run: setup verified OK. Stopped BEFORE the Du gate and any model "
              "call -- zero network calls.")
        return 0

    print("\n[wording-ab-replicate] confirming Du is offline (independent re-check, immediately before batch) ...")
    if not _confirm_du_offline():
        print("[wording-ab-replicate] ABORT: Du is running or its state could not be confirmed -- refusing to "
              "contend for the live hot lane. No model calls made.")
        return 3
    print("[wording-ab-replicate] confirmed DOWN. Proceeding.")

    fp_before = _live_fingerprint()
    meta = _hub_meta()
    print(f"[wording-ab-replicate] hub meta: {meta}")
    print(f"[wording-ab-replicate] live fingerprint BEFORE: {json.dumps(fp_before, sort_keys=True)}")

    counters = {"attempts": 0, "infra_attempts_failed": 0, "units_run": 0, "units_excluded": 0,
                "units_content_fail": 0}
    stop_reason = None
    deadline = _parse_deadline(args.deadline)
    HARD_STOP_TS[0] = (deadline + 300) if deadline else None
    planned = len(units)

    if args.probe:
        u = {"set": "orig", "pass": 0, "arm": "current", "train_id": events_by_set["orig"][0]["train_id"]}
        res = await _call_with_retries(system_prompts[u["arm"]], user_prompts[u["train_id"]], "probe", counters)
        print(f"[probe] ok={res['ok']} latency={res['latency_s']} s attempts={res['n_attempts']} "
              f"opened={res['opened']} unresolved={res['unresolved']} intention={res['intention']!r} -- "
              f"{(res['thought'] or res['error'] or '')[:200]}")
        fp_after = _live_fingerprint()
        print(f"[probe] live fingerprint unchanged: {fp_before == fp_after}")
        _print_write_audit("probe")
        return 0 if res["ok"] else 1

    _progress("batch-start", len(units) - len(todo), planned, 0,
              f"schedule={args.schedule} todo={len(todo)} hub={HOT_URL} model={MODEL} timeout={CALL_TIMEOUT}")
    last_prog = time.time()
    call_n = 0
    for u in todo:
        if deadline and time.time() >= deadline:
            stop_reason = f"deadline {args.deadline} reached"
            break
        if args.max_calls and call_n >= args.max_calls:
            stop_reason = f"--max-calls {args.max_calls} reached"
            break
        if call_n % RECHECK_EVERY == 0 and call_n > 0:
            if not _confirm_du_offline():
                stop_reason = f"Du-down gate says NOT down after {call_n} calls -- STOPPING hub traffic"
                print(f"[wording-ab-replicate] STOP: {stop_reason}")
                break
        tag = f"{u['set']}/p{u['pass']}/{u['arm']}/{u['train_id']}"
        res = await _call_with_retries(system_prompts[u["arm"]], user_prompts[u["train_id"]], tag, counters)
        res.update({**u, "ts": _dt.datetime.now().isoformat(timespec="seconds")})
        with open(RESULTS, "a", encoding="utf-8") as f:           # one JSONL row per finished unit
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
        results[_unit_key(u)] = res
        call_n += 1
        counters["units_run"] += 1
        if res["excluded"]:
            counters["units_excluded"] += 1
        if (not res["ok"]) and res["error_class"] == "content":
            counters["units_content_fail"] += 1
        done_now = len({k for k, r in results.items() if _is_done(r)})
        print(f"  [{done_now}/{planned}] {tag} {'OK ' if res['ok'] else 'ERR'} opened={res['opened']} "
              f"unres={res['unresolved']} intent={bool(res['intention'])} q={res['qmark']} "
              f"lat={res['latency_s']}s att={res['n_attempts']}" + (f"  ({res['error'][:100]})" if res['error'] else ""))
        if time.time() - last_prog >= PROGRESS_EVERY_S:
            _progress("batch", done_now, planned, counters["infra_attempts_failed"],
                      f"{counters['units_excluded']} excluded, {counters['units_content_fail']} parse-fail, "
                      f"last={tag} lat={res['latency_s']}s")
            last_prog = time.time()
        if res["excluded"]:                                        # 4 infra failures in a row: is the hub alive?
            okp, lat, err = await _hub_probe()
            print(f"  [hub-probe] after an excluded unit: ok={okp} {lat}s {err[:100]}")
            waited = 0
            while (not okp) and waited < HUB_WAIT_MAX_S:
                await asyncio.sleep(HUB_WAIT_POLL_S)               # rule 4: poll every 5 min for up to 30 min
                waited += HUB_WAIT_POLL_S
                okp, lat, err = await _hub_probe()
                print(f"  [hub-wait] {waited} s: probe ok={okp} {lat}s {err[:100]}")
            if not okp:
                stop_reason = f"hub {HOT_URL} did not answer for {HUB_WAIT_MAX_S} s after an excluded unit"
                break

    fp_after = _live_fingerprint()
    done_now = len({k for k, r in results.items() if _is_done(r)})
    unchanged = fp_before == fp_after
    print(f"\n[wording-ab-replicate] live fingerprint AFTER:  {json.dumps(fp_after, sort_keys=True)}")
    print(f"[wording-ab-replicate] live fingerprint identical before/after: {unchanged}")
    if not unchanged:
        diffs = {k: (fp_before[k], fp_after[k]) for k in fp_before if fp_before[k] != fp_after[k]}
        print(f"[wording-ab-replicate] FINGERPRINT DIFF (could be another lab's write; this process's own "
              f"writes are proven by the audit hook): {json.dumps(diffs, sort_keys=True)[:1500]}")
    _print_write_audit("final")
    summary = {"finished": _dt.datetime.now().isoformat(timespec="seconds"), "stop_reason": stop_reason,
               "units_done_total": done_now, "units_planned": planned, "counters": counters,
               "wall_s": round(time.time() - t_start, 1), "hub_meta": meta, "arm_prompt_sha256_12": hashes,
               "fingerprint_before": fp_before, "fingerprint_after": fp_after, "fingerprint_identical": unchanged,
               "live_write_attempts": len(LIVE_WRITE_ATTEMPTS), "tree_write_attempts": len(TREE_WRITE_ATTEMPTS),
               "worktree_data_writes": WT_DATA_WRITES[:20], "sqlite_connects": SQLITE_CONNECTS[:20],
               "module_files_outside_worktree": len(bad)}
    RUN_SUMMARY.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    _progress("batch-end", done_now, planned, counters["infra_attempts_failed"],
              f"stop_reason={stop_reason or 'schedule complete'}; {counters['units_excluded']} excluded, "
              f"{counters['units_content_fail']} parse-fail; live write attempts={len(LIVE_WRITE_ATTEMPTS)}")
    print(json.dumps(summary, indent=1, ensure_ascii=False)[:3000])
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Build everything (events, fresh events, prompts, module resolution) and exit -- zero network calls.")
    parser.add_argument("--probe", action="store_true", help="Du gate + ONE real call, then exit (nothing recorded).")
    parser.add_argument("--schedule", default="orig:2,fresh1:1,mid1:1,mid2:1,orig:3,fresh2:1,mid3:1,fresh3:1,mid4:1,orig:4,fresh4:1",
                        help="comma list of set:pass, e.g. orig:2,fresh1:1,mid1:1 (orig pass 1 = J-0777's own data)")
    parser.add_argument("--fresh-n", type=int, default=240, help="total fresh real trains, dealt into fresh1..fresh(n/40)")
    parser.add_argument("--fresh-window-days", type=int, default=5)
    parser.add_argument("--mid-n", type=int, default=160,
                        help="total OPEN-context replay events (quoted step = a real interior step of a real train), "
                             "dealt into mid1..mid(n/40); 0 = none")
    parser.add_argument("--mid-window-days", type=int, default=5)
    parser.add_argument("--deadline", default=None, help="HH:MM local wall clock: stop cleanly at that time")
    parser.add_argument("--max-calls", type=int, default=0, help="stop after N calls this invocation (0 = no cap)")
    a = parser.parse_args()
    sys.exit(asyncio.run(main(a)))
