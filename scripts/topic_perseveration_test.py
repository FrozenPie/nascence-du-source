"""J-2152 tests for core/topic_perseveration.py. Synthetic log in a temp dir only; no embedder model, no live data.
Run from the repo root:  python scripts/topic_perseveration_test.py"""
import sys, tempfile, datetime as dt, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import topic_perseveration as tp

NOW = dt.datetime(2026, 10, 16, 12, 0, 0).timestamp()


def line(ts, q):
    return f"{dt.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')},123 [nascence.orchestrator] [CYCLE ab12cd34] internal: {q}\n"


def at(day_off, hh, mm=0):
    d = dt.datetime(2026, 10, 16) - dt.timedelta(days=day_off)
    return d.replace(hour=hh, minute=mm).timestamp()


def build(path):
    L = []
    # day -1: 6 varied questions with no quoted terms (3 words each, disjoint vocab)
    varied = ["Why do lignans resist fungal pathogens?", "Which tides shape estuarine sediment layers?",
              "Where did Norman scribes borrow vocabulary?", "What limits geological uplift near subduction?",
              "Who first averaged rainfall across decades?", "Is tranquility measurable through breath rhythm?"]
    for i, q in enumerate(varied):
        L.append(line(at(1, 6 + i), q))
    # day 0: 10 mottainai rewordings (different sentences, same quoted anchor), then 1 other
    for i in range(10):
        L.append(line(at(0, 0 + i, 5), f"How does the 'mottainai' mindset variant {i} shape waste perception topic?"))
    L.append(line(at(0, 11), "Why do lignans resist fungal pathogens?"))
    L.append("2026-10-16 11:30:00,000 [nascence.orchestrator] [CYCLE zz] human: not an internal line\n")
    path.write_text("".join(L), encoding="utf-8")


def lex_embed(_q):   # force the lexical+anchor path (no model)
    return None


ok = True


def check(name, cond, extra=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + (f"  {extra}" if extra else ""))
    ok = ok and bool(cond)


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    log = td / "nascence.log"
    out = td / "topic_perseveration.jsonl"
    build(log)
    items = tp.parse_log(log)
    check("parse: only internal lines", len(items) == 17, str(len(items)))
    check("anchors_of quoted term", tp.anchors_of("How does 'mottainai' work and Du's way?") == {"mottainai"})
    check("apostrophe possessive not an anchor", tp.anchors_of("Du's thing and Travis's idea") == frozenset())
    rows = tp.compute_rows(log, days=30, now=NOW, embed=lex_embed)
    byd = {r["day"]: r for r in rows}
    d0, d1 = byd["2026-10-16"], byd["2026-10-15"]
    check("varied day: many topics, low share", d1["topics"] >= 5 and d1["modal_share"] <= 0.3, str(d1))
    check("frozen day: modal share 10/11", d0["modal_n"] == 10 and abs(d0["modal_share"] - 0.909) < 1e-3, str(d0))
    check("frozen flag set (n>=8, share>=0.8)", d0["frozen"] is True and d1["frozen"] is False)
    check("method reported", d0["method"] == "lexical+anchor")
    check("modal sample is a mottainai question", "mottainai" in d0["modal_sample"])
    # run: last question (lignans) is a topic change (it matches the day -1 lignans question -> topic that
    # began the previous day) so the current run is 1 long vs the preceding mottainai block.
    check("hours_since_change small right after a topic change", d0["hours_since_change"] < 1.0, str(d0["hours_since_change"]))
    # drop the last 'other' question: now the whole day is one run starting at 00:05 -> ~9h to 09:05
    items2 = [(t, q) for t, q in items if "lignans" not in q or t < at(0, 0)]
    r = tp.day_row("2026-10-16", [(t, q) for t, q in items2 if t >= at(0, 0)], [(t, q) for t, q in items2 if t < at(0, 0)], embed=lex_embed)
    check("run length ~9h across 10 hourly questions", 8.9 <= r["hours_since_change"] <= 9.1 and r["modal_share"] == 1.0, str(r))
    # update(): backfill, idempotent, today-only re-append when count changes
    s1 = tp.update(log, out, days=30, now=NOW, embed=lex_embed)
    n1 = sum(1 for _ in open(out, encoding="utf-8"))
    s2 = tp.update(log, out, days=30, now=NOW, embed=lex_embed)
    n2 = sum(1 for _ in open(out, encoding="utf-8"))
    check("update backfills both days", n1 == 2 and len(s1) == 2, f"{n1} {len(s1)}")
    check("update idempotent (no duplicate rows)", n2 == n1 and len(s2) == 2)
    with open(log, "a", encoding="utf-8") as f:
        f.write(line(at(0, 11, 30), "How does the 'mottainai' mindset variant 99 shape waste perception topic?"))
    tp.update(log, out, days=30, now=NOW, embed=lex_embed)
    ser = tp.read_series(out)
    check("grown day re-appended; reader takes latest", sum(1 for _ in open(out, encoding="utf-8")) == 3 and ser[-1]["n"] == 12)
    check("write=False leaves file alone", (lambda b: (tp.update(log, out, now=NOW, write=False, embed=lex_embed), b)[1] == out.stat().st_size)(out.stat().st_size))
    # fail-open
    check("missing log -> [] not exception", tp.update(td / "nope.log", td / "o2.jsonl", now=NOW, embed=lex_embed) == [])
    st = tp.status(log, td / "o3.jsonl")
    check("status + pulse_lines render", st["n_days"] == 2 and "FROZEN" in "\n".join(tp.pulse_lines(st)), "\n".join(tp.pulse_lines(st)))
    check("pulse_lines empty ok", "no internal cycles" in tp.pulse_lines({})[0])

