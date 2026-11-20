"""
Regression: *_shadow co-recall rows are would-have-shown EVIDENCE, not downstream reads (J-1738 / F-2372).

The gap: D-0289's kill-switch (core/associative_recall.IDLE_AMBIENT_RECALL = False, flipped by D-0310) makes
recall_block() log the fragments it WOULD have shown as source="monologue_shadow" rows in
data/co_recall_ledger.jsonl (D-0292's IDLE_DIVERGENT_SEED does the same with "divergent_shadow"). Those ids never
reached a thought, yet memory_edges.downstream_read_counts() -- the D-0084 / J-0382 signal under
core/memory/store.py:read_count_importance_shadow -- counted every row's ids with no `source` test; co_recall_status()
(the M1 read-out du_pulse prints) counted their pairs into pairs_ungated; and log_co_recall() itself fanned the same
would-have-shown ids out to opponent_process.observe_activation (developed=None -> a FULL growth step) and
spring_ledger.observe_co_recall (naive weight). The fix, all in core/memory_edges.py:
  * downstream_read_counts() and co_recall_status() skip rows whose `source` ends "_shadow"
  * log_co_recall() still APPENDS the row (J-1512's defeater read needs it, by source) but skips the two sibling ticks

What this proves, ISOLATED: no model, no DB, no live data. memory_edges' ledger path and opponent_process's /
spring_ledger's state + log paths are redirected into a temp dir before anything is written, and the live stores
under C:\\Nascence\\data are stat-ed before and after (the small ones hashed).
  [1] helper      _is_shadow_source: suffix "_shadow" only; None / "" / lookalikes / non-str are not shadow
  [2] reads       downstream_read_counts: shadow + divergent_shadow rows add nothing; real sources, legacy rows with no
                  `source`, source=None and lookalike sources still count; the ts window and since_ts behave as before;
                  garbage / blank lines tolerated; a missing ledger -> {} (fail-open); a ledger with no shadow rows
                  gives exactly what the pre-J-1738 logic gives
  [3] read-out    co_recall_status: shadow rows leave rows / with_2plus_ids / pairs_ungated alone and are reported as
                  shadow_rows_excluded; total_rows stays the ledger's own count
  [4] writes      log_co_recall: a *_shadow source still appends its row (ids, n_ids, source intact, readable by source
                  the way J-1512 reads it) but ticks neither sibling and writes no skip rows; a real source still ticks
                  both (and a developed row still moves the gated weight); the ledger the writer produced reads back
                  through downstream_read_counts without the shadow ids
  [5] the live stores are untouched, and no data/ dir appeared in this checkout

  python scripts/_test_j1738_shadow_rows_not_reads.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
import traceback
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1738_shadow_rows_"))
print("isolated store dir:", TMP)

# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo (and, when this is
# run from C:\Nascence itself, ROOT/data is the same place) -- watch both.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WATCH = [_LIVE_DATA / n for n in (
    "co_recall_ledger.jsonl", "opponent_process_state.json", "opponent_process_shadow.jsonl",
    "spring_ledger_state.json", "spring_ledger_shadow.jsonl", "read_count_importance_shadow.jsonl")]
_WATCH += [_LIVE_DATA / "memory" / "nascence.db", _LIVE_DATA / "memory" / "nascence.db-wal"]
_WATCH += [ROOT / "data" / "co_recall_ledger.jsonl"]
_ROOT_DATA_EXISTED = (ROOT / "data").exists()


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    md5 = hashlib.md5(p.read_bytes()).hexdigest() if st.st_size < 5_000_000 else ""
    return (st.st_size, st.st_mtime_ns, md5)


_before = {p: _snap(p) for p in _WATCH}

from core import memory_edges as ME      # noqa: E402
from core import opponent_process as OP  # noqa: E402
from core import spring_ledger as SP     # noqa: E402

# nothing below may reach a default (live) path by accident
ME._CO_LEDGER = TMP / "unused_until_redirected.jsonl"
ME._DATA = TMP
OP._DATA = TMP
OP._STATE, OP._LOG = TMP / "opponent_process_state.json", TMP / "opponent_process_shadow.jsonl"
SP._DATA = TMP
SP._STATE, SP._LOG = TMP / "spring_ledger_state.json", TMP / "spring_ledger_shadow.jsonl"
SP.SAVE_MIN_INTERVAL_S = 0   # J-2418: these tests read the state file right after a call
OP.SAVE_MIN_INTERVAL_S = 0
SP.LIVE_EDGE_WRITE = False   # belt and braces: no code path in this test may open the live memory_edges DB

FAILS = 0


def check(cond, label):
    global FAILS
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        FAILS += 1


def section(title, fn):
    global FAILS
    print(title)
    try:
        fn()
    except Exception:
        FAILS += 1
        print("  FAIL  section raised:\n" + traceback.format_exc())


NOW = time.time()
DAY = 86400.0


def row(ids, source="__omit__", ts=None, developed=None, restate_sim=None):
    r = {"ts": round(NOW if ts is None else ts, 1), "n_ids": len(ids), "ids": list(ids),
         "restate_sim": restate_sim, "developed": developed, "step": 0}
    if source != "__omit__":
        r["source"] = source
    return r


def write_ledger(path: Path, rows, extra_lines=()):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        for line in extra_lines:
            f.write(line + "\n")


def read_ledger(path: Path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def ref_counts_pre_j1738(path: Path, since_ts=None, days=14.0):
    """Verbatim copy of downstream_read_counts() as it was before J-1738 (no source test) -- the reference."""
    cutoff = float(since_ts) if since_ts is not None else (time.time() - days * 86400)
    counts = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if (r.get("ts") or 0) < cutoff:
                continue
            for fid in r.get("ids") or []:
                if fid:
                    counts[fid] = counts.get(fid, 0) + 1
    return counts


REAL = [
    row(["A", "B"], "monologue", developed=1, restate_sim=0.5),   # a real, developed co-recall
    row(["A"], "wandering"),                                       # a second real read of A
    row(["F", "G"]),                                               # legacy row: no `source` key at all (pre audit #10)
    row(["H"], None),                                              # source explicitly null
    row(["I"], "shadowing"),                                       # lookalike: does not END with _shadow
    row(["L"], "my_shadow_walk"),                                  # lookalike: contains it mid-string
]
SHADOW = [
    row(["C", "D"], "monologue_shadow"),                           # D-0289 would-have-shown
    row(["E"], "divergent_shadow"),                                # D-0292 would-have-shown, single id
]
OLD = [
    row(["OLD"], "monologue", ts=NOW - 20 * DAY),                  # real but outside the 14-day window
    row(["OLDSH"], "monologue_shadow", ts=NOW - 20 * DAY),         # shadow AND outside the window
]


def t_helper():
    f = getattr(ME, "_is_shadow_source", None)
    check(callable(f), "memory_edges._is_shadow_source exists")
    if not callable(f):
        return
    for s in ("monologue_shadow", "divergent_shadow", "x_shadow", "_shadow"):
        check(f(s) is True, f"{s!r} is a shadow source")
    for s in (None, "", "monologue", "wandering", "shadow", "shadowing", "my_shadow_walk", "monologue_shadow_v2", 7):
        check(f(s) is False, f"{s!r} is NOT a shadow source")


def t_reads():
    led = TMP / "reads_ledger.jsonl"
    write_ledger(led, REAL + SHADOW + OLD, extra_lines=("{not json", "", "   "))
    ME._CO_LEDGER = led
    got = ME.downstream_read_counts(days=14.0)
    want = {"A": 2, "B": 1, "F": 1, "G": 1, "H": 1, "I": 1, "L": 1}
    check(got == want, f"downstream_read_counts(days=14) == real reads only {want}  (got {got})")
    check(not ({"C", "D", "E", "OLDSH"} & set(got)), "no would-have-shown id (C, D, E, OLDSH) is counted as a read")
    check("OLD" not in got, "the 14-day window still drops a real row 20 days old")
    got30 = ME.downstream_read_counts(since_ts=NOW - 30 * DAY)
    check(got30.get("OLD") == 1 and "OLDSH" not in got30,
          f"since_ts overrides days as before: the 20-day-old REAL row counts, the 20-day-old shadow row does not (got {got30})")
    # no shadow rows in the ledger -> identical to the pre-J-1738 logic
    clean = TMP / "reads_clean.jsonl"
    write_ledger(clean, REAL + OLD[:1], extra_lines=("{not json",))
    ME._CO_LEDGER = clean
    check(ME.downstream_read_counts(days=14.0) == ref_counts_pre_j1738(clean, days=14.0),
          "a ledger with no shadow rows reads exactly as the pre-J-1738 function read it")
    ME._CO_LEDGER = TMP / "does_not_exist.jsonl"
    check(ME.downstream_read_counts() == {}, "a missing ledger -> {} (fail-open kept)")


def t_status():
    led = TMP / "status_ledger.jsonl"
    write_ledger(led, REAL + SHADOW + OLD)
    ME._CO_LEDGER = led
    st = ME.co_recall_status(days=7.0)
    check(st.get("rows") == len(REAL), f"rows counts the {len(REAL)} real in-window rows, not the shadow ones (got {st.get('rows')})")
    check(st.get("with_2plus_ids") == 2, f"with_2plus_ids == 2: (A,B) and (F,G) (got {st.get('with_2plus_ids')})")
    check(st.get("pairs_ungated") == 2, f"pairs_ungated == 2, the shadow pair (C,D) is not counted (got {st.get('pairs_ungated')})")
    check(st.get("pairs_gated") == 1, f"pairs_gated == 1 (got {st.get('pairs_gated')})")
    check(st.get("developed_share") == 1.0, f"developed_share unchanged by shadow rows (got {st.get('developed_share')})")
    check(st.get("shadow_rows_excluded") == len(SHADOW),
          f"the exclusion is reported, not silent: shadow_rows_excluded == {len(SHADOW)} (got {st.get('shadow_rows_excluded')})")
    check(st.get("total_rows") == len(REAL) + len(SHADOW) + len(OLD),
          f"total_rows stays the ledger's own row count (got {st.get('total_rows')})")
    only_shadow = TMP / "status_only_shadow.jsonl"
    write_ledger(only_shadow, SHADOW)
    ME._CO_LEDGER = only_shadow
    st2 = ME.co_recall_status(days=7.0)
    check(st2.get("rows") == 0 and st2.get("total_rows") == len(SHADOW),
          f"a window holding only shadow rows reads as no rows (du_pulse then prints nothing) (got {st2})")


def t_writes():
    led = TMP / "writes_ledger.jsonl"
    ME._CO_LEDGER = led
    opp_state, opp_log, sp_state, sp_log = OP._STATE, OP._LOG, SP._STATE, SP._LOG
    for p in (led, opp_state, opp_log, sp_state, sp_log):
        check(not p.exists(), f"starts clean: {p.name}")
    ME.log_co_recall(["X", "Y", "Z"], None, 0, source="monologue_shadow")
    rows = read_ledger(led)
    check(len(rows) == 1 and rows[0].get("source") == "monologue_shadow" and rows[0].get("ids") == ["X", "Y", "Z"]
          and rows[0].get("n_ids") == 3 and rows[0].get("developed") is None,
          f"the monologue_shadow row IS appended with ids / n_ids / source intact (got {rows})")
    check(not any(p.exists() for p in (opp_state, opp_log, sp_state, sp_log)),
          "...and ticked NEITHER opponent_process NOR spring_ledger (no state file, no log row)")
    ME.log_co_recall(["Q"], None, 0, source="divergent_shadow")
    check(len(read_ledger(led)) == 2 and not any(p.exists() for p in (opp_state, opp_log, sp_state, sp_log)),
          "a single-id divergent_shadow row is appended and writes no 'fewer-than-2-ids' skip row to either sibling log")
    ME.log_co_recall(["X", "Y", "Z"], None, 0, source="monologue")
    check(len(read_ledger(led)) == 3, "a real source appends its row as before")
    ost, sst = json.loads(opp_state.read_text(encoding="utf-8")), json.loads(sp_state.read_text(encoding="utf-8"))
    check(sorted(ost) == ["X|Y", "X|Z", "Y|Z"] and sorted(sst) == ["X|Y", "X|Z", "Y|Z"],
          f"...and still ticks BOTH siblings, one per pair (opponent {sorted(ost)}, spring {sorted(sst)})")
    sp_rows = [json.loads(l) for l in open(sp_log, encoding="utf-8") if l.strip()]
    check(len(sp_rows) == 3 and {r.get("source") for r in sp_rows} == {"monologue"},
          f"spring_ledger's log holds only the real source's 3 pair ticks (got {[r.get('source') for r in sp_rows]})")
    ME.log_co_recall(["X", "Y"], 0.5)   # default source, a developed verdict
    sst2 = json.loads(sp_state.read_text(encoding="utf-8"))
    check(sst2["X|Y"]["w_gated"] > 0 and sst2["X|Z"]["w_gated"] == 0,
          f"a real developed row still moves the gated weight (X|Y {sst2['X|Y']['w_gated']}, X|Z {sst2['X|Z']['w_gated']})")
    # J-1512 reads the ledger by source: the would-have-shown ids must be there, untouched
    shadow_rows = [r for r in read_ledger(led) if r.get("source") == "monologue_shadow"]
    check(len(shadow_rows) == 1 and shadow_rows[0]["ids"] == ["X", "Y", "Z"],
          "read directly by source (as J-1512's defeater read does) the would-have-shown ids are all still there")
    got = ME.downstream_read_counts(days=1.0)
    check(got == {"X": 2, "Y": 2, "Z": 1},
          f"end to end: what the writer produced reads back as real reads only -- X 2, Y 2, Z 1, no phantom Q (got {got})")


def t_live_untouched():
    after = {p: _snap(p) for p in _WATCH}
    check(after == _before, "every live store watched (ledger, sibling states/logs, shadow log, DB, WAL) is byte/mtime-identical")
    check(_ROOT_DATA_EXISTED or not (ROOT / "data").exists(), "no data/ dir was created in this checkout")


section("[1] helper", t_helper)
section("[2] downstream_read_counts", t_reads)
section("[3] co_recall_status", t_status)
section("[4] log_co_recall", t_writes)
section("[5] live stores", t_live_untouched)

print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(0 if FAILS == 0 else 1)
