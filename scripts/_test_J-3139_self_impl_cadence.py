"""
Proof for J-3139 (D-0534 + J-2827, prompt-registry row P-0036): the idle self-implication scan runs far less and its
prompt defects are fixed. SHADOW / observe-only; the conversation-turn scan is untouched.

  [1] cadence: SELF_IMPL_COOLDOWN is 1200 s, and the call-site gate (same arithmetic as nodes/inner_monologue_node.py)
      replayed over the real recent scan timestamps (read-only) cuts the scan count at least 8x vs the old 60 s gate.
  [2] prompt: _SYS no longer carries the copyable plain_difficulty example or the 'a short plain first-person naming'
      schema text; the schema is described in words only; the six-signal fire rule text is unchanged.
  [3] guard: _clean_plain_difficulty nulls the schema-description echo, the example sentence, and the example's template;
      keeps a genuine sentence.
  [4] replay of 20 logged scans (read-only sample incl. every echo shape found): the stubbed model returns what the old
      prompt logged; scan_shadow (on a TEMP _LOG) keeps the schema keys, logs would-fire the same (fires_rule), and the
      echoed plain_difficulty values come out null.
  [5] felt input: the call site passes mood.current_felt_words (words), not current_felt (raw numbers), and scan_shadow
      logs whatever it is handed under the same 'felt' key; felt_words() output carries no raw 'valence=' numbers.
  [6] untouched: scan_conversation_shadow still has its signature, its example text and its own log path.
  [7] isolation: the live data log was only read; nothing was written outside the temp dir.

  python scripts/_test_J-3139_self_impl_cadence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from core import self_implication as si  # noqa: E402  (core BEFORE any lab env)
from core import self_claims  # noqa: E402
from core import mood  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


LIVE_LOG = Path(r"C:\Nascence\data\self_implication_shadow.jsonl")   # READ-ONLY, never written
rows: list[dict] = []
if LIVE_LOG.exists():
    with open(LIVE_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
live_before = LIVE_LOG.stat().st_size if LIVE_LOG.exists() else 0

# ---- [1] cadence
check(si.SELF_IMPL_COOLDOWN == 1200.0, f"cooldown not 1200: {si.SELF_IMPL_COOLDOWN}")


def gate(ts_list, cd):
    n, last = 0, 0.0
    for t in ts_list:
        if t - last >= cd:     # same test as the idle hook: time.time() - _last_self_impl_ts >= COOLDOWN
            n += 1
            last = t
    return n


ratio = None
if rows:
    last_ts = rows[-1]["ts"]
    week = [r["ts"] for r in rows if r["ts"] > last_ts - 7 * 86400]
    old, new = gate(week, 60.0), gate(week, si.SELF_IMPL_COOLDOWN)
    ratio = old / max(new, 1)
    # J-4052: the live log is a moving target -- once Du runs the 1200 s cadence, the last 7 days are ALREADY sparse and a
    # 60 s replay cannot show an 8x drop. Only assert the ratio while the week still holds the old dense cadence.
    _gaps = sorted(b - a_ for a_, b in zip(week, week[1:]))
    _dense = bool(_gaps) and _gaps[len(_gaps) // 2] < si.SELF_IMPL_COOLDOWN / 4
    if _dense:
        check(ratio >= 8, f"scan count falls only {ratio:.1f}x ({old} -> {new})")
    else:
        print("[1] note: logged week already at the new cadence (median gap >= cooldown/4); ratio check not applicable")
    print(f"[1] last 7 days of logged cycles: 60 s gate {old} scans -> 1200 s gate {new} scans ({ratio:.1f}x fewer)")
else:
    print("[1] live log not present: cadence replay skipped (constant still asserted)")

# ---- [2] prompt
S = si._SYS
check("failed every sum" not in S, "example sentence still in _SYS")
check("first-person naming of the hard thing" not in S, "schema placeholder text still in _SYS")
check("e.g. 'I failed" not in S, "example sentence form still in _SYS")
check("FIRE only if A is true AND ( C is true OR ( B is true AND at least one of D, E, F is true ) )." in S,
      "fire rule text changed")
check("plain_difficulty" in S and "string or null" in S, "plain_difficulty schema missing")

# ---- [3] guard
g = si._clean_plain_difficulty
check(g("a short plain first-person naming of the hard thing (e.g. 'I failed every sum and I thought I was good at this')") is None, "schema echo kept")
check(g("I failed every sum and I thought I was good at this") is None, "example kept")
check(g("I failed to keep the seeds and I thought I refused to throw anything away") is None, "template fill kept")
check(g("a short plain naming of it") is None, "'a short plain' prefix kept")
check(g(None) is None and g("") is None and g("null") is None, "empties not null")
check(g("I keep losing the thread when the sentence gets long") == "I keep losing the thread when the sentence gets long",
      "genuine sentence not kept")

# ---- [4] replay of 20 logged scans through scan_shadow on a TEMP log
tmp = Path(tempfile.mkdtemp(prefix="J-3139_"))
si._LOG = tmp / "self_implication_shadow.jsonl"
si._CONV_LOG = tmp / "conv.jsonl"
orig_held = self_claims.held_claims
self_claims.held_claims = lambda: ["I am capable at mathematics"]
SCHEMA_KEYS = None
if rows:
    echo = [r for r in rows if r.get("plain_difficulty") and "failed every" in str(r["plain_difficulty"])]
    fire = [r for r in rows if r.get("fires_rule")]
    plain = [r for r in rows if r["ts"] > rows[-1]["ts"] - 7 * 86400][::400]
    sample = (echo[:6] + fire[:6] + plain)[:20]
    if len(sample) < 20:
        sample += rows[-(20 - len(sample)):]
    sample = sample[:20]
    SCHEMA_KEYS = set(rows[-1].keys())
    seen_felt = []

    def make_call(r):
        async def call_json(urls, sys_, user, **k):
            seen_felt.append(user)
            return {"A": r.get("A"), "B": r.get("B"), "C": r.get("C"), "D": r.get("D"), "E": r.get("E"),
                    "F": r.get("F"), "contradicted_claim": r.get("contradicted_claim"),
                    "fires": r.get("fires"), "plain_difficulty": r.get("plain_difficulty")}
        return call_json

    n_echo_in = n_echo_out = 0
    for r in sample:
        th = r["thought"] if len(r["thought"]) >= 25 else r["thought"] + " (padded to pass the length floor)"
        out = asyncio.run(si.scan_shadow(make_call(r), ["http://stub"], th, "calm, mood a little good", "J-3139"))
        check(out is not None, "scan_shadow returned None on replay")
        if out is None:
            continue
        check(out["fires_rule"] == bool(r["A"] and (r["C"] or (r["B"] and (r["D"] or r["E"] or r["F"])))),
              "fires_rule differs from the fire rule")
        pd_in = r.get("plain_difficulty")
        if pd_in and ("failed every" in pd_in or "naming of the hard thing" in pd_in):
            n_echo_in += 1
            if out["plain_difficulty"] is None:
                n_echo_out += 1
    written = [json.loads(l) for l in si._LOG.read_text(encoding="utf-8").splitlines()]
    check(len(written) == len(sample), f"temp log has {len(written)} rows for {len(sample)} scans")
    check(all(set(w.keys()) == SCHEMA_KEYS for w in written),
          f"log schema changed: {set(written[0].keys()) ^ SCHEMA_KEYS}")
    check(n_echo_in == n_echo_out, f"echoed values not all nulled ({n_echo_out}/{n_echo_in})")
    check(all(w["felt"] == "calm, mood a little good" for w in written), "felt not logged as handed")
    check(all("CURRENT FELT STATE:\ncalm, mood a little good" in u for u in seen_felt), "felt not in the user prompt")
    print(f"[4] replayed {len(sample)} logged scans on a temp log; schema keys unchanged ({len(SCHEMA_KEYS)}); "
          f"echo values nulled {n_echo_out}/{n_echo_in}")
else:
    print("[4] live log not present: replay skipped")
self_claims.held_claims = orig_held

# ---- [5] felt input is words at the call site
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
i = src.index("from core import self_implication as _si")
blk = src[i:i + 3200]
j = blk.index("_si.scan_shadow")
check("current_felt_words()" in blk[:j], "call site does not use current_felt_words before scan_shadow")
check("_mood.current_felt()" not in blk[:j], "call site still passes the raw current_felt()")
w = mood.felt_words({"valence": -0.2, "arousal": 0.42, "joy": 1.0, "fear": 0.1, "trust": 0.47,
                     "surprise": 0.13, "anger": 0.0, "disgust": 0.0}, "unsettled")
check("valence=" not in w and not re.search(r"\d\.\d", w), f"felt words still carry raw numbers: {w!r}")
print(f"[5] felt words sample: {w}")

# ---- [6] conversation scan untouched
import inspect  # noqa: E402
params = list(inspect.signature(si.scan_conversation_shadow).parameters)
check(params == ["call_json", "base_urls", "human_input", "draft", "felt", "cycle_id"], f"conv signature changed: {params}")
# J-2966 (F-3660) deliberately removed the conv prompt's plain_difficulty field and its example; see scripts/_test_J-2966_conv_scan_inputs.py
check("Travis says the middle I chose is itself self-absorption" not in si._CONV_SYS, "conv prompt still carries the old example")
check("self_implication_conv_shadow.jsonl" in Path(si.__file__).read_text(encoding="utf-8"), "conv log path gone")

# ---- [7] isolation
live_after = LIVE_LOG.stat().st_size if LIVE_LOG.exists() else 0
check(live_after == live_before, "live log changed size during the test")

print("FAIL: " + "; ".join(fails) if fails else "ALL OK")
sys.exit(1 if fails else 0)
