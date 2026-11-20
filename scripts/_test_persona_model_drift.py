"""
_test_persona_model_drift.py -- J-1673: verify scripts/check_persona_model_drift.py actually detects drift.

A drift detector that has only ever been run against files that agree has proven nothing -- "no output" looks
identical whether it works or is vacuous. So this runs the check against inputs where the right answer is KNOWN:
  1. port_of() on the URL shapes PERSONAS uses, plus malformed ones.
  2. find_drift() on synthetic tables -- every branch: agree, the exact J-1669 shape (stale string on a hub
     port), the exact 2026-08-20 shape (wrong model on the hot-lane ollama port), an unmapped port (must be
     SKIPPED, not flagged -- the briefing's own carve-out), no port, and three kinds of malformed entry.
  3. exit_code()/main() -- 0 agree, 1 drift/malformed, 2 inconclusive (nothing compared / tables unloadable),
     so a vacuous run can never look like an all-clear.
  4. The REAL tables: no drift today (F-2245's hand audit, now automatic).
  5. The actual J-1669 bug, re-introduced into the REAL core/peers.py source text in memory (nothing on disk is
     touched): the check must flag exactly that persona.
  6. The script run as a subprocess against the real repo: exit 0.
  7. (J-1678) The wiring in scripts/du_pulse.py -- the helpers, the [8] FLAGS block, the [9] JSON gauge and the JSON
     flag mirror -- cut out of du_pulse.py's REAL source text and exec'd in du_pulse's own order (du_pulse.py itself
     cannot be run here: it opens the live DB and writes data/.du_pulse_last). Covers: all agree -> the one-line
     "none (N compared)" and no flag; the J-1669 bug -> one flag per stale persona; the 08-20 hot-lane shape ->
     eviction wording; a loader that raises / an unimportable check / nothing compared / a helper that raises ->
     a loud INCONCLUSIVE or "check block failed" flag and the pulse stays alive. DU_PULSE_PY=<path> points this
     section at another du_pulse.py (that is how it is shown to FAIL on the pre-change file and on broken ones).

Reads source files only -- no data/ store is touched and no model server is called, so it is safe with Du live.
Exit 1 on any failed check. Run: python -X utf8 scripts/_test_persona_model_drift.py
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import subprocess
import sys
import types
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import check_persona_model_drift as chk   # noqa: E402

FAILS: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(("  ok   " if ok else "  FAIL ") + label + (f"   [{detail}]" if detail and not ok else ""))
    if not ok:
        FAILS.append(label)


def run_main(loader) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = chk.main(loader=loader)
    return code, buf.getvalue()


# ── 1. port_of ────────────────────────────────────────────────────────────────────────────────────────
print("1. port_of")
for url, want in (("http://127.0.0.1:11442", "11442"), ("http://LAN-HOST:11441/", "11441"),
                  ("127.0.0.1:11433", "11433"), ("http://[::1]:11433", "11433"),
                  ("http://localhost", None), ("http://127.0.0.1:notaport", None), ("", None),
                  (None, None), (11433, None)):
    check(f"port_of({url!r}) == {want!r}", chk.port_of(url) == want, repr(chk.port_of(url)))

# ── 2. find_drift on synthetic tables ─────────────────────────────────────────────────────────────────
print("2. find_drift (synthetic)")
MAP = {"11433": "qwen3.5:9b", "11439": "gemma4:12b", "11442": "yi:34b-v1.5"}


def entry(url, model):
    return {"name": "X", "model": model, "url": url}


PERSONAS = {
    "agree":    entry("http://127.0.0.1:11442", "yi:34b-v1.5"),
    "stale":    entry("http://127.0.0.1:11439", "llama3.1:8b"),          # the J-1669 shape
    "hotlane":  entry("http://127.0.0.1:11433", "mistral:7b-instruct"),  # the 2026-08-20 shape
    "unmapped": entry("http://LAN-HOST:12345", "anything:1b"),
    "noport":   entry("http://example.invalid", "anything:1b"),
    "nomodel":  {"name": "X", "url": "http://127.0.0.1:11442"},
    "nourl":    {"name": "X", "model": "yi:34b-v1.5"},
    "notdict":  "oops",
}
R = {r.persona: r for r in chk.find_drift(PERSONAS, MAP)}
check("one Result per persona, in order", list(R) == list(PERSONAS), str(list(R)))
check("agreeing persona -> ok", R["agree"].status == "ok" and R["agree"].port == "11442")
s = R["stale"]
check("stale hub string -> drift with the right fields",
      (s.status, s.port, s.persona_model, s.mapped_model) == ("drift", "11439", "llama3.1:8b", "gemma4:12b"), str(s))
check("hub-port drift is worded as cosmetic/telemetry", "telemetry" in s.note and "evict" not in s.note, s.note)
h = R["hotlane"]
check("wrong model on :11433 -> drift, worded as an eviction risk",
      h.status == "drift" and h.port == "11433" and "evict" in h.note, str(h))
check("UNMAPPED port is skipped, NOT flagged (briefing carve-out)",
      R["unmapped"].status == "skip" and R["unmapped"].port == "12345", str(R["unmapped"]))
check("url with no port is skipped", R["noport"].status == "skip" and R["noport"].port is None)
check("missing 'model' is malformed", R["nomodel"].status == "malformed" and "'model'" in R["nomodel"].note)
check("missing 'url' is malformed", R["nourl"].status == "malformed" and "'url'" in R["nourl"].note)
check("non-dict entry is malformed", R["notdict"].status == "malformed")
check("format_result names persona, port, both strings",
      all(x in chk.format_result(s) for x in ("stale", ":11439", "'llama3.1:8b'", "'gemma4:12b'", "DRIFT")),
      chk.format_result(s))
check("agree line carries the model and no DRIFT word",
      "yi:34b-v1.5" in chk.format_result(R["agree"]) and "DRIFT" not in chk.format_result(R["agree"]))

# ── 3. exit codes (and that main() survives bad loaders) ──────────────────────────────────────────────
print("3. exit_code / main")
ok_p = {"a": entry("http://127.0.0.1:11442", "yi:34b-v1.5")}
skip_p = {"b": entry("http://127.0.0.1:12345", "z")}
check("agree only -> 0", run_main(lambda: (ok_p, MAP))[0] == 0)
check("agree + skip -> 0 (a skip is not a failure)", run_main(lambda: ({**ok_p, **skip_p}, MAP))[0] == 0)
code, out = run_main(lambda: ({**ok_p, "stale": PERSONAS["stale"]}, MAP))
check("agree + drift -> 1 and the DRIFT line is printed", code == 1 and "DRIFT" in out and "stale" in out, out)
check("malformed -> 1", run_main(lambda: ({"n": "oops"}, MAP))[0] == 1)
code, out = run_main(lambda: (skip_p, MAP))
check("ONLY skips -> 2, explicitly NOT an all-clear", code == 2 and "NOT an all-clear" in out, out)
check("no personas at all -> 2", run_main(lambda: ({}, MAP))[0] == 2)
check("empty _MODEL_BY_BASE -> 2 (everything unmapped must not read as clean)", run_main(lambda: (ok_p, {}))[0] == 2)


def _boom():
    raise ImportError("No module named 'aiohttp'")


code, out = run_main(_boom)
check("unloadable tables -> 2 with the reason shown, no traceback", code == 2 and "INCONCLUSIVE" in out and "aiohttp" in out, out)
check("loader returning non-dicts -> 2", run_main(lambda: (None, None))[0] == 2)

# ── 4. the real tables ────────────────────────────────────────────────────────────────────────────────
print("4. real tables")
personas, model_by_base = chk.load_tables()
real = chk.find_drift(personas, model_by_base)
for r in real:
    print(chk.format_result(r))
check("real PERSONAS vs real _MODEL_BY_BASE: no drift, nothing malformed",
      not [r for r in real if r.status in ("drift", "malformed")], chk.summary(real))
check("real run actually compared something (not vacuous)", any(r.status == "ok" for r in real), chk.summary(real))
check("every real persona was compared or skipped with a reason",
      len(real) == len(personas) and all(r.note for r in real if r.status == "skip"))

# ── 5. re-introduce the real bug into the real source text (in memory only) ───────────────────────────
print("5. the actual J-1669 bug, re-introduced into core/peers.py's source text")
# J-1669's bug: twain AND shackleton both said "llama3.1:8b" while :11439 served gemma4:12b. Reproduce exactly that
# when both still exist and are comparable; otherwise fall back to one comparable persona (the test must not rot
# just because the roster changed).
ok_names = [r.persona for r in real if r.status == "ok"]
victims = [p for p in ("twain", "shackleton") if p in ok_names] or ok_names[:1]
src = (ROOT / "core" / "peers.py").read_text(encoding="utf-8")
mutated, n = src, 0
for v in victims:
    # Each PERSONAS entry opens on one line:  "key": {"name": ..., "model": "<m>", ...  -- swap that persona's model.
    pat = re.compile(r'(^\s*"' + re.escape(v) + r'":\s*\{[^\n]*?"model":\s*)"[^"]*"', re.M)
    mutated, k = pat.subn(r'\1"llama3.1:8b"', mutated, count=1)
    n += k
check("mutation constructed (source layout still matches)", bool(victims) and n == len(victims),
      f"victims={victims} substituted={n}")
if victims and n == len(victims):
    mod = types.ModuleType("peers_mutated")
    mod.__file__ = str(ROOT / "core" / "peers.py")
    exec(compile(mutated, mod.__file__, "exec"), mod.__dict__)
    res = chk.find_drift(mod.PERSONAS, model_by_base)
    drifted = [r for r in res if r.status == "drift"]
    check(f"exactly {victims} flagged, no collateral flags",
          sorted(r.persona for r in drifted) == sorted(victims), str([(r.persona, r.status) for r in res]))
    for r in drifted:
        print("  ", chk.format_result(r).strip())
    check("each flagged line carries the stale string and the REAL mapped model for its port",
          all(r.persona_model == "llama3.1:8b" and r.mapped_model == model_by_base[r.port] for r in drifted),
          str(drifted))
    check("and main() on the mutated tables exits 1", run_main(lambda: (mod.PERSONAS, model_by_base))[0] == 1)

# ── 6. the script as a subprocess against the real repo ───────────────────────────────────────────────
print("6. subprocess")
cp = subprocess.run([sys.executable, str(HERE / "check_persona_model_drift.py")], capture_output=True,
                    text=True, encoding="utf-8", errors="replace", timeout=120)
check("real repo: exit 0 and '0 DRIFT' in the summary", cp.returncode == 0 and "0 DRIFT" in cp.stdout,
      f"rc={cp.returncode} out={cp.stdout[-300:]} err={cp.stderr[-300:]}")

# ── 7. the du_pulse.py [8] FLAGS + [9] JSON wiring (J-1678) ───────────────────────────────────────────
print("7. du_pulse.py wiring")
# du_pulse.py is a flat script -- it opens the live DB and writes data/.du_pulse_last on every run -- so it can be neither
# imported nor run here. Instead the four marked pieces J-1678 added are cut out of its REAL source text and exec'd, in
# du_pulse's own order, in a scratch namespace: what is tested is the text that ships, not a copy of it. DU_PULSE_PY
# points the test at another du_pulse.py (used to show it FAILS on the pre-change file and on deliberately broken ones).
DU_PULSE = Path(os.environ.get("DU_PULSE_PY") or HERE / "du_pulse.py")
dp = DU_PULSE.read_text(encoding="utf-8")
compile_err = None
try:
    compile(dp, str(DU_PULSE), "exec")
except SyntaxError as exc:
    compile_err = repr(exc)
check("du_pulse.py compiles", compile_err is None, compile_err or "")


def _between(begin: str, end: str) -> str | None:
    """The source between two marker comments (exactly one of each, in order), minus the begin marker's own line."""
    if dp.count(begin) != 1 or dp.count(end) != 1 or dp.index(begin) > dp.index(end):
        return None
    return dp[dp.index(begin): dp.index(end)].split("\n", 1)[1]


