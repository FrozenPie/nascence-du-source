"""
Proof for J-3302 (T4 tension lifecycle analysis). The analysis script is read-only; this test checks its arithmetic on a
synthetic world in a temp dir, and the two code facts the report rests on.

  [1] the rest matcher: a felt-number-only change keeps token Jaccard 0.667 (> 0.5, rest holds); a change of BOTH
      numbers drops it to 0.43 (rest silently stops matching).  Re-stated from nodes/subconscious_node.py.
  [2] _t4_label_key (real function, imported) differs per felt number, so the fatigue counter splits.
  [3] family() merges the number variants and the 40-char / 60-char log truncations.
  [4] end to end on a temp live dir (log + probation jsonl + judge jsonl + state json + sqlite): hearings, chains,
      judged, admitted, probation, solidify, rest counted per family; the first hearing after the solidify is timed.
  [5] discharge arithmetic through the REAL core.tension_ledger.score_tension: a prediction_error source is NOT remapped
      by get_event_sources (critic_rejection only), so a 0.6 drain takes 4.0 -> 1.6 and the count stays 4.
  [6] isolation: nothing under the live data dir was written (mtime check on the files the script reads).

  python scripts/_test_J-3302_tension_lifecycle.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import core  # noqa: E402,F401  (core BEFORE anything lab-ish)
from core import tension_ledger as TL  # noqa: E402
import analysis_J3302_tension_lifecycle as A  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="J3302_"))
ok = True


def check(name, cond, extra=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + (("  " + str(extra)) if extra else ""))
    ok = ok and bool(cond)


# [1] rest matcher
base = "prediction_error:factual_recall (felt 0.95 vs real 0.50)"
check("[1a] felt-only change keeps the rest (Jaccard > 0.5)",
      A.jacc(A.toks(base), A.toks("prediction_error:factual_recall (felt 0.92 vs real 0.50)")) > 0.5,
      round(A.jacc(A.toks(base), A.toks("prediction_error:factual_recall (felt 0.92 vs real 0.50)")), 3))
two = A.jacc(A.toks("prediction_error:comprehension (felt 0.00 vs real 0.50)"),
             A.toks("prediction_error:comprehension (felt 0.10 vs real 0.85)"))
check("[1b] both numbers changing breaks the rest (Jaccard <= 0.5)", two <= 0.5, round(two, 3))

# [2] the real label key function splits per number
try:
    from nodes.subconscious_node import SubconsciousNode
    real_key = SubconsciousNode._t4_label_key
    check("[2a] real _t4_label_key == copy in the analysis script",
          real_key(base) == A.label_key(base))
    check("[2b] the fatigue key differs between felt 0.95 and 0.92",
          real_key(base) != real_key("prediction_error:factual_recall (felt 0.92 vs real 0.50)"))
except Exception as exc:  # the node import can be heavy; fall back to the copy but say so
    print("NOTE node import failed (%r); using the copy" % (exc,))
    check("[2b] copy: key differs", A.label_key(base) != A.label_key(base.replace("0.95", "0.92")))

# [3] family()
check("[3a] family merges number variants",
      A.family(base) == A.family("prediction_error:factual_recall (felt 0.92 vs re")
      == "prediction_error:factual_recall")
check("[3b] family merges 40- and 60-char truncations of a text label",
      A.family("unresolved: the Bluebird's arrival") == A.family("unresolved: the bluebird's arrival"))

# [4] synthetic live dir
live = TMP / "live"
(d := live / "data" / "logs").mkdir(parents=True)
(live / "data" / "memory").mkdir(parents=True)
t0 = time.mktime(time.strptime("2026-10-30 13:58:29", "%Y-%m-%d %H:%M:%S"))
lines = [
    "2026-10-30 12:00:00,000 [nascence.subconscious] [subconscious] T4 CHAIN — tension='prediction_error:factual_recall (felt 0.95 vs re' → evidence ✓ → delta='x' → authored",
    "2026-10-30 13:00:00,000 [nascence.subconscious] [subconscious] T4 considered 3 fragment(s) — no change: weighed the crossings — no genuine movement, still circling (tension: 'prediction_error:factual_recall (felt 0.95 vs real 0.50)')",
    "2026-10-30 13:58:29,000 [nascence.subconscious] [subconscious] T4 probation RESOLVED → solidify (integration={})",
    "2026-10-30 13:58:52,000 [nascence.subconscious] [subconscious] T4 CHAIN — tension='prediction_error:factual_recall (felt 0.92 vs re' → evidence ✓ → delta='y' → authored",
    "2026-10-31 15:23:35,000 [nascence.subconscious] [subconscious] T4 question RESTED after 3 no-movement hearings: 'prediction_error:factual_recall (felt 0.95 vs real 0.50)' (returns in 3d)",
    "2026-10-31 15:23:36,000 [nascence.subconscious] [subconscious] T4 considered 3 fragment(s) — no change: weighed the crossings — no genuine movement, still circling (tension: 'prediction_error:factual_recall (felt 0.95 vs real 0.50)')",
]
(live / "data" / "nascence.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
t_chain1 = time.mktime(time.strptime("2026-10-30 12:00:00", "%Y-%m-%d %H:%M:%S"))
(d / "provisional_identity.jsonl").write_text("\n".join(json.dumps(x) for x in [
    {"ts": t_chain1 + 60, "event": "open", "theme": "prediction_error:factual_recall (felt 0.95 vs real 0.50)"},
    {"ts": t0, "event": "solidify", "theme": "prediction_error:factual_recall (felt 0.95 vs real 0.50)"},
]) + "\n", encoding="utf-8")
(d / "t4_emissary_judge.jsonl").write_text(json.dumps({"ts": t_chain1 + 30, "emissary_warranted": 0.7}) + "\n", encoding="utf-8")
(live / "data" / "contradiction_ledger_log.jsonl").write_text(json.dumps({"ts": t0}) + "\n", encoding="utf-8")
(live / "data" / "subconscious_state.json").write_text(json.dumps({"t4_rests": [], "t4_fatigue_counts": {}}), encoding="utf-8")
db = live / "data" / "memory" / "nascence.db"
con = sqlite3.connect(db)
con.execute("CREATE TABLE shadow_events (event_id TEXT, timestamp REAL, cycle_id TEXT, raw_input TEXT, rejected_draft TEXT,"
            " corrections TEXT, emotion_primary TEXT, embedding BLOB, resolved INT DEFAULT 0, source TEXT)")
for i in range(4):   # four prediction_error events inside the newest-300 window before the solidify
    con.execute("INSERT INTO shadow_events VALUES (?,?,?,?,?,?,?,?,?,?)",
                (f"e{i}", t0 - 600 * (i + 1), "c", "r", "d", json.dumps([base]), "x", None, 0, "prediction_error"))
con.commit(); con.close()
before = {p: p.stat().st_mtime_ns for p in (live / "data").rglob("*") if p.is_file()}
out = TMP / "out"
sys.argv = ["x", "--live", str(live), "--out", str(out)]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    A.main()
S = json.load(open(out / "summary.json", encoding="utf-8"))
T = json.load(open(out / "family_table.json", encoding="utf-8"))
fr = [r for r in T if r["family"] == "prediction_error:factual_recall"][0]
check("[4a] hearings counted (2 chains + 2 considered)", fr["hearings"] == 4 and fr["chains_authored"] == 2, fr["hearings"])
check("[4b] rest, probation, solidify, judged, admitted counted",
      (fr["rests"], fr["probations"], fr["solidified"], fr["judged"], fr["admitted"]) == (1, 1, 1, 1, 1),
      (fr["rests"], fr["probations"], fr["solidified"], fr["judged"], fr["admitted"]))
check("[4c] first hearing after the solidify is 23 s later", S["hearings_after_10_30_solidify"]["first_after_seconds"] == 23.0,
      S["hearings_after_10_30_solidify"]["first_after_seconds"])
check("[4d] discharge window sees exactly the 4 member events", S["discharge_10_30"]["window_factual_recall_pe_events"] == 4)

# [5] real score_tension arithmetic
ids = [f"e{i}" for i in range(4)]
srcs = {i: ("prediction_error", t0) for i in ids}
b = TL.score_tension({"member_event_ids": ids, "label": "x"}, srcs, now=t0)
a = TL.score_tension({"member_event_ids": ids, "label": "x"}, srcs, now=t0 + 1, resolutions={i: 0.6 for i in ids})
check("[5a] 4 prediction_error events = pressure 4.0", b["contradiction_pressure"] == 4.0)
check("[5b] a 0.6 drain per event leaves 1.6 and the count stays 4",
      a["contradiction_pressure"] == 1.6 and a["contradiction_count"] == 4, (a["contradiction_pressure"], a["contradiction_count"]))
check("[5c] the summary reproduces [5]", S["discharge_10_30"]["pressure_before"] == 4.0
      and S["discharge_10_30"]["pressure_after_CURRENT_code_remap_is_critic_only_plus_0.6_drain"] == 1.6)

# [6] isolation
after = {p: p.stat().st_mtime_ns for p in (live / "data").rglob("*") if p.is_file()}
check("[6] the temp live dir was not written by the analysis (mtimes unchanged)", before == after)
# and the real live dir: the script's only write target is --out (checked by reading main())
src = (ROOT / "scripts" / "analysis_J3302_tension_lifecycle.py").read_text(encoding="utf-8")
check("[6b] the analysis script opens sqlite read-only", "mode=ro&immutable=1" in src)
check("[6c] every write in the analysis script targets --out",
      all("out /" in ln for ln in src.splitlines() if '"w"' in ln and "open(" in ln))
check("[7] rest-leak reconstruction ran (synthetic world has no pe leak)", S["rest_leaks_reconstructed"] == [])

print("\nALL OK" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
