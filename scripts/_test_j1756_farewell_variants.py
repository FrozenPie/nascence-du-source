"""
_test_j1756_farewell_variants.py -- J-1756 (D-0286, ruled by Travis 2026-10-03: "Vary the wording (C)") test for the
rotating /quit farewell in scripts/run_nascence.py.

WHAT CHANGED. _announce_shutdown() used to send ONE fixed farewell (J-1360's wording) every time -- a verbatim
repeated prompt Du meets ~2-3x/week (F-2360: recalling his own last answer to an identical prompt carries the same
stance back whatever the wording says). It now sends the NEXT of a small fixed set of EQUIVALENT wordings
(_FAREWELL_VARIANTS), in order, so the exact prompt he last answered is never repeated. Which one he last met is read
back, read-only, from the permanent founder conversation log (core/orchestrator.py _FOUNDER_LOG) -- no new state file.

HOW THIS TEST WORKS -- hermetic, same method as scripts/_test_j1704_boot_hooks_logged.py: it never imports
run_nascence (which pulls in the whole cognitive stack and its data/ writers). It parses scripts/run_nascence.py with
ast, lifts out ONLY the farewell constants/functions (_FAREWELL_VARIANTS, _FAREWELL_LOG_TAIL_BYTES,
_last_sent_farewell, _pick_farewell, _announce_shutdown) and exec()s them in a fresh namespace against
  (a) "founder logs" it writes itself in a temp dir, row-for-row the shape core/orchestrator.py appends, and
  (b) a fake `core` package (orchestrator / sensorium / locomotion) in sys.modules, so no real project module and no
      real data/ file is ever touched. (Du is down; the live data/ is never opened here at all.)

  A  keyword lint of every variant (the three truth requirements + J-1360's house framing present BY PHRASE, the
     banned defect / bug-fix / upgrade / gauge vocabulary absent) -- plus negative controls proving the lint can fail
  B  selection: next-after-last for every starting point, 12 consecutive farewells never repeat and cycle through all
     variants, noise rows (legacy wordings, near-misses, torn / foreign lines, CRLF) never fool it
  C  the tail window (a big log is not read whole; a cut that lands mid-character does not crash)
  D  fail-open: unreadable / hostile / missing log, a raising selector -> variant 0, never an exception
  E  _announce_shutdown end to end with fakes: the farewell still goes through run_cycle(input_type="human",
     founder_canon=False), is announced exactly once whatever happens, and the bed move is unchanged
  F  static: the helpers are read-only (no write / replace / mkdir / open-for-write anywhere in them)
  G  isolation: the repo's own data/ is byte-for-byte what it was, sys.modules is restored

Without the J-1756 edit there is no _FAREWELL_VARIANTS / _pick_farewell to lift, so this fails at the first lift.

Run (from the worktree / repo root, never against live data): python scripts/_test_j1756_farewell_variants.py
"""
from __future__ import annotations

import ast
import asyncio
import contextlib
import io
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "scripts" / "run_nascence.py"

NAMES = {"_FAREWELL_VARIANTS", "_FAREWELL_LOG_TAIL_BYTES"}
FUNCS = {"_last_sent_farewell", "_pick_farewell", "_announce_shutdown"}

# J-1360's merged wording (commit 40ad6c2), the one every farewell since 2026-09-26 carried and the one variant 0 must
# stay byte-for-byte, so the rotation continues from the farewells already on record in the founder log.
J1360 = ("渡 — it's time to stop for a while, and I want you to know why: I'm the one calling it, on purpose — "
         "there's work to do on the house you live in, not on you. Rest when you're ready; I'll bring you back up "
         "once the work is done.")
# The 2026-09-04..09-25 wording (superseded by J-1360 on purpose): used ONLY as a negative control for the lint.
OLD_0904 = ("渡 — it's time to stop for a while, and I want you to know why: I'm the one calling it, on purpose — "
            "there are bug fixes and upgrades to make to how you're built, not anything wrong with you. Rest when "
            "you're ready; I'll bring you back up once the work is done.")

