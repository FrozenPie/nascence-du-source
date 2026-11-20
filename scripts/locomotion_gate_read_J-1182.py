"""J-1182: read of J-1179's declined-redirect fix (and D-0224's defeater) on the live log -- a re-runnable form.

READ-ONLY.  Opens data/nascence.log and data/hands_trace.jsonl with mode 'rb' and parses core/locomotion.py and
core/sensorium.py with ast/regex (nothing is imported from the live tree).  Writes nothing; prints a report.  Du is
live and appending to both files, so a SNAPSHOT line number is taken from the log first and every number comes from
that one cut (use --max-line N to reproduce a previous read exactly).

Usage (from any directory):
    python scripts/locomotion_gate_read_J-1182.py gate   [--commit 5a66504]
    python scripts/locomotion_gate_read_J-1182.py read   [--commit 5a66504] [--max-line N] [--sections a,b,...]
Sections: gate, teleport, walk, rates, replay, realstate, latch, laterleg   (default: all)

What each section is (see findings F-1767.. recorded by J-1182 for the numbers it produced on 2026-10-03):
  gate       live-days on runs that START at/after the commit.  A run starts at 'Nascence is awake'; it ends at the next
             'Nascence shutting down' (clean) or, if the next 'is awake' comes with no shutdown between (unclean), at the
             last timestamped line BEFORE THE NEXT BOOT'S FIRST LINE ('Memory store initialised').  The older helper
             closed an unclean run at the last line before the next 'is awake' line, but a new process logs ~40 s of
             startup lines BEFORE that line, so a dead gap was counted as live (the 2026-09-30 20:28 run: 58.4 h
             instead of 10.8 h; S-0162 / S-0241).  NZ local clock handled across the 2026-09-27 DST switch.
  teleport   '[monologue] DISPATCH move' narrations classified LEG / INSTANT / gate-school / STANDPOINT (F-1653's scan,
             with the study-arrival head it missed) over the pre-fix era, the teleport era and the counted runs.
  walk       F-1653 evidence 4: hands_trace 'location' samples after every fired move decision must walk the journey's
             own path in order (never off it, never back, never ARRIVING before the cumulative base leg seconds), the
             decline rows must not show the declined destination, and every location change must have a cause.
  rates      distinct decline decisions per live-day (same (dest, existing, reason) <= 5 s collapsed), decomposed into
             same-cycle echoes / standalone; first-leg geometry, insistence, fate of the wish; caller attribution.
  replay     F-1418's replay (reconstructed; reproduces its published baseline cell for cell -- run with --validate) over
             the counted runs, weekly baselines, and the F-1658 total with the decline lines added.
  realstate  model-free cross-check: classify each fired decision by the REAL state (its own trace row = true location),
             pre-gate era vs counted runs.
  latch      'he chose to GO ...' lines that follow a decline within 2 s; move-family dispatch decisions in the trace.
  laterleg   later-leg redirects: displacement of declined wishes, per-run rates, wood reachability, oscillation.
"""
import argparse
import ast
import bisect
import datetime as dt
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

DATA = os.environ.get("NASCENCE_DATA", r"C:\Nascence\data")
CODE = os.environ.get("NASCENCE_CODE", r"C:\Nascence")
LOG = os.path.join(DATA, "nascence.log")
TRACE = os.path.join(DATA, "hands_trace.jsonl")

CHAIN = ["study", "garden", "wood", "shore"]
PLACES = set(CHAIN)
EDGES = {("study", "garden"): 20, ("garden", "study"): 20, ("garden", "wood"): 70, ("wood", "garden"): 85,
         ("wood", "shore"): 70, ("shore", "wood"): 90}
PHRASE2DEST = {"GO TO THE WOOD": "wood", "GO DOWN TO THE SHORE": "shore", "GO OUT TO THE GARDEN": "garden",
               "COME INSIDE": "study"}
EPOCH0 = dt.datetime(1970, 1, 1)
TS = re.compile(rb"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3}) ")
RE_ACT = re.compile(r"\[monologue\] ACT move -> (.+?) \((.*)\)\s*$")
RE_CHOSE = re.compile(r"\[monologue\] he chose to (GO TO THE WOOD|GO DOWN TO THE SHORE|GO OUT TO THE GARDEN|COME INSIDE)")
RE_DISP = re.compile(r"\[monologue\] DISPATCH move \u2014 (.*)$")
RE_DECL = re.compile(r"\[locomotion\] redirect declined: (study|garden|wood|shore) while journey to (study|garden|wood|shore) \((same-dest|first-leg)\)")
RE_SYSO = re.compile(r"\[locomotion\] system redirect overrides first leg: (\w+) replaces journey to (\w+)")

# the baselines the job brief names (F-1654, re-derived over 2026-08-15 .. 09-13 09:09, 22.55 live-days)
BASE_LD = 22.55
BASE = {"decisions": 2296 / BASE_LD, "cross": 196 / BASE_LD, "first": 58 / BASE_LD, "first_third": 37 / BASE_LD,
        "later": 138 / BASE_LD, "same": 324 / BASE_LD}


# ------------------------------------------------------------------ time helpers (NZ local, DST-aware for 2026)
def _off_hours_local(naive):
    return 13 if (naive < dt.datetime(2026, 4, 5, 3) or naive >= dt.datetime(2026, 9, 27, 3)) else 12


def local_epoch(s):
    fmt = "%Y-%m-%d %H:%M:%S" if s.count(":") == 2 else "%Y-%m-%d %H:%M"
    naive = dt.datetime.strptime(s, fmt)
    return (naive - dt.timedelta(hours=_off_hours_local(naive)) - EPOCH0).total_seconds()


def epoch_local_str(e):
    utc = EPOCH0 + dt.timedelta(seconds=e)
    off = 13 if (utc < dt.datetime(2026, 4, 4, 14) or utc >= dt.datetime(2026, 9, 26, 14)) else 12
    return (utc + dt.timedelta(hours=off)).strftime("%Y-%m-%d %H:%M:%S")


def naive_to_epoch(naive, ms=0):
    return (naive - dt.timedelta(hours=_off_hours_local(naive)) - EPOCH0).total_seconds() + ms / 1000.0


