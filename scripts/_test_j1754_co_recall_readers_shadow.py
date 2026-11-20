"""
Regression: the remaining DIRECT readers of data/co_recall_ledger.jsonl skip *_shadow would-have-shown rows
(J-1754 -- F-2372 sibling, the follow-up to J-1738).

The gap: J-1738 made core/memory_edges.py (downstream_read_counts, co_recall_status, log_co_recall) treat a ledger row
whose `source` ends "_shadow" (D-0289 "monologue_shadow", D-0292 "divergent_shadow": the fragments a switched-off
path WOULD have shown, never shown to a thought) as evidence, not as a recall. Three scripts/hud paths read the ledger
file directly and still counted those rows:
  * scripts/spring_ledger_backfill.py   replays every row through spring_ledger.observe_co_recall (phantom naive ticks)
  * scripts/geometry_co_evocation_test.py  _load_ledger(): "real recall groups" included would-have-shown groups
  * hud/server.py                        the co_recall HUD card charted n_ids / restate_sim / developed per ledger row
The other direct readers need no change here (geometry_realness_test.build_joined_dataset keeps only
source == "monologue", which geometry_hybrid_retrieval_test reuses; scripts/dream_experiment_a.py reads a key
(`fragment_ids`) no ledger row carries, so its dormancy scan is inert -- see the J-1754 finding / follow-up job).

What this proves, ISOLATED: no model, no DB, no live data. spring_ledger's state + log are redirected into a temp dir,
every ledger is a temp file, the HUD's DATA_DIR is a temp dir, and the live stores (the co-recall ledger, the spring /
opponent-process stores, the satisfaction / prediction-error / shadow-integrity / buses canaries) are hashed before
and after.
  [1] helper     hud/server._is_shadow_source agrees with core.memory_edges._is_shadow_source on a battery of sources
  [2] backfill   spring_ledger_backfill.backfill(): shadow + divergent_shadow rows add no pair and no tick (a real pair
                 that a shadow row repeats is ticked once); real sources, legacy no-`source` rows, source=None and
                 lookalike sources still replay; shadow_rows_excluded is reported; the state equals a run on the same
                 ledger with the shadow rows physically removed
  [3] co-evocation  _load_ledger(): only real multi-id rows come back; identical to the pre-change filter on a
                 shadow-free ledger
  [4] HUD        load_monitor("co_recall"): no shadow row in the series, the 140-row window stays full, last_ts is the
                 last REAL row; other cards and _tail_rows' default behaviour are unchanged
  [5] the live stores are untouched and no data/ dir appeared in this checkout

  python scripts/_test_j1754_co_recall_readers_shadow.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import time
import traceback
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1754_co_recall_readers_"))
print("isolated store dir:", TMP)

# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo (and, when this is
# run from C:\Nascence itself, ROOT/data is the same place) -- watch both.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WATCH = [_LIVE_DATA / n for n in (
    "co_recall_ledger.jsonl", "spring_ledger_state.json", "spring_ledger_shadow.jsonl",
    "opponent_process_state.json", "opponent_process_shadow.jsonl",
    "satisfaction_log.jsonl", "satisfaction_state.json", "prediction_error_log.jsonl",
    "prediction_error_state.json", "buses_log.jsonl")]
_WATCH += [_LIVE_DATA / "logs" / "shadow_integrity.jsonl"]
_WATCH += [ROOT / "data" / n for n in ("co_recall_ledger.jsonl", "spring_ledger_state.json", "spring_ledger_shadow.jsonl")]
_ROOT_DATA_EXISTED = (ROOT / "data").exists()


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, st.st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest())


_before = {p: _snap(p) for p in _WATCH}

# core BEFORE anything else (F-2406/F-2423): prove it resolved inside THIS checkout, not the shared C:\Nascence tree.
from core import memory_edges as ME   # noqa: E402
from core import spring_ledger as SP  # noqa: E402

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


check(Path(ME.__file__).resolve().is_relative_to(ROOT) and Path(SP.__file__).resolve().is_relative_to(ROOT),
      f"core.memory_edges / core.spring_ledger were imported from THIS checkout ({Path(ME.__file__).resolve()})")

# nothing below may reach a default (live) path by accident
ME._DATA = TMP
ME._CO_LEDGER = TMP / "unused_until_redirected.jsonl"
SP._DATA = TMP
SP._STATE, SP._LOG = TMP / "spring_ledger_state.json", TMP / "spring_ledger_shadow.jsonl"
SP.SAVE_MIN_INTERVAL_S = 0   # J-2418: these tests read the state file right after a call
SP.LIVE_EDGE_WRITE = False   # belt and braces: no code path in this test may open the live memory_edges DB


def load_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NOW = time.time()


def fid(n: int) -> str:
    return f"{n:012d}-frag"


def row(ids, source="__omit__", ts=None, developed=None, restate_sim=None, n_ids=None):
    r = {"ts": round(NOW if ts is None else ts, 1), "n_ids": len(ids) if n_ids is None else n_ids, "ids": list(ids),
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


# ---------------------------------------------------------------------------------------------------------------
# the ledger every section shares: real rows of every kind + shadow rows (some on pairs no real row ever touched, one
# repeating a real pair)
# ---------------------------------------------------------------------------------------------------------------
REAL_ROWS = [
    row([fid(1), fid(2)], "monologue", ts=NOW - 900, developed=1, restate_sim=0.6),
    row([fid(2), fid(3)], "wandering", ts=NOW - 800, developed=0, restate_sim=0.9),
    row([fid(1), fid(3)], ts=NOW - 700),                                  # legacy: no `source` key at all
    row([fid(12), fid(13)], None, ts=NOW - 600),                          # source: null
    row([fid(10), fid(11)], "shadow_monologue", ts=NOW - 500),            # lookalike (prefix, not suffix) -> real
    row([fid(20)], "monologue", ts=NOW - 400, developed=0, restate_sim=0.3),   # one id: never a pair
]
SHADOW_ROWS = [
    row([fid(7), fid(8), fid(9)], "monologue_shadow", ts=NOW - 850),      # a pair set no real row ever touched
    row([fid(8), fid(9)], "divergent_shadow", ts=NOW - 750),
    row([fid(1), fid(2)], "monologue_shadow", ts=NOW - 650),              # repeats a REAL pair
]


def interleave(real, shadow):
    out = real + shadow
    out.sort(key=lambda r: r["ts"])
    return out


def t_helper():
    HUD = load_file(ROOT / "hud" / "server.py", "j1754_hud_server_helper")
    battery = [None, "", "monologue", "monologue_shadow", "divergent_shadow", "_shadow", "shadow", "shadow_monologue",
               "monologue_shadow ", "MONOLOGUE_SHADOW", 5, ["x_shadow"], b"x_shadow", 0, False]
    bad = [s for s in battery if bool(HUD._is_shadow_source(s)) != bool(ME._is_shadow_source(s))]
    check(not bad, f"hud._is_shadow_source agrees with core.memory_edges._is_shadow_source on {len(battery)} inputs (disagree on: {bad})")


def t_backfill():
    SB = load_file(ROOT / "scripts" / "spring_ledger_backfill.py", "j1754_spring_ledger_backfill")
    led_all = TMP / "bf_ledger_all.jsonl"
    led_real = TMP / "bf_ledger_real_only.jsonl"
    extra = ["", "this is not json"]       # a blank line and a garbage line, as the live ledger may carry
    write_ledger(led_all, interleave(REAL_ROWS, SHADOW_ROWS), extra)
    write_ledger(led_real, interleave(REAL_ROWS, []), extra)

    SB._LEDGER = led_all
    res_all = SB.backfill()
    state_all = SP._load()
    log_all = [json.loads(l) for l in open(SP._LOG, encoding="utf-8") if l.strip()] if SP._LOG.exists() else []

    SB._LEDGER = led_real
    res_real = SB.backfill()
    state_real = SP._load()

    k = lambda a, b: f"{fid(a)[:12]}|{fid(b)[:12]}"
    phantom = [key for key in state_all if any(f"{n:012d}" in key for n in (7, 8, 9))]
    check(not phantom, f"no pair built from a shadow-only id reaches the spring ledger (found {phantom})")
    check(k(1, 2) in state_all and state_all[k(1, 2)]["n_naive"] == 1,
          f"a real pair a shadow row repeats is ticked once, not twice (n_naive={state_all.get(k(1, 2), {}).get('n_naive')})")
    real_keys = {k(1, 2), k(2, 3), k(1, 3), k(12, 13), k(10, 11)}
    check(set(state_all) == real_keys,
          f"real sources, a legacy no-source row, source=None and a lookalike source all still replay (pairs: {sorted(state_all)})")
    check(res_all.get("shadow_rows_excluded") == 3,
          f"shadow_rows_excluded is reported: 3 (got {res_all.get('shadow_rows_excluded')})")
    check(res_all["activations"] == 5 and res_all["skipped_or_single_id"] == 2,
          f"activations / skipped keep their meaning: 5 and 2 (the single-id row + the garbage line) -- got {res_all['activations']} / {res_all['skipped_or_single_id']}")
    check(res_all["ledger_rows_read"] == res_all["activations"] + res_all["skipped_or_single_id"] + res_all.get("shadow_rows_excluded", 0),
          "every non-blank ledger line is accounted for: read = activations + skipped + shadow_rows_excluded")
    check(not [r for r in log_all if str(r.get("source", "")).endswith("_shadow")],
          "no spring_ledger shadow-log tick carries a backfill:*_shadow source")
    check(state_all == state_real and res_real.get("shadow_rows_excluded") == 0,
          "the state is identical to a run on the same ledger with the shadow rows physically removed (which excludes none)")


def t_co_evocation():
    CE = load_file(ROOT / "scripts" / "geometry_co_evocation_test.py", "j1754_geometry_co_evocation_test")
    led = TMP / "ce_ledger.jsonl"
    real = [
        row([fid(1), fid(2), fid(3)], "monologue", ts=NOW - 900),
        row([fid(4), fid(5)], "wandering", ts=NOW - 800),
        row([fid(6), fid(7)], ts=NOW - 700),                               # legacy no `source`
        row([fid(8), fid(9)], None, ts=NOW - 600),                         # source: null
        row([fid(10), fid(11)], "shadow_monologue", ts=NOW - 500),         # lookalike -> real
        row([fid(30)], "monologue", ts=NOW - 450),                         # n_ids 1: never a group
        row([], "monologue", ts=NOW - 440),                                # n_ids 0
    ]
    shadow = [
        row([fid(40), fid(41), fid(42), fid(43)], "monologue_shadow", ts=NOW - 850),
        row([fid(44), fid(45)], "divergent_shadow", ts=NOW - 750),
    ]
    write_ledger(led, interleave(real, shadow), ["not json", ""])
    CE._LEDGER = led
    got = CE._load_ledger()
    want = [r["ids"] for r in interleave(real, []) if r["n_ids"] >= 2 and r["ids"]]
    check([r["ids"] for r in got] == want,
          f"only real multi-id rows come back, in file order ({len(got)} rows; shadow groups dropped)")
    check(not [r for r in got if str(r.get("source", "")).endswith("_shadow")], "no returned row has a *_shadow source")

    write_ledger(led, interleave(real, []), [])
    pre_change = [r for r in (json.loads(l) for l in open(led, encoding="utf-8") if l.strip())
                  if r.get("n_ids", 0) >= 2 and r.get("ids")]
    check(CE._load_ledger() == pre_change, "on a ledger with no shadow rows the result equals the pre-change filter exactly")


def t_hud():
    HUD = load_file(ROOT / "hud" / "server.py", "j1754_hud_server")
    d = TMP / "hud_data"
    d.mkdir(exist_ok=True)
    HUD.DATA_DIR = d
    base = NOW - 400 * 30
    rows, live_ts, shadow_ts = [], [], []
    for i in range(399):   # 399 rows: the LAST raw row (i=398) is a shadow row, so last_ts below can tell the filter worked
        ts = round(base + i * 30, 1)
        if i % 3 == 2:     # a would-have-shown row: n_ids 7 is impossible for a live row below, restate/developed None
            rows.append({"ts": ts, "n_ids": 7, "ids": [fid(900 + j) for j in range(7)], "restate_sim": None,
                         "developed": None, "step": 0, "source": "monologue_shadow"})
            shadow_ts.append(ts)
        else:
            rows.append({"ts": ts, "n_ids": i % 5, "ids": [], "restate_sim": 0.5, "developed": i % 2, "step": 1,
                         "source": "monologue"})
            live_ts.append(ts)
    write_ledger(d / "co_recall_ledger.jsonl", rows)

    s = HUD.load_monitor("co_recall")
    check(s.get("kind") == "vars", f"the co_recall card still renders as a vars chart (kind={s.get('kind')})")
    check(len(s.get("ts", [])) == 140, f"the 140-row window stays full of REAL rows (got {len(s.get('ts', []))})")
    check(not (set(s.get("ts", [])) & set(shadow_ts)), "no would-have-shown row's timestamp is in the series")
    check(7 not in s.get("n_ids", []), "no phantom n_ids (the shadow rows' signature value) is charted")
    check(None not in s.get("developed", [None]) and None not in s.get("restate_sim", [None]),
          "no None gaps in developed / restate_sim (the shadow rows' signature) -- every charted row has a verdict")
    check(s.get("last_ts") == live_ts[-1] and s.get("span_s") == round(live_ts[-1] - s["ts"][0], 1),
          f"last_ts / span_s describe the REAL rows (last_ts {s.get('last_ts')} == last live {live_ts[-1]})")

    # other cards: the generic path must be unchanged -- a *_shadow `source` there is just a field
    write_ledger(d / "opponent_process_shadow.jsonl",
                 [{"ts": round(NOW - 30 + i, 1), "b_after": 0.1 * i, "activation_n": i, "source": "x_shadow"} for i in range(30)])
    o = HUD.load_monitor("opponent_process")
    check(len(o.get("ts", [])) == 30, f"another card with *_shadow-sourced rows keeps every row (got {len(o.get('ts', []))})")

    tail = HUD._tail_rows(d / "co_recall_ledger.jsonl", limit=5)
    check(len(tail) == 5 and sum(1 for r in tail if r.get("source") == "monologue_shadow") == 2,
          "_tail_rows without a filter is unchanged: the last 5 raw rows, shadow ones included")
    check(HUD.load_monitor("no_such_card") == {"kind": "empty"}, "an unknown card still returns the empty series")
    HUD.DATA_DIR = TMP / "hud_data_missing"
    check(HUD.load_monitor("co_recall").get("kind") == "empty", "a missing ledger is still the fail-open empty series")


def t_live_untouched():
    after = {p: _snap(p) for p in _WATCH}
    check(after == _before, f"every live store watched ({len(_WATCH)} files: ledger, spring/opponent stores, canaries) is byte/mtime-identical")
    check(_ROOT_DATA_EXISTED or not (ROOT / "data").exists(), "no data/ dir was created in this checkout")


section("[1] helper", t_helper)
section("[2] spring_ledger_backfill", t_backfill)
section("[3] geometry_co_evocation_test", t_co_evocation)
section("[4] hud/server co_recall card", t_hud)
section("[5] live stores", t_live_untouched)

print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(0 if FAILS == 0 else 1)