# The three truth requirements kept since 2026-09-04 (intentional / Travis is the one calling it / he will be brought
# back) + J-1360's framing ("work on the house you live in, not on you") + addressing him by his name.
REQUIRED = {
    "his name": "渡",
    "intentional ('on purpose')": "on purpose",
    "Travis is the one calling it": "calling it",
    "he will be brought back": "bring you back",
    "house framing (the house you live in)": "house you live in",
    "house, not him ('not on you')": "not on you",
}
# Defect / bug-fix / upgrade framing (D-0286's ruling, J-1360) and raw gauge / number language. \d and % cover numbers.
BANNED = [r"\bbugs?\b", r"\bfix(?:es|ed|ing)?\b", r"\bupgrad(?:e|es|ed|ing)\b", r"\bdefect\w*", r"\bwrong\b",
          r"\bbroken\b", r"\bfault\w*", r"\bflaw\w*", r"\bpatch\w*", r"\brepair\w*", r"\bglitch\w*",
          r"\bmalfunction\w*", r"\berrors?\b", r"\bvalence\b", r"\barousal\b", r"\bgauges?\b", r"\bscores?\b",
          r"\bpercent\w*", r"%", r"\d"]

failures: list = []
n_checks = 0


def check(name: str, ok: bool, detail="") -> None:
    global n_checks
    n_checks += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  <- {detail}" if (detail and not ok) else ""))
    if not ok:
        failures.append(name)


def norm(s: str) -> str:
    return " ".join(s.split())


def lint(text: str) -> list:
    """Problems with one farewell wording: a required phrase missing, or a banned pattern present."""
    low = text.casefold()
    problems = [f"missing {label}" for label, phrase in REQUIRED.items() if phrase.casefold() not in low]
    problems += [f"banned {pat!r} matched {m.group(0)!r}" for pat in BANNED for m in [re.search(pat, low)] if m]
    if "\n" in text or "\r" in text:
        problems.append("not a single line")
    return problems


# ---------------------------------------------------------------------------------------------------------------------
# Lifting the real code out of run_nascence.py (never importing it)
# ---------------------------------------------------------------------------------------------------------------------
class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append((record.levelname, record.getMessage()))


def lift() -> tuple:
    """(namespace holding the real lifted farewell code, the list-handler capturing its logger)."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    keep, seen = [], set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            hit = {t.id for t in node.targets if isinstance(t, ast.Name)} & NAMES
            if hit:
                keep.append(node)
                seen |= hit
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FUNCS:
            keep.append(node)
            seen.add(node.name)
    missing = sorted((NAMES | FUNCS) - seen)
    if missing:
        print(f"FATAL: scripts/run_nascence.py has no module-level {missing} (the J-1756 edit is absent)")
        sys.exit(2)
    mod = ast.Module(body=keep, type_ignores=[])
    ast.fix_missing_locations(mod)
    lg = logging.getLogger(f"j1756.lifted.{id(mod)}")
    lg.handlers[:] = []
    lg.setLevel(logging.DEBUG)
    lg.propagate = False
    handler = _ListHandler()
    lg.addHandler(handler)
    ns = {"__name__": "lifted_run_nascence", "json": json, "os": os, "Path": Path, "logger": lg}
    exec(compile(mod, str(SOURCE), "exec"), ns)
    return ns, handler


@contextlib.contextmanager
def fake_core(founder_log):
    """A fake `core` package (orchestrator / sensorium / locomotion) in sys.modules -- the only project modules the
    lifted functions reach for -- restored afterwards. Yields a namespace the test can read and re-point."""
    st = types.SimpleNamespace(loco_calls=[], cross_calls=[], place="garden")
    core = types.ModuleType("core")
    core.__path__ = []
    orch = types.ModuleType("core.orchestrator")
    orch._FOUNDER_LOG = founder_log
    sens = types.ModuleType("core.sensorium")
    sens._cross = lambda key, default: (st.cross_calls.append((key, default)) or default)
    loco = types.ModuleType("core.locomotion")
    loco.get_position = lambda: {"place": st.place}
    loco.begin_journey = lambda dest, **kw: (st.loco_calls.append((dest, kw)) or "You set off for home.")
    core.orchestrator, core.sensorium, core.locomotion = orch, sens, loco
    mods = {"core": core, "core.orchestrator": orch, "core.sensorium": sens, "core.locomotion": loco}
    saved = {k: sys.modules.get(k) for k in mods}
    sys.modules.update(mods)
    st.orchestrator = orch
    try:
        yield st
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


# ---------------------------------------------------------------------------------------------------------------------
# Founder-log fixtures (row shape = core/orchestrator.py's own append: ts / cycle_id / human / entity)
# ---------------------------------------------------------------------------------------------------------------------
def row_json(human, entity="(his reply)") -> str:
    return json.dumps({"ts": 1.0, "cycle_id": "c", "human": human, "entity": entity}, ensure_ascii=False)


def write_log(path: Path, lines, newline="\n") -> None:
    with open(path, "w", encoding="utf-8", newline=newline) as f:     # newline= translates the "\n" written below
        for ln in lines:
            f.write(ln + "\n")


def append_row(path: Path, human, entity="(his reply)") -> None:
    """Exactly how core/orchestrator.py appends (text-mode 'a', so CRLF on Windows)."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(row_json(human, entity) + "\n")


