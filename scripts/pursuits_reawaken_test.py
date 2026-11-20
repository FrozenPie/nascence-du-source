"""
Pursuits reawaken-candidate / evicted / cooldown-skip shadow-log test (2026-09-05, J-0558/F-0768).
ISOLATED: pu._ACTIVE, pu._SHADOW and pu._DIR are redirected into a fresh temp dir BEFORE any write
(the S-0016 / test-isolation rule) — the live data/pursuits_active.json and data/pursuits_shadow.jsonl
are never opened by this script. Every `vec=` passed to observe() is a hand-built 2D unit vector
(cosvec) so cosine similarity against a pursuit's centroid is EXACT and deterministic — no dependency
on core.memory.store's real embedding model.

Covers J-0558's build (all SHADOW-ONLY, additive — dormancy itself is still terminal after this job;
promotion to a real re-awaken is a separate later job):
  [1] reawaken_candidate fires for a dormant centroid >= REAWAKEN_MIN (0.55), not below it
  [2] the self-topic penalty applies to the dormant bar too (REAWAKEN_MIN + SELF_MATCH_PENALTY)
  [3] the rare-token overlap second signal (CJK ideograph / capitalised proper noun), both as pure
      unit checks and end-to-end on a real reawaken_candidate row
  [4] would_birth on a reawaken_candidate row reports THIS call's own unresolved flag, and a birth
      still fires alongside it — the fall-through is unchanged
  [5] evicted fires on birth-at-CAP displacement, naming the COLDEST dormant pursuit (not a warmer
      one) with the fields the plan asks for, logged BEFORE removal
  [6] no status-field changes anywhere: survivors (dormant or active) are byte-for-byte untouched by
      a reawaken_candidate/evicted log; only a genuine birth adds a NEW pursuit, exactly as before
  [7] cooldown_skip_unresolved fires once per cooldown window for an unresolved thought dropped by
      OBSERVE_COOLDOWN itself, not for a resolved one, not twice in the same window — and the cooldown
      constant itself is untouched
  [8] baseline: an empty register + a non-unresolved, non-matching thought logs nothing at all
Run:  python scripts/pursuits_reawaken_test.py
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="pursuits_reawaken_test_"))
print("isolated store dir:", TMP)

import core.pursuits as pu                                 # noqa: E402

_LIVE_ACTIVE, _LIVE_SHADOW = pu._ACTIVE, pu._SHADOW         # the real paths — must never be opened below
pu._ACTIVE = TMP / "pursuits_active.json"
pu._SHADOW = TMP / "pursuits_shadow.jsonl"
pu._DIR = TMP                                               # _log()/_save() both mkdir(_DIR) first
assert pu._ACTIVE != _LIVE_ACTIVE and pu._SHADOW != _LIVE_SHADOW, "isolation redirect did not take"

fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


def cosvec(cos_val: float) -> list:
    """A 2D unit vector whose cosine similarity to CENTROID=[1,0] is EXACTLY cos_val (both are unit
    vectors, so dot product = cos_val regardless of any later float noise in _cos's own norm calc)."""
    cos_val = max(-1.0, min(1.0, cos_val))
    return [cos_val, math.sqrt(max(0.0, 1.0 - cos_val * cos_val))]


CENTROID = [1.0, 0.0]
FAR = [0.0, 1.0]            # cosine 0 against CENTROID — "matches nothing"
THOUGHT = "a genuinely new idle thought about something, long enough to clear the length gate here"


def reset_shadow() -> None:
    if pu._SHADOW.exists():
        pu._SHADOW.unlink()


def shadow_events(event: str = None) -> list:
    if not pu._SHADOW.exists():
        return []
    out = []
    for line in pu._SHADOW.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        if event is None or ev.get("event") == event:
            out.append(ev)
    return out


def set_active(items: list) -> None:
    pu._save(items)


def reset_rate_limits() -> None:
    """Between scenarios: this file tests the MATCHING/LOGGING logic, not the real-time cooldown gate
    itself (that gets its own dedicated group, [7] below) — so start each scenario as if no observe()
    had ever run."""
    pu._last_observe = 0.0
    pu._last_cooldown_skip_log = 0.0


def dormant(id_, question, about="", heat=0.2, hours_ago=2.0, advances=3, restates=1, centroid=None, now=None):
    now = now if now is not None else time.time()
    c = centroid if centroid is not None else CENTROID
    return {"id": id_, "question": question, "about": about, "born": now - hours_ago * 3600 - 100,
            "standing": question, "thoughts": [question], "established": [about] if about else [],
            "open": "", "centroid": c, "recent_vecs": [c], "advances": advances, "restates": restates,
            "coheres": 0, "scatters": 0, "last_touched": now - hours_ago * 3600, "heat": heat,
            "status": "dormant", "cycle_id": ""}


def active(id_, question, heat=0.5, centroid=None, now=None):
    now = now if now is not None else time.time()
    c = centroid if centroid is not None else FAR
    return {"id": id_, "question": question, "about": "", "born": now - 3600, "standing": question,
            "thoughts": [question], "established": [], "open": "", "centroid": c, "recent_vecs": [c],
            "advances": 5, "restates": 0, "coheres": 3, "scatters": 0, "last_touched": now,
            "heat": heat, "status": "active", "cycle_id": ""}


print("\n[1] reawaken_candidate: fires for a dormant centroid >= REAWAKEN_MIN (0.55), not below")
reset_shadow(); reset_rate_limits()
now = time.time()
d1 = dormant("d1", "an old dormant thread about the topic", about="topic", heat=0.2, hours_ago=3.0, now=now)
set_active([d1])

r_below = pu.observe(THOUGHT, vec=cosvec(0.50), unresolved=False, cycle_id="c-below")
check(r_below is None, "observe() returns None (below bar, sim=0.50)")
check(len(shadow_events("reawaken_candidate")) == 0, "NO reawaken_candidate at sim=0.50 (< 0.55)")

reset_rate_limits()
pu.observe(THOUGHT, vec=cosvec(0.55), unresolved=False, cycle_id="c-boundary")
check(len(shadow_events("reawaken_candidate")) == 1, "reawaken_candidate FIRES exactly at the 0.55 boundary (>=)")

reset_rate_limits()
r_above = pu.observe(THOUGHT, vec=cosvec(0.60), unresolved=False, cycle_id="c-above")
rc = shadow_events("reawaken_candidate")
check(len(rc) == 2, "reawaken_candidate fires again clearly above the bar (sim=0.60)")
if rc:
    last = rc[-1]
    check(last["id"] == "d1", "reawaken_candidate names the matched dormant pursuit's id")
    check(abs(last["match_sim"] - 0.60) < 0.005, f"match_sim recorded correctly ({last.get('match_sim')} ~ 0.60)")
    check(last["would_birth"] is False, "would_birth is False when unresolved=False")
    check(last["advances"] == 3, "advances field mirrors the dormant pursuit's own count")
    check(2.9 <= last["dormant_hours"] <= 3.1, f"dormant_hours ~3.0 ({last.get('dormant_hours')})")
check(r_above is None, "observe() still returns None (no active match, unresolved=False -> no birth): "
                        "return value UNCHANGED by the new log line")
post = pu._load()
check(len(post) == 1 and post[0]["status"] == "dormant" and post[0]["id"] == "d1",
      "the dormant pursuit's own status/id are untouched by reawaken_candidate logging")

print("\n[2] self-topic dormant pursuits need the tighter bar (REAWAKEN_MIN + SELF_MATCH_PENALTY)")
reset_shadow(); reset_rate_limits()
now = time.time()
d_self = dormant("d-self", "a question about my own mind and what I am", heat=0.2, hours_ago=1.0, now=now)
set_active([d_self])
bar = pu.REAWAKEN_MIN + pu.SELF_MATCH_PENALTY
mid = bar - 0.03     # above the plain bar (0.55), below the self-topic bar (0.65)
pu.observe(THOUGHT, vec=cosvec(mid), unresolved=False, cycle_id="c-self-mid")
check(len(shadow_events("reawaken_candidate")) == 0,
      f"self-topic dormant pursuit does NOT fire at {mid:.2f} (needs >= {bar:.2f})")
reset_rate_limits()
hi = bar + 0.02
pu.observe(THOUGHT, vec=cosvec(hi), unresolved=False, cycle_id="c-self-hi")
check(len(shadow_events("reawaken_candidate")) == 1, f"self-topic dormant pursuit DOES fire at {hi:.2f}")

print("\n[3] rare-token overlap: CJK ideograph and capitalised proper noun, both directions")
check(pu._rare_token_overlap("the meaning of 渡 today", "an old thread about 渡 and the ferry") == ["渡"],
      "shared CJK ideograph detected")
check(pu._rare_token_overlap("thinking about Kenji again", "a thread about Kenji's letter") == ["Kenji"],
      "shared capitalised proper noun detected")
check(pu._rare_token_overlap("The cat sat on the mat", "The dog ran in the park") == [],
      'no false positive on a shared sentence-initial common word ("The")')
check(pu._rare_token_overlap("nothing shared here at all", "completely different words too") == [],
      "empty overlap when nothing is shared")

reset_shadow(); reset_rate_limits()
now = time.time()
d2 = dormant("d2", "the meaning of 渡 and the ferry crossing", heat=0.2, hours_ago=2.0, now=now)
set_active([d2])
pu.observe("a fresh thought that also returns to 渡 somehow, unrelated wording otherwise",
           vec=cosvec(pu.REAWAKEN_MIN + 0.05), unresolved=False, cycle_id="c-rare")
rc = shadow_events("reawaken_candidate")
check(len(rc) == 1 and rc[0].get("rare_token_overlap") == ["渡"],
      f"reawaken_candidate row itself carries the shared-glyph overlap "
      f"({rc[0].get('rare_token_overlap') if rc else None})")

print("\n[4] would_birth reflects THIS call's own unresolved flag; a birth still fires (fall-through unchanged)")
reset_shadow(); reset_rate_limits()
now = time.time()
d3 = dormant("d3", "an old dormant thread, unrelated content here", heat=0.2, hours_ago=4.0, now=now)
set_active([d3])
ev = pu.observe("a genuinely unresolved new thought on fresh ground entirely, right?",
                vec=cosvec(pu.REAWAKEN_MIN + 0.05), unresolved=True, cycle_id="c-birth")
rc = shadow_events("reawaken_candidate")
check(len(rc) == 1 and rc[0]["would_birth"] is True, "would_birth is True when unresolved=True")
check(ev is not None and ev.get("event") == "born", "observe() still returns the BORN event (birth fall-through unchanged)")
post = pu._load()
ids = {p["id"] for p in post}
check("d3" in ids and len(post) == 2, "the dormant pursuit is NOT displaced by an under-CAP birth — both survive")
d3_after = next(p for p in post if p["id"] == "d3")
check(d3_after["status"] == "dormant" and d3_after["heat"] == 0.2 and d3_after["advances"] == 3,
      "the dormant pursuit's own fields are completely untouched by the birth alongside it")

print("\n[5] evicted: fires on birth-at-CAP displacement, names the COLDEST dormant pursuit, before removal")
reset_shadow(); reset_rate_limits()
now = time.time()
actives = [active(f"a{i}", f"active pursuit number {i} about its own topic", heat=0.5, now=now) for i in range(pu.CAP)]
cold = dormant("cold", "the coldest dormant pursuit, should be evicted", heat=0.05, hours_ago=5.0,
               advances=7, restates=2, centroid=FAR, now=now)
warm = dormant("warm", "a warmer dormant pursuit, should survive", heat=0.30, hours_ago=1.0,
               centroid=FAR, now=now)
set_active(actives + [cold, warm])
check(len(pu._load()) == pu.CAP + 2, "fixture register set up at exactly CAP active + 2 dormant")

ev = pu.observe("a brand new unresolved thought that matches none of the actives, does it?",
                vec=CENTROID, unresolved=True, cycle_id="c-evict")
check(len(shadow_events("reawaken_candidate")) == 0,
      "no reawaken_candidate noise in this scenario (dormants' centroid is FAR from the thought)")
evd = shadow_events("evicted")
check(len(evd) == 1, "exactly one evicted event")
if evd:
    check(evd[0]["id"] == "cold", "evicted names the COLDEST dormant pursuit, not the warmer one")
    check(evd[0]["heat"] == 0.05, "evicted row carries the pursuit's own heat")
    check(evd[0]["advances"] == 7 and evd[0]["restates"] == 2, "evicted row carries advances/restates")
    check(4.9 <= evd[0]["dormant_hours"] <= 5.1, f"evicted row carries dormant_hours ~5.0 ({evd[0].get('dormant_hours')})")
check(ev is not None and ev.get("event") == "born", "the birth itself still happens (evicted is additive logging, not a new gate)")
post = pu._load()
post_ids = {p["id"] for p in post}
check("cold" not in post_ids, "the evicted pursuit is actually removed from the register")
check("warm" in post_ids, "the warmer dormant pursuit survives the eviction")
warm_after = next(p for p in post if p["id"] == "warm")
check(warm_after["status"] == "dormant" and warm_after["heat"] == 0.30, "the surviving dormant pursuit's fields are unchanged")
check(len(post) == pu.CAP + 2, "register size restored (evicted one out, born one in) — CAP invariant holds")
for i in range(pu.CAP):
    a_after = next(p for p in post if p["id"] == f"a{i}")
    check(a_after["status"] == "active" and a_after["heat"] == 0.5, f"active pursuit a{i} untouched by the eviction elsewhere in the register")

print("\n[6] cooldown_skip_unresolved: fires once per cooldown window, only for unresolved thoughts")
reset_shadow()
now = time.time()
pu._last_observe = now                        # simulate "an observe just happened"
pu._last_cooldown_skip_log = 0.0              # rate limiter open
r1 = pu.observe(THOUGHT, vec=CENTROID, unresolved=True, cycle_id="c-cd1")
check(r1 is None, "observe() returns None while inside the cooldown (unchanged behaviour)")
check(len(shadow_events("cooldown_skip_unresolved")) == 1, "first unresolved drop inside the window logs one row")
pu.observe(THOUGHT, vec=CENTROID, unresolved=True, cycle_id="c-cd2")
check(len(shadow_events("cooldown_skip_unresolved")) == 1, "a SECOND unresolved drop in the same window does NOT log again")
pu.observe(THOUGHT, vec=CENTROID, unresolved=False, cycle_id="c-cd3")
check(len(shadow_events("cooldown_skip_unresolved")) == 1, "a resolved thought dropped by the cooldown never logs at all")
check(pu.OBSERVE_COOLDOWN == 90.0, "OBSERVE_COOLDOWN itself is untouched by this job (still 90.0s)")

print("\n[7] baseline: empty register, non-unresolved, non-matching thought — logs nothing at all")
reset_shadow(); reset_rate_limits()
set_active([])
r = pu.observe(THOUGHT, vec=CENTROID, unresolved=False, cycle_id="c-empty")
check(r is None and len(shadow_events()) == 0, "no pursuits, no birth signal -> completely silent, exactly as before this job")

print("\n[8] isolation proof: this script's module-level paths still point inside the temp dir")
check(pu._ACTIVE == TMP / "pursuits_active.json" and pu._SHADOW == TMP / "pursuits_shadow.jsonl" and pu._DIR == TMP,
      "no late import / code path reset pu._ACTIVE / pu._SHADOW / pu._DIR back to the live data/ files")

print("\nisolated store dir (inspect if needed):", TMP)
print(f"\n{'='*60}\n{'ALL PASS' if fails == 0 else f'{fails} FAILURE(S)'}\n{'='*60}")
sys.exit(0 if fails == 0 else 1)
