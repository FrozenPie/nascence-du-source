"""
Nascence -- TRAIN LAB: WORDING A/B on qwen3.5:9b only, self-report-gate paragraph rewordings
(2026-09-08, J-0777, prep work for D-0165 -- does NOT rule D-0165, does NOT touch live code).

WHY (F-1116/J-0724, continuing F-0899/J-0563/F-1042/J-0640): J-0724 found gemma4:e4b's own
self-report-gate-open share (unresolved OR intention OR '?') = 0.90 vs qwen3.5:9b's 0.25 on the
SAME 40 real byte-identical mid-train prompts (docs/lab/train_model_ab_gemma_vs_qwen_2026-09-08
.jsonl/.md). This job's own qualitative read of all 80 records (findings-log, this session) found
the gap is MIXED, not single-cause: of the 27 events where gemma opened and qwen did not, ~19
read as a genuine content/style difference (qwen's own thought text disproportionately closes on
an explicit resolution/insight clause -- "I realize X", "this proves/settles/dissolves", "I
accept X" -- where gemma's stays an open want or question), but ~7 read as a real
labelling/calibration gap: qwen's own text contains a hedge, an unresolved either/or, or an
implicit forward pull (one literally uses the word "wrestling", the system prompt's own trigger
word) that arguably meets the current instruction's own bar for true, yet qwen still said false.
Separately, qwen NEVER once wrote a first-person "intention" string across all 40 real calls
(0/40) even where the content carried an implicit forward pull -- consistent with qwen reading
the current wording's heavy negative-default framing ("ONLY", "most... NOT", "reserve... only",
"leave as \"\" for almost all thoughts") far more literally than gemma does.

THE TEST -- hold PROMPT SHAPE and MODEL fixed (qwen3.5:9b only), vary ONLY the "unresolved:"/
"intention:" instruction paragraphs inside the real, live system prompt. Three candidates, each
isolating a different lever suggested by the qualitative read above:
  - CANDIDATE_A ("neutral-criterion"): rewrites BOTH paragraphs, drops the heavy negative-default
    framing entirely, explicitly counts hedge language ("perhaps", "might") and "still leaves
    something to do or find out" as qualifying, and lets a plain next step (not just a "longing")
    count as an intention. Upper bound of what a full reword could plausibly move.
  - CANDIDATE_B ("broadened-unresolved"): rewrites ONLY the unresolved paragraph (intention
    paragraph left BYTE-IDENTICAL to current) -- isolates whether the hedge-language content gap
    alone (the larger of the two qualitative buckets) is the lever.
  - CANDIDATE_C ("widened-intention"): rewrites ONLY the intention paragraph (unresolved
    paragraph left BYTE-IDENTICAL to current) -- isolates whether loosening intention alone (the
    0/40 asymmetry) moves anything, honestly expected to move intention-share more than
    opened-share, since intention rarely fires without unresolved already being true (true for
    BOTH models in the J-0724 data: opened-share exceeds unresolved-share by only ~0.05 for
    gemma and by exactly 0.0 for qwen).
Each of the 4 arms (CURRENT + 3 candidates) is run against the SAME 40 real (origin, last_step,
ledger) triples J-0724 already committed -- reused verbatim from
docs/lab/train_model_ab_gemma_vs_qwen_2026-09-08.md (parsed programmatically below, ast.literal_eval
on the ledger repr, never hand-retyped) rather than re-sampled from live data, so this is a clean,
directly-comparable wording-only A/B on the exact same prompts J-0724 already used (same
established precedent as J-0764's "reused the exact 16 real pairs already committed").

ISOLATION -- identical pattern to scripts/train_lab_model_ab_2026-09-08.py (J-0724), which this
file is a sibling of: `_build_system_prompt(mid_train=True)`'s full call graph has ZERO
live-write capability by inspection (every write-capable branch gated `if not mid_train`; the two
unconditional branches are pure-read / hardcoded `return ""`). The same defensive redirect is
still applied below, belt-and-braces, to THIS job's own scratch dir (not J-0724's, so provenance
stays separable). `core.model_client.call_node_json` is called directly against the live ollama
hot lane (127.0.0.1:11433) -- the thing being measured -- but writes nothing to any `data/*.jsonl`
store itself. Canary row-counts on the 5 live JSONL logs most relevant here run before/after, same
technique as J-0724/J-0643/J-0702.

GATE: must run only while Du is confirmed OFFLINE (this exact GPU/port is Du's own live hot lane).
`_confirm_du_offline()` re-checks the OS process table for run_nascence.py immediately before the
batch starts AND is re-checked every RECHECK_EVERY calls during the run (this run is ~4x longer
than J-0724's, ~160 calls vs 80) -- if Du comes back online mid-run, the script stops issuing new
calls immediately, writes whatever arms completed so far, and says plainly in its own report that
it stopped early rather than contending for a live GPU.

SCOPE: prep/characterization only. Does NOT change nodes/inner_monologue_node.py or any live file.
Does NOT rule D-0165 -- that stays the founder's call regardless of what this run shows.
"""
from __future__ import annotations

