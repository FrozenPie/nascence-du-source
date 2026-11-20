"""scripts/hub_log_cold_warm.py (J-1668, 2026-10-03) -- observational cold/warm classification of every twain/shackleton letter generation
against the :11439 hub's OWN log (data/logs/cpu_tier_11439.log). READ-ONLY: opens the hub log and the
two thread.jsonl files for reading, writes nothing under C:\\Nascence, makes zero model calls.

The hub log has HH:MM:SS.mmm lines (since J-0500, 2026-09-03):
  [HH:MM:SS.mmm] [cpu-tier] loading gemma4:12b from ...
  [HH:MM:SS.mmm] [cpu-tier] gemma4:12b loaded in Ns
  [HH:MM:SS.mmm] [cpu-tier] gemma4:12b idle 300s -- unloading (RAM freed)
  [HH:MM:SS.mmm] [chat] N msgs -> M chars in T.Ts (json=...)
A [chat] line is printed when the response returns; T includes lock wait + any cold load + generation.
A request is COLD iff a 'loaded in' line sits between the previous [chat] line and this one.
Each letter is matched to its [chat] line by (time-of-day within a few seconds, chars >= len(text)).
Run: python scripts/hub_log_cold_warm.py   (read-only; zero model calls; about 1 s)
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Nascence")
LOG = ROOT / "data" / "logs" / "cpu_tier_11439.log"
LINE = re.compile(r"^\[(\d\d):(\d\d):(\d\d)\.(\d{3})\] \[(cpu-tier|chat|generate)\] (.*)$")


def nz_offset_h(utc: dt.datetime) -> int:
    # NZ DST 2026: ends Sun 5 Apr 03:00 NZDT, starts Sun 27 Sep 02:00 NZST (= 26 Sep 14:00 UTC)
    if dt.datetime(2026, 9, 26, 14, 0) <= utc.replace(tzinfo=None) or utc.replace(tzinfo=None) < dt.datetime(2026, 4, 4, 14, 0):
        return 13
    return 12


def local_of(ts: float) -> dt.datetime:
    u = dt.datetime.fromtimestamp(ts, dt.timezone.utc).replace(tzinfo=None)
    return u + dt.timedelta(hours=nz_offset_h(u))


def nonlatin_ratio(text: str) -> float:
    import unicodedata
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if "LATIN" not in unicodedata.name(c, "")) / len(letters)


# ---- parse the hub log into events with a wrap-detected day counter -------------------------------
events = []   # dict(i, tod_s, day, kind, text, chars, dur, cold, idle_before)
prev_tod = None
day = 0
for ln_no, raw in enumerate(LOG.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
    m = LINE.match(raw)
    if not m:
        continue
    h, mi, s, ms, tag, rest = m.groups()
    tod = int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 1000
    if prev_tod is not None and tod < prev_tod - 60:
        day += 1
    prev_tod = tod
    ev = {"ln": ln_no, "tod": tod, "day": day, "tag": tag, "rest": rest}
    if tag == "chat":
        mm = re.match(r"(\d+) msgs -> (\d+) chars in ([\d.]+)s", rest)
        if mm:
            ev.update(kind="chat", msgs=int(mm.group(1)), chars=int(mm.group(2)), dur=float(mm.group(3)))
        else:
            ev["kind"] = "other"
    elif "loaded in" in rest:
        mm = re.search(r"loaded in (\d+)s", rest)
        ev.update(kind="loaded", load_s=int(mm.group(1)) if mm else None)
    elif "unloading" in rest:
        ev["kind"] = "unload"
    elif "loading" in rest:
        ev["kind"] = "loading"
    else:
        ev["kind"] = "other"
    events.append(ev)

# classify each chat event: cold iff a 'loaded' event occurred since the previous chat event
cold_flag = False
last_chat_end = None
load_s_pending = None
load_end_abs = None        # absolute time the most recent load finished
pos_since_load = 0         # 1 = first request after the load (the cold one), 2 = second, ...
for ev in events:
    if ev["kind"] == "loaded":
        cold_flag = True
        load_s_pending = ev.get("load_s")
        load_end_abs = ev["day"] * 86400 + ev["tod"]
        pos_since_load = 0
    elif ev["kind"] == "unload":
        load_end_abs = None
        pos_since_load = 0
    elif ev["kind"] == "chat":
        ev["cold"] = cold_flag
        ev["load_s"] = load_s_pending if cold_flag else None
        ev["abs"] = ev["day"] * 86400 + ev["tod"]
        ev["idle_before"] = (ev["abs"] - ev["dur"]) - last_chat_end if last_chat_end is not None else None
        pos_since_load += 1
        ev["pos_since_load"] = pos_since_load
        ev["secs_load_end_to_start"] = ((ev["abs"] - ev["dur"]) - load_end_abs) if load_end_abs is not None else None
        last_chat_end = ev["abs"]
        cold_flag = False
        load_s_pending = None

chats = [e for e in events if e["kind"] == "chat"]
print(f"hub log: {len(events)} timestamped events, {len(chats)} [chat] lines, "
      f"{sum(1 for e in chats if e['cold'])} cold ({100*sum(1 for e in chats if e['cold'])/max(1,len(chats)):.1f}%), "
      f"{sum(1 for e in events if e['kind']=='loaded')} loaded-lines, {sum(1 for e in events if e['kind']=='unload')} unloads, "
      f"wrap-days spanned: {events[-1]['day'] if events else 0}")

# ---- cold-load durations, and cold vs warm chat durations for context -----------------------------
loads = [e["load_s"] for e in events if e["kind"] == "loaded" and e.get("load_s") is not None]
if loads:
    loads_sorted = sorted(loads)
    print(f"cold load times (s): n={len(loads)} min={loads_sorted[0]} median={loads_sorted[len(loads)//2]} max={loads_sorted[-1]}")

# ---- match letters ---------------------------------------------------------------------------------
letters = []
for persona in ("twain", "shackleton"):
    rows = [json.loads(l) for l in (ROOT / "data" / "Correspondence" / persona / "thread.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    for i, r in enumerate(rows, 1):
        if r["from"] == persona:
            letters.append({"persona": persona, "idx": i, "ts": r["ts"], "text": r["text"]})
letters.sort(key=lambda x: x["ts"])

print("\nper-letter match (letters whose local time-of-day has a [chat] line with chars>=len(text) within 0..8s before the thread ts):")
print(f"{'persona':10s} {'#':>3s} {'local ts':19s} {'len':>5s} {'nonlat':>6s} | {'chat ln':>7s} {'chars':>5s} {'dur_s':>7s} {'COLD':>5s} {'load_s':>6s} {'idle_before_s':>13s} {'day':>3s}")
matched = []
for L in letters:
    ldt = local_of(L["ts"])
    tod = ldt.hour * 3600 + ldt.minute * 60 + ldt.second + ldt.microsecond / 1e6
    cands = []
    for e in chats:
        d = tod - e["tod"]
        if 0 <= d <= 8 and e["chars"] >= len(L["text"]) and e["chars"] - len(L["text"]) <= 250:
            cands.append((d, e))
    ratio = nonlatin_ratio(L["text"])
    if len(cands) == 1:
        e = cands[0][1]
        matched.append((L, e, ratio))
        ib = e["idle_before"]
        sl = e["secs_load_end_to_start"]
        print(f"{L['persona']:10s} {L['idx']:3d} {ldt:%Y-%m-%d %H:%M:%S} {len(L['text']):5d} {ratio:6.3f} | {e['ln']:7d} {e['chars']:5d} {e['dur']:7.1f} {str(e['cold']):>5s} {str(e['load_s']):>6s} {('%.0f' % ib) if ib is not None else 'n/a':>13s} {e['day']:3d}"
              f"   pos_since_load={e['pos_since_load']} secs_since_load_end_at_start={('%.0f' % sl) if sl is not None else 'n/a'}")
    else:
        print(f"{L['persona']:10s} {L['idx']:3d} {ldt:%Y-%m-%d %H:%M:%S} {len(L['text']):5d} {ratio:6.3f} | {'NO MATCH' if not cands else 'AMBIGUOUS x%d' % len(cands)}")

print("\nsummary over matched letters:")
cold = [m for m in matched if m[1]["cold"]]
warm = [m for m in matched if not m[1]["cold"]]
print(f"  matched {len(matched)} of {len([l for l in letters])} letters; cold={len(cold)} warm={len(warm)}")
print(f"  degenerate (nonlatin>0.10): cold={sum(1 for m in cold if m[2] > 0.10)}/{len(cold)}  warm={sum(1 for m in warm if m[2] > 0.10)}/{len(warm)}")

# ---- hub-wide cold fraction, for context: how often is a call to this hub cold at all? ------------
print("\nhub-wide (all callers): cold fraction by idle gap before the request")
bins = [(0, 60), (60, 300), (300, 900), (900, 3600), (3600, 1e12)]
for lo, hi in bins:
    sel = [e for e in chats if e["idle_before"] is not None and lo <= e["idle_before"] < hi]
    c = sum(1 for e in sel if e["cold"])
    print(f"  idle {lo:>5.0f}-{('inf' if hi > 1e11 else '%5.0f' % hi):>5s}s: n={len(sel):5d} cold={c:5d}")

# ---- aside: unloads that land immediately after a long generation (idle clock = request START) ------
prev_chat = None
imm = 0
imm_long = 0
n_unload = 0
for ev in events:
    if ev["kind"] == "chat":
        prev_chat = ev
    elif ev["kind"] == "unload":
        n_unload += 1
        ev["abs"] = ev["day"] * 86400 + ev["tod"]
        if prev_chat is not None and 0 <= ev["abs"] - prev_chat["abs"] <= 2.0:
            imm += 1
            if prev_chat["dur"] > 240:
                imm_long += 1
print(f"\nunloads total={n_unload}; unloads landing <=2 s after a chat line's end={imm} (of which that chat ran >240 s: {imm_long})")
long_chats = [e for e in chats if e["dur"] > 300]
print(f"chat calls with duration > 300 s (>= idle-unload threshold): {len(long_chats)} of {len(chats)}")
