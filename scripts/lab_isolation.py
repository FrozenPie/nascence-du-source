"""
Nascence -- shared lab isolation helper: telemetry + write-audit (F-1683, J-1199).

WHY THIS EXISTS: `core.model_client.call_node()` (and everything that funnels through it --
call_node_json, _ask, etc.) writes THREE telemetry rows per LLM call, not one:
  - core.telemetry.log_llm_call        -> data/llm_calls.jsonl        (HUD hardware/LLM-push graphs)
  - core.telemetry.log_thought_station -> data/thought_station_log.jsonl  (J-0939/2026-09-15, F-1308;
                                           D-0214's persistent model-attribution evidence, UNCAPPED)
  - core.telemetry.log_llm_latency     -> data/llm_latency.jsonl      (2026-08-21 HUD latency instrument)
Each path is a module-level Path global on core/telemetry.py, computed once at import time relative to
that module's own __file__ (`_DATA = Path(__file__).parent.parent / "data"`).

F-1683 (2026-09-21, found while running J-0791): all 11 offline lab scripts that isolate telemetry
(ablation_lab, lod_retrieval_lab, person_costume_lab, routing_lab, singlepass_lab, train_lab,
train_lab_model_ab_2026-09-08, train_lab_wording_ab_2026-09-08, train_state_invitro, voice_lab,
widen_lab) neutralised only log_llm_call -- log_thought_station did not exist until J-0939 added it
2026-09-15, and none of the 11 (all written earlier) was ever revisited. A lab that resolves
`core.telemetry` to the SHARED tree (cwd C:\\Nascence, or a sys.path.insert(0, C:\\Nascence) -- the
F-1285 trap) while Du is LIVE would still append real rows to data/thought_station_log.jsonl and
data/llm_latency.jsonl -- D-0214's own multi-week attribution log -- while every existing check only
ever looked at log_llm_call and reported clean.

This module is the ONE shared, tested place that closes the gap, lifted unchanged in behaviour from
scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py (F-1683's own fix script; its --dry-run
and --probe both recorded "write attempts under live data: 0" on 2026-09-22), so every lab shares one
copy instead of N hand-copies that can individually drift out of date -- exactly what produced F-1683
in the first place.

TWO independent pieces, meant to be used TOGETHER (the audit hook is the proof; the neutraliser is the
thing being proven):

1. neutralize_telemetry(scratch_dir, telemetry_module) -- no-ops all THREE call_node() writers above
   AND redirects every private Path-valued global on core.telemetry (currently _DATA, _CALLS, _HW,
   _LLM, _LAT, _STATIONS) into scratch_dir. The Path redirect is belt-and-braces: today the 3 no-op'd
   functions are the module's only writers, but a future writer added to core/telemetry.py (the way
   log_thought_station itself was added 2026-09-15, silently outdating the 11 scripts' own copies)
   would still land in scratch_dir, not live, the moment a caller adds its NAME to TELEMETRY_NOOP_FUNCS
   below -- and even before that, would land in scratch_dir rather than data/ if it reads an existing
   Path global rather than hardcoding one. Returns a dict a caller can hand to restore_telemetry() to
   undo the patch (for a caller that only wants telemetry neutralised for a scoped `with`-like block,
   e.g. scripts/lod_retrieval_lab.py's own isolate()-scoped pattern).

2. install_write_audit() -- a sys.addaudithook-based instrument, meant to be installed BEFORE any repo
   import so an import-time write is caught too, that classifies every write-shaped filesystem event
   (open for write/append/create/truncate, rename, remove, mkdir, truncate, chmod, symlink/link, every
   shutil.* mutator, plus sqlite3.connect for visibility) by whether its path resolves under
   C:\\Nascence\\data or C:\\Nascence\\docs (LIVE -- must stay empty for a genuinely isolated run),
   elsewhere under C:\\Nascence (TREE -- e.g. a stray shared-tree import, F-1285), or under any of the
   caller's own named informational roots (e.g. its own scratch dir -- proves what a redirect covered,
   not a violation). `.summary(tag)` returns the "write attempts under live data: N" line this
   project's labs already print; `.print_summary(tag)` also prints the itemised detail.

Does NOT change core/model_client.py -- stays exactly as Du's live process uses it today
(additive-only; base systems are protected). Does NOT change what any lab measures -- only how
thoroughly its telemetry side-effects are neutralised and proven absent.

UPDATE 2026-09-22 (D-0252/J-1214): core/telemetry.py ITSELF now carries a central, module-level
LAB_MODE guard (enter_lab_mode()/exit_lab_mode()) that every one of its three writers checks before
writing -- the SOURCE-side complement to this file's CALLER-side no-ops, closing the broader class of
gap F-1683 found (a future writer this file's own TELEMETRY_NOOP_FUNCS list is never updated for)
rather than just this file's one specific instance of it. neutralize_telemetry()/restore_telemetry()
below now flip that flag too (getattr-guarded, so an older or test-double telemetry_module without it
still works exactly as before), so every caller of this file gets both layers for free. This file's
own code still never edits core/telemetry.py's source -- still additive-only; Du's live process never
calls enter_lab_mode() either way.

USAGE (top of a lab script, as early as possible -- ideally before ANY `from core import ...`, so
install_write_audit() also catches an import-time write):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))   # only if scripts/ is not already on
                                                                 # sys.path -- it usually already is
                                                                 # when run as `python scripts/x.py`
    from lab_isolation import install_write_audit, neutralize_telemetry, restore_telemetry

    _audit = install_write_audit()
    from core import telemetry
    neutralize_telemetry(SCRATCH_DIR, telemetry)   # fire-and-forget: most labs never restore
    ...
    print(_audit.summary("final"))     # -> "[final] write attempts under live data: 0   (...)"
    assert _audit.clean

Scoped variant (matches scripts/lod_retrieval_lab.py's own save/restore-around-a-block pattern):

    saved = neutralize_telemetry(lab_dir, telemetry)
    try:
        ...
    finally:
        restore_telemetry(telemetry, saved)
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable

# ── live roots this project's tooling must never write under while "isolated" ──────────────────────
LIVE_ROOT = Path(r"C:\Nascence")
LIVE_DATA = LIVE_ROOT / "data"
LIVE_DOCS = LIVE_ROOT / "docs"

# call_node() calls all three of these on every inference call (core/model_client.py:255, :265, :331);
# none may write while a lab is isolating telemetry. Order matches core/telemetry.py's own definition
# order. Adding a name here is the BELT (an explicit, redundant no-op per function); since D-0252/
# J-1214, neutralize_telemetry() below ALSO flips core.telemetry's own central _LAB_MODE flag (the
# BRACES) -- a future writer core/telemetry.py adds that guards itself the same way the existing three
# now do (checking that module-level flag) is refused centrally without its name ever needing to be
# added here. This list is no longer the ONLY place a future writer needs registering, though naming
# it here too costs nothing and keeps this an honest, current inventory of what call_node() itself does.
TELEMETRY_NOOP_FUNCS = ("log_llm_call", "log_thought_station", "log_llm_latency")

_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "os.symlink", "os.link", "shutil.copyfile", "shutil.copymode", "shutil.copystat",
                 "shutil.copytree", "shutil.move", "shutil.rmtree"}


def _norm(p) -> str:
    return os.path.abspath(os.fsdecode(os.fspath(p))).lower()


def _under(s: str, root: str) -> bool:
    return s == root or s.startswith(root + os.sep)


# ── piece 2: the write-audit hook ───────────────────────────────────────────────────────────────────
class WriteAudit:
    """One instance = one installed sys.addaudithook. Build via install_write_audit() (below), not
    directly, unless a caller genuinely wants non-default live_roots/tree_root. CPython audit hooks
    cannot be removed once added (only made inert by process exit -- see sys.addaudithook's own docs),
    so there is no .uninstall(); a caller that wants a clean slate between two runs in the SAME process
    should clear the instance's own list attributes instead of installing a second hook."""

    def __init__(self, live_roots: Iterable[Path] | None = None, tree_root: Path = LIVE_ROOT,
                informational_roots: dict[str, Path] | None = None):
        self.live_roots = [_norm(p) for p in (live_roots or [LIVE_DATA, LIVE_DOCS])]
        self.tree_root = _norm(tree_root)
        self.informational_roots = {name: _norm(p) for name, p in (informational_roots or {}).items()}
        self.live_write_attempts: list = []              # under a live root -- MUST stay empty
        self.tree_write_attempts: list = []               # elsewhere under tree_root -- MUST stay empty
        self.informational_writes: dict = {name: [] for name in self.informational_roots}  # OK, expected
        self.sqlite_connects: list = []                    # informational only
        self._installed = False

    def _classify(self, event: str, path, mode) -> None:
        s = _norm(path)
        if any(_under(s, r) for r in self.live_roots):
            self.live_write_attempts.append((event, str(path), mode))
            return
        if _under(s, self.tree_root):
            self.tree_write_attempts.append((event, str(path), mode))
            return
        for name, root in self.informational_roots.items():
            if _under(s, root):
                self.informational_writes[name].append((event, str(path), mode))
                return

    def _audit(self, event, args) -> None:
        try:
            if event == "open":
                path, mode, flags = args[0], args[1], args[2]
                if isinstance(path, int):
                    return
                writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                    isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT |
                                                             os.O_APPEND | os.O_TRUNC)))
                if writing:
                    self._classify("open", path, mode)
            elif event in _WRITE_EVENTS:
                for a in args:
                    if isinstance(a, (str, bytes, os.PathLike)):
                        self._classify(event, a, None)
            elif event == "sqlite3.connect":
                self.sqlite_connects.append(str(args[0]))
        except Exception:
            pass   # an audit hook must never be the thing that raises into real work

    def install(self) -> "WriteAudit":
        if not self._installed:
            sys.addaudithook(self._audit)
            self._installed = True
        return self

    @property
    def clean(self) -> bool:
        """True iff nothing wrote under a live root and nothing wrote elsewhere under tree_root."""
        return not self.live_write_attempts and not self.tree_write_attempts

    def summary(self, tag: str = "") -> str:
        extra_bits = "; ".join(f"{name}: {len(lst)}" for name, lst in self.informational_writes.items())
        prefix = f"[{tag}] " if tag else ""
        return (f"{prefix}write attempts under live data: {len(self.live_write_attempts)}   "
                f"(elsewhere under {self.tree_root}: {len(self.tree_write_attempts)}"
                + (f"; {extra_bits}" if extra_bits else "")
                + f"; sqlite3.connect calls: {len(self.sqlite_connects)})")

    def print_summary(self, tag: str = "", detail_limit: int = 20) -> None:
        print(self.summary(tag))
        for label, lst in (("LIVE", self.live_write_attempts), ("TREE", self.tree_write_attempts)):
            for item in lst[:detail_limit]:
                print(f"    {label}: {item}")
        for name, lst in self.informational_writes.items():
            for item in lst[:detail_limit]:
                print(f"    {name}: {item}")
        for item in self.sqlite_connects[:detail_limit]:
            print(f"    sqlite: {item}")


