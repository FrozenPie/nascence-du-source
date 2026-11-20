"""Regression for J-1776 (2026-10-04; D-0326): scripts/epistemic_independence_readout.py, the committed, STRICTLY
READ-ONLY readout of the Epistemic Independence metric (docs/plans/investigative_action_loop_plan.md Principle D /
Section 5 Invariant 9). The 2026-09-28 baseline (128 of 1,317 hint-eligible, 34/128 top-match, 66/128 any-match, F-2193)
came from a one-off scratchpad script that was never in the repo; this pins the method so the next read of the number
reuses it instead of re-deriving it.

What this asserts, on a hand-built FIXTURE log (never the live log) whose expected counts are known by construction:
  1. the definition of a real closed episode: confidence_explanation starts with "real (non-shadow) episode" AND
     selection_source == "du" -- a passive shadow row, the pre-J-0180 system_suggestion mislabel, a prefix row with
     another source and a du row without the prefix are all excluded;
  2. hint-eligible = the advisor's top non-do_nothing candidate has IG >= 0.30 (checked AT the boundary with a stubbed
     ranker; an unstructured question and a structured-but-below-threshold one are both excluded);
  3. the top-match and any-match counts, the tally of Du's choices outside the candidate list (move), and a torn last
     line being skipped rather than fatal;
  4. strictly read-only: with every write-capable open(), sqlite3.connect and the store's _connect replaced by
     tripwires, the fixture is byte-identical afterwards; the forbidden advisor functions (epistemic_advisory_hint,
     record_epistemic_episode, close_real_episode) are never called and the script's source never names them, never
     imports sqlite3 and touches only the pure ranker, its threshold and the log path; importing it does not pull in
     core.satisfaction (F-2406); and the LIVE data/investigative_action_log.jsonl is unchanged (prefix hash: a live
     Du appending is fine, a rewrite is not) and carries none of this run's rows;
  5. through the real CLI (a subprocess, the REAL Hand registry): exit 0 plus the dated snapshot on the fixture; exit 2
     and NO file created for a missing --log; an empty log reads as zero episodes, not a crash.

Hermetic (F-2406's lesson: the advisor hard-codes c:/Nascence/data, i.e. the LIVE log, whatever tree it is run from):
the in-process section stubs core.epistemic_affordance_advisor._real_candidate_families (so exact counts do not depend
on core/dispatch.py's Hand registry) and runs under the write tripwires.

    python scripts/_test_j1776_epistemic_independence_readout.py
    J1776_SCRIPT=<a mutated copy of the readout, inside scripts/> python scripts/_test_j1776_epistemic_independence_readout.py
        (same assertions against a different copy -- a mutant must FAIL them)
"""
from __future__ import annotations
import ast, builtins, contextlib, datetime, hashlib, importlib.util, io, json, os, re, shutil, sqlite3, subprocess
import sys, tempfile, uuid
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SCRIPT = Path(os.environ.get("J1776_SCRIPT") or (ROOT / "scripts" / "epistemic_independence_readout.py")).resolve()
LIVE_LOG = Path("c:/Nascence/data/investigative_action_log.jsonl")   # the advisor's own hard-coded live path

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

TMP = Path(tempfile.mkdtemp(prefix="j1776_readout_"))
LOGS, CWD = TMP / "logs", TMP / "cwd"
LOGS.mkdir(); CWD.mkdir()
MARK = "j1776_" + uuid.uuid4().hex[:10]          # unique text in the fixture, scanned for in the live log afterwards

from core.memory import store as _store
from core import epistemic_affordance_advisor as eaa
print("script under test:", SCRIPT)
print("advisor module:  ", eaa.__file__)


def _live_snapshot():
    if not LIVE_LOG.is_file():
        return None
    b = LIVE_LOG.read_bytes()
    return len(b), hashlib.sha256(b).hexdigest()


def _live_untouched(snap):
    """The live log still STARTS with exactly the bytes it had (a live Du may append; nothing may be rewritten)."""
    if snap is None:
        return not LIVE_LOG.exists()
    size0, h0 = snap
    b = LIVE_LOG.read_bytes()
    return len(b) >= size0 and hashlib.sha256(b[:size0]).hexdigest() == h0