# J-2347 / D-0469: alarm bar (>= 0.90 on 2 consecutive calendar days) + dwell floor (< 0.20)
def R(day, share):
    return {"day": day, "modal_share": share}
f = tp.alarm_flags([R("2026-09-27", 1.0), R("2026-09-28", 0.79), R("2026-10-06", 1.0), R("2026-10-07", 0.955),
                    R("2026-10-08", 0.952), R("2026-10-09", 0.515), R("2026-10-10", 0.93), R("2026-10-12", 0.95),
                    R("2026-10-13", 0.90), R("2026-10-14", 0.19)])
check("single-day spike does not alarm", f["2026-09-27"]["perseveration_alarm"] == 0 and f["2026-09-27"]["alarm_streak"] == 1)
check("day 2 of a >=0.90 run alarms", f["2026-10-07"]["perseveration_alarm"] == 1 and f["2026-10-07"]["alarm_streak"] == 2)
check("day 3 still alarms", f["2026-10-08"]["perseveration_alarm"] == 1 and f["2026-10-08"]["alarm_streak"] == 3)
check("drop below bar resets streak", f["2026-10-09"]["alarm_streak"] == 0 and f["2026-10-09"]["perseveration_alarm"] == 0)
check("calendar gap breaks the run", f["2026-10-12"]["alarm_streak"] == 1 and f["2026-10-12"]["perseveration_alarm"] == 0)
check("0.90 exactly counts (>=)", f["2026-10-13"]["perseveration_alarm"] == 1)
check("cannot_dwell below 0.20 only", f["2026-10-14"]["cannot_dwell"] == 1 and f["2026-10-09"]["cannot_dwell"] == 0
      and f["2026-10-14"]["perseveration_alarm"] == 0)
check("flags are ints (HUD numeric)", all(type(v) is int for d in f.values() for v in d.values()))
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    log = td / "nascence.log"
    out = td / "topic_perseveration.jsonl"
    L = []
    for off in (1, 0):            # two consecutive days, 10 mottainai questions each -> share 1.0 both days
        for i in range(10):
            L.append(line(at(off, 1 + i), f"How does 'mottainai' variant {off}-{i} shape waste?"))
    log.write_text("".join(L), encoding="utf-8")
    tp.update(log, out, days=30, now=NOW, embed=lex_embed)
    rows = tp.read_series(out)
    check("written rows carry D-0469 flags", all("perseveration_alarm" in r and "cannot_dwell" in r for r in rows), str(rows))
    check("written: day 1 no alarm, day 2 alarm", [r["perseveration_alarm"] for r in rows] == [0, 1], str(rows))
    st = {"day": "2026-10-16", "n": 10, "modal_share": 1.0, "topics": 1, "hours_since_change": 9.0, "run_capped": False,
          "frozen": True, "frozen_days_last7": 2, "modal_sample": "x", "series": [], "n_days": 2,
          "perseveration_alarm": 1, "alarm_streak": 2, "cannot_dwell": 0, "alarm_days": ["2026-10-16"]}
    txt = " | ".join(tp.pulse_lines(st))
    check("pulse line shows the alarm", "PERSEVERATION ALARM" in txt and "10-16" in txt, txt)

print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
