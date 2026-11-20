"""Regression for J-1777 / F-2395 (2026-10-04; D-0326 stands: the 2026-08-14 no-hints law, nothing is ever shown):
a never-shown Stage-A shadow row must not claim adoption_state PRESENTED.

core/epistemic_affordance_advisor.py's InvestigativeEpisode.adoption_state defaulted to "PRESENTED", and
core/orchestrator.py's passive shadow call site (selection_source "advisor_shadow_only") never passes the field, so
every shadow-ranking row said a hint had been presented to Du (1,316 of 2,669 live rows) although nothing is ever
presented. The default is now "UNSEEN" -- the word close_real_episode() already writes explicitly for real closed
episodes. Rows written BEFORE the change keep PRESENTED: the log is an immutable raw record, and readers treat
selection_source in {advisor_shadow_only, system_suggestion} as "never shown" (plan doc Section 5, Invariant 3).
RESTART-GATED: Du picks this up at his next boot.

What this asserts: (1) the dataclass default, taxonomy intact; (2) the orchestrator's REAL shadow call expression --
evaluated from core/orchestrator.py's own source, not re-typed here -- yields UNSEEN, and no InvestigativeEpisode
call anywhere in the repo passes an explicit adoption_state other than UNSEEN; (3) through the real writer
record_epistemic_episode(): the shadow row and a real close_real_episode() row both land UNSEEN in the JSONL and in
the SQLite projection, while pre-existing PRESENTED history rows stay byte-for-byte untouched; (4) the law's
enforcement is untouched: epistemic_advisory_hint() still has zero call sites.

Hermetic (F-2406's lesson: this module hard-codes c:/Nascence/data, i.e. the LIVE log, whatever tree it is run from):
LOG_JSONL_PATH and the module's _connect are redirected into a temp dir; core.memory.store._connect is replaced by a
tripwire BEFORE the advisor is imported, so any path that would reach the real store raises instead of writing; the
live log is then scanned for this run's unique marker (immune to Du appending his own rows if he is running).

    python scripts/_test_j1777_adoption_state_label.py
    J1777_MODULE=<path to another epistemic_affordance_advisor.py> python scripts/_test_j1777_adoption_state_label.py
        (same assertions against a different copy of the module -- e.g. HEAD's pre-J-1777 file -- to show the
         UNSEEN cases FAIL without the change)
"""
from __future__ import annotations
import ast, importlib.util, json, os, shutil, sqlite3, sys, tempfile, time, uuid
from dataclasses import asdict
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

TMP = Path(tempfile.mkdtemp(prefix="j1777_adoption_label_"))
MARK = "j1777_" + uuid.uuid4().hex[:10]          # unique text in every row this run writes
LIVE_LOG = Path("c:/Nascence/data/investigative_action_log.jsonl")   # the module's own hard-coded live path

# Tripwire + redirect BEFORE the advisor is imported (it does `from core.memory.store import _connect`).
from core.memory import store as _store
_store.DB_PATH = TMP / "nascence.db"              # never connected to; belt and braces
def _tripwire(*a, **k):
    raise AssertionError("J-1777 test: the REAL core.memory.store._connect was reached")
_store._connect = _tripwire

_alt = os.environ.get("J1777_MODULE")
if _alt:
    import core  # noqa: F401  (package first, so the alt file's own `from core...` imports resolve)
    _spec = importlib.util.spec_from_file_location("core.epistemic_affordance_advisor", _alt)
    eaa = importlib.util.module_from_spec(_spec)
    sys.modules["core.epistemic_affordance_advisor"] = eaa
    _spec.loader.exec_module(eaa)
else:
    from core import epistemic_affordance_advisor as eaa
print("module under test:", eaa.__file__)

eaa.LOG_JSONL_PATH = TMP / "investigative_action_log.jsonl"
_CONNS = []
def _tmp_connect():
    c = sqlite3.connect(str(TMP / "projection.db")); _CONNS.append(c); return c
eaa._connect = _tmp_connect
eaa._real_candidate_families = lambda location: ["woodwork", "shore", "gather"]   # no core.dispatch import


def _call_name(n):
    f = n.func
    return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)


def _py_files():
    for sub in ("core", "nodes", "scripts", "hud"):
        yield from (ROOT / sub).rglob("*.py")
    yield from ROOT.glob("*.py")


print("\n== 1. the dataclass default")
fld = eaa.InvestigativeEpisode.__dataclass_fields__["adoption_state"]
check("InvestigativeEpisode.adoption_state defaults to UNSEEN", fld.default == "UNSEEN", f"default={fld.default!r}")
check("the 5-state taxonomy is untouched (PRESENTED/CONSIDERED/ADOPTED/REJECTED still legal explicit values)",
      all(s in str(fld.type) for s in ("UNSEEN", "PRESENTED", "CONSIDERED", "ADOPTED", "REJECTED")), str(fld.type))

print("\n== 2. the orchestrator's real shadow call site, and every other constructor")
tree = ast.parse((ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8"))
shadow = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and _call_name(n) == "InvestigativeEpisode"
          and any(k.arg == "selection_source" and isinstance(k.value, ast.Constant)
                  and k.value.value == "advisor_shadow_only" for k in n.keywords)]
check("core/orchestrator.py has exactly one advisor_shadow_only InvestigativeEpisode call site", len(shadow) == 1,
      f"found {len(shadow)}")
bad = []
for p in _py_files():
    if p.name == Path(__file__).name:
        continue
    try:
        src = p.read_text(encoding="utf-8")
        if "InvestigativeEpisode" not in src:
            continue
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.Call) and _call_name(n) == "InvestigativeEpisode":
                for k in n.keywords:
                    if k.arg == "adoption_state" and not (isinstance(k.value, ast.Constant) and k.value.value == "UNSEEN"):
                        bad.append(f"{p.relative_to(ROOT)}:{n.lineno}")
    except (OSError, SyntaxError, UnicodeDecodeError):
        continue