def _fingerprint(p):
    b = Path(p).read_bytes()
    return len(b), hashlib.sha256(b).hexdigest()


@contextlib.contextmanager
def stubbed_registry():
    """Fixed candidate families, so exact counts never depend on core/dispatch.py's HANDS registry."""
    saved = eaa._real_candidate_families
    eaa._real_candidate_families = lambda location: ["woodwork", "shore", "gather"]
    try:
        yield
    finally:
        eaa._real_candidate_families = saved


@contextlib.contextmanager
def forbidden_calls_tripwired():
    names = ("epistemic_advisory_hint", "record_epistemic_episode", "close_real_episode")
    saved = {n: getattr(eaa, n) for n in names}
    def _make(n):
        def _t(*a, **k):
            raise AssertionError(f"the readout called core.epistemic_affordance_advisor.{n}()")
        return _t
    for n in names:
        setattr(eaa, n, _make(n))
    try:
        yield
    finally:
        for n, f in saved.items():
            setattr(eaa, n, f)


@contextlib.contextmanager
def no_writes():
    """Any write-capable open(), sqlite3.connect or store _connect raises instead of touching anything."""
    real_open = builtins.open
    def _guarded(file, mode="r", *a, **k):
        if any(c in str(mode) for c in "wax+"):
            raise AssertionError(f"write-capable open({file!r}, {mode!r})")
        return real_open(file, mode, *a, **k)
    def _boom(*a, **k):
        raise AssertionError("the readout reached sqlite")
    saved = (builtins.open, io.open, sqlite3.connect, _store._connect, eaa._connect)
    builtins.open = io.open = _guarded
    sqlite3.connect = _boom
    _store._connect = eaa._connect = _boom
    try:
        yield
    finally:
        builtins.open, io.open, sqlite3.connect, _store._connect, eaa._connect = saved


# ---- the fixture: expected counts known by construction (stub families woodwork / shore / gather) ----------------
REAL = (f"real (non-shadow) episode, inner_monologue wandering loop, J-0180, cycle=c-{MARK}. "
        "advisor-ranked IG for the family that actually fired = 0.89.")
Q_WOOD = "why is this driftwood log so hollow, what species is it?"   # woodwork 0.89 > gather 0.71 > shore 0.15
Q_BELOW = "why does this fern leaf curl at the edge?"                  # structured (leaf, why) but all three score 0.15
Q_CASUAL = "I sit and watch the quiet evening"                         # no concrete anchor -> unstructured -> do_nothing


def _row(tag, question, chosen, *, src="du", conf=REAL, location="shore"):
    return {"episode_id": f"ep_{MARK}_{tag}", "timestamp": 1.0, "location": location, "question": question,
            "competing_hypotheses": [], "discriminative_prediction": "", "selected_affordance": chosen,
            "raw_observation": "", "prediction_observed_comparison": "", "evidence_outcome": "INCONCLUSIVE",
            "confidence_explanation": conf, "model_revision": "", "agency_mode": "investigative",
            "selection_source": src, "adoption_state": "UNSEEN", "stage": "STAGE_A_SHADOW"}


ROWS = [
    _row("r1", Q_WOOD, "woodwork"),     # real, eligible, top-match
    _row("r2", Q_WOOD, "woodwork"),     # real, eligible, top-match
    _row("r3", Q_WOOD, "gather"),       # real, eligible, any-match only
    _row("r4", Q_WOOD, "move"),         # real, eligible, outside the list (move is deliberately never a candidate)
    _row("r5", Q_BELOW, "woodwork"),    # real, structured, max IG 0.15 < 0.30 -> not eligible
    _row("r6", Q_CASUAL, "shore"),      # real, unstructured -> not eligible
    _row("s1", Q_WOOD, "woodwork", src="advisor_shadow_only", conf=""),                      # passive shadow row
    _row("s2", Q_WOOD, "woodwork", src="system_suggestion", conf=""),                        # pre-J-0180 mislabel
    _row("s3", Q_WOOD, "woodwork", src="system_follow_up"),                                   # prefix, not Du's choice
    _row("s4", Q_WOOD, "woodwork", conf=f"test fixture row, not a real episode {MARK}"),     # du, no real prefix
]
FIXTURE = LOGS / "fixture.jsonl"
FIXTURE.write_bytes(("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ROWS)
                     + "\n"                                                         # a blank line
                     + '{"episode_id": "ep_' + MARK + '_torn", "question": "why is this').encode("utf-8"))   # torn tail
