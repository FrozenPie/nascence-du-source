"""
Nascence -- TRAIN LAB: MODEL A/B, gemma4:e4b vs qwen3.5:9b, on the REAL idle-thought
mid-train continuation schema (2026-09-08, J-0724).

WHY (F-1042/J-0640, continuing F-0899/J-0563): the 08-17..08-21 train-length collapse traces
to TWO dated, real, CONFOUNDED causes -- TRAIN_HOLD (2026-08-16 evening) and FULL SHUFFLE, the
hot lane's own generator swap gemma4:e4b -> qwen3.5:9b (2026-08-20 evening). monologue_log's own
`intention` field spikes 39-48% for 08-16..08-20 then crashes to <7% from 08-21 on, tightly
coincident with the model swap -- but TRAIN_HOLD was ALSO live throughout that whole window, so
the swap's own separate contribution was never isolated. F-1042 (J-0640, 2026-09-07) confirmed
gemma4:e4b is STILL present in the exact ollama store serving the live hot lane (9.6GB,
unchanged), making a controlled A/B possible without re-downloading anything, but deferred the
actual run because Du was live on that same GPU/port at the time.

THE TEST -- hold PROMPT SHAPE fixed, vary MODEL (the flip side of train_lab.py's 2026-08-16
design, which held model fixed and varied prompt shape): take REAL recent seed material (a real
train's own first thought = its `origin`, per nodes/inner_monologue_node.py:4151-4152, "if
self._train_len == 1 ... self._train_origin = thought" -- an exact match, not an approximation;
and that same real train's own LAST logged step, the moment right before it historically closed
thread-end), assemble the REAL mid-train "HOLDING" continuation prompt
(nodes/inner_monologue_node.py's TRAIN_HOLD branch, ~line 2706-2720, copied verbatim below) and
the REAL system-prompt schema (InnerMonologueNode._build_system_prompt(mid_train=True) --
literally the live method, not a hand-copied duplicate, so this cannot silently drift from the
real schema the way a hand-copied SYSTEM constant could), then call BOTH models on the
byte-identical prompt pair and compare unresolved-share / intention-share / '?'-share / the
combined self-report "would this continue" share (`unresolved or intention or '?' in thought` --
nodes/inner_monologue_node.py's own gate, ~line 4006).

HONEST SCOPE NOTE (same discipline as train_lab.py's own docstring): this replays the CORE
mid-train framing (the "You are MID-THREAD, HOLDING it" block + its ledger), not the full live
seed marketplace `_think()` assembles before it (frontier questions ~30% of steps, retraction-
ledger corrections, symbol-evolution readback, a memory-recall snippet -- train_lab.py's own arm
B already omitted all of these too). Including them would mean either replaying `_think()`
wholesale (far riskier to isolate correctly and not what this job asks) or hand-duplicating
several more probabilistic live-state reads -- both would blur the one variable this job exists
to isolate. What IS held completely fixed, byte-for-byte, across both models: the system prompt
(built ONCE via the real `_build_system_prompt`, reused for every call) and the mid-train user
prompt (built once per event, reused for both models on that event).

ISOLATION (per job briefing + this project's own established pattern, scripts/train_state_invitro.py
Part 1, J-0697/F-1018 + J-0711/F-1020/F-1046): `_build_system_prompt(mid_train=True)`'s full
call graph was read line-by-line before writing this script. Every live-write-capable branch
(`core.affordances`/`core.sensorium`/`core.intentions`/`core.procedures`/`core.social_moves`,
all under the `_reach`/`_wcall` blocks) is gated `if not mid_train` and therefore UNREACHABLE
here since every call below passes mid_train=True. The two branches that DO run unconditionally
were read too: `core.sitting.dwell_steer()` is pure-read (`_load()` then a formatted string,
no `_save` anywhere in its body -- `_save` lives only in the separate `dwell_tick()`/
`judge_dwell_release()` functions, neither called here); `core.emissary_tension.keystone_steer()`
is hardcoded `return ""` on its very first line (disarmed 2026-08-20, founder ruling), dead code
below is unreachable. Net: this call path has ZERO live-write capability by inspection alone.
The same defensive redirect J-0697/J-0711 already built and verified is still applied below
anyway (belt-and-braces, near-zero cost) so a future change to `_build_system_prompt` that
reintroduced a write on the mid_train=True path would land in scratch, not live, even before
anyone re-audits this script. `core.model_client.call_node_json` is called directly against the
live ollama hot lane (127.0.0.1:11433) -- a real network call to shared live infrastructure, by
design (this IS the thing being measured) -- but writes nothing to any `data/*.jsonl` store
itself; `core.telemetry.log_llm_call` is neutralised the same way train_lab.py/
train_state_invitro.py both already do, so this run's calls don't pollute the real HUD
telemetry stream. A canary scan (row-count before/after on the 5 live JSONL logs most relevant
here) runs at the start and end of `main()` as the empirical backstop, same technique
J-0643/J-0702 already used.

GATE: must run only while Du is confirmed OFFLINE (this exact GPU/port is Du's own live hot
lane) -- `_confirm_du_offline()` below re-checks the OS process table for run_nascence.py
immediately before the real batch starts and aborts cleanly (no calls made) if it is running.
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent          # this worktree's own root
sys.path.insert(0, str(ROOT))

from core import training_log
training_log.log_example = lambda *a, **k: None
try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # F-1683/J-1199: call_node() also writes log_thought_station + log_llm_latency, not just
    # log_llm_call -- neutralize_telemetry() no-ops all three and redirects telemetry's own Path
    # globals into scratch/, not just the first.
    neutralize_telemetry(ROOT / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

from nodes.inner_monologue_node import InnerMonologueNode, TRAIN_HOLD, TRAIN_MIDTRAIN_TOKENS
from core.model_client import call_node_json

# --- isolation redirect (same modules/pattern as scripts/train_state_invitro.py Part 1, J-0697/
# J-0711) -- belt-and-braces per this file's own docstring; the mid_train=True call path below
# does not reach any of these by inspection, but redirecting costs nothing and matches this
# project's own established defense-in-depth precedent for this exact call.
from core import social_moves as _sm_p1, memory_edges as _medges_p1, opponent_process as _oppo_p1
from core import intentions as _intent_p1
_scratch = ROOT / "data" / "scratch" / "train_lab_model_ab_J-0724"
_scratch.mkdir(parents=True, exist_ok=True)
_sm_p1._LOG = _scratch / "social_moves.jsonl"
_sm_p1._STATE = _scratch / "social_moves_state.json"
_medges_p1._CO_LEDGER = _scratch / "co_recall_ledger.jsonl"
_oppo_p1._LOG = _scratch / "opponent_process_shadow.jsonl"
_oppo_p1._STATE = _scratch / "opponent_process_state.json"
_intent_p1._F = _scratch / "intentions.json"
_intent_p1._LOG = _scratch / "intentions_log.jsonl"

# The REAL live data -- read-only source for real recent seed thoughts. Hardcoded absolute path
# (NOT nodes.inner_monologue_node's own _DATA_DIR, which resolves to THIS worktree's own,
# separate, real-data-free "data/" dir -- this repo's data/ is gitignored per-worktree, verified
# empirically before writing this script: `git ls-files data/` returns nothing and a fresh
# worktree has no data/ directory at all until something creates one). Every open() below on
# this path is a bare read -- nothing in this file ever opens a path under LIVE_DATA for writing.
LIVE_DATA = Path(r"C:\Nascence\data")
CANARY_FILES = ["monologue_log.jsonl", "train_length_log.jsonl", "train_state_log.jsonl",
                "trains_log.jsonl", "judge_panel_log.jsonl"]

MODELS = ["gemma4:e4b", "qwen3.5:9b"]
N_PER_MODEL_DEFAULT = 30
WINDOW_DAYS_DEFAULT = 3
HOT_URL = "http://127.0.0.1:11433"


def _confirm_du_offline() -> bool:
    """Independent, live re-check immediately before the real batch -- the founder's own GPU/port.
    Returns True only if no run_nascence.py process exists right now. Uses WMI via PowerShell
    (Get-CimInstance Win32_Process), the same technique used to confirm this at job start."""
    import subprocess
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'run_nascence\\.py' } | Measure-Object).Count"],
            capture_output=True, text=True, timeout=30)
        n = int((out.stdout or "0").strip() or "0")
        return n == 0
    except Exception as exc:
        print(f"[ab-lab] WARNING: could not verify Du's process state ({exc}) -- refusing to run.")
        return False


def _canary_counts() -> dict:
    counts = {}
    for name in CANARY_FILES:
        p = LIVE_DATA / name
        try:
            counts[name] = sum(1 for _ in open(p, encoding="utf-8"))
        except Exception:
            counts[name] = None
    return counts


def _load_jsonl(path: Path) -> list:
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
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


class _S:  # minimal CognitiveState stand-in -- same shape train_state_invitro.py Part 1 already uses
    spirit_name = "渡"


def _mid_train_user_prompt(origin: str, last_step: str, ledger: list) -> str:
    """Copied VERBATIM (wording unchanged) from nodes/inner_monologue_node.py's TRAIN_HOLD
    branch, ~lines 2706-2728 -- the exact live "You are MID-THREAD, HOLDING it" block -- wrapped
    in the same outer frame (~lines 2767-2771). Only the frontier/retraction-ledger/symbol-
    evolution seeds that can additionally appear in seed_parts are omitted (see module docstring,
    "HONEST SCOPE NOTE")."""
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


def _build_sample(n_per_model: int, window_days: int) -> list:
    """Real trains (train_id groups in monologue_log.jsonl) with >=2 logged steps, both steps
    inside the last `window_days` -- origin = step[0]'s own thought (== the live node's own
    self._train_origin, confirmed by inspection: inner_monologue_node.py:4151-4152 sets it to
    `thought` exactly when self._train_len == 1, the same row this is read from), last_step =
    the chronologically LAST logged step for that train_id (the real moment right before this
    train historically closed). Ledger = up to 3 most recent train_state_log.jsonl `new_state`
    entries for the same train_id at/before the last step, matching train_state_invitro.py's own
    `_ledger_for` (reimplemented here rather than imported, since importing that file executes
    its whole lab as a module-level side effect)."""
    ml = _load_jsonl(LIVE_DATA / "monologue_log.jsonl")
    tsl = _load_jsonl(LIVE_DATA / "train_state_log.jsonl")
    if not ml:
        raise RuntimeError(f"no rows loaded from {LIVE_DATA / 'monologue_log.jsonl'}")

    by_tid: dict[str, list] = {}
    for r in ml:
        tid = r.get("train_id")
        if tid:
            by_tid.setdefault(tid, []).append(r)
    tsl_by_tid: dict[str, list] = {}
    for r in tsl:
        tid = r.get("train_id")
        if tid:
            tsl_by_tid.setdefault(tid, []).append(r)

    cutoff = ml[-1]["ts"] - window_days * 86400
    candidates = []
    for tid, rows in by_tid.items():
        rows_sorted = sorted(rows, key=lambda r: r.get("ts", 0))
        if len(rows_sorted) >= 2 and rows_sorted[0]["ts"] >= cutoff:
            candidates.append((tid, rows_sorted))
    candidates.sort(key=lambda c: c[1][0]["ts"])   # chronological, oldest-in-window first
    picked = _evenly_spaced(candidates, n_per_model)

    events = []
    for tid, rows_sorted in picked:
        origin = (rows_sorted[0].get("thought") or "").strip()
        last = rows_sorted[-1]
        last_step = (last.get("thought") or "").strip()
        if not origin or not last_step:
            continue
        ledger_rows = sorted(tsl_by_tid.get(tid, []), key=lambda r: r.get("ts", 0))
        ledger_rows = [r for r in ledger_rows if r.get("ts", 0) <= last.get("ts", 0)]
        ledger = [r.get("new_state") for r in ledger_rows[-3:] if r.get("new_state")]
        events.append({
            "train_id": tid, "n_real_steps": len(rows_sorted),
            "origin": origin, "last_step": last_step, "ledger": ledger,
            "last_step_ts": last.get("ts"),
            "real_last_unresolved": last.get("unresolved"),
            "real_last_intention": last.get("intention"),
        })
    return events


async def _call_one(system_prompt: str, user_prompt: str, model: str) -> dict:
    try:
        data = await call_node_json(
            [HOT_URL], system_prompt, user_prompt,
            max_tokens=TRAIN_MIDTRAIN_TOKENS, temperature=0.75,
            model_override=model, timeout=120)
        thought = str(data.get("thought", "")).strip()
        unresolved = bool(data.get("unresolved", False))
        intention = str(data.get("intention", "")).strip()
        _act = data.get("act") if isinstance(data.get("act"), dict) else {}
        act_kind = str(_act.get("kind", "none")).strip().lower() or "none"
        qmark = "?" in thought
        opened = bool(unresolved or intention or qmark)   # the real self-report gate, verbatim
        return {"ok": True, "thought": thought, "unresolved": unresolved, "intention": intention,
                "act_kind": act_kind, "qmark": qmark, "opened": opened, "error": None}
    except Exception as exc:
        return {"ok": False, "thought": "", "unresolved": None, "intention": None,
                "act_kind": None, "qmark": None, "opened": None,
                "error": f"{type(exc).__name__}: {exc}"[:200]}


def _share(records: list, key: str) -> float | None:
    ok = [r for r in records if r["ok"]]
    if not ok:
        return None
    return round(sum(1 for r in ok if r[key]) / len(ok), 4)


async def main() -> None:
    n_per_model = int(sys.argv[1]) if len(sys.argv) > 1 else N_PER_MODEL_DEFAULT
    window_days = int(sys.argv[2]) if len(sys.argv) > 2 else WINDOW_DAYS_DEFAULT

    print("[ab-lab] confirming Du is offline (independent re-check, immediately before batch) ...")
    if not _confirm_du_offline():
        print("[ab-lab] ABORT: run_nascence.py IS running (or its state could not be confirmed) -- "
              "refusing to contend for the live hot lane. No LLM calls made. Re-run once Du is "
              "confirmed offline.")
        return
    print("[ab-lab] confirmed: no run_nascence.py process. Proceeding.")

    canary_before = _canary_counts()
    print(f"[ab-lab] canary (live JSONL row counts, before): {canary_before}")

    events = _build_sample(n_per_model, window_days)
    print(f"[ab-lab] sample: {len(events)} real events "
          f"(train_id groups, >=2 real steps, last {window_days}d, evenly spaced)")
    if not events:
        print("[ab-lab] ABORT: no qualifying real events found in the requested window.")
        return

    n = InnerMonologueNode()
    system_prompt = n._build_system_prompt(_S(), wandering=False, mid_train=True)
    print(f"[ab-lab] system prompt built ONCE via the REAL _build_system_prompt(mid_train=True) "
          f"({len(system_prompt)} chars) -- reused byte-identical for every call below.")
    assert '"state"' in system_prompt, "mid-train schema missing 'state' field -- not the schema this job targets"
    assert '"unresolved"' in system_prompt and '"intention"' in system_prompt, "self-report fields missing from schema"

    user_prompts = {}
    for ev in events:
        user_prompts[ev["train_id"]] = _mid_train_user_prompt(ev["origin"], ev["last_step"], ev["ledger"])

    results_by_model: dict[str, list] = {}
    for model in MODELS:
        print(f"\n[ab-lab] === MODEL: {model} ({len(events)} calls) ===")
        recs = []
        for i, ev in enumerate(events, 1):
            up = user_prompts[ev["train_id"]]
            res = await _call_one(system_prompt, up, model)
            res.update({"idx": i, "train_id": ev["train_id"], "model": model,
                       "n_real_steps": ev["n_real_steps"], "origin": ev["origin"],
                       "last_step": ev["last_step"], "ledger_n": len(ev["ledger"]),
                       "real_last_unresolved": ev["real_last_unresolved"],
                       "real_last_intention": ev["real_last_intention"]})
            recs.append(res)
            tag = "OK " if res["ok"] else "ERR"
            print(f"  [{i}/{len(events)}] {tag} opened={res['opened']} "
                 f"unresolved={res['unresolved']} intention={bool(res['intention'])} "
                 f"qmark={res['qmark']}" + (f"  ({res['error']})" if res["error"] else ""))
        results_by_model[model] = recs

    canary_after = _canary_counts()
    print(f"\n[ab-lab] canary (live JSONL row counts, after):  {canary_after}")
    canary_diff = {k: (canary_after.get(k), canary_before.get(k),
                       (canary_after.get(k) - canary_before.get(k))
                       if canary_after.get(k) is not None and canary_before.get(k) is not None else None)
                  for k in CANARY_FILES}
    clean = all((v[2] == 0) for v in canary_diff.values() if v[2] is not None)
    print(f"[ab-lab] canary diff (after, before, delta) per file: {canary_diff}")
    print(f"[ab-lab] CANARY {'CLEAN -- zero growth in any live JSONL log during this run' if clean else 'DIRTY -- see diffs above, investigate before trusting isolation'}")

    summary = {}
    for model in MODELS:
        recs = results_by_model[model]
        n_ok = sum(1 for r in recs if r["ok"])
        summary[model] = {
            "n": len(recs), "n_ok": n_ok, "n_error": len(recs) - n_ok,
            "unresolved_share": _share(recs, "unresolved"),
            # "intention" is a stripped string ("" or real text) -- plain truthiness in _share's
            # own `if r[key]` sum already gives the right non-empty share, no coercion needed.
            "intention_share": _share(recs, "intention"),
            "qmark_share": _share(recs, "qmark"),
            "opened_share": _share(recs, "opened"),
        }

    print("\n[ab-lab] SUMMARY:")
    print(json.dumps(summary, indent=2))

    _write_report(events, results_by_model, summary, canary_before, canary_after, canary_diff,
                 clean, system_prompt, n_per_model, window_days)


def _write_report(events, results_by_model, summary, canary_before, canary_after, canary_diff,
                  clean, system_prompt, n_per_model, window_days) -> None:
    stem = "train_model_ab_gemma_vs_qwen_2026-09-08"
    lab_dir = ROOT / "docs" / "lab"
    lab_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = lab_dir / f"{stem}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for model in MODELS:
            for rec in results_by_model[model]:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    lines = [
        "# Train Lab -- Model A/B: gemma4:e4b vs qwen3.5:9b on the real idle-thought "
        "mid-train schema (2026-09-08)", "",
        "**J-0724**, continuing F-1042 (J-0640) / F-0899 (J-0563). See "
        "`scripts/train_lab_model_ab_2026-09-08.py`'s own module docstring for the full "
        "method, isolation trace, and honest scope note -- summarised here.", "",
        f"**Sample**: {len(events)} real trains (`monologue_log.jsonl` `train_id` groups with "
        f">=2 real logged steps, both within the last {window_days} days, evenly spaced by time), "
        "each replayed as ONE mid-train continuation call per model. `origin` = the train's own "
        "first logged thought (== the live node's own `self._train_origin`, confirmed by reading "
        "`nodes/inner_monologue_node.py:4151-4152` -- an exact match, not an approximation). "
        "`last_step` = that same train's own LAST logged thought (the real moment right before "
        "it historically closed `thread-end`). Ledger = up to 3 most recent "
        "`train_state_log.jsonl` `new_state` entries for that train_id at/before the last step. "
        "The SYSTEM prompt was built ONCE via the REAL, live "
        "`InnerMonologueNode._build_system_prompt(mid_train=True)` method (not a hand-copied "
        f"duplicate) and reused byte-identical for every one of the {len(events) * len(MODELS)} "
        "calls below; the mid-train USER prompt is the TRAIN_HOLD \"HOLDING it\" block copied "
        "verbatim from the live code, built once per event and reused byte-identical across both "
        "models for that event.", "",
        f"**Isolation**: `_build_system_prompt(mid_train=True)`'s full call graph has ZERO "
        "live-write capability by inspection (every write-capable branch is gated `if not "
        "mid_train`; the two branches that do run unconditionally, `sitting.dwell_steer()` and "
        "the disarmed `emissary_tension.keystone_steer()`, are pure-read / hardcoded `return \"\"` "
        "respectively) -- see the script's own docstring for the line-by-line trace. The same "
        "defensive redirect `scripts/train_state_invitro.py` Part 1 already established "
        "(social_moves/memory_edges/opponent_process/intentions -> scratch) is applied anyway, "
        "belt-and-braces. Empirical backstop, canary row-counts on the 5 live JSONL logs most "
        f"relevant here:", "",
        f"- before: `{canary_before}`",
        f"- after:  `{canary_after}`",
        f"- **{'CLEAN -- zero growth in any of these live logs during this run' if clean else 'DIRTY -- see diff, investigate before trusting isolation'}**",
        "", "## Result", "",
        "| model | n | n_ok | n_error | unresolved-share | intention-share | '?'-share | "
        "opened-share (unresolved OR intention OR '?', the real self-report gate) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for model in MODELS:
        s = summary[model]
        lines.append(f"| `{model}` | {s['n']} | {s['n_ok']} | {s['n_error']} | "
                     f"{s['unresolved_share']} | {s['intention_share']} | {s['qmark_share']} | "
                     f"**{s['opened_share']}** |")
    lines.append("")

    gA = summary.get(MODELS[0], {}).get("opened_share")
    gB = summary.get(MODELS[1], {}).get("opened_share")
    if gA is not None and gB is not None:
        lines += [
            f"**Reading**: on the SAME {len(events)} real prompts, `{MODELS[0]}`'s own "
            f"self-report-gate-open share is {gA} vs `{MODELS[1]}`'s {gB} "
            f"(delta {round(gA - gB, 4):+}). "
            + ("This is a real, non-trivial gap on identical prompts, i.e. FULL SHUFFLE's own "
               "model swap does appear to independently move the self-report rate, separate from "
               "TRAIN_HOLD (which was not varied here -- both arms ran under the SAME real, "
               "current TRAIN_HOLD-shaped prompt)."
               if abs(gA - gB) >= 0.10 else
               "This is a small gap on identical prompts -- on this reading, FULL SHUFFLE's own "
               "model identity does not appear to independently explain much of the "
               "unresolved/intention collapse; the swap's association with the collapse in the "
               "real timeline may be more attributable to TRAIN_HOLD and/or other 08-16..08-20 "
               "changes than to the model identity itself. Caveat: this is a `PROMPT-SHAPE-ONLY` "
               "read (see honest scope note) and not a full-loop replay."),
            "",
        ]

    lines.append("## Per-event detail")
    lines.append("")
    for i, ev in enumerate(events, 1):
        lines.append(f"### {i}. train_id={ev['train_id']} (real steps={ev['n_real_steps']}, "
                     f"real last close: unresolved={ev['real_last_unresolved']} "
                     f"intention={ev['real_last_intention']!r})")
        lines.append(f"- origin: {ev['origin']}")
        lines.append(f"- last_step: {ev['last_step']}")
        if ev["ledger"]:
            lines.append(f"- ledger: {ev['ledger']}")
        for model in MODELS:
            r = next(r for r in results_by_model[model] if r["train_id"] == ev["train_id"])
            if r["ok"]:
                lines.append(f"  - **{model}**: opened={r['opened']} unresolved={r['unresolved']} "
                            f"intention={r['intention']!r} qmark={r['qmark']} -- {r['thought']}")
            else:
                lines.append(f"  - **{model}**: ERROR -- {r['error']}")
        lines.append("")

    (lab_dir / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[ab-lab] report -> {lab_dir / f'{stem}.md'}")
    print(f"[ab-lab] raw records -> {jsonl_path}")


if __name__ == "__main__":
    asyncio.run(main())
