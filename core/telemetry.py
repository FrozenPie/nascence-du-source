"""
Nascence — Telemetry for the HUD (2026-07-08, Travis): two live graphs.
  1. HARDWARE LOAD — a line per local GPU + the CPU, how hard each is worked over time.
  2. LLM PUSH      — a line per model, how often/hard we push each (calls/min over time).

Design: `log_llm_call()` is written by core/model_client on EVERY inference call (fire-and-forget, in Du's
process) → data/llm_calls.jsonl. `sample()` is called from the HUD on each refresh (rate-limited) — it reads
the machine's GPU/CPU right then (system-wide nvidia-smi + psutil, so it sees the load Du's inference drives)
and aggregates the call-log into calls/min per model → two time-series jsonl the HUD auto-renders as
multi-line cards. Fail-open throughout; nothing here touches Du's cognition.

Topology note: locally there is ONE GPU (the 1080 Ti hot lane) + the Threadripper CPU — both sampled here.
The Dreamer's 3070 is REMOTE (Ramses) and not visible to local nvidia-smi, but its workload shows in the LLM
graph (phi3:mini's rate). A Ramses-side agent could add its util later.
"""
from __future__ import annotations

import collections
import contextlib
import json
import os
import subprocess
import threading
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_CALLS = _DATA / "llm_calls.jsonl"        # per-call log (written by model_client, read by sample())
_HW    = _DATA / "hardware_load.jsonl"    # hardware time-series (HUD card)
_LLM   = _DATA / "llm_usage.jsonl"        # per-model calls/min time-series (HUD card)

_OWNER_STAMP = _DATA / "telemetry_owner.stamp"   # J-1932/F-2557: mtime = "Du's process sampled within _OWNER_FRESH_S"
_OWNER_FRESH_S  = 30.0                    # > _SAMPLE_MIN_GAP + nvidia-smi's 4 s timeout; the real worst observed gap is 23.4 s (F-3352), margin ~6.6 s (not ~20 s)

_SERIES_CAP     = 600                     # keep the last ~600 samples per series (rolling window)
_CALLS_CAP      = 6000                    # keep the last ~6000 call records
_SAMPLE_MIN_GAP = 6.0                     # FLOOR: at most one sample per 6 s (HUD polls faster than this); ~10 s observed (median 10.3, F-3352) since the ~5 s tick fires every 2nd time
_RATE_WINDOW    = 60.0                    # calls/min = calls in the last 60s
# always-emitted models, so their lines stay continuous (0 when idle); extras seen live are added on top.
# Full shuffle 2026-08-20: the serving roster is qwen3.5:9b (Self) / phi3:mini (Subconscious) /
# gemma4:12b (judge1) / mistral:7b-instruct (judge2) / yi:34b (dreamer, lazy). llama3.1:8b and
# qwen2.5:7b hold no seat; extras seen live are still added dynamically below.
_KNOWN_MODELS = ["qwen3.5:9b", "phi3:mini", "gemma4:12b", "mistral:7b-instruct"]

_last_sample = 0.0


# ── Lab isolation guard (D-0252, 2026-09-22) ────────────────────────────────────────────────────────
# F-1683 (2026-09-21): 11 lab scripts neutralised only log_llm_call from the CALLER side -- for years,
# none of them was ever revisited when this module grew log_thought_station (2026-09-15) and
# log_llm_latency (2026-08-21) as second and third writers, so each kept "isolating telemetry" while
# actually leaking two of three rows. scripts/lab_isolation.py's neutralize_telemetry() (J-1199, same
# day) fixed the CALLER side with one shared, tested helper instead of N hand-copies -- but a caller
# can only neutralise writer NAMES it already knows, so a future 4th writer would still need every
# caller (the shared helper included) to be told its name -- the exact omission that produced F-1683.
#
# This flag closes it from the SOURCE side instead: every write function below checks it FIRST, so a
# lab process that opts in gets ALL of them -- current and any future one added the same way -- no-op'd
# centrally, with no per-writer registration required anywhere.
#
# Deliberately the OPPOSITE polarity of core/profile.py's guard_path()/mark_live() (the sibling
# precedent this job's own briefing points at): guard_path() defaults to REFUSE and only the one real
# live Du boot opts IN to being allowed to write (mark_live()), because a silent world-store write from
# some unmarked process is the dangerous case there. Here the dangerous case is the mirror image: every
# one of Du's own real inference calls hits these functions, so the safe default has to stay "write,
# exactly as always" -- a flag that defaulted to refusing would break Du's own live telemetry the
# instant this shipped. Only a process that explicitly knows it is a lab opts IN to being blocked.
# Du's live process (scripts/run_nascence.py) never calls enter_lab_mode(), so its behaviour through
# these functions stays byte-identical to before this change.
_LAB_MODE = False


