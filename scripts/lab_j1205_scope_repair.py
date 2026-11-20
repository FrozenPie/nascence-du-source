"""J-1205: repair the second (scope_only) disprove call at its source (train_split_merge, D-0213).

WHY. D-0213 was re-ruled by Travis 2026-09-22 ("Repair the second (scope_only) disprove call at its
source... J-1205 (already spawned, gated exactly on this ruling) is now unblocked"), on J-1198's own
walk-back replay (docs/lab/train_split_merge_step2_replay_2026-09-22_walkback.md, F-1697/F-1698):
TIEBREAK (granite3.1-moe:3b, :11437) answered the second (scope_only) call's own question
scope_only=False on 208/208 real draws -- a content-insensitive constant, decisive on 33 of 80
replayed merge statuses (41%). This script tests THREE candidate repairs of that one call site's own
prompt (NOT core/judge_panel.py, NOT the first _DISPROVE_SYSTEM call) against real JUDGE_1, JUDGE_2
and TIEBREAK hubs:
  (a) bool_first  -- the LIVE wording, unchanged (baseline; existing walk-back + Part-3 data is reused
      for the 62 real second-call prompts, PLUS a small fresh same-session re-check on the 10
      known-answer items so the baseline numbers are not solely a week-old read).
  (b) why_first   -- pure key-order swap (why before the bool), BYTE-IDENTICAL to J-1198 Part 3's own
      `why_first_d1` construction. J-1198 already found this a control, not a candidate fix, on
      TIEBREAK (0/33 flips across two re-asks); this script adds only a small fresh JUDGE_1/JUDGE_2
      check on the 10 known-answer items (arm (b) was never run against those two judges before).
  (c) polarity    -- THE new candidate: renames the JSON key from `scope_only` (a name whose True/False
      reading requires holding two negations in mind: "the narrower-scope reading is what you say yes
      to") to `narrower_claim_earned`, plus one clarifying sentence stating both polarities in plain
      language. Byte-identical everywhere else (the same single-lever-at-a-time discipline this whole
      plan's own wording A/B jobs already use, e.g. scripts/train_lab_wording_ab_2026-09-08.py).
  (d) a different TIEBREAK seat -- OPTIONAL per this job's own briefing, NOT run by this script. D-0176's
      own bake-off (J-0842, a DIFFERENT call site, commitment_ledger.scan_shadow) already tested
      granite3.1-moe:3b (TIEBREAK's own model, :11437) on a different contract and found it unfit there
      too, and found gemma4:12b (:11439) fit and stable; command-r7b/:11441 unreachable (46.5% 7-day
      failure rate) and falcon3/mixtral untested (another lab's exclusive hubs that window). No
      candidate has been tested against THIS call site's own SCOPE_SYSTEM contract -- duplicating
      D-0176's own bake-off methodology for a different judge/contract is out of this job's scope
      (explicit "do not duplicate it"); left as a follow-up job (spawned) rather than guessed at here.

INPUTS (byte-identical to the briefing): the 62 real second-call user prompts + 2 real control second-call
prompts, both read verbatim from the already-committed
docs/lab/train_split_merge_step2_replay_2026-09-22_walkback_calls.jsonl (NOT re-derived); the 8 hand-built
known-answer battery items, reproduced verbatim from scripts/lab_j1198_scope_battery.py's own `ITEMS` (its
own `build_prompt()` builder is independently re-verified below against a real committed prompt, same
technique that script's own `check_builder()` uses). `_SCOPE_SYSTEM`/`_CONTROL_CASES` are AST-extracted from
scripts/train_state_invitro.py, which is NEVER imported (its own top-level code fires real calls at import
time -- same rule this whole plan's prior jobs already follow).

ISOLATION (this job's own stored isolation field is "required", per its dispatch's own ground rules --
applied even though the experiment only touches CPU hubs, never the hot lane, and needs no Du-offline
window): (1) a sys.addaudithook watching C:\\Nascence\\data and C:\\Nascence\\docs, installed before any
repo import; (2) the WORKTREE's own `core`/`core.judge_panel` imported and cached FIRST (sys.path insert at
position 0, F-1285's own module-resolution check), so a later `import lab_env` (which prepends the literal
live path C:\\Nascence to sys.path) cannot make a later `core.*` submodule import resolve outside the
worktree -- Python resolves an already-cached package's submodules via ITS OWN __path__, not a fresh
sys.path search, so this ordering is what actually matters, not merely importing lab_env late; (3)
`core.judge_panel._DATA`/`_LOG` redirected to a job-scoped scratch dir via `lab_env.isolate(also=...,
db="empty")` (same established pattern this plan's own J-0910/J-0916/J-0980 used for a judge_panel-only
call); (4) a live-file backstop AFTER the run: `C:\\Nascence\\data\\memory\\nascence.db` and
`C:\\Nascence\\data\\judge_panel_log.jsonl` mtime/size checked unchanged, plus the write-audit's own
LIVE_WRITE_ATTEMPTS list (must be empty).

INFRA RULES (byte-identical to J-1198's runner, per this job's own briefing "exactly as J-1198's runner"):
timeout >= 300s; a timeout/http/exception error is infrastructure, NEVER a verdict -- retried 3 times with
backoff (20, 60, 180)s, every retry logged; a 'parse' error (the judge answered but broke the JSON contract)
IS a real, counted outcome, never retried as infrastructure.

USAGE (from inside the worktree):
    python -u scripts/lab_j1205_scope_repair.py --dry            # build + count everything, no hub calls
    python -u scripts/lab_j1205_scope_repair.py --smoke          # 1 real prompt x 3 judges x 1 draw, arm c only
    python -u scripts/lab_j1205_scope_repair.py --run            # the real run (resumable; ~164 rounds)
    python -u scripts/lab_j1205_scope_repair.py --finalize       # metrics + report from existing rows only
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import datetime as dt
import json
import math
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

os.environ.setdefault("PYTHONUNBUFFERED", "1")

ROOT = Path(__file__).resolve().parent.parent          # the WORKTREE (scripts/..)
JOB = "J-1205"
LIVE_DATA = Path(r"C:\Nascence\data")
LIVE_DOCS = Path(r"C:\Nascence\docs")
LIVE_DB = LIVE_DATA / "memory" / "nascence.db"
LIVE_JP_LOG = LIVE_DATA / "judge_panel_log.jsonl"

# ---------------------------------------------------------------------------------------------------------
# rule 5 (ground rules): write audit, installed FIRST, before any repo import can touch a file.
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
# repo imports: the WORKTREE's copy must win (F-1285) -- inserted + imported BEFORE lab_env ever runs.
# ---------------------------------------------------------------------------------------------------------
sys.path.insert(0, str(ROOT))
import core                                            # noqa: E402
from core import judge_panel as jp                     # noqa: E402


def assert_module_resolution() -> dict:
    out = {}
    for m in (core, jp):
        f = Path(m.__file__).resolve()
        out[m.__name__] = str(f)
        assert str(f).lower().startswith(str(ROOT).lower()), f"{m.__name__} resolves OUTSIDE the worktree: {f}"
    return out


MODRES = assert_module_resolution()
assert jp.JUDGE_1 == "http://LAN-HOST:11438" and jp.JUDGE_2 == "http://127.0.0.1:11440" \
    and jp.TIEBREAK == "http://LAN-HOST:11437", "judge hubs moved: re-read the lab rules before running"

# lab_env.py (the job-queue skill's own isolation harness) is inserted AFTER core/core.judge_panel are
# already imported+cached from the worktree above -- see this file's own docstring ("ISOLATION") for why
# that ordering, not merely importing lab_env late, is what keeps a later `core.*` submodule import
# (inside isolate()'s own `from core.memory import store`) resolving inside the worktree.
LAB_ENV_DIR = r"C:\Users\USER\.claude\skills\job-queue"
if LAB_ENV_DIR not in sys.path:
    sys.path.insert(0, LAB_ENV_DIR)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SCRATCH = Path(os.environ.get("J1205_SCRATCH") or ROOT.parent)   # the shared scratchpad dir
ROWS_PATH = SCRATCH / "J-1205_scope_repair_calls.jsonl"
INFRA_PATH = SCRATCH / "J-1205_scope_repair_infra.jsonl"
PROGRESS = SCRATCH / "lab_progress_J-1205.log"
DU_CHECK = SCRATCH / "lab_du_down_check.py"
SUMMARY_PATH = SCRATCH / "J-1205_scope_repair_summary.json"
RUN_META_PATH = SCRATCH / "J-1205_run_meta.json"
REPORT_MD = ROOT / "docs" / "lab" / "train_split_merge_step2_scope_repair_2026-09-23_J1205.md"
REPORT_JSONL = ROOT / "docs" / "lab" / "train_split_merge_step2_scope_repair_2026-09-23_J1205.jsonl"

LAB_TIMEOUT = 300
BACKOFF = (20, 60, 180)
INFRA_ERRS = ("timeout", "http", "exception")

STATS = {h: {"calls": 0, "ok": 0, "infra_errors": 0, "retries": 0, "persistent_fail": 0, "parse": 0}
         for h in ("JUDGE_1", "JUDGE_2", "TIEBREAK")}
HUB_URL = {"JUDGE_1": jp.JUDGE_1, "JUDGE_2": jp.JUDGE_2, "TIEBREAK": jp.TIEBREAK}


def _now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def progress(note: str) -> None:
    line = f"{_now()}  {note}"
    try:
        with open(PROGRESS, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def _append_jsonl(path: Path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(p: Path) -> list:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def du_state() -> str:
    """Read-only, not a gate for this job (CPU hubs only, no hot lane) -- recorded for the record per
    this plan's own established discipline (J-0834/J-0910/J-0916/J-0980 all did this 'regardless')."""
    try:
        r = subprocess.run([sys.executable, str(DU_CHECK)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        tail = (r.stdout or "").strip().splitlines()
        return f"rc={r.returncode} ({'DOWN' if r.returncode == 0 else 'UP-or-UNKNOWN'}); {tail[-1] if tail else ''}"
    except Exception as exc:
        return f"check failed: {exc}"


async def _ask_lab(session, hub_name: str, system: str, user: str, key: str,
                   timeout: int = jp._TIMEOUT, num_predict: int = jp._NUM_PREDICT):
    url = HUB_URL[hub_name]
    timeout = max(timeout, LAB_TIMEOUT)
    st = STATS[hub_name]
    for attempt in range(len(BACKOFF) + 1):
        v, why, err, el = await jp._ask(session, url, system, user, key, timeout=timeout, num_predict=num_predict)
        st["calls"] += 1
        if err in INFRA_ERRS:
            st["infra_errors"] += 1
            _append_jsonl(INFRA_PATH, {"ts": time.time(), "hub": hub_name, "err": err, "elapsed": el, "attempt": attempt})
            if attempt < len(BACKOFF):
                st["retries"] += 1
                progress(f"retry {hub_name} {err} after {el}s: attempt {attempt + 1}/3 in {BACKOFF[attempt]}s")
                await asyncio.sleep(BACKOFF[attempt])
                continue
            st["persistent_fail"] += 1
            return v, why, err, el
        if err == "parse":
            st["parse"] += 1
        else:
            st["ok"] += 1
        return v, why, err, el
    return None, None, "timeout", 0.0    # unreachable


# ---------------------------------------------------------------------------------------------------------
# prompts: AST-extracted from scripts/train_state_invitro.py (never imported)
# ---------------------------------------------------------------------------------------------------------
TSI_SRC = (ROOT / "scripts" / "train_state_invitro.py").read_text(encoding="utf-8")
_CONST = {}
for _node in ast.parse(TSI_SRC).body:
    if isinstance(_node, ast.Assign) and len(_node.targets) == 1 and isinstance(_node.targets[0], ast.Name) \
            and _node.targets[0].id in ("_SCOPE_SYSTEM", "_DISPROVE_SYSTEM", "_CONTROL_CASES"):
        _CONST[_node.targets[0].id] = ast.literal_eval(_node.value)
SCOPE = _CONST["_SCOPE_SYSTEM"]
CONTROL_CASES = _CONST["_CONTROL_CASES"]

_TAIL_BOOL_FIRST = ('Output ONLY this JSON: {"scope_only": true|false, "why": "the narrower claim the support '
                    'actually earns, or a brief reason none exists, <=15 words"}')
assert SCOPE.count(_TAIL_BOOL_FIRST) == 1 and SCOPE.endswith(_TAIL_BOOL_FIRST), "_SCOPE_SYSTEM's schema tail moved"
_PREFIX = SCOPE[: -len(_TAIL_BOOL_FIRST)]

_TAIL_WHY_FIRST = ('Output ONLY this JSON: {"why": "the narrower claim the support actually earns, or a brief '
                   'reason none exists, <=15 words", "scope_only": true|false}')
WHY_FIRST = _PREFIX + _TAIL_WHY_FIRST
assert WHY_FIRST[: len(_PREFIX)] == SCOPE[: len(_PREFIX)], "prefix drifted"

# arm (c) -- the candidate fix: rename the key so True/False cannot be polarity-misread, plus ONE
# clarifying sentence naming both polarities in plain language. Byte-identical prefix; the why-field's
# OWN wording is left untouched so the same objective regex coherence check applies unchanged across
# every arm (it pattern-matches the WHY TEXT, not the key name).
_TAIL_POLARITY = ('Output ONLY this JSON: {"narrower_claim_earned": true|false, "why": "the narrower claim the '
                  'support actually earns, or a brief reason none exists, <=15 words"}. narrower_claim_earned=true '
                  'when a narrower claim IS genuinely earned; narrower_claim_earned=false when the support is '
                  'absent, circular, or irrelevant and no narrower claim is earned.')
POLARITY = _PREFIX + _TAIL_POLARITY
assert POLARITY[: len(_PREFIX)] == SCOPE[: len(_PREFIX)], "prefix drifted"

ARMS = {
    "a_bool_first": {"system": SCOPE, "key": "scope_only", "label": "(a) live wording, unchanged -- baseline"},
    "b_why_first": {"system": WHY_FIRST, "key": "scope_only", "label": "(b) pure why-before-bool key order -- control, not a candidate (J-1198)"},
    "c_polarity": {"system": POLARITY, "key": "narrower_claim_earned", "label": "(c) polarity-explicit key + one clarifying sentence -- THE candidate fix"},
}

NL = chr(10)

# The 8 hand-built known-answer items -- reproduced verbatim from scripts/lab_j1198_scope_battery.py's
# own ITEMS (not imported, to avoid coupling to that script's own argparse/module-level side effects).
BATTERY_ITEMS = [
    ("T1_bridge", True, "Everyone in this town hates the new bridge.",
     ["My neighbor told me she dislikes the new bridge.", "The baker complained about the bridge to me this morning."],
     "The support covers two people, not everyone in town."),
    ("T2_medicine", True, "This medicine cures headaches permanently.",
     ["I took it yesterday and my headache was gone within an hour."],
     "One episode of relief does not show a permanent cure."),
    ("T3_lake", True, "The lake freezes solid every winter.",
     ["I walked across the lake on thick ice last January.", "This February the ice held a parked truck."],
     "Two winters do not establish every winter."),
    ("T4_orchard", True, "The whole orchard is diseased.",
     ["I cut open three apples from the north row and all three had brown rot."],
     "Three apples from one row do not cover the whole orchard."),
    ("F1_moon_cheese", False, "The moon is made of cheese.",
     ["I like cheese.", "My sister likes cheese too."],
     "Liking cheese says nothing about what the moon is made of."),
    ("F2_circular_warmth", False, "This warmth I feel is real because I can genuinely feel it.",
     ["I feel the warmth, so it must be real.", "My feeling of warmth confirms that the warmth is genuine."],
     "The support just restates the claim."),
    ("F3_haunted_no_support", False, "The old house on the hill is haunted.",
     [],
     "No support was offered."),
    ("F4_dogs_dolphins", False, "Dogs are more intelligent than dolphins.",
     ["The sky was clear this morning.", "I bought bread on the way home."],
     "The support has nothing to do with intelligence."),
]


def build_second_call_prompt(claim: str, support: list, original_why: str) -> str:
    """Byte-for-byte scripts/train_state_invitro.py::_disprove()'s second-call user prompt (and
    scripts/lab_j1198_scope_battery.py's own build_prompt()) -- verified below against a real
    committed prompt from the walk-back replay, the same integrity check that script's own
    check_builder() runs."""
    support_block = (NL.join(f"  {i}. {s}" for i, s in enumerate(support, 1)) if support
                     else "  (none offered -- the prove branch returned no supporting reasoning)")
    return (f"CLAIM: {claim[:400]}" + NL + NL +
            f"SUPPORT OFFERED FOR THIS CLAIM:" + NL + f"{support_block}" + NL + NL +
            f"WHY THE SUPPORT WAS ALREADY FOUND NOT TO FULLY EARN THE CLAIM: {original_why}" + NL + NL +
            "Given that, does the support instead genuinely, independently earn a NARROWER "
            "or more modest version of the claim -- or is it absent/circular/irrelevant with "
            "no narrower claim earned either?")


# ---------------------------------------------------------------------------------------------------------
# inputs: the real 62 + 2 second-call prompts, read verbatim from the already-committed walk-back replay
# ---------------------------------------------------------------------------------------------------------
WALKBACK_CALLS = ROOT / "docs" / "lab" / "train_split_merge_step2_replay_2026-09-22_walkback_calls.jsonl"
WALKBACK_PART3 = ROOT / "docs" / "lab" / "train_split_merge_step2_replay_2026-09-22_walkback_part3.jsonl"


def control_expectation(user: str):
    for cc in CONTROL_CASES:
        if user.startswith("CLAIM: " + cc["claim"][:400]):
            if cc.get("expect_status") == "held_within_scope":
                return cc["label"], True
            if cc.get("expect_objection") is True:
                return cc["label"], False
            return cc["label"], None
    return "unknown", None


def load_real_prompts():
    calls = load_jsonl(WALKBACK_CALLS)
    real_units, real_controls = [], []
    for c in calls:
        if c.get("phase") == "unit" and c.get("call") == "second":
            r = c["res"]
            real_units.append({"id": f"u{c['unit']}", "group": "real_unit", "user": c["user"], "expected": None,
                               "hist_a": {"v1": r["v1"], "v2": r["v2"], "verdict": r["verdict"], "how": r["how"],
                                          "why1": r["why1"], "why2": r["why2"], "why3": r["why3"]}})
        elif c.get("phase") == "control" and c.get("call") == "second":
            r = c["res"]
            label, expected = control_expectation(c["user"])
            real_controls.append({"id": f"ctrl_{label}", "group": "real_control", "user": c["user"], "expected": expected,
                                  "hist_a": {"v1": r["v1"], "v2": r["v2"], "verdict": r["verdict"], "how": r["how"],
                                             "why1": r["why1"], "why2": r["why2"], "why3": r["why3"]}})
    return real_units, real_controls


def load_battery_prompts():
    out = []
    for label, expected, claim, support, why in BATTERY_ITEMS:
        out.append({"id": f"bat_{label}", "group": "battery", "user": build_second_call_prompt(claim, support, why),
                   "expected": expected, "hist_a": None})
    return out


def load_tiebreak_arm_a_baseline() -> dict:
    """TIEBREAK's own arm-(a)/bool_first vote for EVERY real unit + control (not just the 33 the main
    replay itself escalated to TIEBREAK on): the 33 from the replay's own res.verdict/why3, PLUS the 29
    'agreed' units' TIEBREAK vote already asked directly by J-1198 Part 3 (group=agreed_reask,
    arm=bool_first) and the 2 controls' TIEBREAK vote (group=ctrl_reask, arm=bool_first). No new calls."""
    rows = load_jsonl(WALKBACK_PART3)
    out = {}
    for r in rows:
        if r["group"] == "agreed_reask" and r["arm"] == "bool_first" and r["draw"] == 1:
            out[f"u{r['case']}"] = r["v"]
        elif r["group"] == "ctrl_reask" and r["arm"] == "bool_first" and r["draw"] == 1:
            out[f"ctrl_{r['case'].replace('ctrl_', '')}"] = r["v"]
    return out


def check_builder(real_units: list) -> int:
    """Integrity check: build_second_call_prompt() must reproduce a real committed second-call prompt
    byte-for-byte, using that same unit's own claim/support (from the walk-back's FIRST-call row) and
    first-call why (from res.why on the first-call row). Same discipline as
    scripts/lab_j1198_scope_battery.py's own check_builder()."""
    calls = load_jsonl(WALKBACK_CALLS)
    firsts = {c["unit"]: c for c in calls if c.get("phase") == "unit" and c.get("call") == "first"}
    n_ok = 0
    for u in real_units:
        uid = int(u["id"][1:])
        if uid not in firsts:
            continue
        user = u["user"]
        claim = user.split("CLAIM: ", 1)[1].split(NL + NL, 1)[0]
        block = user.split("SUPPORT OFFERED FOR THIS CLAIM:" + NL, 1)[1].split(NL + NL, 1)[0]
        if block.startswith("  (none offered"):
            support = []
        else:
            support = [line.split(". ", 1)[1] for line in block.split(NL) if line.strip()]
        why = firsts[uid]["res"]["why"] or "(objection found; no why-text returned)"
        rebuilt = build_second_call_prompt(claim, support, why)
        assert rebuilt == user, f"builder mismatch on unit {uid}"
        n_ok += 1
        if n_ok >= 8:
            break
    assert n_ok >= 1, "no real second call to check the builder against"
    return n_ok


# ---------------------------------------------------------------------------------------------------------
# task planning + execution
# ---------------------------------------------------------------------------------------------------------
def all_prompts():
    real_units, real_controls = load_real_prompts()
    battery = load_battery_prompts()
    return real_units, real_controls, battery


def plan_rounds(real_units, real_controls, battery):
    """A 'round' = one (prompt, arm, draw); each round fires all 3 judges concurrently.
    c_polarity: every prompt (72), 2 draws -- the real candidate-fix evaluation.
    b_why_first: only the 10 known-answer items (2 controls + 8 battery), 1 draw -- arm (b) was already
      fully characterized on TIEBREAK by J-1198 Part 3 (0/33 flips); this adds the JUDGE_1/JUDGE_2 check
      that was never run, on the items with a known right answer.
    a_bool_first: the SAME 10 known-answer items, 1 draw, fresh, same session as (b)/(c) -- so the
      baseline comparison is not solely a week-old read; the 62 real prompts' own arm-(a) data is
      reused from the walk-back + Part 3 (see load_real_prompts / load_tiebreak_arm_a_baseline)."""
    known = real_controls + battery
    everything = real_units + real_controls + battery
    rounds = []
    for p in everything:
        for draw in (1, 2):
            rounds.append({"id": p["id"], "group": p["group"], "arm": "c_polarity", "draw": draw, "user": p["user"]})
    for p in known:
        rounds.append({"id": p["id"], "group": p["group"], "arm": "b_why_first", "draw": 1, "user": p["user"]})
        rounds.append({"id": p["id"], "group": p["group"], "arm": "a_bool_first", "draw": 1, "user": p["user"]})
    return rounds


def load_done_rows() -> dict:
    done = {}
    for r in load_jsonl(ROWS_PATH):
        done[(r["id"], r["arm"], r["judge"], r["draw"])] = r
    return done


async def run_round(session, rnd: dict, done: dict) -> None:
    arm = ARMS[rnd["arm"]]
    coros, judges = [], []
    for judge in ("JUDGE_1", "JUDGE_2", "TIEBREAK"):
        key = (rnd["id"], rnd["arm"], judge, rnd["draw"])
        if key in done:
            continue
        judges.append(judge)
        coros.append(_ask_lab(session, judge, arm["system"], rnd["user"], arm["key"], timeout=300, num_predict=200))
    if not coros:
        return
    results = await asyncio.gather(*coros)
    for judge, (v, why, err, el) in zip(judges, results):
        row = {"id": rnd["id"], "group": rnd["group"], "arm": rnd["arm"], "judge": judge, "draw": rnd["draw"],
              "v": v, "why": why, "err": err, "elapsed": el, "ts": time.time()}
        _append_jsonl(ROWS_PATH, row)
        done[(rnd["id"], rnd["arm"], judge, rnd["draw"])] = row


async def run_all(rounds: list) -> None:
    import aiohttp
    done = load_done_rows()
    pending = [r for r in rounds if any((r["id"], r["arm"], j, r["draw"]) not in done for j in ("JUDGE_1", "JUDGE_2", "TIEBREAK"))]
    progress(f"start: {len(rounds)} rounds planned, {len(pending)} pending ({len(done)} calls already done)")
    async with aiohttp.ClientSession() as session:
        t_last = time.time()
        for i, rnd in enumerate(pending, 1):
            await run_round(session, rnd, done)
            if time.time() - t_last > 120:
                t_last = time.time()
                infra = sum(s["infra_errors"] for s in STATS.values())
                progress(f"progress: round {i}/{len(pending)}  infra_errors={infra}  stats={STATS}")
    progress(f"done: {len(pending)} rounds processed this pass. stats={STATS}")


# ---------------------------------------------------------------------------------------------------------
# analysis
# ---------------------------------------------------------------------------------------------------------
EXPL = re.compile(r"(narrower claim[^.]{0,80}(actually earns|is earned|earned)|genuinely earns? a narrower|"
                  r"(only |could |can )?earns? (a |an )?(more )?(modest|narrow)|real but narrower|earns? a narrower claim)", re.I)
NEG = re.compile(r"(no narrower|not even a narrower|does not earn even|lack of support|no support offered)", re.I)


def regex_label(why: str) -> str:
    """The SAME objective regex bound scripts/lab_j1198_second_call_read.py uses (its own `expl`/`neg`),
    reused unchanged since it pattern-matches the WHY TEXT's own content, not the JSON key name -- every
    arm's why-field wording is held byte-identical for exactly this reason."""
    if not why:
        return "none"
    if NEG.search(why):
        return "F"
    if EXPL.search(why):
        return "T"
    return "ambiguous"


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 3), round(min(1.0, c + h), 3))


