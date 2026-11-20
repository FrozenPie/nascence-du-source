"""J-2173 / D-0429(b): wonder anti-repeat gate helpers (pure; reads no live data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core
import core.lane2 as L
wt = os.environ.get("J2173_WT")
if wt:
    assert os.path.abspath(core.__file__).lower().startswith(os.path.abspath(wt).lower()), core.__file__
now = 1_000_000.0
rows = [{"ts": now - 3600, "wonder": "Why does the tide rise twice a day?", "topic": "tide", "would_ask": True},
        {"ts": now - 8 * 86400, "wonder": "What makes the gull cry at dusk?", "topic": "bird", "would_ask": True}]
r = L._wonder_repeat_check("Why does the tide rise two times a day?", "tide", rows, now)
assert r["lexical_repeat"] and r["topic_asked_today"], r
r = L._wonder_repeat_check("How do cormorants dry their wings?", "bird", rows, now)
assert not r["lexical_repeat"] and not r["topic_asked_today"], r
r = L._wonder_repeat_check("What makes the gull cry at dusk?", "bird", rows, now)   # >7d old: not a repeat
assert not r["lexical_repeat"] and r["lexical_sim_max"] == 0.0, r
assert L._wonder_repeat_check("anything here", None, [], now)["lexical_repeat"] is False
assert L._wonder_repeat_check("x", "t", [{"ts": "bad"}], now)["lexical_repeat"] is False
assert L._wonder_stems("The tides glowing") == L._wonder_stems("tide glow")
print("ok")