def enter_lab_mode() -> None:
    """Declare this process a lab/offline process: log_llm_call, log_thought_station and
    log_llm_latency (and any future writer added here that checks _LAB_MODE the same way) become
    no-ops from this call forward -- matching this module's own existing fail-open convention (a
    no-op, not an exception: nothing here has ever been allowed to raise into a real inference call,
    and a caller wanting a guaranteed write count should read scripts/lab_isolation.py's own
    WriteAudit.clean, not an exception from this module).

    Call once, as early as possible -- before any log_* call, ideally before any inference call at
    all. scripts/lab_isolation.py's neutralize_telemetry() calls this automatically (D-0252/J-1214:
    so its own 11 existing callers, and any future one, get this central guard for free on top of its
    own per-function no-ops). A lab script not using that helper may call this directly instead.

    Du's live process (scripts/run_nascence.py) never calls this. Idempotent (safe to call more than
    once -- a plain flag, not a counter; see exit_lab_mode()'s docstring for the one caveat that
    follows from that)."""
    global _LAB_MODE
    _LAB_MODE = True


def exit_lab_mode() -> None:
    """Undo enter_lab_mode(): the three writers above resume writing normally. Only needed by a
    caller using the SCOPED pattern (neutralize_telemetry()/restore_telemetry() around one block,
    e.g. scripts/lod_retrieval_lab.py's own save/restore-around-isolate() usage) that must go back to
    real writes afterward in the same process -- restore_telemetry() calls this automatically. A
    fire-and-forget lab that calls enter_lab_mode() once for its whole run has no need to call this.

    _LAB_MODE is a plain flag, not a reference count: two overlapping (nested, not sequential) scoped
    blocks in the same process would have the inner restore_telemetry() turn writes back on while the
    outer block is still active -- the same non-reentrant caveat neutralize_telemetry() itself already
    documents for calling IT twice (the second call's saved dict does not capture the true original
    state either). None of this project's lab scripts nest scoped blocks today."""
    global _LAB_MODE
    _LAB_MODE = False


_LAT = _DATA / "llm_latency.jsonl"        # per-call wall-clock (2026-08-21) — written by model_client
_JSONFAIL = _DATA / "llm_json_parse_fail.jsonl"   # D-0354/J-1840: call_node_json parse failures per attempt
_BREAKER = _DATA / "lane_breaker.jsonl"   # J-1832/F-2466: per-lane circuit-breaker transitions (open/half_open/
                                           # close/reopen), written by model_client.call_node_json. UNCAPPED
                                           # on purpose -- its whole job is making the stall hours visible.
_STATIONS = _DATA / "thought_station_log.jsonl"   # persistent per-call model-attribution log (J-0939,
                                           # 2026-09-15, F-1308) — written by model_client at the SAME
                                           # call site as log_llm_call below, but NEVER capped (mirrors
                                           # _LAT's own precedent: a separate ancillary file next to
                                           # llm_calls.jsonl so ITS cap/row-count stays untouched).
                                           # llm_calls.jsonl's _CALLS_CAP made it unable to answer "which
                                           # model wrote this thought" past ~0.89 observed days
                                           # (thermal_causality.md S9 Row 2 / D-0214's defeater); this
                                           # file exists to answer that over any window. If disk ever
                                           # becomes a real concern, that is a founder retention call
                                           # (scripts/retention.py, D-0156's precedent) — not a silent
                                           # auto-trim here; live data/ is explicitly out of that
                                           # script's scope today, same as every other live data/*.jsonl.


