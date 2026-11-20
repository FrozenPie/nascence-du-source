#!/usr/bin/env python
"""adjacent_possible_read.py -- J-2519 (plan: pursuits; thought T-0106).

Question (docs/reviews/frontier_disciplines_2026-10-30.md section 8, Kauffman /
Bedau & Packard): does the set of things Du can do, ask and name in one step
keep expanding WITHOUT a world upgrade, or is every expansion explained by a
build (exogenous evolution)?

READ-ONLY. Zero LLM. Imports nothing from core/ or nodes/. Reads data/ files
and runs read-only `git log`. Writes only to --out (default: stdout + optional
JSON dump path given on the command line).

DECLARED BEFORE THE FIRST RUN (do not tune to the outcome)
----------------------------------------------------------
Honest scope: the REACHABLE set per day cannot be reconstructed read-only
(objects-present snapshots are not logged per day), so this measures the
REALISED adjacent possible: components Du actually touched in one step. That
is a lower bound on the reachable set, and the only thing persistence can be
tested on.

Component families (each component has a first-seen ts and a set of active ts):
  Q  frontier question       data/frontier.json questions[]: id; first=born;
                             active ts = {born, last_offered, last_seen}.
  D  deed affordance         data/hands_trace.jsonl dispatch[] with
                             decision == "FIRE": (family, norm(object), place).
  H  hand x place            data/hands_trace.jsonl hands[]: (hand, location).
  P  procedure near HELD     data/procedures_log.jsonl: key, first ts its rung is
                             >= "persisted" (one rung below held); active ts =
                             every later log event on that key.
  N  name the world lacks    data/missing_object_flags.jsonl: norm(phrase);
                             first = ts; active = every flag ts of that phrase.
  F  fieldcraft made thing   data/fieldcraft_ledger.jsonl: ("craft", craft) and
                             ("thing", deed, thing); active = every row ts.
Persistent novelty: a component whose first ts is on day d and that has an
active ts on or after first + PERSIST_DAYS (14 d). Components first seen after
END - 14 d are CENSORED (cannot be judged) and are excluded from persistence.

World-upgrade timeline: commits (read-only git log) touching UPGRADE_PATHS,
excluding the initial import commit INITIAL_COMMIT. Code reaches Du only at a
boot, so an upgrade's EFFECTIVE ts = the first "Nascence is awake." line in
data/nascence.log at or after the commit ts. A component is ALIGNED if its first
ts lies in [effective, effective + ALIGN_DAYS] for any upgrade; else UNALIGNED.
Sensitivity (reported, not the verdict): alignment by raw commit ts.

Analysis window: first ts >= WINDOW_START (git history start; earlier upgrades are
invisible so earlier components cannot be classified) and <= END - 14 d.
Running days: local days with >= 1 hands_trace row.

Verdict rules (on persistent novelty, all families pooled, primary alignment):
  UNDETERMINED  if unaligned running days < MIN_UNALIGNED_DAYS (the world changes
                so often there is no unaligned stretch to test).
  FALSIFIED     (exogenous) if unaligned persistent count == 0 or the unaligned
                rate per unaligned running day <= NOISE_RATE.
  ENDOGENOUS    otherwise.
Curve shape (unaligned persistent rate, second half vs first half of window):
  SATURATING if ratio < 0.5; DECELERATING if 0.5 <= ratio < 0.8; OPEN if >= 0.8.
"""
import json, re, subprocess, sys, time, collections, os, datetime

ROOT = r"C:\Nascence"
PERSIST_DAYS = 14
ALIGN_DAYS = 3
NOISE_RATE = 1 / 7          # persistent components per unaligned running day
MIN_UNALIGNED_DAYS = 7
INITIAL_COMMIT = "8eef0bb9"
WINDOW_START = "2026-08-28"  # day after the initial git import (2026-08-27)
UPGRADE_PATHS = [            # briefing set + every world-content / hands module
    "core/actions.py", "core/hands.py", "core/fieldcraft.py",
    "core/garden*.py", "core/cat*.py", "core/shore_life.py", "core/wood_life.py",
    "core/study_life.py", "core/world_content_*.py", "core/world_objects.py",
    "core/world_detail.py", "core/soundscape.py", "core/weather_conditions.py",
    "core/letters.py", "core/practical_lesson.py", "docs/staged/*upgrade*.md",
]
DAY = 86400.0
_DET = {"the", "a", "an", "my", "some", "this", "that", "his", "her", "its", "these", "those", "more"}