def install_write_audit(**kwargs) -> WriteAudit:
    """Convenience wrapper: build a WriteAudit watching Nascence's own live roots (override via
    live_roots=/tree_root=/informational_roots= kwargs -- see WriteAudit) and install it. Call this
    FIRST, before any `from core import ...`, so an import-time write is caught too."""
    return WriteAudit(**kwargs).install()


# ── piece 1: telemetry neutralisation ───────────────────────────────────────────────────────────────
def neutralize_telemetry(scratch_dir=None, telemetry_module=None) -> dict:
    """No-ops core.telemetry's three call_node() writers (TELEMETRY_NOOP_FUNCS) and redirects every
    Path-valued private global on the module into scratch_dir. Safe to call twice (the second call's
    `saved` dict just captures the first call's no-ops/redirected paths, not the original module
    values -- call it once per process for a fire-and-forget lab, or pair with restore_telemetry()
    for a scoped block).

    scratch_dir: where the (belt-and-braces) Path globals get redirected. Defaults to a fresh per-
        process temp dir under tempfile.gettempdir() if omitted -- always OUTSIDE C:\\Nascence -- so a
        caller that has no scratch/ISO dir of its own yet still gets full protection with zero extra
        plumbing. Prefer passing the caller's own scratch dir when it has one (keeps every redirected
        artifact in one place next to the rest of that run's output).
    telemetry_module: pass the already-imported `core.telemetry` module when the caller has it (avoids
        a second import path -- e.g. a caller using `from core import telemetry as _tel` should pass
        `_tel`). If omitted this imports `core.telemetry` itself (requires the repo root already be on
        sys.path, true for every one of this project's lab scripts by the time they reach this call).

    Returns {"funcs": {name: original_callable, ...}, "paths": {name: original_Path, ...},
             "scratch_dir": Path} for restore_telemetry().
    """
    if telemetry_module is None:
        from core import telemetry as telemetry_module
    if scratch_dir is None:
        scratch_dir = Path(tempfile.gettempdir()) / "nascence_lab_isolation" / f"telemetry_{os.getpid()}"
    scratch_dir = Path(scratch_dir)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    saved = {"funcs": {}, "paths": {}, "scratch_dir": scratch_dir}
    for fn in TELEMETRY_NOOP_FUNCS:
        saved["funcs"][fn] = getattr(telemetry_module, fn, None)
        setattr(telemetry_module, fn, lambda *a, **k: None)
    for name in dir(telemetry_module):
        val = getattr(telemetry_module, name, None)
        if isinstance(val, Path) and name.startswith("_"):
            saved["paths"][name] = val
            setattr(telemetry_module, name, scratch_dir / f"telemetry{name}{val.suffix or '.d'}")
    # D-0252/J-1214: also flip core.telemetry's own central LAB_MODE guard, so both layers agree and a
    # future writer this function's own TELEMETRY_NOOP_FUNCS list was never updated for is STILL
    # refused (module-side, no name registration needed here). getattr-guarded so a caller passing an
    # older telemetry_module, or a test double lacking the method (e.g. this file's own __main__
    # self-check below), still works exactly as before -- this call is additive, never required.
    _enter_lab_mode = getattr(telemetry_module, "enter_lab_mode", None)
    if callable(_enter_lab_mode):
        _enter_lab_mode()
    return saved