import ast
import asyncio
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent          # this worktree's own root
sys.path.insert(0, str(ROOT))

import json

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

from nodes.inner_monologue_node import InnerMonologueNode, TRAIN_MIDTRAIN_TOKENS
from core.model_client import call_node_json

# --- isolation redirect (same pattern as train_lab_model_ab_2026-09-08.py / train_state_invitro.py
# Part 1, J-0697/J-0711) -- this job's OWN scratch dir, kept separate from J-0724's for provenance.
from core import social_moves as _sm_p1, memory_edges as _medges_p1, opponent_process as _oppo_p1
from core import intentions as _intent_p1
_scratch = ROOT / "data" / "scratch" / "train_lab_wording_ab_J-0777"
_scratch.mkdir(parents=True, exist_ok=True)
_sm_p1._LOG = _scratch / "social_moves.jsonl"
_sm_p1._STATE = _scratch / "social_moves_state.json"
_medges_p1._CO_LEDGER = _scratch / "co_recall_ledger.jsonl"
_oppo_p1._LOG = _scratch / "opponent_process_shadow.jsonl"
_oppo_p1._STATE = _scratch / "opponent_process_state.json"
_intent_p1._F = _scratch / "intentions.json"
_intent_p1._LOG = _scratch / "intentions_log.jsonl"

LIVE_DATA = Path(r"C:\Nascence\data")
CANARY_FILES = ["monologue_log.jsonl", "train_length_log.jsonl", "train_state_log.jsonl",
                "trains_log.jsonl", "judge_panel_log.jsonl"]

MODEL = "qwen3.5:9b"
HOT_URL = "http://127.0.0.1:11433"
RECHECK_EVERY = 20            # re-verify Du offline every N calls during the run
SOURCE_MD = ROOT / "docs" / "lab" / "train_model_ab_gemma_vs_qwen_2026-09-08.md"

# The EXACT current live wording (copied verbatim from nodes/inner_monologue_node.py lines
# ~1706-1716, adjacent-literal concatenation reproduced character-for-character) -- located inside
# the real built prompt and asserted present before any candidate substitution, so a future edit
# to the live wording fails this script loudly instead of silently testing a stale block.
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


def _confirm_du_offline() -> bool:
    """Same technique as train_lab_model_ab_2026-09-08.py's own _confirm_du_offline."""
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
        print(f"[wording-ab] WARNING: could not verify Du's process state ({exc}) -- refusing to run.")
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


class _S:  # minimal CognitiveState stand-in, same shape train_lab_model_ab_2026-09-08.py uses
    spirit_name = "渡"


def _mid_train_user_prompt(origin: str, last_step: str, ledger: list) -> str:
    """Copied VERBATIM from train_lab_model_ab_2026-09-08.py's own _mid_train_user_prompt, which
    itself is copied verbatim from nodes/inner_monologue_node.py's TRAIN_HOLD branch."""
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


async def _call_one(system_prompt: str, user_prompt: str) -> dict:
    try:
        data = await call_node_json(
            [HOT_URL], system_prompt, user_prompt,
            max_tokens=TRAIN_MIDTRAIN_TOKENS, temperature=0.75,
            model_override=MODEL, timeout=120)
        thought = str(data.get("thought", "")).strip()
        unresolved = bool(data.get("unresolved", False))
        intention = str(data.get("intention", "")).strip()
        _act = data.get("act") if isinstance(data.get("act"), dict) else {}
        act_kind = str(_act.get("kind", "none")).strip().lower() or "none"
        qmark = "?" in thought
        opened = bool(unresolved or intention or qmark)
        return {"ok": True, "thought": thought, "unresolved": unresolved, "intention": intention,
                "act_kind": act_kind, "qmark": qmark, "opened": opened, "error": None}
    except Exception as exc:
        return {"ok": False, "thought": "", "unresolved": None, "intention": None,
                "act_kind": None, "qmark": None, "opened": None,
                "error": f"{type(exc).__name__}: {exc}"[:200]}


