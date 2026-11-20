"""J-3431 / F-4065: does Du downtime inflate stand life for the D-0547 sit gate?
Read-only. Reads <data>/nascence.log (uptime instrument) and <data>/commitment_ledger.jsonl.
Usage: python scripts/j3431_standlife_downtime.py [DATA_DIR] [OUT_JSON]
Instrument: 'Nascence is awake' = boot, 'Nascence shutting down' = clean stop, any log line = alive.
A gap between consecutive log lines > GAP_S is treated as down (crash / hang / stall) so a missing shutdown line
(crash) still ends the session at the last line seen.
"""
import sys, re, json, bisect, datetime, collections
from pathlib import Path

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Nascence\data")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else None
GAP_S = 600.0
TS = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3}) ")

def parse_log():
    """Returns [(t, kind)], kind in ''|'boot'|'shut'. boot = the live store opening (a full Du process start)."""
    out = []
    for line in open(DATA / "nascence.log", encoding="utf-8", errors="replace"):
        m = TS.match(line)
        if not m:
            continue
        t = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp() + int(m.group(2)) / 1000
        if out and t < out[-1][0] - 5:
            continue          # out-of-order line: ignore
        k = ""
        if "Memory store initialised" in line and ("data" + chr(92) + "memory" + chr(92) + "nascence.db") in line:
            k = "boot"
        elif "Nascence shutting down" in line:
            k = "shut"
        out.append((t, k))
    return out

def up_intervals(lines, gap_s, t_from=0.0):
    """Up intervals = runs of log lines cut at: a gap > gap_s, a shutdown line, or a boot line (a new process)."""
    iv = []
    start = prev = None
    prev_kind = ""
    for t, k in lines:
        if t < t_from:
            continue
        if start is None:
            start = prev = t
        elif t - prev > gap_s or prev_kind == "shut" or k == "boot":
            iv.append((start, prev)); start = t
        prev, prev_kind = t, k
    if start is not None:
        iv.append((start, prev))
    return iv

def uptime_between(iv, starts, a, b):
    """seconds of up time inside [a,b]"""
    if b <= a:
        return 0.0
    i = max(0, bisect.bisect_right(starts, a) - 1)
    tot = 0.0
    while i < len(iv) and iv[i][0] < b:
        lo, hi = max(a, iv[i][0]), min(b, iv[i][1])
        if hi > lo:
            tot += hi - lo
        i += 1
    return tot

T_FROM = datetime.datetime(2026, 6, 30).timestamp()

def main():
    lines = parse_log()
    iv = up_intervals(lines, GAP_S, T_FROM)
    starts = [x[0] for x in iv]
    rows = [json.loads(l) for l in open(DATA / "commitment_ledger.jsonl", encoding="utf-8") if l.strip()]
    formed = {r["id"]: r for r in rows if r.get("event") == "formed"}
    dis = [r for r in rows if r.get("event") == "dissolved"]
    log_lo, log_hi = iv[0][0], iv[-1][1]
    res = {"log_from": log_lo, "log_last": log_hi, "log_lines": len(lines),
           "boot_lines": sum(1 for _, k in lines if k == "boot"), "shutdown_lines": sum(1 for _, k in lines if k == "shut"),
           "up_intervals": len(iv), "gap_s": GAP_S, "total_wall_s": log_hi - log_lo, "total_up_s": sum(b - a for a, b in iv)}
    out_rows = []
    for r in dis:
        f = formed.get(r["id"])
        lb = f.get("load_bearing") if f else None
        held = r["ts"] - r["lifespan_seconds"]
        covered = held >= log_lo and r["ts"] <= log_hi
        up = uptime_between(iv, starts, held, r["ts"]) if covered else None
        out_rows.append({"id": r["id"], "ts": r["ts"], "life_s": r["lifespan_seconds"], "scans": r.get("lifespan_scans"),
                         "reaff": r.get("reaffirmed"), "sit_gate": r.get("sit_gate"), "formed_seen": bool(f),
                         "load_bearing": lb, "up_s": up, "covered": covered})
    res["dissolved_total"] = len(dis)
    res["formed_matched"] = sum(1 for x in out_rows if x["formed_seen"])
    res["load_bearing_counts"] = dict(collections.Counter(str(x["load_bearing"]) for x in out_rows))
    json.dump({"summary": res, "rows": out_rows}, open(OUT, "w") if OUT else sys.stdout, indent=0)

if __name__ == "__main__":
    main()