def _stmt(prefix: str) -> str | None:
    """The one single-line statement that starts with `prefix` (None unless there is exactly one)."""
    hits = [ln for ln in dp.splitlines() if ln.startswith(prefix)]
    return hits[0] if len(hits) == 1 else None


helpers = _between("J-1678 helpers begin", "J-1678 helpers end")
blk8 = _between("J-1678 [8] begin", "J-1678 [8] end")
reg9 = _stmt('_G["regression_alarms"]["persona_model_drift"] = ')
mir9 = _stmt("_flags.extend(_persona_drift_flags(")
safe_m = re.search(r"^def _safe\(.*?(?=^\S)", dp, re.M | re.S)      # du_pulse's own _safe(), verbatim
missing = [n for n, v in (("helpers", helpers), ("[8] block", blk8), ("JSON gauge", reg9), ("JSON flag mirror", mir9),
                          ("_safe", safe_m)) if v is None]
check("all four J-1678 pieces are present exactly once (helpers, [8] block, JSON gauge, JSON flag mirror)",
      not missing, "missing: " + ", ".join(missing))
anchors = ["J-1678 helpers end", 'print("\\n[8] FLAGS")', "J-1678 [8] begin", "J-1678 [8] end",
           'print("  " + ("\\n  ".join(flags) if flags else "none"))', "MARKER.write_text(str(now))", "def _safe(fn",
           '_G["regression_alarms"]["persona_model_drift"] = ', '_ra = _G["regression_alarms"]',
           "_flags.extend(_persona_drift_flags(", "_summary = {"]