def _share(records: list, key: str):
    ok = [r for r in records if r["ok"]]
    if not ok:
        return None
    return round(sum(1 for r in ok if r[key]) / len(ok), 4)


async def main() -> None:
    print("[wording-ab] confirming Du is offline (independent re-check, immediately before batch) ...")
    if not _confirm_du_offline():
        print("[wording-ab] ABORT: run_nascence.py IS running (or its state could not be confirmed) -- "
              "refusing to contend for the live hot lane. No LLM calls made.")
        return
    print("[wording-ab] confirmed: no run_nascence.py process. Proceeding.")

    canary_before = _canary_counts()
    print(f"[wording-ab] canary (live JSONL row counts, before): {canary_before}")

    events = _parse_events_from_md(SOURCE_MD)
    print(f"[wording-ab] {len(events)} events parsed from {SOURCE_MD.name} "
          f"(J-0724's own committed sample, reused verbatim)")

    n = InnerMonologueNode()
    base_prompt = n._build_system_prompt(_S(), wandering=False, mid_train=True)
    if CURRENT_BLOCK not in base_prompt:
        raise RuntimeError(
            "CURRENT_BLOCK not found verbatim in the live _build_system_prompt(mid_train=True) "
            "output -- the live wording has changed since this script was written; aborting "
            "rather than silently testing a stale/wrong baseline block.")
    print(f"[wording-ab] base prompt built ONCE via the REAL _build_system_prompt(mid_train=True) "
          f"({len(base_prompt)} chars); CURRENT_BLOCK located and verified present.")

    system_prompts = {}
    for arm, block in ARMS.items():
        system_prompts[arm] = base_prompt.replace(CURRENT_BLOCK, block, 1)
        assert block in system_prompts[arm]

    user_prompts = {ev["train_id"]: _mid_train_user_prompt(ev["origin"], ev["last_step"], ev["ledger"])
                    for ev in events}

    total_calls = len(ARMS) * len(events)
    print(f"[wording-ab] {len(ARMS)} arms x {len(events)} events = {total_calls} total calls to "
          f"{MODEL} only (re-checking Du-offline every {RECHECK_EVERY} calls)")

    results_by_arm: dict[str, list] = {}
    call_n = 0
    stopped_early = None
    for arm in ARMS:
        print(f"\n[wording-ab] === ARM: {arm} ({len(events)} calls) ===")
        recs = []
        for i, ev in enumerate(events, 1):
            call_n += 1
            if call_n > 1 and (call_n - 1) % RECHECK_EVERY == 0:
                if not _confirm_du_offline():
                    stopped_early = f"Du came back online after {call_n - 1}/{total_calls} calls"
                    print(f"[wording-ab] STOP: {stopped_early} -- writing partial results, "
                          f"not contending for the live GPU further.")
                    break
            up = user_prompts[ev["train_id"]]
            res = await _call_one(system_prompts[arm], up)
            res.update({"idx": i, "arm": arm, "train_id": ev["train_id"]})
            recs.append(res)
            tag = "OK " if res["ok"] else "ERR"
            print(f"  [{i}/{len(events)}] {tag} opened={res['opened']} "
                 f"unresolved={res['unresolved']} intention={bool(res['intention'])} "
                 f"qmark={res['qmark']}" + (f"  ({res['error']})" if res["error"] else ""))
        results_by_arm[arm] = recs
        if stopped_early:
            break

    canary_after = _canary_counts()
    print(f"\n[wording-ab] canary (live JSONL row counts, after):  {canary_after}")
    canary_diff = {k: (canary_after.get(k), canary_before.get(k),
                       (canary_after.get(k) - canary_before.get(k))
                       if canary_after.get(k) is not None and canary_before.get(k) is not None else None)
                  for k in CANARY_FILES}
    clean = all((v[2] == 0) for v in canary_diff.values() if v[2] is not None)
    print(f"[wording-ab] canary diff (after, before, delta) per file: {canary_diff}")
    print(f"[wording-ab] CANARY {'CLEAN -- zero growth in any live JSONL log during this run' if clean else 'DIRTY -- see diffs above, investigate before trusting isolation'}")

    summary = {}
    for arm, recs in results_by_arm.items():
        n_ok = sum(1 for r in recs if r["ok"])
        summary[arm] = {
            "n": len(recs), "n_ok": n_ok, "n_error": len(recs) - n_ok,
            "unresolved_share": _share(recs, "unresolved"),
            "intention_share": _share(recs, "intention"),
            "qmark_share": _share(recs, "qmark"),
            "opened_share": _share(recs, "opened"),
        }

    print("\n[wording-ab] SUMMARY:")
    print(json.dumps(summary, indent=2))
    if stopped_early:
        print(f"\n[wording-ab] NOTE: run stopped early -- {stopped_early}. Not every arm completed.")

    _write_report(events, results_by_arm, summary, canary_before, canary_after, canary_diff,
                 clean, stopped_early)