def norm(s):
    w = re.sub(r"[^\w\s']", " ", (s or "").lower()).split()
    while w and w[0] in _DET:
        w = w[1:]
    return " ".join(w)


def day(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def jl(path):
    with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


def collect():
    comp = collections.defaultdict(lambda: {"first": None, "act": []})

    def add(key, ts, first=False):
        if ts is None:
            return
        c = comp[key]
        if first or c["first"] is None or ts < c["first"]:
            c["first"] = ts if c["first"] is None else min(c["first"], ts)
        c["act"].append(ts)

    run_days, n_trace = set(), 0
    for r in jl("data/hands_trace.jsonl"):
        ts = r.get("ts"); n_trace += 1
        if not ts:
            continue
        run_days.add(day(ts))
        loc = r.get("location") or "?"
        for d in r.get("dispatch") or []:
            if isinstance(d, dict) and d.get("decision") == "FIRE":
                add(("D", d.get("family"), norm(d.get("object")), loc), ts)
        for h in r.get("hands") or []:
            if isinstance(h, dict) and h.get("hand"):
                add(("H", h["hand"], loc), ts)
    fr = json.load(open(os.path.join(ROOT, "data/frontier.json"), encoding="utf-8"))
    for q in fr.get("questions", []):
        k = ("Q", q["id"])
        for f in ("born", "last_offered", "last_seen"):
            add(k, q.get(f))
    near = {}
    order = ["occurred", "persisted", "held", "held_under_pressure"]
    for r in jl("data/procedures_log.jsonl"):
        key, ts, rung = r.get("key"), r.get("ts"), r.get("rung")
        if not key or not ts:
            continue
        if key not in near and rung in order and order.index(rung) >= 1:
            near[key] = ts
        if key in near:
            add(("P", key), ts)
    for r in jl("data/missing_object_flags.jsonl"):
        add(("N", norm(r.get("phrase"))), r.get("ts"))
    for r in jl("data/fieldcraft_ledger.jsonl"):
        if r.get("craft"):
            add(("F", "craft", r["craft"]), r.get("ts"))
        if r.get("thing"):
            add(("F", "thing", r.get("deed"), norm(r["thing"])), r.get("ts"))
    return comp, run_days, n_trace


def boots():
    out = []
    pat = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ \[nascence\.main\] Nascence is awake\.")
    with open(os.path.join(ROOT, "data/nascence.log"), encoding="utf-8", errors="replace") as f:
        for line in f:
            if "Nascence is awake." in line:
                m = pat.match(line)
                if m:
                    out.append(time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")))
    return sorted(out)


def upgrades():
    cmd = ["git", "-C", ROOT, "log", "--format=%h|%ct|%s", "--"] + UPGRADE_PATHS
    rows = []
    for line in subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8").stdout.splitlines():
        h, ct, s = line.split("|", 2)
        if h.startswith(INITIAL_COMMIT[:7]):
            continue
        rows.append((h, float(ct), s))
    return sorted(rows, key=lambda r: r[1])


def main():
    comp, run_days, n_trace = collect()
    bt = boots()
    ups = upgrades()
    end = max(max(c["act"]) for c in comp.values() if c["act"])
    w0 = time.mktime(time.strptime(WINDOW_START, "%Y-%m-%d"))
    wend = end - PERSIST_DAYS * DAY
    eff = []
    for h, ct, s in ups:
        b = next((x for x in bt if x >= ct), None)
        if b is not None:
            eff.append((h, ct, b, s))
    eff_ts = sorted(set(e[2] for e in eff))
    raw_ts = sorted(set(e[1] for e in eff))

    def aligned(ts, marks):
        return any(m <= ts <= m + ALIGN_DAYS * DAY for m in marks)

    win_days = sorted(d for d in run_days if WINDOW_START <= d <= day(wend))
    al_days = {d for d in win_days if aligned(time.mktime(time.strptime(d + " 12:00", "%Y-%m-%d %H:%M")), eff_ts)
               or any(day(m + k * DAY) == d for m in eff_ts for k in range(ALIGN_DAYS + 1))}
    un_days = [d for d in win_days if d not in al_days]
    half = win_days[len(win_days) // 2] if win_days else WINDOW_START

    fam = collections.defaultdict(lambda: collections.Counter())
    unaligned_list = []
    cum = collections.Counter()
    for k, c in comp.items():
        f = c["first"]
        if f is None or not (w0 <= f):
            continue
        F = k[0]
        if f > wend:
            fam[F]["censored"] += 1
            continue
        pers = any(t >= f + PERSIST_DAYS * DAY for t in c["act"])
        a = aligned(f, eff_ts); ar = aligned(f, raw_ts)
        fam[F]["new"] += 1
        if pers:
            fam[F]["persistent"] += 1
            fam[F]["pers_aligned" if a else "pers_unaligned"] += 1
            fam[F]["pers_unaligned_rawcommit"] += 0 if ar else 1
            cum[day(f)] += 1
            if not a:
                second = day(f) >= half
                fam[F]["unal_h2" if second else "unal_h1"] += 1
                unaligned_list.append({"id": list(k), "first": day(f), "last_active": day(max(c["act"])),
                                       "n_active": len(c["act"])})
    # size of the adjacent possible per running day (components open: first <= d <= last active)
    size = {}
    spans = [(day(c["first"]), day(max(c["act"])), k[0]) for k, c in comp.items() if c["first"] and c["act"]]
    for d in win_days:
        cnt = collections.Counter(F for a, b, F in spans if a <= d <= b)
        size[d] = dict(cnt)
    tot = collections.Counter()
    for F, c in fam.items():
        tot.update(c)
    nu, na = len(un_days), len(al_days)
    rate_u = tot["pers_unaligned"] / nu if nu else None
    rate_a = tot["pers_aligned"] / na if na else None
    if nu < MIN_UNALIGNED_DAYS:
        verdict = "UNDETERMINED"
    elif tot["pers_unaligned"] == 0 or rate_u <= NOISE_RATE:
        verdict = "FALSIFIED (exogenous)"
    else:
        verdict = "ENDOGENOUS"
    h1d = [d for d in un_days if d < half]; h2d = [d for d in un_days if d >= half]
    r1 = tot["unal_h1"] / len(h1d) if h1d else None
    r2 = tot["unal_h2"] / len(h2d) if h2d else None
    shape = None
    if r1:
        ratio = (r2 or 0) / r1
        shape = "SATURATING" if ratio < 0.5 else ("DECELERATING" if ratio < 0.8 else "OPEN")
    weekly = collections.OrderedDict()
    for d in win_days:
        wk = datetime.date.fromisoformat(d).isocalendar()
        key = "%d-W%02d" % (wk[0], wk[1])
        weekly.setdefault(key, size[d])
    res = {
        "trace_rows": n_trace, "components_total": len(comp), "boots": len(bt),
        "window": [WINDOW_START, day(wend)], "data_end": day(end), "half_split_day": half,
        "upgrade_commits": len(ups), "upgrade_commits_effective": len(eff), "distinct_effective_boots": len(eff_ts),
        "running_days_in_window": len(win_days), "aligned_days": na, "unaligned_days": nu,
        "unaligned_day_list": un_days,
        "by_family": {F: dict(c) for F, c in sorted(fam.items())}, "total": dict(tot),
        "rate_persistent_per_unaligned_day": rate_u, "rate_persistent_per_aligned_day": rate_a,
        "unaligned_rate_h1": r1, "unaligned_rate_h2": r2, "curve_shape": shape, "verdict": verdict,
        "cumulative_persistent_by_day": dict(sorted(cum.items())),
        "adjacent_possible_size_weekly_first_day": weekly,
        "unaligned_components": sorted(unaligned_list, key=lambda x: x["first"]),
        "upgrade_timeline": [{"commit": h, "commit_day": day(ct), "effective_boot": day(b), "subject": s[:90]}
                             for h, ct, b, s in eff],
    }
    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out:
        json.dump(res, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    brief = {k: v for k, v in res.items() if k not in ("unaligned_components", "upgrade_timeline",
                                                      "cumulative_persistent_by_day", "unaligned_day_list")}
    print(json.dumps(brief, indent=1, ensure_ascii=False))
    print("unaligned components:", len(unaligned_list))


if __name__ == "__main__":
    main()
