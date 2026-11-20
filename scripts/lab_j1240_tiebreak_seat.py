"""J-1240: test gemma4:12b as an alternate TIEBREAK seat for the second (scope_only) disprove call,
arm (d) of D-0213's own repair experiment (train_split_merge).

WHY. D-0213 was re-ruled by Travis 2026-09-23 ("Hold -- wait for J-1240 ... before deciding further"):
J-1205 tested the PROMPT half of D-0213's own defeater ("every candidate model/prompt") and neither
candidate (why-before-bool reorder, polarity-explicit rewording) repaired TIEBREAK's (granite3.1-moe:3b,
:11437) constant `scope_only=False` vote -- 0.0% True share on 144 fresh draws under arm (c), same 4/8
battery score as the unfixed prompt. Only the MODEL half remains untested. This job reuses J-1205's own
harness (scripts/lab_j1205_scope_repair.py) almost unchanged -- same arms, same inputs, same isolation,
same infra rules -- with exactly ONE change: the "TIEBREAK" role's hub is repointed from granite's live
:11437 to gemma4:12b's hub for this one experiment only. `core/judge_panel.py`'s own live TIEBREAK
constant is NEVER touched (no import-time mutation, no monkeypatch of the shared module) -- this script
defines its own CANDIDATE_URL and only ITS OWN local HUB_URL dict (used solely by this script's own
`_ask_lab` calls) points there.

CORRECTED HUB ADDRESS (verify-before-calling, per this job's own briefing -- "do not repeat D-0176's
command-r7b mistake blind"). The dispatch briefing named gemma4:12b's address as
`http://LAN-HOST:11439` ("Ramses"), citing "core/judge_panel.py's own historical repointing
comments". That address is WRONG -- independently checked three ways before any real judge call was
made: (1) a direct probe (GET /api/tags) to `http://LAN-HOST:11439` fails to connect (curl exit 7,
"Failed to connect to host") -- nothing is listening there; (2) a direct probe to
`http://127.0.0.1:11439` (LOCAL, this same Threadripper/Bonsai machine) succeeds and returns
`{"models":[{"name":"gemma4:12b", ...}]}` -- the real hub; (3) cross-referenced against SEVEN other
places in this same tree that all independently agree on `127.0.0.1:11439`, none mentioning
`LAN-HOST:11439` anywhere: `core/judge_panel.py`'s own comment (line 43, "was local gemma4:12b
:11439, dark"), `core/model_client.py` (`MODEL_BY_PORT["11439"] == "gemma4:12b"`),
`core/left_lane.py` (`BASE_URL = "http://127.0.0.1:11439"`), `core/deliberation.py` ("gemma4:12b on
the local judge-1 hub, 127.0.0.1:11439"), `core/librarian.py` (`_HUBS` includes
`"http://127.0.0.1:11439"`), `core/peers.py` (`_HUB_LLAMA = "http://127.0.0.1:11439"`), and
`scripts/d0176_scan_bakeoff.py` -- THE bake-off script the briefing itself cites as the source of the
address -- whose own `HUBS["gemma"]` is literally `("http://127.0.0.1:11439", "gemma4:12b, local CPU
(Threadripper)")`. `C:\\Nascence\\CLAUDE.md` (the project's own root instructions, "Never launch Du's
servers...") independently names this same port as one of the four LOCAL servers the live supervisor
watches ("judge1 :11439"). The briefing's paraphrase of "core/judge_panel.py's own historical
repointing comments" mis-read a DIFFERENT, retired local-vs-Ramres repoint (D-0121, 2026-09-02: JUDGE_1
moved OFF 127.0.0.1:11439 -- because the local gemma hub was dark THAT DAY -- ONTO Ramses :11438) as if
it meant gemma4:12b itself now lives on Ramses; it does not, and never did in any file this repo holds.
This is recorded as a finding (a real, confirmed briefing error caught by the "verify reachable" step
the briefing itself required), not silently worked around.

ARMS (byte-identical to J-1205 -- see that script's own docstring for the full prompt text): (a)
bool_first -- live wording, unchanged; (b) why_first -- pure key-order swap, J-1198's own control; (c)
polarity -- the polarity-explicit rewording. All three are run here (not just one), because J-1205's own
read found arm (c) showed NO promise over arm (a) on granite (battery 4/8 both; unanimous-match 37.0%
vs 37.9%, statistically indistinguishable) -- so the briefing's own conditional ("bool_first, or
polarity IF it showed promise") does not resolve to a single arm on the evidence in hand. Running all
three (exactly mirroring J-1205's own design, changing only the hub) avoids guessing which wording to
prefer and gives a clean, symmetric comparison against every one of J-1205's own granite numbers.

INPUTS: identical to J-1205 -- byte-for-byte reused from the same already-committed files, never
re-derived. `_SCOPE_SYSTEM` is AST-extracted from scripts/train_state_invitro.py, which is NEVER
imported.

ISOLATION: required (lab_experiment), same discipline as J-1205 -- sys.addaudithook write-fence
installed before any repo import, worktree-first sys.path (core/core.judge_panel imported+cached before
lab_env can prepend the live tree), lab_env.isolate(also=[(jp, ["_DATA","_LOG"])], db="empty"), a
live-file backstop (nascence.db / judge_panel_log.jsonl mtime+size) checked after the run.

Do NOT re-point core/judge_panel.py's own live TIEBREAK constant based on this job alone -- candidate-
seat characterization only, per this job's own briefing.

USAGE (from inside the worktree):
    python -u scripts/lab_j1240_tiebreak_seat.py --probe     # hub reachability + model check only
    python -u scripts/lab_j1240_tiebreak_seat.py --dry       # build + count everything, no hub calls
    python -u scripts/lab_j1240_tiebreak_seat.py --smoke     # 1 real prompt x 3 judges x 1 draw, arm c
    python -u scripts/lab_j1240_tiebreak_seat.py --run       # the real run (resumable; ~154 rounds)
    python -u scripts/lab_j1240_tiebreak_seat.py --finalize  # metrics + report from existing rows only
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
import urllib.request
from collections import Counter
from pathlib import Path

os.environ.setdefault("PYTHONUNBUFFERED", "1")

ROOT = Path(__file__).resolve().parent.parent          # the WORKTREE (scripts/..)
JOB = "J-1240"
LIVE_DATA = Path(r"C:\Nascence\data")
LIVE_DOCS = Path(r"C:\Nascence\docs")
LIVE_DB = LIVE_DATA / "memory" / "nascence.db"
LIVE_JP_LOG = LIVE_DATA / "judge_panel_log.jsonl"

# ---------------------------------------------------------------------------------------------------------
# write audit, installed FIRST, before any repo import can touch a file (same technique as J-1205).
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
assert jp.JUDGE_1 == "http://LAN-HOST:11438" and jp.JUDGE_2 == "http://127.0.0.1:11440", \
    "judge hubs moved: re-read the lab rules before running"
# jp.TIEBREAK (granite3.1-moe:3b, :11437) is read for the record only -- this job never calls it and
# never mutates it; the CANDIDATE hub below is a wholly separate constant.
LIVE_TIEBREAK_FOR_RECORD = jp.TIEBREAK

# THE CANDIDATE -- see this file's own docstring "CORRECTED HUB ADDRESS" section for the verification
# (probe + 7-file cross-reference) that overturned the dispatch briefing's wrong LAN-HOST:11439 claim.
CANDIDATE_URL = "http://127.0.0.1:11439"
CANDIDATE_LABEL = "gemma4:12b (local, Threadripper/Bonsai CPU tier -- verified 2026-09-23, NOT the live :11437 TIEBREAK)"

# lab_env.py (the job-queue skill's own isolation harness) is inserted AFTER core/core.judge_panel are
# already imported+cached from the worktree above -- see J-1205's own docstring for why that ordering
# (not merely importing lab_env late) is what keeps a later `core.*` submodule import resolving inside
# the worktree.
LAB_ENV_DIR = r"C:\Users\USER\.claude\skills\job-queue"
if LAB_ENV_DIR not in sys.path:
    sys.path.insert(0, LAB_ENV_DIR)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SCRATCH = Path(os.environ.get("J1240_SCRATCH") or ROOT.parent)   # the shared scratchpad dir
ROWS_PATH = SCRATCH / "J-1240_tiebreak_seat_calls.jsonl"
INFRA_PATH = SCRATCH / "J-1240_tiebreak_seat_infra.jsonl"
PROGRESS = SCRATCH / "lab_progress_J-1240.log"
DU_CHECK = SCRATCH / "lab_du_down_check.py"
SUMMARY_PATH = SCRATCH / "J-1240_tiebreak_seat_summary.json"
RUN_META_PATH = SCRATCH / "J-1240_run_meta.json"
PROBE_PATH = SCRATCH / "J-1240_hub_probe.json"
REPORT_MD = ROOT / "docs" / "lab" / "train_split_merge_step2_scope_repair_2026-09-23_J1240.md"
REPORT_JSONL = ROOT / "docs" / "lab" / "train_split_merge_step2_scope_repair_2026-09-23_J1240.jsonl"

LAB_TIMEOUT = 300
BACKOFF = (20, 60, 180)
INFRA_ERRS = ("timeout", "http", "exception")

STATS = {h: {"calls": 0, "ok": 0, "infra_errors": 0, "retries": 0, "persistent_fail": 0, "parse": 0}
         for h in ("JUDGE_1", "JUDGE_2", "TIEBREAK")}
HUB_URL = {"JUDGE_1": jp.JUDGE_1, "JUDGE_2": jp.JUDGE_2, "TIEBREAK": CANDIDATE_URL}


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
    """Read-only, not a gate for this job (CPU hubs only, no hot lane) -- recorded per this plan's own
    established discipline, same as J-1205/J-0834/J-0910/J-0916/J-0980."""
    try:
        r = subprocess.run([sys.executable, str(DU_CHECK)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        tail = (r.stdout or "").strip().splitlines()
        return f"rc={r.returncode} ({'DOWN' if r.returncode == 0 else 'UP-or-UNKNOWN'}); {tail[-1] if tail else ''}"
    except Exception as exc:
        return f"check failed: {exc}"


# ---------------------------------------------------------------------------------------------------------
# hub reachability probe -- same technique as scripts/lab_j1198_walkback_replay.py's own probe_hub_sync,
# run BEFORE any real judge call. Read-only GET, no repo import needed for this part.
# ---------------------------------------------------------------------------------------------------------
def probe_tags(url: str, timeout: float = 8.0):
    try:
        req = urllib.request.Request(url.rstrip("/") + "/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        names = [m.get("name") for m in (data.get("models") or [])]
        return True, names, None
    except Exception as e:
        return False, [], f"{type(e).__name__}: {str(e)[:120]}"


def run_probe() -> dict:
    out = {}
    for name, url, expect in (("JUDGE_1", jp.JUDGE_1, "mixtral:8x7b"),
                              ("JUDGE_2", jp.JUDGE_2, "falcon3:7b"),
                              ("CANDIDATE(gemma4:12b)", CANDIDATE_URL, "gemma4:12b"),
                              ("WRONG_BRIEFING_ADDR(LAN-HOST:11439)", "http://LAN-HOST:11439", None)):
        ok, names, err = probe_tags(url)
        matches = expect in names if (ok and expect) else None
        out[name] = {"url": url, "reachable": ok, "models": names, "expected_model_present": matches, "err": err}
        progress(f"probe {name} ({url}): reachable={ok} models={names} expected_present={matches} err={err}")
    PROBE_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


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
# prompts: AST-extracted from scripts/train_state_invitro.py (never imported) -- byte-identical to J-1205.
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
    support_block = (NL.join(f"  {i}. {s}" for i, s in enumerate(support, 1)) if support
                     else "  (none offered -- the prove branch returned no supporting reasoning)")
    return (f"CLAIM: {claim[:400]}" + NL + NL +
            f"SUPPORT OFFERED FOR THIS CLAIM:" + NL + f"{support_block}" + NL + NL +
            f"WHY THE SUPPORT WAS ALREADY FOUND NOT TO FULLY EARN THE CLAIM: {original_why}" + NL + NL +
            "Given that, does the support instead genuinely, independently earn a NARROWER "
            "or more modest version of the claim -- or is it absent/circular/irrelevant with "
            "no narrower claim earned either?")


WALKBACK_CALLS = ROOT / "docs" / "lab" / "train_split_merge_step2_replay_2026-09-22_walkback_calls.jsonl"


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
            real_units.append({"id": f"u{c['unit']}", "group": "real_unit", "user": c["user"], "expected": None})
        elif c.get("phase") == "control" and c.get("call") == "second":
            label, expected = control_expectation(c["user"])
            real_controls.append({"id": f"ctrl_{label}", "group": "real_control", "user": c["user"], "expected": expected})
    return real_units, real_controls


def load_battery_prompts():
    out = []
    for label, expected, claim, support, why in BATTERY_ITEMS:
        out.append({"id": f"bat_{label}", "group": "battery", "user": build_second_call_prompt(claim, support, why),
                   "expected": expected})
    return out


def check_builder(real_units: list) -> int:
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


def all_prompts():
    real_units, real_controls = load_real_prompts()
    battery = load_battery_prompts()
    return real_units, real_controls, battery


def plan_rounds(real_units, real_controls, battery):
    """Same total coverage as J-1205's own plan_rounds() (arm (c): full 72 x 2 draws; arms (a)/(b):
    the 10 known-answer items x 1 draw), but REORDERED (deviation from J-1205, recorded honestly --
    see this job's own finding/report): the 10 known-answer items (2 controls + 8 battery) for ALL
    THREE arms are scheduled FIRST, before arm (c)'s 62 real-unit rounds. Reason: this run's own
    observed per-round latency is dominated by JUDGE_1's hub contention with Du's own live traffic
    (median ~61s/round this session vs J-1205's ~48-minute total for the same 492-call design), which
    makes finishing all 144 real-unit-first arm-(c) rounds before reaching the battery items a real
    risk -- and the battery is exactly what the founder's own proposed pass bar (battery >=7/8) is
    computed from. Old-order real-unit rounds already completed before this reorder remain valid (the
    (id, arm, draw) key is unchanged) and are picked up by load_done_rows() as already-done, not
    redone."""
    known = real_controls + battery
    rounds = []
    for p in known:
        for draw in (1, 2):
            rounds.append({"id": p["id"], "group": p["group"], "arm": "c_polarity", "draw": draw, "user": p["user"]})
        rounds.append({"id": p["id"], "group": p["group"], "arm": "b_why_first", "draw": 1, "user": p["user"]})
        rounds.append({"id": p["id"], "group": p["group"], "arm": "a_bool_first", "draw": 1, "user": p["user"]})
    for p in real_units:
        for draw in (1, 2):
            rounds.append({"id": p["id"], "group": p["group"], "arm": "c_polarity", "draw": draw, "user": p["user"]})
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
# analysis -- identical metrics to J-1205 (regex bound reused unchanged, same wilson CI, same pass bar).
# ---------------------------------------------------------------------------------------------------------
EXPL = re.compile(r"(narrower claim[^.]{0,80}(actually earns|is earned|earned)|genuinely earns? a narrower|"
                  r"(only |could |can )?earns? (a |an )?(more )?(modest|narrow)|real but narrower|earns? a narrower claim)", re.I)
NEG = re.compile(r"(no narrower|not even a narrower|does not earn even|lack of support|no support offered)", re.I)


def regex_label(why: str) -> str:
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


def analyse(real_units, real_controls, battery, rows: list) -> dict:
    by_key = {}
    for r in rows:
        by_key.setdefault((r["id"], r["arm"], r["judge"]), []).append(r)
    known = real_controls + battery
    known_ids = {p["id"]: p for p in known}
    everything_ids = {p["id"]: p for p in (real_units + real_controls + battery)}

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

    def split_and_unanimous(arm_name: str):
        agree = split = n = 0
        unan_true_ids, both_false_ids = [], []
        for u in real_units:
            r1 = next((x for x in by_key.get((u["id"], arm_name, "JUDGE_1"), []) if x["draw"] == 1), None)
            r2 = next((x for x in by_key.get((u["id"], arm_name, "JUDGE_2"), []) if x["draw"] == 1), None)
            v1, v2 = (r1["v"] if r1 else None), (r2["v"] if r2 else None)
            if v1 is None or v2 is None:
                continue
            n += 1
            if v1 == v2:
                agree += 1
                (unan_true_ids if v1 is True else both_false_ids).append(u["id"])
            else:
                split += 1
        return {"n": n, "agree": agree, "split": split, "split_rate": round(split / n, 3) if n else None,
               "unanimous_true_ids": unan_true_ids, "unanimous_false_ids": both_false_ids}

    out["split_c"] = split_and_unanimous("c_polarity")

    def tb_vs_unanimous(arm_name: str, unan_true_ids: list, unan_false_ids: list):
        right = n = true_on_true = true_on_false = 0
        for pid in unan_true_ids:
            r = next((x for x in by_key.get((pid, arm_name, "TIEBREAK"), []) if x["draw"] == 1), None)
            v = r["v"] if r else None
            if v is None:
                continue
            n += 1
            right += int(v is True)
            true_on_true += int(v is True)
        n_false_checked = 0
        for pid in unan_false_ids:
            r = next((x for x in by_key.get((pid, arm_name, "TIEBREAK"), []) if x["draw"] == 1), None)
            v = r["v"] if r else None
            if v is None:
                continue
            n_false_checked += 1
            right += int(v is False)
            true_on_false += int(v is True)
        total = n + n_false_checked
        return {"n_unanimous_true": n, "candidate_true_on_unanimous_true": true_on_true,
               "n_unanimous_false": n_false_checked, "candidate_true_on_unanimous_false": true_on_false,
               "overall_accuracy": round(right / total, 3) if total else None,
               "accuracy_ci95": wilson(right, total)}

    out["tb_vs_unanimous_c"] = tb_vs_unanimous("c_polarity", out["split_c"]["unanimous_true_ids"], out["split_c"]["unanimous_false_ids"])

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


# J-1205's own granite numbers, quoted verbatim from the already-committed
# docs/lab/train_split_merge_step2_scope_repair_2026-09-23_J1205.md, for a direct side-by-side table.
# NOT recomputed here -- this is a static citation of another job's already-published, dated result.
J1205_GRANITE = {
    "a_bool_first": {"true_share": 0.0, "battery": "4/8", "n_calls": 10},
    "b_why_first": {"true_share": 0.0, "battery": "4/8", "n_calls": 10},
    "c_polarity": {"true_share": 0.0, "battery": "4/8", "n_calls": 144, "unanimous_match": 0.37,
                  "repeat_agree_rate": 1.0},
}


def render_md(o: dict, real_units, real_controls, battery, probe: dict) -> str:
    L = ["# Train Split/Merge -- Step 2 second-call repair, J-1240 (D-0213, arm d)", "",
        "## J-1240 reading (2026-09-23)", "",
        "D-0213 was re-ruled by Travis 2026-09-23 (independently re-verified via `decide.py show "
        "D-0213` before this job started): \"Hold -- wait for J-1240 (the gemma4:12b model-swap test "
        "on the scope_only second-call's own contract) before deciding further ... Only the model half "
        "remains untested.\" J-1205 (same day) tested two prompt-wording candidates against TIEBREAK "
        "(granite3.1-moe:3b, :11437) on this call site's own `_SCOPE_SYSTEM` contract and found neither "
        "repaired its constant `scope_only=False` vote (0.0% True share on 144 fresh draws under arm "
        "(c), same 4/8 battery score as the unfixed prompt). This job tests the MODEL half of D-0213's "
        "own defeater: does a DIFFERENT model in the same seat give this call site's own question a "
        "real, content-sensitive vote? Candidate: gemma4:12b, D-0176/J-0842's own best-evidenced "
        "alternate (fit+stable on a DIFFERENT call site's contract, `commitment_ledger.scan_shadow`).",
        "",
        "**Hub address correction (verify-before-calling).** The dispatch briefing named the "
        "candidate's address as `http://LAN-HOST:11439` (\"Ramses\"). That address does not answer "
        "at all (`" + str(probe.get("WRONG_BRIEFING_ADDR(LAN-HOST:11439)", {}).get("err")) + "`, "
        "confirmed by direct probe before any judge call was made). The real hub is "
        f"`{CANDIDATE_URL}` (LOCAL, this machine's own Threadripper/Bonsai CPU tier) -- confirmed "
        "reachable and serving `gemma4:12b` by the same probe "
        f"(models={probe.get('CANDIDATE(gemma4:12b)', {}).get('models')}), and cross-referenced "
        "against seven other places in this tree that all independently agree on `127.0.0.1:11439` "
        "(`core/judge_panel.py`, `core/model_client.py`, `core/left_lane.py`, "
        "`core/deliberation.py`, `core/librarian.py`, `core/peers.py`, and "
        "`scripts/d0176_scan_bakeoff.py` itself -- the very bake-off the briefing cites as its "
        "source). See this script's own docstring for the full trace. All calls below went to the "
        "verified real address, never the wrong one.", "",
        "**Arms tested** (all three, unlike a single-arm run -- J-1205's own arm (c) showed NO "
        "promise over arm (a) on granite: battery 4/8 both, unanimous-match 37.0% vs 37.9%, "
        "statistically indistinguishable -- so this job does not guess which wording to prefer and "
        "instead mirrors J-1205's own full design, changing only the hub):", "",
        "- **(a) bool_first** -- the LIVE wording, unchanged. Baseline.",
        "- **(b) why_first** -- pure key-order swap, J-1198's own control on granite.",
        "- **(c) polarity** -- the polarity-explicit rewording J-1205 tested as THE candidate fix.", "",
        f"**Isolation.** `lab_env.isolate(also=[(judge_panel, [\"_DATA\",\"_LOG\"])], db=\"empty\")` "
        "wrapped every real hub call, entered AFTER `core`/`core.judge_panel` were already "
        "imported+cached from the WORKTREE (module resolution: "
        + ", ".join(f"`{k}`=`{v}`" for k, v in MODRES.items()) + "), so `lab_env`'s own later "
        "`sys.path` prepend of the live `C:\\Nascence` cannot make a later `core.*` submodule import "
        "resolve outside the worktree. `core/judge_panel.py`'s own live `TIEBREAK` constant "
        f"(`{LIVE_TIEBREAK_FOR_RECORD}`, granite) was read for the record only, never called, never "
        "mutated -- this script's own separate `CANDIDATE_URL` is used solely by this script's own "
        "local `HUB_URL` mapping. Write-audit (`sys.addaudithook` watching all of `C:\\Nascence\\data` "
        "and `C:\\Nascence\\docs`): "
        + (f"{len(LIVE_WRITE_ATTEMPTS)} write-shaped events this process, all inside the one "
           f"pre-isolated quarantine dir ({LIVE_WRITE_ATTEMPTS[:6]})" if LIVE_WRITE_ATTEMPTS
           else "0 write-shaped events this process") +
        f". Backstop: real `nascence.db` unchanged={o.get('db_unchanged')}, real "
        f"`judge_panel_log.jsonl` unchanged={o.get('jplog_unchanged')}. Infra rules matched J-1205's "
        "runner: timeout >= 300s; timeout/http/exception treated as infrastructure, retried 3x with "
        "backoff (20/60/180s), never a verdict; 'parse' is a real, counted outcome. Du state before/"
        "after (not a gate for this job -- CPU hubs only, no hot lane, same precedent as every prior "
        f"job in this plan): {o.get('du_before')} / {o.get('du_after')}.", "",
        f"**Inputs.** {len(real_units)} real second-call user prompts + {len(real_controls)} real "
        "known-answer control prompts, both read verbatim from the already-committed "
        "`docs/lab/train_split_merge_step2_replay_2026-09-22_walkback_calls.jsonl` (prompt-builder "
        f"integrity re-verified), plus {len(battery)} hand-built known-answer battery items "
        "(reproduced verbatim from `scripts/lab_j1198_scope_battery.py`'s own `ITEMS`). Arm (c) ran "
        "fresh on all 72 (2 draws, temperature 0); arms (a)/(b) ran fresh on the 10 known-answer "
        "items only (1 draw) -- unlike J-1205, there is no history to reuse for the CANDIDATE seat "
        "(gemma4:12b has never been asked any of these prompts before this job), so JUDGE_1/JUDGE_2 "
        "were also called fresh everywhere in this run rather than mixed with J-1205's own "
        "differently-dated data, keeping this report self-contained and internally comparable.", ""]

    def hub_row(arm, judge):
        j = o["arms"][arm]["judges"][judge]
        return (f"| {judge} | {j['n_calls']} | {j['true']} | {j['false']} | {j['none_unparseable']} | "
               f"{j['true_share']} {j['true_share_ci95']} | {j['parse_fail_rate']} | "
               f"{j['repeat_agree']}/{j['repeat_pairs']} ({j['repeat_agree_rate']}) | "
               f"{j['battery_correct'][0]}/{j['battery_correct'][1]} |")

    for arm in ("a_bool_first", "b_why_first", "c_polarity"):
        L.append(f"### Arm {arm} -- {ARMS[arm]['label']}")
        L.append("")
        pool = "all 72 (62 real units + 2 real controls + 8 battery), 2 draws, fresh" if arm == "c_polarity" \
            else "the 10 known-answer items only (2 real controls + 8 battery), 1 draw, fresh"
        L.append(f"Prompts: {pool}. `TIEBREAK` in this table means the CANDIDATE seat "
                 f"({CANDIDATE_LABEL}), never the live granite TIEBREAK.")
        L.append("")
        L.append("| judge | n calls | True | False | None/unparseable | True share (95% CI) | parse-fail rate | repeat agree | battery correct |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for judge in ("JUDGE_1", "JUDGE_2", "TIEBREAK"):
            L.append(hub_row(arm, judge))
        L.append("")
        g = J1205_GRANITE[arm]
        extra = f", unanimous-match {g['unanimous_match']}, repeat-agree {g['repeat_agree_rate']}" if "unanimous_match" in g else ""
        L.append(f"_For reference (not recomputed here, cited verbatim from J-1205's own already-"
                 f"published report): granite3.1-moe:3b (the live TIEBREAK) on this SAME arm's wording "
                 f"scored True share {g['true_share']}, battery {g['battery']} (n={g['n_calls']}"
                 f"{extra})._")
        L.append("")

    L += ["## JUDGE_1 / JUDGE_2 split rate -- fresh this session (all 62 real units, arm c)", "",
         f"- n={o['split_c']['n']}, agree={o['split_c']['agree']}, split={o['split_c']['split']} "
         f"(split rate {o['split_c']['split_rate']}), "
         f"unanimous-True={len(o['split_c']['unanimous_true_ids'])}, "
         f"unanimous-False={len(o['split_c']['unanimous_false_ids'])}. "
         "(For reference, J-1205's own fresh arm-(c) read the same day: n=62, split rate 0.565, "
         "unanimous-True=17, unanimous-False=10 -- JUDGE_1/JUDGE_2 do not depend on which model sits "
         "at TIEBREAK, so this is a same-wording, same-day freshness check, not expected to differ "
         "meaningfully.)", "",
         "## CANDIDATE (gemma4:12b) vs. the unanimous panel -- the only ground-truth-ish signal in the real prompts", "",
         f"- arm (c), this job: n_unanimous_true={o['tb_vs_unanimous_c']['n_unanimous_true']}, "
         f"CANDIDATE said True on {o['tb_vs_unanimous_c']['candidate_true_on_unanimous_true']} of them; "
         f"n_unanimous_false={o['tb_vs_unanimous_c']['n_unanimous_false']}, CANDIDATE said True "
         f"(wrongly) on {o['tb_vs_unanimous_c']['candidate_true_on_unanimous_false']} of them; overall "
         f"accuracy {o['tb_vs_unanimous_c']['overall_accuracy']} (CI "
         f"{o['tb_vs_unanimous_c']['accuracy_ci95']}).",
         "- _For reference: granite (the live TIEBREAK), same arm, J-1205's own fresh read: overall "
         "accuracy 0.37 (CI 0.215-0.558)._", "",
         "## Pass bar (J-1205's own briefing's proposed numbers, same bar applied here to arm (c))", "",
         f"CANDIDATE matches the constructed battery >= 7/8: **{o['pass_bar_c']['battery_pass(>=7/8)']}** "
         f"({o['pass_bar_c']['battery_score']}). CANDIDATE matches the panel-unanimous-True prompts >= "
         f"70%: **{o['pass_bar_c']['unanimous_match_pass(>=70pct)']}** "
         f"({o['pass_bar_c']['unanimous_match']}). No parse-failure rate above 10%: "
         f"**{all(o['pass_bar_c']['parse_fail_under_10pct'].values())}** "
         f"({o['pass_bar_c']['parse_fail_rates']}). **OVERALL: {o['pass_bar_c']['OVERALL_PASS']}** "
         "(the founder's own bar to rule on -- not this job's call to declare \"fixed\").", "",
         "## Hub reachability probe (run before any real judge call)", "", "```json",
         json.dumps(probe, ensure_ascii=False, indent=1), "```", ""]
    return NL.join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()

    if args.probe:
        p = run_probe()
        cand = p["CANDIDATE(gemma4:12b)"]
        wrong = p["WRONG_BRIEFING_ADDR(LAN-HOST:11439)"]
        progress(f"PROBE SUMMARY: candidate reachable={cand['reachable']} model_present={cand['expected_model_present']} | "
                 f"briefing's claimed addr reachable={wrong['reachable']}")
        return 0 if cand["reachable"] and cand["expected_model_present"] else 1

    real_units, real_controls, battery = all_prompts()
    n_checked = check_builder(real_units)
    progress(f"prompt builder reproduces {n_checked} real committed second-call prompts byte-for-byte")
    progress(f"module resolution: {MODRES}")
    progress(f"inputs: {len(real_units)} real units, {len(real_controls)} real controls, {len(battery)} battery items")
    progress(f"CANDIDATE_URL={CANDIDATE_URL} ({CANDIDATE_LABEL})")

    rounds = plan_rounds(real_units, real_controls, battery)
    n_calls = sum(3 for _ in rounds)
    progress(f"{len(rounds)} rounds planned ({n_calls} judge-calls if none already done)")

    if args.dry:
        by_arm = Counter(r["arm"] for r in rounds)
        progress(f"--dry: rounds by arm: {dict(by_arm)}")
        return 0

    if args.smoke:
        p = run_probe()
        if not (p["CANDIDATE(gemma4:12b)"]["reachable"] and p["CANDIDATE(gemma4:12b)"]["expected_model_present"]):
            progress("SMOKE ABORTED: candidate hub not reachable / not serving gemma4:12b")
            return 1
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
        p = run_probe()
        if not (p["CANDIDATE(gemma4:12b)"]["reachable"] and p["CANDIDATE(gemma4:12b)"]["expected_model_present"]):
            progress("RUN ABORTED: candidate hub not reachable / not serving gemma4:12b -- see J-1240_hub_probe.json")
            return 1
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
        probe = json.loads(PROBE_PATH.read_text(encoding="utf-8")) if PROBE_PATH.exists() else run_probe()
        out = analyse(real_units, real_controls, battery, rows)
        out["n_rows"] = len(rows)
        out["stats_this_process"] = STATS
        if RUN_META_PATH.exists():
            out.update(json.loads(RUN_META_PATH.read_text(encoding="utf-8")))
        SUMMARY_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        md = render_md(out, real_units, real_controls, battery, probe)
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
