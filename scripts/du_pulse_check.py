"""
du_pulse_check — the persistent, structured wrapper over du_pulse.py (built 2026-08-29, J-0417,
docs/plans/du_pulse_rebuild.md). Modeled directly on gauge-check's proven four-way command split
(C:\\Users\\USER\\.claude\\skills\\gauge-check\\gauge_check.py): `run` records a real timestamped
reading, `watch` is the durable carry-forward register `/du-pulse` never had (the J-0120-shaped gap
the plan doc names), `history` trends one gauge across past runs, `board` is a fast no-recompute
check-in.

Where du_pulse.py's own report is a wall of text a session reads once and forgets, this tool reads
the additive `###PULSE_JSON_BEGIN###...###PULSE_JSON_END###` block du_pulse.py now prints after its
existing output (scripts/du_pulse.py, "[9] JSON SUMMARY BLOCK", added the same day) and PERSISTS it —
all 73 gauges, every run, per D-0094 (2026-08-29: snapshot everything, not just flagged/watched ones,
"was there an early signal in a gauge nobody was watching yet"). Watch-item resolution is manual-only
per D-0095 (2026-08-29) — this tool never claims to auto-detect whether a watched condition became
true; `run` only surfaces open watch-items alongside the new reading for a human/session to judge.

Store: C:\\Nascence\\docs\\du_pulse_checks.jsonl — one JSON object per line, IDs P-0001 upward.
Fields: id, ts, session, window (cut/last_restart/now/label from du_pulse.py's own JSON block),
gauge_count (73), categories (the full 4-category gauge snapshot), flags (du_pulse.py's own flags
list), severity (this tool's first-pass read per category — see severity_for_run below), open_watch
(ids of watch-items that were open at the time this run recorded, for later cross-reference).

Watch store: C:\\Nascence\\docs\\du_pulse_watches.jsonl — one JSON object per line, IDs W-0001
upward. Fields: id, ts_created, session, text, linked_plan, linked_job, status (open|resolved),
resolved_ts, resolved_by_session, resolved_note.

Usage:
  du_pulse_check.py run [--session <uuid>]
      Executes du_pulse.py (subprocess, real live data — same script, unmodified behavior), parses
      its JSON block, records ONE new P-XXXX snapshot of all 73 gauges, evaluates first-pass
      severity per the 4-category taxonomy (gauge_rethink.md "Taxonomy landing"), and prints any
      OPEN watch-items as a reminder (never auto-resolved — D-0095).
  du_pulse_check.py watch add "<text>" [--linked-plan SLUG] [--linked-job J-0001] [--session <uuid>]
      Records a new durable watch-item — the direct fix for the J-0120-shaped gap (a "watch this
      next time" ask with nowhere durable to live).
  du_pulse_check.py watch list [--open]
      Lists watch-items, optionally filtered to open ones.
  du_pulse_check.py watch resolve <id> --note "..." [--session <uuid>]
      Marks a watch-item resolved. Manual-only (D-0095) — no condition-detection logic; the note is
      the human/session's own judgment of what was found.
  du_pulse_check.py history --gauge <name>
      Trends one gauge's readings across every past P-XXXX run (searches all 4 categories for the
      given key). "name" matches a JSON key from the categories block, e.g. `newest_memory_write`,
      `judge_panel`, `dream_arcs`.
  du_pulse_check.py board
      Prints the LAST recorded P-XXXX snapshot — severity, flags, open watch-items — no recompute.
"""
import sys, os, json, argparse, subprocess
from pathlib import Path
from datetime import datetime, timezone

_SKILLS = Path(r"C:\Users\USER\.claude\skills")
sys.path.insert(0, str(_SKILLS / "_plan_tools_common"))
import common as ct

sys.stdout.reconfigure(encoding="utf-8")

