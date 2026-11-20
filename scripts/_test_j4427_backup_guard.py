"""J-4427 / F-5128: wider per-boot state backup, the empty/all-NUL source guard, and NUL-tolerant telemetry readers.

Temp paths only: no read or write of the real data/ directory. Every module-level path the code under test would
use is pointed at a temp dir before any call, and retention.boot_rotate is replaced by a stub.
    python scripts/_test_j4427_backup_guard.py
"""
from __future__ import annotations

import json
import logging
import sys
import tempfile
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import core  # noqa: E402  (core BEFORE anything else, and it must be THIS tree's core)
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__

# retention must never run against a real tree from this test
_fake_ret = types.ModuleType("scripts.retention")
_fake_ret.boot_rotate = lambda cls, root=None: []
import scripts  # noqa: E402
sys.modules["scripts.retention"] = _fake_ret
scripts.retention = _fake_ret

from scripts import backup_memory as bm  # noqa: E402
from scripts import backup_identity as bi  # noqa: E402
from core import telemetry as tel  # noqa: E402

for m in (bm, bi, tel):
    assert Path(m.__file__).resolve().is_relative_to(HERE), m.__file__

FAILS: list = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        FAILS.append(name)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.recs = []

    def emit(self, r):
        self.recs.append((r.levelname, r.getMessage()))


cap = _Cap()
logging.getLogger("nascence.backup").addHandler(cap)
logging.getLogger("nascence.backup").setLevel(logging.DEBUG)