check("no InvestigativeEpisode(...) call in the repo passes an explicit adoption_state other than UNSEEN", not bad, str(bad))

shadow_ep = None
if len(shadow) == 1:
    expr = ast.Expression(body=shadow[0]); ast.fix_missing_locations(expr)
    ns = {"_eaa": eaa, "time": time, "_uuid": uuid, "_loc": "shore",
          "_raw_q": f"{MARK} why is this driftwood log so hollow?", "_h_list": ["a borer made it"],
          "_top": {"affordance": "woodwork", "reason": "Working the wood exposes grain.", "expected_information_gain": 0.53}}
    try:
        shadow_ep = eval(compile(expr, "core/orchestrator.py", "eval"), ns)   # the call exactly as run_cycle() runs it
    except Exception as exc:
        check("the orchestrator's shadow call expression evaluates (its free names are stubbed above)", False, repr(exc))
if shadow_ep is not None:
    check("the shadow episode the orchestrator builds says UNSEEN", shadow_ep.adoption_state == "UNSEEN",
          f"adoption_state={shadow_ep.adoption_state!r}")

print("\n== 3. the real writer: temp JSONL + temp SQLite projection, history untouched")
if shadow_ep is None:
    check("a shadow episode was built to write", False)
else:
    hist = []
    for src in ("advisor_shadow_only", "system_suggestion"):          # rows as the pre-J-1777 code wrote them
        d = asdict(shadow_ep); d.update(adoption_state="PRESENTED", selection_source=src, episode_id=f"ep_hist_{MARK}_{src}")
        hist.append(json.dumps(d, ensure_ascii=False) + "\n")
    eaa.LOG_JSONL_PATH.write_text("".join(hist), encoding="utf-8")
    seed = eaa.LOG_JSONL_PATH.read_bytes()

    eaa.record_epistemic_episode(shadow_ep)
    real_ep = eaa.close_real_episode(f"{MARK} why is this driftwood log so hollow, what species is it?",
                                     "work the wood and read the grain", "shore",
                                     [("look", "a grey shore"), ("woodwork", "A pale tan grain, silver beech perhaps.")],
                                     cycle_id="c-j1777")
    check("close_real_episode built a real closed episode", real_ep is not None)
    eaa.record_epistemic_episode(real_ep)

    rows = [json.loads(l) for l in eaa.LOG_JSONL_PATH.read_text(encoding="utf-8").splitlines()]
    check("four rows in the temp log (2 history + shadow + real)", len(rows) == 4, f"{len(rows)} rows")
    if len(rows) == 4:
        h1, h2, sh, rl = rows
        check("shadow row: advisor_shadow_only / UNSEEN / STAGE_A_SHADOW / UNTESTED",
              (sh["selection_source"], sh["adoption_state"], sh["stage"], sh["evidence_outcome"])
              == ("advisor_shadow_only", "UNSEEN", "STAGE_A_SHADOW", "UNTESTED"),
              str((sh["selection_source"], sh["adoption_state"], sh["stage"], sh["evidence_outcome"])))
        check("real closed row: du / UNSEEN (unchanged behaviour)",
              (rl["selection_source"], rl["adoption_state"]) == ("du", "UNSEEN"),
              str((rl["selection_source"], rl["adoption_state"])))
        check("history rows still say PRESENTED (the raw log is never relabelled)",
              (h1["adoption_state"], h2["adoption_state"]) == ("PRESENTED", "PRESENTED"))
        check("the appended log is byte-for-byte the old history plus new rows", eaa.LOG_JSONL_PATH.read_bytes().startswith(seed))
        check("zero new rows carry PRESENTED", not [r for r in rows[2:] if r["adoption_state"] == "PRESENTED"])
    with sqlite3.connect(str(TMP / "projection.db")) as c:
        proj = dict(c.execute("SELECT episode_id, adoption_state FROM investigative_episodes").fetchall())
    check("SQLite projection: shadow and real rows both UNSEEN",
          proj.get(shadow_ep.episode_id) == "UNSEEN" and proj.get(real_ep.episode_id) == "UNSEEN", str(proj))

print("\n== 4. the 2026-08-14 law's enforcement is untouched")
callers = []
for p in _py_files():
    if p.name == Path(__file__).name:
        continue
    try:
        src = p.read_text(encoding="utf-8")
        if "epistemic_advisory_hint" not in src:
            continue
        callers += [f"{p.relative_to(ROOT)}:{n.lineno}" for n in ast.walk(ast.parse(src))
                    if isinstance(n, ast.Call) and _call_name(n) == "epistemic_advisory_hint"]
    except (OSError, SyntaxError, UnicodeDecodeError):
        continue
check("epistemic_advisory_hint() has zero call sites", not callers, str(callers))

print("\n== 5. nothing leaked into a live store")
leaked = LIVE_LOG.exists() and MARK in LIVE_LOG.read_text(encoding="utf-8", errors="ignore")
check("no row of this run reached the live data/investigative_action_log.jsonl", not leaked)
check("the real store _connect tripwire was never reached (it would have raised above)", True)

for c in _CONNS:
    try: c.close()
    except Exception: pass
shutil.rmtree(TMP, ignore_errors=True)
print(f"\nJ-1777 adoption_state label: {'ALL PASS' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
