"""
Test suite -- J-3125 / F-3852 / P-0111: Lane 2 `_coherence_check` shows the judge the NEWEST records (built newest-first
inside a 1,200 character budget, whole entries only, then shown oldest first), not the first 600 characters of an
oldest-first join.  New observation slice 300 -> 400.  The sysmsg is byte-identical.

Hermetic: the panel call (`core.judge_panel.rule_detail`) is replaced by a recording stub, lane2's data paths are
redirected to a temp dir, non-loopback sockets are refused, and this checkout's live data/ files are stat-checked before
and after.  No hub is called.  (Live-panel replays are scripts/lane2_coherence_replay_J3125.py, run separately.)

Run: python scripts/_test_J3125_lane2_coherence_newest.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402
assert str(Path(_core_pkg.__file__).resolve()).lower().startswith(str(ROOT).lower()), _core_pkg.__file__
from core import lane2  # noqa: E402
from core import judge_panel as _jp  # noqa: E402

_ORIG_DATA = lane2._DATA
_WATCH = ("lane2_shadow.jsonl", "llm_calls.jsonl", "nascence.log", "lane2_store.json", "judge_panel_log.jsonl")


def _snap() -> dict:
    out = {}
    for n in _WATCH:
        p = _ORIG_DATA / n
        out[n] = (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None
    return out


_LIVE_BEFORE = _snap()
TMP = Path(tempfile.mkdtemp(prefix="j3125_lane2_"))
lane2._DATA = TMP
lane2._LOG = TMP / "lane2_shadow.jsonl"
lane2._STATE = TMP / "lane2_store.json"

CHECKS: list[tuple[str, bool]] = []


def check(name: str, cond, detail: str = "") -> None:
    CHECKS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name, ("" if cond or not detail else f"  [{detail}]"))


_NONLOCAL: list = []
_real_connect = socket.socket.connect


def _guard(self, address, *a, **k):
    host = address[0] if isinstance(address, tuple) else address
    if host not in ("127.0.0.1", "::1", "localhost"):
        _NONLOCAL.append(address)
        raise OSError("test guard: real network connect refused")
    return _real_connect(self, address, *a, **k)


socket.socket.connect = _guard

# ── the recording panel stub ────────────────────────────────────────────────────────────────────────
SEEN: list[dict] = []
_MARK = {"newest": None, "oldest": None}


async def _stub_rule_detail(system, user, key, context="", num_predict=0, tiebreak_url=None, **kw):
    """A VISIBILITY judge: says incoherent (False) iff a planted marker is visible in the RECENT RECORD part of the
    prompt it was actually given -- i.e. it can only catch what it is shown.  Records every call."""
    SEEN.append({"system": system, "user": user, "key": key, "context": context, "tiebreak_url": tiebreak_url})
    record = user.split("\n\nNEW OBSERVATION:")[0]
    for m in (_MARK["newest"], _MARK["oldest"]):
        if m and m in record:
            return {"verdict": False, "how": "agreed"}
    return {"verdict": True, "how": "agreed"}


_jp.rule_detail = _stub_rule_detail


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def entry(notice: str, place="the_study", standpoint="at_the_door", ts=0.0) -> dict:
    return {"ts": ts, "notice": notice, "place": place, "standpoint": standpoint, "sources": ["x"]}


def words(tag: str, n: int) -> str:
    """A notice of ~n characters made of whole words, starting with `tag`."""
    s = tag
    i = 0
    while len(s) < n:
        s += f" word{i:02d}"
        i += 1
    return s[:n].rsplit(" ", 1)[0] if len(s) > n else s


def check_one(store, notice="A small grey cat sits by the hearth.", flag=True):
    SEEN.clear()
    old = lane2._COHERENCE_NEWEST_FIRST
    lane2._COHERENCE_NEWEST_FIRST = flag
    try:
        res = run(lane2._coherence_check({"notice": notice}, store,
                                         {"world": {"place": "the_study"}, "standpoint": "at_the_door"}))
    finally:
        lane2._COHERENCE_NEWEST_FIRST = old
    return res, (SEEN[-1] if SEEN else None)


# ── A. the sysmsg is byte-identical to the pre-change code ──────────────────────────────────────────
def _sysmsg_block(src: str) -> str:
    i = src.index('sysmsg = ("You judge whether a NEW observation is PLAUSIBLE')
    j = src.index('usr = f"RECENT RECORD', i)
    return src[i:j]


try:
    base = subprocess.run(["git", "-C", str(ROOT), "show", "20481a18:core/lane2.py"], capture_output=True, check=True).stdout
    base_src = base.decode("utf-8-sig").replace("\r\n", "\n")
    cur_src = (ROOT / "core" / "lane2.py").read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
    # J-3127 (2026-11-06) added `"why": "<one short clause>"` to the FINAL instruction only; every other word must still
    # be byte-identical, so the two source lines of that instruction are normalised back before comparing.
    _norm = re.sub(r'true\|false, \\"why\\": "\s+"\\"<one short clause>\\"\}"\)', 'true|false}")', _sysmsg_block(cur_src))
    check("A1 sysmsg source block is byte-identical to the pre-change commit (20481a18) apart from the J-3127 why clause",
          _sysmsg_block(base_src) == _norm)
except Exception as exc:       # pragma: no cover
    check("A1 sysmsg identical to pre-change commit", False, repr(exc))

# ── B. short histories: the prompt is unchanged from the old build ──────────────────────────────────
short = {"factual": [entry(f"Quiet note {i}.", ts=i) for i in range(6)]}
r_new, s_new = check_one(short)
r_old, s_old = check_one(short, flag=False)
check("B1 short history: usr identical new vs old build", s_new["user"] == s_old["user"], s_new["user"][:80])
check("B2 short history: sysmsg identical new vs old flag", s_new["system"] == s_old["system"])
check("B3 coherence key and tiebreak seat unchanged",
      s_new["key"] == "coherent" and s_new["context"] == "lane2:coherence"
      and s_new["tiebreak_url"] == lane2._TIEBREAK_LANE2)
check("B4 reply carries hist_v 2 / hist_dropped 0 on the new build", r_new.get("hist_v") == 2 and r_new.get("hist_dropped") == 0, str(r_new))
check("B5 flag off: no hist_v marker, verdict shape as before", "hist_v" not in r_old and r_old["verdict"] == "coherent", str(r_old))

# ── C. production-length history: newest record visible, order still oldest-first ───────────────────
long6 = [entry(words(f"E{i}", 196), ts=i) for i in range(6)]          # ~196 + 25 label each => ~1,330 joined
store_long = {"factual": long6}
r, s = check_one(store_long)
rec = s["user"].split("\n\nNEW OBSERVATION:")[0].replace("RECENT RECORD (oldest first): ", "")
n_old_len = len(" / ".join(f"[the_study/at_the_door] {e['notice']}" for e in long6))
check("C0 fixture is production length (> 1,200 joined)", n_old_len > 1200, str(n_old_len))
check("C1 newest record is in the prompt, whole", f"[the_study/at_the_door] {long6[5]['notice']}" in rec)
check("C2 history within the 1,200 budget", len(rec) <= 1200, str(len(rec)))
check("C3 only whole entries kept: every kept entry appears in full",
      all(p in rec for p in [f"[the_study/at_the_door] {e['notice']}" for e in long6[1:]]) and "E0" not in rec)
check("C4 the oldest whole entry was dropped, hist_dropped counts it", r.get("hist_dropped") == 1, str(r))
pos = [rec.index(f"E{i}") for i in range(1, 6)]
check("C5 shown oldest first", pos == sorted(pos))
check("C6 prompt header still says oldest first", s["user"].startswith("RECENT RECORD (oldest first): "))
r2, s2 = check_one(store_long, flag=False)
rec_old = s2["user"].split("\n\nNEW OBSERVATION:")[0]
check("C7 OLD build never showed the newest record on this fixture (the F-3852 defect, reproduced)",
      long6[5]["notice"] not in rec_old and len(rec_old) <= len("RECENT RECORD (oldest first): ") + 600)

# ── D. visibility canaries (the stub can only catch what it is shown) ───────────────────────────────
def canary_store(position: str, entry_len: int) -> dict:
    es = [entry(words(f"calm{i}", entry_len), ts=i) for i in range(6)]
    marker = "zzFIREISOUTzz"
    idx = 5 if position == "newest" else 0
    es[idx] = entry(marker + " " + words("calm", entry_len - 14), ts=idx)
    _MARK["newest"] = marker if position == "newest" else None
    _MARK["oldest"] = marker if position == "oldest" else None
    return {"factual": es}


def verdict(store, flag):
    res, _ = check_one(store, flag=flag)
    return res["verdict"]


for ln, tag in ((196, "max-length"), (60, "short")):
    st = canary_store("newest", ln)
    old_v, new_v = verdict(st, False), verdict(st, True)
    if ln == 196:
        check(f"D1 newest-only contradiction, {tag}: OLD misses, NEW catches", old_v == "coherent" and new_v == "incoherent", f"{old_v}/{new_v}")
    else:
        check(f"D2 newest-only contradiction, {tag} (fits the old 600): both catch", old_v == "incoherent" and new_v == "incoherent", f"{old_v}/{new_v}")
for ln, tag in ((196, "max-length"), (60, "short")):
    st = canary_store("oldest", ln)
    old_v, new_v = verdict(st, False), verdict(st, True)
    if ln == 196:
        # The honest cost of the change, pinned so nobody is surprised: at the very longest histories the budget
        # drops the OLDEST whole entry, which the old build still showed.
        check(f"D3 oldest-only contradiction, {tag}: OLD catches, NEW drops it (known, documented tradeoff)",
              old_v == "incoherent" and new_v == "coherent", f"{old_v}/{new_v}")
    else:
        check(f"D4 oldest-only contradiction, {tag}: both catch", old_v == "incoherent" and new_v == "incoherent", f"{old_v}/{new_v}")
_MARK["newest"] = _MARK["oldest"] = None

# ── E. unit checks on the helpers ───────────────────────────────────────────────────────────────────
h, dropped = lane2._coherence_history(long6)
check("E1 _coherence_history returns (text, dropped)", isinstance(h, str) and dropped == 1)
# the newest entry alone too long: cut at a word boundary, never mid-word
big = [entry(" ".join(f"alpha{i:03d}" for i in range(400)), ts=1)]
hb, db = lane2._coherence_history(big)
full = "[the_study/at_the_door] " + big[0]["notice"]
check("E2 oversize newest entry kept alone, cut <= budget", len(hb) <= 1200 and db == 0, str(len(hb)))
check("E3 cut is at a word boundary (next char in the source is a space)", full.startswith(hb) and full[len(hb)] == " ", repr(full[len(hb):len(hb) + 4]))
hb2, _ = lane2._coherence_history([entry("x" * 3000, place=None, standpoint=None)])
check("E4 an unbreakable single word is hard-cut at the budget", hb2 == "x" * 1200, str(len(hb2)))
check("E5 _cut_at_word keeps a short text whole and cuts on a space",
      lane2._cut_at_word("one two three", 100) == "one two three"
      and lane2._cut_at_word("one two three", 9) == "one two"
      and lane2._cut_at_word("one two three", 7) == "one two"
      and lane2._cut_at_word("one two three", 8) == "one two")
check("E6 entries with no notice are skipped and not counted as dropped",
      lane2._coherence_history([entry(""), entry("kept note")]) == ("[the_study/at_the_door] kept note", 0))
check("E7 no usable entries -> empty history", lane2._coherence_history([entry("")]) == ("", 0))
r_empty, _ = check_one({"factual": [entry("")]})
check("E8 _coherence_check with no usable history still answers no-history", r_empty == {"verdict": "cannot_tell", "how": "no-history"}, str(r_empty))
# a budget that fits exactly: 3 entries of 100 chars + 2 separators
ents = [entry("a" * 70, place=None, standpoint=None), entry("b" * 70, place=None, standpoint=None), entry("c" * 70, place=None, standpoint=None)]
hx, dx = lane2._coherence_history(ents, budget=70 * 3 + 6)
check("E9 exact-fit budget keeps all three", dx == 0 and hx == " / ".join(e["notice"] for e in ents))
hy, dy = lane2._coherence_history(ents, budget=70 * 3 + 5)
check("E10 one character short drops the OLDEST whole entry", dy == 1 and hy.startswith("b"))

# ── F. new observation slice is 400, not 300 ────────────────────────────────────────────────────────
nn = words("obs", 600)
_, sf = check_one(short, notice=nn)
obs = sf["user"].split("NEW OBSERVATION: ")[1]
expect = ("[the_study/at_the_door] " + nn)[:400]
check("F1 new observation cut at 400 characters (label included)", obs == expect and len(obs) == 400, str(len(obs)))
_, sg = check_one(short, notice=nn, flag=False)
check("F2 flag off keeps the old 300 cut", len(sg["user"].split("NEW OBSERVATION: ")[1]) == 300)

# ── G. status() reader: the v2-only split rate ───────────────────────────────────────────────────────
rows = []
for i, (coh) in enumerate([
        {"verdict": "coherent", "how": "agreed"},                                   # legacy row
        {"verdict": "incoherent", "how": "agreed"},                                  # legacy row
        {"verdict": "coherent", "how": "agreed", "hist_v": 2, "hist_dropped": 0},
        {"verdict": "incoherent", "how": "tiebreak", "hist_v": 2, "hist_dropped": 1},
        {"verdict": "coherent", "how": "agreed", "hist_v": 2, "hist_dropped": 0},
        {"verdict": "cannot_tell", "how": "error", "hist_v": 2}]):
    rows.append({"kind": "tick", "ts": 1000 + i, "coherence": coh,
                 "grounding": {"grounded_share": 1.0}})
(TMP / "lane2_shadow.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
try:
    from core import lane2_break_habituation as _hab
    _hab.phase1_metric_sheet = lambda: None
except Exception:
    pass
st = lane2.status()
check("G1 status() keeps the blended coherence verdicts and rate",
      st.get("coherence_verdicts") == {"coherent": 3, "incoherent": 2, "cannot_tell": 1} and st.get("incoherence_rate") == 0.4,
      str((st.get("coherence_verdicts"), st.get("incoherence_rate"))))
check("G2 status() reports the v2-only verdicts and rate",
      st.get("coherence_verdicts_v2") == {"coherent": 2, "incoherent": 1, "cannot_tell": 1} and st.get("incoherence_rate_v2") == 0.333,
      str((st.get("coherence_verdicts_v2"), st.get("incoherence_rate_v2"))))

# ── H. isolation ────────────────────────────────────────────────────────────────────────────────────
check("H1 no non-loopback connect was attempted", not _NONLOCAL, str(_NONLOCAL))
check("H2 this checkout's live data files were not touched", _snap() == _LIVE_BEFORE, f"{_LIVE_BEFORE} vs {_snap()}")
shutil.rmtree(TMP, ignore_errors=True)

bad = [n for n, ok in CHECKS if not ok]
print(f"\n{len(CHECKS) - len(bad)}/{len(CHECKS)} checks passed")
sys.exit(1 if bad else 0)