with tempfile.TemporaryDirectory(prefix="j4427_") as td:
    td = Path(td)
    data, dest = td / "data", td / "backups"
    data.mkdir()
    dest.mkdir()
    # ---- 1. the 16 crash-wiped files are in STATE_FILES
    wiped = ["spring_ledger_state.json", "opponent_process_state.json", "room_state.json", "life_state.json",
             "cat_state.json", "transport_lines.json", "transport_cause_lines.json", "sound_knowledge.json",
             "climate_state.json", "fieldcraft.json", "supply.json", "smell_field.json", "world_manifest_live.json",
             "garden_life.json", "shore_life.json", "wood_life.json"]
    missing = [n for n in wiped if n not in bm.STATE_FILES]
    check("all 16 crash-wiped files listed in STATE_FILES", not missing, missing)
    check("STATE_FILES has no duplicates", len(set(bm.STATE_FILES)) == len(bm.STATE_FILES))

    # ---- 2. first snapshot: everything good
    for n in bm.STATE_FILES:
        (data / n).write_text(json.dumps({"name": n, "v": 1}), encoding="utf-8")
    n1 = bm.backup_state("20261120_100000", data=data, dest=dest)
    s1 = dest / "state_20261120_100000"
    man1 = json.loads((s1 / bm.MANIFEST).read_text(encoding="utf-8"))
    check("good boot: every file copied", n1 == len(bm.STATE_FILES) and len(man1["copied"]) == n1, (n1, man1))
    check("good boot: no skips, no warnings", not man1["skipped"] and not [r for r in cap.recs if r[0] == "WARNING"],
          cap.recs)

    # ---- 3. crash: spring ledger all NUL (big), room_state empty, cat_state missing
    big = 3 * (1 << 20) + 17
    (data / "spring_ledger_state.json").write_bytes(b"\x00" * big)
    (data / "room_state.json").write_bytes(b"")
    (data / "cat_state.json").unlink()
    # a good file with a NUL prefix-free body that only *contains* a NUL later must still be copied
    (data / "supply.json").write_bytes(b'{"a": 1}' + b"\x00" * 10)
    n2 = bm.backup_state("20261120_110000", data=data, dest=dest)
    s2 = dest / "state_20261120_110000"
    man2 = json.loads((s2 / bm.MANIFEST).read_text(encoding="utf-8"))
    check("crash boot: NUL file skipped with reason",
          man2["skipped"].get("spring_ledger_state.json", "").startswith("all NUL"), man2["skipped"])
    check("crash boot: empty file skipped with reason",
          man2["skipped"].get("room_state.json", "").startswith("empty"), man2["skipped"])
    check("crash boot: missing file recorded", "cat_state.json" in man2["missing"], man2["missing"])
    check("crash boot: count excludes skipped + missing", n2 == len(bm.STATE_FILES) - 3, n2)
    check("crash boot: partly-NUL file with real content still copied", "supply.json" in man2["copied"])
    sp2 = (s2 / "spring_ledger_state.json").read_bytes()
    check("crash boot: NUL source never copied; last good copy carried forward",
          json.loads(sp2)["v"] == 1 and man2["carried"].get("spring_ledger_state.json") == s1.name, man2["carried"])
    check("crash boot: earlier good snapshot untouched",
          json.loads((s1 / "spring_ledger_state.json").read_text())["v"] == 1)
    warns = [m for lv, m in cap.recs if lv == "WARNING"]
    check("crash boot: one WARNING per damaged source, naming it",
          sum("spring_ledger_state.json" in m for m in warns) == 1 and sum("room_state.json" in m for m in warns) == 1,
          warns)

    # ---- 4. a second crash boot: carry still finds the good copy (skips the carried-only snapshot? no: carried
    #         copy in s2 is itself good, so it is the newest good one)
    n3 = bm.backup_state("20261120_120000", data=data, dest=dest)
    man3 = json.loads((dest / "state_20261120_120000" / bm.MANIFEST).read_text(encoding="utf-8"))
    check("second crash boot: still carried, from the newest good copy",
          man3["carried"].get("spring_ledger_state.json") == s2.name, man3["carried"])

    # ---- 5. no earlier good copy at all: skip, warn, nothing written
    fresh = td / "fresh_backups"
    fresh.mkdir()
    cap.recs.clear()
    bm.backup_state("20261120_130000", data=data, dest=fresh)
    s5 = fresh / "state_20261120_130000"
    check("no earlier copy: damaged file absent from snapshot", not (s5 / "spring_ledger_state.json").exists())
    check("no earlier copy: warning says so",
          any("no earlier good copy" in m for lv, m in cap.recs if lv == "WARNING"), cap.recs)

    # ---- 6. source_damage speed / edge
    good_big = data / "good_big.json"
    good_big.write_bytes(b"{" + b" " * (5 << 20) + b"}")
    t0 = time.time()
    r = bm.source_damage(good_big)
    check("source_damage: good 5 MB file passes in one read", r is None and time.time() - t0 < 0.5, r)

    # ---- 7. backup_identity guard (module paths pointed at temp)
    idd = td / "id_data"
    idd.mkdir()
    ax = idd / "axiom.json"
    ax.write_bytes(b"\x00" * 4096)
    ok_t = idd / "reading_state.json"
    ok_t.write_text('{"x": 1}', encoding="utf-8")
    bi.DEST = td / "snap"
    bi.TARGETS = [ax, ok_t]
    line = bi.backup()
    day = time.strftime("%Y%m%d")
    check("backup_identity: NUL axiom not snapshotted", not (bi.DEST / day / "axiom.json").exists())
    check("backup_identity: good file snapshotted", (bi.DEST / day / "reading_state.json").exists())
    check("backup_identity: report line carries the WARNING", "WARNING skipped damaged source: axiom.json" in line,
          line)
    ax.write_text('{"name": "Du"}', encoding="utf-8")
    line2 = bi.backup()
    check("backup_identity: a later boot the same day snapshots the repaired file",
          (bi.DEST / day / "axiom.json").exists() and "WARNING" not in line2, line2)

    # ---- 8. telemetry readers tolerate the crash's NUL line
    calls = td / "llm_calls.jsonl"
    now = time.time()
    good = [{"ts": now - 5, "model": "m1", "pc": 400, "nc": 4096, "node": "http://h:11433", "by": "a:1"}
            for _ in range(6)]
    glued = {"ts": now - 1, "model": "m2", "pc": 300, "nc": 4096, "node": "http://h:11433", "by": "a:1"}
    with open(calls, "wb") as f:
        for r in good:
            f.write((json.dumps(r) + "\n").encode())
        f.write(b"\x00" * 3000 + (json.dumps(glued) + "\n").encode())   # the crash shape: NULs, then the next row
        f.write(b"not json at all\n")
    tel._CALLS = calls
    rows = tel._read_jsonl_rows(calls)
    check("_read_jsonl_rows: NUL-glued row recovered, garbage skipped", len(rows) == 7 and rows[-1]["model"] == "m2",
          len(rows))
    rates = tel._llm_rates()
    check("_llm_rates: counts survive the NUL line", rates.get("m1") == 6 and rates.get("m2") == 1, rates)
    ws = tel.window_status()
    check("window_status: not 'unreadable'", "why" not in ws and ws, ws)
    js = tel.job_status(min_calls=1)
    check("job_status: not 'unreadable'", "why" not in js, js)
    lat = td / "llm_latency.jsonl"
    with open(lat, "wb") as f:
        f.write((json.dumps({"ok": True, "by": "a", "pe": 10, "pe_s": 0.1, "s": 1.0}) + "\n").encode())
        f.write(b"\x00" * 500 + b"\n")
    tel._LAT = lat
    ps = tel.prefill_share_status()
    check("prefill_share_status: reads past a NUL line", "a" in ps.get("by_caller", {}), ps)
    # the old reader shape, for contrast: one NUL line made the whole list comprehension raise
    try:
        [json.loads(l) for l in open(calls, encoding="utf-8") if l.strip()]
        old_raised = False
    except ValueError:
        old_raised = True
    check("contrast: the pre-J-4427 reader shape raises on this file", old_raised)

    # ---- 9. HUD tail reader (hud/server.py) recovers the glued row too
    src = (HERE / "hud" / "server.py").read_text(encoding="utf-8")
    check("hud _tail_rows strips NUL before parsing", 'line = line.replace("\\x00", "").strip()' in src)

print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