def restore_telemetry(telemetry_module, saved: dict) -> None:
    """Undo neutralize_telemetry(): restore the original functions and Path globals it saved, AND
    (D-0252/J-1214) exit core.telemetry's own central LAB_MODE guard that neutralize_telemetry() now
    also sets -- without this, the ORIGINAL functions being restored here would still see
    _LAB_MODE == True and silently keep no-op'ing, defeating the point of restoring them. For a caller
    that only wants telemetry neutralised for a scoped block (mirrors scripts/lod_retrieval_lab.py's
    own try/finally-around-isolate() pattern) rather than for the rest of the process's life."""
    for name, fn in saved.get("funcs", {}).items():
        if fn is not None:
            setattr(telemetry_module, name, fn)
    for name, path in saved.get("paths", {}).items():
        setattr(telemetry_module, name, path)
    _exit_lab_mode = getattr(telemetry_module, "exit_lab_mode", None)
    if callable(_exit_lab_mode):
        _exit_lab_mode()


if __name__ == "__main__":
    # Self-check only -- no repo import, no network, nothing under C:\Nascence touched. Confirms the
    # audit hook classifies correctly and neutralize/restore round-trips, before any lab script trusts
    # either piece. `python scripts/lab_isolation.py` should print two OK lines and exit 0.
    sys.stdout.reconfigure(encoding="utf-8")
    import shutil as _shutil

    _tmp = Path(tempfile.mkdtemp(prefix="lab_isolation_selfcheck_"))
    try:
        fake_live = _tmp / "FakeNascence" / "data"
        fake_live.mkdir(parents=True, exist_ok=True)
        audit = WriteAudit(live_roots=[fake_live], tree_root=_tmp / "FakeNascence").install()
        with open(fake_live / "probe.txt", "w", encoding="utf-8") as f:
            f.write("x")
        assert len(audit.live_write_attempts) == 1, "audit hook did not classify a live-root write"
        print("OK: write-audit hook classifies a live-root write ->", audit.summary("selfcheck"))

        class _FakeTelemetry:
            _DATA = fake_live
            _CALLS = fake_live / "llm_calls.jsonl"

            @staticmethod
            def log_llm_call(*a, **k):
                with open(_FakeTelemetry._CALLS, "a", encoding="utf-8") as f:
                    f.write("row\n")

            @staticmethod
            def log_thought_station(*a, **k):
                pass

            @staticmethod
            def log_llm_latency(*a, **k):
                pass

        tel = _FakeTelemetry()
        scratch = _tmp / "scratch"
        saved = neutralize_telemetry(scratch, tel)
        tel.log_llm_call("m", "n")               # must now be a no-op
        assert tel._CALLS == scratch / "telemetry_CALLS.jsonl", \
            f"Path global was not redirected into scratch_dir as expected: {tel._CALLS!r}"
        assert not (fake_live / "llm_calls.jsonl").exists(), "no-op'd log_llm_call still wrote a row"
        restore_telemetry(tel, saved)
        assert tel._CALLS == fake_live / "llm_calls.jsonl", "restore_telemetry did not restore the Path global"
        print("OK: neutralize_telemetry no-ops + redirects, restore_telemetry undoes it")
    finally:
        _shutil.rmtree(_tmp, ignore_errors=True)
