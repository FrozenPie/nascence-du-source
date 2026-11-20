"""scripts/garden_netting_gate.py (J-2112, garden_upgrade, D-0418 ruling (i), travis 2026-10-15).

The D-0278 netting-discoverability check came back null three times (F-1946, F-2252, F-2734) for one structural
reason: the affordance text only renders when a VULNERABLE shoot-stage crop stands in a bed slot, and no such shoot
has existed since 2026-09-04 (dead seed bank, zero sow deeds, the tin in the wood). D-0418 ruled: stop re-reading on
the calendar; queue the read ONLY when the event happens. This is that gate.

What it does (zero LLM, read-only on Du's data, idempotent):
  * reads data/garden_ledger.jsonl and data/garden.json;
  * EVENT A: the first ledger row with deed == "sow";
  * EVENT B: a plant at stage "shoot" standing in a bed slot (slot is not None) whose species is VULNERABLE by the
    same structural rule core/garden.py's _bed_vulnerable() uses (catalogue kind != weed and life not evergreen /
    herbaceous), looked up in core.garden.CATALOGUE so it never goes stale against the species table;
  * when either fires and the marker says it has not fired before, files ONE job-queue entry (the D-0278 netting read,
    the J-1679 check's successor, plan garden_upgrade, source decision:D-0418) through job_queue.py add, quoting the
    event, then writes the marker (docs/reviews/garden_netting_gate_state.json) so it never files twice;
  * otherwise prints the state and exits 0. Any failure prints a one-line reason and exits 0: the gate must never break
    the maintenance pass that runs it (plan-maintain step 7c).

It never writes under data/ (the write fence stays untouched; the marker lives under docs/reviews/). Nothing here
reaches Du: no hint, no world change (D-0418 (iii) was deliberately not chosen).

Usage:
  python scripts/garden_netting_gate.py [--ledger PATH] [--garden PATH] [--marker PATH] [--dry-run] [--session UUID]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "garden_ledger.jsonl"
GARDEN = ROOT / "data" / "garden.json"
MARKER = ROOT / "docs" / "reviews" / "garden_netting_gate_state.json"
JOB_QUEUE = Path.home() / ".claude" / "skills" / "job-queue" / "job_queue.py"
VULNERABLE_STAGES = ("shoot",)

JOB_TITLE = ("D-0278 netting-discoverability read (event-gated successor of J-1679/F-2734; D-0418 (i)): "
             "a vulnerable shoot now stands in the bed -- did the exposure sentence render, and did Du net it?")
JOB_BRIEFING = (
    "Filed automatically by scripts/garden_netting_gate.py (J-2112, D-0418 ruling (i)) because the event D-0278's "
    "check waits for has happened: {event}. READ F-2734 FIRST (the third null pickup; it carries the method, the "
    "restart/merge gates and the instrument caveats), then F-2252 and F-1946, and D-0278 / D-0333 for context. "
    "READ-ONLY, Du may be live. WHAT TO CHECK: (1) from the event's timestamp on, did a vulnerable shoot-stage crop "
    "(core/garden.py _bed_vulnerable: catalogue kind != weed, life not evergreen/herbaceous) stand in an un-netted bed "
    "slot by day, and for how many live hours; (2) did the exposure sentence / 'one seed-leaf pecked through' clause "
    "render in Du's prompts (grep data/nascence.log and the garden prompt ledger for the J-1350 text); (3) did Du net "
    "the bed (a 'net' deed in data/garden_ledger.jsonl; the 09-28 'unnet' is a known false positive), look at the "
    "netting, or speak of it; (4) eaten_by_birds / volunteer events in data/garden_events.jsonl after the event; "
    "(5) D-0278's defeater: netting never used despite being genuinely surfaced over a real window -- say whether the "
    "window is real yet. OUTCOME: findings_log.py record with quoted rows (--confidence verified); if the defeater "
    "clause fires, open a decision; plan_state.py note on garden_upgrade. Do not re-run this on a calendar: if the "
    "window is too short, defer THIS job with --not-before.")


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        for ln in Path(path).read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                continue
    except Exception:
        pass
    return rows


def _catalogue() -> dict:
    try:
        sys.path.insert(0, str(ROOT))
        from core.garden import CATALOGUE
        return dict(CATALOGUE)
    except Exception:
        return {}


def vulnerable(species: str, catalogue: dict | None = None) -> bool:
    """core/garden.py _bed_vulnerable()'s rule, applied by species name: not a weed, life not evergreen/herbaceous."""
    cat = (catalogue if catalogue is not None else _catalogue()).get(species) or {}
    if not cat:
        return False
    return cat.get("kind") != "weed" and cat.get("life") not in ("evergreen", "herbaceous")