apos = [dp.find(a) for a in anchors]
check("pieces sit in du_pulse's own order: helpers defined before the [8] call (a swallowed NameError there would "
      "silently kill the check); [8] block before the flags print and the marker write; gauge after _safe; mirror "
      "after _ra and before _summary",
      all(p >= 0 for p in apos) and apos == sorted(set(apos)), str(list(zip(anchors, apos))))

if not missing:
    safe_src = safe_m.group(0)

    def run_pieces(*, loader=None, drop_module=False, break_helper=False):
        """Exec the pieces in du_pulse's own order against a patched load_tables; return the namespace + [8]'s output."""
        ns = {"ROOT": ROOT, "sys": sys, "flags": [], "_G": {"regression_alarms": {}}, "_flags": []}
        exec(safe_src, ns)
        exec(helpers, ns)
        if break_helper:
            ns["_persona_drift_check"] = lambda: 1 / 0
        saved_load, saved_mod = chk.load_tables, sys.modules.get("check_persona_model_drift")
        buf = io.StringIO()
        try:
            if loader is not None:
                chk.load_tables = loader
            if drop_module:
                sys.modules["check_persona_model_drift"] = None      # `import check_persona_model_drift` now raises
            with contextlib.redirect_stdout(buf):
                exec(blk8, ns)
                exec(reg9, ns)
                ns["_ra"] = ns["_G"]["regression_alarms"]
                exec(mir9, ns)
        finally:
            chk.load_tables = saved_load
            sys.modules["check_persona_model_drift"] = saved_mod
        ns["printed"] = buf.getvalue()
        return ns

    # all agree (the real tables): the pulse must SHOW that the check ran, and flag nothing.
    real_ok = sum(1 for r in real if r.status == "ok")
    real_skip = sum(1 for r in real if r.status == "skip")
    ns = run_pieces()
    g = ns["_G"]["regression_alarms"]["persona_model_drift"]
    want = f"  persona model drift: none ({real_ok} compared" + (f", {real_skip} skipped" if real_skip else "") + ")"
    print("   [8] prints on the real tables:", ns["printed"].strip())
    check("real tables: [8] prints the one-line 'persona model drift: none (N compared)'",
          want in ns["printed"].splitlines(), repr(ns["printed"]))
    check("real tables: no flag anywhere (text flags and JSON flags)", ns["flags"] == [] and ns["_flags"] == [],
          str(ns["flags"]))
    check("real tables: gauge = status none, N compared, nothing flagged, no reason",
          isinstance(g, dict) and (g["status"], g["compared"], g["drift"], g["malformed"], g["reason"])
          == ("none", real_ok, [], [], None), str(g))

    # the actual J-1669 bug (section 5's mutated PERSONAS): one flag per stale persona, and it must NOT look clean.
    mod = globals().get("mod")
    if mod is not None and victims:
        ns = run_pieces(loader=lambda: (mod.PERSONAS, model_by_base))
        g = ns["_G"]["regression_alarms"]["persona_model_drift"]
        fl = ns["flags"]

        def _flag_ok(v):
            port = next(r.port for r in real if r.persona == v)
            return any(f.startswith(f"persona model drift: {v} :{port} ") and "'llama3.1:8b'" in f
                       and repr(model_by_base[port]) in f for f in fl)

        for f in fl:
            print("   [8] flag:", f)
        check("J-1669 bug re-introduced: one flag per stale persona, and NO 'none' line (it must not look clean)",
              len(fl) == len(victims) and "none (" not in ns["printed"], f"flags={fl} printed={ns['printed']!r}")
        check("each flag names the persona, its :port, the stale string and the REAL mapped model",
              all(_flag_ok(v) for v in victims), str(fl))
        check("JSON gauge: status drift, exactly those personas, with both model strings",
              g["status"] == "drift" and sorted(d["persona"] for d in g["drift"]) == sorted(victims)
              and all(d["persona_model"] == "llama3.1:8b" and d["mapped_model"] == model_by_base[d["port"]]
                      for d in g["drift"]), str(g))
        check("JSON _flags mirrors [8]'s flags exactly", ns["_flags"] == fl, str(ns["_flags"]))

    ns = run_pieces(loader=lambda: ({"marcus": entry("http://127.0.0.1:11433", "falcon3:7b")}, MAP))
    check("08-20 shape (wrong model on the hot-lane ollama port): flagged, with the eviction wording",
          len(ns["flags"]) == 1 and ":11433" in ns["flags"][0] and "evict" in ns["flags"][0]
          and "'qwen3.5:9b'" in ns["flags"][0], str(ns["flags"]))

    # fail-open: every way the check can fail must leave the pulse running AND say so (a flag, never silence).
    ns = run_pieces(loader=_boom)                                  # reaching this line = nothing escaped the block
    g = ns["_G"]["regression_alarms"]["persona_model_drift"]
    check("tables unloadable (loader raises): ONE INCONCLUSIVE flag with the reason, and no 'none' line",
          len(ns["flags"]) == 1 and "INCONCLUSIVE" in ns["flags"][0] and "aiohttp" in ns["flags"][0]
          and "NOT an all-clear" in ns["flags"][0] and "none (" not in ns["printed"], str(ns["flags"]))
    check("... and the JSON side agrees: gauge inconclusive, the same flag mirrored",
          g["status"] == "inconclusive" and ns["_flags"] == ns["flags"], str(g))
    ns = run_pieces(drop_module=True)
    check("check script unimportable: INCONCLUSIVE flag that names it",
          len(ns["flags"]) == 1 and "INCONCLUSIVE" in ns["flags"][0] and "check_persona_model_drift" in ns["flags"][0],
          str(ns["flags"]))
    ns = run_pieces(loader=lambda: (skip_p, MAP))
    check("nothing compared (every persona skipped): INCONCLUSIVE flag, never an all-clear",
          len(ns["flags"]) == 1 and "nothing was compared" in ns["flags"][0] and "none (" not in ns["printed"],
          str(ns["flags"]) + repr(ns["printed"]))
    ns = run_pieces(loader=lambda: ({"n": "oops"}, MAP))
    check("malformed PERSONAS entry: flagged as malformed",
          ns["flags"] == ["persona model drift: n malformed — entry is not a dict"], str(ns["flags"]))
    ns = run_pieces(break_helper=True)
    check("a helper that itself raises is caught by the [8] block's own handler: a 'check block failed' flag",
          len(ns["flags"]) == 1 and "check block failed" in ns["flags"][0] and "ZeroDivisionError" in ns["flags"][0],
          str(ns["flags"]))
    check("... and the JSON side stays loud too (gauge None -> an INCONCLUSIVE 'no result' flag, not silence)",
          ns["_G"]["regression_alarms"]["persona_model_drift"] is None and len(ns["_flags"]) == 1
          and "INCONCLUSIVE" in ns["_flags"][0], str(ns["_flags"]))

print()
if FAILS:
    print(f"{len(FAILS)} FAILED:", *FAILS, sep="\n  - ")
    raise SystemExit(1)
print("ALL OK")
