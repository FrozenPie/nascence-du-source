"""
J-1681 test for scripts/du_lifetimes.py (exact per-process Du lifetimes from nascence.log markers + the
"which lifetimes ran the code that landed at T" classifier) and its --from-log surface in
scripts/du_restart_history.py. Synthetic logs live in a temp dir; the real data/nascence.log is only READ
(binary, byte-snapshotted). Nothing in data/ is written.

Run:  python scripts/du_lifetimes_test.py             # unit tests + validation against the real log
      python scripts/du_lifetimes_test.py --geometry  # also reproduce F-2255's two geometry_tuples.jsonl
                                                      # boundaries (reads the 131 MB file, read-only, ~10 s)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import du_lifetimes as dl  # noqa: E402  (ModuleNotFoundError before J-1681)

failures = []


def check(name, cond, detail=""):
    if not cond:
        failures.append(name)
    print(f"  {'PASS' if cond else 'FAIL'} {name}" + (f"   [{detail}]" if detail and not cond else ""))


def utc(y, mo, d, h, mi, s=0, ms=0, off=12):
    """UTC epoch of a LOCAL wall time at a FIXED UTC offset (NZST +12, NZDT +13): independent of zoneinfo."""
    tz = dt.timezone(dt.timedelta(hours=off))
    return dt.datetime(y, mo, d, h, mi, s, tzinfo=tz).timestamp() + ms / 1000.0


def ln(ts, msg, logger="nascence.main"):
    return f"{ts} [{logger}] {msg}\r\n".encode("utf-8")


AWAKE = "Nascence is awake. Enter text to begin a thought cycle."
MEM = "Memory store initialised at C:\\Nascence\\data\\memory\\nascence.db"
DOWN = "Nascence shutting down."
BUSY = "[composer] bridge not started (port 8765 busy?): [WinError 10048] Only one usage of each socket address"
M = dl.Marker


def near(a, b, tol=1e-3):
    return a is not None and abs(a - b) <= tol


# ---------------------------------------------------------------------------------------------
# S1: four lifetimes covering every rule (2026-09-05 is NZST, UTC+12)
# ---------------------------------------------------------------------------------------------
S1 = [
    ln("2026-09-05 10:00:00,000", MEM, "nascence.memory"),                      # L0 start
    ln("2026-09-05 10:00:20,500", AWAKE),
    ln("2026-09-05 10:30:00,000", "[CYCLE ab] complete in 3.1s", "nascence.orchestrator"),
    b"Traceback (most recent call last):\r\n",                                   # no timestamp: not a line of record
    ln("2026-09-05 11:00:00,000", DOWN),                                         # L0 SHUTDOWN
    ln("2026-09-05 11:10:00,000", MEM, "nascence.memory"),                      # 645 s before L1 awake: too old
    ln("2026-09-05 11:20:00,000", MEM, "nascence.memory"),
    ln("2026-09-05 11:20:30,000", MEM, "nascence.memory"),                      # latest in window: L1 start
    ln("2026-09-05 11:20:45,000", AWAKE),
    ln("2026-09-05 11:21:00,000", "[CYCLE cd] human: Nascence is awake, said Du. Nascence shutting down? "
       "Memory store initialised?", "nascence.orchestrator"),                    # quoted markers: NOT markers
    ln("2026-09-05 12:00:00,000", "[stability] tick #1", "nascence.competence"),  # L1's last line, no shutdown
    ln("2026-09-05 12:30:00,000", AWAKE),                                        # L2: no memory-init -> start = awake
    ln("2026-09-05 12:30:03,000", BUSY),                                         # port busy: L1 still alive
    ln("2026-09-05 13:00:00,000", DOWN),                                         # the pair's single shutdown line
    ln("2026-09-05 13:10:00,000", MEM, "nascence.memory"),                      # L3 start
    ln("2026-09-05 13:10:10,000", AWAKE),
    ln("2026-09-05 13:40:00,000", "heartbeat", "nascence.competence"),           # last line: open tail
]


def run_cli(*cmd):
    p = subprocess.run([sys.executable, *cmd], capture_output=True, text=True, encoding="utf-8", timeout=180)
    return p.returncode, p.stdout, p.stderr


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    s1 = td / "s1.log"
    s1.write_bytes(b"".join(S1))

    print("\n[1] markers, lifetime starts/ends, strict matching")
    d = dl.load(s1)
    c, lts = d["counts"], d["lifetimes"]
    check("marker counts (quoted marker text ignored)", (c["awake"], c["memory_init"], c["shutdown"], c["port_busy"]) == (4, 5, 2, 1), str(c))
    check("4 lifetimes: 2 SHUTDOWN, 2 UNCLEAN, 1 OVERLAP", (c["lifetimes"], c["shutdown_ended"], c["unclean"], c["overlap"]) == (4, 2, 2, 1), str(c))
    L0, L1, L2, L3 = lts
    check("L0 starts at its memory-init line (20.5 s before awake), ends at the shutdown line",
          near(L0["start"], utc(2026, 9, 5, 10, 0)) and near(L0["awake"], utc(2026, 9, 5, 10, 0, 20, 500))
          and near(L0["end"], utc(2026, 9, 5, 11, 0)) and L0["end_kind"] == "SHUTDOWN" and L0["start_marker"] == "memory_init"
          and near(L0["hours"], 1.0))
    check("L1 start = LATEST memory-init within 400 s (11:20:30, not 11:20:00 / the 645 s-old 11:10:00)",
          near(L1["start"], utc(2026, 9, 5, 11, 20, 30)))
    check("L1 UNCLEAN: end = last log line before the next boot (12:00:00), not the next start",
          L1["end_kind"] == "UNCLEAN" and near(L1["end"], utc(2026, 9, 5, 12, 0)))
    check("L2 has no memory-init: start = its awake line", L2["start_marker"] == "awake" and near(L2["start"], utc(2026, 9, 5, 12, 30)))
    check("L3 is the open tail: UNCLEAN, end = last log line, end_hi None",
          L3["tail"] and L3["end_kind"] == "UNCLEAN" and near(L3["end"], utc(2026, 9, 5, 13, 40)) and L3["end_hi"] is None)

    print("\n[2] OVERLAP (double launch: port-busy line right after the awake line, older Du never shut down)")
    check("L2 flagged OVERLAP with L1 and carries the evidence line",
          L2["overlap"] and L2["overlap_with"] == 1 and "bridge not started" in (L2["overlap_evidence"] or ""))
    check("L1 overlapped_by [2]; its end_hi stretched to the overlapping lifetime's end (13:00:00)",
          L1["overlapped_by"] == [2] and near(L1["end_hi"], utc(2026, 9, 5, 13, 0)))
    check("a port-busy line is NOT overlap when the older lifetime shut down cleanly first",
          not any(x["overlap"] for x in dl.build_lifetimes(
              [M(100.0, None, "a"), M(300.0, 290.0, "a")], [], [M(200.0, 190.0, "d")], [M(301.0, 300.0, "busy")], 400.0)))

    print("\n[3] start rule edge: a memory-init at or before the PREVIOUS awake line is not this boot's")
    pure = dl.build_lifetimes([M(1000.0, None, "a"), M(1100.0, 1090.0, "a")], [M(990.0, None, "m")], [], [], 1200.0)
    check("boot A uses the 990 memory-init; boot B (110 s later, same meminit is pre-A-awake) falls back to its awake",
          near(pure[0]["start"], 990.0) and pure[1]["start_marker"] == "awake" and near(pure[1]["start"], 1100.0))

    print("\n[4] byte snapshot: never read past it; an unfinished last line is dropped")
    snap = td / "snap.log"
    base = b"".join(S1)
    snap.write_bytes(base)
    size0 = snap.stat().st_size
    with open(snap, "ab") as f:                      # Du appends live
        f.write(ln("2026-09-05 14:00:00,000", MEM, "nascence.memory") + ln("2026-09-05 14:00:09,000", AWAKE))
    check("size= snapshot excludes lines appended afterwards",
          len(dl.scan_log(snap, size=size0)["awake"]) == 4 and len(dl.scan_log(snap)["awake"]) == 5)
    check("a snapshot that cuts a line in half drops that line", len(dl.scan_log(snap, size=size0 + 10)["awake"]) == 4)
    part = td / "part.log"
    part.write_bytes(base + b"2026-09-05 14:00:09,000 [nascence.main] Nascence is awake. Enter")   # no newline yet
    check("a final line with no newline yet is not counted", len(dl.scan_log(part)["awake"]) == 4)

    print("\n[5] local time -> UTC epoch (zoneinfo) incl. DST edges")
    dst = td / "dst.log"
    dst.write_bytes(b"".join([
        ln("2026-09-27 01:59:00,000", MEM, "nascence.memory"),                 # NZST +12, 1 min before spring-forward
        ln("2026-09-27 01:59:20,000", AWAKE),
        ln("2026-09-27 03:00:30,000", DOWN),                                   # NZDT +13: 90 s later in real time
        ln("2027-04-04 02:30:00,000", "tick", "nascence.x"),                   # first pass of the repeated hour (NZDT)
        ln("2027-04-04 02:58:00,000", "tick", "nascence.x"),
        ln("2027-04-04 02:59:30,000", "tick", "nascence.x"),
        ln("2027-04-04 02:10:00,000", MEM, "nascence.memory"),                 # clock stepped back: 2nd pass (NZST)
        ln("2027-04-04 02:10:20,000", AWAKE),
        ln("2027-04-04 02:40:00,000", DOWN),
        ln("2027-04-04 03:05:00,000", "after", "nascence.x"),
    ]))
    dd = dl.load(dst)
    a, b = dd["lifetimes"]
    check("spring-forward: 01:59:00 NZST -> 03:00:30 NZDT is 90 s of real time", near(a["end"] - a["start"], 90.0), str(a))
    check("fall-back: the repeated hour's 2nd pass is read as NZST (a 1 h-early epoch is the bug)",
          near(b["start"], utc(2027, 4, 4, 2, 10, off=12)) and not near(b["start"], utc(2027, 4, 4, 2, 10, off=13))
          and near(b["end"], utc(2027, 4, 4, 2, 40, off=12)), str(b))
    check("fall-back handling is reported as a warning", any("DST fall-back" in w for w in dd["warnings"]), str(dd["warnings"]))
    check("plain NZST / NZDT dates convert with the right offset",
          near(dl.load(s1)["lifetimes"][0]["start"], utc(2026, 9, 5, 10, 0, off=12))
          and near(dl.parse_when("2026-10-03 08:15:27"), utc(2026, 10, 3, 8, 15, 27, off=13)))

    print("\n[6] classifier: booted-after / alive-across / maybe-alive / ended-before / live-hours")
    r = dl.classify(lts, utc(2026, 9, 5, 11, 5))
    check("t between L0's shutdown and L1's boot: L1,L2,L3 ran the change; L0 ended before",
          [x["i"] for x in r["booted_after"]] == [1, 2, 3] and r["alive_across"] == [] and r["maybe_alive_across"] == [] and r["ended_before"] == 1)
    check("live-hours of post-landing lifetimes: lo = sum of evidence-of-life hours, hi counts L1 to its stretched end_hi",
          near(r["live_hours_post"], 1.658) and near(r["live_hours_post_max"], 2.658) and r["n_overlap_post"] == 1, str(r["live_hours_post"]) + "/" + str(r["live_hours_post_max"]))
    r = dl.classify(lts, utc(2026, 9, 5, 10, 30))
    check("t inside L0: L0 ran the OLD code (and kept running it 0.5 h after t); L1..L3 booted after",
          [x["i"] for x in r["alive_across"]] == [0] and near(r["alive_across"][0]["old_code_hours_after_t"], 0.5)
          and near(r["old_code_hours_after_t"], 0.5) and [x["i"] for x in r["booted_after"]] == [1, 2, 3])
    r = dl.classify(lts, utc(2026, 9, 5, 12, 15))
    check("t in L1's silent tail (12:00 last line .. 13:00 end_hi): L1 is MAYBE-alive (old code if so), never booted-after",
          [x["i"] for x in r["maybe_alive_across"]] == [1] and r["alive_across"] == [] and [x["i"] for x in r["booted_after"]] == [2, 3])
    r = dl.classify(lts, utc(2026, 9, 5, 13, 9, 30))
    check("a change landing 30 s before a boot is flagged CLOSE-CALL (boot still counts as after)",
          [x["i"] for x in r["booted_after"]] == [3] and r["booted_after"][0]["close_call"] and near(r["booted_after"][0]["delta_s"], 30.0)
          and r["n_close_call"] == 1 and r["ended_before"] == 3)
    r = dl.classify(lts, utc(2026, 9, 5, 9, 0))
    check("t before the first boot: everything booted after, first_boot_after is lifetime 0",
          len(r["booted_after"]) == 4 and r["first_boot_after"]["i"] == 0 and r["alive_across"] == [])
    r = dl.classify(lts, utc(2026, 9, 6, 9, 0))
    check("t after the last line: the open TAIL may still be running (maybe-alive), the rest ended before",
          [x["i"] for x in r["maybe_alive_across"]] == [3] and r["ended_before"] == 3 and r["booted_after"] == [])

    print("\n[7] reference instants: file mtime, commit COMMITTER date, ISO strings")
    f = td / "x.txt"
    f.write_text("x")
    os.utime(f, (1787957000, 1787957000))
    check("epoch_for_file is the mtime", near(dl.epoch_for_file(f), 1787957000.0))
    check("parse_when: epoch string, offset ISO, naive ISO = log-local time",
          near(dl.parse_when("1787957042.9"), 1787957042.9)
          and near(dl.parse_when("2026-08-29T10:27:19+12:00"), utc(2026, 8, 29, 10, 27, 19))
          and near(dl.parse_when("2026-08-29 10:27:19"), utc(2026, 8, 29, 10, 27, 19)))
    repo = td / "repo"
    repo.mkdir()
    env = dict(os.environ, GIT_AUTHOR_DATE="2026-08-20T10:00:00+12:00", GIT_COMMITTER_DATE="2026-08-29T10:27:19+12:00")
    try:
        subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", "x"], check=True, capture_output=True, env=env)
        check("epoch_for_commit is the COMMITTER date (not the author date)",
              near(dl.epoch_for_commit("HEAD", repo), utc(2026, 8, 29, 10, 27, 19)))
        try:
            dl.epoch_for_commit("no-such-rev-xyz", repo)
            check("an unresolvable rev raises ValueError", False)
        except ValueError:
            check("an unresolvable rev raises ValueError", True)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"  SKIP commit-date tests (git unavailable: {e})")

    print("\n[8] CLIs: du_lifetimes.py and du_restart_history.py --from-log (forwarded flags), old flags intact")
    rc, out, err = run_cli(str(HERE / "du_lifetimes.py"), "--log", str(s1), "--at", "2026-09-05 11:05:00", "--json")
    j = json.loads(out) if rc == 0 else {}
    check("du_lifetimes.py --json: 4 lifetimes + classification", rc == 0 and len(j.get("lifetimes", [])) == 4
          and [x["i"] for x in j["classification"]["booted_after"]] == [1, 2, 3], err[-300:])
    rc, out, err = run_cli(str(HERE / "du_restart_history.py"), "--from-log", "--log", str(s1), "--at", "2026-09-05 11:05:00", "--json")
    j2 = json.loads(out) if rc == 0 else {}
    check("du_restart_history.py --from-log forwards --log/--at/--json", rc == 0 and j2.get("lifetimes") == j.get("lifetimes")
          and j2.get("classification") == j.get("classification"), err[-300:])
    rc, out, err = run_cli(str(HERE / "du_lifetimes.py"), "--log", str(s1), "--at", "2026-09-05 11:05:00")
    check("plain-text report prints the BOOTED AFTER section and the OVERLAP flag", rc == 0 and "BOOTED AFTER t" in out and "OVERLAP" in out, err[-300:])
    rc, out, err = run_cli(str(HERE / "du_restart_history.py"), "--help")
    check("du_restart_history.py keeps --since/--check-live and gains --from-log",
          rc == 0 and "--since" in out and "--check-live" in out and "--from-log" in out)
    rc, out, err = run_cli(str(HERE / "du_restart_history.py"), "--bogus")
    check("without --from-log an unknown flag is still an argparse error (behaviour preserved)", rc == 2 and "unrecognized" in err)

# ---------------------------------------------------------------------------------------------
# Validation against the REAL log (read-only). F-2255's reference snapshot is the first 84,810,536
# bytes of data/nascence.log (taken while Du was live): 284 awake / 347 memory-init / 253 shutdown.
# ---------------------------------------------------------------------------------------------
PIN = 84_810_536
print("\n[9] real data/nascence.log against the J-0949 / F-2255 reference numbers")
REAL = dl.DEFAULT_LOG
if REAL.exists() and REAL.stat().st_size >= PIN:
    rd = dl.load(REAL, size=PIN)
    rc_ = rd["counts"]
    check("snapshot counts 284 awake / 347 memory-init / 253 shutdown", (rc_["awake"], rc_["memory_init"], rc_["shutdown"]) == (284, 347, 253), str(rc_))
    check("284 lifetimes, one per awake line", rc_["lifetimes"] == 284)
    ov = [x for x in rd["lifetimes"] if x["overlap"]]
    check("exactly one OVERLAP: the 2026-09-05 11:37:04 double launch", len(ov) == 1 and ov[0]["start_local"] == "2026-09-05 11:37:04", str(ov))
    mood = dl.classify(rd["lifetimes"], dl.parse_when("2026-08-29 10:27:19"))
    check("first boot after core/mood.py landed (10:27 NZST) = 2026-08-29 10:42:46 local",
          mood["first_boot_after"]["start_local"] == "2026-08-29 10:42:46", str(mood["first_boot_after"]))
    soma = dl.classify(rd["lifetimes"], dl.parse_when("2026-08-29 13:24:08"))
    check("first boot after core/somatic.py's body cache (~13:24) = 2026-08-29 17:24:54 local",
          soma["first_boot_after"]["start_local"] == "2026-08-29 17:24:54", str(soma["first_boot_after"]))
    full = dl.load(REAL)
    check("the log is append-only: the first 284 lifetimes of the full file equal the snapshot's",
          [x["start"] for x in full["lifetimes"][:284]] == [x["start"] for x in rd["lifetimes"]]
          and full["counts"]["awake"] >= 284 and full["counts"]["shutdown"] >= 253)
else:
    print("  SKIP (data/nascence.log missing or shorter than the reference snapshot)")


def geometry_check():
    """F-2255: the four fallback sources switch from 100% null to populated inside exactly two lifetimes."""
    gt = Path(r"C:\Nascence\data\geometry_tuples.jsonl")
    print("\n[10] data/geometry_tuples.jsonl boundaries (--geometry; read-only, byte-snapshotted)")
    if not gt.exists() or not REAL.exists():
        print("  SKIP (files missing)")
        return
    size = gt.stat().st_size                          # snapshot first
    lts = dl.load(REAL)["lifetimes"]
    starts = [x["start"] for x in lts]
    aff = dl.classify(lts, dl.parse_when("2026-08-29 10:27:19"))["first_boot_after"]
    body = dl.classify(lts, dl.parse_when("2026-08-29 13:24:08"))["first_boot_after"]
    fb = {"reading", "inner_thought", "subconscious_synthesis", "active_imagination"}
    rows, read = [], 0
    with open(gt, "rb") as f:
        for raw in f:
            read += len(raw)
            if read > size:
                break
            r = json.loads(raw)
            if r.get("source") in fb:
                rows.append((r["ts"], r.get("body") is None, r.get("affect") is None))
    rows.sort()
    pre_aff = [x for x in rows if x[0] < aff["start"]]
    first_aff = min(x[0] for x in rows if not x[2])
    pre_body = [x for x in rows if x[0] < body["start"]]
    first_body = min(x[0] for x in rows if not x[1])
    cold = [x for x in rows if body["start"] <= x[0] < first_body]
    print(f"  four-source rows {len(rows)}; before the affect boot {len(pre_aff)}; "
          f"first non-null affect ts {first_aff:.1f} (+{first_aff - aff['start']:.0f} s); "
          f"first non-null body ts {first_body:.1f} (+{first_body - body['start']:.0f} s); {len(cold)} null body rows before it in that lifetime")
    nxt_aff = min((s for s in starts if s > aff["start"]), default=float("inf"))
    nxt_body = min((s for s in starts if s > body["start"]), default=float("inf"))
    check("every four-source row before the 10:42:46 boot is null on affect AND body", all(x[1] and x[2] for x in pre_aff))
    check("the first non-null affect row is inside the 10:42:46 lifetime, +76 s, ts 1787957042.9",
          aff["start"] <= first_aff < nxt_aff and round(first_aff - aff["start"]) == 76 and near(first_aff, 1787957042.9, 0.06))
    check("every four-source row before the 17:24:54 boot has body null", all(x[1] for x in pre_body))
    check("the first non-null body row is inside the 17:24:54 lifetime, +1015 s, ts 1787982109.4",
          body["start"] <= first_body < nxt_body and round(first_body - body["start"]) == 1015 and near(first_body, 1787982109.4, 0.06))
    check("28 null cold-start body rows precede it in that lifetime (F-2255)", len(cold) == 28 and all(x[1] for x in cold))


if "--geometry" in sys.argv[1:]:
    geometry_check()

print()
if failures:
    print(f"FAILED {len(failures)}: " + "; ".join(failures))
    sys.exit(1)
print("ALL PASSED")
