"""J-3036 / F-3743 (P-0098) -- READ-ONLY replay of the invention v2 check over logged Lane 2 tick rows.
Reads data/lane2_shadow.jsonl (path arg or default C:/Nascence/data/lane2_shadow.jsonl), rebuilds each row's
percepts from what the row stored (world_fields, and the sounds/smells/daylight lines of percept_lines), calls
core.lane2._invention_check, and reports before/after per window. Writes nothing. No model calls.
Fidelity caveat: the row stores GLOSSED sound/smell text ('waves on shingle'), not raw tokens, so the
sound/smell licence is replayed on the gloss; the script reports how often its rebuilt current/legacy verdict
equals the stored one (fidelity) so the approximation is measured, not assumed."""
import sys, json, re, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import lane2 as L   # noqa: E402

LOG = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Nascence/data/lane2_shadow.jsonl")
WINDOWS = {
    "post_boot_10-29": (dt.datetime(2026, 10, 29, 18, 30).timestamp(), 9e12),
    "10-13..10-20": (dt.datetime(2026, 10, 13).timestamp(), dt.datetime(2026, 10, 21).timestamp()),
}

def _line(lines, key):
    m = re.search(r"^- " + re.escape(key) + r": (.*)$", lines or "", re.M)
    return [x.strip() for x in m.group(1).split(",") if x.strip()] if m else []

def percepts_of(r):
    lines = r.get("percept_lines") or ""
    dl = _line(lines, "daylight")
    return {"world_fields": r.get("world_fields") or [],
            "world": {"sounds": _line(lines, "sounds"), "smells": _line(lines, "smells"),
                      "daylight": (dl[0] if dl else r.get("daylight") or "")}}

def main():
    rows = []
    for l in LOG.open(encoding="utf-8", errors="replace"):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if isinstance(r.get("invention"), dict) and "notice" in r:
            rows.append(r)
    for name, (a, b) in WINDOWS.items():
        w = [r for r in rows if a <= float(r.get("ts") or 0) < b]
        n = len(w)
        if not n:
            print(name, "n=0"); continue
        fid_cur = fid_leg = 0
        cur = leg = v2 = 0
        only_unc = 0
        topics = {}
        for r in w:
            res = L._invention_check(r, percepts_of(r))
            stored = r["invention"]
            fid_cur += res["invention_flag"] == bool(stored.get("invention_flag"))
            sl = stored["invention_flag_legacy"] if "invention_flag_legacy" in stored else stored.get("invention_flag")
            fid_leg += res["invention_flag_legacy"] == bool(sl)
            cur += bool(stored.get("invention_flag"))
            leg += bool(sl)
            v2 += res["invention_flag_v2"]
            if stored.get("invention_flag") and not res["invention_flag_v2"]:
                only_unc += 1
            for t in res["invented_topics_v2"]:
                topics[t] = topics.get(t, 0) + 1
        print(f"{name}: n={n} stored_current={cur} ({cur/n:.1%}) stored_legacy={leg} ({leg/n:.1%}) "
              f"v2={v2} ({v2/n:.1%}) cleared_by_v2={only_unc}")
        print(f"   replay fidelity vs stored: current {fid_cur}/{n}, legacy {fid_leg}/{n}; v2 topics {topics}")

if __name__ == "__main__":
    main()