def log_llm_latency(model: str, node: str, caller: str, secs: float, ok: bool,
                    grammar: int | None = None, think: bool = False, pe: int | None = None,
                    pe_s: float | None = None, ec: int | None = None, ec_s: float | None = None,
                    fn: str = "", raw_http: bool = False) -> None:
    """One compact row per inference call with its DURATION (lane-slot wait + request + parse).
    Separate file from llm_calls.jsonl so job_status()/window_status() row counts are untouched.
    {ts, model, node(port), by(caller), s(seconds), ok[, g]}. `g` (D-0354 / J-1840) is present only on
    json_mode calls: 1 = the JSON grammar (format=json) was sent, 0 = withheld (first attempt on the
    no-grammar-first :11441 lane). `t` (J-2852) is present, as 1, only on a think=true call.
    PREFILL VISIBILITY (J-2675 / F-3426): `pe` = the hub's prompt_eval_count (prompt tokens it actually
    processed), `pe_s` = prompt_eval_duration in seconds (the prefill time; ollama reports it, the
    llama.cpp project hubs report only the counts so pe_s is absent there), `ec` = eval_count (generated
    tokens), `ec_s` = eval_duration in seconds. Each key is written ONLY when the reply carried it (missing =
    unknown, never 0); no existing key changes. Read by scripts/prefill_share_report.py and
    prefill_share_status(). Fail-open; never raises into a call."""
    if _LAB_MODE:
        return
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        row = {"ts": round(time.time(), 1), "model": model or "?",
               "node": (node or "")[-5:], "by": (caller or "")[:60],
               "s": round(float(secs), 2), "ok": 1 if ok else 0}
        if raw_http:                   # J-3761 / F-4370: a direct aiohttp post to a hub (not via model_client); `by`/`fn` name the
            row["h"] = 1              # call site or, for judge_panel, its real caller -- absent = routed through model_client
        if fn:                         # J-3760 / F-4371: the frame's qualified function name; `by` unchanged
            row["fn"] = str(fn)[:80]
        if grammar is not None:
            row["g"] = 1 if grammar else 0
        if think:
            row["t"] = 1          # J-2852: System-2 (think=true) call; absent = think off (licensed vs plain comparable)
        for _k, _v, _nd in (("pe", pe, None), ("pe_s", pe_s, 3), ("ec", ec, None), ("ec_s", ec_s, 3)):
            if _v is not None:
                row[_k] = int(_v) if _nd is None else round(float(_v), _nd)
        with open(_LAT, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


import contextvars as _contextvars
import sys as _sys

# J-3761 / F-4370: the raw-HTTP stations (judge_panel._ask, left_lane, lane2, deliberative_judge) post to a hub's
# /api/chat directly instead of through core.model_client, so they wrote only a coarse llm_calls label and NO
# llm_latency row. `raw_http_latency` is the additive latency row for them, shaped exactly like model_client's.
# RAW_HTTP_CALLER lets a shared station (judge_panel, 14 callers) name its REAL caller: the entry point sets it to
# (by, fn) for the duration of one call; a ContextVar is task-local and gather() copies it into child tasks.
RAW_HTTP_CALLER: "_contextvars.ContextVar[tuple | None]" = _contextvars.ContextVar("nascence_raw_http_caller", default=None)


def caller_outside(*modules: str, depth: int = 14) -> tuple:
    """(`module:line`, qualified function name) of the first frame whose module is not in `modules` and not asyncio.
    ("", "") when none is found. Fail-open. Walks f_back, so it is meaningful only along an awaited chain."""
    try:
        f = _sys._getframe(1)
        for _ in range(depth):
            if f is None:
                break
            mod = f.f_globals.get("__name__", "")
            if mod and mod != __name__ and mod not in modules and not mod.startswith("asyncio"):
                return (f"{mod}:{f.f_lineno}", getattr(f.f_code, "co_qualname", "") or f.f_code.co_name)
            f = f.f_back
    except Exception:
        pass
    return ("", "")


class raw_http_latency:
    """Async context manager: `async with _tel.raw_http_latency(url, model), session.post(...) as resp:` writes ONE
    llm_latency row (model, node=port, by, fn, seconds, ok) when the block ends; ok = no exception left the block.
    `by`/`fn` default to the calling frame (module:line of the station's own call site, and that function's
    qualname), or to RAW_HTTP_CALLER when an entry point has set it. Never raises, never swallows the block's own
    exception, writes nothing in lab mode (log_llm_latency's own rule)."""

    def __init__(self, url: str, model: str = "judge", by: str = "", fn: str = ""):
        self._url, self._model = url, model
        self._by, self._fn = by, fn
        try:
            if not by:
                ctx = RAW_HTTP_CALLER.get()
                if ctx and ctx[0]:
                    self._by, self._fn = ctx[0], (fn or ctx[1])
                else:
                    f = _sys._getframe(1)
                    self._by = f"{f.f_globals.get('__name__', '')}:{f.f_lineno}"
                    self._fn = fn or getattr(f.f_code, "co_qualname", "") or f.f_code.co_name
        except Exception:
            pass
        self._t0 = time.monotonic()

    async def __aenter__(self):
        self._t0 = time.monotonic()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            log_llm_latency(self._model, self._url, self._by, time.monotonic() - self._t0, exc_type is None,
                            fn=self._fn, raw_http=True)
        except Exception:
            pass
        return False


def prefill_share_status(window_rows: int = 5000, rows: list | None = None) -> dict:
    """The READ path for the pe/pe_s/ec/ec_s fields log_llm_latency now carries (J-2675 / F-3426): per caller
    (`by`), over the rows that carry token counts, the median prompt tokens, median prefill seconds, median
    generation seconds, and the prefill share of call time (sum pe_s / sum s over rows that carry pe_s).
    `rows` may be passed (tests / the report script); otherwise the tail of data/llm_latency.jsonl is read.
    Rows without `pe` are counted in `n_total` only -- an old row or a hub that sent no count is 'unknown',
    never zero. Fail-open: returns {"rows": 0} when there is nothing."""
    if rows is None:
        try:
            rows = _read_jsonl_rows(_LAT)[-window_rows:]   # J-4427: NUL / bad lines skipped, not fatal
        except Exception:
            rows = []
    def _med(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else None
    out: dict = {}
    for r in rows:
        if not isinstance(r, dict) or not r.get("ok"):
            continue
        d = out.setdefault(r.get("by") or "?", {"n_total": 0, "pe": [], "pe_s": [], "ec_s": [], "s_pe": [], "s_all": []})
        d["n_total"] += 1
        if isinstance(r.get("pe"), (int, float)):
            d["pe"].append(r["pe"])
        if isinstance(r.get("pe_s"), (int, float)) and isinstance(r.get("s"), (int, float)):
            d["pe_s"].append(r["pe_s"]); d["s_pe"].append(r["s"])
        if isinstance(r.get("ec_s"), (int, float)):
            d["ec_s"].append(r["ec_s"])
        if isinstance(r.get("s"), (int, float)):
            d["s_all"].append(r["s"])
    res = {}
    for by, d in out.items():
        tot = sum(d["s_pe"])
        res[by] = {"n_total": d["n_total"], "n_with_pe": len(d["pe"]), "n_with_pe_s": len(d["pe_s"]),
                   "med_prompt_tokens": _med(d["pe"]), "med_prefill_s": _med(d["pe_s"]),
                   "med_gen_s": _med(d["ec_s"]), "med_call_s": _med(d["s_all"]),
                   "prefill_share": round(sum(d["pe_s"]) / tot, 3) if tot > 0 else None}
    return {"rows": len(rows), "by_caller": res}


def log_json_parse_fail(model: str, node: str, caller: str, attempt: int, grammar: int, fn: str = "") -> None:
    """One row per call_node_json CONTENT failure (the reply came back but extract_json could not parse
    it) -- D-0354 / J-1840's defeater instrument. {ts, model, node(port), by(caller), attempt(0-based),
    g(1 grammar sent / 0 withheld)}. First-attempt parse-failure rate per caller = rows here with
    attempt 0 and g 0 / that caller's g=0 rows in llm_latency.jsonl (same `by` label, same node).
    Separate file so llm_latency.jsonl's one-row-per-call semantics stay untouched. Fail-open."""
    if _LAB_MODE:
        return
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_JSONFAIL, "a", encoding="utf-8") as f:
            _row = {"ts": round(time.time(), 1), "model": model or "?",
                    "node": (node or "")[-5:], "by": (caller or "")[:60],
                    "attempt": int(attempt), "g": 1 if grammar else 0}
            if fn:                     # J-3760 / F-4371: additive function-name key; `by` unchanged
                _row["fn"] = str(fn)[:80]
            f.write(json.dumps(_row) + "\n")
    except Exception:
        pass


def log_lane_breaker(event: str, base_url: str, fails: int = 0, open_s: float | None = None,
                     skipped: int | None = None, cooloff: float | None = None) -> None:
    """One row per circuit-breaker TRANSITION on an inference lane (J-1832 / F-2466).
    {ts, node(port), url, event, fails[, open_s][, skipped][, cooloff]}.
    event: "open" (N consecutive transport timeouts), "half_open" (cool-off over, one probe call allowed),
    "close" (a call got through -- carries `open_s` = how long the lane was tripped and `skipped` = how
    many call_node_json attempts were routed around it meanwhile), "reopen" (the probe failed).
    Sum `open_s` over "close" rows = hours Du's background work was spared a stalled lane. UNCAPPED
    (see _BREAKER). Honours _LAB_MODE like every other writer here. Fail-open; never raises."""
    if _LAB_MODE:
        return
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        row = {"ts": round(time.time(), 1), "node": (base_url or "")[-5:], "url": base_url or "",
               "event": event, "fails": int(fails)}
        if open_s is not None:
            row["open_s"] = round(float(open_s), 1)
        if skipped is not None:
            row["skipped"] = int(skipped)
        if cooloff is not None:
            row["cooloff"] = float(cooloff)
        with open(_BREAKER, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def log_thought_station(model: str, node: str = "", caller: str = "", fn: str = "") -> None:
    """One line per inference call — the PERSISTENT, UNCAPPED counterpart to log_llm_call's capped
    llm_calls.jsonl (same resolved `model`, same call site, written right beside it in
    core/model_client.call_node). {ts, model, node(port), by(caller)}.

    Built for J-0939 (2026-09-15, F-1308): docs/plans/thermal_causality.md's S9 Row 2 needed a DIRECT
    (not inferred) read of which model authored a given idle thought over a multi-week window, and no
    existing record survived longer than llm_calls.jsonl's own observed ~0.89-day cap window to answer
    it. Correlate a row here against a data/monologue_log.jsonl row by nearest `ts` for the SAME `by`
    call-site label (the idle thought generator's own call site, currently
    `nodes.inner_monologue_node:<line>(InnerMonologueNode)` — verified live in llm_calls.jsonl itself)
    to attribute a station to one specific logged thought. Fail-open; never raises into a call.
    """
    if _LAB_MODE:
        return
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_STATIONS, "a", encoding="utf-8") as f:
            _row = {"ts": round(time.time(), 1), "model": model or "?",
                    "node": (node or "")[-5:], "by": (caller or "")[:60]}
            if fn:                     # J-3760 / F-4371: additive function-name key; `by` unchanged
                _row["fn"] = str(fn)[:80]
            f.write(json.dumps(_row) + "\n")
    except Exception:
        pass


# J-1926 / F-2550: log_llm_call (loop thread) appends to llm_calls.jsonl while J-1910's telemetry worker thread rewrites it through _cap (read all lines, write_text the tail); one lock for the append and for _cap's whole read-modify-write.
_JSONL_LOCK = threading.Lock()


def log_llm_call(model: str, node: str = "", *, prompt_chars: int | None = None,
                 num_ctx: int | None = None, capped: bool = False, caller: str = "",
                 system_chars: int | None = None, fn: str = "") -> None:
    """One line per inference call — model + node, plus (2026-08-20) the CONTEXT WINDOW fields.

    The window fields exist to answer a question we could not previously answer at all: **is a lane's
    `num_ctx` actually being used, or are we paying for empty room?** Measured that day on Lane 2,
    `prompt_eval_count` was IDENTICAL at num_ctx 512/2048/8192/32768 — the window is ROOM, not content —
    while 32768 cost phi3:mini 37.4s against 3.4s for the same output. So an oversized window is not
    free and not harmless, and the only way to size one honestly is to know what the prompts really are.

    `capped` is the other half: `_cap_prompt` silently truncates from the MIDDLE, which is exactly where
    the injected memory context sits. A lane running at 30% utilisation and a lane truncating 40% of its
    prompts need opposite fixes, and today they look identical from outside.

    All fields optional and keyword-only — every existing caller keeps working unchanged. Fail-open.
    """
    if _LAB_MODE:
        return
    try:
        rec = {"ts": round(time.time(), 1), "model": model or "?", "node": node}
        if prompt_chars is not None:
            rec["pc"] = int(prompt_chars)          # short keys: this row is written on EVERY inference
        if num_ctx is not None:
            rec["nc"] = int(num_ctx)
        if capped:
            rec["cap"] = 1
        if caller:
            rec["by"] = caller                     # "module:line" — identifies the prompt JOB
        if fn:
            rec["fn"] = str(fn)[:80]               # J-3760 / F-4371: qualified function name beside `by`
        if system_chars is not None:
            rec["sc"] = int(system_chars)          # the system prompt shares the same window
        with _JSONL_LOCK, open(_CALLS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _read_jsonl_rows(path: Path) -> list:
    """J-4427 / F-5128: every parseable row of a jsonl, in file order. The 2026-11-20 crash zero-filled the tail of
    llm_calls.jsonl (and hardware_load / llm_usage / pursuits_series), leaving one line of NUL bytes with the next
    boot's first row glued after it. The old `[json.loads(l) for l in ...]` raised on that one line, so _llm_rates / window_status /
    job_status lost EVERY row until the bad line aged out of the file. NULs are stripped first (that recovers the
    glued row); a line that still does not parse is skipped. Raises only if the file cannot be opened."""
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.replace("\x00", "").strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def _cap(path: Path, n: int) -> None:
    """Trim a jsonl to its last n lines, only when it has grown well past n (cheap amortised)."""
    try:
        # J-1926: whole read-modify-write under the lock for llm_calls.jsonl (the one file the loop thread also appends to), so
        # log_llm_call's append cannot land between the read and the rewrite; _HW/_LLM are only ever written by the sample body.
        with (_JSONL_LOCK if path == _CALLS else contextlib.nullcontext()):
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) > n * 1.3:
                path.write_text("\n".join(lines[-n:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def _gpu_load() -> dict:
    """Per local GPU: {name util %, name VRAM %} via nvidia-smi. Empty on any failure/no GPU."""
    out: dict = {}
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=4)
        for line in r.stdout.strip().splitlines():
            parts = [x.strip() for x in line.split(",")]
            if len(parts) < 4:
                continue
            name, util, used, total = parts[0], parts[1], parts[2], parts[3]
            short = name.replace("NVIDIA GeForce ", "").replace("NVIDIA ", "")   # "GTX 1080 Ti"
            out[f"{short} GPU%"] = float(util)
            out[f"{short} VRAM%"] = round(100.0 * float(used) / max(1.0, float(total)), 1)
    except Exception:
        pass
    return out


def _llm_rates() -> dict:
    """Calls-per-model in the last _RATE_WINDOW seconds (≈ calls/min). Read-only over the call log."""
    try:
        now = time.time()
        rows = _read_jsonl_rows(_CALLS)[-_CALLS_CAP:]   # J-4427: NUL / bad lines skipped, not fatal
        c = collections.Counter(r.get("model", "?") for r in rows
                                if isinstance(r, dict) and now - float(r.get("ts", 0)) <= _RATE_WINDOW)
        return dict(c)
    except Exception:
        return {}


_GATE_LOCK = threading.Lock()   # guards the _last_sample claim (the loop thread and the HUD thread both call in)
_BODY_LOCK = threading.Lock()   # one sample body at a time: its _cap passes are read-modify-write on the same files
_IS_OWNER = False   # J-1932: set by kick() (Du's substrate heartbeat). sample() (the HUD process) never sets it.
_worker: "threading.Thread | None" = None   # the one in-flight off-loop sample body, or None; touched only by kick()
TELEMETRY_OFFLOOP = True        # kill-switch: False makes kick() run the plain synchronous sample() on the caller's thread


def _claim(force: bool) -> float | None:
    """The rate gate. Returns the claimed sample time, or None when the 6 s floor gap has not elapsed."""
    global _last_sample
    now = time.time()
    with _GATE_LOCK:
        if not force and now - _last_sample < _SAMPLE_MIN_GAP:
            return None
        _last_sample = now
    return now


def _stamp_owner() -> None:
    """Owner process only: touch the stamp the guest (HUD) process reads. Fail-open; a lab process never stamps."""
    if _LAB_MODE:
        return
    try:
        _OWNER_STAMP.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass


def _owned_elsewhere() -> bool:
    """True when ANOTHER process is the live sampler/capper (its stamp is fresh). Cross-process, lock-free: the HUD
    process only ever READS these series while Du's kick() is alive, so no two processes append to hardware_load /
    llm_usage or rewrite llm_calls.jsonl through _cap at once (J-1932 / F-2557). A dead or hung owner stops stamping,
    so within _OWNER_FRESH_S the guest takes over again (HUD graphs keep growing when Du is down)."""
    if _IS_OWNER:
        return False
    try:
        return (time.time() - os.path.getmtime(_OWNER_STAMP)) < _OWNER_FRESH_S
    except Exception:
        return False


def _sample_body(now: float) -> None:
    """The work of one sample: hardware row + llm-usage row + the three caps. Fail-open."""
    if _IS_OWNER:
        _stamp_owner()
    # ── hardware ──
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)     # % since the last call (0.0 on the very first)
    except Exception:
        cpu = None
    hw = {"ts": round(now, 1), "CPU %": cpu, **_gpu_load()}
    try:
        with open(_HW, "a", encoding="utf-8") as f:
            f.write(json.dumps(hw) + "\n")
        _cap(_HW, _SERIES_CAP)
    except Exception:
        pass
    # ── llm push (calls/min per model — known models always emitted for continuous lines) ──
    rates = _llm_rates()
    row = {"ts": round(now, 1)}
    for m in _KNOWN_MODELS:
        row[m] = rates.get(m, 0)
    for m, n in rates.items():                       # any extra model seen live
        if m not in row:
            row[m] = n
    try:
        with open(_LLM, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        _cap(_LLM, _SERIES_CAP)
    except Exception:
        pass
    # _CALLS was NEVER capped (found 2026-08-20): it declared _CALLS_CAP = 6000 and had grown to 44,393
    # lines / 3.5 MB. The cost was not disk — `_llm_rates()` parses the WHOLE file on every HUD refresh
    # to answer a 60-second question, so the HUD got steadily slower forever. Capping it here, next to
    # the other two, is where the missing line always belonged.
    _cap(_CALLS, _CALLS_CAP)


def sample(force: bool = False) -> None:
    """Rate-limited: append one hardware row + one llm-usage row. Called from the HUD refresh (its own thread,
    so synchronous there is fine). Fail-open. The substrate heartbeat calls kick() instead."""
    if _owned_elsewhere():      # J-1932: Du's process is sampling; the HUD process reads only
        return
    now = _claim(force)
    if now is None:
        return
    with _BODY_LOCK:
        _sample_body(now)


def _run_worker(now: float) -> None:
    try:
        with _BODY_LOCK:
            _sample_body(now)
    except Exception:
        pass


def kick() -> None:
    """The substrate heartbeat's call (core/sensorium.tick, every ~5 s on the event-loop thread) -- J-1910 / F-2540.

    sample()'s body was 53 ms/tick mean on that chain (82 ms median when it fires, about every other tick):
    a synchronous nvidia-smi subprocess (~50 ms), `_llm_rates()` re-parsing the whole ~1 MB llm_calls.jsonl
    (~25-30 ms) and three `_cap()` whole-file passes (~6 ms each). None of that has to happen on the loop
    thread, and nothing reads its result inline (it only appends two HUD series rows), so this does the
    cheap part -- one clock comparison and the rate-gate claim -- on the caller's thread and runs the body
    on a dedicated daemon thread. The rows written, their fields, the cadence (at most one sample per 6 s floor; ~10 s observed because the driving tick is ~5 s, F-3352) and the caps are exactly
    sample()'s (same `_sample_body`). A body still in flight (nvidia-smi can take up to its 4 s timeout)
    means this tick does nothing and the gate simply stays open for the next one. Fail-open: never raises,
    never blocks. TELEMETRY_OFFLOOP=False = the plain synchronous sample()."""
    global _worker, _IS_OWNER
    try:
        _IS_OWNER = True    # J-1932: this process is the one sampler/capper while it runs
        if not TELEMETRY_OFFLOOP:
            return sample()
        if time.time() - _last_sample < _SAMPLE_MIN_GAP:
            return
        w = _worker
        if w is not None and w.is_alive():
            return
        now = _claim(False)
        if now is None:
            return
        t = threading.Thread(target=_run_worker, args=(now,), name="telemetry-sample", daemon=True)
        _worker = t
        t.start()
    except Exception:
        pass


_CHARS_PER_TOKEN = 3.0     # same assumption `model_client._cap_prompt` derives its cap from — if that
                           # constant ever moves, this must move with it or the two disagree silently.
_EMPTY_ROOM_P95 = 0.35     # p95 utilisation below this = the window is mostly never used
_TRUNCATING_RATE = 0.10    # >10% of prompts hitting the cap = we are cutting real context


def window_status(lane: str = "") -> dict:
    """**The read path for the window fields — this is the instrument, not `log_llm_call`.**

    Answers, per lane: is `num_ctx` right-sized? Three outcomes need three different fixes, and from
    outside the process they are currently indistinguishable:
      - **OVERSIZED** — p95 utilisation well under the window. We pay VRAM and wall-clock for room the
        prompts never reach (measured: 32768 cost phi3 37.4s vs 3.4s for identical output).
      - **TRUNCATING** — `_cap_prompt` is cutting prompts. It truncates from the MIDDLE, which is where
        injected memory/recall sits, so this is silent context loss, not a slow path.
      - **right-sized** — neither.

    Returns `{}` with a `why` when there is no data yet, never a fabricated verdict.
    """
    try:
        rows = _read_jsonl_rows(_CALLS)[-_CALLS_CAP:]   # J-4427: NUL / bad lines skipped, not fatal
    except Exception as e:
        return {"why": f"call log unreadable: {e!r}"}
    rows = [r for r in rows if isinstance(r, dict) and r.get("pc") is not None]
    if not rows:
        return {"why": "no rows carry window fields yet — Du has not run since this was instrumented"}

    out: dict = {}
    lanes = collections.defaultdict(list)
    for r in rows:
        port = next((p for p in str(r.get("node", "")).split(":") if p.isdigit()), r.get("node") or "?")
        lanes[port].append(r)
    for port, rs in sorted(lanes.items()):
        if lane and lane not in port:
            continue
        toks = sorted(r["pc"] / _CHARS_PER_TOKEN for r in rs)
        ncs = [r["nc"] for r in rs if r.get("nc")]
        nc = max(ncs) if ncs else None
        p95 = toks[min(len(toks) - 1, int(len(toks) * 0.95))]
        cap_rate = sum(1 for r in rs if r.get("cap")) / len(rs)
        util_p95 = round(p95 / nc, 3) if nc else None
        if cap_rate > _TRUNCATING_RATE:
            verdict = f"TRUNCATING — {cap_rate:.0%} of prompts cut from the middle"
        elif util_p95 is not None and util_p95 < _EMPTY_ROOM_P95:
            verdict = f"OVERSIZED — p95 uses {util_p95:.0%} of a {nc} window; the rest is empty room"
        else:
            verdict = "right-sized"
        by = collections.Counter(r.get("by") or "?" for r in rs)
        out[port] = {"calls": len(rs), "num_ctx": nc,
                     "tok_med": round(toks[len(toks) // 2]), "tok_p95": round(p95),
                     "util_p95": util_p95, "cap_rate": round(cap_rate, 3),
                     "top_callers": [c for c, _ in by.most_common(4)], "verdict": verdict}
    return out


def job_status(min_calls: int = 5) -> dict:
    """Per prompt JOB (`module:line`) rather than per lane. **This is the one to read.**

    A lane average is the wrong unit and would hide the thing we care about: `inner_monologue_node`
    holds 9 distinct jobs split across TWO lanes whose windows differ 3x, `subconscious_node` holds
    10 across `base_urls` and a separate `_T4_URLS`, and `dream_node` has 1. They do different work,
    at different sizes, against different windows. Averaged together they describe none of them —
    which is exactly why the three had to be treated separately.

    `min_calls` suppresses jobs seen too few times to say anything about; they are counted in
    `sparse` rather than silently dropped, because a job that fires once a day is information too.
    """
    try:
        rows = _read_jsonl_rows(_CALLS)[-_CALLS_CAP:]   # J-4427: NUL / bad lines skipped, not fatal
    except Exception as e:
        return {"why": f"call log unreadable: {e!r}"}
    rows = [r for r in rows if isinstance(r, dict) and r.get("pc") is not None and r.get("by")]
    if not rows:
        return {"why": "no rows carry job attribution yet — Du has not run since this was wired"}

    jobs = collections.defaultdict(list)
    for r in rows:
        jobs[r["by"]].append(r)
    out: dict = {}
    sparse = 0
    for job, rs in jobs.items():
        if len(rs) < min_calls:
            sparse += 1
            continue
        # total = user prompt + system prompt; both occupy the same window.
        tot = sorted((r["pc"] + (r.get("sc") or 0)) / _CHARS_PER_TOKEN for r in rs)
        ncs = [r["nc"] for r in rs if r.get("nc")]
        nc = max(ncs) if ncs else None
        p95 = tot[min(len(tot) - 1, int(len(tot) * 0.95))]
        cap_rate = sum(1 for r in rs if r.get("cap")) / len(rs)
        util = round(p95 / nc, 3) if nc else None
        if cap_rate > _TRUNCATING_RATE:
            verdict = f"TRUNCATING {cap_rate:.0%}"
        elif util is not None and util < _EMPTY_ROOM_P95:
            verdict = f"OVERSIZED — p95 uses {util:.0%} of {nc}"
        else:
            verdict = "right-sized"
        out[job] = {"calls": len(rs), "num_ctx": nc, "model": rs[-1].get("model"),
                    "tok_med": round(tot[len(tot) // 2]), "tok_p95": round(p95),
                    "util_p95": util, "cap_rate": round(cap_rate, 3), "verdict": verdict}
    ordered = dict(sorted(out.items(), key=lambda kv: -(kv[1]["tok_p95"] or 0)))
    if sparse:
        ordered["_sparse_jobs_below_min_calls"] = sparse
    return ordered


def status() -> dict:
    """For the HUD/pulse: current hardware snapshot + recent per-model call totals + window sizing."""
    return {"hardware": {"CPU %": (__import__("psutil").cpu_percent(interval=None)
                                   if _has_psutil() else None), **_gpu_load()},
            "llm_calls_last_min": _llm_rates(),
            "context_windows": window_status()}


def _has_psutil() -> bool:
    try:
        import psutil  # noqa: F401
        return True
    except Exception:
        return False
