"""J-1198 lab runner: the D-0213 walk-back replay (Du-OFFLINE lab window, 2026-09-22, Part 2).

WHAT THIS IS. The n=80 replay of docs/plans/train_split_merge.md's Step 2 disprove mechanism, exactly the
one J-1086 ran on 2026-09-18 (`python scripts/train_state_invitro.py 40`, n_per_window=40, byte-identical
window A via the deterministic `_evenly_spaced`, plus window B), but run against the J-1198 build of
`scripts/train_state_invitro.py` (D-0213 re-ruled 2026-09-18: the SECOND, scope-only disprove call no longer
falls through to UNDETERMINED on a TIEBREAK-decided verdict; the FIRST call's fallback is untouched).

HOW IT DIFFERS FROM `python scripts/train_state_invitro.py 40` (and ONLY this). It exec()s every definition of
that script (everything above its `if True:` main block, Part 1's in-vitro checks included) into one namespace,
then runs the script's own `_run_step2_lab(40, ...)` unchanged, with the lab window's rules wrapped around it
IN THIS PROCESS ONLY (core/judge_panel.py, core/model_client.py and the script's own event selection, prompts,
`_prove`, `_disprove`, control check and report writer are NOT modified):
  * rule 4 (infrastructure errors): `core.judge_panel._ask` and `core.model_client.call_node` are wrapped so every
    request gets timeout >= 300 s (the module default of 90 s is bound at import and a request queued behind
    another lab's call can exceed it and read as a false `unavailable`); a `timeout`/`http`/`exception` error is
    infrastructure, NEVER a verdict: retried 3 times with backoff (20 s, 60 s, 180 s), every retry logged, counted
    per hub; a unit that still fails after the retries is EXCLUDED from every rate (never counted UNDETERMINED);
  * rule 5 (isolation): a sys.addaudithook records every write-shaped call under C:\\Nascence\\data or
    C:\\Nascence\\docs (must be 0), the telemetry and judge-panel log paths are redirected to SCRATCH before any
    call, and the live files' md5 / size+mtime are recorded before and after;
  * rule 7 (long batch): every finished unit is appended to a resumable JSONL (a re-run skips finished units);
  * rule 2 (Du-down gate): re-checked every 30 minutes by the heartbeat; UP-or-UNKNOWN stops all hub traffic;
  * every `rule_detail()` call (both votes, tiebreak vote, why-texts, the exact prompt) is appended to a calls
    JSONL, which Part 3 (scripts/lab_j1198_part3_tiebreak_reads.py) reads back.

Usage (from inside the worktree):
    python -u scripts/lab_j1198_walkback_replay.py --dry        # build the events only, no model calls
    python -u scripts/lab_j1198_walkback_replay.py --probe-only # preflight the four hubs only
    python -u scripts/lab_j1198_walkback_replay.py 40           # the real run (detach it: see start_j1198_replay.ps1)
    python -u scripts/lab_j1198_walkback_replay.py 40 --harvest [--max-units 60] [--target-tb 28]   # see below

NOTE on revisions: the main replay ran the revision of this file that PRECEDED two later, behaviour-neutral-for-the-main-run
edits: the preflight was moved from a nested function into the module-level `preflight()`, and the `--harvest` mode was
added (with `UNIT_PHASE`/`UNITS_HARVEST`/`CALLS_HARVEST`). `--harvest` (extra units run only to find more second-call
TIEBREAK-decided prompts for Part 3, never in a tally) was built and its event selection verified (it reproduces the
main run's events exactly and shares none with them), but it was NOT used: the main replay already held more than the
24 tiebreak-decided second calls the brief asks Part 3 to re-ask, so its hub-running half is untested.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("FOR_DISABLE_CONSOLE_CTRL_HANDLER", "1")   # rule 7: torch/MKL-linked Fortran runtime abort
os.environ.setdefault("PYTHONUNBUFFERED", "1")

import asyncio
import datetime as dt
import hashlib
import json
import subprocess
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent                      # the WORKTREE
SCRIPT = ROOT / "scripts" / "train_state_invitro.py"
SCRATCH = Path(os.environ.get("J1198_SCRATCH") or ROOT.parent)
JOB = "J-1198"
LIVE_DATA = Path(r"C:\Nascence\data")
LIVE_DOCS = Path(r"C:\Nascence\docs")

UNITS_PATH = SCRATCH / "lab_j1198_units.jsonl"        # one row per finished unit (resumable)
CALLS_PATH = SCRATCH / "lab_j1198_calls.jsonl"        # every rule_detail() call with its exact prompt
UNITS_HARVEST = SCRATCH / "lab_j1198_units_harvest.jsonl"   # --harvest mode only (extra units, never in the tallies)
CALLS_HARVEST = SCRATCH / "lab_j1198_calls_harvest.jsonl"
UNIT_PHASE = "unit"                                   # "harvest" in --harvest mode
HARVEST_BASE = 1000                                   # harvest unit ids are 1001... (never collide with 1..80)
INFRA_PATH = SCRATCH / "lab_j1198_infra.jsonl"        # every infrastructure error / retry / exclusion
SNAP_BEFORE = SCRATCH / "lab_j1198_livesnap_before.json"
SNAP_AFTER = SCRATCH / "lab_j1198_livesnap_after.json"
SUMMARY_PATH = SCRATCH / "lab_j1198_run_summary.json"
PROGRESS = SCRATCH / f"lab_progress_{JOB}.log"
DU_CHECK = SCRATCH / "lab_du_down_check.py"
TEL_DIR = SCRATCH / "lab_j1198_tel"                   # redirected telemetry paths (rule 5)

LAB_TIMEOUT = 300                                     # rule 4: use timeout=300 in OUR process only
BACKOFF = (20, 60, 180)                               # rule 4: retry 3 times with backoff
INFRA_ERRS = ("timeout", "http", "exception")         # infrastructure, never a verdict ('parse' is the judge's own output)

# ---------------------------------------------------------------------------------------------------------
# rule 5: write audit. Installed FIRST, before any repo import can touch a file.
# ---------------------------------------------------------------------------------------------------------
_WATCH = [str(LIVE_DATA).lower(), str(LIVE_DOCS).lower()]
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "os.link", "os.symlink", "shutil.copyfile", "shutil.copymode", "shutil.copystat",
                 "shutil.copytree", "shutil.move", "shutil.rmtree"}
LIVE_WRITE_ATTEMPTS: list = []


def _under_watch(p) -> bool:
    try:
        if isinstance(p, int):
            return False
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in _WATCH)


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing and _under_watch(path):
                LIVE_WRITE_ATTEMPTS.append(("open", str(path), mode))
        elif event in _WRITE_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and _under_watch(a):
                    LIVE_WRITE_ATTEMPTS.append((event, str(a), None))
                    break
    except Exception:
        pass


sys.addaudithook(_audit)

# ---------------------------------------------------------------------------------------------------------
# progress log (rule 17), run state
# ---------------------------------------------------------------------------------------------------------
STATS: dict = defaultdict(lambda: {"calls": 0, "ok": 0, "infra_errors": 0, "retries": 0, "persistent_fail": 0,
                                   "parse": 0, "secs": []})
CUR = {"unit": None, "phase": None, "attempt": 0, "persistent": set()}
STOP = {"flag": None}
DONE: dict = {}          # (idx, close_ts) -> stored unit row
EXCLUDED: list = []      # infra-excluded units
T_START = time.time()
PLANNED = {"n": 0}


def _now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def progress(phase: str, done: int, planned: int, note: str) -> None:
    infra = sum(s["infra_errors"] for s in STATS.values())
    line = f"{_now()}  {phase}  {done}/{planned}  infra_errors={infra}  {note}"
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def _append_jsonl(path: Path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _md5(p: Path) -> str:
    try:
        return hashlib.md5(p.read_bytes()).hexdigest()
    except Exception:
        return ""


def live_snapshot() -> dict:
    """rule 5: md5 of the three small live state files, size+mtime of the two live logs."""
    snap = {}
    for f in ("position.json", "room_state.json", "life_state.json"):
        p = LIVE_DATA / f
        snap[f] = {"md5": _md5(p), "exists": p.exists()}
    for f in ("judge_panel_log.jsonl", "llm_latency.jsonl"):
        p = LIVE_DATA / f
        try:
            st = p.stat()
            snap[f] = {"size": st.st_size, "mtime": st.st_mtime}
        except Exception:
            snap[f] = {"exists": False}
    return snap


# ---------------------------------------------------------------------------------------------------------
# hub probes (urllib, no telemetry, no judge log) and the Du-down gate
# ---------------------------------------------------------------------------------------------------------
_PROBE_SYS = 'Reply with JSON only: {"ok": true}'


def probe_hub_sync(name: str, base: str, model: str, ollama: bool, timeout: float = 120.0):
    payload = {"model": model, "stream": False, "format": "json",
               "messages": [{"role": "system", "content": _PROBE_SYS}, {"role": "user", "content": "ping"}],
               "options": {"temperature": 0.0, "num_predict": 24}}
    if ollama:
        payload["think"] = False
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(base + "/api/chat", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        content = ((data.get("message") or {}).get("content") or "")[:60]
        return True, round(time.monotonic() - t0, 1), content
    except Exception as e:
        return False, round(time.monotonic() - t0, 1), f"{type(e).__name__}: {str(e)[:80]}"


async def probe(name: str, timeout: float = 120.0):
    base, model, ollama = HUBS[name]
    return await asyncio.to_thread(probe_hub_sync, name, base, model, ollama, timeout)


async def du_is_down() -> bool:
    """rule 2. Exit 0 of the orchestrator's own check = DOWN; anything else (UP or UNKNOWN) = stop."""
    def _run():
        r = subprocess.run([sys.executable, str(DU_CHECK)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
        return r.returncode, (r.stdout or "").strip().splitlines()[-1:] or [""]
    try:
        rc, tail = await asyncio.to_thread(_run)
    except Exception as e:                       # noqa: BLE001 -- an unreadable check is UNKNOWN
        return False
    return rc == 0


async def wait_for_hubs(names, total: float = 1800.0, every: float = 300.0) -> bool:
    """rule 4: a hub that does not answer in 120 s -> poll every 5 minutes for up to 30 minutes."""
    t0 = time.monotonic()
    while True:
        res = await asyncio.gather(*[probe(n) for n in names])
        bad = [n for n, (ok, _s, _d) in zip(names, res) if not ok]
        _append_jsonl(INFRA_PATH, {"ts": time.time(), "event": "hub_poll", "hubs": list(names),
                                   "results": {n: r for n, r in zip(names, res)}})
        if not bad:
            progress("hub-healed", len(DONE), PLANNED["n"], f"hubs answered again: {list(names)}")
            return True
        if time.monotonic() - t0 >= total or STOP["flag"]:
            progress("hub-down", len(DONE), PLANNED["n"],
                     f"still not answering after {int((time.monotonic()-t0)/60)} min: {bad}")
            return False
        progress("hub-wait", len(DONE), PLANNED["n"], f"not answering: {bad}; polling every {int(every)} s")
        slept = 0.0
        while slept < every and not STOP["flag"]:
            await asyncio.sleep(20)
            slept += 20


# ---------------------------------------------------------------------------------------------------------
# repo imports: the WORKTREE's copy must win (F-1285), telemetry redirected (rule 5)
# ---------------------------------------------------------------------------------------------------------
sys.path.insert(0, str(ROOT))
import core                                                   # noqa: E402
from core import judge_panel as _jp                           # noqa: E402
from core import model_client as _mc                          # noqa: E402
from core import telemetry as _tel                            # noqa: E402

HUBS = {"HOT": ("http://127.0.0.1:11433", "qwen3.5:9b", True),
        "JUDGE_2": (_jp.JUDGE_2, "judge", False),
        "TIEBREAK": (_jp.TIEBREAK, "judge", False),
        "JUDGE_1": (_jp.JUDGE_1, "judge", False)}
_HUB_NAME = {_jp.JUDGE_1: "JUDGE_1", _jp.JUDGE_2: "JUDGE_2", _jp.TIEBREAK: "TIEBREAK"}
assert HUBS["JUDGE_1"][0] == "http://LAN-HOST:11438" and HUBS["JUDGE_2"][0] == "http://127.0.0.1:11440" \
    and HUBS["TIEBREAK"][0] == "http://LAN-HOST:11437", "judge hubs moved: re-read the lab rules"

TEL_DIR.mkdir(parents=True, exist_ok=True)
_tel._DATA = TEL_DIR
_tel._CALLS = TEL_DIR / "llm_calls.jsonl"
_tel._HW = TEL_DIR / "hardware_load.jsonl"
_tel._LLM = TEL_DIR / "llm_usage.jsonl"
_tel._LAT = TEL_DIR / "llm_latency.jsonl"
_tel._STATIONS = TEL_DIR / "thought_station_log.jsonl"
_jp._DATA = SCRATCH / "lab_j1198_jp"
_jp._DATA.mkdir(parents=True, exist_ok=True)
_jp._LOG = _jp._DATA / "judge_panel_log_scratch.jsonl"

# The script's Part 1 (the in-vitro checks at its top, run on every invocation) calls
# InnerMonologueNode._build_system_prompt(), which reaches ~19 world-store writers (core/garden.py,
# core/wood_life.py, ...) fenced by core.profile.guard_path (D-0179: a non-live process that resolves a write
# to a data/ path is REFUSED). J-1086 got past the fence by wrapping the run in lab_env.isolate() (a lab dir
# under C:\Nascence\data\_lab plus a ~670 MB DB copy) -- this window forbids that (writes under live data;
# disk at 14 percent free). The fence's own documented remedy is "redirect this path BEFORE calling in":
# done centrally here, for THIS process only -- every path the fence would refuse (under this worktree's
# data/ OR the canonical live C:\Nascence\data) is mapped into SCRATCH/lab_j1198_world/<same relative path>,
# and every caller uses guard_path()'s RETURN value as the path it writes (checked: 0 direct-name imports,
# `path = profile.guard_path(_F)` at every call site). Nothing under data/ is written; a path already
# outside every data root passes through exactly as the original does. core/profile.py is not edited.
from core import profile as _profile                          # noqa: E402

_WORLD_SANDBOX = SCRATCH / "lab_j1198_world"
WORLD_REDIRECTS: Counter = Counter()


def _guard_path_to_scratch(path):
    if _profile.LIVE:
        return path
    p = Path(path)
    rel = _profile._data_relative(p)
    if rel is None:
        return path
    dest = _WORLD_SANDBOX / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    WORLD_REDIRECTS[str(rel)] += 1
    return dest


_profile.guard_path = _guard_path_to_scratch


def assert_module_resolution() -> dict:
    """rule 6: every core module this run relies on must resolve INSIDE the worktree."""
    import nodes.inner_monologue_node as _imn                 # noqa: F401 -- also proves _DATA_DIR below
    out = {}
    for m in (core, _jp, _mc, _tel, _imn):
        f = Path(m.__file__).resolve()
        out[m.__name__] = str(f)
        assert str(f).lower().startswith(str(ROOT).lower()), f"{m.__name__} resolves OUTSIDE the worktree: {f}"
    out["nodes.inner_monologue_node._DATA_DIR"] = str(_imn._DATA_DIR)
    assert str(_imn._DATA_DIR.resolve()).lower().startswith(str(ROOT).lower()), "_DATA_DIR outside worktree"
    return out


# ---------------------------------------------------------------------------------------------------------
# the rule-4 wrappers (this process only)
# ---------------------------------------------------------------------------------------------------------
_orig_ask = _jp._ask
_orig_rule_detail = _jp.rule_detail
_orig_call_node = _mc.call_node
HOT_TRANSPORT = {"err": None}


async def _ask_lab(session, url, system, user, key, timeout=_jp._TIMEOUT, num_predict=_jp._NUM_PREDICT):
    hub = _HUB_NAME.get(url, url)
    timeout = max(timeout, LAB_TIMEOUT)
    for attempt in range(len(BACKOFF) + 1):
        v, why, err, el = await _orig_ask(session, url, system, user, key, timeout=timeout, num_predict=num_predict)
        st = STATS[hub]
        st["calls"] += 1
        st["secs"].append(el)
        if err in INFRA_ERRS:
            st["infra_errors"] += 1
            _append_jsonl(INFRA_PATH, {"ts": time.time(), "event": "infra_error", "hub": hub, "err": err,
                                       "elapsed": el, "attempt": attempt, "unit": CUR["unit"], "phase": CUR["phase"]})
            if attempt < len(BACKOFF):
                st["retries"] += 1
                progress("retry", len(DONE), PLANNED["n"],
                         f"{hub} {err} after {el}s on unit {CUR['unit']}: retry {attempt+1}/3 in {BACKOFF[attempt]}s")
                await asyncio.sleep(BACKOFF[attempt])
                continue
            st["persistent_fail"] += 1
            CUR["persistent"].add(hub)
            return v, why, err, el
        if err == "parse":
            st["parse"] += 1
        else:
            st["ok"] += 1
        return v, why, err, el
    return None, None, "timeout", 0.0     # unreachable


async def _rule_detail_lab(system, user, key, context="", num_predict=_jp._NUM_PREDICT):
    t0 = time.time()
    res = await _orig_rule_detail(system, user, key, context, num_predict=num_predict)
    _append_jsonl(CALLS_PATH, {
        "ts": time.time(), "unit": CUR["unit"], "phase": CUR["phase"], "attempt": CUR["attempt"], "key": key,
        "call": {"objection_found": "first", "scope_only": "second"}.get(key, "other"),
        "system_sha": hashlib.sha1(system.encode("utf-8")).hexdigest()[:10], "user": user,
        "num_predict": num_predict, "wall_s": round(time.time() - t0, 2),
        "res": {k: res.get(k) for k in ("v1", "v2", "verdict", "how", "err1", "err2", "err3",
                                        "why1", "why2", "why3", "why")}})
    return res


async def _call_node_lab(base_url, system_prompt, user_prompt, **kw):
    """Hot-lane wrapper: timeout >= 300 s (a request queued behind another lab), and a transport-level failure
    (timeout / connection) is remembered so `_prove_lab` can tell it from a content failure (bad JSON)."""
    import aiohttp
    kw["timeout"] = max(kw.get("timeout", 120), LAB_TIMEOUT)
    t0 = time.monotonic()
    try:
        out = await _orig_call_node(base_url, system_prompt, user_prompt, **kw)
        st = STATS["HOT"]
        st["calls"] += 1
        st["ok"] += 1
        st["secs"].append(round(time.monotonic() - t0, 2))
        return out
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, OSError) as exc:
        st = STATS["HOT"]
        st["calls"] += 1
        st["secs"].append(round(time.monotonic() - t0, 2))
        HOT_TRANSPORT["err"] = f"{type(exc).__name__}: {str(exc)[:120]}"
        raise


def _make_prove_lab(orig_prove):
    async def _prove_lab(claim, ledger_lines):
        for attempt in range(len(BACKOFF) + 1):
            HOT_TRANSPORT["err"] = None
            res = await orig_prove(claim, ledger_lines)
            if HOT_TRANSPORT["err"] is None:
                return res                      # incl. content failures: a bad-JSON prove is a real outcome
            st = STATS["HOT"]
            st["infra_errors"] += 1
            _append_jsonl(INFRA_PATH, {"ts": time.time(), "event": "infra_error", "hub": "HOT",
                                       "err": HOT_TRANSPORT["err"], "attempt": attempt, "unit": CUR["unit"],
                                       "phase": CUR["phase"]})
            if attempt < len(BACKOFF):
                st["retries"] += 1
                progress("retry", len(DONE), PLANNED["n"],
                         f"HOT {HOT_TRANSPORT['err'][:60]} on unit {CUR['unit']}: retry {attempt+1}/3 in {BACKOFF[attempt]}s")
                await asyncio.sleep(BACKOFF[attempt])
                continue
            st["persistent_fail"] += 1
            CUR["persistent"].add("HOT")
            return res
        return res
    return _prove_lab


_jp._ask = _ask_lab
_jp.rule_detail = _rule_detail_lab
_mc.call_node = _call_node_lab


# ---------------------------------------------------------------------------------------------------------
# the unit-level wrapper: resume, exclusion, hub-wait
# ---------------------------------------------------------------------------------------------------------
def _load_done() -> None:
    if not UNITS_PATH.exists():
        return
    for line in UNITS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            DONE[(row["idx"], row["orig_close_ts"])] = row


def _excluded_stub(idx, window, close_row, claim_row, reason) -> dict:
    return {"idx": idx, "window": window, "orig_close_ts": close_row["ts"], "orig_reason": close_row.get("reason"),
            "orig_train_id": close_row.get("train_id"), "claim": claim_row.get("thought", "") or "",
            "about": claim_row.get("about", "") or "", "ledger_n": 0, "support": [], "prove_error": None,
            "objection": [], "disprove_status": "INFRA_EXCLUDED", "disprove_how": None, "disprove_error": reason,
            "disprove_scope_how": None, "disprove_scope_error": None,
            "root_id": None, "prove_id": None, "disprove_id": None}


def _make_replay_one_lab(orig_replay_one):
    async def _replay_one_lab(idx, window, close_row, claim_row, ledger_lines, trains_mod, cargo_types_mod):
        key = (idx, close_row["ts"])
        if key in DONE:
            return DONE[key]["record"]
        if STOP["flag"]:
            return _excluded_stub(idx, window, close_row, claim_row, f"not run: stopped ({STOP['flag']})")
        t_unit = time.time()
        unit_attempt = 0
        while True:
            unit_attempt += 1
            CUR.update(unit=idx, phase=UNIT_PHASE, attempt=unit_attempt, persistent=set())
            rec = await orig_replay_one(idx, window, close_row, claim_row, ledger_lines, trains_mod, cargo_types_mod)
            if not CUR["persistent"]:
                row = {"idx": idx, "window": window, "orig_close_ts": close_row["ts"], "attempt": unit_attempt,
                       "elapsed_s": round(time.time() - t_unit, 1), "done_at": time.time(), "record": rec}
                _append_jsonl(UNITS_PATH, row)
                DONE[key] = row
                progress("unit", len(DONE), PLANNED["n"],
                         f"idx={idx} {rec['disprove_status']} ({rec['disprove_how']}/{rec.get('disprove_scope_how')}) "
                         f"{row['elapsed_s']}s")
                return rec
            failed = sorted(CUR["persistent"])
            _append_jsonl(INFRA_PATH, {"ts": time.time(), "event": "unit_infra_failure", "unit": idx,
                                       "attempt": unit_attempt, "hubs": failed})
            progress("unit-infra", len(DONE), PLANNED["n"], f"idx={idx} attempt {unit_attempt}: persistent infra failure on {failed}")
            healed = await wait_for_hubs(failed)
            if healed and unit_attempt < 2 and not STOP["flag"]:
                continue                       # the hub answers again: give the unit one more full attempt
            reason = f"infra failure on {failed} after retries" + ("" if healed else "; hub still down after 30 min")
            EXCLUDED.append({"idx": idx, "window": window, "hubs": failed, "reason": reason})
            _append_jsonl(INFRA_PATH, {"ts": time.time(), "event": "unit_excluded", "unit": idx, "hubs": failed,
                                       "reason": reason})
            if not healed:
                STOP["flag"] = f"hub down: {failed}"
            return _excluded_stub(idx, window, close_row, claim_row, reason)
    return _replay_one_lab


def _make_control_check_lab(orig_control):
    async def _control_lab():
        for attempt in (1, 2):
            CUR.update(unit="control", phase="control", attempt=attempt, persistent=set())
            res = await orig_control()
            if not CUR["persistent"]:
                return res
            failed = sorted(CUR["persistent"])
            progress("control-infra", 0, PLANNED["n"], f"control check hit persistent infra failure on {failed}")
            if not await wait_for_hubs(failed):
                STOP["flag"] = f"hub down: {failed}"
                return res
        return res
    return _control_lab


def _make_report_lab(orig_write):
    def _write_lab_report_lab(summary, report_stem=None, intro_note="", scratch_label="train_split_merge_j0562"):
        recs = summary["records"]
        good = [r for r in recs if r.get("disprove_status") != "INFRA_EXCLUDED"]
        excluded = [r for r in recs if r.get("disprove_status") == "INFRA_EXCLUDED"]
        n = len(good) or 1
        cnt = Counter(r["disprove_status"] for r in good)
        summary = dict(summary)
        summary["records"] = good
        summary["n_replayed"] = len(good)
        summary["merge_status_distribution"] = dict(cnt)
        summary["merge_status_share"] = {k: round(v / n, 3) for k, v in cnt.items()}
        summary["nonempty_objection_share"] = round(sum(1 for r in good if r["objection"]) / n, 3) if good else None
        infra_txt = infra_paragraph(len(good), excluded)
        orig_write(summary, report_stem=report_stem, intro_note=(intro_note + "\n\n" + infra_txt).strip(),
                   scratch_label=scratch_label)
    return _write_lab_report_lab


def infra_paragraph(n_good: int, excluded: list) -> str:
    per_hub = []
    for hub in ("HOT", "JUDGE_1", "JUDGE_2", "TIEBREAK"):
        s = STATS.get(hub)
        if not s or not s["calls"]:
            continue
        secs = sorted(s["secs"])
        med = secs[len(secs) // 2] if secs else None
        per_hub.append(f"{hub}: {s['calls']} requests, {s['infra_errors']} infrastructure errors "
                       f"({100.0 * s['infra_errors'] / s['calls']:.1f}%), {s['retries']} retries, "
                       f"{s['persistent_fail']} failed after all retries, {s['parse']} 'parse' answers "
                       f"(the judge answered but broke the JSON contract: NOT infrastructure), median {med}s")
    ex = (f"{len(excluded)} unit(s) EXCLUDED from every rate: {[r['idx'] for r in excluded]}"
          if excluded else "0 units excluded")
    return ("**J-1198 infrastructure accounting (lab rules 4/5/7, this process only):** every request ran with "
            f"timeout >= {LAB_TIMEOUT}s; a `timeout`/`http`/`exception` error was retried 3 times with backoff "
            f"{list(BACKOFF)}s and is never a verdict. Units in the tallies below: {n_good}; {ex}. Per hub: "
            + "; ".join(per_hub) + ".")


# ---------------------------------------------------------------------------------------------------------
# heartbeat: progress every ~10 minutes, Du-down gate every 30
# ---------------------------------------------------------------------------------------------------------
async def heartbeat():
    beats = 0
    while True:
        await asyncio.sleep(600)
        beats += 1
        progress("heartbeat", len(DONE), PLANNED["n"],
                 f"elapsed={int((time.time()-T_START)/60)}min excluded={len(EXCLUDED)} live_write_attempts={len(LIVE_WRITE_ATTEMPTS)}")
        if beats % 3 == 0:
            down = await du_is_down()
            if not down:
                await asyncio.sleep(60)
                down = await du_is_down()
            progress("du-check", len(DONE), PLANNED["n"], "DOWN" if down else "UP-or-UNKNOWN -> STOP all hub traffic")
            if not down:
                STOP["flag"] = "du up or unknown"


# ---------------------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------------------
def load_script_namespace() -> dict:
    src = SCRIPT.read_text(encoding="utf-8")
    marker = "\nif True:  # always run when this file is executed directly"
    assert src.count(marker) == 1, "main-block marker moved: re-read scripts/train_state_invitro.py"
    head = src.split(marker)[0]
    ns = {"__name__": "train_state_invitro_j1198", "__file__": str(SCRIPT)}
    exec(compile(head, str(SCRIPT), "exec"), ns)
    return ns


async def main_async(ns: dict, n: int, dry: bool) -> dict:
    job_tag, report_stem, intro_note = ns["_j1198_run_params"](n)
    PLANNED["n"] = 2 * n
    hb = asyncio.create_task(heartbeat())
    try:
        return await ns["_run_step2_lab"](n, job_tag=job_tag, report_stem=report_stem, intro_note=intro_note)
    finally:
        hb.cancel()


async def preflight() -> bool:
    if not await du_is_down():
        progress("du-check", 0, PLANNED["n"], "UP-or-UNKNOWN at start -> refusing to send hub traffic")
        return False
    names = ["JUDGE_1", "JUDGE_2", "TIEBREAK", "HOT"]
    results = await asyncio.gather(*[probe(nm) for nm in names])
    for nm, r in zip(names, results):
        progress("probe", 0, PLANNED["n"], f"{nm} {'OK' if r[0] else 'FAIL'} {r[1]}s {r[2]!r}")
    bad = [nm for nm, r in zip(names, results) if not r[0]]
    if bad:
        return await wait_for_hubs(bad)
    return True


# ---------------------------------------------------------------------------------------------------------
# --harvest: extra units, run AFTER the main replay, ONLY to find more second-call TIEBREAK-decided prompts for
# Part 3 (the brief asks to re-ask >= 24 of them; the main n=80 replay may not contain that many). Never in the
# replay's tallies. Same procedure as the main run: the candidate list is the SAME `_evenly_spaced(qualifying, 3n)`,
# and the harvest takes the joined candidates the main run did NOT use (per window, ranks n+1 ...), interleaving the
# two windows. Same wrappers (rule 4/5/7), own resumable files, own unit ids (1001...).
# ---------------------------------------------------------------------------------------------------------
def build_harvest_events(ns: dict, n: int, max_events: int) -> list:
    from collections import defaultdict as _dd
    _load = ns["_load_jsonl"]
    D = ns["_DATA_DIR"]
    tll, ml, tsl = _load(D / "train_length_log.jsonl"), _load(D / "monologue_log.jsonl"), _load(D / "train_state_log.jsonl")
    ml_by_tid = _dd(list)
    for r in ml:
        if r.get("train_id"):
            ml_by_tid[r["train_id"]].append(r)
    ml_sorted = sorted(ml, key=lambda r: r.get("ts", 0))
    ml_ts = [r.get("ts", 0) for r in ml_sorted]
    tsl_by_tid = _dd(list)
    for r in tsl:
        if r.get("train_id"):
            tsl_by_tid[r["train_id"]].append(r)
    per_window = []
    for label, (lo, hi), use_tid in (("A_pre_step1_2026-08-03_to_08-16", ns["_WINDOW_A"], False),
                                     ("B_post_fix_2026-08-25_onward", ns["_WINDOW_B"], True)):
        qualifying = sorted([r for r in tll if r.get("reason") == "thread-end" and lo <= r.get("ts", -1) < hi],
                            key=lambda r: r["ts"])
        candidates = ns["_evenly_spaced"](qualifying, min(len(qualifying), max(n * 3, n)))
        joined = []
        for row in candidates:
            claim_row = None
            if use_tid and row.get("train_id"):
                pool = [m for m in ml_by_tid.get(row["train_id"], []) if m.get("unresolved") is False]
                if pool:
                    claim_row = min(pool, key=lambda m: abs(m["ts"] - row["ts"]))
            if claim_row is None:
                claim_row, _gap = ns["_nearest_ml_close_row"](ml_sorted, ml_ts, row["ts"])
            if claim_row is None or not (claim_row.get("thought") or "").strip():
                continue
            joined.append((label, row, claim_row, ns["_ledger_for"](tsl_by_tid, claim_row.get("train_id"), k=3)))
        per_window.append(joined)
    # sanity: the first n joined of each window are exactly the main run's events (idx 1..n = A, n+1..2n = B)
    if UNITS_PATH.exists():
        main_rows = [json.loads(l) for l in UNITS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
        want = {(r["idx"], r["orig_close_ts"]) for r in main_rows}
        got = {(i + 1, ev[1]["ts"]) for i, ev in enumerate(per_window[0][:n])} | \
              {(n + i + 1, ev[1]["ts"]) for i, ev in enumerate(per_window[1][:n])}
        assert want <= got, "harvest selection does not reproduce the main run's events: refusing"
    rest_a, rest_b = per_window[0][n:], per_window[1][n:]
    merged = []
    for i in range(max(len(rest_a), len(rest_b))):
        if i < len(rest_a):
            merged.append(rest_a[i])
        if i < len(rest_b):
            merged.append(rest_b[i])
    return merged[:max_events]


def count_tb_cases(main_calls: Path, harvest_calls: Path) -> int:
    seen = set()
    for p in (main_calls, harvest_calls):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            if c.get("call") == "second" and c.get("phase") in ("unit", "harvest") and c["res"]["how"] == "tiebreak":
                seen.add((c["phase"], c["unit"]))
    return len(seen)


def harvest_main(n: int, max_units: int, target_tb: int) -> int:
    global UNITS_PATH, CALLS_PATH, UNIT_PHASE
    main_calls = CALLS_PATH
    ns = load_script_namespace()
    events = build_harvest_events(ns, n, max_units)         # reads the MAIN units file for its sanity check
    UNITS_PATH, CALLS_PATH, UNIT_PHASE = UNITS_HARVEST, CALLS_HARVEST, "harvest"
    PLANNED["n"] = len(events)
    _load_done()
    progress("harvest-start", len(DONE), len(events),
             f"target >= {target_tb} tiebreak-decided second calls in total; have {count_tb_cases(main_calls, CALLS_HARVEST)} so far")
    if count_tb_cases(main_calls, CALLS_HARVEST) >= target_tb:
        progress("harvest-done", len(DONE), len(events), "target already met: nothing to harvest")
        return 0
    if not asyncio.run(preflight()):
        progress("abort", len(DONE), len(events), "harvest preflight failed")
        return 3
    ns["_prove"] = _make_prove_lab(ns["_prove"])
    replay = _make_replay_one_lab(ns["_replay_one"])
    import core.trains as _trains
    from core import cargo_types as _ct
    from lab_isolation import neutralize_telemetry
    scratch_dir = ROOT / "scratch" / f"train_split_merge_J-1198_harvest_n{n}"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    _trains._DATA = scratch_dir
    _trains._LOG = scratch_dir / "trains_log_scratch.jsonl"
    # F-1683/F-1710/J-1199/J-1211: neutralize_telemetry() no-ops all three call_node() writers
    # (log_llm_call, log_thought_station, log_llm_latency) and redirects telemetry's own Path
    # globals into scratch_dir -- the same swap J-1199 made in the other 11 lab scripts, and the
    # one this file's own _run_step2_lab() (exec'd from train_state_invitro.py above) already
    # makes at its own call site. This --harvest-only path was the one F-1710 found still using
    # the old single-function no-op (module-level TEL_DIR already redirects _tel's Path globals
    # for every path in this file regardless, so this was belt-and-braces, not a live leak -- see
    # this job's own finding for the full read).
    neutralize_telemetry(scratch_dir, _tel)

    async def _run():
        hb = asyncio.create_task(heartbeat())
        try:
            for i, (label, close_row, claim_row, ledger) in enumerate(events, 1):
                if STOP["flag"] or count_tb_cases(main_calls, CALLS_HARVEST) >= target_tb:
                    break
                await replay(HARVEST_BASE + i, label, close_row, claim_row, ledger, _trains, _ct)
        finally:
            hb.cancel()

    t0 = time.time()
    asyncio.run(_run())
    have = count_tb_cases(main_calls, CALLS_HARVEST)
    after = live_snapshot()
    before = json.loads(SNAP_BEFORE.read_text(encoding="utf-8"))["snap"]
    (SCRATCH / "lab_j1198_harvest_summary.json").write_text(json.dumps({
        "units_done": len(DONE), "tiebreak_second_calls_total": have, "target": target_tb, "stopped": STOP["flag"],
        "excluded": EXCLUDED, "wall_minutes": round((time.time() - t0) / 60, 1),
        "live_files_unchanged": before == after, "write_attempts_under_live_data": len(LIVE_WRITE_ATTEMPTS),
        "hubs": {h: {k: (v if k != "secs" else {"n": len(v)}) for k, v in s.items()} for h, s in STATS.items()}},
        indent=1), encoding="utf-8")
    progress("harvest-done", len(DONE), len(events),
             f"tiebreak-decided second calls now {have} (target {target_tb}); wall={round((time.time()-t0)/60,1)}min "
             f"live_write_attempts={len(LIVE_WRITE_ATTEMPTS)} live_unchanged={before == after}")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    probe_only = "--probe-only" in sys.argv
    harvest = "--harvest" in sys.argv
    n = int(args[0]) if args else 40
    print(f"[j1198] root={ROOT} scratch={SCRATCH} n_per_window={n} dry={dry} harvest={harvest}", flush=True)
    res = assert_module_resolution()
    print("[j1198] module resolution (all must be inside the worktree):", json.dumps(res, indent=1), flush=True)

    if not SNAP_BEFORE.exists():
        SNAP_BEFORE.write_text(json.dumps({"ts": time.time(), "snap": live_snapshot()}, indent=1), encoding="utf-8")
    print("[j1198] live snapshot (before):", json.dumps(json.loads(SNAP_BEFORE.read_text(encoding="utf-8"))["snap"]), flush=True)

    if probe_only:
        ok = asyncio.run(preflight())
        return 0 if ok else 3

    if harvest:
        def _arg(name, default):
            for i, a in enumerate(sys.argv):
                if a == name and i + 1 < len(sys.argv):
                    return int(sys.argv[i + 1])
            return default
        return harvest_main(n, _arg("--max-units", 60), _arg("--target-tb", 28))

    ns = load_script_namespace()
    print("[j1198] script namespace loaded; _DATA_DIR =", ns["_DATA_DIR"], flush=True)

    if dry:
        planned: list = []

        async def _stub_replay(idx, window, close_row, claim_row, ledger_lines, trains_mod, cargo_mod):
            planned.append({"idx": idx, "window": window, "close_ts": close_row["ts"], "claim": claim_row.get("thought", ""),
                            "reason": close_row.get("reason"), "train_id": claim_row.get("train_id")})
            return {"idx": idx, "window": window, "orig_close_ts": close_row["ts"], "disprove_status": "DRY",
                    "disprove_how": None, "support": [], "objection": []}

        async def _stub_control():
            return []

        ns["_replay_one"] = _stub_replay
        ns["_run_control_check"] = _stub_control
        ns["_write_lab_report"] = lambda *a, **k: None
        asyncio.run(main_async(ns, n, True))
        out = SCRATCH / "lab_j1198_dry_plan.json"
        out.write_text(json.dumps(planned, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[j1198] DRY: {len(planned)} events planned -> {out}", flush=True)
        print("[j1198] write attempts under live data:", len(LIVE_WRITE_ATTEMPTS), LIVE_WRITE_ATTEMPTS[:3], flush=True)
        return 0

    _load_done()
    progress("start", len(DONE), 2 * n, f"resume: {len(DONE)} unit(s) already finished; n_per_window={n}")
    ok = asyncio.run(preflight())
    if not ok:
        progress("abort", len(DONE), 2 * n, "preflight failed (Du up/unknown or a hub never answered): partial = nothing new")
        return 3

    ns["_prove"] = _make_prove_lab(ns["_prove"])
    ns["_replay_one"] = _make_replay_one_lab(ns["_replay_one"])
    ns["_run_control_check"] = _make_control_check_lab(ns["_run_control_check"])
    ns["_write_lab_report"] = _make_report_lab(ns["_write_lab_report"])

    t0 = time.time()
    summary = asyncio.run(main_async(ns, n, False))
    wall_min = round((time.time() - t0) / 60, 1)

    # ---- after: live-file check, audit count, per-hub stats -------------------------------------------------
    after = live_snapshot()
    SNAP_AFTER.write_text(json.dumps({"ts": time.time(), "snap": after}, indent=1), encoding="utf-8")
    before = json.loads(SNAP_BEFORE.read_text(encoding="utf-8"))["snap"]
    unchanged = (before == after)
    out = {"job": JOB, "wall_minutes_this_launch": wall_min, "units_done": len(DONE), "units_excluded": EXCLUDED,
           "stopped": STOP["flag"], "live_files_unchanged": unchanged, "live_before": before, "live_after": after,
           "write_attempts_under_live_data": len(LIVE_WRITE_ATTEMPTS), "write_attempt_detail": LIVE_WRITE_ATTEMPTS[:20],
           "hubs": {h: {k: (v if k != "secs" else {"n": len(v), "median": sorted(v)[len(v) // 2] if v else None,
                                                   "max": max(v) if v else None}) for k, v in s.items()}
                    for h, s in STATS.items()},
           "module_resolution": res}
    SUMMARY_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[j1198] write attempts under live data:", len(LIVE_WRITE_ATTEMPTS), flush=True)
    print("[j1198] live files unchanged (md5 / size+mtime):", unchanged, flush=True)
    progress("finished", len(DONE), 2 * n,
             f"wall={wall_min}min excluded={len(EXCLUDED)} stopped={STOP['flag']} live_write_attempts={len(LIVE_WRITE_ATTEMPTS)} live_unchanged={unchanged}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