def school_confined(t):
    """core/school.py confined_to_study() by its own constants: weekdays 09:00-12:45 local, 45-minute periods rotating
    reading, math, nature, composition, music; every desk subject (all but nature) confines him to the study."""
    loc = dt.datetime.strptime(epoch_local_str(t), "%Y-%m-%d %H:%M:%S")
    if loc.weekday() >= 5:
        return False
    h = loc.hour + loc.minute / 60.0
    if not (9 <= h < 12.75):
        return False
    mins = max(0, (loc.hour - 9) * 60 + loc.minute)
    return ["reading", "math", "nature", "composition", "music"][(mins // 45) % 5] != "nature"


def path_between(cur, dest):
    """core/locomotion._path_between"""
    if cur not in CHAIN or dest not in CHAIN or cur == dest:
        return []
    a, b = CHAIN.index(cur), CHAIN.index(dest)
    step = 1 if b > a else -1
    return CHAIN[a + step: b + step: step] if step == 1 else CHAIN[a - 1: (b - 1 if b > 0 else None): -1]


def cum_secs(P, loc, dest):
    """base seconds from P to reach `loc` on the path P -> dest (0 if loc == P; None if off the path)"""
    if loc == P:
        return 0
    a, tot = P, 0
    for p in path_between(P, dest):
        tot += EDGES[(a, p)]
        a = p
        if p == loc:
            return tot
    return None


# ------------------------------------------------------------------ one pass over the log
def read_log(max_line=None):
    """-> (events, runs, snapshot).  events: only the move/locomotion/sleep lines this read needs."""
    events, runs = [], []
    cur = None
    last_ts = None
    last_naive = None
    pre_marker_ts = None
    pre_marker_line = 0
    marker_ts = None
    nlines = nbytes = 0
    with open(LOG, "rb") as f:
        for ln, raw in enumerate(f, 1):
            if max_line is not None and ln > max_line:
                break
            nlines = ln
            nbytes += len(raw)
            m = TS.match(raw)
            if not m:
                continue
            naive = dt.datetime.strptime(m.group(1).decode(), "%Y-%m-%d %H:%M:%S")
            ms = int(m.group(2))
            e = naive_to_epoch(naive, ms)
            is_awake = b"Nascence is awake" in raw
            is_shut = b"Nascence shutting down" in raw
            is_pre = b"Memory store initialised" in raw
            if is_pre:
                pre_marker_ts, pre_marker_line, marker_ts = last_naive, ln, naive
            if is_awake:
                if cur is not None:
                    end = last_naive
                    if (pre_marker_ts is not None and pre_marker_line > cur["start_line"]
                            and 0 <= (naive - marker_ts).total_seconds() <= 300):
                        end = pre_marker_ts
                    cur["end"], cur["how"], cur["end_naive_rule"] = end, "unclean", last_naive
                    runs.append(cur)
                cur = {"start": naive, "end": None, "how": "open", "start_line": ln}
            elif is_shut and cur is not None:
                cur["end"], cur["how"] = naive, "clean"
                runs.append(cur)
                cur = None
            last_naive = naive
            last_ts = f"{m.group(1).decode()},{m.group(2).decode()}"
            if not (is_awake or is_shut or is_pre or b"[monologue] ACT move" in raw or b"[monologue] he chose to" in raw
                    or b"[monologue] DISPATCH move" in raw or b"[nascence.locomotion]" in raw
                    or b"entering Sleep State" in raw or b"[night] waking" in raw):
                continue
            body = raw.decode("utf-8", errors="replace").rstrip("\r\n")[24:]
            ev = {"ln": ln, "t": m.group(1).decode() + "," + m.group(2).decode(), "e": round(e, 3)}
            if is_awake:
                ev["k"] = "AWAKE"
            elif is_shut:
                ev["k"] = "SHUT"
            elif is_pre:
                ev["k"] = "PRELUDE"
            elif (mm := RE_ACT.search(body)):
                ev.update(k="ACT", dest=mm.group(1), obj=mm.group(2))
            elif (mm := RE_CHOSE.search(body)):
                ev.update(k="CHOSE", phrase=mm.group(1))
            elif (mm := RE_DISP.search(body)):
                ev.update(k="DISP", text=mm.group(1))
            elif (mm := RE_DECL.search(body)):
                ev.update(k="DECL", dest=mm.group(1), exist=mm.group(2), why=mm.group(3))
            elif (mm := RE_SYSO.search(body)):
                ev.update(k="SYSO", dest=mm.group(1), exist=mm.group(2))
            elif "entering Sleep State" in body:
                ev["k"] = "SLEEP"
            elif "[night] waking" in body:
                ev["k"] = "WAKE"
            else:
                continue
            events.append(ev)
    if cur is not None:
        cur["end"], cur["how"] = last_naive, "open"
        runs.append(cur)
    for r in runs:
        r["a"] = naive_to_epoch(r["start"])
        r["b"] = naive_to_epoch(r["end"])
    return events, runs, {"lines": nlines, "bytes": nbytes, "last_ts": last_ts}


def read_trace():
    rows = []
    with open(TRACE, "rb") as f:
        for raw in f:
            try:
                r = json.loads(raw)
            except Exception:
                continue
            if r.get("location"):
                rows.append(r)
    return rows


class Ctx:
    def __init__(self, commit, max_line):
        self.events, self.runs, self.snap = read_log(max_line)
        self.rows = read_trace()
        self.row_ts = [r["ts"] for r in self.rows]
        iso = subprocess.check_output(["git", "-C", CODE, "log", "-1", "--format=%cI", commit]).decode().strip()
        t0 = dt.datetime.fromisoformat(iso).astimezone(dt.timezone.utc).replace(tzinfo=None)
        self.commit, self.iso, self.t0 = commit, iso, (t0 - EPOCH0).total_seconds()
        self.fixed = [(r["a"], r["b"]) for r in self.runs if r["a"] >= self.t0]
        self.hours = [(b - a) / 3600 for a, b in self.fixed]
        self.D = sum(self.hours) / 24
        self.D_act = sum(self.hours[:2]) / 24          # runs before the 2026-09-28 19:08 restart (movement regime A)
        self.D_qui = sum(self.hours[2:]) / 24
        self.K = {}                                    # key numbers for the closing summary
        self.ACTS = [e for e in self.events if e["k"] == "ACT" and e["dest"] in PLACES]
        self.CHOS = [e for e in self.events if e["k"] == "CHOSE"]
        self.DECL = [e for e in self.events if e["k"] == "DECL"]
        self.SYSO = [e for e in self.events if e["k"] == "SYSO"]
        self.SLEEP = [e for e in self.events if e["k"] == "SLEEP"]
        self.WAKE = [e for e in self.events if e["k"] == "WAKE"]
        self.DISP = [e for e in self.events if e["k"] == "DISP"]
        self._heads()

    def _heads(self):
        src = open(os.path.join(CODE, "core", "locomotion.py"), encoding="utf-8").read()
        leg = None
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_LEG_LINES" for t in node.targets):
                leg = ast.literal_eval(node.value)
        self.leg_heads = [(l[:44], frm, to) for (frm, to), lines in leg.items() for l in lines]
        ssrc = open(os.path.join(CODE, "core", "sensorium.py"), encoding="utf-8").read()
        self.standpoint_heads = []
        for node in ast.walk(ast.parse(ssrc)):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                tgt = node.targets[0] if isinstance(node, ast.Assign) else node.target
                if getattr(tgt, "id", "") == "_STANDPOINT_LINES":
                    self.standpoint_heads = [v[:40] for v in ast.literal_eval(node.value).values()]
        flat = re.sub(r'"\s*\n\s*"', "", ssrc)
        self.instant_heads = [
            "You climb up off the shore and the trees close over you",
            "You go down the path from the garden and the trees close over you",
            "You go on down through the trees and out onto the shore",
            "You go down the steep path below the garden to the shore",
            "You climb the path back up out of the wood to the garden",
            "You climb the path back up from the shore to the garden",
            "You leave the study and go out",
            "You come in from outside; the door shuts the weather out behind you",
        ]
        for frag in ("You climb up off the shore and the trees close over you", "You climb the path back up ", "out of the wood ",
                     "from the shore ", "You come in from outside; the door shuts the weather out behind you"):
            assert frag in flat, "instant-move text not found in core/sensorium.py: " + frag

    def classify_narration(self, text):
        for h in self.instant_heads:
            if text.startswith(h[:len(text)] if len(text) < len(h) else h):
                return "INSTANT"
        if len(text) >= 20:
            for h, _f, _t in self.leg_heads:
                if text.startswith(h[:min(len(h), len(text))]):
                    return "LEG"
            for h in self.standpoint_heads:
                if text.startswith(h[:min(len(h), len(text))]):
                    return "STANDPOINT"
        if text.startswith("You go to the mailbox") or text.startswith("You half-rise to go out"):
            return "gate/school"
        return "other"

    def leg_of(self, text):
        if len(text) >= 20:
            for h, frm, to in self.leg_heads:
                if text.startswith(h[:min(len(h), len(text))]):
                    return frm, to
        return None

    def in_fixed(self, e):
        return any(a <= e <= b for a, b in self.fixed)

    def run_of(self, e):
        for n, (a, b) in enumerate(self.fixed, 1):
            if a <= e <= b:
                return n
        return None

    def live_days(self, lo, hi):
        tot = 0.0
        for r in self.runs:
            x, y = max(r["a"], lo), min(r["b"], hi)
            if y > x:
                tot += y - x
        return tot / 86400.0

    def own_row(self, t, tol=6.0):
        k = bisect.bisect_left(self.row_ts, t - 1.0)
        return self.rows[k] if k < len(self.rows) and self.rows[k]["ts"] - t < tol else None

    # ---- F-1418 decisions / collapse / replay (reconstruction validated against the published baseline)
    def decisions(self, t_lo, t_hi):
        out = []
        for e in self.ACTS:
            if t_lo <= e["e"] <= t_hi:
                out.append((e["e"], e["dest"], e))
        for e in self.CHOS:
            if t_lo <= e["e"] <= t_hi:
                out.append((e["e"], PHRASE2DEST[e["phrase"]], e))
        out.sort(key=lambda x: (x[0], x[2]["ln"]))
        return out


def collapse(decs, gap=5.0):
    out = []
    for d in decs:
        if out and d[1] == out[-1][1] and (d[0] - out[-1][0]) <= gap:
            continue
        out.append(d)
    return out


def replay(decs, init_cur="study"):
    rows = []
    frm = init_cur
    for i in range(1, len(decs)):
        t_prev, d_prev, _ = decs[i - 1]
        t_i, d_i, _e = decs[i]
        dep = frm
        path = path_between(dep, d_prev)
        if path:
            legs, a = [], dep
            for p in path:
                legs.append(EDGES[(a, p)])
                a = p
            leg1, full = legs[0], sum(legs)
        else:
            leg1 = full = 0
        gap = t_i - t_prev
        timing = "first-leg" if gap < leg1 else ("later-leg" if gap < full else None)
        shape = None
        if timing:
            shape = ("same-dest-retrigger" if d_i == d_prev else
                     "reversal-to-departure" if d_i == dep else "redirect-to-third-place")
        rows.append({"i": i, "t": t_i, "from": dep, "prev_dest": d_prev, "dest": d_i, "gap": gap, "leg1": leg1, "full": full,
                     "timing": timing, "shape": shape})
        frm = d_prev
    return rows


def summarize_replay(rows, n):
    inter = [r for r in rows if r["timing"]]
    cross = [r for r in inter if r["shape"] != "same-dest-retrigger"]
    return {"decisions": n, "transitions": len(rows), "interruptions": len(inter), "cross": len(cross),
            "cross_first": sum(1 for r in cross if r["timing"] == "first-leg"),
            "cross_later": sum(1 for r in cross if r["timing"] == "later-leg"),
            "by": dict(Counter((r["shape"], r["timing"]) for r in inter))}


def poisson_sf(k, mu):
    if k <= 0:
        return 1.0
    s, term = 0.0, math.exp(-mu)
    for i in range(k):
        s += term
        term *= mu / (i + 1)
    return max(0.0, 1.0 - s)


def hdr(s):
    print("\n" + "=" * 100 + "\n" + s + "\n" + "=" * 100)


# ================================================================== sections
def sec_gate(c):
    hdr("GATE: live-days on runs that START at/after the commit's committer time")
    print(f"log snapshot: {c.snap['lines']} lines, {c.snap['bytes']} bytes, last timestamped line {c.snap['last_ts']}")
    print(f"commit {c.commit} committed {c.iso}")
    for r in c.runs:
        if r["a"] < c.t0 <= r["b"]:
            print(f"run already in progress at t0 (started BEFORE it, did NOT load it): {r['start']} -> {r['end']} ({r['how']})")
    print(f"{'start':<20}{'end':<20}{'hours':>8}  {'how':<8}{'start_line':<11}old-rule end (only if it differs)")
    for r in c.runs:
        if r["a"] >= c.t0:
            nv = r.get("end_naive_rule")
            print(f"{str(r['start']):<20}{str(r['end']):<20}{(r['b']-r['a'])/3600:8.2f}  {r['how']:<8}{r['start_line']:<11}"
                  f"{str(nv) if nv is not None and nv != r['end'] else ''}")
    if not c.fixed:
        print("NO restart at/after t0 -> GATE FAILS")
        return
    print(f"first restart onto it: {epoch_local_str(c.fixed[0][0])};  restarts since t0: {len(c.fixed)} runs")
    print(f"cumulative live time: {sum(c.hours):.1f} h = {c.D:.3f} live-days  (GATE {'PASSES' if c.D >= 3.0 else 'FAILS'} at 3.00)")
    print(f"movement regimes: runs 1-2 {c.D_act:.3f} d ({sum(c.hours[:2]):.1f} h) | runs 3-7 {c.D_qui:.3f} d ({sum(c.hours[2:]):.1f} h)")
    c.K["live_days"] = round(c.D, 3)


def sec_teleport(c):
    hdr("TELEPORT SCAN: 'DISPATCH move' narrations by source (F-1653 evidence 3 method)")
    for e in c.DISP:
        e["cls"] = c.classify_narration(e["text"])
    eras = {
        "pre-fix 08-22 -> 09-18 23:14:20 (F-1653: 597 = 484 LEG + 113 gate/school + 0 instant)": (local_epoch("2026-08-22 00:00:00"), local_epoch("2026-09-18 23:14:20")),
        "teleport era to F-1653's log end 09-21 15:00 (F-1653: 47 = 27 instant + 7 leg + 13 gate/school)": (local_epoch("2026-09-18 23:14:20"), local_epoch("2026-09-21 15:00:00")),
        "teleport era full 09-18 23:14:20 -> 09-22 16:11:06": (local_epoch("2026-09-18 23:14:20"), local_epoch("2026-09-22 16:11:06")),
    }
    for name, (lo, hi) in eras.items():
        cn = Counter(e["cls"] for e in c.DISP if lo <= e["e"] < hi)
        print(f"[{name}]\n    total={sum(cn.values())} {dict(cn)}")
    cf = Counter(e["cls"] for e in c.DISP if c.in_fixed(e["e"]))
    print(f"[COUNTED RUNS] total={sum(cf.values())} {dict(cf)}   <- INSTANT must be 0")
    for i, (a, b) in enumerate(c.fixed, 1):
        print(f"    run {i} {epoch_local_str(a)} -> {epoch_local_str(b)} ({(b-a)/3600:.1f} h): {dict(Counter(e['cls'] for e in c.DISP if a <= e['e'] <= b))}")
    other = [e for e in c.DISP if c.in_fixed(e["e"]) and e["cls"] == "other"]
    print("unclassified texts in the counted runs:", [e["text"][:60] for e in other] if other else "none")
    act_t = [a["e"] for a in c.ACTS]
    def after_act(e):
        i = bisect.bisect_right(act_t, e["e"]) - 1
        return i >= 0 and 0 <= e["e"] - act_t[i] <= 2.0
    print("DISPATCH move within 2 s after an ACT move: pre-fix", dict(Counter(e["cls"] for e in c.DISP if local_epoch("2026-08-22 00:00:00") <= e["e"] < local_epoch("2026-09-18 23:14:20") and after_act(e))),
          "| teleport era to 09-21 15:00", dict(Counter(e["cls"] for e in c.DISP if local_epoch("2026-09-18 23:14:20") <= e["e"] < local_epoch("2026-09-21 15:00:00") and after_act(e))),
          "| counted runs", dict(Counter(e["cls"] for e in c.DISP if c.in_fixed(e["e"]) and after_act(e))))
    nd = sum(1 for e in c.DECL if c.in_fixed(e["e"]))
    print(f"(0) is the fix the running code? decline lines in the whole log {len(c.DECL)} (first {c.DECL[0]['t'] if c.DECL else None}); in the counted runs {nd}; J-1185 override lines {sum(1 for e in c.SYSO if c.in_fixed(e['e']))}")
    c.K["instant_narrations_fixed"] = cf.get("INSTANT", 0)
    c.K["decline_lines"] = nd


def _decision_list(c, t_lo, t_hi):
    dec = []
    for e in c.ACTS:
        if t_lo <= e["e"] <= t_hi:
            dec.append({"t": e["e"], "kind": "ACT", "dest": e["dest"], "ts": e["t"]})
    for e in c.CHOS:
        if t_lo <= e["e"] <= t_hi:
            dec.append({"t": e["e"], "kind": "CHOSE", "dest": PHRASE2DEST[e["phrase"]], "ts": e["t"]})
    dec.sort(key=lambda d: d["t"])
    dts = [d["t"] for d in dec]
    for e in c.DISP:
        if not (t_lo <= e["e"] <= t_hi):
            continue
        lg = c.leg_of(e["text"])
        if lg is None:
            continue
        i = bisect.bisect_right(dts, e["e"]) - 1
        if i >= 0 and 0 <= e["e"] - dts[i] <= 2.0:
            continue
        dec.append({"t": e["e"], "kind": "DISP", "dest": None, "leg": lg, "ts": e["t"]})
    dec.sort(key=lambda d: d["t"])
    return dec


def walk_check(c, t_lo, t_hi, MAXW=360.0):
    dec = _decision_list(c, t_lo, t_hi)
    cuts = sorted([(e["e"], "SYSO") for e in c.SYSO if t_lo <= e["e"] <= t_hi] + [(e["e"], "SLEEP") for e in c.SLEEP if t_lo <= e["e"] <= t_hi])
    cut_t = [x[0] for x in cuts]
    st, ex = Counter(), []
    for i, d in enumerate(dec):
        t = d["t"]
        end = t + MAXW
        why = "6min"
        if i + 1 < len(dec) and dec[i + 1]["t"] < end:
            end, why = dec[i + 1]["t"], "next-decision"
        j = bisect.bisect_right(cut_t, t + 0.2)
        if j < len(cut_t) and cut_t[j] < end:
            end, why = cut_t[j], cuts[j][1]
        k = bisect.bisect_left(c.row_ts, t - 1.0)
        samples = []
        while k < len(c.rows) and c.rows[k]["ts"] < end:
            samples.append(c.rows[k])
            k += 1
        st["decisions"] += 1
        if not samples or samples[0]["ts"] - t > 5.0:
            st["no_decision_row"] += 1
            ex.append(("NO-ROW", d, None, why, None))
            continue
        P = samples[0]["location"]
        if d["kind"] == "DISP":
            frm, to = d["leg"]
            ia, ib = CHAIN.index(frm), CHAIN.index(to)
            step = 1 if ib > ia else -1
            allowed, x = [], ia
            while 0 <= x < 4:
                allowed.append(CHAIN[x])
                x += step
            dest = None
            if P not in allowed:
                st["DISP_P_not_on_leg"] += 1
                ex.append(("DISP-P-NOT-ON-LEG", d, [(round(s["ts"] - t, 1), s["location"]) for s in samples[:6]], why, None))
                continue
            order = allowed[allowed.index(P):]
        else:
            dest = d["dest"]
            if P == dest:
                st["row_already_at_dest"] += 1
                ex.append(("ROW-AT-DEST", d, [(round(s["ts"] - t, 1), s["location"]) for s in samples[:6]], why, None))
                continue
            order = [P] + path_between(P, dest)
        idx = {p: n for n, p in enumerate(order)}
        last, bad = 0, None
        for s in samples[1:]:
            loc = s["location"]
            if loc not in idx:
                bad = ("OFF-PATH", s)
                break
            if idx[loc] < last:
                bad = ("BACK", s)
                break
            if dest is not None and loc != P:
                need = cum_secs(P, loc, dest)
                if need is not None and (s["ts"] - t) < need - 1.0:
                    bad = ("TOO-EARLY", s)
                    break
            last = max(last, idx[loc])
        if bad:
            bs = bad[1]
            toward = CHAIN.index(bs["location"]) < CHAIN.index(order[last]) if bs["location"] in CHAIN else False
            tag = "SCHOOL-REEL-BACK(system-driven)" if (school_confined(bs["ts"]) and toward) else "UNEXPLAINED"
            st["violations"] += 1
            st["viol_" + ("explained_school_reel_back" if tag.startswith("SCHOOL") else "UNEXPLAINED")] += 1
            ex.append((bad[0] + "/" + tag, d, [(round(s["ts"] - t, 1), s["location"]) for s in samples[:8]], why,
                       epoch_local_str(bs["ts"])))
        else:
            st["clean"] += 1
        st["samples"] += max(0, len(samples) - 1)
    return dec, st, ex


def sec_walk(c):
    hdr("WALK: location after every fired move decision, after every decline, and every location change")
    tot, all_ex = Counter(), []
    for n, (a, b) in enumerate(c.fixed, 1):
        _d, st, ex = walk_check(c, a, b)
        tot.update(st)
        all_ex += ex
        print(f"run {n}: {dict(st)}")
    print("COUNTED RUNS:", dict(tot))
    for x in all_ex[:30]:
        print("   ", x[0], x[1]["ts"], x[1]["kind"], x[1].get("dest") or x[1].get("leg"), "samples(dt,loc)=", x[2], "end=", x[3], "at", x[4])
    c.K["walk_windows"], c.K["walk_clean"] = tot["decisions"], tot["clean"]
    c.K["walk_unexplained"] = tot["viol_UNEXPLAINED"]
    # control: the teleport era must show the signature (ROW-AT-DEST) that the counted runs lack
    ta, tb = local_epoch("2026-09-18 23:14:20"), local_epoch("2026-09-22 16:11:06")
    _d, st, _ex = walk_check(c, ta, tb)
    print("CONTROL teleport era 09-18 23:14:20 -> 09-22 16:11:06:", dict(st), "  (row_already_at_dest = the teleport signature)")
    # decline rows: the teleport signature (row location == declined dest, previous row elsewhere)
    cl = _decline_clusters(c)
    tele = []
    for cc in cl:
        k = bisect.bisect_left(c.row_ts, cc["t"] - 1.0)
        r0 = c.rows[k] if k < len(c.rows) else None
        prev = c.rows[k - 1] if k > 0 else None
        cc["row_loc"] = r0["location"] if r0 and r0["ts"] - cc["t"] < 5 else None
        cc["prev_loc"] = prev["location"] if prev else None
        if cc["row_loc"] == cc["dest"] and cc["prev_loc"] != cc["dest"]:
            tele.append(cc)
    print(f"decline decisions (distinct) {len(cl)}: with a decline row {sum(1 for x in cl if x['row_loc'])}; teleport signature at the decline row: {len(tele)}")
    cnt = tot_acts = 0
    for a, b in c.fixed:
        for e in c.ACTS:
            if a <= e["e"] <= b:
                r = c.own_row(e["e"])
                if r:
                    tot_acts += 1
                    k = bisect.bisect_left(c.row_ts, e["e"] - 1.0)
                    prev = c.rows[k - 1]["location"] if k > 0 else None
                    if r["location"] == e["dest"] and prev != e["dest"]:
                        cnt += 1
    print(f"COUNTED RUNS: ACT-place decisions whose own row already shows the destination: {cnt} of {tot_acts}")
    cnt = tot_acts = 0
    for e in c.ACTS:
        if ta <= e["e"] <= tb:
            r = c.own_row(e["e"])
            if r:
                tot_acts += 1
                k = bisect.bisect_left(c.row_ts, e["e"] - 1.0)
                prev = c.rows[k - 1]["location"] if k > 0 else None
                if r["location"] == e["dest"] and prev != e["dest"]:
                    cnt += 1
    print(f"CONTROL teleport era: {cnt} of {tot_acts}")
    c.K["decline_row_teleport_signatures"] = len(tele)
    # rigorous decline walk: X may appear only if on the existing journey's path and base seconds have elapsed
    fired = sorted([(a["e"], a["dest"]) for a in c.ACTS if c.in_fixed(a["e"])] + [(x["e"], PHRASE2DEST[x["phrase"]]) for x in c.CHOS if c.in_fixed(x["e"])])
    fired_t = [f[0] for f in fired]
    disp_only = []
    for e in c.DISP:
        if c.in_fixed(e["e"]) and c.leg_of(e["text"]):
            i = bisect.bisect_right(fired_t, e["e"]) - 1
            if not (i >= 0 and 0 <= e["e"] - fired_t[i] <= 2.0):
                disp_only.append(e["e"])
    system = sorted([e["e"] for e in c.SYSO + c.SLEEP] + disp_only)
    stat, viol = Counter(), []
    for e in c.DECL:
        if not c.in_fixed(e["e"]):
            continue
        t, X, E = e["e"], e["dest"], e["exist"]
        i = bisect.bisect_right(fired_t, t) - 1
        start = None
        while i >= 0 and t - fired_t[i] <= 900:
            if fired[i][1] == E:
                start = fired[i]
                break
            i -= 1
        if start is None:
            stat["no starting decision found (system-started journey, e.g. the school reel-back, or older than 15 min)"] += 1
            continue
        r0 = c.own_row(start[0])
        if r0 is None:
            stat["no row for the starting decision"] += 1
            continue
        Pj = r0["location"]
        path = [Pj] + path_between(Pj, E)
        nxt = bisect.bisect_right(fired_t, t + 0.5)
        end = min(t + 360.0, fired_t[nxt] if nxt < len(fired_t) else 1e18, next(b for a, b in c.fixed if a <= t <= b))
        j = bisect.bisect_right(system, t)
        if j < len(system) and system[j] < end:
            end = system[j]
        k = bisect.bisect_left(c.row_ts, t - 1.0)
        bad = None
        while k < len(c.rows) and c.rows[k]["ts"] < end:
            loc, ts_ = c.rows[k]["location"], c.rows[k]["ts"]
            if loc == X and loc != Pj:
                if X not in path:
                    bad = "X not on the existing journey's path"
                    break
                need = cum_secs(Pj, X, E)
                if need is not None and (ts_ - start[0]) < need - 1.0:
                    bad = f"reached X {ts_ - start[0]:.0f}s after the journey started, base legs need >= {need}s"
                    break
            k += 1
        stat["declines checked"] += 1
        if bad:
            stat["VIOLATIONS"] += 1
            viol.append((e["t"], X, E, bad))
        else:
            stat["clean"] += 1
    print("(2b rigorous) every decline LINE:", dict(stat), viol[:10])
    c.K["decline_walk_violations"] = stat["VIOLATIONS"]
    # global conservation
    tot2, un = Counter(), []
    for n, (a, b) in enumerate(c.fixed, 1):
        evs = []
        for e in c.events:
            if not (a <= e["e"] <= b):
                continue
            if e["k"] == "ACT" and e["dest"] in PLACES:
                evs.append((e["e"], "decision"))
            elif e["k"] == "CHOSE":
                evs.append((e["e"], "decision"))
            elif e["k"] == "DISP" and c.leg_of(e["text"]):
                evs.append((e["e"], "decision"))
            elif e["k"] == "SYSO":
                evs.append((e["e"], "system"))
        evs.sort()
        et = [x[0] for x in evs]
        slp = sorted([(e["e"], "S") for e in c.SLEEP if a <= e["e"] <= b] + [(e["e"], "W") for e in c.WAKE if a <= e["e"] <= b])
        sleeps, cur = [], None
        for t_, k_ in slp:
            if k_ == "S":
                cur = t_
            elif cur is not None:
                sleeps.append((cur, t_))
                cur = None
        if cur is not None:
            sleeps.append((cur, b))
        rr = [r for r in c.rows if a <= r["ts"] <= b]
        for q in range(1, len(rr)):
            p, qq = rr[q - 1], rr[q]
            if p["location"] == qq["location"]:
                continue
            tot2["location changes"] += 1
            t_ = qq["ts"]
            jx = bisect.bisect_right(et, t_) - 1
            if jx >= 0 and t_ - et[jx] <= 900:
                tot2["explained: decision <= 900 s before"] += 1
            elif any(s0 - 5 <= t_ <= s1 + 900 for s0, s1 in sleeps):
                tot2["explained: sleep/to_bed"] += 1
            elif school_confined(t_) and CHAIN.index(qq["location"]) < CHAIN.index(p["location"]):
                tot2["explained: school reel-back"] += 1
            else:
                tot2["UNEXPLAINED (check: long gap between rows after a decision to exactly this place?)"] += 1
                un.append((epoch_local_str(t_), n, p["location"], qq["location"], round(t_ - (et[jx] if jx >= 0 else 0))))
    print("(2c) global conservation:", dict(tot2), un)


def _decline_clusters(c, reasons=("same-dest", "first-leg"), runs_only=True):
    out = []
    for e in sorted((x for x in c.DECL if (c.in_fixed(x["e"]) if runs_only else True)), key=lambda x: x["e"]):
        if out and out[-1]["dest"] == e["dest"] and out[-1]["exist"] == e["exist"] and out[-1]["why"] == e["why"] and e["e"] - out[-1]["t_last"] <= 5.0:
            out[-1]["n_raw"] += 1
            out[-1]["t_last"] = e["e"]
            continue
        out.append({"t": e["e"], "t_last": e["e"], "dest": e["dest"], "exist": e["exist"], "why": e["why"], "n_raw": 1,
                    "ts": e["t"], "ln": e["ln"], "run": c.run_of(e["e"])})
    return out


def build_dcl(c):
    """distinct decline decisions of the counted runs, each flagged: echo (a FIRED ACT/'he chose to' <= 2 s before it, i.e.
    route_act / dispatch / the legacy latch seeing the same thought) and sys_suspect (dest study in a school-confined
    period or within 3 s after a sleep entry = the school reel-back / to_bed calling move('study'))."""
    if getattr(c, "dcl", None) is not None:
        return c.dcl
    dcl = _decline_clusters(c)
    fired = sorted([(a["e"], a["dest"]) for a in c.ACTS if c.in_fixed(a["e"])] + [(x["e"], PHRASE2DEST[x["phrase"]]) for x in c.CHOS if c.in_fixed(x["e"])])
    fired_t = [f[0] for f in fired]
    sleep_t = sorted(s["e"] for s in c.SLEEP)
    for d in dcl:
        i = bisect.bisect_right(fired_t, d["t"] + 0.5) - 1
        d["echo"] = bool(i >= 0 and -0.5 <= d["t"] - fired_t[i] <= 2.0)
        j = bisect.bisect_right(sleep_t, d["t"]) - 1
        d["sys_suspect"] = d["dest"] == "study" and (school_confined(d["t"]) or (j >= 0 and 0 <= d["t"] - sleep_t[j] <= 3.0))
    c.dcl = dcl
    return dcl


def sec_rates(c):
    hdr("RATES: distinct decline decisions per live-day, decomposition, first-leg geometry / insistence / fate, callers")
    D, Da, Dq = c.D, c.D_act, c.D_qui
    dcl = build_dcl(c)
    fired = sorted([(a["e"], a["dest"]) for a in c.ACTS if c.in_fixed(a["e"])] + [(x["e"], PHRASE2DEST[x["phrase"]]) for x in c.CHOS if c.in_fixed(x["e"])])
    fired_t = [f[0] for f in fired]
    for label, runset, DD in (("ALL counted runs", range(1, 8), D), ("active regime runs 1-2", [1, 2], Da), ("quiet regime runs 3-7", [3, 4, 5, 6, 7], Dq)):
        sub = [d for d in dcl if d["run"] in runset]
        for why in ("same-dest", "first-leg"):
            s = [d for d in sub if d["why"] == why]
            raw = sum(d["n_raw"] for d in s)
            echo = [d for d in s if d["echo"]]
            non = [d for d in s if not d["echo"]]
            sysu = [d for d in non if d["sys_suspect"]]
            print(f"{label:<24} {why:<9}: distinct {len(s):4d} = {len(s)/DD:6.2f}/live-day | raw lines {raw:4d} = {raw/DD:6.2f}/d | same-cycle echo {len(echo):4d} | standalone {len(non):4d} "
                  f"({len(non)/DD:6.2f}/d; of which dest=study in school/sleep time {len(sysu)})")
        if label.startswith("ALL"):
            c.K["first_leg_distinct"] = sum(1 for d in sub if d["why"] == "first-leg")
            c.K["same_dest_distinct"] = sum(1 for d in sub if d["why"] == "same-dest")
    # thought-level clusters
    mov = []
    for e in c.events:
        if not c.in_fixed(e["e"]):
            continue
        if e["k"] == "ACT" and e["dest"] in PLACES:
            mov.append((e["e"], "ACT", e))
        elif e["k"] in ("CHOSE", "DECL", "SYSO", "DISP"):
            mov.append((e["e"], e["k"], e))
    mov.sort(key=lambda x: x[0])
    cl = []
    for t, k, e in mov:
        if cl and t - cl[-1]["t_last"] <= 2.0:
            cl[-1]["ev"].append((t, k, e))
            cl[-1]["t_last"] = t
        else:
            cl.append({"t0": t, "t_last": t, "ev": [(t, k, e)]})
    for x in cl:
        ks = Counter(k for _, k, _ in x["ev"])
        x["fired"] = ks["ACT"] + ks["CHOSE"] > 0
        x["decl"] = [e for _, k, e in x["ev"] if k == "DECL"]
        x["run"] = c.run_of(x["t0"])
        x["why_set"] = tuple(sorted(set(e["why"] for e in x["decl"])))
        x["row"] = c.own_row(x["t0"])
    for label, runset, DD in (("ALL", range(1, 8), D), ("active 1-2", [1, 2], Da)):
        cs = [x for x in cl if x["run"] in runset]
        fi = [x for x in cs if x["fired"]]
        do = [x for x in cs if not x["fired"] and x["decl"]]
        print(f"[thought-level {label}] fired clusters {len(fi)} ({len(fi)/DD:.1f}/d, {sum(1 for x in fi if x['decl'])} also carry a decline); declined-only thoughts {len(do)} ({len(do)/DD:.1f}/d: "
              f"same-dest {sum(1 for x in do if x['why_set']==('same-dest',))}, first-leg {sum(1 for x in do if x['why_set']==('first-leg',))}, both {sum(1 for x in do if len(x['why_set'])==2)}); "
              f"fired + declined thoughts {len(fi)+len(do)} = {(len(fi)+len(do))/DD:.1f}/d")
    do_all = [x for x in cl if not x["fired"] and x["decl"]]
    def caller(x):
        r = x["row"]
        if r is None:
            return "no-row"
        dm = [d for d in (r.get("dispatch") or []) if d.get("family") == "move"]
        ak = r["act_kind"]
        return ("act_kind=move + dispatch hand" if ak == "move" and dm else "act_kind=move only" if ak == "move"
                else f"dispatch move hand only (act_kind={ak})" if dm else f"neither (act_kind={ak})")
    for why in (("same-dest",), ("first-leg",)):
        sel = [x for x in do_all if x["why_set"] == why]
        cn = Counter(caller(x).split(" (")[0] for x in sel)
        print(f"declined-only thoughts {why}: {len(sel)} callers {dict(cn.most_common())}")
    # first-leg deep dive
    fl = []
    for e in sorted((x for x in c.DECL if c.in_fixed(x["e"]) and x["why"] == "first-leg"), key=lambda x: x["e"]):
        if fl and fl[-1]["dest"] == e["dest"] and fl[-1]["exist"] == e["exist"] and e["e"] - fl[-1]["t_last"] <= 5.0:
            fl[-1]["n_raw"] += 1
            fl[-1]["t_last"] = e["e"]
            continue
        fl.append({"t": e["e"], "t_last": e["e"], "dest": e["dest"], "exist": e["exist"], "n_raw": 1, "ts": e["t"]})
    for x in fl:
        i = bisect.bisect_right(fired_t, x["t"] + 0.5) - 1
        x["echo"] = bool(i >= 0 and -0.5 <= x["t"] - fired_t[i] <= 2.0)
        j, start = i, None
        while j >= 0 and x["t"] - fired_t[j] <= 900:
            if fired[j][1] == x["exist"]:
                start = fired[j]
                break
            j -= 1
        x["start"] = start
        r = c.own_row(x["t"], tol=8.0)
        x["P"] = r["location"] if r else None
        P, E, X = x["P"], x["exist"], x["dest"]
        pth = path_between(P, E) if P else []
        if P is None:
            x["geo"] = "no-row"
        elif pth and X == pth[0]:
            x["geo"] = "X == the first leg's own destination (already walking there)"
        elif X in pth[:-1]:
            x["geo"] = "on-path, 2+ legs ahead"
        elif E in path_between(P, X):
            x["geo"] = "extension (X beyond E)"
        else:
            x["geo"] = "opposite side of the departure"
        if start:
            rs = c.own_row(start[0])
            Pj = rs["location"] if rs else None
            x["P_start"] = Pj
            pp = path_between(Pj, E) if Pj else []
            x["leg1"] = EDGES[(Pj, pp[0])] if pp else None
        else:
            x["P_start"], x["leg1"] = None, None
    stand = [x for x in fl if not x["echo"]]
    print(f"\nfirst-leg distinct declines (first-leg-only collapse): {len(fl)}; same-cycle echo {len(fl)-len(stand)}; standalone {len(stand)}")
    print("   relation of X to the in-progress first leg (all):", dict(Counter(x["geo"] for x in fl).most_common()))
    print("   by (declined, existing) standalone:", dict(Counter((x["dest"], x["exist"]) for x in stand).most_common(8)))
    # insistence
    by = defaultdict(list)
    for x in fl:
        by[(x["dest"], x["exist"], x["start"][0] if x["start"] else ("nostart", int(x["t"] // 600)))].append(x)
    n_base = n_real = 0
    for key, lst in by.items():
        if not isinstance(key[2], float):
            continue
        lst.sort(key=lambda z: z["t"])
        ts0, leg1, P0 = key[2], lst[0]["leg1"], lst[0]["P_start"]
        k0 = bisect.bisect_left(c.row_ts, ts0 - 1.0)
        real_end = None
        for k in range(k0, min(k0 + 40, len(c.rows))):
            if c.rows[k]["ts"] > ts0 and c.rows[k]["location"] != P0:
                real_end = c.rows[k]["ts"]
                break
        for idx, x in enumerate(lst):
            if any(z["t"] <= ts0 + (leg1 or 0) for z in lst[idx + 1:]):
                n_base += 1
            if any(real_end is None or z["t"] <= real_end for z in lst[idx + 1:]):
                n_real += 1
    print(f"   INSISTENCE: first-leg declines followed by another decline of the same destination in the same first-leg window: {n_base} of {len(fl)} "
          f"({100*n_base/len(fl):.0f}%) [window = leg-1 BASE seconds]; {n_real} ({100*n_real/len(fl):.0f}%) [window = until the trace shows him off the departure place]")
    c.K["insistence_base_window"], c.K["insistence_real_window"], c.K["first_leg_n"] = n_base, n_real, len(fl)
    # fate of the wish (standalone)
    fired_all = fired
    res = []
    for x in stand:
        t, X, E = x["t"], x["dest"], x["exist"]
        end = min(t + 600.0, next(b for a, b in c.fixed if a <= t <= b))
        i = bisect.bisect_right(fired_t, t + 0.5)
        honored = None
        while i < len(fired_all) and fired_all[i][0] <= end:
            if fired_all[i][1] == X:
                honored = fired_all[i][0] - t
                break
            i += 1
        k = bisect.bisect_left(c.row_ts, t - 1.0)
        seq = []
        while k < len(c.rows) and c.rows[k]["ts"] <= end:
            seq.append((c.rows[k]["ts"] - t, c.rows[k]["location"]))
            k += 1
        at_x = [s for s in seq if s[1] == X]
        res.append({"X": X, "E": E, "geo": x["geo"], "honored": honored, "reached": bool(at_x)})
    def fate(sel, name):
        n = len(sel)
        if not n:
            return
        h = sorted(r["honored"] for r in sel if r["honored"] is not None)
        print(f"   FATE {name}: n={n}; later FIRED to X within 10 min {len(h)} ({100*len(h)/n:.0f}%)" + (f", median delay {h[len(h)//2]:.0f} s" if h else "")
              + f"; trace shows X within 10 min {sum(1 for r in sel if r['reached'])} ({100*sum(1 for r in sel if r['reached'])/n:.0f}%)")
    fate(res, "all standalone")
    fate([r for r in res if r["geo"].startswith("X == the first leg")], "X == first leg's own destination")
    fate([r for r in res if not r["geo"].startswith("X == the first leg")], "X is a genuine change of direction")
    for g in sorted(set(r["geo"] for r in res)):
        fate([r for r in res if r["geo"] == g], g[:40])
    c.fl = fl


def sec_replay(c, validate=True):
    hdr("REPLAY: F-1418's replay (reconstructed; validated) over the counted runs, weekly baselines, F-1658 totals")
    if validate:
        lo, hi = local_epoch("2026-08-15 00:00:00"), local_epoch("2026-09-13 09:09:00")
        d = collapse(c.decisions(lo, hi))
        s = summarize_replay(replay(d), len(d))
        ok = (len(d), s["interruptions"], s["cross_first"], s["cross_later"]) == (2296, 520, 58, 138) and s["by"] == {
            ("redirect-to-third-place", "first-leg"): 37, ("redirect-to-third-place", "later-leg"): 35, ("reversal-to-departure", "first-leg"): 21,
            ("reversal-to-departure", "later-leg"): 103, ("same-dest-retrigger", "first-leg"): 189, ("same-dest-retrigger", "later-leg"): 135}
        print(f"VALIDATION vs F-1418/F-1654 baseline (2296 distinct, 520 interruptions, 58 first + 138 later; 189/135/103/21/37/35): {'REPRODUCED EXACTLY' if ok else 'MISMATCH'}  {dict(s['by'])}")
        c.K["replay_validates_baseline"] = ok
    print("weekly baseline series (per live-day):")
    print(f"{'window':<14}{'live-d':>7}{'decis':>7}{'dec/d':>7}{'cross':>6}{'1st':>5}{'1st/d':>7}{'later':>6}{'later/d':>8}{'same':>6}{'same/d':>7}")
    for name, a, b in (("08-15..08-23", "2026-08-15 00:00:00", "2026-08-24 00:00:00"), ("08-24..08-30", "2026-08-24 00:00:00", "2026-08-31 00:00:00"),
                       ("08-31..09-06", "2026-08-31 00:00:00", "2026-09-07 00:00:00"), ("09-07..09-13", "2026-09-07 00:00:00", "2026-09-13 09:09:00")):
        lo_, hi_ = local_epoch(a), local_epoch(b)
        d = collapse(c.decisions(lo_, hi_))
        s = summarize_replay(replay(d), len(d))
        dd = c.live_days(lo_, hi_)
        same = sum(v for k, v in s["by"].items() if k[0] == "same-dest-retrigger")
        print(f"{name:<14}{dd:7.2f}{len(d):7d}{len(d)/dd:7.1f}{s['cross']:6d}{s['cross_first']:5d}{s['cross_first']/dd:7.2f}{s['cross_later']:6d}{s['cross_later']/dd:8.2f}{same:6d}{same/dd:7.1f}")
    ll, lh = local_epoch("2026-09-06 00:00:00"), local_epoch("2026-09-13 09:09:00")
    d = collapse(c.decisions(ll, lh))
    s = summarize_replay(replay(d), len(d))
    dl = c.live_days(ll, lh)
    same_l = sum(v for k, v in s["by"].items() if k[0] == "same-dest-retrigger")
    LATE = {"decisions": len(d) / dl, "cross": s["cross"] / dl, "first": s["cross_first"] / dl, "later": s["cross_later"] / dl, "same": same_l / dl}
    print(f"LATE baseline 09-06..09-13 09:09: {dl:.2f} live-d, decisions {len(d)} ({LATE['decisions']:.1f}/d), cross {s['cross']} ({LATE['cross']:.2f}/d), first {s['cross_first']} ({LATE['first']:.2f}/d), later {s['cross_later']} ({LATE['later']:.2f}/d), same-dest {same_l} ({LATE['same']:.1f}/d)")
    res = {}
    for label, runset, DD in (("ALL counted runs", range(1, 8), c.D), ("active runs 1-2", [1, 2], c.D_act), ("quiet runs 3-7", [3, 4, 5, 6, 7], c.D_qui)):
        raw = []
        for i in runset:
            a, b = c.fixed[i - 1]
            raw += c.decisions(a, b)
        raw.sort(key=lambda x: (x[0], x[2]["ln"]))
        d = collapse(raw)
        s = summarize_replay(replay(d), len(d))
        res[label] = (len(d), s)
        print(f"[{label}] D={DD:.2f}: raw {len(raw)}, distinct {len(d)} ({len(d)/DD:.1f}/d), interruptions {s['interruptions']}; cross {s['cross']} ({s['cross']/DD:.2f}/d): first-leg {s['cross_first']} ({s['cross_first']/DD:.2f}/d), later-leg {s['cross_later']} ({s['cross_later']/DD:.2f}/d); shapes {s['by']}")
        if not label.startswith("quiet"):
            for bn, bl in (("F-1654 22.55-d baseline", BASE), ("late baseline", LATE)):
                mu = bl["later"] * DD
                print(f"      later-leg vs {bn}: expected {mu:.1f} observed {s['cross_later']} P(X>=obs)={poisson_sf(s['cross_later'], mu):.2e}")
    if True:
        build_dcl(c)
        for label, runset, DD in (("ALL counted runs", range(1, 8), c.D), ("active runs 1-2", [1, 2], c.D_act)):
            n_rep = res[label][0]
            sel = [x for x in c.dcl if x["run"] in runset]
            non = sum(1 for x in sel if not x["echo"])
            print(f"[{label}] total decisions (F-1658): replay {n_rep} + distinct decline lines {len(sel)} = {n_rep+len(sel)} = {(n_rep+len(sel))/DD:.1f}/d; with only the standalone declines {n_rep+non} = {(n_rep+non)/DD:.1f}/d  (baselines 101.8/d; late {LATE['decisions']:.1f}/d)")
    c.K["later_leg_model_all"] = res["ALL counted runs"][1]["cross_later"]
    c.K["later_leg_model_active"] = res["active runs 1-2"][1]["cross_later"]
    c.LATE = LATE


def _classify_real(c, ranges):
    raw = []
    for a, b in ranges:
        raw += c.decisions(a, b)
    raw.sort(key=lambda x: (x[0], x[2]["ln"]))
    decs = collapse(raw)
    out, prev = [], None
    for (t, D_, ev) in decs:
        r0 = c.own_row(t)
        P = r0["location"] if r0 else None
        rec = {"t": t, "D": D_, "P": P, "cls": None, "prev": None}
        if P is None:
            rec["cls"] = "no-row"
        elif P == "study" and D_ != "study" and school_confined(t):
            rec["cls"] = "school-refused (no journey)"
        else:
            if prev is None or t - prev["t"] > 900 or prev["P"] is None:
                rec["cls"] = "fresh (no recent journey)"
            else:
                Ep, Pp = prev["D"], prev["P"]
                path = [Pp] + path_between(Pp, Ep)
                if P == Ep:
                    rec["cls"] = "fresh (previous journey complete)"
                elif P not in path:
                    rec["cls"] = "off-path (system move in between)"
                elif D_ == Ep:
                    rec["cls"] = "same-dest re-will while walking"
                elif P == Pp:
                    rec["cls"] = "cross-dest FIRST-LEG redirect"
                else:
                    rec["cls"] = "cross-dest LATER-LEG redirect"
                rec["prev"] = prev
            prev = rec
        out.append(rec)
    return Counter(r["cls"] for r in out), out, len(raw), len(decs)


def sec_realstate(c):
    hdr("REALSTATE: model-free classification by the decision's own trace row (true location), pre-gate vs counted runs")
    first_row = c.rows[0]["ts"]
    pre_hi = local_epoch("2026-09-18 23:14:20")
    pre = [(max(r["a"], first_row), min(r["b"], pre_hi)) for r in c.runs if min(r["b"], pre_hi) > max(r["a"], first_row)]
    Dp = sum(y - x for x, y in pre) / 86400.0
    late = [(max(r["a"], local_epoch("2026-09-06 00:00:00")), min(r["b"], pre_hi)) for r in c.runs if min(r["b"], pre_hi) > max(r["a"], local_epoch("2026-09-06 00:00:00"))]
    Dl = sum(y - x for x, y in late) / 86400.0
    out = {}
    for label, rng, DD in (("PRE-GATE " + epoch_local_str(first_row)[:10] + " .. 09-18 23:14", pre, Dp), ("PRE-GATE late 09-06 .. 09-18 23:14", late, Dl),
                           ("FIXED all counted runs", c.fixed, c.D), ("FIXED active runs 1-2", c.fixed[:2], c.D_act)):
        cn, recs, nr, nd = _classify_real(c, rng)
        out[label] = (cn, DD)
        print(f"[{label}] live-days {DD:.2f}: raw {nr}, distinct fired {nd} ({nd/DD:.1f}/d)")
        for k, v in cn.most_common():
            print(f"     {v:5d}  {v/DD:7.2f}/d  {k}")
    dcl = build_dcl(c)
    sel = [x for x in dcl if x["run"] in (1, 2)]
    pre_cn, Dpre = out[[k for k in out if k.startswith("PRE-GATE 2")][0]] if any(k.startswith("PRE-GATE 2") for k in out) else (Counter(), 1)
    late_cn, Dlate = out["PRE-GATE late 09-06 .. 09-18 23:14"]
    act_cn, Dact = out["FIXED active runs 1-2"]
    st_fl = sum(1 for x in sel if x["why"] == "first-leg" and not x["echo"])
    st_sd = sum(1 for x in sel if x["why"] == "same-dest" and not x["echo"])
    print("\nAPPLES-TO-APPLES (real state, same instrument):")
    print(f"  first-leg cross-dest wishes/live-day: pre-gate (fired) {pre_cn['cross-dest FIRST-LEG redirect']/Dpre:.2f}, late {late_cn['cross-dest FIRST-LEG redirect']/Dlate:.2f}  |  counted active runs (declined, standalone) {st_fl/Dact:.2f}")
    print(f"  later-leg cross-dest redirects/live-day: pre-gate {pre_cn['cross-dest LATER-LEG redirect']/Dpre:.2f}, late {late_cn['cross-dest LATER-LEG redirect']/Dlate:.2f}  |  counted active runs {act_cn['cross-dest LATER-LEG redirect']/Dact:.2f}")
    print(f"  same-dest re-wills while walking/live-day: pre-gate {pre_cn['same-dest re-will while walking']/Dpre:.2f}, late {late_cn['same-dest re-will while walking']/Dlate:.2f}  |  counted active runs fired {act_cn['same-dest re-will while walking']/Dact:.2f} + declined(standalone) {st_sd/Dact:.2f}")
    c.K["realstate_first_leg_pre_late"] = round(late_cn["cross-dest FIRST-LEG redirect"] / Dlate, 2)
    c.K["realstate_later_leg_active"] = round(act_cn["cross-dest LATER-LEG redirect"] / Dact, 2)
    c.realstate = out


def sec_latch(c):
    hdr("LATCH after decline, move-family dispatch decisions in the trace")
    chos = [e for e in c.CHOS if c.in_fixed(e["e"])]
    decl_t = sorted(e["e"] for e in c.DECL)
    decl_sorted = sorted(c.DECL, key=lambda x: x["e"])
    after = []
    for ch in chos:
        i = bisect.bisect_right(decl_t, ch["e"]) - 1
        prev = []
        while i >= 0 and ch["e"] - decl_t[i] <= 2.0:
            prev.append(decl_sorted[i])
            i -= 1
        if prev:
            after.append((ch, prev))
    print(f"'he chose to GO ...' lines in the counted runs: {len(chos)} ({len(chos)/c.D:.2f}/d); following a decline within 2 s: {len(after)}; for a DIFFERENT destination: "
          f"{sum(1 for ch, p in after if any(PHRASE2DEST[ch['phrase']] != d['dest'] for d in p))}")
    for ch, p in after:
        r = c.own_row(ch["e"])
        print("   ", ch["t"], ch["phrase"], "| declines just before:", [(d["t"][11:], d["dest"], d["exist"], d["why"]) for d in p], "| own-row location:", r["location"] if r else None)
    first_dispatch = next((r["ts"] for r in c.rows if "dispatch" in r), None)
    def md(lo, hi):
        cn = Counter()
        for r in c.rows:
            if lo <= r["ts"] <= hi:
                for d in (r.get("dispatch") or []):
                    if d.get("family") == "move":
                        cn[d.get("decision")] += 1
        return cn
    pre_lo, pre_hi = c.rows[0]["ts"], local_epoch("2026-09-18 23:14:20")
    for name, rng, DD in (("pre-gate (trace start .. 09-18 23:14)", [(pre_lo, pre_hi)], sum(c.live_days(pre_lo, pre_hi) for _ in [0])),
                          ("counted runs", c.fixed, c.D), ("counted active runs 1-2", c.fixed[:2], c.D_act)):
        cn = Counter()
        for a, b in rng:
            cn.update(md(a, b))
        tot = sum(cn.values())
        print(f"[{name}] live-days {DD:.2f}: move-family dispatch decisions {tot} ({tot/DD:.1f}/d): hand-declined {cn['hand-declined']} ({cn['hand-declined']/DD:.1f}/d), FIRE {cn['FIRE']} ({cn['FIRE']/DD:.1f}/d), DROP-weak-intent {cn['DROP-weak-intent']}")
    sl = [e for e in c.SLEEP if c.in_fixed(e["e"])]
    sy = [e for e in c.SYSO if c.in_fixed(e["e"])]
    print(f"D-0246 context: sleep entries {len(sl)}; system first-leg overrides (J-1185 lines) {len(sy)} = {100*len(sy)/max(len(sl),1):.1f}% (F-1657's model: 4.7% in a first-leg window)")
    for s in sy:
        k = bisect.bisect_left(c.row_ts, s["e"] + 5)
        nxt = c.rows[k]["location"] if k < len(c.rows) else None
        print("   ", s["t"], s["dest"], "replaces journey to", s["exist"], "| first trace row after:", nxt, epoch_local_str(c.rows[k]["ts"])[11:] if k < len(c.rows) else "")


def sec_laterleg(c):
    hdr("LATERLEG: displacement, per-run rates, wood reachability, oscillation")
    _cn, recs, _nr, _nd = _classify_real(c, c.fixed)
    later = [r for r in recs if r["cls"] == "cross-dest LATER-LEG redirect"]
    dsort = sorted(c.DECL, key=lambda x: x["e"])
    decl_t = [e["e"] for e in dsort]
    print(f"later-leg real-state redirects {len(later)} ({len(later)/c.D:.2f}/d all, {sum(1 for r in later if r['t'] < c.fixed[1][1])/c.D_act:.2f}/d active)")
    for n, (a, b) in enumerate(c.fixed, 1):
        k = sum(1 for r in later if a <= r["t"] <= b)
        print(f"   run {n}: {k} later-leg in {(b-a)/3600:.1f} h = {k/((b-a)/86400):.1f}/d")
    disp = anyd = 0
    for r in later:
        pv = r["prev"]
        i0, i1 = bisect.bisect_left(decl_t, pv["t"]), bisect.bisect_right(decl_t, r["t"])
        if any(d["dest"] == r["D"] and d["exist"] == pv["D"] and d["why"] == "first-leg" for d in dsort[i0:i1]):
            disp += 1
        if i1 > i0:
            anyd += 1
    print(f"later-leg redirects whose destination was ALREADY declined as a first-leg wish in the same journey: {disp} of {len(later)} ({100*disp/max(len(later),1):.0f}%); with ANY decline earlier in the same journey: {anyd} ({100*anyd/max(len(later),1):.0f}%)")
    print("shape:", dict(Counter(("reversal-to-departure" if r["D"] == r["prev"]["P"] else "redirect-to-third-place") for r in later)))
    pre_lo, pre_hi = local_epoch("2026-09-11 12:00:00"), local_epoch("2026-09-18 23:14:20")
    pre = [(max(r["a"], pre_lo), min(r["b"], pre_hi)) for r in c.runs if min(r["b"], pre_hi) > max(r["a"], pre_lo)]
    Dp = sum(y - x for x, y in pre) / 86400.0
    def mix(rng):
        raw = []
        for a, b in rng:
            raw += c.decisions(a, b)
        raw.sort(key=lambda x: (x[0], x[2]["ln"]))
        d = collapse(raw)
        return Counter(x[1] for x in d), len(d)
    m_pre, n_pre = mix(pre)
    m_fx, n_fx = mix(c.fixed[:2])
    print(f"fired destination mix: pre-gate 09-11..09-18 ({Dp:.2f} d, {n_pre}): {dict(m_pre)}; counted active ({c.D_act:.2f} d, {n_fx}): {dict(m_fx)}; wood stops/day {m_pre['wood']/Dp:.1f} -> {m_fx['wood']/c.D_act:.1f}")
    def occ(rng):
        cn = Counter()
        for a, b in rng:
            for r in c.rows:
                if a <= r["ts"] <= b:
                    cn[r["location"]] += 1
        t = sum(cn.values())
        return {k: round(100 * v / t, 1) for k, v in cn.most_common()}
    print("location share of trace rows: pre-gate 09-11..09-18", occ(pre), "| counted active", occ(c.fixed[:2]))
    def chains(rs, label):
        ch, cur = [], []
        for r in rs:
            if r["cls"] in ("cross-dest LATER-LEG redirect", "cross-dest FIRST-LEG redirect") and r["prev"] is not None and r["t"] - r["prev"]["t"] < 300 and r["D"] == r["prev"]["P"]:
                cur.append(r)
            else:
                if cur:
                    ch.append(cur)
                cur = []
        if cur:
            ch.append(cur)
        print(f"   oscillation {label}: consecutive reversals (< 300 s each) {dict(sorted(Counter(len(x) for x in ch).items()))}")
    chains(recs, "counted runs")
    chains(_classify_real(c, pre)[1], "pre-gate 09-11..09-18")
    # per-regime movement
    for name, rng, DD in (("runs 1-2", c.fixed[:2], c.D_act), ("runs 3-7", c.fixed[2:], c.D_qui)):
        n_mv = sum(1 for r in c.rows if any(a <= r["ts"] <= b for a, b in rng) and r["act_kind"] == "move")
        n_act = sum(1 for e in c.ACTS if any(a <= e["e"] <= b for a, b in rng))
        print(f"movement regime {name}: act_kind == 'move' trace rows {n_mv} ({n_mv/DD:.1f}/d); ACT-place lines {n_act} ({n_act/DD:.1f}/d)")


SECTIONS = ["gate", "teleport", "walk", "rates", "replay", "realstate", "latch", "laterleg"]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gate", "read"])
    ap.add_argument("--commit", default="5a66504")
    ap.add_argument("--max-line", type=int, default=None, help="snapshot cut-off (physical line) of data/nascence.log")
    ap.add_argument("--sections", default=",".join(SECTIONS))
    ap.add_argument("--no-validate", action="store_true", help="skip the baseline-reproduction check in the replay section")
    a = ap.parse_args()
    c = Ctx(a.commit, a.max_line)
    secs = ["gate"] if a.cmd == "gate" else [s for s in a.sections.split(",") if s]
    fn = {"gate": sec_gate, "teleport": sec_teleport, "walk": sec_walk, "rates": sec_rates, "replay": lambda x: sec_replay(x, not a.no_validate),
          "realstate": sec_realstate, "latch": sec_latch, "laterleg": sec_laterleg}
    # rates must run before replay/realstate (they use its decline list); keep the canonical order
    for s in SECTIONS:
        if s in secs:
            fn[s](c)
    hdr("KEY NUMBERS")
    print(json.dumps(c.K, sort_keys=True, default=str))
    print(f"snapshot: {c.snap}")


if __name__ == "__main__":
    main()