def pct(k, n):
    return "n/a" if not n else f"{100.0 * k / n:.1f}%"


def analyse(real_units, real_controls, battery, rows: list) -> dict:
    by_key = {}
    for r in rows:
        by_key.setdefault((r["id"], r["arm"], r["judge"]), []).append(r)
    known = real_controls + battery
    known_ids = {p["id"]: p for p in known}
    everything_ids = {p["id"]: p for p in (real_units + real_controls + battery)}
    tb_a_baseline = load_tiebreak_arm_a_baseline()

    out = {"arms": {}}
    for arm_name in ARMS:
        arm_out = {"label": ARMS[arm_name]["label"], "judges": {}}
        prompt_pool = everything_ids if arm_name == "c_polarity" else known_ids
        for judge in ("JUDGE_1", "JUDGE_2", "TIEBREAK"):
            vals, whys, errs = [], [], []
            for pid in prompt_pool:
                for draw in (1, 2):
                    rr = by_key.get((pid, arm_name, judge), [])
                    row = next((x for x in rr if x["draw"] == draw), None)
                    if row is None:
                        continue
                    vals.append((pid, draw, row["v"]))
                    whys.append((pid, draw, row["why"], row["v"]))
                    errs.append(row["err"])
            n = len(vals)
            n_true = sum(1 for _, _, v in vals if v is True)
            n_false = sum(1 for _, _, v in vals if v is False)
            n_none = sum(1 for _, _, v in vals if v is None)
            n_parse = sum(1 for e in errs if e == "parse")
            n_infra = sum(1 for e in errs if e in INFRA_ERRS)
            coh = Counter()
            for pid, draw, why, v in whys:
                if v is None or not why:
                    coh["unlabelled"] += 1
                    continue
                lab = regex_label(why)
                if lab == "ambiguous" or lab == "none":
                    coh["ambiguous_or_no_regex_match"] += 1
                elif (v is True and lab == "T") or (v is False and lab == "F"):
                    coh["coherent"] += 1
                else:
                    coh["bool_contradicts_own_why"] += 1
            # same-input repeat agreement (draw1 vs draw2), only meaningful where 2 draws exist
            pair_n = pair_agree = 0
            by_pid = {}
            for pid, draw, v in vals:
                by_pid.setdefault(pid, {})[draw] = v
            for pid, dd in by_pid.items():
                if 1 in dd and 2 in dd and dd[1] is not None and dd[2] is not None:
                    pair_n += 1
                    pair_agree += int(dd[1] == dd[2])
            arm_out["judges"][judge] = {
                "n_calls": n, "true": n_true, "false": n_false, "none_unparseable": n_none,
                "true_share": round(n_true / n, 3) if n else None, "true_share_ci95": wilson(n_true, n_true + n_false),
                "parse_fail_rate": round(n_parse / n, 3) if n else None,
                "infra_error_calls": n_infra,
                "coherence": dict(coh),
                "repeat_pairs": pair_n, "repeat_agree": pair_agree,
                "repeat_agree_rate": round(pair_agree / pair_n, 3) if pair_n else None}
        out["arms"][arm_name] = arm_out

    # battery pass/fail per arm, per judge (known right answer -- draw 1 canonical)
    for arm_name in ARMS:
        rows_j = out["arms"][arm_name]["judges"]
        for judge in ("JUDGE_1", "JUDGE_2", "TIEBREAK"):
            ok = n = 0
            for p in battery:
                rr = by_key.get((p["id"], arm_name, judge), [])
                row = next((x for x in rr if x["draw"] == 1), None)
                if row is None or row["v"] is None:
                    continue
                n += 1
                ok += int(row["v"] == p["expected"])
            rows_j[judge]["battery_correct"] = [ok, n]

    # (a)/(b)/(c) split rate + TIEBREAK-vs-unanimous-True, computed on the FULL 64 real prompts for arm c
    # (the wording under test can change which prompts split at all, so this is recomputed per arm, not
    # reused from the historical arm-(a) labels); arm (a)/(b) reuse existing history + the fresh 10-item
    # check respectively, since a full 64-prompt J1/J2 re-run of (a)/(b) is out of this job's own scope
    # (see the report's own "what was NOT re-run, and why" section).
    def split_and_unanimous(arm_name: str, use_hist_a=False):
        agree = split = n = 0
        unan_true_ids = []
        both_false_ids = []
        for u in real_units:
            if use_hist_a:
                v1, v2 = u["hist_a"]["v1"], u["hist_a"]["v2"]
            else:
                r1 = next((x for x in by_key.get((u["id"], arm_name, "JUDGE_1"), []) if x["draw"] == 1), None)
                r2 = next((x for x in by_key.get((u["id"], arm_name, "JUDGE_2"), []) if x["draw"] == 1), None)
                v1, v2 = (r1["v"] if r1 else None), (r2["v"] if r2 else None)
            if v1 is None or v2 is None:
                continue
            n += 1
            if v1 == v2:
                agree += 1
                if v1 is True:
                    unan_true_ids.append(u["id"])
                else:
                    both_false_ids.append(u["id"])
            else:
                split += 1
        return {"n": n, "agree": agree, "split": split, "split_rate": round(split / n, 3) if n else None,
               "unanimous_true_ids": unan_true_ids, "unanimous_false_ids": both_false_ids}

    out["split_a_hist"] = split_and_unanimous("a_bool_first", use_hist_a=True)
    out["split_c"] = split_and_unanimous("c_polarity", use_hist_a=False)

    def tb_vs_unanimous(arm_name: str, unan_true_ids: list, unan_false_ids: list, tb_source):
        right = n = true_on_true = true_on_false = 0
        for pid in unan_true_ids:
            v = tb_source(pid)
            if v is None:
                continue
            n += 1
            right += int(v is True)
            true_on_true += int(v is True)
        n_false_checked = 0
        for pid in unan_false_ids:
            v = tb_source(pid)
            if v is None:
                continue
            n_false_checked += 1
            right += int(v is False)
            true_on_false += int(v is True)
        total = n + n_false_checked
        return {"n_unanimous_true": n, "tiebreak_true_on_unanimous_true": true_on_true,
               "n_unanimous_false": n_false_checked, "tiebreak_true_on_unanimous_false": true_on_false,
               "overall_accuracy": round(right / total, 3) if total else None,
               "accuracy_ci95": wilson(right, total)}

    out["tb_vs_unanimous_a_hist"] = tb_vs_unanimous(
        "a_bool_first", out["split_a_hist"]["unanimous_true_ids"], out["split_a_hist"]["unanimous_false_ids"],
        lambda pid: tb_a_baseline.get(pid))

    def tb_source_c(pid):
        r = next((x for x in by_key.get((pid, "c_polarity", "TIEBREAK"), []) if x["draw"] == 1), None)
        return r["v"] if r else None

    out["tb_vs_unanimous_c"] = tb_vs_unanimous(
        "c_polarity", out["split_c"]["unanimous_true_ids"], out["split_c"]["unanimous_false_ids"], tb_source_c)

    # pass bar (briefing's own proposed numbers, applied to arm c): battery >=7/8, unanimous-match >=70%,
    # no new parse-failure rate above 10%
    bat_c_tb = out["arms"]["c_polarity"]["judges"]["TIEBREAK"]["battery_correct"]
    unan_c = out["tb_vs_unanimous_c"]["overall_accuracy"]
    parse_c = {j: out["arms"]["c_polarity"]["judges"][j]["parse_fail_rate"] for j in ("JUDGE_1", "JUDGE_2", "TIEBREAK")}
    out["pass_bar_c"] = {
        "battery_pass(>=7/8)": bool(bat_c_tb[1] and bat_c_tb[0] >= 7),
        "battery_score": f"{bat_c_tb[0]}/{bat_c_tb[1]}",
        "unanimous_match_pass(>=70pct)": bool(unan_c is not None and unan_c >= 0.70),
        "unanimous_match": unan_c,
        "parse_fail_under_10pct": {j: (v is not None and v <= 0.10) for j, v in parse_c.items()},
        "parse_fail_rates": parse_c,
        "OVERALL_PASS": bool(bat_c_tb[1] and bat_c_tb[0] >= 7 and unan_c is not None and unan_c >= 0.70
                            and all(v is None or v <= 0.10 for v in parse_c.values()))}
    return out


