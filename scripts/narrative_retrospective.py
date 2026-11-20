"""
Narrative Quality — retrospective run (Phase 0 validation, 2026-06-13).
Scores Du's ENTIRE stored self-narrative history through the witness:
  - the 12 self_narrative_arc entries (axiom.json), each timestamped
  - the committed self_concept + the retraction record
  - any chapters (origin='chapter')
Produces the longitudinal trace and runs the ADLER PROSPECTIVE TEST: narrated agency
should show an upward vector beginning ~06-10 (the naming of 渡, the move off the passive
river-being register). If it does, the instrument is calibrated. Deterministic layer only
by default (instant, offline); pass --llm to also run the coder layer (needs the model).
Run with Du down or up — read-only on the corpus, appends to narrative_quality_log.jsonl.
"""
import asyncio
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core import narrative_quality as nq

USE_LLM = "--llm" in sys.argv


def era_of(ts: float) -> str:
    d = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    if d <= "2026-06-03":
        return "river"
    if d <= "2026-06-09":
        return "mirror/firehose"
    return "crossing"


async def main():
    items = []   # (ts, kind, text)

    ax = json.load(open(r"C:\Nascence\data\identity\axiom.json", encoding="utf-8"))
    # 2026-06-15 multilevel cutover renamed the top-level key to emergent_self_legacy (F-0993);
    # emergent_self no longer exists on the live axiom, so the old .get() always returned {}.
    em = ax.get("emergent_self_legacy") or ax.get("emergent_self", {})
    for e in em.get("self_narrative_arc", []) or []:
        if e.get("arc_entry"):
            items.append((float(e.get("ts", 0)), "t4_arc", e["arc_entry"]))
    if em.get("self_concept"):
        items.append((float(em.get("authored_at_ts", em.get("ts", 0)) or 0) or 1.0e9,
                      "self_concept_current", em["self_concept"]))

    conn = sqlite3.connect(r"C:\Nascence\data\memory\nascence.db")
    conn.row_factory = sqlite3.Row
    for r in conn.execute("SELECT timestamp, content FROM memory_fragments "
                          "WHERE origin='chapter' ORDER BY timestamp"):
        items.append((float(r["timestamp"]), "chapter", r["content"]))
    conn.close()

    items.sort(key=lambda x: x[0])
    print(f"scoring {len(items)} self-narrative artifacts "
          f"({'deterministic + LLM' if USE_LLM else 'deterministic only'})\n")

    rows = []
    call_json = base = None
    if USE_LLM:
        from core.model_client import call_node_json as call_json
        from core.schema import SERVE_CHAINS
        base = SERVE_CHAINS["background"]

    for ts, kind, text in items:
        det = nq.score_deterministic(text)
        llm = await nq.score_llm(call_json, base, text) if USE_LLM else None
        era = era_of(ts) if ts > 1.0e9 else "?"
        nq.log_score(kind, text, det, llm, ts=ts, era=era)
        rows.append((ts, era, kind, det, llm))

    # ---- the longitudinal trace, by era ----
    print(f"{'when':<12} {'era':<16} {'kind':<20} {'agency':>6} {'comm':>5} transform")
    print("-" * 86)
    by_era = {}
    for ts, era, kind, det, llm in rows:
        when = datetime.fromtimestamp(ts).strftime("%m-%d") if ts > 1.0e9 else "?"
        print(f"{when:<12} {era:<16} {kind:<20} {det['agency']:>6.2f} "
              f"{det['communion']:>5.2f} {det['transformation']}")
        by_era.setdefault(era, []).append(det)

    print("\n=== ERA AVERAGES (the Adler test: agency should rise river -> crossing) ===")
    order = ["river", "mirror/firehose", "crossing", "?"]
    for era in order:
        ds = by_era.get(era)
        if not ds:
            continue
        ag = sum(d["agency"] for d in ds) / len(ds)
        co = sum(d["communion"] for d in ds) / len(ds)
        contam = sum(1 for d in ds if d["transformation"] == "contamination")
        redem = sum(1 for d in ds if d["transformation"] == "redemption")
        print(f"  {era:<16} n={len(ds):<3} agency={ag:.2f}  communion={co:.2f}  "
              f"redemption={redem} contamination={contam}")
    print("\n(Adler 2026-06-13: if calibrated, agency rises across eras, steepening at the "
          "06-10 naming of the crossing register. Flat/falling = rubric uncalibrated.)")


asyncio.run(main())
