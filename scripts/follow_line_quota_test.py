"""Hermetic test for J-4081 (D-0780 b): daily quota on Follow Line consequence re-boarding. Temp-path stores only."""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import follow_line as fl, frontier as fr, coupling_rides as cr
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate, _hash_file

ok = True
def check(n, c):
    global ok; ok = ok and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")

LIVE = Path(r"C:\Nascence\data")
CAN = [LIVE / "frontier.json", LIVE / "frontier.light.json", LIVE / "logs" / "follow_line_shadow.jsonl"]
DEF = (fl.CONSEQUENCE_DAILY_QUOTA, fl.CONSEQUENCE_QUOTA_MODE)
before = [_hash_file(p) for p in CAN]
qlog_live = LIVE / "logs" / "follow_line_consequence_quota.jsonl"
existed = qlog_live.exists()

def rows(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []

with isolate(also=[(fr, ["_F", "_SEM_SHADOW_LOG"]), (fl, ["SHADOW_LOG", "CONS_QUOTA_LOG"]), (cr, ["_LOG"])], db="empty") as lab:
    fr.FRONTIER_SEMANTIC_MERGE = None
    cr._DATA = lab
    fl.FOLLOW_LINE = "live"
    fl.CONSEQUENCE_DAILY_QUOTA = 3
    n = [0]
    def cons(src="consequence", **kw):
        n[0] += 1
        return fl.board(f"if the tide turns then thing number {n[0]} unique zebra{n[0]} follows", src, kind="claim",
                        asked_by={"about_key": f"k{n[0]}"}, depth=1, guard=False, **kw)
    fl._cons_log.clear()
    fl.CONSEQUENCE_QUOTA_MODE = "enforce"
    got = [cons() for _ in range(5)]
    check("enforce: first 3 board, 4th and 5th refused", [bool(g) for g in got] == [True, True, True, False, False])
    r = rows(fl.CONS_QUOTA_LOG)
    check("enforce: 2 refused rows logged with quota/used", len(r) == 2 and r[0]["outcome"] == "refused" and r[0]["used_24h"] == 3 and r[0]["quota"] == 3)
    ask = [fl.board(f"why does the moon wobble variant number {i} quokka{i}", "asked", kind="question") for i in range(6)]
    check("asked boarding is uncapped by the quota", all(ask))
    cl = fl.board("a claim of his own, wholly distinct parrot", "claim", kind="claim")
    check("claim boarding uncapped", bool(cl))
    # window expiry
    fl._cons_log.clear(); fl._cons_log.extend([fl._now() - fl.CONS_QUOTA_WINDOW_S - 5] * 3)
    check("entries older than 24h expire", bool(cons()))
    # shadow mode
    fl._cons_log.clear(); fl.CONSEQUENCE_QUOTA_MODE = "shadow"
    before_n = len(rows(fl.CONS_QUOTA_LOG))
    got = [cons() for _ in range(5)]
    r = rows(fl.CONS_QUOTA_LOG)[before_n:]
    check("shadow: all 5 board, 2 would_refuse rows logged", all(bool(g) for g in got) and [x["outcome"] for x in r] == ["would_refuse"] * 2)
    # off mode
    fl._cons_log.clear(); fl.CONSEQUENCE_QUOTA_MODE = "off"; before_n = len(rows(fl.CONS_QUOTA_LOG))
    got = [cons() for _ in range(5)]
    check("off: all board, nothing logged, nothing counted", all(bool(g) for g in got) and len(rows(fl.CONS_QUOTA_LOG)) == before_n and not fl._cons_log)
check("module defaults are quota 48, enforce", DEF == (48, "enforce"))
after = [_hash_file(p) for p in CAN]
check("CANARY: live stores byte-identical", before == after)
check("CANARY: live quota log not created", qlog_live.exists() == existed)
print("\nALL PASS" if ok else "\nFAILURES"); sys.exit(0 if ok else 1)
