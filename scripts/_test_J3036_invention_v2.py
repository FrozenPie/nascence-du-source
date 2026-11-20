"""
Test suite -- J-3036 / F-3743 (P-0098): Lane 2 invention_flag_v2 / invented_topics_v2 beside the legacy keys.
Hermetic: pure-function checks on core.lane2._invention_check plus status() over a temp log (lane2._LOG redirected
to a temp dir). No model call, no hub, no live store is read or written.
Run: python scripts/_test_J3036_invention_v2.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import itertools
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402
assert str(Path(_core_pkg.__file__).resolve()).lower().startswith(str(ROOT).lower()), _core_pkg.__file__
from core import lane2 as L  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if (detail and not cond) else ""))
    if not cond:
        FAILS.append(name)


def P(fields=(), sounds=(), smells=(), daylight="night"):
    return {"world_fields": list(fields),
            "world": {"sounds": list(sounds), "smells": list(smells), "daylight": daylight}}


# 1. the old keys keep their meaning, the new keys are present
r = L._invention_check({"notice": "x", "uncertain": "x", "expect_next": "x"}, P())
check("all six keys present", set(r) == {"invented_topics", "invention_flag", "invented_topics_legacy",
                                          "invention_flag_legacy", "invented_topics_v2", "invention_flag_v2"}, str(sorted(r)))

# 2. uncertain-only hedge: old flags it, v2 does not (F-3743 54% class)
out = {"notice": "The room is quiet.", "uncertain": "I cannot see the fire or hear the tide.", "expect_next": "Nothing."}
r = L._invention_check(out, P())
check("uncertain-only: current flag still True", r["invention_flag"] and r["invented_topics"] == ["fire", "tide"], str(r))
check("uncertain-only: legacy unchanged", r["invented_topics_legacy"] == ["fire", "tide"], str(r))
check("uncertain-only: v2 clear", r["invention_flag_v2"] is False and r["invented_topics_v2"] == [], str(r))

# 3. a real assertion in notice / expect_next is still flagged by v2
r = L._invention_check({"notice": "The fire crackles.", "uncertain": "", "expect_next": ""}, P())
check("asserted fire with no fire field: v2 flags", r["invented_topics_v2"] == ["fire"], str(r))
r = L._invention_check({"notice": "", "uncertain": "", "expect_next": "The tide will turn."}, P())
check("expect_next is scanned by v2", r["invented_topics_v2"] == ["tide"], str(r))

# 4. wet/damp licensed from smells (F-3743 27-of-33 class); old checks still flag
out = {"notice": "The air feels damp and the ground is wet.", "uncertain": "", "expect_next": ""}
r = L._invention_check(out, P(smells=["wet_earth"]))
check("smells wet_earth licenses wet+damp in v2", r["invented_topics_v2"] == [], str(r))
check("...while current/legacy still flag them",
      r["invented_topics"] == ["damp", "wet"] and r["invented_topics_legacy"] == ["damp", "wet"], str(r))
r = L._invention_check(out, P(smells=["salt_weed"]))
check("unrelated smell does not license wet/damp", r["invented_topics_v2"] == ["damp", "wet"], str(r))
r = L._invention_check(out, P())
check("no smells: wet/damp flagged", r["invented_topics_v2"] == ["damp", "wet"], str(r))
r = L._invention_check({"notice": "It is raining.", "uncertain": "", "expect_next": ""}, P(smells=["wet_earth"]))
check("rain is NOT licensed by a wet smell", r["invented_topics_v2"] == ["raining"], str(r))
r = L._invention_check({"notice": "Moonlight on the shingle.", "uncertain": "", "expect_next": ""},
                       P(smells=["moonlight_dew"]))
check("moon stays strict even if a smell token contains it", r["invented_topics_v2"] == ["moonlight"], str(r))
bare = P()
bare["world"]["smells"] = "wet_earth"
r = L._invention_check(out, bare)
check("a bare-string smells value is not iterated by character", r["invented_topics_v2"] == [], str(r))

# 5. v2 keeps the F-1936 licences (sound token, daylight) and is a subset of the current verdict
r = L._invention_check({"notice": "The sun is low and a cat is purring.", "uncertain": "", "expect_next": ""},
                       P(sounds=["cat_purr"], daylight="dusk"))
check("v2 keeps sound-token and daylight licences", r["invented_topics_v2"] == [] and r["invention_flag"] is False, str(r))
words = ["fire", "tide", "sun", "moon", "cat", "wet", "damp", "rain", "wind", "sound", "smell", "light", "dim"]
subset_ok = True
for a, b in itertools.product(words, words):
    for sm in ([], ["wet_earth"]):
        x = L._invention_check({"notice": a, "uncertain": b, "expect_next": ""}, P(smells=sm))
        if not set(x["invented_topics_v2"]) <= set(x["invented_topics"]):
            subset_ok = False
check("v2 topics are always a subset of the current topics (v2 only ever clears)", subset_ok)

# 6. the wonder caller scans its own field in v2 (not silently nothing)
r = L._invention_check({"wonder": "Why does the fire burn?"}, P(), out_fields=("wonder",))
check("wonder call: v2 scans the wonder field", r["invented_topics_v2"] == ["fire"], str(r))


# 7. status(): three series, v2 rate over rows that carry the key only
def tick(inv, ts):
    return {"kind": "tick", "ts": ts, "grounding": {"grounded_share": 1.0}, "invention": inv,
            "metaphor_flags": [], "coherence": {"verdict": "coherent"}}


old_rows = [tick({"invention_flag": True, "invented_topics": ["wet"]}, 1.0),   # pre-restart: no v2 key
            tick({"invention_flag": False, "invented_topics": []}, 2.0)]
new_rows = [tick({"invention_flag": True, "invented_topics": ["fire"], "invention_flag_legacy": True,
                  "invented_topics_legacy": ["fire"], "invention_flag_v2": False, "invented_topics_v2": []}, 3.0),
            tick({"invention_flag": True, "invented_topics": ["sun"], "invention_flag_legacy": True,
                  "invented_topics_legacy": ["sun"], "invention_flag_v2": True, "invented_topics_v2": ["sun"]}, 4.0)]
tmp = Path(tempfile.mkdtemp(prefix="J3036_"))
orig_log = L._LOG
try:
    L._LOG = tmp / "lane2_shadow.jsonl"
    L._LOG.write_text("\n".join(json.dumps(x) for x in old_rows + new_rows) + "\n", encoding="utf-8")
    st = L.status()
finally:
    L._LOG = orig_log
check("status: tick count 4", st.get("ticks") == 4, str(st.get("ticks")))
check("status: invention_rate (metric of record) semantics unchanged", st.get("invention_rate") == 0.75,
      str(st.get("invention_rate")))
check("status: v2 rate is over the 2 rows that carry the key, not 4",
      st.get("invention_rate_v2") == 0.5 and st.get("invention_v2_n") == 2, str(st.get("invention_rate_v2")))
check("status: v2 coverage 0.5", st.get("invention_v2_coverage") == 0.5, str(st.get("invention_v2_coverage")))
check("status: same-rows current and legacy contrast",
      st.get("invention_rate_on_v2_rows") == 1.0 and st.get("invention_rate_legacy_on_v2_rows") == 1.0)
check("status: v2 topics counted", st.get("invented_topics_v2") == {"sun": 1}, str(st.get("invented_topics_v2")))
check("status: legacy series still present", "invention_rate_legacy" in st and "invented_topics_legacy" in st)

try:
    L._LOG = tmp / "old.jsonl"
    L._LOG.write_text(json.dumps(old_rows[0]) + "\n", encoding="utf-8")
    st0 = L.status()
finally:
    L._LOG = orig_log
check("status: before the restart v2 rate is None, coverage 0.0 (no back-fill)",
      st0.get("invention_rate_v2") is None and st0.get("invention_v2_coverage") == 0.0, str(st0.get("invention_rate_v2")))

print("\nALL PASS" if not FAILS else f"\n{len(FAILS)} FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