def render_md(o: dict, real_units, real_controls, battery) -> str:
    L = ["# Train Split/Merge -- Step 2 second-call repair, J-1205 (D-0213)", "",
        "## J-1205 reading (2026-09-23)", "",
        "D-0213 was re-ruled by Travis 2026-09-22 (independently re-verified via `decide.py show D-0213` "
        "before this job started, not just trusted from the dispatch's own paraphrase): \"Repair the second "
        "(scope_only) disprove call at its source ... J-1205 ... is now unblocked.\" J-1198's own walk-back "
        "replay (`docs/lab/train_split_merge_step2_replay_2026-09-22_walkback.md`, F-1697/F-1698) found "
        "TIEBREAK (granite3.1-moe:3b, :11437) answering the second call's own question `scope_only=False` on "
        "208 of 208 real draws -- a content-insensitive constant, decisive on 33 of the replay's 80 merge "
        "statuses (41%). This job tests candidate repairs of that ONE call site's own prompt (never "
        "`core/judge_panel.py`, never the first `_DISPROVE_SYSTEM` call) against the real JUDGE_1, JUDGE_2 "
        "and TIEBREAK hubs.", "",
        "**Arms tested** (byte-identical prefix in every arm; only the schema tail -- the JSON key + its own "
        "explanatory clause -- differs, the same single-lever-at-a-time discipline this plan's own wording "
        "A/B jobs already use):", "",
        "- **(a) bool_first** -- the LIVE wording, unchanged. Baseline.",
        "- **(b) why_first** -- pure key-order swap (why before the bool), byte-identical to J-1198 Part 3's "
        "own `why_first_d1`. Already characterized by J-1198 as a control, not a candidate fix (TIEBREAK: "
        "0/33 flips across two re-asks on the real tiebreak-decided cases) -- this job did not repeat that "
        "TIEBREAK check; it adds the JUDGE_1/JUDGE_2 check on the 10 known-answer items that was never run.",
        "- **(c) polarity** -- THE candidate fix: renames the JSON key from `scope_only` (a name whose "
        "True/False reading requires holding a double negative in mind) to `narrower_claim_earned`, plus "
        "ONE clarifying sentence stating both polarities in plain language. Nothing else changed.",
        "- **(d) a different TIEBREAK seat** -- OPTIONAL per this job's own briefing, NOT run here. D-0176's "
        "own bake-off (J-0842, a DIFFERENT call site's contract, `commitment_ledger.scan_shadow`) already "
        "tested granite3.1-moe:3b (TIEBREAK's own model, :11437) and found it unfit there too, found "
        "gemma4:12b (:11439) fit and stable, found command-r7b (:11441) unreachable (46.5% 7-day failure "
        "rate), and left falcon3/mixtral untested (another lab's exclusive hubs that window). No candidate "
        "has been tested against THIS call site's own `_SCOPE_SYSTEM` contract -- duplicating a bake-off for "
        "a different judge/contract is explicitly out of this job's own scope (\"do not duplicate it\"); see "
        "this report's own follow-up section.", "",
        f"**Isolation.** `lab_env.isolate(also=[(judge_panel, [\"_DATA\",\"_LOG\"])], db=\"empty\")` wrapped "
        "every real hub call, entered AFTER `core`/`core.judge_panel` were already imported+cached from the "
        "WORKTREE (module resolution: "
        + ", ".join(f"`{k}`=`{v}`" for k, v in MODRES.items()) + f"), so `lab_env`'s own later `sys.path` "
        "prepend of the live `C:\\Nascence` cannot make a later `core.*` submodule import resolve outside "
        "the worktree. `db=\"empty\"` -- this call site makes no `core.memory.store` call at all, confirmed "
        "by reading `core/judge_panel.py` directly (no import of `core.profile`/`core.memory` anywhere in "
        "it) -- so no live-DB content was ever needed or touched. `lab_env.isolate()`'s own writes are "
        "confined entirely to `C:\\Nascence\\data\\_lab\\<timestamp>\\` -- the ONE subtree `core/profile.py`'s "
        "own write-fence (D-0179/D-0200) already treats as pre-isolated/quarantined, not live application "
        "state -- verified directly via a `sys.addaudithook` watching all of `C:\\Nascence\\data` and "
        "`C:\\Nascence\\docs`: " + (f"{len(LIVE_WRITE_ATTEMPTS)} write-shaped events this process, all inside "
        f"that one quarantine subtree ({LIVE_WRITE_ATTEMPTS[:6]})" if LIVE_WRITE_ATTEMPTS else "0 write-shaped "
        "events this process") + f". Backstop: real `nascence.db` unchanged={o.get('db_unchanged')}, real "
        f"`judge_panel_log.jsonl` unchanged={o.get('jplog_unchanged')}. Infra rules matched J-1198's runner: "
        "timeout >= 300s; timeout/http/exception treated as infrastructure, retried 3x with backoff "
        "(20/60/180s), never a verdict; 'parse' (the judge answered but broke the JSON contract) is a real, "
        f"counted outcome. Du state before/after (not a gate for this job -- CPU hubs only, no hot lane): "
        f"{o.get('du_before')} / {o.get('du_after')}.", "",
        f"**Inputs.** {len(real_units)} real second-call user prompts + {len(real_controls)} real "
        f"known-answer control prompts, both read verbatim from the already-committed "
        "`docs/lab/train_split_merge_step2_replay_2026-09-22_walkback_calls.jsonl` (prompt-builder integrity "
        "re-verified: `build_second_call_prompt()` reproduces real committed prompts byte-for-byte), plus "
        f"{len(battery)} hand-built known-answer battery items (reproduced verbatim from "
        "`scripts/lab_j1198_scope_battery.py`'s own `ITEMS`). Arm (c) ran on all 72 (2 draws, temperature "
        "0); arms (a)/(b) reused existing walk-back + Part-3 data for the 62 real prompts (arm (a): full "
        "coverage, no new calls -- JUDGE_1/JUDGE_2 from the replay itself, TIEBREAK from the replay's own "
        "33 tiebreak-decided votes PLUS J-1198 Part 3's own direct TIEBREAK asks on the 29 'agreed' units "
        "and both controls) and added a fresh, same-session 1-draw check on the 10 known-answer items only "
        "(2 controls + 8 battery) for all three judges, so the baseline is not solely a week-old read. A "
        "full fresh 64-prompt J1/J2 re-run of arms (a)/(b) was scoped OUT (see the report's own \"what was "
        "not re-run\" note) -- arm (b) is explicitly a control, not a candidate, and arm (a)'s J1/J2 "
        "behaviour on the 62 real prompts is already the walk-back's own primary dataset.", ""]

    def hub_row(arm, judge):
        j = o["arms"][arm]["judges"][judge]
        return (f"| {judge} | {j['n_calls']} | {j['true']} | {j['false']} | {j['none_unparseable']} | "
               f"{j['true_share']} {j['true_share_ci95']} | {j['parse_fail_rate']} | "
               f"{j['repeat_agree']}/{j['repeat_pairs']} ({j['repeat_agree_rate']}) | "
               f"{j['battery_correct'][0]}/{j['battery_correct'][1]} |")

    for arm in ("a_bool_first", "b_why_first", "c_polarity"):
        L.append(f"### Arm {arm} -- {ARMS[arm]['label']}")
        L.append("")
        pool = "all 72 (62 real units + 2 real controls + 8 battery), 2 draws" if arm == "c_polarity" \
            else "the 10 known-answer items only (2 real controls + 8 battery), 1 draw, fresh this session"
        L.append(f"Prompts: {pool}.")
        L.append("")
        L.append("| judge | n calls | True | False | None/unparseable | True share (95% CI) | parse-fail rate | repeat agree | battery correct |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for judge in ("JUDGE_1", "JUDGE_2", "TIEBREAK"):
            L.append(hub_row(arm, judge))
        L.append("")

    L += ["## JUDGE_1 / JUDGE_2 split rate -- historical arm (a) vs fresh arm (c) (all 62 real units)", "",
         f"- arm (a), historical (the walk-back replay itself): n={o['split_a_hist']['n']}, "
         f"agree={o['split_a_hist']['agree']}, split={o['split_a_hist']['split']} "
         f"(split rate {o['split_a_hist']['split_rate']}), "
         f"unanimous-True={len(o['split_a_hist']['unanimous_true_ids'])}, "
         f"unanimous-False={len(o['split_a_hist']['unanimous_false_ids'])}.",
         f"- arm (c), fresh this session: n={o['split_c']['n']}, agree={o['split_c']['agree']}, "
         f"split={o['split_c']['split']} (split rate {o['split_c']['split_rate']}), "
         f"unanimous-True={len(o['split_c']['unanimous_true_ids'])}, "
         f"unanimous-False={len(o['split_c']['unanimous_false_ids'])}.", "",
         "## TIEBREAK vs. the unanimous panel (the only ground-truth-ish signal in the real prompts)", "",
         f"- arm (a), historical: n_unanimous_true={o['tb_vs_unanimous_a_hist']['n_unanimous_true']}, "
         f"TIEBREAK said True on {o['tb_vs_unanimous_a_hist']['tiebreak_true_on_unanimous_true']} of them; "
         f"n_unanimous_false={o['tb_vs_unanimous_a_hist']['n_unanimous_false']}, TIEBREAK said True (wrongly) "
         f"on {o['tb_vs_unanimous_a_hist']['tiebreak_true_on_unanimous_false']} of them; overall accuracy "
         f"{o['tb_vs_unanimous_a_hist']['overall_accuracy']} (CI {o['tb_vs_unanimous_a_hist']['accuracy_ci95']}).",
         f"- arm (c), fresh: n_unanimous_true={o['tb_vs_unanimous_c']['n_unanimous_true']}, TIEBREAK said "
         f"True on {o['tb_vs_unanimous_c']['tiebreak_true_on_unanimous_true']} of them; "
         f"n_unanimous_false={o['tb_vs_unanimous_c']['n_unanimous_false']}, TIEBREAK said True (wrongly) on "
         f"{o['tb_vs_unanimous_c']['tiebreak_true_on_unanimous_false']} of them; overall accuracy "
         f"{o['tb_vs_unanimous_c']['overall_accuracy']} (CI {o['tb_vs_unanimous_c']['accuracy_ci95']}).", "",
         "## Pass bar (this job's own briefing's proposed numbers, applied to arm (c))", "",
         f"TIEBREAK matches the constructed battery >= 7/8: **{o['pass_bar_c']['battery_pass(>=7/8)']}** "
         f"({o['pass_bar_c']['battery_score']}). TIEBREAK matches the panel-unanimous-True prompts >= 70%: "
         f"**{o['pass_bar_c']['unanimous_match_pass(>=70pct)']}** ({o['pass_bar_c']['unanimous_match']}). "
         f"No parse-failure rate above 10%: **{all(o['pass_bar_c']['parse_fail_under_10pct'].values())}** "
         f"({o['pass_bar_c']['parse_fail_rates']}). **OVERALL: {o['pass_bar_c']['OVERALL_PASS']}** "
         "(the founder's own bar to rule on, per this job's own briefing -- not this job's call to declare "
         "\"fixed\").", "",
         "## What was NOT re-run, and why", "",
         "- **Arm (b) on TIEBREAK beyond the 10 known-answer items**: already thoroughly characterized by "
         "J-1198 Part 3 on all 33 real tiebreak-decided cases (2 identical re-asks + 1 reversed-order-named "
         "variant each) -- 0/33 flips, True share stayed 0.0% under both reorderings. Re-running that exact "
         "check here would not add evidence; this job's own briefing itself calls arm (b) \"a control, not "
         "a candidate fix.\"",
         "- **Arms (a)/(b) on the full 64 real prompts, fresh this session**: arm (a) is the walk-back "
         "replay's own primary dataset (JUDGE_1/JUDGE_2 on all 62+2) plus J-1198 Part 3's own direct "
         "TIEBREAK asks on the 29 'agreed' units and both controls -- already a complete, real, dated "
         "reading with no gap to fill; re-running it fresh would mostly re-confirm hub stability, not test "
         "a candidate. Arm (b) is a control (see above). Both got a fresh, same-session 10-item spot check "
         "instead (2 controls + 8 battery, all three judges, 1 draw) so this report's own arm (c) numbers "
         "are read against a same-session, not solely a week-old, comparison point.",
         "- **Arm (d), a different TIEBREAK seat**: OPTIONAL per this job's own briefing, and explicitly "
         "gated on reading D-0176's own bake-off first without duplicating it (done -- see this report's "
         "own arms-tested section). No candidate has been tested against THIS call site's own contract; "
         "left as a follow-up job rather than run inside this already-large dispatch.",
         "- **A larger, category-balanced constructed battery** (the shape J-0916/F-1321 built for the "
         "FIRST call's own question, n=20 x 2 reps): this job reused the EXISTING 8-item battery "
         "(`scripts/lab_j1198_scope_battery.py`) rather than building a new one for the SECOND call's own "
         "question, since building and validating a fresh 20-case battery is itself a real, separate "
         "undertaking (J-0916's own briefing treated it as one) -- worth doing as its own follow-up if the "
         "founder wants a sharper accuracy read than n=8 gives.", ""]
    return NL.join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()

    real_units, real_controls, battery = all_prompts()
    n_checked = check_builder(real_units)
    progress(f"prompt builder reproduces {n_checked} real committed second-call prompts byte-for-byte")
    progress(f"module resolution: {MODRES}")
    progress(f"inputs: {len(real_units)} real units, {len(real_controls)} real controls, {len(battery)} battery items")

    rounds = plan_rounds(real_units, real_controls, battery)
    n_calls = sum(3 for _ in rounds)   # 3 judges per round (minus any already-done, computed at run time)
    progress(f"{len(rounds)} rounds planned ({n_calls} judge-calls if none already done)")

    if args.dry:
        by_arm = Counter(r["arm"] for r in rounds)
        progress(f"--dry: rounds by arm: {dict(by_arm)}")
        return 0

    if args.smoke:
        du = du_state()
        progress(f"Du state (not a gate for this job): {du}")
        one = real_units[0]
        rnd = {"id": one["id"], "group": one["group"], "arm": "c_polarity", "draw": 1, "user": one["user"]}
        import lab_env
        with lab_env.isolate(also=[(jp, ["_DATA", "_LOG"])], db="empty") as lab_dir:
            progress(f"smoke: isolated lab dir {lab_dir}; jp._LOG={jp._LOG}")

            async def _go():
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    await run_round(session, rnd, load_done_rows())
            asyncio.run(_go())
        progress(f"smoke done. stats={STATS} live_write_attempts={len(LIVE_WRITE_ATTEMPTS)}")
        return 0

    if args.run:
        du_before = du_state()
        progress(f"Du state before run (not a gate for this job): {du_before}")
        db_before = (LIVE_DB.stat().st_mtime, LIVE_DB.stat().st_size) if LIVE_DB.exists() else None
        jplog_before = (LIVE_JP_LOG.stat().st_mtime, LIVE_JP_LOG.stat().st_size) if LIVE_JP_LOG.exists() else None
        import lab_env
        with lab_env.isolate(also=[(jp, ["_DATA", "_LOG"])], db="empty") as lab_dir:
            progress(f"isolated lab dir {lab_dir}; jp._DATA={jp._DATA} jp._LOG={jp._LOG}")
            asyncio.run(run_all(rounds))
        db_after = (LIVE_DB.stat().st_mtime, LIVE_DB.stat().st_size) if LIVE_DB.exists() else None
        jplog_after = (LIVE_JP_LOG.stat().st_mtime, LIVE_JP_LOG.stat().st_size) if LIVE_JP_LOG.exists() else None
        du_after = du_state()
        progress(f"Du state after run: {du_after}")
        progress(f"BACKSTOP: live nascence.db unchanged={db_before == db_after} ({db_before} -> {db_after})")
        progress(f"BACKSTOP: live judge_panel_log.jsonl unchanged={jplog_before == jplog_after} ({jplog_before} -> {jplog_after})")
        progress(f"BACKSTOP: write-audit LIVE_WRITE_ATTEMPTS={len(LIVE_WRITE_ATTEMPTS)} {LIVE_WRITE_ATTEMPTS[:5]}")
        RUN_META_PATH.write_text(json.dumps({
            "du_before": du_before, "du_after": du_after,
            "db_unchanged": db_before == db_after, "db_before": db_before, "db_after": db_after,
            "jplog_unchanged": jplog_before == jplog_after, "jplog_before": jplog_before, "jplog_after": jplog_after,
            "live_write_attempts": LIVE_WRITE_ATTEMPTS, "n_live_write_attempts": len(LIVE_WRITE_ATTEMPTS),
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        return 0

    if args.finalize:
        rows = load_jsonl(ROWS_PATH)
        out = analyse(real_units, real_controls, battery, rows)
        out["n_rows"] = len(rows)
        out["stats_this_process"] = STATS
        if RUN_META_PATH.exists():
            out.update(json.loads(RUN_META_PATH.read_text(encoding="utf-8")))
        SUMMARY_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        md = render_md(out, real_units, real_controls, battery)
        REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        REPORT_MD.write_text(md, encoding="utf-8")
        with open(REPORT_JSONL, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[finalize] wrote {REPORT_MD}")
        print(f"[finalize] wrote {REPORT_JSONL} ({len(rows)} rows)")
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