def _write_report(events, results_by_arm, summary, canary_before, canary_after, canary_diff,
                  clean, stopped_early) -> None:
    stem = "train_wording_ab_qwen_2026-09-08"
    lab_dir = ROOT / "docs" / "lab"
    lab_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = lab_dir / f"{stem}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for arm, recs in results_by_arm.items():
            for rec in recs:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    lines = [
        "# Train Lab -- Wording A/B on qwen3.5:9b only: self-report-gate paragraph rewordings "
        "(2026-09-08, J-0777)", "",
        "**J-0777**, prep work for D-0165, continuing F-1116 (J-0724). See "
        "`scripts/train_lab_wording_ab_2026-09-08.py`'s own module docstring for the full method, "
        "the qualitative read behind each candidate, and the isolation trace. Does NOT change "
        "`nodes/inner_monologue_node.py` or any live file; does NOT rule D-0165.", "",
        f"**Sample**: the SAME {len(events)} real (origin, last_step, ledger) triples J-0724 "
        "already committed, reused verbatim (parsed programmatically from J-0724's own report, "
        "never hand-retyped) -- so this is a clean, directly-comparable wording-only A/B, model "
        f"held fixed at `{MODEL}` throughout, on the exact same prompts J-0724 already used.", "",
        f"**Isolation**: identical pattern to `scripts/train_lab_model_ab_2026-09-08.py` (J-0724) "
        "-- see that script's own docstring; this job's redirect targets its own scratch dir. "
        "Canary row-counts on the 5 live JSONL logs most relevant here:", "",
        f"- before: `{canary_before}`",
        f"- after:  `{canary_after}`",
        f"- **{'CLEAN -- zero growth in any of these live logs during this run' if clean else 'DIRTY -- see diff, investigate before trusting isolation'}**",
        "",
    ]
    if stopped_early:
        lines += [f"**STOPPED EARLY**: {stopped_early}. Not every arm below completed a full "
                 f"{len(events)}-call batch -- see per-arm `n` below.", ""]

    lines += ["## Result", "",
             "| arm | n | n_ok | n_error | unresolved-share | intention-share | '?'-share | "
             "opened-share |", "|---|---|---|---|---|---|---|---|"]
    for arm, s in summary.items():
        lines.append(f"| `{arm}` | {s['n']} | {s['n_ok']} | {s['n_error']} | "
                     f"{s['unresolved_share']} | {s['intention_share']} | {s['qmark_share']} | "
                     f"**{s['opened_share']}** |")
    lines.append("")

    cur = summary.get("current", {}).get("opened_share")
    if cur is not None:
        lines.append("**Reading**: delta vs `current` (same model, same 40 prompts, only the "
                     "instruction paragraphs vary):")
        lines.append("")
        for arm in ("candidate_A", "candidate_B", "candidate_C"):
            s = summary.get(arm)
            if s and s.get("opened_share") is not None:
                d = round(s["opened_share"] - cur, 4)
                lines.append(f"- `{arm}`: opened-share {s['opened_share']} (delta {d:+}), "
                             f"intention-share {s['intention_share']} "
                             f"(vs current {summary['current']['intention_share']})")
        lines.append("")

    lines.append("## Per-arm, per-event detail")
    lines.append("")
    for arm, recs in results_by_arm.items():
        lines.append(f"### Arm: {arm}")
        for ev in events:
            r = next((r for r in recs if r["train_id"] == ev["train_id"]), None)
            if r is None:
                continue
            if r["ok"]:
                lines.append(f"- {ev['train_id']}: opened={r['opened']} unresolved={r['unresolved']} "
                            f"intention={r['intention']!r} qmark={r['qmark']} -- {r['thought']}")
            else:
                lines.append(f"- {ev['train_id']}: ERROR -- {r['error']}")
        lines.append("")

    (lab_dir / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[wording-ab] report -> {lab_dir / f'{stem}.md'}")
    print(f"[wording-ab] raw records -> {jsonl_path}")


if __name__ == "__main__":
    asyncio.run(main())