def detect(ledger: Path = LEDGER, garden: Path = GARDEN, catalogue: dict | None = None) -> dict | None:
    """The event, or None. Event A (first sow deed) wins over event B (a vulnerable shoot in a bed slot)."""
    for r in _read_jsonl(ledger):
        if r.get("deed") == "sow":
            return {"kind": "sow", "ts": r.get("ts"), "row": r}
    try:
        g = json.loads(Path(garden).read_text(encoding="utf-8"))
    except Exception:
        return None
    plants = g.get("plants") or {}
    items = plants.items() if isinstance(plants, dict) else enumerate(plants)
    for pid, p in items:
        if not isinstance(p, dict):
            continue
        if p.get("stage") in VULNERABLE_STAGES and p.get("slot") is not None and vulnerable(str(p.get("species")), catalogue):
            return {"kind": "shoot", "ts": p.get("germ_ts") or p.get("sown_ts"), "plant_id": pid,
                    "species": p.get("species"), "stage": p.get("stage"), "slot": p.get("slot"),
                    "netted": g.get("netted")}
    return None


def _load_marker(marker: Path) -> dict:
    try:
        return json.loads(Path(marker).read_text(encoding="utf-8"))
    except Exception:
        return {}


def file_job(title: str, briefing: str, session: str | None) -> str:
    """Files the read job through job_queue.py add (the one sanctioned writer of docs/job_queue.jsonl). Returns its
    first output line (e.g. 'J-2200 ADDED ...'). Raises on failure so the caller does not write the marker."""
    cmd = [sys.executable, str(JOB_QUEUE), "add", "--title", title, "--briefing", briefing, "--urgency", "3",
           "--autonomy", "ready", "--category", "analysis", "--source", "decision:D-0418", "--plan", "garden_upgrade"]
    if session:
        cmd += ["--session", session]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "job_queue.py add failed").strip()[:400])
    return (p.stdout or "").strip().splitlines()[-1] if p.stdout.strip() else "ADDED"


def run(ledger: Path = LEDGER, garden: Path = GARDEN, marker: Path = MARKER, dry_run: bool = False,
        session: str | None = None, filer=file_job, catalogue: dict | None = None) -> dict:
    """One gate pass. Returns a dict describing what happened; never raises."""
    out = {"ts": round(time.time(), 1), "event": None, "fired_before": False, "filed": None, "dry_run": dry_run}
    try:
        state = _load_marker(marker)
        if state.get("fired"):
            out["fired_before"] = True
            out["event"] = state.get("event")
            out["filed"] = state.get("filed")
            return out
        ev = detect(ledger, garden, catalogue)
        out["event"] = ev
        if ev is None:
            return out
        ev_text = (f"first sow deed at ts {ev.get('ts')}: {json.dumps(ev.get('row'), ensure_ascii=False)[:200]}"
                   if ev["kind"] == "sow" else
                   f"vulnerable shoot in a bed slot: {ev.get('species')} ({ev.get('plant_id')}) stage {ev.get('stage')} "
                   f"slot {ev.get('slot')} netted={ev.get('netted')} germ_ts {ev.get('ts')}")
        if dry_run:
            out["filed"] = f"DRY-RUN would file: {JOB_TITLE[:80]}..."
            return out
        filed = filer(JOB_TITLE, JOB_BRIEFING.format(event=ev_text), session)
        out["filed"] = filed
        try:
            Path(marker).parent.mkdir(parents=True, exist_ok=True)
            Path(marker).write_text(json.dumps({"fired": True, "fired_ts": out["ts"], "event": ev, "event_text": ev_text,
                                                "filed": filed, "by": "scripts/garden_netting_gate.py (J-2112, D-0418)"},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as exc:
            out["marker_error"] = f"{type(exc).__name__}: {exc}"
        return out
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ledger", default=str(LEDGER))
    ap.add_argument("--garden", default=str(GARDEN))
    ap.add_argument("--marker", default=str(MARKER))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--session", "--session-id", dest="session", default=None)
    a = ap.parse_args()
    res = run(Path(a.ledger), Path(a.garden), Path(a.marker), a.dry_run, a.session)
    tag = ("already fired" if res["fired_before"] else "FIRED" if res.get("filed") else "no event" if res.get("event") is None else "event, not filed")
    print(f"[garden-netting-gate] {tag}: " + json.dumps(res, ensure_ascii=False, default=str)[:600])
    return 0


if __name__ == "__main__":
    sys.exit(main())