STORE = ct.ROOT / "docs" / "du_pulse_checks.jsonl"
WATCH_STORE = ct.ROOT / "docs" / "du_pulse_watches.jsonl"
PULSE_SCRIPT = Path(__file__).parent / "du_pulse.py"
NOW = datetime.now(timezone.utc)

BEGIN_MARK = "###PULSE_JSON_BEGIN###"
END_MARK = "###PULSE_JSON_END###"

CATEGORY_ORDER = ("regression_alarms", "growth_trackers", "shadow_evidence", "engagement_texture")
CATEGORY_LABEL = {
    "regression_alarms": "REGRESSION ALARMS", "growth_trackers": "GROWTH TRACKERS",
    "shadow_evidence": "SHADOW-RUN EVIDENCE", "engagement_texture": "ENGAGEMENT/TEXTURE",
}


# ── generic jsonl load/save/next-id, same shape as gauge_check.py ──────────────────────────────

def _load(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in ct.read_text(path).splitlines() if l.strip()]


def _save(path, rows):
    ct.atomic_write_text(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def _next_id(rows, prefix):
    n = max((int(r["id"].split("-")[1]) for r in rows), default=0) + 1
    return f"{prefix}-{n:04d}"


# ── running du_pulse.py + parsing its additive JSON block ──────────────────────────────────────

def run_pulse():
    """Executes the real du_pulse.py (same file, unmodified existing behavior) as a subprocess and
    parses the additive JSON block it now prints after its existing report. Returns (summary_dict,
    raw_stdout). Raises RuntimeError with the raw output on any parse failure — never silently
    fabricates a reading."""
    proc = subprocess.run(
        [sys.executable, str(PULSE_SCRIPT)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
    )
    out = proc.stdout or ""
    if BEGIN_MARK not in out or END_MARK not in out:
        raise RuntimeError(
            f"du_pulse.py did not emit a JSON block (exit {proc.returncode}). "
            f"stderr tail: {(proc.stderr or '')[-500:]}")
    body = out.split(BEGIN_MARK, 1)[1].split(END_MARK, 1)[0].strip()
    try:
        summary = json.loads(body)
    except Exception as e:
        raise RuntimeError(f"du_pulse.py JSON block failed to parse: {e}\nBody: {body[:300]}")
    return summary, out


# ── first-pass severity per the 4-category taxonomy (gauge_rethink.md "Taxonomy landing") ──────
# Heuristic, not a formula handed down from on high (same posture as gauge_check.py's own
# severity_for) — the point is a fast, defensible FIRST read of a 73-gauge snapshot, not a final
# verdict. Regression alarms get a real ALARM/clear read because their whole point is "fires
# loudly, bad direction" (du_pulse.py's own `flags` list already IS that read, mirrored here).
# The other 3 categories are non-diagnostic by design (growth trackers: low=early not broken;
# shadow evidence: still-experimental; engagement/texture: descriptive) — they get an activity
# COUNT, not a verdict, so "N/15 growth trackers showing activity" is a fact, not a judgment call
# this tool has any business making unilaterally.

def _has_signal(v):
    if v is None:
        return False
    if isinstance(v, dict):
        if not v:
            return False
        for vv in v.values():
            if isinstance(vv, (int, float)) and vv:
                return True
            if isinstance(vv, str) and vv:
                return True
            if isinstance(vv, (list, dict)) and vv:
                return True
        return False
    if isinstance(v, list):
        return bool(v)
    return bool(v)


ALARM_TERMS = ("over cap", "no memory write", "written this window", "critical", "live leak")


def severity_for_run(categories, flags):
    sev = {}
    ra_alarm = any(any(t in f.lower() for t in ALARM_TERMS) for f in flags)
    sev["regression_alarms"] = "ALARM" if ra_alarm else "clear"
    for cat in ("growth_trackers", "shadow_evidence", "engagement_texture"):
        gauges = categories.get(cat) or {}
        active = sum(1 for v in gauges.values() if _has_signal(v))
        sev[cat] = f"{active}/{len(gauges)} showing activity" if gauges else "n/a"
    return sev


# ── watch-items (manual-only resolution, D-0095) ────────────────────────────────────────────────

def _open_watches():
    return [w for w in _load(WATCH_STORE) if w["status"] == "open"]


def cmd_watch_add(a):
    rows = _load(WATCH_STORE)
    rec = {
        "id": _next_id(rows, "W"), "ts_created": NOW.isoformat(), "session": a.session,
        "text": a.text.strip(), "linked_plan": a.linked_plan, "linked_job": a.linked_job,
        "status": "open", "resolved_ts": None, "resolved_by_session": None, "resolved_note": None,
    }
    rows.append(rec)
    _save(WATCH_STORE, rows)
    ct.log_event(tool="du-pulse-check", kind="watch_added", ref=rec["id"],
                detail=rec["text"][:160], session=a.session)
    link = f" [plan:{a.linked_plan}]" if a.linked_plan else (f" [job:{a.linked_job}]" if a.linked_job else "")
    print(f"{rec['id']} watching: {rec['text']}{link}")


def cmd_watch_list(a):
    rows = _load(WATCH_STORE)
    if a.open:
        rows = [r for r in rows if r["status"] == "open"]
    if not rows:
        print("No watch-items recorded yet." if not a.open else "No OPEN watch-items.")
        return
    print(f"# WATCH-ITEMS ({len(rows)}{', open only' if a.open else ''})\n")
    for r in rows:
        mark = "○ open" if r["status"] == "open" else "● resolved"
        link = f" [plan:{r['linked_plan']}]" if r.get("linked_plan") else (
            f" [job:{r['linked_job']}]" if r.get("linked_job") else "")
        print(f"  {r['id']}  {mark}  {r['ts_created'][:16]}{link}")
        print(f"    {r['text']}")
        if r["status"] == "resolved":
            print(f"    -> resolved {r['resolved_ts'][:16]}: {r['resolved_note']}")


def cmd_watch_resolve(a):
    rows = _load(WATCH_STORE)
    rec = next((r for r in rows if r["id"] == a.id), None)
    if rec is None:
        print(f"No watch-item {a.id!r} found.")
        return
    if rec["status"] == "resolved":
        print(f"{a.id} is already resolved ({rec['resolved_ts'][:16]}: {rec['resolved_note']}).")
        return
    rec["status"] = "resolved"
    rec["resolved_ts"] = NOW.isoformat()
    rec["resolved_by_session"] = a.session
    rec["resolved_note"] = a.note.strip()
    _save(WATCH_STORE, rows)
    ct.log_event(tool="du-pulse-check", kind="watch_resolved", ref=a.id,
                detail=rec["resolved_note"][:160], session=a.session)
    print(f"{a.id} resolved: {rec['resolved_note']}")


# ── run / history / board ───────────────────────────────────────────────────────────────────────

def cmd_run(a):
    summary, raw = run_pulse()
    categories = summary.get("categories") or {}
    flags = summary.get("flags") or []
    sev = severity_for_run(categories, flags)

    rows = _load(STORE)
    open_watches = _open_watches()
    rec = {
        "id": _next_id(rows, "P"), "ts": NOW.isoformat(), "session": a.session,
        "window": summary.get("window"), "gauge_count": summary.get("gauge_count"),
        "categories": categories, "flags": flags, "severity": sev,
        "open_watch": [w["id"] for w in open_watches],
    }
    rows.append(rec)
    _save(STORE, rows)
    ct.log_event(tool="du-pulse-check", kind="run_recorded", ref=rec["id"],
                detail=f"{rec['gauge_count']} gauges, {len(flags)} flag(s), "
                       f"regression={sev.get('regression_alarms')}", session=a.session)

    print(f"{rec['id']}  {rec['ts'][:16]}  {rec['gauge_count']} gauges snapshotted\n")
    for cat in CATEGORY_ORDER:
        print(f"  {CATEGORY_LABEL[cat]:24} {sev.get(cat, 'n/a')}")
    print()
    if flags:
        print(f"# FLAGS ({len(flags)})")
        for f in flags:
            print(f"  - {f}")
    else:
        print("# FLAGS: none")
    if open_watches:
        print(f"\n# OPEN WATCH-ITEMS ({len(open_watches)}) — check manually against this reading (D-0095: no auto-detect)")
        for w in open_watches:
            print(f"  {w['id']}: {w['text']}")
    else:
        print("\n# OPEN WATCH-ITEMS: none")


def cmd_history(a):
    rows = _load(STORE)
    if not rows:
        print("No du_pulse_check runs recorded yet.")
        return
    rows.sort(key=lambda r: r["ts"])
    found_any = False
    print(f"# HISTORY for gauge {a.gauge!r} — {len(rows)} run(s) checked\n")
    for r in rows:
        hit = None
        hit_cat = None
        for cat, gauges in (r.get("categories") or {}).items():
            if a.gauge in gauges:
                hit = gauges[a.gauge]
                hit_cat = cat
                break
        if hit is None:
            continue
        found_any = True
        print(f"{r['ts'][:16]}  {r['id']}  [{hit_cat}]")
        print(f"  {json.dumps(hit, ensure_ascii=False)[:200]}")
    if not found_any:
        print(f"(gauge {a.gauge!r} not found in any recorded run's categories block — check the "
              f"exact key name, e.g. via `board`)")


def cmd_board(a):
    rows = _load(STORE)
    if not rows:
        print("No du_pulse_check runs recorded yet — run `du_pulse_check.py run` first.")
        return
    last = max(rows, key=lambda r: r["ts"])
    print(f"# BOARD — last recorded run: {last['id']}  {last['ts'][:16]}\n")
    sev = last.get("severity") or {}
    for cat in CATEGORY_ORDER:
        print(f"  {CATEGORY_LABEL[cat]:24} {sev.get(cat, 'n/a')}")
    flags = last.get("flags") or []
    print()
    if flags:
        print(f"# FLAGS ({len(flags)})")
        for f in flags:
            print(f"  - {f}")
    else:
        print("# FLAGS: none")
    open_ids = last.get("open_watch") or []
    all_watches = {w["id"]: w for w in _load(WATCH_STORE)}
    still_open = [wid for wid in open_ids if all_watches.get(wid, {}).get("status") == "open"]
    if still_open:
        print(f"\n# OPEN WATCH-ITEMS ({len(still_open)})")
        for wid in still_open:
            print(f"  {wid}: {all_watches[wid]['text']}")
    else:
        print("\n# OPEN WATCH-ITEMS: none")


def main():
    p = argparse.ArgumentParser(prog="du_pulse_check")
    sub = p.add_subparsers(dest="cmd", required=True)

    lr = sub.add_parser("run")
    lr.add_argument("--session")
    lr.set_defaults(fn=cmd_run)

    watch = sub.add_parser("watch")
    wsub = watch.add_subparsers(dest="watch_cmd", required=True)

    wa = wsub.add_parser("add")
    wa.add_argument("text")
    wa.add_argument("--linked-plan")
    wa.add_argument("--linked-job")
    wa.add_argument("--session")
    wa.set_defaults(fn=cmd_watch_add)

    wl = wsub.add_parser("list")
    wl.add_argument("--open", action="store_true")
    wl.set_defaults(fn=cmd_watch_list)

    wr = wsub.add_parser("resolve")
    wr.add_argument("id")
    wr.add_argument("--note", required=True)
    wr.add_argument("--session")
    wr.set_defaults(fn=cmd_watch_resolve)

    lh = sub.add_parser("history")
    lh.add_argument("--gauge", required=True)
    lh.set_defaults(fn=cmd_history)

    lb = sub.add_parser("board")
    lb.set_defaults(fn=cmd_board)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