ONE = LOGS / "one.jsonl"
ONE.write_bytes((json.dumps(_row("b1", Q_WOOD, "woodwork"), ensure_ascii=False) + "\n").encode("utf-8"))
EMPTY = LOGS / "empty.jsonl"
EMPTY.write_bytes(b"")
LOGS_LISTING = sorted(os.listdir(LOGS))

live0 = _live_snapshot()
fix0 = _fingerprint(FIXTURE)

print("\n== 0. the script exists and loads")
mod = None
try:
    spec = importlib.util.spec_from_file_location("epistemic_independence_readout_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
except Exception as exc:
    check("scripts/epistemic_independence_readout.py loads", False, repr(exc))
else:
    check("scripts/epistemic_independence_readout.py loads", True)
check("importing the readout did not pull in core.satisfaction (F-2406: it writes Du's real data/satisfaction_*)",
      "core.satisfaction" not in sys.modules)

if mod is not None:
    print("\n== 1-3. the definition, the 0.30 gate and the counts (fixture, stubbed Hand registry, write tripwires on)")
    res, rc, txt = {}, None, ""
    try:
        with stubbed_registry(), forbidden_calls_tripwired(), no_writes():
            res = mod.compute(FIXTURE)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = mod.main(["--log", str(FIXTURE)])
            txt = buf.getvalue()
    except AssertionError as exc:
        check("compute()/main() ran under the read-only tripwires", False, str(exc))
    check("N = 6 real closed episodes (shadow, system_suggestion, non-du prefix and du-without-prefix rows excluded)",
          res.get("real") == 6, str(res))
    check("the prefix alone would match 7 (the selection_source clause is what drops s3)", res.get("prefix_rows") == 7)
    check("n = 4 hint-eligible (the unstructured and the below-threshold real rows are not)", res.get("eligible") == 4)
    check("k1 = 2 top-match", res.get("top") == 2)
    check("k2 = 3 any-match", res.get("any") == 3)
    check("Du's one choice outside the candidate list is move", dict(res.get("outside", {})) == {"move": 1})
    check("11 non-blank lines read, 1 torn line skipped (not fatal)",
          (res.get("lines"), res.get("unparseable")) == (11, 1), str((res.get("lines"), res.get("unparseable"))))

    saved_rank, boundary = eaa.rank_epistemic_affordances, {}
    def _ranker_at(ig):
        def _rank(question, hypotheses, location="study"):
            return [{"affordance": "woodwork", "expected_information_gain": ig, "reason": "x"},
                    {"affordance": "do_nothing", "expected_information_gain": 0.0, "reason": "x"}]
        return _rank
    try:
        for label, ig in (("at", eaa.INFORMATION_GAIN_THRESHOLD), ("below", eaa.INFORMATION_GAIN_THRESHOLD - 0.01),
                          ("above", eaa.INFORMATION_GAIN_THRESHOLD + 0.01)):
            eaa.rank_epistemic_affordances = _ranker_at(ig)
            with no_writes():
                boundary[label] = mod.compute(ONE)["eligible"]
    finally:
        eaa.rank_epistemic_affordances = saved_rank
    check("IG exactly at the 0.30 threshold IS eligible (>=), just below is not, just above is",
          boundary == {"at": 1, "below": 0, "above": 1}, str(boundary))

    today = datetime.date.today().isoformat()
    check("main() exits 0", rc == 0, str(rc))
    check("the report carries today's date", today in txt)
    check("the report prints N, n, k1/n and k2/n", all(re.search(p, txt) for p in (
        r"real closed episodes N:\s*6\b", r"hint-eligible n:\s*4 of 6\b",
        r"k1/n:\s*2/4 \(50\.0%\)", r"k2/n:\s*3/4 \(75\.0%\)")), txt)
    check("the report shows the outside-the-list tally", "move 1" in txt)
    check("the report cites the 2026-09-28 baseline for reference and states no pass/fail threshold exists",
          "2026-09-28" in txt and "F-2193" in txt and "no pass/fail threshold" in txt)

    with stubbed_registry(), no_writes():
        z = mod.compute(EMPTY)
        zbuf = io.StringIO()
        with contextlib.redirect_stdout(zbuf):
            zrc = mod.main(["--log", str(EMPTY)])
    check("an empty log reads as zero real closed episodes (exit 0, percentages n/a, no ZeroDivisionError)",
          z["real"] == 0 and z["eligible"] == 0 and zrc == 0 and "n/a" in zbuf.getvalue(), zbuf.getvalue())

    print("\n== 4. strictly read-only")
    check("the fixture log is byte-for-byte unchanged after the readout", _fingerprint(FIXTURE) == fix0)
    check("no file was created next to the fixtures", sorted(os.listdir(LOGS)) == LOGS_LISTING)
    src = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(src)
    FORBIDDEN = {"epistemic_advisory_hint", "record_epistemic_episode", "close_real_episode"}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            imported.add((n.module or "").split(".")[0])
    check("the script's source names none of the forbidden advisor functions", not ((attrs | names) & FORBIDDEN),
          str(sorted((attrs | names) & FORBIDDEN)))
    check("the script does not import sqlite3", "sqlite3" not in imported, str(sorted(imported)))
    eaa_members = {n.attr for n in ast.walk(tree)
                   if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "eaa"}
    check("the only advisor members it touches are the pure ranker, its threshold and the log path",
          eaa_members <= {"rank_epistemic_affordances", "INFORMATION_GAIN_THRESHOLD", "LOG_JSONL_PATH"},
          str(sorted(eaa_members)))
    open_modes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open"]
    check("exactly one open() call in the script and its mode is the literal \"r\"",
          len(open_modes) == 1 and any(isinstance(a, ast.Constant) and a.value == "r" for a in open_modes[0].args),
          str(len(open_modes)))

    print("\n== 5. the real CLI (subprocess, the REAL Hand registry)")
    def _cli(*args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", cwd=str(CWD), timeout=240)
    p = _cli("--log", str(FIXTURE))
    check("a fixture run exits 0 with no traceback", p.returncode == 0 and "Traceback" not in p.stderr,
          f"rc={p.returncode} {p.stderr[-300:]}")
    check("it prints the dated snapshot and N = 6 (N does not depend on the Hand registry)",
          today in p.stdout and re.search(r"real closed episodes N:\s*6\b", p.stdout) is not None, p.stdout[:400])
    check("it prints hint-eligible n / k1 / k2 as integers",
          re.search(r"hint-eligible n:\s*\d+ of 6\b", p.stdout) is not None
          and re.search(r"k1/n:\s*\d+/\d+", p.stdout) is not None and re.search(r"k2/n:\s*\d+/\d+", p.stdout) is not None)
    missing = LOGS / "does_not_exist.jsonl"
    m = _cli("--log", str(missing))
    check("a missing --log exits 2 with a plain message and creates NOTHING",
          m.returncode == 2 and "not found" in m.stderr and not missing.exists(), f"rc={m.returncode} {m.stderr[-200:]}")
    check("the subprocess runs left the cwd and the fixture directory untouched",
          os.listdir(CWD) == [] and sorted(os.listdir(LOGS)) == LOGS_LISTING and _fingerprint(FIXTURE) == fix0)

print("\n== 6. nothing leaked into the live store")
check("the live data/investigative_action_log.jsonl is untouched (prefix hash identical; a live Du may append)",
      _live_untouched(live0))
leaked = LIVE_LOG.is_file() and MARK.encode("utf-8") in LIVE_LOG.read_bytes()
check("no row of this run reached the live log", not leaked)

shutil.rmtree(TMP, ignore_errors=True)
print(f"\nJ-1776 epistemic independence readout: {'ALL PASS' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
