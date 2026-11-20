"""J-3136 / D-0530: judge panel returns NO VERDICT on a v1/v2 split for keys where the granite tiebreak is a
constant. Stubs every model call; writes only under a temp dir; touches no live data.

Also a tool: `python scripts/_test_J3136_constant_tiebreak.py --live-replay [LOG]` READS a judge_panel_log.jsonl
(default C:\\Nascence\\data\\judge_panel_log.jsonl, read-only) and prints (a) the per-key granite tiebreak true-rate
since 2026-08-28 with the constant verdict, and (b) the 7-day replay: per key how many verdicts would have changed
from True (or False) to no-verdict. measure()/replay() below are what GRANITE_CONSTANT_TIEBREAK_KEYS was derived
from; re-run before editing that list."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import sys, json, time, asyncio, tempfile, datetime
from pathlib import Path
from collections import defaultdict
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env)
from core import judge_panel as jp  # noqa: E402
assert Path(jp.__file__).resolve().parent.parent == ROOT, "imported the wrong tree"

GRANITE_HUBS = (None, "11437")     # rows before 2026-09-28 carry no hub3; override rows (e.g. 11439 gemma4) are excluded
SINCE = datetime.datetime(2026, 8, 28).timestamp()


def _load(path):
    rows = []
    for l in Path(path).read_text(encoding="utf-8").splitlines():
        if l.strip():
            try:
                rows.append(json.loads(l))
            except Exception:
                pass
    return rows


def measure(rows, since=SINCE, min_n=50, lo=0.05, hi=0.95):
    """{key: (n, true, rate, is_constant)} over granite-decided tiebreak rows since `since`."""
    d = defaultdict(lambda: [0, 0])
    for r in rows:
        if r.get("ts", 0) < since or r.get("how") != "tiebreak" or r.get("hub3") not in GRANITE_HUBS:
            continue
        d[r["key"]][0] += 1
        d[r["key"]][1] += 1 if r.get("verdict") else 0
    return {k: (n, t, t / n, n >= min_n and (t / n <= lo or t / n >= hi)) for k, (n, t) in d.items()}


def replay(rows, keys, days=7):
    """Per key (in `keys`): splits seen in the last `days` of the log, how many a granite tiebreak decided,
    and how many of those decided verdicts would now be no-verdict, split True->none / False->none."""
    last = max(r["ts"] for r in rows)
    out = defaultdict(lambda: {"splits": 0, "granite_decided": 0, "true_to_none": 0, "false_to_none": 0,
                               "override_hub_splits": 0})
    for r in rows:
        if r["ts"] < last - days * 86400 or r["key"] not in keys:
            continue
        if r.get("v1") is None or r.get("v2") is None or r["v1"] == r["v2"]:
            continue
        o = out[r["key"]]
        o["splits"] += 1
        if r.get("hub3") not in GRANITE_HUBS and r.get("s3") is not None:
            o["override_hub_splits"] += 1       # a caller's own tiebreak_url: the rule does not apply
            continue
        if r.get("how") == "tiebreak":
            o["granite_decided"] += 1
            o["true_to_none" if r["verdict"] else "false_to_none"] += 1
    return dict(out)


if "--live-replay" in sys.argv:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    log = args[0] if args else r"C:\Nascence\data\judge_panel_log.jsonl"
    rows = _load(log)
    m = measure(rows)
    print("granite tiebreak true-rate since 2026-08-28 (n, true, rate, CONSTANT):")
    for k, (n, t, rate, c) in sorted(m.items(), key=lambda x: -x[1][0]):
        print(f"  {k:14s} n={n:5d} true={t:5d} rate={rate:.3f} {'CONSTANT' if c else ''}")
    const = {k for k, v in m.items() if v[3]}
    print("derived constant set:", sorted(const), "| code constant:", sorted(jp.GRANITE_CONSTANT_TIEBREAK_KEYS))
    print("7-day replay over the code constant:")
    for k, v in sorted(replay(rows, set(jp.GRANITE_CONSTANT_TIEBREAK_KEYS)).items()):
        print(" ", k, v)
    sys.exit(0)

# ---------------------------------------------------------------- the constant itself
assert jp.GRANITE_CONSTANT_TIEBREAK_KEYS == frozenset({"resolves", "held", "bears", "genuine", "taken_up"})
for k in ("advances", "coherent", "cuts", "supported", "aligns", "metaphor", "contradicted"):
    assert k not in jp.GRANITE_CONSTANT_TIEBREAK_KEYS, k
assert jp.SKIP_CONSTANT_TIEBREAK is True

# ---------------------------------------------------------------- measure()/replay() on a synthetic log
now = time.time()
syn = []
def _row(key, v1, v2, how, verdict, hub3, age_d=1.0):
    return {"ts": now - age_d * 86400, "key": key, "v1": v1, "v2": v2, "how": how, "verdict": verdict,
            "hub3": hub3, "s3": 1.0 if hub3 else None}
for i in range(60):   # constant-true key
    syn.append(_row("alpha", True, False, "tiebreak", True, "11437"))
for i in range(60):   # constant-false key, old rows with no hub3 field at all
    r = _row("beta", True, False, "tiebreak", False, None); r["s3"] = 1.0; syn.append(r)
for i in range(60):   # a real mixed key
    syn.append(_row("gamma", True, False, "tiebreak", i % 2 == 0, "11437"))
for i in range(10):   # constant but too few rulings
    syn.append(_row("delta", True, False, "tiebreak", True, "11437"))
for i in range(80):   # override hub rows (gemma4) are not granite and not counted
    syn.append(_row("epsilon", True, False, "tiebreak", True, "11439"))
m = measure(syn)
assert m["alpha"][3] and m["beta"][3] and not m["gamma"][3] and not m["delta"][3] and "epsilon" not in m, m
rp = replay(syn, {"alpha", "beta", "gamma", "epsilon"})
assert rp["alpha"]["true_to_none"] == 60 and rp["beta"]["false_to_none"] == 60, rp
assert rp["epsilon"]["override_hub_splits"] == 80 and rp["epsilon"]["granite_decided"] == 0, rp

# ---------------------------------------------------------------- rule_detail() with stubbed hubs, temp log
tmp = Path(tempfile.mkdtemp(prefix="j3136_"))
jp._DATA = tmp
jp._LOG = tmp / "judge_panel_log.jsonl"

calls = []
VOTES = {}      # url -> bool | None


async def _fake_ask(session, url, system, user, key, timeout=jp._TIMEOUT, num_predict=jp._NUM_PREDICT):
    calls.append(url)
    return VOTES[url], "stub why", None, 0.01


jp._ask = _fake_ask


def run(key, v1, v2, v3, **kw):
    calls.clear()
    VOTES.clear()
    VOTES[jp.JUDGE_1], VOTES[jp.JUDGE_2] = v1, v2
    VOTES[jp.TIEBREAK] = v3
    VOTES["http://stub-override:1"] = v3
    return asyncio.run(jp.rule_detail("sys", "usr", key, context="j3136", **kw))


# split on a constant key: no tiebreak call, no verdict, tb_skipped
d = run("bears", True, False, True)
assert d["verdict"] is None and d["how"] == "split_no_tiebreak" and d["tb_skipped"] is True, d
assert jp.TIEBREAK not in calls and len(calls) == 2, calls
assert d["why"] is None and d["why3"] is None and d["hub3"] is None and d["err3"] is None
for k in ("resolves", "held", "genuine", "taken_up"):
    d = run(k, False, True, True)
    assert d["verdict"] is None and d["how"] == "split_no_tiebreak" and d["tb_skipped"] is True, (k, d)
    assert jp.TIEBREAK not in calls, (k, calls)

# rule() wrapper: None
VOTES.clear(); VOTES[jp.JUDGE_1], VOTES[jp.JUDGE_2], VOTES[jp.TIEBREAK] = True, False, True
assert asyncio.run(jp.rule("s", "u", "resolves")) is None

# agreement on a constant key is untouched
d = run("bears", True, True, None)
assert d["verdict"] is True and d["how"] == "agreed" and d["tb_skipped"] is False and len(calls) == 2, d

# non-constant key: tiebreak still consulted and decides
d = run("advances", True, False, False)
assert d["verdict"] is False and d["how"] == "tiebreak" and d["tb_skipped"] is False, d
assert calls[-1] == jp.TIEBREAK and d["hub3"] == "11437", (calls, d)
d = run("coherent", True, False, True)
assert d["verdict"] is True and d["how"] == "tiebreak", d

# caller override (lane2's gemma4 pattern): constant key + own tiebreak_url is NOT skipped
d = run("held", True, False, True, tiebreak_url="http://stub-override:1")
assert d["verdict"] is True and d["how"] == "tiebreak" and d["tb_skipped"] is False, d
assert calls[-1] == "http://stub-override:1", calls
# an override that IS the shared TIEBREAK url is the same as no override
d = run("held", True, False, True, tiebreak_url=jp.TIEBREAK)
assert d["how"] == "split_no_tiebreak" and d["tb_skipped"] is True, d

# judges down stays 'unavailable', not 'split'
d = run("bears", None, True, True)
assert d["how"] == "unavailable" and d["tb_skipped"] is False, d

# revert switch restores the old path
jp.SKIP_CONSTANT_TIEBREAK = False
d = run("bears", True, False, True)
assert d["verdict"] is True and d["how"] == "tiebreak", d
jp.SKIP_CONSTANT_TIEBREAK = True

# ---------------------------------------------------------------- the logged rows and status()
rows = _load(jp._LOG)
skipped = [r for r in rows if r.get("tb_skipped")]
assert skipped and all(r["how"] == "split_no_tiebreak" and r["verdict"] is None and r["hub3"] is None
                       and r["s3"] is None for r in skipped), skipped
assert all("tb_skipped" not in r for r in rows if r["how"] != "split_no_tiebreak")
st = jp.status()
sk = st["tb_skipped_24h"]
assert sk["bears"] == {"no_verdict": 1, "rulings": 4}, sk     # skipped, agreed, unavailable, revert-switch tiebreak
assert sk["resolves"] == {"no_verdict": 2, "rulings": 2}, sk   # run() + rule() wrapper
assert sk["held"] == {"no_verdict": 2, "rulings": 3}, sk       # skipped, override-tiebreak (not skipped), own-url skipped
assert "advances" not in sk and "coherent" not in sk, sk
assert jp._LOG.parent == tmp, "wrote outside the temp dir"

print("J-3136 OK: constant-key splits -> no verdict without a tiebreak call; non-constant keys, overrides, "
      "agreements and the revert switch unchanged; status()['tb_skipped_24h'] reads the new row field")