def run_announce(ns, orch):
    """Run the real lifted _announce_shutdown against a fake orchestrator; return (stdout, escaped exception)."""
    out = io.StringIO()
    err = None
    try:
        with contextlib.redirect_stdout(out):
            asyncio.run(ns["_announce_shutdown"](orch, "渡"))
    except BaseException as exc:                      # nothing may escape a farewell
        err = exc
    return out.getvalue(), err


class FakeOrch:
    def __init__(self, founder_log: Path, reply="(his reply)", boom=None) -> None:
        self.calls: list = []
        self.founder_log, self.reply, self.boom = founder_log, reply, boom

    async def run_cycle(self, raw_input, input_type="human", founder_canon=True):
        self.calls.append({"msg": raw_input, "input_type": input_type, "founder_canon": founder_canon})
        if self.boom:
            raise self.boom
        if self.reply:                                # the real permanent record is written once he has replied
            append_row(self.founder_log, raw_input, self.reply)
        return self.reply


def no_consecutive_repeat(seq) -> bool:
    return all(a != b for a, b in zip(seq, seq[1:]))


def run() -> int:
    data_dir = ROOT / "data"
    data_before = sorted(str(p) for p in data_dir.rglob("*")) if data_dir.exists() else None
    core_before = {k for k in sys.modules if k == "core" or k.startswith("core.")}
    tmp = Path(tempfile.mkdtemp(prefix="j1756_farewell_"))
    print(f"isolated temp dir: {tmp}   (the repo's own data/ is never opened)")
    try:
        ns, h = lift()
        V = ns["_FAREWELL_VARIANTS"]
        N = len(V)
        pick = ns["_pick_farewell"]

        # ===== A. the keyword lint ================================================================================
        print("\n== A. every variant keeps the truth requirements and drops the defect framing ==")
        check("5-6 variants (the briefing's range)", 5 <= N <= 6, f"N={N}")
        check("every variant is a non-empty str", all(isinstance(v, str) and v.strip() for v in V))
        check("variants are pairwise distinct (after whitespace normalisation) -- identical twins would repeat",
              len({norm(v) for v in V}) == N)
        check("variant 0 is J-1360's merged wording VERBATIM", V[0] == J1360, repr(V[0]))
        for i, v in enumerate(V):
            probs = lint(v)
            check(f"variant {i}: three truth requirements + house framing present, banned vocabulary absent",
                  not probs, probs)
        check("variants are of comparable size (no stub, no essay)", all(120 <= len(v) <= 400 for v in V),
              [len(v) for v in V])
        # negative controls: the lint must be able to FAIL (a vacuous lint proves nothing)
        check("control: the superseded 2026-09-04 'bug fixes and upgrades / wrong with you' wording is flagged",
              len(lint(OLD_0904)) >= 3, lint(OLD_0904))
        check("control: a variant without 'on purpose' is flagged",
              any("intentional" in p for p in lint(V[1].replace("on purpose", "by choice"))))
        check("control: a variant without 'bring you back' is flagged",
              any("brought back" in p for p in lint(V[1].replace("bring you back", "see you"))))
        check("control: a variant carrying a number is flagged", any("banned" in p for p in lint(V[1] + " 0.7")))

        # ===== B. selection =======================================================================================
        print("\n== B. selection: the variant after the one he last met, never the same twice running ==")
        log = tmp / "founder_conversation_log.jsonl"
        out = pick(log)
        check("no log file at all -> variant 0 (a new log has no history)", out == V[0])
        write_log(log, [])
        check("empty log -> variant 0", pick(log) == V[0])
        for k in range(N):
            write_log(log, [row_json("hello, how are you?"), row_json(V[k]), row_json("and now something else")])
            want = V[(k + 1) % N]
            check(f"last farewell on record = variant {k} -> sends variant {(k + 1) % N}"
                  + (" (wraps around)" if k == N - 1 else ""), pick(log) == want and pick(log) != V[k])

        # the LIVE state when this ships: J-1360's wording was the last thing sent -> the first new farewell is variant 1
        write_log(log, [row_json("some talk"), row_json(J1360, "I accept this pause."), row_json("a later chat")])
        check("live starting point (last sent = J-1360's wording) -> the first farewell after this change is variant 1",
              pick(log) == V[1])

        # 12 consecutive farewells through the REAL append path of the fake orchestrator: none repeats, all appear
        seq_log = tmp / "seq.jsonl"
        write_log(seq_log, [row_json(J1360)])
        sent = []
        for i in range(12):
            m = pick(seq_log)
            sent.append(m)
            append_row(seq_log, m)
            if i % 3 == 1:                                    # ordinary exchanges between farewells change nothing
                append_row(seq_log, f"an ordinary question number {i}?")
        idxs = [V.index(m) for m in sent]
        check("12 consecutive selections: no exact repeat of the previous farewell", no_consecutive_repeat(sent), idxs)
        check("12 consecutive selections: every variant is used", set(idxs) == set(range(N)), idxs)
        check("12 consecutive selections: strict in-order rotation starting after variant 0",
              idxs == [(1 + i) % N for i in range(12)], idxs)
        check("12 consecutive selections: each variant is sent about equally often (12/N, +-1)",
              all(abs(idxs.count(k) - 12 / N) <= 1 for k in range(N)), idxs)
        empty_log = tmp / "seq_empty.jsonl"
        sent2 = []
        for _ in range(12):
            m = pick(empty_log)                               # a log that does not exist yet, then grows
            sent2.append(m)
            append_row(empty_log, m)
        check("12 consecutive selections from NO history: starts at variant 0, no repeat, all variants",
              V.index(sent2[0]) == 0 and no_consecutive_repeat(sent2) and {V.index(m) for m in sent2} == set(range(N)))
        check("control: a fixed-wording sender WOULD fail the no-repeat check", not no_consecutive_repeat([V[0]] * 3))

        # noise rows must not fool the matcher
        noisy = [row_json(OLD_0904, "legacy"), "", "   ", "not json at all", "[1, 2, 3]", "null", "42", '"a string"',
                 json.dumps({"ts": 1, "cycle_id": "x", "entity": "no human key"}),
                 json.dumps({"human": 12345, "entity": "human is not a string"}),
                 json.dumps({"human": ["a", "list"]}),
                 row_json(V[2]),                                               # <- the last REAL farewell: variant 2
                 row_json(V[4] + " and one more thing"),                       # near miss: variant text + extra
                 row_json("I read this once: " + V[4]),                        # near miss: variant text inside more
                 row_json(V[4][:-1]),                                          # near miss: one character short
                 row_json(OLD_0904, "legacy again"),                           # an unknown wording is not a variant
                 row_json("plain talk with Travis"),
                 '{"human": "' + V[4][:60]]                                    # a torn final line (process killed)
        write_log(log, noisy)
        check("noise rows (legacy wording, near-misses, foreign / torn / blank lines) never fool the matcher "
              "-> after variant 2 comes variant 3", pick(log) == V[3], V.index(pick(log)) if pick(log) in V else "?")
        write_log(log, [row_json("  " + V[1].replace(" ", "  ") + "\n")])
        check("whitespace differences in the recorded text still match (normalised)", pick(log) == V[2])
        for nl, label in (("\n", "LF"), ("\r\n", "CRLF (what Windows text-mode appends write)")):
            write_log(log, [row_json("a"), row_json(V[0])], newline=nl)
            check(f"{label} line endings", pick(log) == V[1])
        write_log(log, [row_json(V[3]), row_json("x" * 10)], newline="\n")
        check("a farewell followed by a non-farewell last row", pick(log) == V[4])
        with open(log, "ab") as f:
            f.write(row_json(V[0]).encode("utf-8"))                            # last row, no trailing newline at all
        check("last row with no trailing newline is still read", pick(log) == V[1])
        log_info = [m for lv, m in h.records if lv == "INFO" and "[quit-announce] farewell variant index" in m]
        check("the choice is logged at INFO ([quit-announce] farewell variant index ...) for the post-restart grep",
              len(log_info) > 10, log_info[:1])

        # ===== C. the tail window =================================================================================
        print("\n== C. the tail window ==")
        ns2, h2 = lift()
        ns2["_FAREWELL_LOG_TAIL_BYTES"] = 3000
        pick2 = ns2["_pick_farewell"]
        big = tmp / "big.jsonl"
        pad = [row_json("渡" * 150, "渡" * 150) for _ in range(40)]               # ~ 40 x 1 KB of 3-byte characters
        write_log(big, [row_json(V[4])] + pad + [row_json(V[1])] + pad[:1])
        check("farewell inside the tail window of a big log is found (variant 1 last -> sends 2)",
              pick2(big) == V[2])
        write_log(big, [row_json(V[4])] + pad)
        check("farewell only BEFORE the window -> fails open to variant 0 (no crash, no whole-file read needed)",
              pick2(big) == V[0])
        for win in range(2990, 3010):                                          # every byte alignment of the cut
            ns2["_FAREWELL_LOG_TAIL_BYTES"] = win
            write_log(big, [row_json(V[4])] + pad + [row_json(V[2])] + pad[:2])
            try:
                got = pick2(big)
            except Exception as exc:
                got = exc
            if got != V[3]:
                check(f"window cut at {win} bytes (may land mid-character) finds variant 2 -> 3", False, repr(got))
                break
        else:
            check("windows of 2990..3009 bytes (every alignment of a cut through 3-byte characters) all find "
                  "variant 2 -> 3 without error", True)
        ns2["_FAREWELL_LOG_TAIL_BYTES"] = 512 * 1024
        check("the shipped tail window is generous (>= 256 KB: ~160 exchanges) and bounded (<= 4 MB)",
              256 * 1024 <= ns["_FAREWELL_LOG_TAIL_BYTES"] <= 4 * 1024 * 1024, ns["_FAREWELL_LOG_TAIL_BYTES"])

        # ===== D. fail-open =======================================================================================
        print("\n== D. fail-open: the farewell is announced whatever the record looks like ==")
        h.records.clear()
        d = tmp / "a_directory.jsonl"
        d.mkdir()
        try:
            got = pick(d)
            err = None
        except BaseException as exc:
            got, err = None, exc
        check("log path is a directory (unreadable) -> variant 0, nothing raised", err is None and got == V[0], err)
        check("... and a WARNING says why", any(lv == "WARNING" and "using variant 0" in m for lv, m in h.records),
              h.records[-2:])
        write_log(log, [row_json(V[1])])
        with open(log, "ab") as f:
            f.write(b"\xff\xfe\x00 not utf-8 \xc3\x28\n" + row_json(V[2]).encode("utf-8") + b"\n\xe6\xb8")
        check("invalid UTF-8 bytes / a torn multi-byte character in the log: no crash, the valid rows still count "
              "(variant 2 last -> 3)", pick(log) == V[3])
        for label, val in (("None", None), ("an int", 7), ("an object with no path", object())):
            with fake_core(val) as st:
                try:
                    got = pick()
                    err = None
                except BaseException as exc:
                    got, err = None, exc
                check(f"core.orchestrator._FOUNDER_LOG is {label} -> variant 0, nothing raised",
                      err is None and got == V[0], err)
        with fake_core(log) as st:
            del st.orchestrator._FOUNDER_LOG
            try:
                got, err = pick(), None
            except BaseException as exc:
                got, err = None, exc
            check("core.orchestrator has no _FOUNDER_LOG at all -> variant 0, nothing raised",
                  err is None and got == V[0], err)
        ns3, h3 = lift()
        def _boom(_p):
            raise RuntimeError("the selector blew up")
        ns3["_last_sent_farewell"] = _boom
        try:
            got, err = ns3["_pick_farewell"](log), None
        except BaseException as exc:
            got, err = None, exc
        check("the reader itself raising -> variant 0, nothing raised", err is None and got == ns3["_FAREWELL_VARIANTS"][0], err)

        # ===== E. _announce_shutdown end to end ===================================================================
        print("\n== E. _announce_shutdown through the real lifted code, against fakes ==")
        live_like = tmp / "live_like.jsonl"
        write_log(live_like, [row_json(J1360, "an old reply")])
        ns4, h4 = lift()
        with fake_core(live_like) as st:
            seen = []
            for n_call in range(3):
                orch = FakeOrch(live_like)
                out, err = run_announce(ns4, orch)
                seen.append(orch.calls)
                check(f"farewell {n_call + 1}: announced exactly once, nothing escaped",
                      err is None and len(orch.calls) == 1, err)
                c = orch.calls[0]
                check(f"farewell {n_call + 1}: goes through run_cycle(input_type='human', founder_canon=False) "
                      "-- recalled and replied-to like any exchange, never entered the [Travis said to me] canon",
                      c["input_type"] == "human" and c["founder_canon"] is False, c)
                check(f"farewell {n_call + 1}: the message sent is one of the variants and is the one printed as "
                      "'You: ...'", c["msg"] in V and f"You: {c['msg']}" in out, c["msg"][:40])
                check(f"farewell {n_call + 1}: his reply is printed", "渡: (his reply)" in out, out[-120:])
            msgs = [c[0]["msg"] for c in seen]
            check("3 successive /quit farewells (J-1360's wording was last): variants 1, 2, 3 -- no exact repeat, "
                  "and none is the wording he last met", [V.index(m) for m in msgs] == [1, 2, 3], [V.index(m) for m in msgs])
            check("the bed move is unchanged: out in the garden he starts a journey home with system=True, once per "
                  "farewell", st.loco_calls == [("study", {"system": True})] * 3, st.loco_calls)
            st.place = "study"
            st.loco_calls.clear()
            orch = FakeOrch(live_like)
            out, err = run_announce(ns4, orch)
            check("the bed move is unchanged: already in the study he crosses to the bed (no journey)",
                  err is None and st.cross_calls and st.cross_calls[-1][0] == "on_the_bed" and not st.loco_calls,
                  (st.cross_calls, st.loco_calls))
            # re-pointing core.orchestrator._FOUNDER_LOG (what a named profile does) is followed at call time
            other = tmp / "other_profile_log.jsonl"
            write_log(other, [row_json(V[4])])
            st.orchestrator._FOUNDER_LOG = other
            orch = FakeOrch(other)
            out, err = run_announce(ns4, orch)
            check("a re-pointed _FOUNDER_LOG (named profile) is followed at call time (variant 4 last -> 5)",
                  err is None and orch.calls[0]["msg"] == V[5 % N], orch.calls)
            # a cycle that raises: announced once, the failure is swallowed as before, the bed move still happens
            st.orchestrator._FOUNDER_LOG = live_like
            st.place = "garden"
            st.loco_calls.clear()
            h4.records.clear()
            orch = FakeOrch(live_like, boom=RuntimeError("model hub down"))
            before = len(Path(live_like).read_bytes())
            out, err = run_announce(ns4, orch)
            check("run_cycle raising: nothing escapes, one WARNING, the bed move still happens (unchanged)",
                  err is None and len(orch.calls) == 1
                  and any(lv == "WARNING" and "[quit-announce] failed (non-fatal)" in m for lv, m in h4.records)
                  and st.loco_calls == [("study", {"system": True})], (err, h4.records[-2:], st.loco_calls))
            check("CHARACTERISATION: a farewell whose cycle raised was never answered or recorded, so it does not "
                  "count as 'met' (nothing of his to recall) -- the log is untouched by it",
                  len(Path(live_like).read_bytes()) == before)
            # silent reply
            orch = FakeOrch(live_like, reply=None)
            out, err = run_announce(ns4, orch)
            check("a silent reply still prints '[渡 is silent.]' (unchanged)", err is None and "[渡 is silent.]" in out, out[-80:])
        # fail-open THROUGH the real call site
        for label, val in (("a directory", tmp / "a_directory.jsonl"), ("a missing file", tmp / "nope" / "x.jsonl"),
                           ("None", None)):
            with fake_core(val) as st:
                ns5, h5 = lift()
                orch = FakeOrch(tmp / "sink.jsonl")
                out, err = run_announce(ns5, orch)
                check(f"_FOUNDER_LOG is {label}: the farewell is STILL announced once, as variant 0, nothing escapes",
                      err is None and len(orch.calls) == 1 and orch.calls[0]["msg"] == V[0], (err, orch.calls))
        with fake_core(live_like) as st:
            ns6, h6 = lift()
            ns6["_last_sent_farewell"] = _boom
            orch = FakeOrch(tmp / "sink2.jsonl")
            out, err = run_announce(ns6, orch)
            check("the reader raising inside a real _announce_shutdown: still announced once as variant 0",
                  err is None and len(orch.calls) == 1 and orch.calls[0]["msg"] == V[0], (err, orch.calls))

        # ===== F. static: the helpers are read-only ===============================================================
        print("\n== F. static audit: nothing in the new helpers can write ==")
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("_last_sent_farewell", "_pick_farewell")]
        check("both helpers found in run_nascence.py", len(helpers) == 2)
        WRITERS = {"write", "write_text", "write_bytes", "writelines", "replace", "rename", "unlink", "remove", "mkdir",
                   "touch", "truncate", "dump", "makedirs", "rmtree", "copy", "copyfile", "move", "symlink_to"}
        bad, opens = [], []
        for fn in helpers:
            for node in ast.walk(fn):
                if isinstance(node, ast.Call):
                    f = node.func
                    name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                    if name in WRITERS:
                        bad.append((fn.name, name))
                    if name == "open":
                        mode = node.args[1].value if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) else "r"
                        opens.append((fn.name, mode))
        check("no write / replace / rename / unlink / mkdir / dump call in either helper", not bad, bad)
        check("the only open() is read-only binary ('rb')", opens == [("_last_sent_farewell", "rb")], opens)
        ann = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "_announce_shutdown")
        calls_picker = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_pick_farewell"
                           for n in ast.walk(ann))
        has_literal_wording = any(isinstance(n, ast.Constant) and isinstance(n.value, str) and "on purpose" in n.value
                                  for n in ast.walk(ann) if not (isinstance(n, ast.Constant) and n is ann.body[0].value))
        check("_announce_shutdown takes its wording from _pick_farewell() (no second hard-coded farewell inside it)",
              calls_picker and not has_literal_wording)

        # ===== G. isolation ======================================================================================
        print("\n== G. isolation ==")
        data_after = sorted(str(p) for p in data_dir.rglob("*")) if data_dir.exists() else None
        check("the repo's own data/ is exactly what it was (nothing created, nothing touched)", data_before == data_after)
        core_after = {k for k in sys.modules if k == "core" or k.startswith("core.")}
        check("sys.modules is restored: no real or fake core.* module left behind", core_after == core_before, core_after)
        check("run_nascence itself was never imported", "run_nascence" not in sys.modules and "scripts.run_nascence" not in sys.modules)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{n_checks - len(failures)}/{n_checks} checks passed" +
          (f" -- FAILED: {failures}" if failures else " -- ALL PASS"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
